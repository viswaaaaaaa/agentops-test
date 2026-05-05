"""
Agent Pipeline (LangGraph)
--------------------------
Sequential chain: orchestrator → code_reviewer → security_scanner → test_analyzer → synthesis
Each agent self-skips if it's not in the orchestrator's task list.
"""
from langgraph.graph import StateGraph, END
from core.state import AgentState
from agents.orchestrator     import orchestrator_node
from agents.code_reviewer    import code_reviewer_node
from agents.security_scanner import security_scanner_node
from agents.test_analyzer    import test_analyzer_node
from agents.synthesis        import synthesis_node


def build_pipeline() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("orchestrator",     orchestrator_node)
    graph.add_node("code_reviewer",    code_reviewer_node)
    graph.add_node("security_scanner", security_scanner_node)
    graph.add_node("test_analyzer",    test_analyzer_node)
    graph.add_node("synthesis",        synthesis_node)

    # Sequential — agents self-skip via "if not in tasks" check
    graph.set_entry_point("orchestrator")
    graph.add_edge("orchestrator",     "code_reviewer")
    graph.add_edge("code_reviewer",    "security_scanner")
    graph.add_edge("security_scanner", "test_analyzer")
    graph.add_edge("test_analyzer",    "synthesis")
    graph.add_edge("synthesis",        END)

    return graph.compile()


pipeline = build_pipeline()


def run_pipeline(pr_data: dict) -> dict:
    initial_state: AgentState = {
        "pr_number":     pr_data["pr_number"],
        "repo_full":     pr_data["repo_full"],
        "pr_title":      pr_data["pr_title"],
        "pr_body":       pr_data.get("pr_body", ""),
        "diff":          pr_data["diff"],
        "changed_files": pr_data.get("changed_files", []),
        "tasks":         [],
        "errors":        [],
        "code_review":   None,
        "security_scan": None,
        "test_analysis": None,
        "final_review":  None,
        "posted":        False,
    }
    return pipeline.invoke(initial_state)