"""
SQLite データベースモジュール
YAMLファイルの代わりに使う安全なデータストア

テーブル:
  - leads          : リード（見込み客）
  - queue_items    : 投稿キュー
  - performance_log: SNSパフォーマンス記録
  - decisions      : 判断待ちキュー
"""

from __future__ import annotations

import json
import sqlite3
import logging
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / "data" / "upj.db"


def init_db():
    """データベースとテーブルを初期化する"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_conn() as conn:
        conn.executescript("""
        -- ────────────── リード ──────────────
        CREATE TABLE IF NOT EXISTS leads (
            lead_id     TEXT PRIMARY KEY,
            created_at  TEXT NOT NULL,
            brand       TEXT,
            name        TEXT,
            company     TEXT,
            email       TEXT,
            phone       TEXT,
            line_user_id TEXT,
            stage       TEXT DEFAULT 'L1',
            last_contact TEXT,
            outcome     TEXT,
            next_action TEXT,
            notes       TEXT,
            followup_sent TEXT DEFAULT '[]',
            source      TEXT DEFAULT 'line',
            updated_at  TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_leads_brand   ON leads(brand);
        CREATE INDEX IF NOT EXISTS idx_leads_stage   ON leads(stage);
        CREATE INDEX IF NOT EXISTS idx_leads_outcome ON leads(outcome);

        -- ────────────── 投稿キュー ──────────────
        CREATE TABLE IF NOT EXISTS queue_items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            brand       TEXT NOT NULL,
            channel     TEXT NOT NULL,
            media_type  TEXT DEFAULT 'image',
            caption     TEXT,
            text        TEXT,
            message     TEXT,
            title       TEXT,
            content     TEXT,
            image_url   TEXT,
            video_url   TEXT,
            hashtags    TEXT,
            scheduled_at TEXT,
            posted      INTEGER DEFAULT 0,
            posted_at   TEXT,
            source      TEXT DEFAULT 'manual',
            topic       TEXT,
            filename    TEXT UNIQUE,
            created_at  TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_queue_brand   ON queue_items(brand);
        CREATE INDEX IF NOT EXISTS idx_queue_channel ON queue_items(channel);
        CREATE INDEX IF NOT EXISTS idx_queue_posted  ON queue_items(posted);
        CREATE INDEX IF NOT EXISTS idx_queue_sched   ON queue_items(scheduled_at);

        -- ────────────── パフォーマンスログ ──────────────
        CREATE TABLE IF NOT EXISTS performance_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            brand           TEXT,
            platform        TEXT,
            topic           TEXT,
            post_id         TEXT UNIQUE,
            caption_head    TEXT,
            likes           INTEGER DEFAULT 0,
            reach           INTEGER DEFAULT 0,
            comments        INTEGER DEFAULT 0,
            saves           INTEGER DEFAULT 0,
            plays           INTEGER DEFAULT 0,
            engagement_rate REAL DEFAULT 0,
            play_rate       REAL DEFAULT 0,
            posted_hour     INTEGER,
            logged_at       TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_perf_brand    ON performance_log(brand);
        CREATE INDEX IF NOT EXISTS idx_perf_platform ON performance_log(platform);

        -- ────────────── 判断待ち ──────────────
        CREATE TABLE IF NOT EXISTS decisions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            filename    TEXT UNIQUE,
            type        TEXT,
            reason      TEXT NOT NULL,
            context     TEXT DEFAULT '{}',
            resolved    INTEGER DEFAULT 0,
            created_at  TEXT NOT NULL,
            resolved_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_dec_resolved ON decisions(resolved);

        -- ────────────── 操作ログ ──────────────
        CREATE TABLE IF NOT EXISTS activity_log (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            action     TEXT NOT NULL,
            brand      TEXT,
            platform   TEXT,
            detail     TEXT,
            status     TEXT DEFAULT 'ok',
            created_at TEXT NOT NULL
        );
        """)
    log.info(f"データベース初期化完了: {DB_PATH}")


@contextmanager
def get_conn():
    """SQLite接続のコンテキストマネージャー（自動コミット・ロールバック）"""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")   # 並列アクセスを安全に
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ══════════════════════════════════════════
# LEADS
# ══════════════════════════════════════════

def upsert_lead(data: dict) -> str:
    """リードを作成または更新。lead_id を返す。"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lid = data.get("lead_id") or _new_lead_id()
    followup = json.dumps(data.get("followup_sent", []))
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO leads
                (lead_id,created_at,brand,name,company,email,phone,
                 line_user_id,stage,last_contact,outcome,next_action,
                 notes,followup_sent,source,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(lead_id) DO UPDATE SET
                brand=excluded.brand, name=excluded.name,
                company=excluded.company, email=excluded.email,
                phone=excluded.phone, line_user_id=excluded.line_user_id,
                stage=excluded.stage, last_contact=excluded.last_contact,
                outcome=excluded.outcome, next_action=excluded.next_action,
                notes=excluded.notes, followup_sent=excluded.followup_sent,
                updated_at=excluded.updated_at
        """, (
            lid, data.get("created_at", now[:10]),
            data.get("brand"), data.get("name"), data.get("company"),
            data.get("email"), data.get("phone"), data.get("line_user_id"),
            data.get("stage", "L1"), data.get("last_contact"),
            data.get("outcome"), data.get("next_action"),
            data.get("notes"), followup,
            data.get("source", "line"), now,
        ))
    return lid


def get_lead(lead_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM leads WHERE lead_id=?", (lead_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    d["followup_sent"] = json.loads(d.get("followup_sent") or "[]")
    return d


def list_leads(brand: str = "", stage: str = "", outcome: str = "active",
               limit: int = 200) -> list[dict]:
    sql = "SELECT * FROM leads WHERE 1=1"
    params: list = []
    if brand:
        sql += " AND brand=?"; params.append(brand)
    if stage:
        sql += " AND stage=?"; params.append(stage)
    if outcome == "active":
        sql += " AND (outcome IS NULL OR outcome='')"
    elif outcome:
        sql += " AND outcome=?"; params.append(outcome)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    result = []
    for row in rows:
        d = dict(row)
        d["followup_sent"] = json.loads(d.get("followup_sent") or "[]")
        result.append(d)
    return result


def update_lead_stage(lead_id: str, stage: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        conn.execute(
            "UPDATE leads SET stage=?, updated_at=? WHERE lead_id=?",
            (stage, now, lead_id)
        )


def _new_lead_id() -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    with get_conn() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM leads WHERE lead_id LIKE ?", (f"{today}-%",)
        ).fetchone()[0]
    return f"{today}-{count+1:03d}"


# ══════════════════════════════════════════
# QUEUE
# ══════════════════════════════════════════

def enqueue(data: dict) -> int:
    """投稿をキューに追加。id を返す。"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        cur = conn.execute("""
            INSERT OR IGNORE INTO queue_items
                (brand,channel,media_type,caption,text,message,title,content,
                 image_url,video_url,hashtags,scheduled_at,posted,source,
                 topic,filename,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,0,?,?,?,?)
        """, (
            data.get("brand"), data.get("channel"),
            data.get("media_type", "image"),
            data.get("caption"), data.get("text"),
            data.get("message"), data.get("title"), data.get("content"),
            data.get("image_url"), data.get("video_url"),
            data.get("hashtags"), data.get("scheduled_at"),
            data.get("source", "manual"), data.get("topic"),
            data.get("filename"), now,
        ))
    return cur.lastrowid


def list_queue(brand: str = "", channel: str = "",
               pending_only: bool = True) -> list[dict]:
    sql = "SELECT * FROM queue_items WHERE 1=1"
    params: list = []
    if brand:
        sql += " AND brand=?"; params.append(brand)
    if channel:
        sql += " AND channel=?"; params.append(channel)
    if pending_only:
        sql += " AND posted=0"
    sql += " ORDER BY COALESCE(scheduled_at, created_at) ASC"
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def next_pending(brand: str, channel: str) -> dict | None:
    """次の投稿可能アイテムを返す（scheduled_at が未来のものはスキップ）"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    with get_conn() as conn:
        row = conn.execute("""
            SELECT * FROM queue_items
            WHERE brand=? AND channel=? AND posted=0
              AND (scheduled_at IS NULL OR scheduled_at <= ?)
            ORDER BY COALESCE(scheduled_at, created_at) ASC
            LIMIT 1
        """, (brand, channel, now)).fetchone()
    return dict(row) if row else None


def mark_posted(item_id: int):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        conn.execute(
            "UPDATE queue_items SET posted=1, posted_at=? WHERE id=?",
            (now, item_id)
        )


def delete_queue_item(item_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM queue_items WHERE id=?", (item_id,))


def count_pending(brand: str = "", channel: str = "") -> int:
    sql = "SELECT COUNT(*) FROM queue_items WHERE posted=0"
    params: list = []
    if brand:
        sql += " AND brand=?"; params.append(brand)
    if channel:
        sql += " AND channel=?"; params.append(channel)
    with get_conn() as conn:
        return conn.execute(sql, params).fetchone()[0]


# ══════════════════════════════════════════
# PERFORMANCE LOG
# ══════════════════════════════════════════

def log_performance(data: dict):
    with get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO performance_log
                (brand,platform,topic,post_id,caption_head,
                 likes,reach,comments,saves,plays,
                 engagement_rate,play_rate,posted_hour,logged_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            data.get("brand"), data.get("platform"),
            data.get("topic"), data.get("post_id"),
            data.get("caption_head","")[:80],
            data.get("metrics",{}).get("likes", 0),
            data.get("metrics",{}).get("reach", 0),
            data.get("metrics",{}).get("comments", 0),
            data.get("metrics",{}).get("saves", 0),
            data.get("metrics",{}).get("plays", 0),
            data.get("engagement_rate", 0),
            data.get("play_rate", 0),
            data.get("posted_hour"),
            data.get("logged_at", datetime.now().strftime("%Y-%m-%d %H:%M")),
        ))


def get_performance_summary_db(brand: str, platform: str = "instagram",
                                limit: int = 30) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT * FROM performance_log
            WHERE brand=? AND platform=?
            ORDER BY logged_at DESC LIMIT ?
        """, (brand, platform, limit)).fetchall()
    return [dict(r) for r in rows]


# ══════════════════════════════════════════
# DECISIONS
# ══════════════════════════════════════════

def add_decision(reason: str, type_: str = "要確認",
                 context: dict | None = None, filename: str = "") -> int:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not filename:
        filename = f"decision_{now.replace(' ','_').replace(':','')}.yaml"
    with get_conn() as conn:
        cur = conn.execute("""
            INSERT OR IGNORE INTO decisions (filename,type,reason,context,created_at)
            VALUES (?,?,?,?,?)
        """, (filename, type_, reason, json.dumps(context or {}), now))
    return cur.lastrowid


def list_decisions(resolved: bool = False) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM decisions WHERE resolved=? ORDER BY created_at DESC",
            (1 if resolved else 0,)
        ).fetchall()
    result = []
    for row in rows:
        d = dict(row)
        d["context"] = json.loads(d.get("context") or "{}")
        result.append(d)
    return result


def resolve_decision(decision_id: int):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        conn.execute(
            "UPDATE decisions SET resolved=1, resolved_at=? WHERE id=?",
            (now, decision_id)
        )


# ══════════════════════════════════════════
# ACTIVITY LOG
# ══════════════════════════════════════════

def log_activity(action: str, brand: str = "", platform: str = "",
                 detail: str = "", status: str = "ok"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO activity_log (action,brand,platform,detail,status,created_at)
            VALUES (?,?,?,?,?,?)
        """, (action, brand, platform, detail, status, now))


def list_activity(limit: int = 50) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM activity_log ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


# ══════════════════════════════════════════
# STATS
# ══════════════════════════════════════════

def get_stats() -> dict:
    """ダッシュボード用の統計を一括取得"""
    with get_conn() as conn:
        ig_pending   = conn.execute(
            "SELECT COUNT(*) FROM queue_items WHERE channel='instagram' AND posted=0"
        ).fetchone()[0]
        line_pending = conn.execute(
            "SELECT COUNT(*) FROM queue_items WHERE channel='line' AND posted=0"
        ).fetchone()[0]
        leads_active = conn.execute(
            "SELECT COUNT(*) FROM leads WHERE (outcome IS NULL OR outcome='') AND stage!='L5'"
        ).fetchone()[0]
        leads_contracted = conn.execute(
            "SELECT COUNT(*) FROM leads WHERE outcome='contracted'"
        ).fetchone()[0]
        leads_total  = conn.execute(
            "SELECT COUNT(*) FROM leads"
        ).fetchone()[0]
        decisions_open = conn.execute(
            "SELECT COUNT(*) FROM decisions WHERE resolved=0"
        ).fetchone()[0]
        # 今月の新規リード
        this_month = datetime.now().strftime("%Y-%m")
        leads_new_month = conn.execute(
            "SELECT COUNT(*) FROM leads WHERE created_at LIKE ?",
            (f"{this_month}%",)
        ).fetchone()[0]
        # パイプライン
        funnel = {}
        for stage in ("L1","L2","L3","L4","L5"):
            funnel[stage] = conn.execute(
                "SELECT COUNT(*) FROM leads WHERE stage=? AND (outcome IS NULL OR outcome='')",
                (stage,)
            ).fetchone()[0]

    cvr = round(leads_contracted / leads_total * 100, 1) if leads_total > 0 else 0
    return {
        "ig_pending":      ig_pending,
        "line_pending":    line_pending,
        "leads_active":    leads_active,
        "leads_contracted":leads_contracted,
        "leads_new_month": leads_new_month,
        "decisions_open":  decisions_open,
        "cvr":             cvr,
        "mrr":             0,
        "funnel":          funnel,
    }


def get_monthly_leads(months: int = 6) -> dict:
    """月別リード数"""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as cnt
            FROM leads
            GROUP BY month
            ORDER BY month DESC
            LIMIT ?
        """, (months,)).fetchall()
    data = list(reversed(rows))
    return {
        "labels": [r["month"] for r in data],
        "values": [r["cnt"]   for r in data],
    }


# ══════════════════════════════════════════
# BACKUP
# ══════════════════════════════════════════

def backup_db(backup_dir: str = ""):
    """データベースをバックアップ"""
    import shutil
    bdir = Path(backup_dir) if backup_dir else DB_PATH.parent / "backups"
    bdir.mkdir(parents=True, exist_ok=True)
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = bdir / f"upj_{ts}.db"
    shutil.copy2(DB_PATH, dest)
    # 古いバックアップを削除（30日以上前）
    cutoff = datetime.now().timestamp() - 30 * 86400
    for f in bdir.glob("upj_*.db"):
        if f.stat().st_mtime < cutoff:
            f.unlink()
    log.info(f"バックアップ完了: {dest}")
    return str(dest)


# ══════════════════════════════════════════
# MIGRATION: YAML → SQLite
# ══════════════════════════════════════════

def migrate_from_yaml():
    """既存のYAMLファイルをSQLiteに移行する（初回のみ）"""
    import yaml
    base = Path(__file__).parent

    migrated = {"leads": 0, "queue": 0, "performance": 0, "decisions": 0}

    # リード移行
    leads_dir = base.parent / "sales-system" / "leads"
    if leads_dir.exists():
        for f in leads_dir.glob("*.yaml"):
            try:
                data = yaml.safe_load(f.read_text(encoding="utf-8"))
                if data and "lead_id" in data:
                    upsert_lead(data)
                    migrated["leads"] += 1
            except Exception as e:
                log.warning(f"リード移行スキップ {f.name}: {e}")

    # キュー移行
    queue_root = base / "content_queue"
    if queue_root.exists():
        for yaml_file in queue_root.rglob("*.yaml"):
            if "calendar" in str(yaml_file):
                continue
            try:
                data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
                if data and isinstance(data, dict) and "brand" in data:
                    data["filename"] = yaml_file.name
                    enqueue(data)
                    migrated["queue"] += 1
            except Exception as e:
                log.warning(f"キュー移行スキップ {yaml_file.name}: {e}")

    # パフォーマンスログ移行
    perf_path = base / "logs" / "performance_log.yaml"
    if perf_path.exists():
        try:
            items = yaml.safe_load(perf_path.read_text(encoding="utf-8")) or []
            for item in items:
                log_performance(item)
                migrated["performance"] += 1
        except Exception as e:
            log.warning(f"パフォーマンスログ移行エラー: {e}")

    # 判断待ち移行
    decision_dir = base / "decision_queue"
    if decision_dir.exists():
        for f in decision_dir.glob("*.yaml"):
            try:
                data = yaml.safe_load(f.read_text(encoding="utf-8"))
                if data and not data.get("resolved"):
                    add_decision(
                        reason=data.get("reason",""),
                        type_=data.get("type","要確認"),
                        context=data.get("context",{}),
                        filename=f.name,
                    )
                    migrated["decisions"] += 1
            except Exception as e:
                log.warning(f"判断待ち移行スキップ {f.name}: {e}")

    log.info(f"移行完了: {migrated}")
    return migrated


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("データベース初期化中...")
    init_db()
    print("YAMLデータを移行中...")
    result = migrate_from_yaml()
    print(f"移行完了: {result}")
    print(f"データベース: {DB_PATH}")
