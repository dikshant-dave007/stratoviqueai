import os
import uuid
from datetime import datetime
from typing import Optional
from time import time

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from starlette.middleware.base import BaseHTTPMiddleware

load_dotenv()

from backend.graph.workflow import graph
from backend.graph.state import MarketingState
from backend.pdf_generator import generate_pdf
from backend.config import app_logger, perf_logger, get_token_summary, reset_token_tracker, log_token_summary

app = FastAPI(title="StratoviqueAI", version="2.0.0")
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

app_logger.info("StratoviqueAI FastAPI application initialized")


# ── Timing Middleware ─────────────────────────────────────────────────────────

class TimingMiddleware(BaseHTTPMiddleware):
    """Middleware to track endpoint execution time"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time()
        response = await call_next(request)
        duration = (time() - start_time) * 1000  # milliseconds
        
        # Extract session ID from params/body if available
        session_id = request.query_params.get("session_id", "")
        endpoint = request.url.path
        method = request.method
        status = response.status_code
        
        status_prefix = "OK" if 200 <= status < 300 else "WN" if 400 <= status < 500 else "ER"
        
        perf_logger.info(
            f"{status_prefix} {method:6s} {endpoint:30s} | {status} | {duration:7.2f}ms" + 
            (f" | Session: {session_id[:8]}..." if session_id else "")
        )
        
        return response


app.add_middleware(TimingMiddleware)

# ── In-memory stores ──────────────────────────────────────────────────────────
sessions: dict[str, dict] = {}
report_history: list[dict] = []


def _err(request, error, session_id=None, failed_step=None, inputs=None):
    return templates.TemplateResponse("error.html", {
        "request": request, "error": error,
        "session_id": session_id, "failed_step": failed_step, "inputs": inputs,
    })


# ── API: sessions list for sidebar ───────────────────────────────────────────

@app.get("/api/sessions", response_class=JSONResponse)
async def api_sessions():
    """Returns history list for the sidebar — newest first."""
    return list(reversed([{
        "session_id":   r["session_id"],
        "company_name": r["company_name"],
        "industry":     r["industry"],
        "goals":        r["goals"],
        "created_at":   r["created_at"],
    } for r in report_history]))


# ── Pages ─────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/history", response_class=HTMLResponse)
async def history(request: Request):
    return templates.TemplateResponse("history.html", {
        "request": request,
        "reports": list(reversed(report_history)),
    })

@app.get("/history/{session_id}", response_class=HTMLResponse)
async def history_detail(request: Request, session_id: str):
    report = next((r for r in report_history if r["session_id"] == session_id), None)
    if not report:
        return _err(request, "Report not found in history.")
    return templates.TemplateResponse("result.html", {
        "request": request, "session_id": session_id,
        "state": report["state"], "company_name": report["company_name"],
        "from_history": True,
    })


# ── Generate ──────────────────────────────────────────────────────────────────

@app.post("/generate", response_class=HTMLResponse)
async def generate(
    request: Request,
    company_name: str = Form(...),
    product_description: str = Form(...),
    target_audience: str = Form(...),
    budget: str = Form(...),
    goals: str = Form(...),
    industry: str = Form(...),
):
    session_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}

    app_logger.info(f"[Session {session_id}] New generation request | Company: {company_name} | Industry: {industry}")
    
    # Reset token tracker for new session
    reset_token_tracker()

    form_inputs = {
        "company_name": company_name, "product_description": product_description,
        "target_audience": target_audience, "budget": budget,
        "goals": goals, "industry": industry,
    }

    initial_state: MarketingState = {
        **form_inputs,
        "market_research": None, "audience_profile": None,
        "channel_strategy": None, "content_strategy": None,
        "final_report": None, "human_approved": None,
        "human_feedback": None, "current_step": "research",
        "errors": [], "session_id": session_id,
        "created_at": datetime.utcnow().isoformat(),
    }

    sessions[session_id] = {"config": config, "state": initial_state, "inputs": form_inputs}

    try:
        app_logger.debug(f"[Session {session_id}] Starting workflow execution")
        result = graph.invoke(initial_state, config=config)
        sessions[session_id]["state"] = result
        
        # Log token summary
        app_logger.info(f"[Session {session_id}] Workflow completed successfully")
        log_token_summary()
        
        return templates.TemplateResponse("review.html", {
            "request": request, "session_id": session_id,
            "state": result, "company_name": company_name,
        })
    except Exception as e:
        app_logger.error(f"[Session {session_id}] Workflow failed: {str(e)}", exc_info=True)
        return _err(request, str(e), session_id,
                    initial_state.get("current_step", "research"), form_inputs)


# ── Approve ───────────────────────────────────────────────────────────────────

@app.post("/approve/{session_id}", response_class=HTMLResponse)
async def approve(
    request: Request, session_id: str,
    feedback: Optional[str] = Form(default=""),
):
    if session_id not in sessions:
        app_logger.warning(f"[Session {session_id}] Approve request for expired session")
        return _err(request, "Session expired. Please resubmit.")

    session = sessions[session_id]
    config, state = session["config"], session["state"]

    app_logger.info(f"[Session {session_id}] Human approval received and proceeding to final report")

    try:
        # Correct LangGraph resume pattern with interrupt_before:
        # 1. Update the checkpointed state with approval + feedback
        # 2. Resume by invoking with None (continues from interrupt point)
        feedback_text = feedback.strip() if feedback and feedback.strip() else "No additional feedback."
        app_logger.debug(f"[Session {session_id}] Updating state with approval and feedback")
        
        graph.update_state(config, {
            "human_approved": True,
            "human_feedback": feedback_text,
        })
        
        result = graph.invoke(None, config=config)
        sessions[session_id]["state"] = result

        company = state.get("company_name", "Unknown")
        report_history.append({
            "session_id": session_id, "company_name": company,
            "industry": state.get("industry", ""),
            "goals": state.get("goals", ""),
            "budget": state.get("budget", ""),
            "created_at": datetime.utcnow().strftime("%d %b %Y, %H:%M"),
            "state": result,
        })

        # Log final token summary
        log_token_summary()
        app_logger.info(f"[Session {session_id}] Final report generated and saved to history")

        return templates.TemplateResponse("result.html", {
            "request": request, "session_id": session_id,
            "state": result, "company_name": company, "from_history": False,
        })
    except Exception as e:
        app_logger.error(f"[Session {session_id}] Approval/report generation failed: {str(e)}", exc_info=True)
        return _err(request, str(e), session_id, "report", session.get("inputs", {}))


# ── Retry ─────────────────────────────────────────────────────────────────────

@app.post("/retry/{session_id}", response_class=HTMLResponse)
async def retry(request: Request, session_id: str):
    if session_id not in sessions:
        app_logger.warning(f"[Session {session_id}] Retry request for expired session")
        return _err(request, "Session expired. Please resubmit.")

    session = sessions[session_id]
    config, inputs = session["config"], session.get("inputs", {})
    last_state = session.get("state", {})

    app_logger.info(f"[Session {session_id}] Retry requested, resetting errors and re-running")
    
    try:
        # Reset errors and re-run from last checkpoint
        graph.update_state(config, {"errors": []})
        result = graph.invoke(None, config=config)
        sessions[session_id]["state"] = result
        
        app_logger.info(f"[Session {session_id}] Retry completed successfully")
        
        return templates.TemplateResponse("review.html", {
            "request": request, "session_id": session_id,
            "state": result, "company_name": inputs.get("company_name", ""),
        })
    except Exception as e:
        app_logger.error(f"[Session {session_id}] Retry failed: {str(e)}", exc_info=True)
        return _err(request, str(e), session_id,
                    last_state.get("current_step", "unknown"), inputs)


# ── PDF Download ─────────────────────────────────────────────────────────────

@app.get("/download/{session_id}")
async def download_pdf(session_id: str):
    """Generate and stream a ReportLab PDF for a completed strategy."""
    app_logger.debug(f"[Session {session_id}] PDF download requested")
    # Check live sessions first, then history
    state = None
    company_name = "strategy"

    if session_id in sessions:
        state        = sessions[session_id]["state"]
        company_name = state.get("company_name", "strategy")
    else:
        report = next((r for r in report_history if r["session_id"] == session_id), None)
        if report:
            state        = report["state"]
            company_name = report["company_name"]

    if not state:
        app_logger.warning(f"[Session {session_id}] PDF download failed - session not found")
        return Response(content="Session not found.", status_code=404)

    if not state.get("final_report"):
        app_logger.warning(f"[Session {session_id}] PDF download failed - report not yet generated")
        return Response(content="Report not yet generated.", status_code=400)

    try:
        app_logger.info(f"[Session {session_id}] Generating PDF for {company_name}")
        pdf_bytes = generate_pdf(state)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename  = f"{company_name.replace(' ', '_')}_StratoviqueAI_{timestamp}.pdf"
        app_logger.info(f"[Session {session_id}] PDF generated successfully - {len(pdf_bytes)} bytes")
        return Response(
            content    = pdf_bytes,
            media_type = "application/pdf",
            headers    = {"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        app_logger.error(f"[Session {session_id}] PDF generation failed: {str(e)}", exc_info=True)
        return Response(content=f"PDF generation failed: {str(e)}", status_code=500)


# ── Status / Health ───────────────────────────────────────────────────────────

@app.get("/status/{session_id}", response_class=JSONResponse)
async def status(session_id: str):
    if session_id not in sessions:
        app_logger.debug(f"[Session {session_id}] Status request for unknown session")
        return JSONResponse({"error": "Session not found"}, status_code=404)
    s = sessions[session_id]["state"]
    status_info = {
        "session_id": session_id, "current_step": s.get("current_step"),
        "has_research": bool(s.get("market_research")),
        "has_audience": bool(s.get("audience_profile")),
        "has_channel":  bool(s.get("channel_strategy")),
        "has_content":  bool(s.get("content_strategy")),
        "has_report":   bool(s.get("final_report")),
        "human_approved": s.get("human_approved"),
    }
    app_logger.debug(f"[Session {session_id}] Status: {status_info['current_step']}")
    return status_info

@app.get("/health")
async def health():
    app_logger.debug("Health check requested")
    return {"status": "ok", "service": "StratoviqueAI", "version": "2.0.0"}
