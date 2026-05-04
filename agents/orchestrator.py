"""
Orchestrator Agent
------------------
Uses the fast LLM (Groq free tier) to plan which agents to invoke
based on the PR diff. This keeps routing cheap and fast.
"""
import json
from langchain.schema import HumanMessage, SystemMessage
from core.llm import get_fast_llm
from core.state import AgentState

SYSTEM_PROMPT = """You are an orchestrator for a multi-agent code review system.
Given a pull request diff, decide which specialist agents are needed.

Agents available:
- code_reviewer   : logic errors, bugs, code quality, style
- security_scanner: OWASP vulnerabilities, hardcoded secrets, injection risks
- test_analyzer   : missing tests, coverage gaps, untested edge cases

Respond ONLY with valid JSON — no explanation, no markdown:
{
  "tasks": ["code_reviewer", "security_scanner", "test_analyzer"],
  "reason": "one sentence rationale"
}

Rules:
- Always include code_reviewer
- Include security_scanner if diff touches auth, DB queries, file I/O, env vars, or network calls
- Include test_analyzer if diff adds/modifies functions without corresponding test changes
- Skip agents that clearly don't apply (e.g. skip security for a README-only change)
"""


def orchestrator_node(state: AgentState) -> AgentState:
    """Decide which agents to run based on the PR diff."""
    llm = get_fast_llm()

    diff_preview = state["diff"][:3000]  # keep routing call cheap
    changed = ", ".join(state["changed_files"][:20])

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"""
PR title: {state['pr_title']}
Changed files: {changed}

Diff preview:
{diff_preview}
"""),
    ]

    try:
        response = llm.invoke(messages)
        raw = response.content.strip()
        # strip accidental markdown fences
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw)
        tasks = result.get("tasks", ["code_reviewer"])
    except Exception as e:
        # safe fallback — run all agents
        tasks = ["code_reviewer", "security_scanner", "test_analyzer"]
        state["errors"] = state.get("errors", []) + [f"Orchestrator parse error: {e}"]

    return {**state, "tasks": tasks}
