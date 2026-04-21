"""
AI Governance リポジトリ

org_database の低レベル関数をラップして
エージェント・タスク操作の骨格を提供する。
"""

from __future__ import annotations

from typing import Optional

import org_database as db
from models.types import TaskMode, TaskStatus


class AiCeoRepo:
    def setup(self, user_id: str, reports_to_user_id: str,
              persona: dict | None = None,
              decision_authority: dict | None = None) -> str:
        return db.create_ai_ceo_profile(
            user_id, reports_to_user_id, persona, decision_authority
        )

    def get(self) -> dict | None:
        return db.get_ai_ceo_profile()


class AgentRepo:
    """AIエージェント操作"""

    def register(self, user_id: str, agent_type: str,
                 reports_to_id: str = "",
                 model: str = "claude-sonnet-4-6",
                 system_prompt: str = "",
                 config: dict | None = None,
                 capabilities: list[str] | None = None,
                 brand_ids: list[str] | None = None) -> str:
        agent_id = db.create_ai_agent(
            user_id, agent_type, reports_to_id, model, system_prompt, config
        )
        for cap in capabilities or []:
            db.add_agent_capability(agent_id, cap)
        for i, brand_id in enumerate(brand_ids or []):
            db.assign_agent_to_brand(agent_id, brand_id, is_primary=(i == 0))
        return agent_id

    def get(self, agent_id: str) -> dict | None:
        return db.get_ai_agent(agent_id)

    def list_active(self) -> list[dict]:
        return db.list_ai_agents(active_only=True)

    def add_capability(self, agent_id: str, capability: str,
                       config: dict | None = None):
        db.add_agent_capability(agent_id, capability, config)

    def assign_brand(self, agent_id: str, brand_id: str,
                     is_primary: bool = False):
        db.assign_agent_to_brand(agent_id, brand_id, is_primary=is_primary)


class TaskRepo:
    """エージェントタスク操作"""

    def create(
        self,
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
        tid = db.create_task(
            title=title, mode=mode,
            assigned_to_agent_id=assigned_to_agent_id,
            requested_by_user_id=requested_by_user_id,
            brand_id=brand_id, description=description,
            priority=priority, input_data=input_data,
            scheduled_at=scheduled_at,
        )
        for dep_id in depends_on or []:
            db.add_task_dependency(tid, dep_id)
        return tid

    def update_status(self, task_id: str, status: TaskStatus,
                      error_message: str = "", output_data: dict | None = None):
        db.update_task_status(task_id, status, error_message, output_data)

    def get(self, task_id: str) -> dict | None:
        return db.get_task(task_id)

    def list(self, status: str = "", agent_id: str = "",
             brand_id: str = "", limit: int = 100) -> list[dict]:
        return db.list_tasks(status, agent_id, brand_id, limit)

    def get_dependencies(self, task_id: str) -> list[dict]:
        return db.get_task_dependencies(task_id)

    def get_blockers(self, task_id: str) -> list[dict]:
        return db.get_blocking_tasks(task_id)

    def is_runnable(self, task_id: str) -> bool:
        """依存タスクが全て完了しているか"""
        return len(self.get_blockers(task_id)) == 0


class RunRepo:
    def start(self, task_id: str, agent_id: str) -> str:
        return db.start_run(task_id, agent_id)

    def finish(self, run_id: str, status: str = "completed",
               log_entries: list | None = None,
               tokens_used: int = 0, cost_usd: float = 0,
               error_message: str = ""):
        db.finish_run(run_id, status, log_entries, tokens_used, cost_usd, error_message)


class EscalationRepo:
    def create(self, task_id: str, reason: str,
               agent_id: str = "", escalated_to_user_id: str = "",
               context: dict | None = None) -> str:
        return db.create_escalation(task_id, reason, agent_id, escalated_to_user_id, context)

    def list_open(self) -> list[dict]:
        return db.list_escalations(status="open")


class ApprovalRepo:
    def request(self, task_id: str, title: str,
                requested_by_agent_id: str = "",
                description: str = "",
                approver_user_ids: list[str] | None = None,
                expires_at: str = "") -> str:
        return db.create_approval(
            task_id, title, requested_by_agent_id,
            description, approver_user_ids, expires_at
        )

    def decide(self, approval_id: str, approver_user_id: str,
               decision: str, comment: str = ""):
        db.decide_approval_step(approval_id, approver_user_id, decision, comment)
