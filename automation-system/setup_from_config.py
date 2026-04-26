"""
全体セットアップスクリプト
===========================
os_config.yaml の定義を読み込み、DBに一括登録します。
冪等 — 何度実行しても同じ状態になります。

実行:
  cd automation-system
  python3 setup_from_config.py
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import yaml
import org_database as db
import database as main_db

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

CFG_PATH = Path(__file__).parent / "config" / "os_config.yaml"

# ── ブランドスラッグ → DB brand_id マッピング ─────────────────
BRAND_SLUG_MAP = {
    "upjapan":         "upj",
    "dsc-marketing":   "dsc",
    "cashflowsupport": "cfj",
    "bangkok-peach":   "bangkok-peach",
    "satoshi-blog":    "satoshi-blog",
}


def _get_or_create_user(name: str, user_type: str, role_id: str,
                         org_id: str, email: str = "") -> str:
    with db.get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM users WHERE role_id=? AND name=? LIMIT 1",
            (role_id, name),
        ).fetchone()
        if row:
            return row["id"]
        uid = db._uid()
        conn.execute(
            """INSERT OR IGNORE INTO users
               (id,organization_id,role_id,user_type,name,email,is_active,created_at)
               VALUES (?,?,?,?,?,?,1,?)""",
            (uid, org_id, role_id, user_type, name, email, db._now()),
        )
        return uid


def _get_brand_id(slug: str) -> str | None:
    with db.get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM brands WHERE slug=?", (slug,)
        ).fetchone()
    return row["id"] if row else None


def _get_org_id() -> str | None:
    with db.get_conn() as conn:
        row = conn.execute("SELECT id FROM organizations LIMIT 1").fetchone()
    return row["id"] if row else None


def run():
    log.info("=== 全体セットアップ開始 ===")

    # ── 1. スキーマ初期化 ────────────────────────────────────
    log.info("スキーマ初期化...")
    main_db.init_db()   # automation DB（投稿・リード・コンテンツキュー等）
    db.init_org_db()    # 組織・AIガバナンス DB

    # ── 2. os_config.yaml 読み込み ───────────────────────────
    cfg = yaml.safe_load(CFG_PATH.read_text(encoding="utf-8"))
    president_cfg = cfg.get("president", {})
    ceo_cfg       = cfg.get("ai_ceo", {})
    agents_cfg    = cfg.get("agents", [])

    # ── 3. 組織確認 ──────────────────────────────────────────
    org_id = _get_org_id()
    if not org_id:
        log.warning("組織が未登録です。先に seed_org.py を実行してください。")
        log.info("seed_org.py を自動実行します...")
        import seed_org
        result = seed_org.seed()
        org_id = result["organization_id"]
        log.info(f"組織登録完了: {org_id}")

    log.info(f"組織ID: {org_id}")

    # ── 4. Human President の user ───────────────────────────
    log.info(f"President: {president_cfg.get('name', 'Satoshi')} を登録...")
    president_user_id = _get_or_create_user(
        name      = president_cfg.get("name", "Satoshi"),
        user_type = "human",
        role_id   = "human_president",
        org_id    = org_id,
        email     = "satoshi6667s@gmail.com",
    )
    log.info(f"  President user_id: {president_user_id}")

    # ── 5. AI CEO ────────────────────────────────────────────
    log.info(f"AI CEO: {ceo_cfg.get('name', 'CEO Agent')} を登録...")
    ceo_user_id = _get_or_create_user(
        name      = ceo_cfg.get("name", "CEO Agent"),
        user_type = "ai",
        role_id   = "ai_ceo",
        org_id    = org_id,
    )
    ceo_agent_id = db.create_ai_agent(
        user_id       = ceo_user_id,
        agent_type    = "ceo",
        reports_to_id = president_user_id,
        model         = ceo_cfg.get("model", "claude-sonnet-4-6"),
        system_prompt = ceo_cfg.get("description", ""),
        agent_id      = ceo_cfg.get("id", "ai-ceo"),
    )
    log.info(f"  AI CEO agent_id: {ceo_agent_id}")

    # ── 6. 各エージェントを登録 ──────────────────────────────
    log.info(f"エージェント {len(agents_cfg)} 件を登録...")
    for a in agents_cfg:
        yaml_id     = a["id"]
        name        = a.get("name", yaml_id)
        model       = a.get("model", "claude-haiku-4-5-20251001")
        description = a.get("description", "")
        tools       = a.get("tools", [])
        brand_slug  = a.get("brand") or ""

        # AI user を作成（重複は無視）
        agent_user_id = _get_or_create_user(
            name      = name,
            user_type = "ai",
            role_id   = "ai_agent",
            org_id    = org_id,
        )

        # エージェント登録（YAML ID を DB ID として使用）
        db.create_ai_agent(
            user_id       = agent_user_id,
            agent_type    = a.get("role", "content").lower().replace(" ", "_"),
            reports_to_id = ceo_user_id,
            model         = model,
            system_prompt = description,
            agent_id      = yaml_id,   # ← YAML ID を DB ID として使う
        )

        # ケイパビリティ（ツール）を登録
        db.upsert_agent_capabilities(yaml_id, tools)

        # ブランドへの割り当て
        brand_db_slug = BRAND_SLUG_MAP.get(brand_slug, brand_slug)
        brand_id = _get_brand_id(brand_db_slug) if brand_slug else None
        if brand_id:
            with db.get_conn() as conn:
                conn.execute(
                    """INSERT OR IGNORE INTO agent_assignments
                       (agent_id, brand_id, is_primary, created_at)
                       VALUES (?,?,1,?)""",
                    (yaml_id, brand_id, db._now()),
                )

        log.info(f"  [{yaml_id}] {name} tools={tools}")

    # ── 7. DB 確認 ───────────────────────────────────────────
    with db.get_conn() as conn:
        agent_count = conn.execute("SELECT COUNT(*) FROM ai_agents").fetchone()[0]
        brand_count = conn.execute("SELECT COUNT(*) FROM brands").fetchone()[0]
        task_count  = conn.execute("SELECT COUNT(*) FROM agent_tasks").fetchone()[0]

    log.info("=== セットアップ完了 ===")
    log.info(f"  組織: {org_id}")
    log.info(f"  ブランド数: {brand_count}")
    log.info(f"  エージェント数: {agent_count}")
    log.info(f"  タスク数: {task_count}")
    return True


if __name__ == "__main__":
    ok = run()
    sys.exit(0 if ok else 1)
