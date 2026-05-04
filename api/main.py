"""
FastAPI Application
-------------------
Endpoints:
  POST /webhook/github    — receives GitHub PR events
  GET  /reviews/{pr}      — fetch stored review for a PR
  POST /reviews/{pr}/approve  — human approves and posts review
  POST /reviews/{pr}/edit     — human edits then posts review
  GET  /health            — health check
"""
import hmac
import hashlib
import json
import asyncio
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from github import Github, GithubException

from core.config import GITHUB_TOKEN, GITHUB_WEBHOOK_SECRET
from core.pipeline import run_pipeline
from api.db import save_review, get_review, mark_posted

app = FastAPI(title="AgentOps", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

gh = Github(GITHUB_TOKEN)


# ── Webhook ───────────────────────────────────────────────────────

@app.post("/webhook/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """Receive GitHub PR webhook and trigger agent pipeline."""
    payload = await request.body()

    # Verify signature
    if GITHUB_WEBHOOK_SECRET:
        sig = request.headers.get("X-Hub-Signature-256", "")
        expected = "sha256=" + hmac.new(
            GITHUB_WEBHOOK_SECRET.encode(), payload, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(sig, expected):
            raise HTTPException(status_code=401, detail="Invalid signature")

    event = request.headers.get("X-GitHub-Event", "")
    data  = json.loads(payload)

    if event != "pull_request":
        return {"status": "ignored", "event": event}

    action = data.get("action", "")
    if action not in ("opened", "synchronize", "reopened"):
        return {"status": "ignored", "action": action}

    pr_data = await _extract_pr_data(data)
    background_tasks.add_task(_run_and_store, pr_data)

    return {"status": "accepted", "pr": pr_data["pr_number"]}


async def _run_and_store(pr_data: dict):
    """Run pipeline in background and store result."""
    try:
        result = await asyncio.to_thread(run_pipeline, pr_data)
        save_review(pr_data["repo_full"], pr_data["pr_number"], result)
    except Exception as e:
        print(f"Pipeline error: {e}")


async def _extract_pr_data(data: dict) -> dict:
    """Fetch PR diff from GitHub API."""
    repo_full  = data["repository"]["full_name"]
    pr_number  = data["pull_request"]["number"]
    pr_title   = data["pull_request"]["title"]
    pr_body    = data["pull_request"].get("body") or ""

    repo = gh.get_repo(repo_full)
    pr   = repo.get_pull(pr_number)

    diff_parts, changed_files = [], []
    for f in pr.get_files():
        changed_files.append(f.filename)
        if f.patch:
            diff_parts.append(f"diff --git a/{f.filename} b/{f.filename}\n{f.patch}")

    return {
        "pr_number":    pr_number,
        "repo_full":    repo_full,
        "pr_title":     pr_title,
        "pr_body":      pr_body,
        "diff":         "\n".join(diff_parts),
        "changed_files": changed_files,
    }


# ── Review endpoints ──────────────────────────────────────────────

@app.get("/reviews/{repo_owner}/{repo_name}/{pr_number}")
def get_review_endpoint(repo_owner: str, repo_name: str, pr_number: int):
    repo_full = f"{repo_owner}/{repo_name}"
    review = get_review(repo_full, pr_number)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review


class ApproveRequest(BaseModel):
    edited_body: str | None = None   # optional human edit


@app.post("/reviews/{repo_owner}/{repo_name}/{pr_number}/approve")
def approve_review(repo_owner: str, repo_name: str, pr_number: int, body: ApproveRequest):
    """Human approves — post the review to GitHub."""
    repo_full = f"{repo_owner}/{repo_name}"
    review = get_review(repo_full, pr_number)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    comment_body = body.edited_body or review["final_review"]["comment_body"]

    try:
        repo = gh.get_repo(repo_full)
        pr   = repo.get_pull(pr_number)
        pr.create_issue_comment(comment_body)
        mark_posted(repo_full, pr_number)
        return {"status": "posted"}
    except GithubException as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Health ────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}
