"""
組織・AIガバナンス シードスクリプト

実行: python seed_org.py

冪等 (idempotent) — 何度実行しても同じ状態になる。
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# automation-system/ を import パスに追加
sys.path.insert(0, str(Path(__file__).parent))

import org_database as db
from repositories.org_repo import OrganizationRepo, RoleRepo
from repositories.ai_repo import AiCeoRepo, AgentRepo

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)


# ══════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════

def seed():
    log.info("=== 組織・AIガバナンス シード開始 ===")

    # ── 0. スキーマ初期化 ─────────────────────
    db.init_org_db()

    org_repo   = OrganizationRepo()
    role_repo  = RoleRepo()
    ceo_repo   = AiCeoRepo()
    agent_repo = AgentRepo()

    # ── 1. ロール ─────────────────────────────
    log.info("ロール作成...")
    role_repo.seed_defaults()

    # ── 2. 組織 ───────────────────────────────
    log.info("組織作成...")
    org_id = org_repo.get_or_create(
        name="Universal Planet Japan",
        slug="upj-group",
        description="UPJ グループ — 複数ブランドを展開するデジタルマーケティング企業",
    )

    # ── 3. ブランド ───────────────────────────
    log.info("ブランド作成...")

    brands_def = [
        dict(slug="upj",          name="UPJ（Universal Planet Japan）", short_name="UPJ",
             color="#5b8af5", url="https://upjapan.co.jp/",
             description="メインブランド"),
        dict(slug="dsc",          name="DSc Marketing", short_name="DSC",
             color="#34d399", url="https://dsc-marketing.com/",
             description="デジタルマーケティング支援"),
        dict(slug="cfj",          name="CashFlow Japan", short_name="CFJ/CSF",
             color="#fbbf24", url="https://cashflowsupport.jp/",
             description="cashflowsupport (alias: CSF)"),
        dict(slug="bangkok-peach",name="Bangkok Peach Group", short_name="BPG",
             color="#f472b6", url="https://bangkok-peach-group.com/",
             description="タイ拠点グループ"),
        dict(slug="satoshi-blog", name="Satoshi Life Blog", short_name="Blog",
             color="#a78bfa", url="https://satoshi-life.site/blog/",
             description="個人ブログ"),
    ]

    brand_ids: dict[str, str] = {}
    for b in brands_def:
        bid = org_repo.get_or_create_brand(
            organization_id=org_id,
            name=b["name"], slug=b["slug"],
            short_name=b.get("short_name",""),
            color=b.get("color",""),
            url=b.get("url",""),
            description=b.get("description",""),
        )
        brand_ids[b["slug"]] = bid
        log.info(f"  ブランド: {b['name']} → {bid}")

    all_brand_ids = list(brand_ids.values())

    # ── 4. Human President ───────────────────
    log.info("Human President 作成...")
    president_id = org_repo.create_user(
        organization_id=org_id,
        name="Satoshi（Human President）",
        user_type="human",
        role_id="human_president",
        email="satoshi6667s@gmail.com",
    )
    # 全ブランドにadmin権限
    for bid in all_brand_ids:
        org_repo.grant(president_id, bid, "admin")
    log.info(f"  Human President → {president_id}")

    # ── 5. AI CEO ────────────────────────────
    log.info("AI CEO 作成...")
    ai_ceo_user_id = org_repo.create_user(
        organization_id=org_id,
        name="AI CEO",
        user_type="ai",
        role_id="ai_ceo",
    )
    ceo_profile_id = ceo_repo.setup(
        user_id=ai_ceo_user_id,
        reports_to_user_id=president_id,
        persona={
            "style": "strategic, concise, data-driven",
            "language": "ja",
            "escalation_threshold": "high_impact_or_irreversible",
        },
        decision_authority={
            "can_approve_tasks": True,
            "max_spend_usd": 100,
            "requires_president_approval": ["contract", "hire", "major_pivot"],
        },
    )
    for bid in all_brand_ids:
        org_repo.grant(ai_ceo_user_id, bid, "admin")
    log.info(f"  AI CEO user → {ai_ceo_user_id}, profile → {ceo_profile_id}")

    # ── 6. AI Agents ─────────────────────────
    log.info("AI Agents 作成...")

    agents_def = [
        dict(
            name="Chief of Staff Agent",
            agent_type="chief_of_staff",
            system_prompt="組織全体のタスク調整・優先順位付け・エスカレーション判断を担当する参謀AI。",
            capabilities=["task_routing", "prioritization", "escalation", "reporting"],
            brand_ids=all_brand_ids,
        ),
        dict(
            name="NoiMos Agent",
            agent_type="noimos",
            system_prompt="SNS投稿・コンテンツ生成・ブランドボイス維持を担当するクリエイティブAI。",
            capabilities=["instagram_post", "threads_post", "facebook_post", "content_generation"],
            brand_ids=[brand_ids["upj"], brand_ids["dsc"]],
        ),
        dict(
            name="Story Autopilot Agent",
            agent_type="story_autopilot",
            system_prompt="Instagram/Facebook ストーリーの自動生成・スケジューリングを担当するAI。",
            capabilities=["story_generation", "story_scheduling", "story_analytics"],
            brand_ids=[brand_ids["upj"], brand_ids["dsc"], brand_ids["bangkok-peach"]],
        ),
        dict(
            name="MEO Agent",
            agent_type="meo",
            system_prompt="Google ビジネスプロフィールの更新・MEO最適化・クチコミ管理を担当するAI。",
            capabilities=["gbp_update", "review_monitoring", "meo_optimization", "post_gbp"],
            brand_ids=[brand_ids["upj"], brand_ids["cfj"], brand_ids["bangkok-peach"]],
        ),
        dict(
            name="Reputation Agent",
            agent_type="reputation",
            system_prompt="レビュー・クチコミ・ブランド評判の監視と返信を担当するAI。",
            capabilities=["review_reply", "sentiment_analysis", "reputation_report"],
            brand_ids=all_brand_ids,
        ),
        dict(
            name="Asset Brain Agent",
            agent_type="asset_brain",
            system_prompt="画像・動画・クリエイティブ資産の管理・タグ付け・検索を担当するAI。",
            capabilities=["asset_tagging", "asset_search", "asset_generation", "drive_sync"],
            brand_ids=all_brand_ids,
        ),
        dict(
            name="Blog Growth Agent",
            agent_type="blog_growth",
            system_prompt="SEO記事の生成・キーワード調査・WordPress投稿を担当するAI。",
            capabilities=["wordpress_post", "seo_research", "article_generation", "internal_linking"],
            brand_ids=[brand_ids["satoshi-blog"], brand_ids["dsc"]],
        ),
        dict(
            name="Campaign Agent",
            agent_type="campaign",
            system_prompt="広告キャンペーンの設計・実行・最適化を担当するAI。",
            capabilities=["campaign_design", "ad_copy", "campaign_monitoring", "budget_optimization"],
            brand_ids=[brand_ids["upj"], brand_ids["dsc"], brand_ids["cfj"]],
        ),
        dict(
            name="Analytics Agent",
            agent_type="analytics",
            system_prompt="SNS・サイト・広告のパフォーマンス分析とレポート生成を担当するAI。",
            capabilities=["performance_report", "kpi_tracking", "anomaly_detection", "forecast"],
            brand_ids=all_brand_ids,
        ),
        dict(
            name="Automation Runner Agent",
            agent_type="automation_runner",
            system_prompt="スケジュール実行・API連携・ワークフロートリガーを担当するAI。",
            capabilities=["scheduler", "api_trigger", "webhook", "workflow_run"],
            brand_ids=all_brand_ids,
        ),
        dict(
            name="Approval & Compliance Agent",
            agent_type="approval_compliance",
            system_prompt="承認フロー管理・コンプライアンスチェック・ポリシー適用を担当するAI。",
            capabilities=["approval_routing", "compliance_check", "policy_enforcement", "audit_log"],
            brand_ids=all_brand_ids,
        ),
        dict(
            name="Growth Lab Agent",
            agent_type="growth_lab",
            system_prompt="A/Bテスト・実験設計・グロースハック施策の立案と測定を担当するAI。",
            capabilities=["ab_test", "experiment_design", "growth_analysis", "hypothesis_testing"],
            brand_ids=[brand_ids["upj"], brand_ids["dsc"], brand_ids["satoshi-blog"]],
        ),
    ]

    agent_ids: dict[str, str] = {}
    for a in agents_def:
        # AI user を作成
        agent_user_id = org_repo.create_user(
            organization_id=org_id,
            name=a["name"],
            user_type="ai",
            role_id="ai_agent",
        )
        # エージェント登録
        agent_id = agent_repo.register(
            user_id=agent_user_id,
            agent_type=a["agent_type"],
            reports_to_id=ai_ceo_user_id,
            system_prompt=a["system_prompt"],
            capabilities=a["capabilities"],
            brand_ids=a["brand_ids"],
        )
        agent_ids[a["agent_type"]] = agent_id
        log.info(f"  Agent: {a['name']} → {agent_id}")

    # ── 7. サンプルタスク ─────────────────────
    log.info("サンプルタスク作成...")
    from repositories.ai_repo import TaskRepo
    task_repo = TaskRepo()

    t1 = task_repo.create(
        title="UPJ Instagram 週次投稿スケジュール生成",
        mode="semi_auto",
        assigned_to_agent_id=agent_ids.get("noimos",""),
        requested_by_user_id=president_id,
        brand_id=brand_ids["upj"],
        description="今週分のInstagram投稿キャプション・ハッシュタグを生成してキューに積む",
        priority=3,
        input_data={"week": "2026-W17", "posts_count": 5},
    )
    t2 = task_repo.create(
        title="UPJ SNS パフォーマンスレポート",
        mode="full_auto",
        assigned_to_agent_id=agent_ids.get("analytics",""),
        requested_by_user_id=president_id,
        brand_id=brand_ids["upj"],
        description="先週のSNS全チャネルのパフォーマンスを集計してレポートを生成する",
        priority=5,
        depends_on=[t1],
    )
    log.info(f"  サンプルタスク: {t1}, {t2}")

    log.info("=== シード完了 ===")
    return {
        "organization_id": org_id,
        "brand_ids": brand_ids,
        "president_id": president_id,
        "ai_ceo_user_id": ai_ceo_user_id,
        "agent_ids": agent_ids,
        "sample_tasks": [t1, t2],
    }


if __name__ == "__main__":
    result = seed()
    print("\n--- シード結果 ---")
    print(f"組織ID       : {result['organization_id']}")
    print(f"Human President: {result['president_id']}")
    print(f"AI CEO       : {result['ai_ceo_user_id']}")
    print(f"ブランド数    : {len(result['brand_ids'])}")
    print(f"エージェント数: {len(result['agent_ids'])}")
    print(f"サンプルタスク: {result['sample_tasks']}")
