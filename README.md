# AgentOps 🤖
### Multi-Agent AI Code Review System

[![Python](https://img.shields.io/badge/Python-3.13-blue)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.28-green)](https://langchain-ai.github.io/langgraph/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)](https://fastapi.tiangolo.com)
[![Groq](https://img.shields.io/badge/Groq-Llama3.3_70B-orange)](https://groq.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

> An autonomous multi-agent system that reviews GitHub Pull Requests in real-time — detecting bugs, security vulnerabilities, and test coverage gaps using LangGraph orchestration and LLM-powered analysis.

---

## 🎯 Demo

![AgentOps Demo](assets/demo.png)

**Real output on a PR with intentional vulnerabilities:**
- 🔴 CRITICAL — Hardcoded secret key detected (99% confidence)
- 🔴 CRITICAL — `eval()` enables code injection attacks (99% confidence)
- 🔴 CRITICAL — SQL injection via string formatting (99% confidence)

---

## 🏗️ Architecture

```
GitHub PR opened
      │
      ▼
GitHub Webhook → FastAPI
      │
      ▼
Orchestrator Agent (decides which agents to run)
      │
      ├──► Code Reviewer    (bugs, logic, quality)
      ├──► Security Scanner (OWASP, secrets, injection)
      └──► Test Analyzer    (coverage gaps, missing tests)
      │
      ▼
Synthesis Agent (merges findings, scores severity)
      │
      ▼
Human-in-the-loop approval gate
      │
      ▼
GitHub PR Comment posted
```

---

## ✨ Key Features

- **Multi-agent orchestration** via LangGraph state machine — each agent specializes in a specific review domain
- **Confidence scoring** — findings below threshold are flagged for human review instead of auto-posted
- **Fallback routing** — Security Scanner uses rule-based regex as fallback when LLM confidence is low
- **Human-in-the-loop** — all reviews require human approval before posting to GitHub
- **Swappable LLM** — switch between Groq, Gemini, or Claude with one config change
- **Persistent storage** — all reviews stored in SQLite (local) / Supabase Postgres (production)

---

## 🤖 Agent Breakdown

| Agent | Responsibility | Model |
|---|---|---|
| Orchestrator | Plans which agents to run based on diff | Groq Llama 3.3 70B |
| Code Reviewer | Bugs, logic errors, code quality | Groq Llama 3.3 70B |
| Security Scanner | OWASP Top 10, secrets, injection risks | Groq + rule-based fallback |
| Test Analyzer | Coverage gaps, missing test cases | Groq Llama 3.3 70B |
| Synthesis | Merges findings, formats GitHub comment | Pure Python |

---

## 🚀 Quick Start

### 1. Clone & install
```bash
git clone https://github.com/viswaaaaaaa/agentops-test
cd agentops-test
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. Get free API keys
| Service | Link | Cost |
|---|---|---|
| Groq (LLM) | [console.groq.com](https://console.groq.com) | Free |
| GitHub Token | Settings → Developer settings → PAT (classic) → `repo` scope | Free |

### 3. Configure
```bash
cp .env.example .env
# Fill in GROQ_API_KEY and GITHUB_TOKEN
```

### 4. Run
```bash
uvicorn api.main:app --reload --port 8000
ngrok http 8000  # expose to GitHub webhooks
```

### 5. Connect GitHub webhook
- Go to your repo → Settings → Webhooks → Add webhook
- Payload URL: `https://your-ngrok-url/webhook/github`
- Content type: `application/json`
- Events: Pull requests

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/webhook/github` | GitHub webhook receiver |
| GET | `/reviews/{owner}/{repo}/{pr}` | Fetch stored review |
| POST | `/reviews/{owner}/{repo}/{pr}/approve` | Approve & post to GitHub |
| GET | `/health` | Health check |

---

## 🔧 Swap LLM in one line

```bash
# .env
LLM_PROVIDER=groq    # Free, 14,400 req/day (default)
LLM_PROVIDER=gemini  # Free tier available
LLM_PROVIDER=claude  # Best quality, paid
```

---

## 📁 Project Structure

```
agentops/
├── agents/
│   ├── orchestrator.py      # Plans agent tasks
│   ├── code_reviewer.py     # Bug & quality analysis
│   ├── security_scanner.py  # Security vulnerability detection
│   ├── test_analyzer.py     # Test coverage analysis
│   └── synthesis.py         # Merges & formats findings
├── core/
│   ├── config.py            # Single config, swap LLM here
│   ├── llm.py               # LLM factory (Groq/Gemini/Claude)
│   ├── pipeline.py          # LangGraph state machine
│   └── state.py             # Typed shared state
├── api/
│   ├── main.py              # FastAPI app + webhook handler
│   └── db.py                # SQLite storage layer
└── requirements.txt
```

---

## 🛠️ Tech Stack

- **Agent Framework:** LangGraph (stateful multi-agent orchestration)
- **LLM:** Groq Llama 3.3 70B (free tier)
- **Backend:** FastAPI + Uvicorn
- **Database:** SQLite (local) → Supabase Postgres (production)
- **GitHub Integration:** PyGithub + Webhooks
- **Deployment:** Railway

## ⚠️ Security Notes

- **Never commit `.env`** — it contains your API keys
- `.gitignore` is configured to exclude `.env`, `venv/`, and `*.db`
- Use `.env.example` as a template (safe to commit, no real keys)
- If you accidentally push a key, **revoke it immediately** on the provider's dashboard

---

## 📄 License

MIT License — feel free to use this for your own projects.