"""
Seed / mock data for President & CEO dashboards.
Replace each get_* function with a real data source when ready.
"""
from datetime import datetime, timedelta

_NOW = datetime.now()
_TODAY = _NOW.strftime("%Y年%m月%d日")


def get_morning_brief() -> dict:
    return {
        "generated_at": _NOW.strftime("%H:%M"),
        "date": _TODAY,
        "mood": "good",  # good | caution | alert
        "summary": (
            "昨日は全ブランド合計37件の自動投稿が完了しました。"
            "DSc Marketingのインスタグラムが高エンゲージメント（いいね率4.2%）で好調です。"
            "3件の新規リードが入電し、うち2件はL2に昇格しました。"
            "Bangkok Peachの写真素材が残り2日分まで減少しています。早急な補充が必要です。"
        ),
        "highlights": [
            {"icon": "📈", "text": "本日の投稿: 全ブランド合計 7件 実行済み"},
            {"icon": "👤", "text": "新規リード: 3件（うちL2昇格 2件）"},
            {"icon": "💬", "text": "LINE自動返信: 24件処理（未対応 3件）"},
            {"icon": "📊", "text": "DSc Instagram: エンゲージメント率 4.2%（業界平均の2倍）"},
        ],
    }


def get_priority_actions() -> list:
    return [
        {"icon": "📸", "text": "Bangkok Peach の写真素材を補充する（残り2枚・1日分）", "urgency": "high", "link": "/inbox"},
        {"icon": "△",  "text": "DSc Marketing — Instagramリール承認が22時間滞留",       "urgency": "high", "link": "/decisions"},
        {"icon": "💬", "text": "LINE未返信 3件 — 48時間以内に手動対応が必要",           "urgency": "high", "link": "/leads"},
        {"icon": "📝", "text": "UPJ Threadsキャンペーン案を確認・承認",                  "urgency": "mid",  "link": "/decisions"},
        {"icon": "📊", "text": "CSF 今週投稿が1件のみ — 追加コンテンツの指示を",       "urgency": "mid",  "link": "/queue"},
        {"icon": "💰", "text": "BPG 撮影予算3万円の承認（提案書準備済み）",            "urgency": "low",  "link": "/decisions"},
    ]


def get_pending_approvals() -> list:
    return [
        {"brand": "DSc", "color": "#34d399", "type": "Instagramリール",    "title": "AIで変わる採用活動2025",        "age_h": 22},
        {"brand": "UPJ", "color": "#5b8af5", "type": "Threadsキャンペーン", "title": "GW特別企画 — 5日連続投稿案",   "age_h": 6},
        {"brand": "CSF", "color": "#fbbf24", "type": "LINE配信メッセージ",  "title": "キャッシュフロー診断ご案内",   "age_h": 48},
    ]


def get_danger_alerts() -> list:
    return [
        {"level": "alert", "text": "Bangkok Peach: 写真素材が残り2枚（今日中に枯渇リスク）"},
        {"level": "warn",  "text": "CSF: 今週のInstagram投稿が1件のみ（目標3件）"},
        {"level": "warn",  "text": "LINE: 未設定キーワード3件 — 自動返信失敗の可能性"},
        {"level": "info",  "text": "DSc Instagram: 承認待ちリールが22時間超え — リーチ機会損失"},
    ]


def get_brand_status() -> dict:
    return {
        "upjapan": {
            "name": "UPJ", "color": "#5b8af5",
            "posts_today": 2, "posts_week": 8, "target_week": 10,
            "leads_active": 5, "media_left": 12, "health": "good",
            "link": "/brands/upjapan",
        },
        "dsc-marketing": {
            "name": "DSc", "color": "#34d399",
            "posts_today": 4, "posts_week": 18, "target_week": 21,
            "leads_active": 12, "media_left": 28, "health": "good",
            "link": "/brands/dsc-marketing",
        },
        "cashflowsupport": {
            "name": "CSF", "color": "#fbbf24",
            "posts_today": 0, "posts_week": 1, "target_week": 5,
            "leads_active": 3, "media_left": 5, "health": "warn",
            "link": "/brands/cashflowsupport",
        },
        "satoshi-blog": {
            "name": "Blog", "color": "#a78bfa",
            "posts_today": 0, "posts_week": 2, "target_week": 3,
            "leads_active": 0, "media_left": 0, "health": "good",
            "link": "/brands/satoshi-blog",
        },
        "bangkok-peach": {
            "name": "BPG", "color": "#f472b6",
            "posts_today": 1, "posts_week": 5, "target_week": 7,
            "leads_active": 8, "media_left": 2, "health": "alert",
            "link": "/brands/bangkok-peach",
        },
    }


def get_agent_status() -> list:
    return [
        {"name": "Morning Operator",    "icon": "☀️",  "status": "ok",    "last_run": "今朝 07:30", "next_run": "明朝 07:30", "detail": "朝ブリーフ・投稿スケジュール完了"},
        {"name": "SNS Auto Poster",     "icon": "📤",  "status": "ok",    "last_run": "15分前",     "next_run": "45分後",     "detail": "4プラットフォーム稼働中"},
        {"name": "LINE Responder",      "icon": "💬",  "status": "warn",  "last_run": "2時間前",    "next_run": "常時待機",   "detail": "未定義キーワード3件あり"},
        {"name": "Lead Intake",         "icon": "👤",  "status": "ok",    "last_run": "30分前",     "next_run": "常時待機",   "detail": "本日3件処理・2件L2昇格"},
        {"name": "Sales Followup",      "icon": "📞",  "status": "ok",    "last_run": "1時間前",    "next_run": "明日 10:00", "detail": "フォローアップ5件送信済み"},
        {"name": "Content Scheduler",   "icon": "📅",  "status": "ok",    "last_run": "6時間前",    "next_run": "毎時",       "detail": "週次カレンダー・キュー管理中"},
        {"name": "Photo Importer",      "icon": "📷",  "status": "idle",  "last_run": "昨日",       "next_run": "手動実行",   "detail": "インボックス新規ファイルなし"},
        {"name": "Analytics Puller",    "icon": "◈",   "status": "ok",    "last_run": "1時間前",    "next_run": "毎時",       "detail": "全ブランドGA4・SNS取得中"},
    ]


def get_recent_runs() -> list:
    return [
        {"time": "07:30", "agent": "Morning Operator",  "brand": "全ブランド", "result": "ok",   "detail": "朝ブリーフ生成・投稿5件スケジュール"},
        {"time": "08:15", "agent": "SNS Auto Poster",   "brand": "DSc",       "result": "ok",   "detail": "Instagram投稿完了（いいね率4.2%）"},
        {"time": "09:00", "agent": "Lead Intake",        "brand": "DSc",       "result": "ok",   "detail": "新規リード3件・2件L2昇格"},
        {"time": "09:45", "agent": "SNS Auto Poster",   "brand": "UPJ",       "result": "ok",   "detail": "Threads・Facebook投稿完了"},
        {"time": "10:30", "agent": "LINE Responder",     "brand": "DSc",       "result": "warn", "detail": "未設定キーワード検知（シナリオ追加必要）"},
        {"time": "11:00", "agent": "Sales Followup",     "brand": "CSF",       "result": "ok",   "detail": "フォローアップ3件送信"},
    ]


def get_unreplied() -> dict:
    return {"line": 3, "email": 1, "total": 4}


def get_media_shortage() -> list:
    return [
        {"brand": "BPG",  "color": "#f472b6", "left": 2,  "days": 1, "level": "alert"},
        {"brand": "CSF",  "color": "#fbbf24", "left": 5,  "days": 3, "level": "warn"},
    ]


def get_post_shortage() -> list:
    return [
        {"brand": "CSF", "color": "#fbbf24", "platform": "Instagram", "week_count": 1, "target": 3},
        {"brand": "BPG", "color": "#f472b6", "platform": "Threads",   "week_count": 0, "target": 2},
    ]


def get_blog_candidates() -> list:
    return [
        {"id": 1, "title": "AIで変わる中小企業のマーケティング戦略2025",     "score": 92, "brand": "DSc",  "brand_color": "#34d399", "status": "draft", "link": "/blog/1"},
        {"id": 2, "title": "タイ移住者が語るバンコクの本当の生活費",          "score": 88, "brand": "Blog", "brand_color": "#a78bfa", "status": "draft", "link": "/blog/2"},
        {"id": 3, "title": "資金繰り改善のための3つのキャッシュフロー習慣",   "score": 78, "brand": "CSF",  "brand_color": "#fbbf24", "status": "idea",  "link": "/blog/3"},
    ]


def get_blog_projects() -> list:
    return [
        {
            "id": 1, "brand": "DSc", "brand_color": "#34d399",
            "title": "AIで変わる中小企業のマーケティング戦略2025",
            "source_type": "instagram", "source_platform": "Instagram",
            "source_caption": "AIを使ったマーケ自動化で月商3倍！中小企業でもできる5ステップを解説します✨",
            "engagement_score": 92, "status": "draft",
            "created_at": (_NOW - timedelta(days=1)).strftime("%Y-%m-%d"),
        },
        {
            "id": 2, "brand": "Blog", "brand_color": "#a78bfa",
            "title": "タイ移住者が語るバンコクの本当の生活費",
            "source_type": "threads", "source_platform": "Threads",
            "source_caption": "バンコク生活費の真実。家賃・食費・交通費を全部公開します。",
            "engagement_score": 88, "status": "draft",
            "created_at": (_NOW - timedelta(days=2)).strftime("%Y-%m-%d"),
        },
        {
            "id": 3, "brand": "CSF", "brand_color": "#fbbf24",
            "title": "資金繰り改善のための3つのキャッシュフロー習慣",
            "source_type": "meo", "source_platform": "Google Maps",
            "source_caption": "口コミ: 資金繰りの相談をしたらとても丁寧に対応してもらえました。",
            "engagement_score": 78, "status": "idea",
            "created_at": (_NOW - timedelta(days=3)).strftime("%Y-%m-%d"),
        },
        {
            "id": 4, "brand": "UPJ", "brand_color": "#5b8af5",
            "title": "フリーランスが海外移住する前に知っておくべき10のこと",
            "source_type": "instagram", "source_platform": "Instagram",
            "source_caption": "海外移住を検討中のフリーランスへ。ビザ・税務・保険の準備リスト",
            "engagement_score": 74, "status": "candidate",
            "created_at": (_NOW - timedelta(days=4)).strftime("%Y-%m-%d"),
        },
        {
            "id": 5, "brand": "DSc", "brand_color": "#34d399",
            "title": "採用コスト半減！AIスクリーニング導入ガイド",
            "source_type": "facebook", "source_platform": "Facebook",
            "source_caption": "採用コストを50%削減したAIスクリーニングの実際の使い方",
            "engagement_score": 71, "status": "candidate",
            "created_at": (_NOW - timedelta(days=5)).strftime("%Y-%m-%d"),
        },
    ]


def get_blog_draft_detail(draft_id: int) -> dict:
    projects = {p["id"]: p for p in get_blog_projects()}
    drafts = {
        1: {
            "id": 1, "project_id": 1,
            "brand": "DSc", "brand_color": "#34d399",
            "title": "AIで変わる中小企業のマーケティング戦略2025",
            "slug": "ai-marketing-sme-2025",
            "meta_description": "中小企業がAIマーケティングを活用して売上3倍を達成する具体的な5ステップを解説します。",
            "seo_keywords": ["AIマーケティング", "中小企業", "自動化", "SNS運用"],
            "word_count": 1820,
            "status": "draft",
            "created_by": "ai",
            "created_at": (_NOW - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"),
            "outline": [
                {"h2": "はじめに — なぜ今AIマーケティングなのか", "h3s": ["競合環境の変化", "中小企業が取り残されるリスク"]},
                {"h2": "ステップ1: SNS自動投稿の仕組みを作る", "h3s": ["コンテンツカレンダー設計", "ツール選定のポイント"]},
                {"h2": "ステップ2: リード獲得フローの自動化", "h3s": ["LINE公式アカウント活用", "CRM連携"]},
                {"h2": "ステップ3: AI分析で改善サイクルを回す", "h3s": ["KPI設計", "週次レポートの読み方"]},
                {"h2": "ステップ4: 顧客フォローアップの自動化", "h3s": ["シナリオ設計", "パーソナライズのコツ"]},
                {"h2": "ステップ5: チーム全体でAIを使いこなす", "h3s": ["研修と浸透", "ツール統合"]},
                {"h2": "まとめ", "h3s": []},
            ],
            "body_preview": "人手不足と広告費高騰が続く今、中小企業がマーケティングで生き残るにはAI活用が不可欠です。本記事では、月商3倍を達成した企業事例をもとに、今日から始められる5つのステップを解説します…",
        },
        2: {
            "id": 2, "project_id": 2,
            "brand": "Blog", "brand_color": "#a78bfa",
            "title": "タイ移住者が語るバンコクの本当の生活費",
            "slug": "bangkok-real-cost-of-living",
            "meta_description": "バンコク移住歴3年の筆者が家賃・食費・交通費・医療費をリアルに公開。月15万円での生活は本当に可能か？",
            "seo_keywords": ["バンコク 生活費", "タイ 移住", "海外移住 費用"],
            "word_count": 2100,
            "status": "draft",
            "created_by": "ai",
            "created_at": (_NOW - timedelta(days=2)).strftime("%Y-%m-%d %H:%M"),
            "outline": [
                {"h2": "バンコクの生活費 — 月別サマリー", "h3s": ["家賃相場", "食費の現実"]},
                {"h2": "エリア別コスト比較", "h3s": ["スクンビット", "シーロム", "バンカピ"]},
                {"h2": "日本人がハマりやすい出費トップ5", "h3s": []},
                {"h2": "月15万円生活は可能か？", "h3s": ["節約モデル", "標準モデル", "快適モデル"]},
                {"h2": "まとめ", "h3s": []},
            ],
            "body_preview": "「バンコクは安い」という先入観、実は半分正解・半分誤解です。3年の移住経験から、実際にかかるお金を包み隠さず公開します…",
        },
        3: {
            "id": 3, "project_id": 3,
            "brand": "CSF", "brand_color": "#fbbf24",
            "title": "資金繰り改善のための3つのキャッシュフロー習慣",
            "slug": "cashflow-3-habits",
            "meta_description": "中小企業の資金繰りを改善する3つの習慣。毎月末の危機を回避するための実践的メソッド。",
            "seo_keywords": ["資金繰り", "キャッシュフロー", "中小企業 経営"],
            "word_count": 0,
            "status": "idea",
            "created_by": "ai",
            "created_at": (_NOW - timedelta(days=3)).strftime("%Y-%m-%d %H:%M"),
            "outline": [
                {"h2": "キャッシュフローの基本を理解する", "h3s": []},
                {"h2": "習慣1: 週次キャッシュフロー確認", "h3s": []},
                {"h2": "習慣2: 売掛金回収の仕組み化", "h3s": []},
                {"h2": "習慣3: 固定費の定期見直し", "h3s": []},
                {"h2": "まとめ", "h3s": []},
            ],
            "body_preview": "",
        },
    }
    d = drafts.get(draft_id, drafts[1])
    d["project"] = projects.get(d["project_id"], {})
    return d


# ══ Daily Brief History ═══════════════════════════════════════

def get_daily_briefs_history() -> list:
    briefs = []
    moods = ["good", "good", "caution", "good", "alert", "good", "good"]
    summaries = [
        "全ブランド合計37件の自動投稿が完了。DSc Instagramが高エンゲージメント（いいね率4.2%）で好調。3件の新規リードが入電しうち2件はL2に昇格。Bangkok Peachの写真素材が残り2日分まで減少。",
        "週次最高エンゲージメントを記録。UPJ Threadsキャンペーンが反響好調。CSF Instagram投稿が今週2件のみで目標達成リスクあり。",
        "全体的に平常運転。MEO口コミが3件入電しAI返信下書き完了。Bangkok Peach撮影が完了し素材が補充された。LINEシナリオ未設定2件を修正済み。",
        "DSc採用AIの記事がオーガニック検索からのアクセスが急増（+340%）。ブログ記事候補として「AIスクリーニング導入ガイド」を自動生成。",
        "Bangkok Peach Instagram: エンゲージメント率が過去30日平均の60%に低下。投稿時間帯と素材品質の見直しを推奨。CSFリードフォローが72時間遅延。",
        "全ブランド週次レポート完了。DSc月商目標を3日前倒しで達成見込み。新規リード週計14件（先週比+40%）。",
        "朝ブリーフ生成開始（自動化システム初日）。全エージェント正常稼働確認。",
    ]
    for i, (mood, summary) in enumerate(zip(moods, summaries)):
        d = _NOW - timedelta(days=i)
        briefs.append({
            "id": i + 1,
            "brief_date": d.strftime("%Y-%m-%d"),
            "date_label": d.strftime("%Y年%m月%d日"),
            "mood": mood,
            "summary": summary,
            "highlights": [
                {"icon": "📈", "text": f"投稿実行: {37 - i * 3}件"},
                {"icon": "👤", "text": f"新規リード: {3 - (i % 3)}件"},
            ],
            "kpis": {
                "posts": 37 - i * 3,
                "leads": 3 - (i % 3),
                "engagement_rate": round(4.2 - i * 0.15, 1),
            },
            "generated_at": (d.replace(hour=7, minute=30)).strftime("%H:%M"),
        })
    return briefs


# ══ AI Chief of Staff ════════════════════════════════════════

def get_ai_recommendations() -> list:
    return [
        {
            "id": 1, "brand": "DSc", "brand_color": "#34d399",
            "category": "コンテンツ", "priority": "high",
            "title": "「AIスクリーニング」記事を今週中に公開すると検索流入が最大化",
            "body": "直近7日間でGoogleの検索ボリュームが+28%増加中。競合記事は3本のみで参入余地あり。下書き完成度85%のため、本日中に完成・公開を推奨します。",
            "action_url": "/blog/5",
        },
        {
            "id": 2, "brand": "CSF", "brand_color": "#fbbf24",
            "category": "SNS戦略", "priority": "high",
            "title": "CSF Instagramの投稿頻度を週3→週5に増加することを推奨",
            "body": "過去4週間の分析で、週5投稿ブランドは週3投稿比でリーチが2.3倍。CSFの現在のエンゲージメント率(2.1%)はポテンシャル(目標3.5%)の60%。投稿頻度が主因と分析。",
            "action_url": "/brands/cashflowsupport",
        },
        {
            "id": 3, "brand": "BPG", "brand_color": "#f472b6",
            "category": "素材", "priority": "high",
            "title": "Bangkok Peach: 素材枯渇リスク — 今日中に撮影依頼を",
            "body": "現在の素材残量で本日分をカバー可能ですが、明日以降の自動投稿が停止します。撮影依頼または既存素材の再活用プランが必要です。",
            "action_url": "/inbox",
        },
        {
            "id": 4, "brand": "UPJ", "brand_color": "#5b8af5",
            "category": "MEO", "priority": "mid",
            "title": "UPJ: GBP投稿を週2回に増やすとMEOスコア向上が見込まれる",
            "body": "同業他社の上位表示店舗は平均週2.4回のGBP投稿を実施。UPJは現在週0.8回。週2回ペースに増やすことで3ヶ月以内にローカル検索順位が改善する可能性が高いです。",
            "action_url": "/meo",
        },
        {
            "id": 5, "brand": None, "brand_color": "#6366f1",
            "category": "全体戦略", "priority": "mid",
            "title": "LINE公式アカウントのシナリオを拡充するタイミング",
            "body": "友達追加数が700名を超え、未設定キーワードからの問い合わせが週10件以上発生。シナリオ拡充により月20〜30件のリード自動取得が見込まれます。",
            "action_url": "/leads",
        },
        {
            "id": 6, "brand": "DSc", "brand_color": "#34d399",
            "category": "採用マーケ", "priority": "low",
            "title": "DSc: Threads投稿の最適時間帯は火・木の20時台",
            "body": "過去60日のエンゲージメントデータ分析結果。現在は随時投稿のため、スケジュール設定変更で推定+18%のリーチ向上が期待できます。",
            "action_url": "/queue",
        },
    ]


def get_performance_snapshot() -> dict:
    brands = ["DSc", "UPJ", "CSF", "BPG", "Blog"]
    brand_colors = {"DSc": "#34d399", "UPJ": "#5b8af5", "CSF": "#fbbf24", "BPG": "#f472b6", "Blog": "#a78bfa"}
    return {
        "period": "過去7日間",
        "generated_at": _NOW.strftime("%Y-%m-%d %H:%M"),
        "summary_kpis": [
            {"label": "総投稿数",      "value": "142",  "delta": "+12%", "direction": "up",   "color": "green"},
            {"label": "平均エンゲ率",  "value": "3.8%", "delta": "+0.4%","direction": "up",   "color": "green"},
            {"label": "新規リード",    "value": "23",   "delta": "+40%", "direction": "up",   "color": "green"},
            {"label": "MEOスコア平均", "value": "72",   "delta": "-3pt", "direction": "down", "color": "yellow"},
            {"label": "ブログ記事化",  "value": "5件",  "delta": "初計測","direction": "up",   "color": "purple"},
            {"label": "未承認案件",    "value": "3",    "delta": "-2",   "direction": "down", "color": "yellow"},
        ],
        "brand_metrics": [
            {"brand": "DSc",  "color": "#34d399", "posts": 52, "engagement": 4.2, "leads": 12, "meo_score": 85, "trend": "up"},
            {"brand": "UPJ",  "color": "#5b8af5", "posts": 31, "engagement": 3.5, "leads": 5,  "meo_score": 72, "trend": "stable"},
            {"brand": "CSF",  "color": "#fbbf24", "posts": 14, "engagement": 2.1, "leads": 3,  "meo_score": 68, "trend": "down"},
            {"brand": "BPG",  "color": "#f472b6", "posts": 28, "engagement": 3.9, "leads": 8,  "meo_score": 61, "trend": "down"},
            {"brand": "Blog", "color": "#a78bfa", "posts": 17, "engagement": 4.8, "leads": 0,  "meo_score": 0,  "trend": "up"},
        ],
        "top_posts": [
            {"brand": "DSc",  "brand_color": "#34d399", "platform": "Instagram", "caption": "AIで採用コスト半減！導入事例を公開", "likes": 284, "reach": 6700, "eng_rate": 4.2},
            {"brand": "Blog", "brand_color": "#a78bfa", "platform": "Threads",   "caption": "バンコク家賃の真実を暴露します",      "likes": 211, "reach": 4300, "eng_rate": 4.9},
            {"brand": "UPJ",  "brand_color": "#5b8af5", "platform": "Instagram", "caption": "フリーランスの海外移住チェックリスト",  "likes": 187, "reach": 5300, "eng_rate": 3.5},
        ],
        "weekly_trend": {
            "labels": [
                (_NOW - timedelta(days=6)).strftime("%-m/%-d"),
                (_NOW - timedelta(days=5)).strftime("%-m/%-d"),
                (_NOW - timedelta(days=4)).strftime("%-m/%-d"),
                (_NOW - timedelta(days=3)).strftime("%-m/%-d"),
                (_NOW - timedelta(days=2)).strftime("%-m/%-d"),
                (_NOW - timedelta(days=1)).strftime("%-m/%-d"),
                _NOW.strftime("%-m/%-d"),
            ],
            "posts": [18, 22, 15, 24, 19, 27, 17],
            "leads": [2, 4, 1, 5, 3, 6, 2],
        },
    }


def get_anomaly_alerts() -> list:
    return [
        {
            "id": 1, "brand": "BPG", "brand_color": "#f472b6",
            "platform": "Instagram", "metric": "エンゲージメント率",
            "expected_value": 3.8, "actual_value": 1.9,
            "delta_pct": -50, "severity": "alert",
            "message": "Bangkok Peach Instagramのエンゲージメント率が過去30日平均の50%に急落。投稿素材の品質低下または投稿時間帯のミスマッチが原因と推定。",
            "resolved": False,
            "created_at": (_NOW - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M"),
        },
        {
            "id": 2, "brand": "CSF", "brand_color": "#fbbf24",
            "platform": "Instagram", "metric": "週次投稿数",
            "expected_value": 5, "actual_value": 1,
            "delta_pct": -80, "severity": "alert",
            "message": "CSF Instagramの今週投稿数が目標(5件)の20%に留まっています。コンテンツ不足によるリーチ損失が発生しています。",
            "resolved": False,
            "created_at": (_NOW - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M"),
        },
        {
            "id": 3, "brand": "DSc", "brand_color": "#34d399",
            "platform": "WordPress", "metric": "オーガニック流入",
            "expected_value": 320, "actual_value": 1408,
            "delta_pct": 340, "severity": "info",
            "message": "DSc WordPressへのオーガニック検索流入が急増（+340%）。「AIスクリーニング」記事がGoogleで急上昇。関連ブログ記事の追加を推奨。",
            "resolved": False,
            "created_at": (_NOW - timedelta(hours=9)).strftime("%Y-%m-%d %H:%M"),
        },
        {
            "id": 4, "brand": "BPG", "brand_color": "#f472b6",
            "platform": "素材管理", "metric": "メディア残量",
            "expected_value": 14, "actual_value": 2,
            "delta_pct": -86, "severity": "alert",
            "message": "Bangkok Peach の投稿用写真素材が残り2枚（約1日分）。このまま補充がなければ明日の自動投稿が停止します。",
            "resolved": False,
            "created_at": (_NOW - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"),
        },
        {
            "id": 5, "brand": "UPJ", "brand_color": "#5b8af5",
            "platform": "LINE", "metric": "未設定キーワード",
            "expected_value": 0, "actual_value": 3,
            "delta_pct": None, "severity": "warn",
            "message": "LINEシナリオに未設定のキーワードが3件あります。自動返信に失敗しリード取りこぼしが発生する可能性があります。",
            "resolved": False,
            "created_at": (_NOW - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M"),
        },
        {
            "id": 6, "brand": "DSc", "brand_color": "#34d399",
            "platform": "Threads", "metric": "承認待ち時間",
            "expected_value": 4, "actual_value": 22,
            "delta_pct": 450, "severity": "warn",
            "message": "DSc Threadsのリール承認が22時間待機中。目標承認時間(4h)を大幅超過。投稿タイミング損失が発生しています。",
            "resolved": True,
            "resolved_at": (_NOW - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M"),
            "created_at": (_NOW - timedelta(hours=22)).strftime("%Y-%m-%d %H:%M"),
        },
    ]


def get_strategy_notes() -> list:
    return [
        {
            "id": 1, "brand": None, "author": "AI CEO",
            "category": "全体戦略", "pinned": True,
            "note": "2025年Q2の成長ドライバーはブログSEOとMEO最適化の二本柱。SNS投稿はブランド認知に留め、リードはブログとGBPから取得する構造に移行する。",
            "created_at": (_NOW - timedelta(days=3)).strftime("%Y-%m-%d"),
        },
        {
            "id": 2, "brand": "DSc", "brand_color": "#34d399",
            "author": "AI CEO", "category": "コンテンツ戦略", "pinned": True,
            "note": "DSc: 採用AI関連コンテンツへの検索需要が急増中。月4本のペースで専門記事を量産し、競合が少ない今のうちに検索上位を取る。リールとブログを連動させたファネル設計を優先する。",
            "created_at": (_NOW - timedelta(days=1)).strftime("%Y-%m-%d"),
        },
        {
            "id": 3, "brand": "CSF", "brand_color": "#fbbf24",
            "author": "AI CEO", "category": "要改善", "pinned": False,
            "note": "CSF: 2週連続でSNS目標未達。根本原因はコンテンツ制作体制の不備（担当者が週2時間しか確保できていない）。短尺リールの自動化を最優先で導入し、手動作業を週30分以下に削減する。",
            "created_at": (_NOW - timedelta(days=2)).strftime("%Y-%m-%d"),
        },
        {
            "id": 4, "brand": "BPG", "brand_color": "#f472b6",
            "author": "AI CEO", "category": "緊急対応", "pinned": False,
            "note": "Bangkok Peach: 素材問題は構造的課題。現地パートナーと月1回の撮影契約を締結し、常に30日分の素材バッファを維持するオペレーションに変更する必要あり。",
            "created_at": (_NOW - timedelta(days=4)).strftime("%Y-%m-%d"),
        },
    ]


# ══ CEO Dashboard ════════════════════════════════════════════

def get_task_queue() -> list:
    return [
        {"id": 1, "priority": "high", "task": "Bangkok Peach素材補充依頼",     "agent": "Photo Importer",    "status": "pending",        "eta": "今日中"},
        {"id": 2, "priority": "high", "task": "DSc Instagramリール承認",        "agent": "SNS Poster",        "status": "waiting_human",  "eta": "2時間"},
        {"id": 3, "priority": "high", "task": "LINE未設定キーワード対応",       "agent": "LINE Responder",    "status": "pending",        "eta": "今日中"},
        {"id": 4, "priority": "mid",  "task": "CSF週次投稿カレンダー緊急生成", "agent": "Content Scheduler", "status": "in_progress",    "eta": "今夜"},
        {"id": 5, "priority": "mid",  "task": "UPJ Threadsキャンペーン承認",   "agent": "SNS Poster",        "status": "waiting_human",  "eta": "6時間"},
        {"id": 6, "priority": "low",  "task": "UPJブログ記事SEO最適化",        "agent": "Blog AI",           "status": "in_progress",    "eta": "48時間"},
        {"id": 7, "priority": "low",  "task": "全ブランド月次レポート生成",    "agent": "Analytics",         "status": "scheduled",      "eta": "月末"},
    ]


def get_bottlenecks() -> list:
    return [
        {"area": "コンテンツ",      "issue": "Bangkok Peach: 写真素材不足でSNS自動化が停止リスク",  "impact": "high"},
        {"area": "承認フロー",      "issue": "DSc: リール承認22時間超え — 投稿タイミング損失",      "impact": "high"},
        {"area": "営業",            "issue": "CSF: L2リードへのフォローが72時間遅延",              "impact": "mid"},
        {"area": "オペレーション",  "issue": "LINE: 3キーワード未設定で自動返信失敗リスク",        "impact": "low"},
    ]


def get_escalations() -> list:
    return [
        {"to": "社長", "urgency": "high", "item": "BPG 写真撮影の予算承認（推定3万円）",      "deadline": "今週中"},
        {"to": "社長", "urgency": "mid",  "item": "CSF 投稿戦略見直しの判断",                 "deadline": "来週"},
        {"to": "社長", "urgency": "mid",  "item": "DSc LINE公式アカウントの本格活用判断",     "deadline": "来週"},
    ]


def get_ceo_priorities() -> list:
    return [
        {"order": 1, "focus": "BPG素材問題の即時解決",    "rationale": "今日中に動かないと明日の自動投稿が止まる"},
        {"order": 2, "focus": "承認滞留案件のクリア",     "rationale": "2件が20時間超え、タイミング逃しによる損失防止"},
        {"order": 3, "focus": "CSF投稿頻度の緊急回復",   "rationale": "今週残り3件の目標達成のためコンテンツ緊急生成"},
        {"order": 4, "focus": "LINEシナリオ補完",         "rationale": "未設定3件の自動返信ロジック追加でリード取りこぼし防止"},
        {"order": 5, "focus": "CSF戦略見直し着手",        "rationale": "2週連続目標未達 — 根本原因の分析と改善提案"},
    ]


def get_ceo_to_president() -> list:
    return [
        {"icon": "💰", "item": "BPG写真撮影予算3万円の承認",           "context": "素材残2日、今週中に決定必要。撮影業者見積もり提出済み"},
        {"icon": "📊", "item": "CSF SNS戦略の方向性決定",              "context": "2週連続投稿目標未達。内容・頻度・ターゲット見直しが必要"},
        {"icon": "🤝", "item": "DSc LINE公式アカウント本格活用判断",   "context": "友達追加700名突破。配信施策の本格投資を判断する時期"},
    ]
