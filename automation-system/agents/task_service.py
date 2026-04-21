"""
Task Service — state machine and business logic for agent tasks.
All DB writes go through org_database; this layer enforces transition rules.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

import org_database as db
from models.types import TaskMode, TaskStatus

log = logging.getLogger(__name__)

# ── Valid state transitions ────────────────────────────────────
VALID_TRANSITIONS: dict[str, set[str]] = {
    "idle":             {"queued", "blocked"},
    "queued":           {"running", "blocked", "failed"},
    "running":          {"waiting_approval", "completed", "failed", "escalated"},
    "blocked":          {"queued"},
    "waiting_approval": {"running", "failed"},
    "escalated":        {"queued", "failed"},
    "completed":        set(),          # terminal
    "failed":           {"queued"},     # retry allowed
}

# Tasks that always need human-president sign-off
PRESIDENT_APPROVAL_PRIORITY_THRESHOLD = 2
APPROVAL_REQUIRED_MODES = {"human_approval_required"}


# ── CRUD ──────────────────────────────────────────────────────

def create_task(
    title: str,
    mode: TaskMode = "semi_auto",
    assigned_to_agent_id: str = "",
    requested_by_user_id: str = "",
    brand_id: str = "",
    description: str = "",
    priority: int = 5,
    input_data: dict | None = None,
    scheduled_at: str = "",
    depends_on: list[str] | None = None,
) -> str:
    """Create a task with optional dependency links. Returns task_id."""
    task_id = db.create_task(
        title=title, mode=mode,
        assigned_to_agent_id=assigned_to_agent_id,
        requested_by_user_id=requested_by_user_id,
        brand_id=brand_id, description=description,
        priority=priority, input_data=input_data or {},
        scheduled_at=scheduled_at,
    )
    for dep_id in (depends_on or []):
        if dep_id and dep_id != task_id:
            db.add_task_dependency(task_id, dep_id)
    log.info(f"Task created: {task_id!r} title={title!r} mode={mode}")
    return task_id


# ── State machine ─────────────────────────────────────────────

def transition(task_id: str, new_status: TaskStatus,
               error_message: str = "",
               output_data: dict | None = None) -> bool:
    """
    Apply a status transition.
    Returns True on success, False if the transition is not allowed.
    """
    task = db.get_task(task_id)
    if not task:
        log.warning(f"transition: task {task_id} not found")
        return False
    current = task["status"]
    allowed = VALID_TRANSITIONS.get(current, set())
    if new_status not in allowed:
        log.warning(f"Blocked transition {current!r} → {new_status!r} for task {task_id}")
        return False
    db.update_task_status(task_id, new_status, error_message, output_data)
    log.info(f"Task {task_id}: {current} → {new_status}")
    return True


def enqueue(task_id: str) -> bool:
    """
    Move idle/failed task to queued.
    If unresolved dependencies exist, move to blocked instead.
    """
    blockers = db.get_blocking_tasks(task_id)
    if blockers:
        return transition(task_id, "blocked")
    return transition(task_id, "queued")


def get_runnable_tasks(limit: int = 20) -> list[dict]:
    """Queued tasks whose every dependency is completed."""
    queued = db.list_tasks(status="queued", limit=limit)
    return [t for t in queued if not db.get_blocking_tasks(t["id"])]


def unblock_downstream(completed_task_id: str):
    """
    After a task completes, promote any tasks that were waiting
    only on it from blocked → queued.
    """
    with db.get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT task_id FROM agent_task_dependencies WHERE depends_on_task_id=?",
            (completed_task_id,),
        ).fetchall()
    for row in rows:
        tid = row["task_id"]
        t = db.get_task(tid)
        if not t or t["status"] != "blocked":
            continue
        if not db.get_blocking_tasks(tid):
            transition(tid, "queued")
            log.info(f"Task {tid} unblocked → queued")


# ── President-approval judgment ───────────────────────────────

def needs_president_approval(task: dict) -> bool:
    """
    True when the task requires the human president's explicit sign-off.
    Rules (any one triggers):
      1. mode = human_approval_required
      2. priority <= 2  (critical)
      3. input_data contains a 'budget' key
    """
    if task.get("mode") in APPROVAL_REQUIRED_MODES:
        return True
    if task.get("priority", 10) <= PRESIDENT_APPROVAL_PRIORITY_THRESHOLD:
        return True
    inp = task.get("input_data") or {}
    if isinstance(inp, dict) and "budget" in inp:
        return True
    return False


def get_task_with_context(task_id: str) -> dict | None:
    """Task dict enriched with blockers, deps, and approval flag."""
    task = db.get_task(task_id)
    if not task:
        return None
    task["blockers"] = db.get_blocking_tasks(task_id)
    task["deps"] = db.get_task_dependencies(task_id)
    task["president_approval_required"] = needs_president_approval(task)
    return task
