"""
Organization リポジトリ

org_database の低レベル関数をラップして
ビジネスロジックに近いインターフェースを提供する。
"""

from __future__ import annotations

import org_database as db
from models.types import Organization, Brand, User, Role


class OrganizationRepo:
    """組織・ブランド・ユーザー操作"""

    # ── organizations ────────────────────────
    def get_or_create(self, name: str, slug: str, description: str = "") -> str:
        existing = db.get_organization_by_slug(slug)
        if existing:
            return existing["id"]
        return db.create_organization(name, slug, description)

    def list(self) -> list[dict]:
        return db.list_organizations()

    # ── brands ───────────────────────────────
    def get_or_create_brand(self, organization_id: str, name: str, slug: str,
                             short_name: str = "", color: str = "",
                             url: str = "", description: str = "") -> str:
        existing = db.get_brand_by_slug(slug)
        if existing:
            return existing["id"]
        return db.create_brand(organization_id, name, slug, short_name, color, url, description)

    def list_brands(self, organization_id: str = "") -> list[dict]:
        return db.list_brands(organization_id)

    # ── users ────────────────────────────────
    def create_user(self, organization_id: str, name: str,
                    user_type: str = "human", role_id: str = "",
                    email: str = "") -> str:
        return db.create_user(organization_id, name, user_type, role_id, email)

    def get(self, user_id: str) -> dict | None:
        return db.get_user(user_id)

    def list_humans(self) -> list[dict]:
        return db.list_users(user_type="human")

    def list_ai_users(self) -> list[dict]:
        return db.list_users(user_type="ai")

    # ── permissions ──────────────────────────
    def grant(self, user_id: str, brand_id: str, level: str = "read"):
        db.grant_brand_permission(user_id, brand_id, level)


class RoleRepo:
    """ロール管理"""

    DEFAULTS = [
        ("Human President", "human_president", 200, "最終意思決定者・オーナー"),
        ("AI CEO",          "ai_ceo",          100, "AI組織の最高執行責任者"),
        ("AI Agent",        "ai_agent",        10,  "専門タスクを担うAIエージェント"),
        ("Manager",         "manager",         50,  "人間マネージャー"),
        ("Member",          "member",          5,   "一般メンバー"),
    ]

    def seed_defaults(self):
        for name, slug, level, desc in self.DEFAULTS:
            db.create_role(name, slug, level, desc)

    def create(self, name: str, slug: str, level: int = 0,
               description: str = "") -> str:
        return db.create_role(name, slug, level, description)
