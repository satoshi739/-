"""
Asset Brain — サービス層

database.py の低レベル CRUD をラップし、
ビジネスロジック・モックシード・AI タガースタブを提供する。

将来の拡張ポイント:
  - AITaggerStub.tag_asset() を Claude API 呼び出しに差し替える
  - get_recommended_* を機械学習スコアに差し替える
"""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
import database as db

# ──────────────────────────────────────────
# AI Tagger Stub（将来 Claude API に差し替え）
# ──────────────────────────────────────────

class AITaggerStub:
    """
    アセットに AI タグを付与するサービス。
    現在はスタブ実装。本番化する場合は tag_asset() を
    Claude claude-haiku-4-5-20251001 の vision 呼び出しに差し替える。
    """

    def tag_asset(self, asset: dict) -> list[str]:
        """ファイルパス・説明文からタグ候補を返す（スタブ）"""
        return []

    def batch_tag(self, asset_ids: list[str]) -> dict[str, list[str]]:
        """複数アセットをまとめてタグ付け（スタブ）"""
        return {aid: [] for aid in asset_ids}


ai_tagger = AITaggerStub()


# ──────────────────────────────────────────
# 推薦ロジック
# ──────────────────────────────────────────

CHANNEL_TYPE_PREF: dict[str, list[str]] = {
    "instagram": ["photo", "video"],
    "tiktok":    ["video"],
    "youtube":   ["video"],
    "threads":   ["photo", "template"],
    "facebook":  ["photo", "video", "template"],
    "twitter":   ["photo", "template"],
    "line":      ["photo", "template"],
    "wordpress": ["photo", "template", "script"],
}


def get_recommended_by_channel(brand: str, channel: str, limit: int = 6) -> list[dict]:
    preferred_types = CHANNEL_TYPE_PREF.get(channel, ["photo"])
    results: list[dict] = []
    for t in preferred_types:
        assets = db.list_assets(brand=brand, asset_type=t, channel=channel,
                                status="active", limit=limit)
        if not assets:
            assets = db.list_assets(brand=brand, asset_type=t, status="active", limit=limit)
        results.extend(assets)
        if len(results) >= limit:
            break
    seen: set[str] = set()
    out: list[dict] = []
    for a in results:
        if a["asset_id"] not in seen:
            seen.add(a["asset_id"])
            out.append(a)
    return out[:limit]


def get_recommended_by_brand(brand: str, limit: int = 8) -> list[dict]:
    return db.list_assets(brand=brand, status="active", limit=limit)


def get_missing_alerts(brands: list[str]) -> list[dict]:
    """素材不足を検出してアラートリストを返す"""
    alerts: list[dict] = []
    for brand in brands:
        stats = {}
        for t in ("photo", "video", "template", "script"):
            stats[t] = len(db.list_assets(brand=brand, asset_type=t, status="active", limit=1))
        if stats["photo"] == 0:
            alerts.append({"brand": brand, "type": "photo", "message": "写真素材がありません"})
        if stats["video"] == 0:
            alerts.append({"brand": brand, "type": "video", "message": "動画素材がありません"})
        if stats["template"] == 0:
            alerts.append({"brand": brand, "type": "template", "message": "テンプレートがありません"})
    return alerts


# ──────────────────────────────────────────
# モック初期データ
# ──────────────────────────────────────────

MOCK_ASSETS = [
    # UPJ
    {
        "brand": "upjapan", "asset_type": "photo", "title": "オフィス外観 春",
        "description": "UPJ オフィスビル正面・桜シーズン",
        "channel_use": ["instagram", "facebook", "wordpress"],
        "season": "spring", "target_audience": ["法人", "パートナー"],
        "copyright_status": "owned", "face_permission": False, "reusable": True,
        "status": "active", "thumbnail_url": "",
        "ai_tags": ["オフィス", "春", "外観", "桜"],
        "performance_note": "春キャンペーンで高エンゲージメント",
        "created_at": "2026-03-15",
    },
    {
        "brand": "upjapan", "asset_type": "video", "title": "サービス紹介リール 60s",
        "description": "UPJ のソリューション紹介・縦型 60 秒",
        "channel_use": ["instagram", "facebook"],
        "season": "all", "target_audience": ["法人", "スタートアップ"],
        "copyright_status": "owned", "face_permission": True, "reusable": True,
        "status": "active", "thumbnail_url": "", "duration_sec": 60,
        "ai_tags": ["サービス紹介", "リール", "縦型", "法人向け"],
        "performance_note": "CTR 3.2%、保存率高",
        "created_at": "2026-02-10",
    },
    {
        "brand": "upjapan", "asset_type": "template", "title": "採用告知バナー",
        "description": "採用ページへの誘導用バナー（1080×1080）",
        "channel_use": ["instagram", "threads", "facebook"],
        "season": "all", "target_audience": ["求職者"],
        "copyright_status": "owned", "face_permission": False, "reusable": True,
        "status": "active", "thumbnail_url": "", "width": 1080, "height": 1080,
        "ai_tags": ["採用", "バナー", "告知"],
        "performance_note": "",
        "created_at": "2026-01-20",
    },
    {
        "brand": "upjapan", "asset_type": "script", "title": "問い合わせ誘導キャプション",
        "description": "CTA 付き汎用キャプションテンプレート",
        "channel_use": ["instagram", "threads", "twitter"],
        "season": "all", "target_audience": ["法人"],
        "copyright_status": "owned", "face_permission": False, "reusable": True,
        "status": "active", "thumbnail_url": "",
        "ai_tags": ["キャプション", "CTA", "汎用"],
        "performance_note": "",
        "created_at": "2026-01-05",
    },
    # DSc Marketing
    {
        "brand": "dsc-marketing", "asset_type": "photo", "title": "マーケ事例 before/after",
        "description": "クライアント数値改善の図解スライド風",
        "channel_use": ["instagram", "tiktok", "facebook"],
        "season": "all", "target_audience": ["中小企業", "個人事業主"],
        "copyright_status": "owned", "face_permission": False, "reusable": True,
        "status": "active", "thumbnail_url": "",
        "ai_tags": ["事例", "before/after", "マーケティング"],
        "performance_note": "保存数 2x 平均超え",
        "created_at": "2026-03-01",
    },
    {
        "brand": "dsc-marketing", "asset_type": "video", "title": "SNS 運用 Tips リール",
        "description": "ショート動画 30 秒・インスタ縦型",
        "channel_use": ["instagram", "tiktok", "youtube"],
        "season": "all", "target_audience": ["個人事業主", "マーケター"],
        "copyright_status": "owned", "face_permission": True, "reusable": True,
        "status": "active", "thumbnail_url": "", "duration_sec": 30,
        "ai_tags": ["SNS運用", "Tips", "リール", "縦型"],
        "performance_note": "再生完了率 68%",
        "created_at": "2026-02-20",
    },
    {
        "brand": "dsc-marketing", "asset_type": "template", "title": "LP ヒーロービジュアル",
        "description": "サービスページ用バナー 1920×1080",
        "channel_use": ["wordpress", "facebook"],
        "season": "all", "target_audience": ["法人"],
        "copyright_status": "owned", "face_permission": False, "reusable": True,
        "status": "active", "thumbnail_url": "", "width": 1920, "height": 1080,
        "ai_tags": ["LP", "バナー", "ヒーロービジュアル"],
        "performance_note": "",
        "created_at": "2026-01-15",
    },
    {
        "brand": "dsc-marketing", "asset_type": "photo", "title": "チームミーティング風景",
        "description": "オフィスでのブレスト風景・自然光",
        "channel_use": ["instagram", "threads", "linkedin"],
        "season": "all", "target_audience": ["法人", "求職者"],
        "copyright_status": "owned", "face_permission": True, "reusable": True,
        "status": "review_needed", "thumbnail_url": "",
        "ai_tags": ["チーム", "オフィス", "ミーティング"],
        "performance_note": "顔出し許可確認中",
        "created_at": "2026-04-01",
    },
    # cashflowsupport
    {
        "brand": "cashflowsupport", "asset_type": "photo", "title": "資金繰り改善グラフ",
        "description": "キャッシュフロー改善を示すインフォグラフィック",
        "channel_use": ["instagram", "facebook", "wordpress"],
        "season": "all", "target_audience": ["中小企業経営者"],
        "copyright_status": "owned", "face_permission": False, "reusable": True,
        "status": "active", "thumbnail_url": "",
        "ai_tags": ["資金繰り", "グラフ", "インフォグラフィック", "経営"],
        "performance_note": "問い合わせ流入多",
        "created_at": "2026-02-28",
    },
    {
        "brand": "cashflowsupport", "asset_type": "script", "title": "LINE 資金繰り相談 初回トーク",
        "description": "LINE 公式アカウントへの最初の返信テンプレート",
        "channel_use": ["line"],
        "season": "all", "target_audience": ["中小企業経営者"],
        "copyright_status": "owned", "face_permission": False, "reusable": True,
        "status": "active", "thumbnail_url": "",
        "ai_tags": ["LINE", "初回トーク", "スクリプト"],
        "performance_note": "返信率 82%",
        "created_at": "2026-01-10",
    },
    # Bangkok Peach
    {
        "brand": "bangkok-peach", "asset_type": "photo", "title": "バンコク店内夜景",
        "description": "バンコク旗艦店・ライティング演出あり",
        "channel_use": ["instagram", "tiktok", "facebook"],
        "season": "all", "target_audience": ["インバウンド", "在タイ日本人"],
        "copyright_status": "owned", "face_permission": False, "reusable": True,
        "status": "active", "thumbnail_url": "",
        "ai_tags": ["バンコク", "店内", "夜景", "ライティング"],
        "performance_note": "インプ 3 万超え",
        "created_at": "2026-03-10",
    },
    {
        "brand": "bangkok-peach", "asset_type": "video", "title": "サービス体験リール 45s",
        "description": "接客シーン・縦型 45 秒 タイ語字幕付き",
        "channel_use": ["instagram", "tiktok"],
        "season": "all", "target_audience": ["タイ人", "在タイ日本人"],
        "copyright_status": "owned", "face_permission": True, "reusable": True,
        "status": "active", "thumbnail_url": "", "duration_sec": 45,
        "ai_tags": ["体験", "リール", "タイ語", "縦型"],
        "performance_note": "フォロワー増加寄与",
        "created_at": "2026-03-20",
    },
    {
        "brand": "bangkok-peach", "asset_type": "template", "title": "LINE 予約リマインダー",
        "description": "予約前日送付テンプレート",
        "channel_use": ["line"],
        "season": "all", "target_audience": ["既存顧客"],
        "copyright_status": "owned", "face_permission": False, "reusable": True,
        "status": "active", "thumbnail_url": "",
        "ai_tags": ["LINE", "予約", "リマインダー"],
        "performance_note": "キャンセル率 -40%",
        "created_at": "2026-02-05",
    },
]

MOCK_TAGS = [
    ("春", "season", "#10b981"),
    ("夏", "season", "#06b6d4"),
    ("秋", "season", "#f59e0b"),
    ("冬", "season", "#6366f1"),
    ("リール", "content", "#8b5cf6"),
    ("縦型", "format", "#a78bfa"),
    ("事例", "content", "#10b981"),
    ("CTA", "content", "#ef4444"),
    ("法人向け", "audience", "#6366f1"),
    ("Instagram", "channel", "#e1306c"),
    ("TikTok", "channel", "#000000"),
    ("LINE", "channel", "#00c300"),
]

MOCK_USAGES = [
    # asset index 0 (UPJ photo)
    (0, "instagram", "upjapan", "IG春投稿2026-03-20", "いいね 312・保存 45", {"likes": 312, "saves": 45, "reach": 4200}),
    (0, "facebook", "upjapan", "FB春告知", "リーチ 2.1k", {"likes": 87, "reach": 2100}),
    # asset index 1 (UPJ video)
    (1, "instagram", "upjapan", "IG_reel_0210", "CTR 3.2%・再生 8k", {"plays": 8000, "reach": 9200}),
    # asset index 4 (DSc photo)
    (4, "instagram", "dsc-marketing", "IG_case_0301", "保存 210・エンゲ 5.1%", {"saves": 210, "engagement_rate": 5.1}),
    (4, "tiktok", "dsc-marketing", "TT_case_0315", "再生 3.2万", {"plays": 32000, "reach": 28000}),
    # asset index 5 (DSc video)
    (5, "tiktok", "dsc-marketing", "TT_tips_0220", "完了率 68%", {"plays": 15000, "reach": 14000}),
    # asset index 8 (CSF photo)
    (8, "instagram", "cashflowsupport", "IG_cf_0228", "問い合わせ 12件", {"likes": 156, "reach": 3100}),
    # asset index 10 (BPG photo)
    (10, "instagram", "bangkok-peach", "IG_bkk_0310", "インプ 3.1万", {"likes": 892, "reach": 31000}),
    (10, "tiktok", "bangkok-peach", "TT_bkk_0312", "再生 5.8万", {"plays": 58000, "reach": 54000}),
]


def seed_mock_data(force: bool = False) -> int:
    """モックデータを投入する。force=True で既存データがあっても再投入。"""
    existing = db.list_assets(status="active", limit=1)
    if existing and not force:
        return 0

    inserted_ids: list[str] = []
    for asset_data in MOCK_ASSETS:
        aid = db.upsert_asset(asset_data)
        inserted_ids.append(aid)

    for name, category, color in MOCK_TAGS:
        db.ensure_tag(name, category, color)

    # タグリンク（簡易マッピング）
    tag_map = {t[0]: db.ensure_tag(*t) for t in MOCK_TAGS}
    _link_asset_tags(inserted_ids, tag_map)

    # 使用履歴
    for usage in MOCK_USAGES:
        idx, channel, brand, used_in, note, perf = usage
        if idx < len(inserted_ids):
            db.record_asset_usage(
                inserted_ids[idx], channel=channel, brand=brand,
                used_in=used_in, result_note=note, performance=perf,
            )

    return len(inserted_ids)


def _link_asset_tags(asset_ids: list[str], tag_map: dict[str, int]):
    keyword_to_tags = {
        "春": ["春"], "video": ["リール", "縦型"], "template": [],
        "instagram": ["Instagram"], "tiktok": ["TikTok"], "line": ["LINE"],
        "法人": ["法人向け"], "事例": ["事例"], "CTA": ["CTA"],
    }
    for i, aid in enumerate(asset_ids):
        asset = MOCK_ASSETS[i]
        linked: set[str] = set()
        if asset.get("season") == "spring":
            linked.add("春")
        if asset.get("asset_type") == "video":
            linked.update(["リール", "縦型"])
        if "instagram" in asset.get("channel_use", []):
            linked.add("Instagram")
        if "tiktok" in asset.get("channel_use", []):
            linked.add("TikTok")
        if "line" in asset.get("channel_use", []):
            linked.add("LINE")
        for tag_name in linked:
            if tag_name in tag_map:
                db.add_asset_tag(aid, tag_name)
