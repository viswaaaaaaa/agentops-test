"""
Security Scanner Agent
----------------------
Checks for OWASP Top 10 vulnerabilities, hardcoded secrets,
injection risks, and insecure patterns.
Falls back to regex-based pattern matching when LLM confidence is low.
"""
import re
import json
from langchain.schema import HumanMessage, SystemMessage
from core.llm import get_llm
from core.state import AgentState
from core.config import CONFIDENCE_THRESHOLD

SYSTEM_PROMPT = """You are a security-focused code reviewer specializing in OWASP Top 10.
Analyze the diff for security vulnerabilities.

Respond ONLY with valid JSON:
{
  "findings": [
    {
      "severity": "critical|major|minor",
      "category": "injection|secrets|auth|crypto|xss|idor|misconfig",
      "file": "path/to/file.py",
      "line": 42,
      "message": "Description of vulnerability",
      "suggestion": "How to fix it",
      "owasp": "A03:2021 - Injection",
      "confidence": 0.92
    }
  ],
  "secrets_found": false,
  "summary": "Security review summary"
}

Focus on:
- SQL/command/LDAP injection (A03)
- Hardcoded secrets, API keys, passwords (A02)
- Broken authentication (A07)
- Insecure direct object references (A01)
- Cryptographic failures — MD5, SHA1, weak keys (A02)
- XSS in templates or rendered output (A03)
- Missing input validation
- Dangerous functions: eval(), exec(), os.system(), subprocess with shell=True
"""

# Regex patterns for rule-based fallback
SECRET_PATTERNS = [
    (r'(?i)(password|passwd|pwd)\s*=\s*["\'][^"\']{4,}["\']',     "Hardcoded password"),
    (r'(?i)(api_key|apikey|secret_key)\s*=\s*["\'][^"\']{8,}["\']',"Hardcoded API key"),
    (r'(?i)Bearer\s+[A-Za-z0-9\-_]{20,}',                          "Hardcoded token"),
    (r'(?i)(aws_access_key_id|aws_secret)\s*=\s*["\'][^"\']+["\']',"AWS credential"),
]

DANGEROUS_PATTERNS = [
    (r'eval\s*\(',             "Use of eval()"),
    (r'exec\s*\(',             "Use of exec()"),
    (r'shell\s*=\s*True',      "subprocess with shell=True"),
    (r'\.raw\s*\(',            "Potential raw SQL"),
    (r'f["\'].*SELECT.*{',     "Possible SQL injection via f-string"),
]


def security_scanner_node(state: AgentState) -> AgentState:
    """Run security scan on the PR diff."""
    if "security_scanner" not in state.get("tasks", []):
        return state

    llm = get_llm()
    diff = state["diff"]

    # Rule-based scan first (always runs, catches obvious issues)
    rule_findings = _rule_based_scan(diff, state["changed_files"])

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"""
PR: {state['pr_title']}
Files: {', '.join(state['changed_files'])}

Diff:
{diff[:6000]}
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

        llm_findings = result.get("findings", [])

        # merge — rule-based findings are always high confidence
        all_findings = rule_findings + [
            f for f in llm_findings
            if f.get("confidence", 0) >= CONFIDENCE_THRESHOLD
        ]
        low_conf = [
            {**f, "needs_human_review": True}
            for f in llm_findings
            if f.get("confidence", 0) < CONFIDENCE_THRESHOLD
        ]

        security_scan = {
            "findings":      all_findings + low_conf,
            "secrets_found": result.get("secrets_found", len(rule_findings) > 0),
            "summary":       result.get("summary", ""),
            "confidence":    0.95 if rule_findings else _avg_confidence(llm_findings),
        }

    except Exception as e:
        security_scan = {
            "findings":      rule_findings,
            "secrets_found": len(rule_findings) > 0,
            "summary":       "LLM scan failed — rule-based scan only",
            "confidence":    0.8 if rule_findings else 0.0,
            "error":         str(e),
        }
        state["errors"] = state.get("errors", []) + [f"Security scanner error: {e}"]

    return {**state, "security_scan": security_scan}


def _rule_based_scan(diff: str, files: list[str]) -> list[dict]:
    findings = []
    lines = diff.split("\n")
    for i, line in enumerate(lines):
        if not line.startswith("+"):
            continue
        code = line[1:]
        for pattern, label in SECRET_PATTERNS:
            if re.search(pattern, code):
                findings.append({
                    "severity":   "critical",
                    "category":   "secrets",
                    "file":       _guess_file(files, i, lines),
                    "line":       i + 1,
                    "message":    f"Rule-based detection: {label}",
                    "suggestion": "Use environment variables or a secrets manager",
                    "confidence": 0.95,
                    "source":     "rule_based",
                })
        for pattern, label in DANGEROUS_PATTERNS:
            if re.search(pattern, code):
                findings.append({
                    "severity":   "major",
                    "category":   "injection",
                    "file":       _guess_file(files, i, lines),
                    "line":       i + 1,
                    "message":    f"Dangerous pattern: {label}",
                    "suggestion": "Review and replace with a safer alternative",
                    "confidence": 0.85,
                    "source":     "rule_based",
                })
    return findings


def _guess_file(files: list[str], line_idx: int, lines: list[str]) -> str:
    for j in range(line_idx, -1, -1):
        if lines[j].startswith("diff --git"):
            parts = lines[j].split(" b/")
            if len(parts) > 1:
                return parts[1]
    return files[0] if files else "unknown"


def _avg_confidence(findings: list) -> float:
    if not findings:
        return 1.0
    return round(sum(f.get("confidence", 0) for f in findings) / len(findings), 2)
