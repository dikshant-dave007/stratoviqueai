# StratoviqueAI
### AI Multi-Agent Marketing Strategy Engine

**StratoviqueAI** is a production-ready, multi-agent AI system designed to generate comprehensive marketing strategies from a single user input. It leverages cutting-edge language models and web search capabilities to research markets, develop strategic positioning, and create campaign concepts—all with human oversight built in.

Built with **LangGraph + Google Gemini + Serper API**.
Inspired by the [crewAI marketing_strategy example](https://github.com/crewAIInc/crewAI-examples/tree/main/crews/marketing_strategy) — rebuilt from scratch for production use.

### Key Features

- **6 Specialized Agents**: Research, brief synthesis, strategic planning, campaign ideation, copywriting, and report generation
- **LangGraph Orchestration**: Robust agent coordination with conditional routing and error recovery
- **Human-in-the-Loop**: Built-in review checkpoint for approving strategies before report generation
- **Web Search Integration**: Real-time market and competitor research via Serper API
- **Cost-Efficient**: Uses Google Gemini (free tier compatible) instead of paid GPT-4
- **Full State Management**: Complete workflow state inspection at every step
- **REST API**: FastAPI endpoints for programmatic access
- **Web Interface**: Modern Jinja2-based frontend with dark editorial design
- **Comprehensive Logging**: Detailed logs for performance tracking, token usage, and debugging

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
User Input (Product/Service/Goal)
  ↓
  [01] Market Research Agent
       └─ Searches for market size, trends, competitors, audience insights
  ↓
  [02] Project Brief Agent
       └─ Synthesizes research into structured brief (problem, audience, opportunity)
  ↓
  [03] Strategy Agent
       └─ Develops positioning, messaging pillars, channel strategy, 12-month roadmap
  ↓
  [04] Campaign Agent
       └─ Ideates 5 distinct campaign concepts with hooks and KPIs
  ↓
  [05] Copy Agent
       └─ Creates ad copy, email sequences, sales scripts, landing page headlines
  ↓
  [HUMAN REVIEW CHECKPOINT] ← Stakeholders approve strategy before final report
  ↓
  [06] Report Agent
       └─ Generates executive summary and formatted final report
  ↓
Output: Complete Marketing Strategy Document
```

### Agent Descriptions

| Agent | Purpose | Inputs | Outputs |
|-------|---------|--------|---------|
| **Market Research** | Gather competitive intelligence and market data | Product/service description | Market insights, competitor analysis, audience data |
| **Project Brief** | Transform raw research into actionable brief | Research results | Structured brief with problem statement, audience, opportunities |
| **Strategy** | Define positioning and go-to-market approach | Project brief | Positioning statement, messaging pillars, channel strategy, roadmap |
| **Campaign** | Generate creative campaign concepts | Strategy framework | 5 campaign concepts with hooks, creatives, and success metrics |
| **Copy** | Craft persuasive marketing copy | Campaign concepts | Ad variations, email sequences, sales scripts, landing page copy |
| **Report** | Compile executive summary | All previous outputs | Final polished marketing strategy document |

---

## Quick Start (Windows)

### Prerequisites
- Python 3.10 or higher
- Internet connection (for API access)
- API keys for Gemini and Serper (see [Required API Keys](#required-api-keys) below)

### Installation Steps

```cmd
cd stratoviqueai
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Then edit `.env` with your API keys:
```env
GEMINI_API_KEY=your_key_here
SERPER_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.0-flash
```

### Running the Application

```cmd
python run.py
```

Then open your browser to **http://localhost:8000**

### Expected Workflow

1. **Input**: Enter product/service description in the web form
2. **Research Phase**: System searches market data and analyzes competitors (~30-60 seconds)
3. **Processing**: Agents sequentially develop strategy, campaigns, and copy
4. **Review**: Human stakeholder reviews and approves the drafted strategy
5. **Report**: Final executive summary is generated and displayed
6. **Download**: Marketing strategy document ready for use

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
│   │   └── agents.py              ← All 6 LangGraph agent nodes with prompts
│   ├── graph/
│   │   ├── state.py               ← TypedDict state (research, brief, strategy, campaigns, copy, etc.)
│   │   └── workflow.py            ← StateGraph + human interrupt checkpoint + error handling
│   ├── tools/
│   │   └── search.py              ← Serper API search wrapper for market research
│   ├── config/
│   │   └── logging_config.py      ← Comprehensive logging setup (app, agents, tokens, performance)
│   ├── prompts/
│   │   └── prompts.py             ← System prompts for each agent (6 specialized prompts)
│   ├── __init__.py
│   └── main.py                    ← FastAPI application + REST endpoints
├── frontend/
│   ├── templates/
│   │   ├── base.html              ← Base template with navigation
│   │   ├── index.html             ← Input form for product/service
│   │   ├── processing.html        ← Live status during agent execution
│   │   ├── review.html            ← Human review checkpoint interface
│   │   ├── result.html            ← Display final marketing strategy
│   │   └── error.html             ← Error handling page
│   └── static/
│       ├── css/style.css          ← Dark editorial design, responsive UI
│       └── js/main.js             ← Real-time processing updates
├── logs/
│   ├── app.log                    ← General application events
│   ├── agents.log                 ← Agent execution details
│   ├── token_usage.log            ← API token tracking for cost analysis
│   └── performance.log            ← Execution timing metrics
├── .env.example                   ← Template for environment variables
├── requirements.txt               ← Python dependencies
├── run.py                         ← Application entry point
└── README.md                      ← This file
```

### Key Directories

- **backend/agents**: Core AI agents that process information at each stage
- **backend/graph**: LangGraph state management and workflow orchestration
- **backend/tools**: External API integrations (Serper for web search)
- **backend/config**: Logging and configuration utilities
- **frontend/templates**: Jinja2 HTML templates for web UI
- **logs**: Persistent logs for debugging and performance monitoring

---

## Configuration & Environment Variables

Create a `.env` file in the `stratoviqueai/` directory:

```env
# LLM Configuration
GEMINI_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini-2.0-flash

# Search Configuration
SERPER_API_KEY=your_serper_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=False
```

### Model Selection

Choose the appropriate Gemini model based on your needs:

| Model | Speed | Quality | Cost | Use Case |
|-------|-------|---------|------|----------|
| **gemini-2.0-flash** | ⚡⚡⚡ (fastest) | ✓✓ (good) | Free tier friendly | Default, fast prototyping |
| **gemini-2.5-pro** | ⚡⚡ (fast) | ✓✓✓ (excellent) | Recommended for client presentations and high-quality output |
| **gemini-1.5-flash** | ⚡⚡⚡ (ultra-fast) | ✓ (basic) | Ultra-light workloads | Quick testing, lightweight environments |

---

## API Endpoints

StratoviqueAI provides REST API endpoints for programmatic integration:

### Web Interface
- **GET** `/` — Main web interface with input form
- **GET** `/status` — Check application health status

### API Endpoints
- **POST** `/api/strategy` — Submit marketing strategy request
- **GET** `/api/strategy/{task_id}` — Retrieve strategy results
- **GET** `/api/review/{task_id}` — Get pending human review
- **POST** `/api/review/{task_id}/approve` — Approve strategy for report generation
- **GET** `/api/logs` — Retrieve system logs

### Example Usage

```bash
# Submit a strategy request
curl -X POST http://localhost:8000/api/strategy \
  -H "Content-Type: application/json" \
  -d '{"product": "AI-powered fitness app targeting busy professionals"}'

# Check status
curl http://localhost:8000/api/strategy/task_123

# Approve strategy
curl -X POST http://localhost:8000/api/review/task_123/approve
```

---

## Logging & Performance Monitoring

The application maintains comprehensive logs in the `logs/` directory:

### Log Files

- **app.log** — General application events, errors, and state changes
- **agents.log** — Detailed agent execution logs with input/output
- **token_usage.log** — API token consumption tracking for cost analysis
- **performance.log** — Execution timing for each operation

### Viewing Logs

```cmd
# Watch logs in real-time (Windows PowerShell)
Get-Content logs\app.log -Wait

# View token usage
type logs\token_usage.log

# Performance metrics
type logs\performance.log
```

---

## Use Cases

### Marketing Teams
Generate comprehensive go-to-market strategies for new products or services without hiring external agencies.

### Product Managers
Quickly validate market positioning and identify competitive opportunities before product launch.

### Startups
Create professional marketing strategies from minimal input—perfect for early-stage companies with limited resources.

### Consultants
Use as a foundation for client strategy work, then customize and refine the AI-generated baseline.

### Content Creators
Generate campaign concepts and copy variations for social media, email, and ads.

---

## Troubleshooting

### "API Key Error" or Unauthorized
- Verify your API keys in `.env` are correct
- Ensure your GEMINI_API_KEY has been created at [aistudio.google.com](https://aistudio.google.com/app/apikey)
- Check that Serper API key has quota remaining at [serper.dev](https://serper.dev)

### "Connection Timeout" or "Port Already in Use"
```cmd
# Change the port in .env (default 8000)
PORT=8001

# Or kill existing process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Agent Execution Hangs
- Check internet connection for API access
- Verify API rate limits haven't been exceeded
- Increase timeout in `workflow.py` if needed
- Review logs in `logs/agents.log` for specific errors

### Low-Quality Outputs
- Switch to `gemini-2.5-pro` model for better results
- Try different product descriptions or be more specific
- Ensure Serper searches are returning relevant results

---

## Development

### Running in Development Mode

```cmd
# Enable debug logging
set DEBUG=True

# Run with auto-reload
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Adding Custom Agents

Edit `backend/agents/agents.py` to add new agent nodes:
1. Define agent function with `@node` decorator
2. Update `state.py` with new state fields
3. Add routing in `backend/graph/workflow.py`

### Creating New Tools

Add new tools in `backend/tools/`:
1. Create wrapper function for external API
2. Import and register in `backend/agents/agents.py`
3. Update prompts to guide agents on tool usage

---

## Performance Considerations

- **Execution Time**: Typical workflow takes 2-5 minutes depending on model and search queries
- **Token Usage**: Average request uses ~10,000-15,000 tokens (Gemini free tier: 1,500 requests/day)
- **Memory**: Application requires ~500MB RAM baseline
- **Concurrency**: Currently supports sequential processing; async enhancement possible

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **LLM** | Google Gemini | Core AI inference engine |
| **Orchestration** | LangGraph | Multi-agent workflow coordination |
| **Search** | Serper API | Market research and competitor analysis |
| **Backend** | FastAPI | REST API and server |
| **Frontend** | Jinja2 + HTML/CSS/JS | Web user interface |
| **Logging** | Python logging | Performance and debugging |

---

## License & Attribution

© 2025 StratoviqueAI. All rights reserved.

Built upon concepts from [crewAI marketing strategy example](https://github.com/crewAIInc/crewAI-examples/tree/main/crews/marketing_strategy), enhanced with LangGraph orchestration, human oversight, and production-ready architecture.

---

## Contributing

Contributions welcome! Areas for enhancement:
- Additional specialized agents (competitive analysis, pricing strategy, etc.)
- Multi-language support
- Advanced reporting formats (PDF, PPTX)
- Analytics dashboard
- Integration with CRM/marketing automation platforms

---

## Support

For issues, questions, or feature requests, please open an issue in the repository.
