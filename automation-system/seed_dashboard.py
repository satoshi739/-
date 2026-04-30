#!/usr/bin/env python3
"""
ダッシュボード向けDBシード — 実システム状態に基づく初期データ投入
実行: python3 automation-system/seed_dashboard.py
"""
from __future__ import annotations
import json, sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import database as db

NOW   = datetime.now()
TODAY = NOW.strftime("%Y-%m-%d")

def run():
    print("=== ダッシュボードDB初期データ投入 ===")
    _seed_daily_briefs()
    _seed_anomaly_alerts()
    _seed_ai_recommendations()
    _seed_strategy_notes()
    _seed_performance_snapshots()
    _seed_blog_projects()
    print("\n完了。")

# ══════════════════════════════════════════
# 1. daily_briefs
# ══════════════════════════════════════════
def _seed_daily_briefs():
    briefs = [
        {
            "brief_date": TODAY,
            "mood": "caution",
            "summary": (
                "scheduler・ブログ自動投稿（全5ブランド 08:30/12:30/18:00）の設定が完了し本番稼働を開始。"
                "DSC Marketingのストーリー投稿がInstagramに正常公開（ig_08644366005755196）。"
                "一方、agent-analytics・agent-content-dsc・agent-content-upj で計8件のタスク失敗を検知。"
                "MEO口コミ14件・インサイト3件・投稿6件が同期済み。Bangkok Peachのレビューに自動返信完了。"
                "本日18:00に全ブランドのブログ初回自動投稿が実行予定。"
            ),
            "highlights": json.dumps([
                {"icon": "check", "text": "ブログ自動投稿スケジュール設定完了（全5ブランド 1日3回）"},
                {"icon": "check", "text": "DSC Instagram ストーリー公開成功"},
                {"icon": "check", "text": "MEO口コミ14件・GBP投稿6件 同期完了"},
                {"icon": "warn",  "text": "エージェントタスク失敗 8件（analytics・content系）"},
                {"icon": "warn",  "text": "satoshi-blog 投稿素材 0件 — 補充必要"},
            ]),
            "kpis": json.dumps({
                "posts": 1,
                "leads": 0,
                "meo_reviews": 14,
                "agent_failures": 8,
            }),
            "generated_at": NOW.strftime("%H:%M"),
        },
        {
            "brief_date": (NOW - timedelta(days=1)).strftime("%Y-%m-%d"),
            "mood": "good",
            "summary": (
                "Bangkok Peach Twitterキューに7件の投稿コンテンツを追加。"
                "インボックスのファイルドロップ後AI自動処理機能が正常動作を確認。"
                "scheduler復旧完了（PID 80040）。heartbeat監視もserver.pyで稼働開始。"
                "全5ブランドのWordPress認証情報の設定が完了。"
            ),
            "highlights": json.dumps([
                {"icon": "check", "text": "Bangkok Peach Twitter 投稿キュー 7件追加"},
                {"icon": "check", "text": "scheduler復旧・heartbeat監視開始"},
                {"icon": "check", "text": "全5ブランドWordPress認証設定完了"},
                {"icon": "check", "text": "インボックス自動AI処理機能 正常動作確認"},
            ]),
            "kpis": json.dumps({"posts": 0, "leads": 0, "queue_added": 7}),
            "generated_at": "07:30",
        },
        {
            "brief_date": (NOW - timedelta(days=9)).strftime("%Y-%m-%d"),
            "mood": "good",
            "summary": (
                "MEO口コミ同期が正常完了（profiles 3件・reviews 14件・insights 3件・posts 6件）。"
                "Bangkok Peachのレビューに自動返信を実行。"
                "publish_approve・idea_approveが各1件処理済み。"
                "DSCストーリーrun#1がInstagramに公開成功。"
            ),
            "highlights": json.dumps([
                {"icon": "check", "text": "MEO同期完了: 口コミ14件・GBP投稿6件"},
                {"icon": "check", "text": "Bangkok Peach レビュー自動返信完了"},
                {"icon": "check", "text": "DSC Instagram ストーリー初回公開成功"},
            ]),
            "kpis": json.dumps({"posts": 1, "leads": 0, "reviews": 14}),
            "generated_at": "07:30",
        },
    ]

    with db.get_conn() as conn:
        existing = {r[0] for r in conn.execute("SELECT brief_date FROM daily_briefs").fetchall()}
        inserted = 0
        for b in briefs:
            if b["brief_date"] not in existing:
                conn.execute(
                    """INSERT INTO daily_briefs
                       (brief_date, mood, summary, highlights_json, kpis_json, generated_at)
                       VALUES (?,?,?,?,?,?)""",
                    (b["brief_date"], b["mood"], b["summary"],
                     b["highlights"], b["kpis"], b["generated_at"])
                )
                inserted += 1
    print(f"daily_briefs: {inserted}件追加")


# ══════════════════════════════════════════
# 2. anomaly_alerts  (実観測した問題を記録)
# ══════════════════════════════════════════
def _seed_anomaly_alerts():
    alerts = [
        {
            "brand": None, "platform": "agent-analytics",
            "metric": "タスク実行失敗",
            "expected_value": 0, "actual_value": 2, "delta_pct": None,
            "severity": "alert",
            "message": "agent-analytics が本日2回タスク失敗（10:36〜10:37）。GA4/GSCデータ取得ができていない可能性あり。ログ確認と再実行が必要。",
            "resolved": 0,
            "created_at": f"{TODAY} 10:37:00",
        },
        {
            "brand": "dsc-marketing", "platform": "agent-content-dsc",
            "metric": "タスク実行失敗",
            "expected_value": 0, "actual_value": 2, "delta_pct": None,
            "severity": "warn",
            "message": "agent-content-dsc が本日2回タスク失敗（10:31〜10:36）。DSCコンテンツ自動生成が停止中。エラーログを確認してください。",
            "resolved": 0,
            "created_at": f"{TODAY} 10:36:59",
        },
        {
            "brand": "upjapan", "platform": "agent-content-upj",
            "metric": "タスク実行失敗",
            "expected_value": 0, "actual_value": 2, "delta_pct": None,
            "severity": "warn",
            "message": "agent-content-upj が本日2回タスク失敗（10:31〜10:32）。UPJapanコンテンツ自動生成が停止中。",
            "resolved": 0,
            "created_at": f"{TODAY} 10:31:58",
        },
        {
            "brand": "satoshi-blog", "platform": "assets",
            "metric": "投稿素材数",
            "expected_value": 10, "actual_value": 0, "delta_pct": -100,
            "severity": "alert",
            "message": "satoshi-blog の投稿用素材が0件。ブログ自動投稿はWordPress直接公開のため影響は限定的だが、SNS用ビジュアル素材の補充が必要。",
            "resolved": 0,
            "created_at": f"{TODAY} 08:00:00",
        },
        {
            "brand": "bangkok-peach", "platform": "assets",
            "metric": "投稿素材数",
            "expected_value": 14, "actual_value": 3, "delta_pct": -79,
            "severity": "warn",
            "message": "Bangkok Peach の素材が3件のみ（photo 1・template 1・video 1）。Twitter投稿キューは7件あるが画像素材が不足。早急な素材補充が推奨されます。",
            "resolved": 0,
            "created_at": f"{TODAY} 08:00:00",
        },
        {
            "brand": "upjapan", "platform": "story",
            "metric": "story承認率",
            "expected_value": 100, "actual_value": 50, "delta_pct": -50,
            "severity": "warn",
            "message": "UPJapan ストーリー候補(run#3)が却下されました。コンテンツ品質またはブランドガイドライン適合性の見直しが必要です。",
            "resolved": 1,
            "created_at": "2026-04-21 19:01:11",
            "resolved_at": "2026-04-21 19:01:11",
        },
    ]

    with db.get_conn() as conn:
        existing_count = conn.execute("SELECT COUNT(*) FROM anomaly_alerts").fetchone()[0]
        if existing_count > 0:
            print(f"anomaly_alerts: スキップ（既に{existing_count}件）")
            return
        for a in alerts:
            conn.execute(
                """INSERT INTO anomaly_alerts
                   (brand, platform, metric, expected_value, actual_value, delta_pct,
                    severity, message, resolved, created_at, resolved_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (a["brand"], a["platform"], a["metric"],
                 a["expected_value"], a["actual_value"], a.get("delta_pct"),
                 a["severity"], a["message"], a["resolved"],
                 a["created_at"], a.get("resolved_at"))
            )
    print(f"anomaly_alerts: {len(alerts)}件追加")


# ══════════════════════════════════════════
# 3. ai_recommendations
# ══════════════════════════════════════════
def _seed_ai_recommendations():
    recs = [
        {
            "brand": None, "category": "システム修復", "priority": "high",
            "title": "失敗エージェント（analytics・content系）のエラー原因を特定・修正する",
            "body": "本日 agent-analytics・agent-content-dsc・agent-content-upj で計8件のタスク失敗を検知。Railwayログ（railway logs）でエラー詳細を確認し、環境変数不足・依存ライブラリ欠落・API認証失敗のいずれかを特定して対処してください。",
            "action_url": "/logs",
        },
        {
            "brand": "satoshi-blog", "category": "素材補充", "priority": "high",
            "title": "satoshi-blog の投稿素材（SNS用ビジュアル）を補充する",
            "body": "satoshi-blog の素材が0件です。WordPressブログはAI自動生成で今日18:00から始まりますが、Instagram・Threads用のビジュアル素材が不足しています。素材インボックスにドロップするか、テンプレートから生成してください。",
            "action_url": "/inbox",
        },
        {
            "brand": "bangkok-peach", "category": "素材補充", "priority": "high",
            "title": "Bangkok Peach 素材を補充（現在 photo 1枚のみ）",
            "body": "Bangkok Peachの画像素材が1枚のみです。Twitterキューに7件のコンテンツがありますが、画像なしでは投稿品質が低下します。少なくとも10〜15枚の写真素材を追加することを推奨します。",
            "action_url": "/inbox",
        },
        {
            "brand": None, "category": "自動化", "priority": "mid",
            "title": "ブログ自動投稿の初回実行（本日18:00）結果を確認する",
            "body": "全5ブランドのブログ自動投稿が本日18:00に初回実行されます。Railwayログで「=== ブログ自動投稿完了 ===」の出力と各ブランドの投稿成功を確認してください。失敗した場合はWordPress認証情報（APP_PASSWORD）を再確認してください。",
            "action_url": "/logs",
        },
        {
            "brand": "bangkok-peach", "category": "SNS戦略", "priority": "mid",
            "title": "Bangkok Peach Twitterキュー 7件の配信スケジュールを設定する",
            "body": "Bangkok Peach のTwitter投稿が7件キューに入っていますが、scheduled_atが未設定（2099-12-31）のものが多数あります。実際の配信日時を設定して自動投稿を有効化してください。",
            "action_url": "/queue",
        },
        {
            "brand": "dsc-marketing", "category": "コンテンツ", "priority": "mid",
            "title": "DSC Marketing Instagramストーリーの継続投稿を設定する",
            "body": "DSC Marketing のストーリー投稿がInstagramで正常公開されています（run#7）。現在の投稿テンプレートを活用して、週3〜5本の定期ストーリー投稿スケジュールを設定することを推奨します。",
            "action_url": "/story-autopilot",
        },
        {
            "brand": None, "category": "MEO", "priority": "low",
            "title": "GBP（Googleビジネスプロフィール）への投稿頻度を週2回以上に増やす",
            "body": "MEO同期で確認したGBP投稿は6件（過去）です。ローカル検索順位向上のため、各ブランドの店舗情報・イベント・キャンペーン投稿を週2回以上のペースで続けることを推奨します。",
            "action_url": "/meo",
        },
    ]

    with db.get_conn() as conn:
        existing_count = conn.execute("SELECT COUNT(*) FROM ai_recommendations").fetchone()[0]
        if existing_count > 0:
            print(f"ai_recommendations: スキップ（既に{existing_count}件）")
            return
        now_str = NOW.strftime("%Y-%m-%d %H:%M:%S")
        for r in recs:
            conn.execute(
                """INSERT INTO ai_recommendations
                   (brand, category, priority, title, body, action_url, dismissed, created_at)
                   VALUES (?,?,?,?,?,?,0,?)""",
                (r["brand"], r["category"], r["priority"], r["title"], r["body"], r["action_url"], now_str)
            )
    print(f"ai_recommendations: {len(recs)}件追加")


# ══════════════════════════════════════════
# 4. strategy_notes
# ══════════════════════════════════════════
def _seed_strategy_notes():
    notes = [
        {
            "brand": None, "author": "AI CEO", "category": "全体戦略", "pinned": 1,
            "note": (
                "2026年Q2の成長ドライバーはブログSEOの自動化。"
                "全5ブランドで1日3記事（08:30/12:30/18:00）の自動投稿体制が整った。"
                "まず3ヶ月間は「記事量産 → 検索流入獲得」に集中し、"
                "SNSはブランド認知に留めてリードはブログとGBPから取る構造を確立する。"
            ),
            "created_at": TODAY,
        },
        {
            "brand": None, "author": "AI CEO", "category": "優先課題", "pinned": 1,
            "note": (
                "エージェントタスク失敗（8件）が最優先課題。"
                "agent-analytics・agent-content-dsc・agent-content-upjのエラーを修正しないと"
                "コンテンツ自動生成とGA4分析が機能しない。"
                "Railwayログでエラー内容を確認し、環境変数・API認証を再確認すること。"
            ),
            "created_at": TODAY,
        },
        {
            "brand": "bangkok-peach", "author": "AI CEO", "category": "素材戦略", "pinned": 0,
            "note": (
                "Bangkok Peach は素材不足が構造的課題。"
                "Twitterキュー7件はコンテンツとして準備できているが画像素材が不足。"
                "現地パートナーと月1回の撮影契約を締結し、"
                "常に30日分（約30枚）の素材バッファを維持するオペレーションが必要。"
            ),
            "created_at": TODAY,
        },
        {
            "brand": "dsc-marketing", "author": "AI CEO", "category": "コンテンツ戦略", "pinned": 0,
            "note": (
                "DSC Marketing は唯一ストーリー投稿が正常稼働しているブランド（run#7 公開済み）。"
                "このモメンタムを活かし、週3〜5本のストーリー定期投稿と"
                "WordPressブログの同時展開でInstagram → ブログ → リード獲得のファネルを構築する。"
            ),
            "created_at": (NOW - timedelta(days=1)).strftime("%Y-%m-%d"),
        },
        {
            "brand": None, "author": "AI CEO", "category": "MEO戦略", "pinned": 0,
            "note": (
                "MEO同期が安定稼働中（口コミ14件・GBP投稿6件・インサイト3件）。"
                "Bangkok PeachのGoogleレビュー自動返信も正常動作を確認。"
                "GBP投稿頻度を週2回以上に増やすことでローカル検索順位の改善が期待できる。"
                "特にupjapan・cashflowsupportのGBP活用が弱い — 優先的に強化する。"
            ),
            "created_at": (NOW - timedelta(days=9)).strftime("%Y-%m-%d"),
        },
    ]

    with db.get_conn() as conn:
        existing_count = conn.execute("SELECT COUNT(*) FROM strategy_notes").fetchone()[0]
        if existing_count > 0:
            print(f"strategy_notes: スキップ（既に{existing_count}件）")
            return
        for n in notes:
            conn.execute(
                """INSERT INTO strategy_notes
                   (brand, author, category, note, pinned, created_at)
                   VALUES (?,?,?,?,?,?)""",
                (n["brand"], n["author"], n["category"], n["note"], n["pinned"], n["created_at"])
            )
    print(f"strategy_notes: {len(notes)}件追加")


# ══════════════════════════════════════════
# 5. performance_snapshots
# ══════════════════════════════════════════
def _seed_performance_snapshots():
    snaps = [
        # DSC — story_publish 2回成功
        {"snap_date": TODAY, "brand": "dsc-marketing", "platform": "instagram",
         "metric_key": "stories_published", "metric_value": 2, "delta_pct": 0,
         "note": "run#1・run#7 正常公開"},
        # MEO — 全ブランド合算
        {"snap_date": TODAY, "brand": None, "platform": "google_business",
         "metric_key": "reviews_total", "metric_value": 14, "delta_pct": 0,
         "note": "MEO sync: profiles 3, reviews 14"},
        {"snap_date": TODAY, "brand": None, "platform": "google_business",
         "metric_key": "gbp_posts_total", "metric_value": 6, "delta_pct": 0,
         "note": "MEO sync: GBP投稿 6件"},
        # Bangkok Peach — queue
        {"snap_date": TODAY, "brand": "bangkok-peach", "platform": "twitter",
         "metric_key": "queue_items", "metric_value": 7, "delta_pct": 700,
         "note": "Twitter投稿キュー 7件追加"},
        # assets 合計
        {"snap_date": TODAY, "brand": "dsc-marketing", "platform": "assets",
         "metric_key": "asset_count", "metric_value": 4, "delta_pct": 0, "note": "photo 2・template 1・video 1"},
        {"snap_date": TODAY, "brand": "upjapan", "platform": "assets",
         "metric_key": "asset_count", "metric_value": 4, "delta_pct": 0, "note": "photo 1・script 1・template 1・video 1"},
        {"snap_date": TODAY, "brand": "bangkok-peach", "platform": "assets",
         "metric_key": "asset_count", "metric_value": 3, "delta_pct": -79, "note": "photo 1・template 1・video 1（不足）"},
        {"snap_date": TODAY, "brand": "cashflowsupport", "platform": "assets",
         "metric_key": "asset_count", "metric_value": 2, "delta_pct": 0, "note": "photo 1・script 1"},
        {"snap_date": TODAY, "brand": "satoshi-blog", "platform": "assets",
         "metric_key": "asset_count", "metric_value": 0, "delta_pct": -100, "note": "素材なし（要補充）"},
    ]

    with db.get_conn() as conn:
        existing_count = conn.execute("SELECT COUNT(*) FROM performance_snapshots").fetchone()[0]
        if existing_count > 0:
            print(f"performance_snapshots: スキップ（既に{existing_count}件）")
            return
        now_str = NOW.strftime("%Y-%m-%d %H:%M:%S")
        for s in snaps:
            conn.execute(
                """INSERT INTO performance_snapshots
                   (snap_date, brand, platform, metric_key, metric_value, delta_pct, note, created_at)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (s["snap_date"], s.get("brand"), s["platform"],
                 s["metric_key"], s["metric_value"], s.get("delta_pct", 0),
                 s.get("note", ""), now_str)
            )
    print(f"performance_snapshots: {len(snaps)}件追加")


# ══════════════════════════════════════════
# 6. blog_projects (placeholder — 18:00の自動投稿実行前)
# ══════════════════════════════════════════
def _seed_blog_projects():
    projects = [
        {
            "brand": "satoshi-blog",
            "title": "バンコク移住1年目でわかった生活費の真実 — 月20万円で豊かに暮らす方法",
            "source_type": "manual", "source_platform": "手動入稿",
            "source_caption": "バンコク在住者向け生活費ガイド。実体験に基づく節約術と快適生活の両立方法。",
            "engagement_score": 85, "status": "draft",
            "created_at": TODAY,
        },
        {
            "brand": "dsc-marketing",
            "title": "AI採用ツール導入で面接コスト50%削減 — 中小企業の実践事例",
            "source_type": "instagram", "source_platform": "Instagram",
            "source_caption": "AI採用スクリーニングで採用コストを半減させた3社の事例を紹介します。",
            "engagement_score": 92, "status": "candidate",
            "created_at": TODAY,
        },
        {
            "brand": "cashflowsupport",
            "title": "資金繰り改善の第一歩 — 中小企業が今すぐできる3つのキャッシュフロー習慣",
            "source_type": "manual", "source_platform": "手動入稿",
            "source_caption": "月末の資金不足を解消するための実践的な3つの習慣を解説。",
            "engagement_score": 78, "status": "candidate",
            "created_at": TODAY,
        },
        {
            "brand": "upjapan",
            "title": "フリーランスが海外移住する前に絶対確認すべき10のチェックリスト",
            "source_type": "manual", "source_platform": "手動入稿",
            "source_caption": "ビザ・税務・保険・銀行口座 — 海外移住前の準備リストを完全網羅。",
            "engagement_score": 74, "status": "idea",
            "created_at": TODAY,
        },
        {
            "brand": "bangkok-peach",
            "title": "バンコクKTV完全ガイド — 初めての方が安心して楽しむための基礎知識",
            "source_type": "twitter", "source_platform": "Twitter/X",
            "source_caption": "バンコク夜遊び完全ガイド｜初心者が最初に直面する3大不安と解消法",
            "engagement_score": 88, "status": "draft",
            "created_at": TODAY,
        },
    ]

    with db.get_conn() as conn:
        existing_count = conn.execute("SELECT COUNT(*) FROM blog_projects").fetchone()[0]
        if existing_count > 0:
            print(f"blog_projects: スキップ（既に{existing_count}件）")
            return
        now_str = NOW.strftime("%Y-%m-%d %H:%M:%S")
        for p in projects:
            conn.execute(
                """INSERT INTO blog_projects
                   (brand, title, source_type, source_platform, source_caption,
                    engagement_score, status, created_at)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (p["brand"], p["title"], p["source_type"], p["source_platform"],
                 p["source_caption"], p["engagement_score"], p["status"], p["created_at"])
            )
    print(f"blog_projects: {len(projects)}件追加")


if __name__ == "__main__":
    run()
