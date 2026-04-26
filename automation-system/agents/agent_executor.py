"""
Agent Executor
==============
Takes a queued task, runs the assigned Claude AI agent against it,
handles tool calls, and closes the run record in org_database.

Entry points:
  run(task_id)        — execute a specific task
  run_next(limit=5)   — pick up to N queued tasks and run them
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import anthropic

# パスを通す
_BASE = Path(__file__).parent.parent
if str(_BASE) not in sys.path:
    sys.path.insert(0, str(_BASE))

import org_database as db
from agents import orchestrator

log = logging.getLogger(__name__)

# ── ディレクトリ定数 ──────────────────────────────────────────
QUEUE_ROOT   = _BASE / "content_queue"
DECISION_DIR = _BASE / "decision_queue"
LEADS_DIR    = _BASE.parent / "sales-system" / "leads"
CALENDAR_DIR = QUEUE_ROOT / "calendar"

# ── Claude クライアント ──────────────────────────────────────
def _client() -> anthropic.Anthropic:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY が設定されていません")
    return anthropic.Anthropic(api_key=key)


# ════════════════════════════════════════════════════════════
# ツール スキーマ定義
# ════════════════════════════════════════════════════════════

TOOL_SCHEMAS: dict[str, dict] = {

    "generate_post": {
        "name": "generate_post",
        "description": "指定ブランド・プラットフォーム向けの投稿文（キャプション＋ハッシュタグ）を生成する",
        "input_schema": {
            "type": "object",
            "properties": {
                "brand":    {"type": "string", "description": "ブランドID (例: dsc-marketing)"},
                "platform": {"type": "string", "description": "投稿先 (instagram/threads/facebook/twitter/line/wordpress)"},
                "topic":    {"type": "string", "description": "投稿テーマ・トピック"},
                "target":   {"type": "string", "description": "ターゲット層"},
                "tone":     {"type": "string", "description": "トーン (例: 親しみやすい・専門的)"},
                "extra":    {"type": "string", "description": "追加指示（省略可）"},
            },
            "required": ["brand", "platform", "topic"],
        },
    },

    "queue_push": {
        "name": "queue_push",
        "description": "生成したコンテンツを投稿キューに追加する",
        "input_schema": {
            "type": "object",
            "properties": {
                "brand":      {"type": "string", "description": "ブランドID"},
                "platform":   {"type": "string", "description": "プラットフォーム"},
                "caption":    {"type": "string", "description": "投稿本文"},
                "hashtags":   {"type": "string", "description": "ハッシュタグ"},
                "image_url":  {"type": "string", "description": "画像URL（省略可）"},
                "scheduled_at": {"type": "string", "description": "予約投稿日時 ISO形式（省略可）"},
            },
            "required": ["brand", "platform", "caption"],
        },
    },

    "weekly_calendar": {
        "name": "weekly_calendar",
        "description": "週次コンテンツカレンダーを自動生成し保存する",
        "input_schema": {
            "type": "object",
            "properties": {
                "brand":     {"type": "string", "description": "ブランドID"},
                "week_note": {"type": "string", "description": "今週の重点テーマや注意事項（省略可）"},
            },
            "required": ["brand"],
        },
    },

    "line_broadcast": {
        "name": "line_broadcast",
        "description": "LINE公式アカウントから全フォロワーに一斉配信する",
        "input_schema": {
            "type": "object",
            "properties": {
                "brand":   {"type": "string", "description": "ブランドID"},
                "message": {"type": "string", "description": "配信メッセージ本文"},
            },
            "required": ["brand", "message"],
        },
    },

    "generate_blog_post": {
        "name": "generate_blog_post",
        "description": "ブログ記事（タイトル・本文・SEOメタ）を生成する",
        "input_schema": {
            "type": "object",
            "properties": {
                "brand":   {"type": "string", "description": "ブランドID"},
                "topic":   {"type": "string", "description": "記事テーマ"},
                "keyword": {"type": "string", "description": "SEOキーワード（省略可）"},
                "length":  {"type": "integer", "description": "目標文字数（省略可、デフォルト1200）"},
            },
            "required": ["brand", "topic"],
        },
    },

    "wordpress_draft": {
        "name": "wordpress_draft",
        "description": "WordPressに記事を下書き保存する",
        "input_schema": {
            "type": "object",
            "properties": {
                "brand":   {"type": "string", "description": "ブランドID"},
                "title":   {"type": "string", "description": "記事タイトル"},
                "content": {"type": "string", "description": "記事本文（HTML or Markdown）"},
                "status":  {"type": "string", "description": "draft or publish（デフォルト: draft）"},
            },
            "required": ["brand", "title", "content"],
        },
    },

    "lead_reply": {
        "name": "lead_reply",
        "description": "リードの問い合わせ内容を読んで返信ドラフトを生成し、LINEまたはメールで送信する",
        "input_schema": {
            "type": "object",
            "properties": {
                "lead_id": {"type": "string", "description": "リードID"},
                "send":    {"type": "boolean", "description": "true=実際に送信, false=ドラフトのみ返す"},
            },
            "required": ["lead_id"],
        },
    },

    "followup_send": {
        "name": "followup_send",
        "description": "指定リードにフォローアップメッセージを送信する",
        "input_schema": {
            "type": "object",
            "properties": {
                "lead_id": {"type": "string", "description": "リードID"},
                "message": {"type": "string", "description": "フォローアップ内容（省略時は自動生成）"},
                "channel": {"type": "string", "description": "line または email（デフォルト: line）"},
            },
            "required": ["lead_id"],
        },
    },

    "stage_update": {
        "name": "stage_update",
        "description": "リードの営業ステージを更新する",
        "input_schema": {
            "type": "object",
            "properties": {
                "lead_id": {"type": "string", "description": "リードID"},
                "stage":   {"type": "string", "description": "新ステージ (new/contacted/qualified/proposal/closed_won/closed_lost)"},
                "note":    {"type": "string", "description": "更新メモ（省略可）"},
            },
            "required": ["lead_id", "stage"],
        },
    },

    "performance_fetch": {
        "name": "performance_fetch",
        "description": "指定ブランドのSNSパフォーマンスサマリーを取得する",
        "input_schema": {
            "type": "object",
            "properties": {
                "brand":    {"type": "string", "description": "ブランドID"},
                "platform": {"type": "string", "description": "プラットフォーム（省略時: instagram）"},
                "days":     {"type": "integer", "description": "集計日数（省略時: 30）"},
            },
            "required": ["brand"],
        },
    },

    "trend_research": {
        "name": "trend_research",
        "description": "指定ブランド・業界のトレンドトピックをリサーチして返す",
        "input_schema": {
            "type": "object",
            "properties": {
                "brand":   {"type": "string", "description": "ブランドID"},
                "keyword": {"type": "string", "description": "調査キーワード（省略可）"},
                "count":   {"type": "integer", "description": "提案数（省略時: 5）"},
            },
            "required": ["brand"],
        },
    },

    "ga4_fetch": {
        "name": "ga4_fetch",
        "description": "Google Analytics 4 からセッション・PV・ユーザー数を取得する",
        "input_schema": {
            "type": "object",
            "properties": {
                "brand": {"type": "string", "description": "ブランドID"},
                "days":  {"type": "integer", "description": "集計日数（省略時: 28）"},
            },
            "required": ["brand"],
        },
    },

    "scheduler_check": {
        "name": "scheduler_check",
        "description": "スケジューラーの直近実行ログと次回予定を確認する",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "取得件数（省略時: 10）"},
            },
            "required": [],
        },
    },

    "decision_triage": {
        "name": "decision_triage",
        "description": "判断待ちキューの未処理件数と優先度リストを返す",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "取得件数（省略時: 20）"},
            },
            "required": [],
        },
    },

    "db_backup": {
        "name": "db_backup",
        "description": "SQLiteデータベースをバックアップファイルにコピーする",
        "input_schema": {
            "type": "object",
            "properties": {
                "note": {"type": "string", "description": "バックアップメモ（省略可）"},
            },
            "required": [],
        },
    },
}


# ════════════════════════════════════════════════════════════
# ツール ハンドラー
# ════════════════════════════════════════════════════════════

def _h_generate_post(inp: dict, ctx: dict) -> dict:
    from dashboard.ai import (
        generate_instagram_post, generate_all_platforms,
        generate_line_message,
    )
    brand    = inp.get("brand", ctx.get("brand_id", "dsc-marketing"))
    platform = inp.get("platform", "instagram")
    topic    = inp.get("topic", "")
    target   = inp.get("target", "一般ユーザー")
    tone     = inp.get("tone", "親しみやすい")
    extra    = inp.get("extra", "")

    if platform == "instagram":
        result = generate_instagram_post(topic, target, tone, brand, extra)
    elif platform == "line":
        result = {"message": generate_line_message(topic, brand)}
    else:
        result = generate_all_platforms(topic, target, tone, brand, [platform], extra)
        result = result.get(platform, result)

    log.info(f"generate_post: brand={brand} platform={platform}")
    return {"ok": True, "result": result}


def _h_queue_push(inp: dict, ctx: dict) -> dict:
    import uuid, yaml
    brand    = inp.get("brand", ctx.get("brand_id", "dsc-marketing"))
    platform = inp.get("platform", "instagram")
    caption  = inp.get("caption", "")
    hashtags = inp.get("hashtags", "")
    image_url = inp.get("image_url", "")
    scheduled_at = inp.get("scheduled_at", "")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    entry = {
        "id":           str(uuid.uuid4())[:8],
        "brand":        brand,
        "platform":     platform,
        "caption":      caption,
        "hashtags":     hashtags,
        "image_url":    image_url,
        "scheduled_at": scheduled_at,
        "posted":       False,
        "source":       "agent",
        "created_at":   datetime.now().isoformat(),
    }
    dest = QUEUE_ROOT / brand / platform
    dest.mkdir(parents=True, exist_ok=True)
    fname = f"{ts}_agent.yaml"
    with open(dest / fname, "w", encoding="utf-8") as f:
        yaml.dump(entry, f, allow_unicode=True, default_flow_style=False)

    # instagram キューにも追加
    if platform == "instagram":
        ig_dir = QUEUE_ROOT / "instagram"
        ig_dir.mkdir(parents=True, exist_ok=True)
        with open(ig_dir / fname, "w", encoding="utf-8") as f:
            yaml.dump(entry, f, allow_unicode=True, default_flow_style=False)

    log.info(f"queue_push: {brand}/{platform} → {fname}")
    return {"ok": True, "file": fname, "brand": brand, "platform": platform}


def _h_weekly_calendar(inp: dict, ctx: dict) -> dict:
    from dashboard.ai import generate_weekly_calendar, save_weekly_calendar
    brand     = inp.get("brand", ctx.get("brand_id", "dsc-marketing"))
    week_note = inp.get("week_note", "")
    extra     = f"今週の注意: {week_note}" if week_note else ""
    cal = generate_weekly_calendar(brand=brand, extra=extra)
    path = save_weekly_calendar(cal, brand=brand)
    log.info(f"weekly_calendar: brand={brand} saved to {path}")
    return {"ok": True, "brand": brand, "saved_to": str(path), "calendar": cal}


def _h_line_broadcast(inp: dict, ctx: dict) -> dict:
    from sns.line_api import LINEMessenger
    brand   = inp.get("brand", ctx.get("brand_id", "dsc-marketing"))
    message = inp.get("message", "")
    if not message:
        return {"ok": False, "error": "message が空です"}
    messenger = LINEMessenger()
    ok = messenger.broadcast(message)
    log.info(f"line_broadcast: brand={brand} ok={ok}")
    return {"ok": ok, "brand": brand, "chars": len(message)}


def _h_generate_blog_post(inp: dict, ctx: dict) -> dict:
    from dashboard.ai import generate_blog_post
    brand   = inp.get("brand", ctx.get("brand_id", "satoshi-blog"))
    topic   = inp.get("topic", "")
    keyword = inp.get("keyword", "")
    length  = inp.get("length", 1200)
    result  = generate_blog_post(topic=topic, brand=brand,
                                  keyword=keyword, length=length)
    log.info(f"generate_blog_post: brand={brand} topic={topic}")
    return {"ok": True, "result": result}


def _h_wordpress_draft(inp: dict, ctx: dict) -> dict:
    from sns.wordpress import WordPressPoster
    brand   = inp.get("brand", ctx.get("brand_id", "satoshi-blog"))
    title   = inp.get("title", "")
    content = inp.get("content", "")
    status  = inp.get("status", "draft")
    wp = WordPressPoster(brand=brand)
    result = wp.create_post(title=title, content=content, status=status)
    log.info(f"wordpress_draft: brand={brand} title={title!r} status={status}")
    return {"ok": True, "result": result}


def _h_lead_reply(inp: dict, ctx: dict) -> dict:
    from dashboard.ai import generate_lead_reply
    lead_id = inp.get("lead_id", "")
    send    = inp.get("send", False)

    lead = db.get_lead(lead_id) if hasattr(db, "get_lead") else None
    if not lead:
        # ファイルから読む
        lead = _load_lead_from_file(lead_id)
    if not lead:
        return {"ok": False, "error": f"Lead {lead_id} が見つかりません"}

    draft = generate_lead_reply(lead)

    if send:
        line_uid = lead.get("line_user_id", "")
        if line_uid:
            from sns.line_api import LINEMessenger
            LINEMessenger().push(line_uid, draft)
            log.info(f"lead_reply sent via LINE: lead_id={lead_id}")
        else:
            log.warning(f"lead_reply: LINE user_id なし, 送信スキップ lead_id={lead_id}")

    return {"ok": True, "lead_id": lead_id, "draft": draft, "sent": send}


def _h_followup_send(inp: dict, ctx: dict) -> dict:
    from dashboard.ai import generate_lead_reply
    lead_id = inp.get("lead_id", "")
    message = inp.get("message", "")
    channel = inp.get("channel", "line")

    lead = _load_lead_from_file(lead_id)
    if not lead:
        return {"ok": False, "error": f"Lead {lead_id} が見つかりません"}

    if not message:
        message = generate_lead_reply(lead)

    if channel == "line":
        line_uid = lead.get("line_user_id", "")
        if line_uid:
            from sns.line_api import LINEMessenger
            ok = LINEMessenger().push(line_uid, message)
        else:
            ok = False
    else:
        ok = False
        log.warning(f"followup_send: channel={channel} 未対応")

    log.info(f"followup_send: lead_id={lead_id} channel={channel} ok={ok}")
    return {"ok": ok, "lead_id": lead_id, "channel": channel}


def _h_stage_update(inp: dict, ctx: dict) -> dict:
    import yaml
    lead_id = inp.get("lead_id", "")
    stage   = inp.get("stage", "")
    note    = inp.get("note", "")

    lead_path = _find_lead_file(lead_id)
    if not lead_path:
        return {"ok": False, "error": f"Lead {lead_id} が見つかりません"}

    with open(lead_path, encoding="utf-8") as f:
        lead = yaml.safe_load(f)

    old_stage = lead.get("stage", "")
    lead["stage"] = stage
    lead["updated_at"] = datetime.now().isoformat()
    if note:
        lead.setdefault("notes", []).append({
            "at": datetime.now().isoformat(), "note": note
        })

    with open(lead_path, "w", encoding="utf-8") as f:
        yaml.dump(lead, f, allow_unicode=True, default_flow_style=False)

    log.info(f"stage_update: lead_id={lead_id} {old_stage} → {stage}")
    return {"ok": True, "lead_id": lead_id, "old_stage": old_stage, "new_stage": stage}


def _h_performance_fetch(inp: dict, ctx: dict) -> dict:
    from sns.performance import get_performance_summary
    brand    = inp.get("brand", ctx.get("brand_id", "dsc-marketing"))
    platform = inp.get("platform", "instagram")
    days     = inp.get("days", 30)
    summary  = get_performance_summary(brand=brand, platform=platform, days=days)
    return {"ok": True, "brand": brand, "platform": platform, "summary": summary}


def _h_trend_research(inp: dict, ctx: dict) -> dict:
    from dashboard.ai import research_trending_topics
    brand   = inp.get("brand", ctx.get("brand_id", "dsc-marketing"))
    keyword = inp.get("keyword", "")
    count   = inp.get("count", 5)
    topics  = research_trending_topics(brand=brand, keyword=keyword, count=count)
    return {"ok": True, "brand": brand, "topics": topics}


def _h_ga4_fetch(inp: dict, ctx: dict) -> dict:
    from sns.analytics import GA4Client
    brand    = inp.get("brand", ctx.get("brand_id", "dsc-marketing"))
    days     = inp.get("days", 28)
    env_key  = brand.upper().replace("-", "_") + "_GA4_PROPERTY_ID"
    client   = GA4Client(property_id_env=env_key)
    overview = client.get_overview(days=days)
    return {"ok": True, "brand": brand, "days": days, "data": overview}


def _h_scheduler_check(inp: dict, ctx: dict) -> dict:
    limit = inp.get("limit", 10)
    logs_dir = _BASE / "logs"
    entries: list[dict] = []
    if logs_dir.exists():
        import yaml
        for f in sorted(logs_dir.glob("*.yaml"), reverse=True)[:limit]:
            try:
                with open(f, encoding="utf-8") as fh:
                    entries.append(yaml.safe_load(fh) or {})
            except Exception:
                pass
    return {"ok": True, "log_count": len(entries), "recent": entries[:limit]}


def _h_decision_triage(inp: dict, ctx: dict) -> dict:
    import yaml
    limit = inp.get("limit", 20)
    items: list[dict] = []
    if DECISION_DIR.exists():
        for f in sorted(DECISION_DIR.glob("*.yaml"), reverse=True)[:limit]:
            try:
                with open(f, encoding="utf-8") as fh:
                    d = yaml.safe_load(fh) or {}
                    d["_file"] = f.name
                    items.append(d)
            except Exception:
                pass
    urgent = [i for i in items if i.get("priority") in ("high", "urgent")]
    return {
        "ok": True,
        "total": len(items),
        "urgent_count": len(urgent),
        "items": items,
    }


def _h_db_backup(inp: dict, ctx: dict) -> dict:
    note = inp.get("note", "")
    db_path = _BASE / "data" / "automation.db"
    if not db_path.exists():
        db_path = _BASE / "automation.db"
    if not db_path.exists():
        return {"ok": False, "error": "データベースファイルが見つかりません"}

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = _BASE / "data" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    dest = backup_dir / f"backup_{ts}.db"
    shutil.copy2(db_path, dest)
    log.info(f"db_backup: {dest} note={note!r}")
    return {"ok": True, "backup_file": str(dest), "note": note}


# ── ハンドラーテーブル ─────────────────────────────────────
TOOL_HANDLERS: dict[str, Any] = {
    "generate_post":    _h_generate_post,
    "queue_push":       _h_queue_push,
    "weekly_calendar":  _h_weekly_calendar,
    "line_broadcast":   _h_line_broadcast,
    "generate_blog_post": _h_generate_blog_post,
    "wordpress_draft":  _h_wordpress_draft,
    "lead_reply":       _h_lead_reply,
    "followup_send":    _h_followup_send,
    "stage_update":     _h_stage_update,
    "performance_fetch": _h_performance_fetch,
    "trend_research":   _h_trend_research,
    "ga4_fetch":        _h_ga4_fetch,
    "scheduler_check":  _h_scheduler_check,
    "decision_triage":  _h_decision_triage,
    "db_backup":        _h_db_backup,
}


# ════════════════════════════════════════════════════════════
# エージェント設定ローダー
# ════════════════════════════════════════════════════════════

def _load_os_config() -> dict:
    import yaml
    cfg_path = _BASE / "config" / "os_config.yaml"
    with open(cfg_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _get_agent_config(agent_id: str) -> dict:
    """
    DB の ai_agents レコード + os_config.yaml の tools 定義をマージして返す。
    """
    agent_row = db.get_ai_agent(agent_id)
    if not agent_row:
        raise ValueError(f"Agent {agent_id} が DB に存在しません")

    cfg = _load_os_config()
    yaml_agents: list[dict] = cfg.get("agents", [])
    yaml_entry = next((a for a in yaml_agents if a["id"] == agent_id), {})

    tools: list[str] = db.get_agent_capabilities_list(agent_id)
    if not tools:
        tools = yaml_entry.get("tools", [])

    return {
        "id":          agent_id,
        "model":       agent_row.get("model") or yaml_entry.get("model", "claude-haiku-4-5-20251001"),
        "role":        yaml_entry.get("role", "AI Agent"),
        "description": yaml_entry.get("description", ""),
        "brand":       yaml_entry.get("brand", ""),
        "tools":       tools,
        "system_prompt": agent_row.get("system_prompt") or "",
    }


def _build_system_prompt(agent_cfg: dict, task: dict) -> str:
    brand_id = task.get("brand_id") or agent_cfg.get("brand") or ""
    brand_ctx = _brand_context(brand_id)

    lines = [
        f"あなたは {agent_cfg['role']} です。",
        agent_cfg["description"],
        "",
        "## 担当タスク",
        f"タイトル: {task.get('title', '')}",
        f"説明: {task.get('description', '')}",
    ]
    if brand_ctx:
        lines += ["", "## ブランドコンテキスト", brand_ctx]

    lines += [
        "",
        "## 行動原則",
        "- 与えられたツールを使ってタスクを完遂してください。",
        "- 一度に複数のツールを使って効率よく処理してください。",
        "- 完了したら日本語で結果サマリーを返してください。",
        "- 不確かな場合は実行せず、理由を説明してください。",
    ]
    return "\n".join(lines)


def _brand_context(brand_id: str) -> str:
    CONTEXTS = {
        "dsc-marketing":   "DSc Marketing — SNS・LINE・Web集客の導線設計・運用支援。月額25,000円〜100,800円。",
        "cashflowsupport": "cashflowsupport — ファクタリング・資金繰り相談。丁寧・経営者目線・透明性を重視。",
        "upjapan":         "UPJ（株式会社ユニバースプラネットジャパン）— 事業設計・収益モデル再設計・国際展開。",
        "bangkok-peach":   "Bangkok Peach Group — バンコク拠点の事業・観光・ライフスタイル。日英タイ対応。",
        "satoshi-blog":    "Satoshi Life Blog — 起業家Satoshiの一人称ブログ。ビジネス・海外生活・AI活用。",
    }
    return CONTEXTS.get(brand_id, "")


# ════════════════════════════════════════════════════════════
# メイン実行ループ
# ════════════════════════════════════════════════════════════

def run(task_id: str) -> dict:
    """
    タスクを1件実行する。
    Returns: {"task_id", "run_id", "status", "output", "tokens_used", "cost_usd"}
    """
    task = db.get_task(task_id)
    if not task:
        raise ValueError(f"Task {task_id} が見つかりません")

    agent_id = task.get("assigned_to_agent_id")
    if not agent_id:
        agent_id = orchestrator.auto_assign(task_id)  # type: ignore[attr-defined]
    if not agent_id:
        raise RuntimeError(f"Task {task_id} に割り当てエージェントがありません")

    run_id = orchestrator.start_task(task_id)
    if not run_id:
        raise RuntimeError(f"Task {task_id} の run 開始に失敗しました")

    agent_cfg = _get_agent_config(agent_id)
    available_tools = [
        TOOL_SCHEMAS[t] for t in agent_cfg["tools"] if t in TOOL_SCHEMAS
    ]

    input_data: dict = {}
    try:
        raw = task.get("input_data") or "{}"
        input_data = json.loads(raw) if isinstance(raw, str) else (raw or {})
    except json.JSONDecodeError:
        pass

    system_prompt = _build_system_prompt(agent_cfg, task)
    initial_message = _build_initial_message(task, input_data)

    messages: list[dict] = [{"role": "user", "content": initial_message}]
    log_entries: list[dict] = []
    tokens_used = 0
    output_text = ""

    client = _client()
    max_iterations = 10

    try:
        for iteration in range(max_iterations):
            kwargs: dict = {
                "model":      agent_cfg["model"],
                "max_tokens": 4096,
                "system":     system_prompt,
                "tools":      available_tools,
                "messages":   messages,
            }

            response = client.messages.create(**kwargs)
            tokens_used += (response.usage.input_tokens + response.usage.output_tokens)

            log_entries.append({
                "iteration":   iteration + 1,
                "stop_reason": response.stop_reason,
                "tokens":      response.usage.input_tokens + response.usage.output_tokens,
            })

            # 終了
            if response.stop_reason == "end_turn":
                for block in response.content:
                    if hasattr(block, "text"):
                        output_text += block.text
                break

            # ツール呼び出し
            if response.stop_reason == "tool_use":
                messages.append({
                    "role":    "assistant",
                    "content": response.content,
                })
                tool_results = []
                for block in response.content:
                    if block.type != "tool_use":
                        continue
                    handler = TOOL_HANDLERS.get(block.name)
                    ctx = {"brand_id": task.get("brand_id", "")}
                    if handler:
                        try:
                            result = handler(block.input, ctx)
                        except Exception as e:
                            result = {"ok": False, "error": str(e)}
                            log.exception(f"Tool {block.name} raised an error")
                    else:
                        result = {"ok": False, "error": f"未実装ツール: {block.name}"}

                    log_entries.append({
                        "tool":   block.name,
                        "input":  block.input,
                        "result": result,
                    })
                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": block.id,
                        "content":     json.dumps(result, ensure_ascii=False),
                    })

                messages.append({"role": "user", "content": tool_results})
                continue

            # 想定外の stop_reason
            log.warning(f"Unexpected stop_reason: {response.stop_reason}")
            break

        else:
            log.warning(f"Task {task_id}: max_iterations({max_iterations}) に達しました")

        cost_usd = tokens_used * 0.000001  # 概算

        orchestrator.complete_task(
            task_id, run_id,
            output_data={"result": output_text, "log": log_entries},
            log_entries=log_entries,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
        )
        log.info(f"Task {task_id} 完了 tokens={tokens_used}")
        return {
            "task_id":     task_id,
            "run_id":      run_id,
            "status":      "completed",
            "output":      output_text,
            "tokens_used": tokens_used,
            "cost_usd":    cost_usd,
        }

    except Exception as e:
        log.exception(f"Task {task_id} 実行エラー")
        orchestrator.fail_task(task_id, run_id, str(e))
        return {
            "task_id": task_id,
            "run_id":  run_id,
            "status":  "failed",
            "error":   str(e),
        }


def run_next(limit: int = 5) -> list[dict]:
    """
    キュー内の実行可能タスクを最大 limit 件取り出して順に実行する。
    Returns: list of run results
    """
    from agents.task_service import get_runnable_tasks
    tasks = get_runnable_tasks(limit=limit)
    results = []
    for t in tasks:
        log.info(f"run_next: starting task {t['id']} — {t.get('title')}")
        result = run(t["id"])
        results.append(result)
    return results


# ════════════════════════════════════════════════════════════
# ユーティリティ
# ════════════════════════════════════════════════════════════

def _build_initial_message(task: dict, input_data: dict) -> str:
    parts = [f"タスク: {task.get('title', '')}"]
    if task.get("description"):
        parts.append(f"詳細: {task['description']}")
    if input_data:
        parts.append(f"入力データ: {json.dumps(input_data, ensure_ascii=False, indent=2)}")
    return "\n".join(parts)


def _load_lead_from_file(lead_id: str) -> dict | None:
    import yaml
    for f in LEADS_DIR.rglob("*.yaml"):
        try:
            with open(f, encoding="utf-8") as fh:
                d = yaml.safe_load(fh) or {}
            if d.get("id") == lead_id or f.stem == lead_id:
                return d
        except Exception:
            pass
    return None


def _find_lead_file(lead_id: str) -> Path | None:
    for f in LEADS_DIR.rglob("*.yaml"):
        try:
            import yaml
            with open(f, encoding="utf-8") as fh:
                d = yaml.safe_load(fh) or {}
            if d.get("id") == lead_id or f.stem == lead_id:
                return f
        except Exception:
            pass
    return None
