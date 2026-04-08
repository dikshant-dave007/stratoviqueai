from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from backend.graph.state import MarketingState
from backend.agents.agents import (
    research_agent,
    audience_agent,
    channel_agent,
    content_agent,
    report_agent,
)
from backend.config import langgraph_logger


def should_generate_report(state: MarketingState) -> str:
    """Route after human review checkpoint."""
    session_id = state.get("session_id", "unknown")
    human_approved = state.get("human_approved")
    
    if human_approved is True:
        langgraph_logger.info(f"[Session {session_id}] Human approved - routing to report generation")
        return "generate_report"
    elif human_approved is False:
        langgraph_logger.info(f"[Session {session_id}] Human rejected - re-running content strategy with feedback")
        # Re-run content strategy with feedback
        return "revise_content"
    # Not yet reviewed — pause here
    langgraph_logger.debug(f"[Session {session_id}] Awaiting human review")
    return "await_review"


def build_workflow() -> StateGraph:
    """Build and compile the StratoviqueAI LangGraph workflow."""
    langgraph_logger.info("Building workflow graph...")

    workflow = StateGraph(MarketingState)

    # ── Register Nodes ──────────────────────────────────────────────────────
    langgraph_logger.debug("Registering workflow nodes")
    workflow.add_node("research", research_agent)
    workflow.add_node("audience", audience_agent)
    workflow.add_node("channel", channel_agent)
    workflow.add_node("content", content_agent)
    workflow.add_node("report", report_agent)

    # ── Sequential Edges ─────────────────────────────────────────────────────
    langgraph_logger.debug("Creating sequential workflow edges")
    workflow.set_entry_point("research")
    workflow.add_edge("research", "audience")
    workflow.add_edge("audience", "channel")
    workflow.add_edge("channel", "content")

    # ── Human Review Conditional Edge ────────────────────────────────────────
    langgraph_logger.debug("Creating conditional routing for human review")
    workflow.add_conditional_edges(
        "content",
        should_generate_report,
        {
            "generate_report": "report",
            "revise_content": "content",   # loop back with feedback
            "await_review": END,           # pause for human input
        },
    )

    workflow.add_edge("report", END)

    # ── Compile with in-memory checkpointer ──────────────────────────────────
    langgraph_logger.debug("Compiling workflow with memory checkpointer")
    memory = MemorySaver()
    compiled_graph = workflow.compile(
        checkpointer=memory,
        interrupt_before=["report"],  # pause before final report for human approval
    )
    
    langgraph_logger.info("Workflow graph compiled successfully")
    return compiled_graph


# Singleton compiled graph
graph = build_workflow()
