"""
Agent State
-----------
Shared typed state that flows through the entire LangGraph pipeline.
Every agent reads from and writes to this object.
"""
from typing import TypedDict, Optional
from dataclasses import dataclass, field


class AgentState(TypedDict):
    # ── Input ──────────────────────────────────────────────────────
    pr_number:    int
    repo_full:    str          # e.g. "owner/repo"
    pr_title:     str
    pr_body:      str
    diff:         str          # full unified diff text
    changed_files: list[str]

    # ── Agent findings ─────────────────────────────────────────────
    code_review:   Optional[dict]   # {findings: [...], confidence: float}
    security_scan: Optional[dict]
    test_analysis: Optional[dict]

    # ── Orchestration ──────────────────────────────────────────────
    tasks:         list[str]        # agents the orchestrator decided to run
    errors:        list[str]        # non-fatal errors during pipeline

    # ── Final output ───────────────────────────────────────────────
    final_review:  Optional[dict]   # synthesized result ready to post
    posted:        bool             # True once comment is posted to GitHub


@dataclass
class Finding:
    """Single finding from any agent."""
    severity:    str      # "critical" | "major" | "minor" | "info"
    category:    str      # "bug" | "security" | "test" | "style"
    file:        str
    line:        Optional[int]
    message:     str
    suggestion:  str
    confidence:  float    # 0.0 – 1.0

    def to_dict(self) -> dict:
        return {
            "severity":   self.severity,
            "category":   self.category,
            "file":       self.file,
            "line":       self.line,
            "message":    self.message,
            "suggestion": self.suggestion,
            "confidence": self.confidence,
        }
