"""
Test Analyzer Agent
-------------------
Identifies missing tests, coverage gaps, and untested edge cases.
"""
import json
from langchain.schema import HumanMessage, SystemMessage
from core.llm import get_llm
from core.state import AgentState
from core.config import CONFIDENCE_THRESHOLD

SYSTEM_PROMPT = """You are a test coverage expert. Analyze the PR diff and identify testing gaps.

Respond ONLY with valid JSON:
{
  "findings": [
    {
      "severity": "major|minor|info",
      "category": "missing_test|edge_case|integration|regression",
      "file": "path/to/file.py",
      "line": null,
      "message": "Description of what is not tested",
      "suggestion": "Specific test case to add",
      "confidence": 0.88
    }
  ],
  "test_coverage_estimate": "good|partial|poor|none",
  "summary": "Testing assessment summary"
}

Look for:
- New functions or methods with no corresponding test file changes
- Edge cases not covered: empty inputs, None, large values, error paths
- Missing integration tests when multiple components interact
- Regression risks — changed logic with no test update
- Happy-path-only tests missing error case coverage

If test files are also changed and coverage looks good, say so.
"""


def test_analyzer_node(state: AgentState) -> AgentState:
    """Run test coverage analysis on the PR diff."""
    if "test_analyzer" not in state.get("tasks", []):
        return state

    llm = get_llm()

    has_test_changes = any(
        "test" in f.lower() or "spec" in f.lower()
        for f in state["changed_files"]
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"""
PR: {state['pr_title']}
Files changed: {', '.join(state['changed_files'])}
Test files included in PR: {has_test_changes}

Diff:
{state['diff'][:6000]}
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

        findings = result.get("findings", [])
        high_conf = [f for f in findings if f.get("confidence", 0) >= CONFIDENCE_THRESHOLD]
        low_conf  = [{**f, "needs_human_review": True}
                     for f in findings if f.get("confidence", 0) < CONFIDENCE_THRESHOLD]

        test_analysis = {
            "findings":               high_conf + low_conf,
            "test_coverage_estimate": result.get("test_coverage_estimate", "unknown"),
            "summary":                result.get("summary", ""),
            "has_test_changes":       has_test_changes,
            "confidence":             _avg_confidence(findings),
        }

    except Exception as e:
        test_analysis = {
            "findings":               [],
            "test_coverage_estimate": "unknown",
            "summary":                "Test analysis failed — manual review recommended",
            "confidence":             0.0,
            "error":                  str(e),
        }
        state["errors"] = state.get("errors", []) + [f"Test analyzer error: {e}"]

    return {**state, "test_analysis": test_analysis}


def _avg_confidence(findings: list) -> float:
    if not findings:
        return 1.0
    return round(sum(f.get("confidence", 0) for f in findings) / len(findings), 2)
