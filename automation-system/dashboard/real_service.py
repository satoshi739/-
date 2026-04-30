"""
Real Service — DBから実データを取得してダッシュボードに渡す。
mock_service.py の各関数と同じシグネチャを持つ。
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

import org_database as db
import database as main_db

log = logging.getLogger(__name__)

_OS_CFG_PATH = Path(__file__).parent.parent / "config" / "os_config.yaml"

# ── os_config.yaml からエージェントメタをキャッシュ ────────────────

def _load_agent_meta() -> dict[str, dict]:
    """agent_id → {name, icon, description} マップを返す"""
    meta: dict[str, dict] = {
        "ai-ceo": {"name": "AI CEO", "icon": "🏢", "description": "全ブランド統括"},
    }
    try:
        cfg = yaml.safe_load(_OS_CFG_PATH.read_text(encoding="utf-8"))
        for a in cfg.get("agents", []):
            aid  = a.get("id", "")
            name = a.get("name", aid)
            role = a.get("role", "")
            meta[aid] = {
                "name":        name,
                "icon":        _role_icon(role),
                "description": a.get("description", "")[:60],
            }
    except Exception as e:
        log.warning(f"os_config.yaml 読み込み失敗: {e}")
    return meta


def _role_icon(role: str) -> str:
    role_l = role.lower()
    if "content" in role_l or "コンテンツ" in role_l:
        return "📸"
    if "blog" in role_l or "記事" in role_l:
        return "✍️"
    if "sales" in role_l or "営業" in role_l:
        return "💰"
    if "analytics" in role_l or "分析" in role_l:
        return "📊"
    if "ops" in role_l or "運用" in role_l:
        return "⚙️"
    return "🤖"


# YAML で定義されたエージェントIDのみ扱う（seed_org の旧UUIDエージェントを除外）
YAML_AGENT_IDS = {
    "ai-ceo",
    "agent-content-upj", "agent-content-dsc", "agent-content-cfj", "agent-content-bpg",
    "agent-blog", "agent-sales", "agent-analytics", "agent-ops",
}

# ブランドスラッグ → 表示名・カラー
BRAND_META = {
    "upj":          {"name": "UPJ",  "color": "#5b8af5", "link": "/brands/upjapan"},
    "upjapan":      {"name": "UPJ",  "color": "#5b8af5", "link": "/brands/upjapan"},
    "dsc":          {"name": "DSC",  "color": "#34d399", "link": "/brands/dsc-marketing"},
    "dsc-marketing":{"name": "DSC",  "color": "#34d399", "link": "/brands/dsc-marketing"},
    "cfj":          {"name": "CFJ",  "color": "#fbbf24", "link": "/brands/cashflowsupport"},
    "cashflowsupport":{"name":"CFJ", "color": "#fbbf24", "link": "/brands/cashflowsupport"},
    "bangkok-peach":{"name": "BPG",  "color": "#f472b6", "link": "/brands/bangkok-peach"},
    "satoshi-blog": {"name": "Blog", "color": "#a78bfa", "link": "/brands/satoshi-blog"},
}


def _status_badge(counts: dict) -> str:
    if counts.get("failed", 0) > 2:
        return "alert"
    if counts.get("failed", 0) > 0:
        return "warn"
    if counts.get("running", 0) > 0:
        return "ok"
    if counts.get("queued", 0) > 0:
        return "ok"
    return "idle"


def get_task_queue() -> list:
    """キュー中・実行中タスクを返す（最大15件）"""
    tasks = []
    for status in ("running", "queued", "waiting_approval", "escalated"):
        tasks += db.list_tasks(status=status, limit=5)

    result = []
    for t in tasks[:15]:
        priority_val = t.get("priority", 5)
        if priority_val <= 2:
            pri_label = "high"
        elif priority_val <= 5:
            pri_label = "mid"
        else:
            pri_label = "low"

        result.append({
            "id":       t["id"][:8],
            "priority": pri_label,
            "task":     t.get("title", ""),
            "agent":    t.get("assigned_to_agent_id", ""),
            "status":   t.get("status", ""),
            "eta":      t.get("scheduled_at", "") or "—",
        })
    return result


def get_bottlenecks() -> list:
    """失敗・ブロック中タスクからボトルネックを抽出"""
    failed  = db.list_tasks(status="failed",  limit=5)
    blocked = db.list_tasks(status="blocked", limit=5)

    result = []
    for t in failed:
        err = t.get("error_message", "") or ""
        result.append({
            "area":   t.get("assigned_to_agent_id", "不明"),
            "issue":  f"[失敗] {t.get('title', '')} — {err[:60]}",
            "impact": "high",
        })
    for t in blocked:
        result.append({
            "area":   t.get("assigned_to_agent_id", "不明"),
            "issue":  f"[ブロック] {t.get('title', '')}",
            "impact": "mid",
        })

    if not result:
        result.append({
            "area":   "システム",
            "issue":  "現在ボトルネックはありません",
            "impact": "low",
        })
    return result


def get_escalations() -> list:
    """未解決エスカレーション一覧"""
    escs = db.list_escalations(status="open")
    result = []
    for e in escs:
        result.append({
            "to":       "社長",
            "urgency":  "high",
            "item":     e.get("reason", "")[:80],
            "deadline": "確認必要",
        })
    if not result:
        result.append({
            "to":       "—",
            "urgency":  "low",
            "item":     "現在エスカレーションはありません",
            "deadline": "—",
        })
    return result


def get_agent_status() -> list:
    """YAMLで定義されたエージェントのステータス一覧"""
    agent_meta = _load_agent_meta()
    counts     = db.get_task_counts_all_agents()
    result     = []

    # YAML定義順で表示
    ordered_ids = [
        "agent-content-upj", "agent-content-dsc", "agent-content-cfj", "agent-content-bpg",
        "agent-blog", "agent-sales", "agent-analytics", "agent-ops",
    ]

    for aid in ordered_ids:
        meta = agent_meta.get(aid, {"name": aid, "icon": "🤖", "description": ""})
        c    = counts.get(aid, {})
        runs = db.list_runs_for_agent(aid, limit=1)

        last_run_str = "未実行"
        if runs:
            started = runs[0].get("started_at", "")
            if started:
                try:
                    dt   = datetime.fromisoformat(started)
                    diff = datetime.now() - dt
                    secs = int(diff.total_seconds())
                    if secs < 3600:
                        last_run_str = f"{secs // 60}分前"
                    elif secs < 86400:
                        last_run_str = f"{secs // 3600}時間前"
                    else:
                        last_run_str = f"{secs // 86400}日前"
                except Exception:
                    last_run_str = started[:16]

        detail_parts = []
        if c.get("running"):
            detail_parts.append(f"実行中{c['running']}件")
        if c.get("queued"):
            detail_parts.append(f"待機{c['queued']}件")
        if c.get("completed"):
            detail_parts.append(f"完了{c['completed']}件")
        if c.get("failed"):
            detail_parts.append(f"失敗{c['failed']}件")

        result.append({
            "name":     meta["name"],
            "icon":     meta["icon"],
            "status":   _status_badge(c),
            "last_run": last_run_str,
            "next_run": "スケジューラー依存",
            "detail":   "、".join(detail_parts) or "タスクなし",
        })

    return result


def get_brand_status() -> dict:
    """各ブランドのタスク状況"""
    brands = db.list_brands()
    result = {}

    for b in brands:
        slug = b["slug"]
        meta = BRAND_META.get(slug, {"name": slug, "color": "#888", "link": f"/brands/{slug}"})

        # そのブランドに割り当てられたタスク件数を取得
        with db.get_conn() as conn:
            completed_today = conn.execute(
                """SELECT COUNT(*) FROM agent_tasks
                   WHERE brand_id=? AND status='completed'
                   AND date(updated_at)=date('now')""",
                (b["id"],),
            ).fetchone()[0]
            queued = conn.execute(
                "SELECT COUNT(*) FROM agent_tasks WHERE brand_id=? AND status='queued'",
                (b["id"],),
            ).fetchone()[0]
            failed = conn.execute(
                "SELECT COUNT(*) FROM agent_tasks WHERE brand_id=? AND status='failed'",
                (b["id"],),
            ).fetchone()[0]

        if failed > 0:
            health = "alert"
        elif queued == 0 and completed_today == 0:
            health = "warn"
        else:
            health = "good"

        result[slug] = {
            "name":         meta["name"],
            "color":        meta["color"],
            "posts_today":  completed_today,
            "posts_week":   0,  # 詳細分析は analytics agent に任せる
            "target_week":  10,
            "leads_active": 0,
            "media_left":   0,
            "health":       health,
            "link":         meta["link"],
        }

    return result


def get_ceo_priorities() -> list:
    """AI CEO の本日の優先事項（最新のCEO実行ログから取得）"""
    try:
        with db.get_conn() as conn:
            row = conn.execute(
                """SELECT log FROM agent_runs
                   WHERE agent_id='ai-ceo' AND status='completed'
                   ORDER BY completed_at DESC LIMIT 1""",
            ).fetchone()
        if not row or not row["log"]:
            return _default_priorities()

        data = json.loads(row["log"])
        decisions = data.get("decisions", [])
        if not decisions:
            return _default_priorities()

        result = []
        for i, d in enumerate(decisions[:5], 1):
            title = d.get("title", d.get("message", ""))
            agent = d.get("agent", "")
            result.append({
                "order":     i,
                "focus":     title[:40] if title else "—",
                "rationale": f"担当: {agent}" if agent else "今日の重点タスク",
            })
        return result

    except Exception as e:
        log.debug(f"get_ceo_priorities error: {e}")
        return _default_priorities()


def _default_priorities() -> list:
    task_counts = {
        "queued":  len(db.list_tasks(status="queued",  limit=1)),
        "failed":  len(db.list_tasks(status="failed",  limit=1)),
        "running": len(db.list_tasks(status="running", limit=1)),
    }
    return [
        {"order": 1, "focus": f"キュー中タスク: {task_counts['queued']}件",  "rationale": "順次実行中"},
        {"order": 2, "focus": f"実行中タスク: {task_counts['running']}件",   "rationale": "エージェント稼働中"},
        {"order": 3, "focus": f"失敗タスク: {task_counts['failed']}件",      "rationale": "要確認・再試行"},
        {"order": 4, "focus": "朝のディスパッチ: 毎朝5:30自動実行",          "rationale": "AI CEOが各エージェントにタスクを割り当て"},
    ]


def get_ceo_to_president() -> list:
    """CEOから社長への報告事項（エスカレーション + CEO最新ログ）"""
    result = []

    escs = db.list_escalations(status="open")
    for e in escs[:3]:
        result.append({
            "icon":    "🚨",
            "item":    e.get("reason", "")[:60],
            "context": "エスカレーション — 確認・対応必要",
        })

    # 失敗タスクを報告
    failed = db.list_tasks(status="failed", limit=3)
    for t in failed:
        result.append({
            "icon":    "❌",
            "item":    f"タスク失敗: {t.get('title', '')}",
            "context": (t.get("error_message") or "エラー詳細を確認してください")[:80],
        })

    if not result:
        result.append({
            "icon":    "✅",
            "item":    "現在、社長への報告事項はありません",
            "context": "全システム正常稼働中",
        })

    return result


def get_pending_approvals() -> list:
    """承認待ちタスク一覧"""
    with db.get_conn() as conn:
        rows = conn.execute(
            """SELECT a.id, a.title, a.task_id, a.status, a.created_at
               FROM approvals a
               WHERE a.status='pending'
               ORDER BY a.created_at DESC LIMIT 10""",
        ).fetchall()

    result = []
    for r in rows:
        result.append({
            "id":          r["id"][:8],
            "title":       r["title"],
            "task_id":     r["task_id"],
            "status":      r["status"],
            "created_at":  r["created_at"][:16] if r["created_at"] else "—",
        })

    return result


def get_morning_brief() -> dict:
    """朝のブリーフ（本日の統計）"""
    with db.get_conn() as conn:
        completed_today = conn.execute(
            """SELECT COUNT(*) FROM agent_tasks
               WHERE status='completed' AND date(updated_at)=date('now')""",
        ).fetchone()[0]
        total_queued = conn.execute(
            "SELECT COUNT(*) FROM agent_tasks WHERE status='queued'",
        ).fetchone()[0]
        total_failed = conn.execute(
            "SELECT COUNT(*) FROM agent_tasks WHERE status='failed'",
        ).fetchone()[0]
        total_agents = conn.execute(
            "SELECT COUNT(*) FROM ai_agents WHERE is_active=1",
        ).fetchone()[0]

    now = datetime.now()
    return {
        "date":             now.strftime("%Y年%m月%d日"),
        "time":             now.strftime("%H:%M"),
        "completed_today":  completed_today,
        "queued":           total_queued,
        "failed":           total_failed,
        "active_agents":    total_agents,
        "status":           "alert" if total_failed > 3 else "warn" if total_failed > 0 else "ok",
        "headline":         f"本日 {completed_today}件完了 / {total_queued}件待機中",
    }


def get_priority_actions() -> list:
    """優先アクション = 承認待ち + エスカレーション + 失敗タスクから生成"""
    result = []
    try:
        approvals = db.list_all_approvals_rich(status="pending")
        for a in approvals[:3]:
            result.append({
                "icon": "approval",
                "text": f"承認待ち: {a.get('title','')[:50]}",
                "urgency": "high",
                "link": "/publishing",
            })
    except Exception:
        pass
    try:
        escs = db.list_escalations(status="open")
        for e in escs[:3]:
            result.append({
                "icon": "escalation",
                "text": e.get("reason", "")[:60],
                "urgency": "high",
                "link": "/decisions",
            })
    except Exception:
        pass
    try:
        failed = db.list_tasks(status="failed", limit=3)
        for t in failed:
            result.append({
                "icon": "failed",
                "text": f"タスク失敗: {t.get('title','')[:50]}",
                "urgency": "mid",
                "link": "/agents",
            })
    except Exception:
        pass
    return result or [{"icon": "ok", "text": "現在、優先対応事項はありません", "urgency": "low", "link": "/"}]


def get_danger_alerts() -> list:
    """危険アラート = anomaly_alertsテーブルの未解決アラート"""
    try:
        with main_db.get_conn() as conn:
            rows = conn.execute(
                """SELECT severity, message FROM anomaly_alerts
                   WHERE resolved=0 ORDER BY
                   CASE severity WHEN 'alert' THEN 0 WHEN 'warn' THEN 1 ELSE 2 END,
                   created_at DESC LIMIT 10"""
            ).fetchall()
        return [{"level": r["severity"], "text": r["message"]} for r in rows]
    except Exception:
        return []


def get_recent_runs() -> list:
    """最近のエージェント実行ログ（database.pyのactivity_logから取得）"""
    try:
        with main_db.get_conn() as conn:
            rows = conn.execute(
                """SELECT created_at, brand, platform, action, status, detail
                   FROM activity_log ORDER BY created_at DESC LIMIT 10"""
            ).fetchall()
        result = []
        for r in rows:
            ts = r["created_at"] or ""
            time_str = ts[11:16] if len(ts) >= 16 else ts
            result.append({
                "time":   time_str,
                "agent":  r["action"] or "—",
                "brand":  r["brand"] or "全ブランド",
                "result": r["status"] or "ok",
                "detail": (r["detail"] or "")[:60],
            })
        return result
    except Exception:
        return []


def get_unreplied() -> dict:
    """未返信リード数"""
    try:
        with main_db.get_conn() as conn:
            line_count = conn.execute(
                """SELECT COUNT(*) FROM leads
                   WHERE (outcome IS NULL OR outcome='') AND source='line'
                   AND (next_action IS NULL OR next_action='')"""
            ).fetchone()[0]
        return {"line": line_count, "email": 0, "total": line_count}
    except Exception:
        return {"line": 0, "email": 0, "total": 0}


def get_media_shortage() -> list:
    """素材不足ブランド一覧（DBのassets件数から推定）"""
    try:
        with main_db.get_conn() as conn:
            rows = conn.execute(
                """SELECT brand, COUNT(*) as cnt FROM assets
                   WHERE status='active' OR status IS NULL
                   GROUP BY brand"""
            ).fetchall()
        brand_counts = {r["brand"]: r["cnt"] for r in rows}
    except Exception:
        brand_counts = {}

    BRAND_META_LOCAL = {
        "bangkok-peach":   {"name": "BPG",  "color": "#f472b6"},
        "cashflowsupport": {"name": "CSF",  "color": "#fbbf24"},
        "upjapan":         {"name": "UPJ",  "color": "#5b8af5"},
        "dsc-marketing":   {"name": "DSC",  "color": "#34d399"},
        "satoshi-blog":    {"name": "Blog", "color": "#a78bfa"},
    }
    result = []
    for slug, meta in BRAND_META_LOCAL.items():
        cnt = brand_counts.get(slug, 0)
        if cnt < 5:
            days = max(1, cnt)
            level = "alert" if cnt < 3 else "warn"
            result.append({
                "brand": meta["name"], "color": meta["color"],
                "left": cnt, "days": days, "level": level,
            })
    return result


def get_post_shortage() -> list:
    """今週投稿数が少ないブランド（posted=1 が済み）"""
    try:
        with main_db.get_conn() as conn:
            rows = conn.execute(
                """SELECT brand, channel, COUNT(*) as cnt FROM queue_items
                   WHERE posted=1
                   AND date(COALESCE(posted_at, scheduled_at)) >= date('now', '-7 days')
                   GROUP BY brand, channel"""
            ).fetchall()
        posted = {}
        for r in rows:
            key = (r["brand"], r["channel"])
            posted[key] = r["cnt"]
    except Exception:
        posted = {}

    TARGETS = {
        ("cashflowsupport", "instagram"): 5,
        ("bangkok-peach",   "instagram"): 7,
        ("upjapan",         "instagram"): 5,
        ("dsc-marketing",   "instagram"): 7,
    }
    BRAND_COLORS = {
        "cashflowsupport": "#fbbf24", "bangkok-peach": "#f472b6",
        "upjapan": "#5b8af5", "dsc-marketing": "#34d399",
    }
    BRAND_NAMES = {
        "cashflowsupport": "CSF", "bangkok-peach": "BPG",
        "upjapan": "UPJ", "dsc-marketing": "DSC",
    }
    result = []
    for (brand, channel), target in TARGETS.items():
        count = posted.get((brand, channel), 0)
        if count < target * 0.7:
            result.append({
                "brand":      BRAND_NAMES.get(brand, brand),
                "color":      BRAND_COLORS.get(brand, "#888"),
                "platform":   channel.capitalize(),
                "week_count": count,
                "target":     target,
            })
    return result


def get_blog_candidates() -> list:
    """ブログ候補（blog_projectsテーブル）"""
    try:
        with main_db.get_conn() as conn:
            rows = conn.execute(
                """SELECT id, title, engagement_score, brand, status
                   FROM blog_projects ORDER BY engagement_score DESC LIMIT 5"""
            ).fetchall()
        BRAND_COLORS = {
            "dsc-marketing": "#34d399", "satoshi-blog": "#a78bfa",
            "cashflowsupport": "#fbbf24", "bangkok-peach": "#f472b6", "upjapan": "#5b8af5",
        }
        BRAND_NAMES = {
            "dsc-marketing": "DSC", "satoshi-blog": "Blog",
            "cashflowsupport": "CSF", "bangkok-peach": "BPG", "upjapan": "UPJ",
        }
        return [
            {
                "id":         r["id"],
                "title":      r["title"],
                "score":      r["engagement_score"] or 0,
                "brand":      BRAND_NAMES.get(r["brand"], r["brand"]),
                "brand_color":BRAND_COLORS.get(r["brand"], "#888"),
                "status":     r["status"],
                "link":       f"/blog/{r['id']}",
            }
            for r in rows
        ]
    except Exception:
        return []


def get_blog_projects() -> list:
    """ブログプロジェクト一覧"""
    try:
        with main_db.get_conn() as conn:
            rows = conn.execute(
                """SELECT id, brand, title, source_type, source_platform,
                          source_caption, engagement_score, status, created_at
                   FROM blog_projects ORDER BY created_at DESC LIMIT 20"""
            ).fetchall()
        BRAND_COLORS = {
            "dsc-marketing": "#34d399", "satoshi-blog": "#a78bfa",
            "cashflowsupport": "#fbbf24", "bangkok-peach": "#f472b6", "upjapan": "#5b8af5",
        }
        BRAND_NAMES = {
            "dsc-marketing": "DSC", "satoshi-blog": "Blog",
            "cashflowsupport": "CSF", "bangkok-peach": "BPG", "upjapan": "UPJ",
        }
        return [
            {
                "id":               r["id"],
                "brand":            BRAND_NAMES.get(r["brand"], r["brand"]),
                "brand_color":      BRAND_COLORS.get(r["brand"], "#888"),
                "title":            r["title"],
                "source_type":      r["source_type"] or "manual",
                "source_platform":  r["source_platform"] or "—",
                "source_caption":   (r["source_caption"] or "")[:100],
                "engagement_score": r["engagement_score"] or 0,
                "status":           r["status"] or "candidate",
                "created_at":       (r["created_at"] or "")[:10],
            }
            for r in rows
        ]
    except Exception:
        return []


def get_blog_draft_detail(draft_id: int) -> dict:
    """ブログ下書き詳細"""
    try:
        with main_db.get_conn() as conn:
            # database.py の blog_drafts カラム名に合わせる（seo_keywords_json でなく seo_keywords）
            row = conn.execute(
                "SELECT * FROM blog_drafts WHERE id=?", (draft_id,)
            ).fetchone()
            if not row:
                proj = conn.execute(
                    "SELECT * FROM blog_projects WHERE id=?", (draft_id,)
                ).fetchone()
                if proj:
                    return _project_as_draft(dict(proj))
                return {}

            proj = conn.execute(
                "SELECT * FROM blog_projects WHERE id=?", (row["project_id"],)
            ).fetchone()

        d = dict(row)
        d["project"] = dict(proj) if proj else {}
        # database.py では seo_keywords（JSON文字列）、outline_json
        d["seo_keywords"] = json.loads(d.get("seo_keywords") or "[]")
        d["outline"]      = json.loads(d.get("outline_json") or "[]")
        BRAND_COLORS = {
            "dsc-marketing": "#34d399", "satoshi-blog": "#a78bfa",
            "cashflowsupport": "#fbbf24", "bangkok-peach": "#f472b6", "upjapan": "#5b8af5",
        }
        BRAND_NAMES = {
            "dsc-marketing": "DSC", "satoshi-blog": "Blog",
            "cashflowsupport": "CSF", "bangkok-peach": "BPG", "upjapan": "UPJ",
        }
        brand_key = d.get("brand", "")
        d["brand_color"] = BRAND_COLORS.get(brand_key, "#888")
        d["brand"]       = BRAND_NAMES.get(brand_key, brand_key)
        return d
    except Exception as e:
        log.warning(f"get_blog_draft_detail error: {e}")
        return {}


def _project_as_draft(p: dict) -> dict:
    """blog_projectをdraft形式に変換（draftがない場合のフォールバック）"""
    BRAND_COLORS = {
        "dsc-marketing": "#34d399", "satoshi-blog": "#a78bfa",
        "cashflowsupport": "#fbbf24", "bangkok-peach": "#f472b6", "upjapan": "#5b8af5",
    }
    BRAND_NAMES = {
        "dsc-marketing": "DSC", "satoshi-blog": "Blog",
        "cashflowsupport": "CSF", "bangkok-peach": "BPG", "upjapan": "UPJ",
    }
    brand_key = p.get("brand", "")
    return {
        "id":           p["id"],
        "project_id":   p["id"],
        "brand":        BRAND_NAMES.get(brand_key, brand_key),
        "brand_color":  BRAND_COLORS.get(brand_key, "#888"),
        "title":        p.get("title", ""),
        "slug":         "",
        "meta_description": "",
        "seo_keywords": [],
        "word_count":   0,
        "status":       p.get("status", "candidate"),
        "created_by":   "ai",
        "created_at":   p.get("created_at", ""),
        "outline":      [],
        "body_preview": p.get("source_caption", ""),
        "project":      p,
    }


def get_daily_briefs_history() -> list:
    """デイリーブリーフ履歴（daily_briefsテーブル）"""
    try:
        with main_db.get_conn() as conn:
            rows = conn.execute(
                """SELECT * FROM daily_briefs ORDER BY brief_date DESC LIMIT 30"""
            ).fetchall()
        result = []
        for r in rows:
            d = datetime.strptime(r["brief_date"], "%Y-%m-%d") if r["brief_date"] else datetime.now()
            result.append({
                "id":           r["id"],
                "brief_date":   r["brief_date"],
                "date_label":   d.strftime("%Y年%m月%d日"),
                "mood":         r["mood"] or "good",
                "summary":      r["summary"] or "",
                "highlights":   json.loads(r["highlights_json"] or "[]"),
                "kpis":         json.loads(r["kpis_json"] or "{}"),
                "generated_at": r["generated_at"] or "",
            })
        return result
    except Exception:
        return []


def get_ai_recommendations() -> list:
    """AI推奨（ai_recommendationsテーブル）"""
    try:
        with main_db.get_conn() as conn:
            rows = conn.execute(
                """SELECT * FROM ai_recommendations
                   WHERE dismissed=0
                   ORDER BY CASE priority WHEN 'high' THEN 0 WHEN 'mid' THEN 1 ELSE 2 END,
                   created_at DESC LIMIT 10"""
            ).fetchall()
        BRAND_COLORS = {
            "dsc-marketing": "#34d399", "satoshi-blog": "#a78bfa",
            "cashflowsupport": "#fbbf24", "bangkok-peach": "#f472b6", "upjapan": "#5b8af5",
        }
        result = []
        for r in rows:
            brand = r["brand"]
            result.append({
                "id":         r["id"],
                "brand":      brand,
                "brand_color":BRAND_COLORS.get(brand or "", "#6366f1"),
                "category":   r["category"] or "一般",
                "priority":   r["priority"] or "mid",
                "title":      r["title"],
                "body":       r["body"] or "",
                "action_url": r["action_url"] or "/",
            })
        return result
    except Exception:
        return []


def get_anomaly_alerts() -> list:
    """異常アラート（anomaly_alertsテーブル）"""
    try:
        with main_db.get_conn() as conn:
            rows = conn.execute(
                """SELECT * FROM anomaly_alerts
                   ORDER BY resolved ASC,
                   CASE severity WHEN 'alert' THEN 0 WHEN 'warn' THEN 1 ELSE 2 END,
                   created_at DESC LIMIT 20"""
            ).fetchall()
        BRAND_COLORS = {
            "dsc-marketing": "#34d399", "satoshi-blog": "#a78bfa",
            "cashflowsupport": "#fbbf24", "bangkok-peach": "#f472b6", "upjapan": "#5b8af5",
        }
        result = []
        for r in rows:
            brand = r["brand"]
            result.append({
                "id":             r["id"],
                "brand":          brand,
                "brand_color":    BRAND_COLORS.get(brand or "", "#888"),
                "platform":       r["platform"] or "—",
                "metric":         r["metric"] or "—",
                "expected_value": r["expected_value"],
                "actual_value":   r["actual_value"],
                "delta_pct":      r["delta_pct"],
                "severity":       r["severity"] or "warn",
                "message":        r["message"] or "",
                "resolved":       bool(r["resolved"]),
                "created_at":     (r["created_at"] or "")[:16],
                "resolved_at":    (r["resolved_at"] or "")[:16],
            })
        return result
    except Exception:
        return []


def get_strategy_notes() -> list:
    """戦略メモ（strategy_notesテーブル）"""
    try:
        with main_db.get_conn() as conn:
            rows = conn.execute(
                """SELECT * FROM strategy_notes
                   ORDER BY pinned DESC, created_at DESC LIMIT 20"""
            ).fetchall()
        BRAND_COLORS = {
            "dsc-marketing": "#34d399", "satoshi-blog": "#a78bfa",
            "cashflowsupport": "#fbbf24", "bangkok-peach": "#f472b6", "upjapan": "#5b8af5",
        }
        result = []
        for r in rows:
            brand = r["brand"]
            result.append({
                "id":         r["id"],
                "brand":      brand,
                "brand_color":BRAND_COLORS.get(brand or "", "#6366f1") if brand else None,
                "author":     r["author"] or "AI CEO",
                "category":   r["category"] or "一般",
                "pinned":     bool(r["pinned"]),
                "note":       r["note"],
                "created_at": (r["created_at"] or "")[:10],
            })
        return result
    except Exception:
        return []


def get_performance_snapshot() -> dict:
    """パフォーマンススナップショット（複数テーブルから集計）"""
    now = datetime.now()
    week_ago = (now - timedelta(days=7)).strftime("%Y-%m-%d")

    # 直近7日の投稿数・リード数（database.py のテーブル）
    try:
        with main_db.get_conn() as conn:
            total_posts = conn.execute(
                """SELECT COUNT(*) FROM queue_items
                   WHERE posted=1 AND date(COALESCE(posted_at, scheduled_at)) >= ?""",
                (week_ago,)
            ).fetchone()[0]
            new_leads = conn.execute(
                """SELECT COUNT(*) FROM leads WHERE date(created_at) >= ?""",
                (week_ago,)
            ).fetchone()[0]
            brand_rows = conn.execute(
                """SELECT brand, COUNT(*) as cnt FROM queue_items
                   WHERE posted=1 AND date(COALESCE(posted_at, scheduled_at)) >= ?
                   GROUP BY brand""",
                (week_ago,)
            ).fetchall()
            brand_posts = {r["brand"]: r["cnt"] for r in brand_rows}
            daily_rows = conn.execute(
                """SELECT date(COALESCE(posted_at, scheduled_at)) as d, COUNT(*) as cnt
                   FROM queue_items
                   WHERE posted=1 AND date(COALESCE(posted_at, scheduled_at)) >= ?
                   GROUP BY d ORDER BY d""",
                (week_ago,)
            ).fetchall()
            lead_rows = conn.execute(
                """SELECT date(created_at) as d, COUNT(*) as cnt FROM leads
                   WHERE date(created_at) >= ?
                   GROUP BY d ORDER BY d""",
                (week_ago,)
            ).fetchall()
    except Exception:
        total_posts = 0
        new_leads = 0
        brand_posts = {}
        daily_rows = []
        lead_rows = []

    # 未承認案件数（org_database の agent_tasks）
    try:
        pending = len(db.list_tasks(status="queued", limit=200)) + len(db.list_tasks(status="waiting_approval", limit=200))
    except Exception:
        pending = 0

    # パフォーマンススナップショットテーブルから最新データ
    try:
        with main_db.get_conn() as conn:
            conn.execute(
                """SELECT brand, metric_key, metric_value, delta_pct
                   FROM performance_snapshots
                   WHERE date(snap_date) >= ? ORDER BY snap_date DESC""",
                (week_ago,)
            ).fetchall()
    except Exception:
        pass

    BRAND_META_LOCAL = {
        "dsc-marketing":   {"name": "DSC",  "color": "#34d399"},
        "upjapan":         {"name": "UPJ",  "color": "#5b8af5"},
        "cashflowsupport": {"name": "CSF",  "color": "#fbbf24"},
        "bangkok-peach":   {"name": "BPG",  "color": "#f472b6"},
        "satoshi-blog":    {"name": "Blog", "color": "#a78bfa"},
    }

    brand_metrics = []
    for slug, meta in BRAND_META_LOCAL.items():
        posts = brand_posts.get(slug, 0)
        brand_metrics.append({
            "brand":      meta["name"],
            "color":      meta["color"],
            "posts":      posts,
            "engagement": 0.0,
            "leads":      0,
            "meo_score":  0,
            "trend":      "stable",
        })

    date_map = {(now - timedelta(days=i)).strftime("%Y-%m-%d"): 0 for i in range(6, -1, -1)}
    for r in daily_rows:
        if r["d"] in date_map:
            date_map[r["d"]] = r["cnt"]
    lead_map = {(now - timedelta(days=i)).strftime("%Y-%m-%d"): 0 for i in range(6, -1, -1)}
    for r in lead_rows:
        if r["d"] in lead_map:
            lead_map[r["d"]] = r["cnt"]

    labels = [(now - timedelta(days=i)).strftime("%-m/%-d") for i in range(6, -1, -1)]

    return {
        "period":       "過去7日間",
        "generated_at": now.strftime("%Y-%m-%d %H:%M"),
        "summary_kpis": [
            {"label": "総投稿数",   "value": str(total_posts), "delta": "直近7日", "direction": "up",   "color": "green"},
            {"label": "新規リード", "value": str(new_leads),   "delta": "直近7日", "direction": "up",   "color": "green"},
            {"label": "未承認案件", "value": str(pending),     "delta": "現在",    "direction": "down" if pending > 0 else "up", "color": "yellow" if pending > 0 else "green"},
        ],
        "brand_metrics": brand_metrics,
        "top_posts": [],
        "weekly_trend": {
            "labels": labels,
            "posts":  list(date_map.values()),
            "leads":  list(lead_map.values()),
        },
    }
