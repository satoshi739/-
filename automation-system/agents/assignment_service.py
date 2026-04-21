"""
Agent Assignment Service
Selects the most appropriate AI agent for a task.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

import org_database as db

log = logging.getLogger(__name__)


def find_best_agent(task: dict) -> Optional[str]:
    """
    Priority order:
    1. Already-assigned active agent — keep it.
    2. Active agent with primary assignment to the task's brand.
    3. Active agent assigned (non-primary) to the brand.
    4. Any active agent (fallback).
    Returns agent_id or None.
    """
    # 1. Already assigned
    current_id = task.get("assigned_to_agent_id")
    if current_id:
        agent = db.get_ai_agent(current_id)
        if agent and agent.get("is_active"):
            return current_id

    brand_id = task.get("brand_id", "")
    all_agents = db.list_ai_agents(active_only=True)
    if not all_agents:
        return None

    if brand_id:
        with db.get_conn() as conn:
            # Primary assignment first
            row = conn.execute(
                """SELECT agent_id FROM agent_assignments
                   WHERE brand_id=? AND is_primary=1 LIMIT 1""",
                (brand_id,),
            ).fetchone()
            if row:
                agent = db.get_ai_agent(row["agent_id"])
                if agent and agent.get("is_active"):
                    return row["agent_id"]
            # Non-primary
            row = conn.execute(
                "SELECT agent_id FROM agent_assignments WHERE brand_id=? LIMIT 1",
                (brand_id,),
            ).fetchone()
            if row:
                agent = db.get_ai_agent(row["agent_id"])
                if agent and agent.get("is_active"):
                    return row["agent_id"]

    # 4. Fallback
    return all_agents[0]["id"]


def assign(task_id: str, agent_id: str) -> bool:
    """Assign agent to task. Returns True on success."""
    task = db.get_task(task_id)
    agent = db.get_ai_agent(agent_id)
    if not task or not agent:
        return False
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with db.get_conn() as conn:
        conn.execute(
            "UPDATE agent_tasks SET assigned_to_agent_id=?, updated_at=? WHERE id=?",
            (agent_id, now, task_id),
        )
    log.info(f"Task {task_id} assigned to agent {agent_id}")
    return True


def auto_assign(task_id: str) -> Optional[str]:
    """Find + assign the best agent. Returns agent_id or None."""
    task = db.get_task(task_id)
    if not task:
        return None
    agent_id = find_best_agent(task)
    if agent_id:
        assign(task_id, agent_id)
    return agent_id
