# StratoviqueAI
### AI Multi-Agent Marketing Strategy Engine

Built with **LangGraph + Gemini + Serper**.
Inspired by the [crewAI marketing_strategy example](https://github.com/crewAIInc/crewAI-examples/tree/main/crews/marketing_strategy) — rebuilt from scratch for production.

---

## How It Compares to the CrewAI Example

| Feature | CrewAI Example | StratoviqueAI |
|---|---|---|
| Agents | 3 (researcher, strategist, writer) | 6 (research, brief, strategy, campaigns, copy, report) |
| LLM | GPT-4o (paid) | Gemini 2.0 Flash (free tier) |
| Search | SerperDevTool | GoogleSerperAPIWrapper |
| Orchestration | CrewAI sequential | LangGraph StateGraph |
| Human review | ✗ Not possible | ✓ Native interrupt checkpoint |
| State inspection | ✗ Opaque | ✓ Full state at every node |
| Frontend | CLI only | FastAPI + Jinja2 web app |
| API | ✗ None | ✓ FastAPI REST endpoints |
| Conditional routing | ✗ None | ✓ conditional_edges |
| Error recovery | Restart from scratch | Per-node checkpoint |

---

## Agent Pipeline

```
User Input
  → [01] Market Research Agent   (Serper search + Gemini analysis)
  → [02] Project Brief Agent     (synthesises research into brief)
  → [03] Strategy Agent          (positioning, channels, roadmap)
  → [04] Campaign Agent          (5 campaign concepts)
  → [05] Copy Agent              (ads, emails, scripts, landing page)
  → [HUMAN REVIEW CHECKPOINT]
  → [06] Report Agent            (final executive report)
```

---

## Quick Start (Windows)

```cmd
cd stratoviqueai
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
notepad .env
python run.py
```

Open → http://localhost:8000

---

## Required API Keys

| Key | Where to get | Cost |
|---|---|---|
| `GEMINI_API_KEY` | [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) | Free (1500 req/day) |
| `SERPER_API_KEY` | [serper.dev](https://serper.dev) | You already have this |

---

## Project Structure

```
stratoviqueai/
├── backend/
│   ├── agents/
│   │   └── agents.py          ← All 6 LangGraph agent nodes
│   ├── graph/
│   │   ├── state.py           ← TypedDict state (MarketingState)
│   │   └── workflow.py        ← StateGraph + human interrupt
│   ├── tools/
│   │   └── search.py          ← Serper search wrapper
│   ├── prompts/
│   │   └── prompts.py         ← All 6 system prompts
│   └── main.py                ← FastAPI app + routes
├── frontend/
│   ├── templates/             ← Jinja2 HTML templates
│   │   ├── base.html
│   │   ├── index.html         ← Input form
│   │   ├── review.html        ← Human review checkpoint
│   │   ├── result.html        ← Final report
│   │   └── error.html
│   └── static/
│       ├── css/style.css      ← Dark editorial design
│       └── js/main.js
├── .env.example
├── requirements.txt
└── run.py
```

---

## Gemini Model Options

Edit `GEMINI_MODEL` in your `.env`:

```
gemini-2.0-flash    ← Default. Fast, free tier friendly
gemini-2.5-pro      ← Best quality output (recommended for client demo)
gemini-1.5-flash    ← Ultra fast, lighter output
```

---

© 2025 StratoviqueAI. All rights reserved.
