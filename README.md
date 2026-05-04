# AgentOps 🤖
### Multi-Agent PR Review Assistant | Free to Build & Run

> LangGraph · Gemini Pro (free) · Groq (free) · FastAPI · GitHub API

---

## What it does

Opens a GitHub PR → webhook fires → 4 agents analyze it in parallel → structured review posted back as a PR comment, with a human-in-the-loop approval gate.

**Agents:**
| Agent | Does | LLM |
|---|---|---|
| Orchestrator | Plans which agents to run | Groq Llama 70B (free, fast) |
| Code Reviewer | Bugs, logic, quality | Gemini Pro (free) |
| Security Scanner | OWASP, secrets, injection | Gemini Pro + rule-based fallback |
| Test Analyzer | Coverage gaps, missing tests | Gemini Pro (free) |
| Synthesis | Merges, formats, confidence gates | Pure Python |

---

## Setup (5 minutes)

### 1. Clone & install
```bash
git clone https://github.com/your-username/agentops
cd agentops
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. Get your free API keys
| Service | Where | Cost |
|---|---|---|
| Gemini Pro | [aistudio.google.com](https://aistudio.google.com) | Free |
| Groq | [console.groq.com](https://console.groq.com) | Free |
| GitHub Token | Settings → Developer Settings → PAT | Free |

### 3. Configure
```bash
cp .env.example .env
# Fill in GEMINI_API_KEY, GROQ_API_KEY, GITHUB_TOKEN
```

### 4. Run locally
```bash
uvicorn api.main:app --reload --port 8000
```

### 5. Expose with ngrok (for GitHub webhook)
```bash
ngrok http 8000
# Copy the https URL → GitHub repo → Settings → Webhooks
# Payload URL: https://your-ngrok-url/webhook/github
# Content type: application/json
# Events: Pull requests
```

---

## Swap LLM in one line

```python
# .env
LLM_PROVIDER=gemini   # free Gemini Pro
LLM_PROVIDER=claude   # Claude Sonnet 4.6 ($3/M tokens)
LLM_PROVIDER=groq     # Groq Llama 70B (free, faster)
```

---

## Architecture

```
GitHub PR → Webhook → FastAPI
                         │
                    Orchestrator (Groq — fast routing)
                    ┌────┼────┐
               Code  Sec  Test  (parallel, Gemini Pro)
                    └────┼────┘
                      Synthesis
                         │
              Human-in-the-loop dashboard
                         │
                  GitHub PR comment
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/webhook/github` | GitHub webhook receiver |
| GET | `/reviews/{owner}/{repo}/{pr}` | Fetch stored review |
| POST | `/reviews/{owner}/{repo}/{pr}/approve` | Approve & post to GitHub |
| GET | `/health` | Health check |

---

## Stack
- **Agents**: LangGraph state machine
- **LLM**: Gemini 2.0 Pro (free) + Groq Llama 70B (free routing)
- **Backend**: FastAPI + Uvicorn
- **DB**: SQLite (local) → Supabase Postgres (production)
- **GitHub**: PyGithub + webhooks
- **Hosting**: Railway free tier
# testing agentops agents
.
