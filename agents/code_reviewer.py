"""
Code Reviewer Agent
-------------------
Analyzes the PR diff for bugs, logic errors, code quality issues.
Returns structured findings with per-finding confidence scores.
Flags low-confidence findings for human review instead of posting them.
"""
import json
from langchain.schema import HumanMessage, SystemMessage
from core.llm import get_llm
from core.state import AgentState, Finding
from core.config import CONFIDENCE_THRESHOLD

SYSTEM_PROMPT = """You are an expert code reviewer. Analyze the provided diff and identify issues.

For each issue found, provide a structured finding. Respond ONLY with valid JSON:
{
  "findings": [
    {
      "severity": "critical|major|minor|info",
      "category": "bug|logic|performance|style|naming",
      "file": "path/to/file.py",
      "line": 42,
      "message": "Clear description of the problem",
      "suggestion": "Specific fix or improvement",
      "confidence": 0.95
    }
  ],
  "overall_quality": "good|needs_work|poor",
  "summary": "One sentence summary of the review"
}

Confidence scoring guide:
- 0.9–1.0: Definite bug or error, very clear
- 0.7–0.9: Likely issue, high confidence
- 0.5–0.7: Possible issue, uncertain context
- Below 0.5: Flag for human review, don't assert

Rules:
- Only report real issues, not style preferences unless egregious
- Be specific — include file name and line number when possible
- If the code looks fine, return an empty findings array
- Do NOT hallucinate issues that aren't in the diff
"""


def code_reviewer_node(state: AgentState) -> AgentState:
    """Run code review on the PR diff."""
    if "code_reviewer" not in state.get("tasks", []):
        return state

    llm = get_llm()

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"""
PR: {state['pr_title']}
Files changed: {', '.join(state['changed_files'])}

Full diff:
{state['diff'][:8000]}
"""),
    ]

    try:
        response = llm.invoke(messages)
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw)

        # split findings by confidence
        findings = result.get("findings", [])
        high_conf = [f for f in findings if f.get("confidence", 0) >= CONFIDENCE_THRESHOLD]
        low_conf  = [f for f in findings if f.get("confidence", 0) <  CONFIDENCE_THRESHOLD]

        # tag low-confidence findings for human review
        for f in low_conf:
            f["needs_human_review"] = True

        code_review = {
            "findings":       high_conf + low_conf,
            "overall_quality": result.get("overall_quality", "unknown"),
            "summary":        result.get("summary", ""),
            "confidence":     _avg_confidence(findings),
        }

    except Exception as e:
        code_review = {
            "findings":  [],
            "summary":   "Code review failed — manual review recommended",
            "confidence": 0.0,
            "error":     str(e),
        }
        state["errors"] = state.get("errors", []) + [f"Code reviewer error: {e}"]

    return {**state, "code_review": code_review}


def _avg_confidence(findings: list) -> float:
    if not findings:
        return 1.0
    return round(sum(f.get("confidence", 0) for f in findings) / len(findings), 2)
