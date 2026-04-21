"""
型定義モジュール — organization / ai_governance

TypedDict で各テーブルの行型を定義する。
実行時の型チェックには使わず、IDE補完と可読性のために使う。
"""

from __future__ import annotations
from typing import Literal, Optional, TypedDict


# ─────────────────────────────────────────
# ENUMS (Literal types)
# ─────────────────────────────────────────

UserType = Literal["human", "ai"]

TaskMode = Literal["full_auto", "semi_auto", "human_approval_required"]

TaskStatus = Literal[
    "idle",
    "queued",
    "running",
    "blocked",
    "waiting_approval",
    "completed",
    "failed",
    "escalated",
]

PermissionLevel = Literal["read", "write", "admin"]

ApprovalStatus = Literal["pending", "approved", "rejected", "expired"]

EscalationStatus = Literal["open", "resolved", "ignored"]

DependencyType = Literal["finish_to_start", "start_to_start", "finish_to_finish"]


# ─────────────────────────────────────────
# organization
# ─────────────────────────────────────────

class Organization(TypedDict):
    id: str
    name: str
    slug: str
    description: Optional[str]
    created_at: str
    updated_at: Optional[str]


class Brand(TypedDict):
    id: str
    organization_id: str
    name: str
    slug: str
    short_name: Optional[str]
    color: Optional[str]
    url: Optional[str]
    description: Optional[str]
    created_at: str
    updated_at: Optional[str]


class Location(TypedDict):
    id: str
    brand_id: str
    name: str
    country: str
    city: Optional[str]
    address: Optional[str]
    timezone: str
    created_at: str
    updated_at: Optional[str]


class Role(TypedDict):
    id: str
    name: str
    slug: str
    description: Optional[str]
    level: int  # 0=agent, 50=manager, 100=ai_ceo, 200=human_president


class User(TypedDict):
    id: str
    organization_id: str
    role_id: Optional[str]
    user_type: UserType
    name: str
    email: Optional[str]
    avatar_url: Optional[str]
    is_active: int
    created_at: str
    updated_at: Optional[str]


class UserBrandPermission(TypedDict):
    id: int
    user_id: str
    brand_id: str
    permission_level: PermissionLevel


# ─────────────────────────────────────────
# ai_governance
# ─────────────────────────────────────────

class AiCeoProfile(TypedDict):
    id: str
    user_id: str
    reports_to_user_id: Optional[str]  # Human President
    persona: Optional[str]             # JSON string
    decision_authority: str            # JSON string
    created_at: str
    updated_at: Optional[str]


class AiAgent(TypedDict):
    id: str
    user_id: str
    agent_type: str
    reports_to_id: Optional[str]  # AI CEO user_id
    model: str
    system_prompt: Optional[str]
    config: str  # JSON string
    is_active: int
    created_at: str
    updated_at: Optional[str]


class AgentCapability(TypedDict):
    id: int
    agent_id: str
    capability: str
    enabled: int
    config: str  # JSON string


class AgentAssignment(TypedDict):
    id: int
    agent_id: str
    brand_id: str
    location_id: Optional[str]
    is_primary: int
    created_at: str


class AgentTask(TypedDict):
    id: str
    title: str
    description: Optional[str]
    assigned_to_agent_id: Optional[str]
    requested_by_user_id: Optional[str]
    brand_id: Optional[str]
    mode: TaskMode
    status: TaskStatus
    priority: int
    input_data: str   # JSON string
    output_data: str  # JSON string
    error_message: Optional[str]
    scheduled_at: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    created_at: str
    updated_at: Optional[str]


class AgentTaskDependency(TypedDict):
    id: int
    task_id: str
    depends_on_task_id: str
    dependency_type: DependencyType


class AgentRun(TypedDict):
    id: str
    task_id: str
    agent_id: str
    run_number: int
    status: str
    log: Optional[str]  # JSON array string
    tokens_used: int
    cost_usd: float
    started_at: str
    completed_at: Optional[str]
    error_message: Optional[str]


class Escalation(TypedDict):
    id: str
    task_id: str
    agent_id: Optional[str]
    escalated_to_user_id: Optional[str]
    reason: str
    context: str  # JSON string
    status: EscalationStatus
    resolved_at: Optional[str]
    resolution_note: Optional[str]
    created_at: str


class Approval(TypedDict):
    id: str
    task_id: str
    title: str
    description: Optional[str]
    requested_by_agent_id: Optional[str]
    status: ApprovalStatus
    expires_at: Optional[str]
    created_at: str
    updated_at: Optional[str]


# ─────────────────────────────────────────
# asset_brain
# ─────────────────────────────────────────

AssetType       = Literal["photo", "video", "template", "script"]
AssetStatus     = Literal["active", "archived", "review_needed"]
CopyrightStatus = Literal["owned", "licensed", "creative_commons", "unknown"]
Season          = Literal["spring", "summer", "fall", "winter", "all"]


class Asset(TypedDict):
    asset_id:         str
    brand:            str
    location:         Optional[str]
    asset_type:       AssetType
    channel_use:      list[str]          # JSON array in DB
    season:           Season
    target_audience:  list[str]          # JSON array in DB
    copyright_status: CopyrightStatus
    face_permission:  int                # 0/1
    reusable:         int                # 0/1
    status:           AssetStatus
    title:            Optional[str]
    description:      Optional[str]
    file_path:        Optional[str]
    thumbnail_url:    Optional[str]
    file_size:        Optional[int]
    duration_sec:     Optional[int]
    width:            Optional[int]
    height:           Optional[int]
    ai_tags:          list[str]          # JSON array in DB
    performance_note: Optional[str]
    created_at:       str
    updated_at:       Optional[str]


class AssetTag(TypedDict):
    tag_id:   int
    name:     str
    category: str
    color:    str


class AssetTagLink(TypedDict):
    id:       int
    asset_id: str
    tag_id:   int


class AssetUsage(TypedDict):
    id:          int
    asset_id:    str
    used_in:     Optional[str]
    channel:     Optional[str]
    brand:       Optional[str]
    used_at:     str
    result_note: Optional[str]
    performance: dict                    # JSON in DB


class AssetCollection(TypedDict):
    collection_id: str
    name:          str
    brand:         Optional[str]
    description:   Optional[str]
    asset_ids:     list[str]             # JSON array in DB
    created_at:    str
    updated_at:    Optional[str]


class ApprovalStep(TypedDict):
    id: int
    approval_id: str
    step_order: int
    approver_user_id: str
    status: str
    comment: Optional[str]
    decided_at: Optional[str]
