"""
Agent Pipeline (LangGraph)
--------------------------
Defines the multi-agent graph:

  orchestrator
       │
  ┌────┼────┐
  │    │    │
code  sec  test   (run in parallel based on orchestrator decision)
  │    │    │
  └────┼────┘
       │
   synthesis
       │
    [done]
"""
from langgraph.graph import StateGraph, END
from core.state import AgentState
from agents.orchestrator    import orchestrator_node
from agents.code_reviewer   import code_reviewer_node
from agents.security_scanner import security_scanner_node
from agents.test_analyzer   import test_analyzer_node
from agents.synthesis       import synthesis_node


def build_pipeline() -> StateGraph:
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("orchestrator",     orchestrator_node)
    graph.add_node("code_reviewer",    code_reviewer_node)
    graph.add_node("security_scanner", security_scanner_node)
    graph.add_node("test_analyzer",    test_analyzer_node)
    graph.add_node("synthesis",        synthesis_node)

    # Flow: orchestrator → all three agents (they self-skip if not in tasks)
    graph.set_entry_point("orchestrator")
    graph.add_edge("orchestrator",     "code_reviewer")
    graph.add_edge("orchestrator",     "security_scanner")
    graph.add_edge("orchestrator",     "test_analyzer")

    # All agents → synthesis
    graph.add_edge("code_reviewer",    "synthesis")
    graph.add_edge("security_scanner", "synthesis")
    graph.add_edge("test_analyzer",    "synthesis")

    graph.add_edge("synthesis", END)

    return graph.compile()


# Singleton pipeline instance
pipeline = build_pipeline()


def run_pipeline(pr_data: dict) -> dict:
    """
    Entry point called by the FastAPI webhook handler.
    pr_data must contain: pr_number, repo_full, pr_title, pr_body, diff, changed_files
    """
    initial_state: AgentState = {
        "pr_number":    pr_data["pr_number"],
        "repo_full":    pr_data["repo_full"],
        "pr_title":     pr_data["pr_title"],
        "pr_body":      pr_data.get("pr_body", ""),
        "diff":         pr_data["diff"],
        "changed_files": pr_data.get("changed_files", []),
        "tasks":        [],
        "errors":       [],
        "code_review":  None,
        "security_scan": None,
        "test_analysis": None,
        "final_review": None,
        "posted":       False,
    }

    result = pipeline.invoke(initial_state)
    return result
