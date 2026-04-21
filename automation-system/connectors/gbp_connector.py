"""
Google Business Profile (GBP) Connector
========================================
Abstract base + Mock implementation.

本番接続ポイント:
  - GBPRealConnector を実装し、Google My Business API v4.9 または
    Business Profile API を呼び出す。
  - 認証: OAuth2 (accounts.google.com) or Service Account
  - 環境変数: GBP_CLIENT_ID, GBP_CLIENT_SECRET, GBP_REFRESH_TOKEN
    もしくは GBP_SERVICE_ACCOUNT_JSON

現在は MockGBPConnector がリアルなサンプルデータを返す。
"""

from __future__ import annotations

import os
import random
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional


# ═══════════════════════════════════════════════════════
# Abstract Interface
# ═══════════════════════════════════════════════════════

class GBPConnector(ABC):

    @abstractmethod
    def sync_locations(self) -> list[dict]:
        """アカウント配下の全拠点を返す。"""

    @abstractmethod
    def sync_reviews(self, location_id: str) -> list[dict]:
        """指定拠点のレビューを返す。"""

    @abstractmethod
    def reply_to_review(self, location_id: str, review_id: str, reply_text: str) -> bool:
        """レビューに返信する。成功 True / 失敗 False。"""

    @abstractmethod
    def delete_review_reply(self, location_id: str, review_id: str) -> bool:
        """返信を削除する。"""

    @abstractmethod
    def sync_posts(self, location_id: str) -> list[dict]:
        """指定拠点の投稿一覧を返す。"""

    @abstractmethod
    def create_post(self, location_id: str, post_data: dict) -> dict:
        """投稿を作成し、作成された投稿データを返す。"""

    @abstractmethod
    def sync_media(self, location_id: str) -> list[dict]:
        """メディア（写真・動画）一覧を返す。"""

    @abstractmethod
    def upload_media(self, location_id: str, media_path: str, category: str = "EXTERIOR") -> dict:
        """写真・動画をアップロードする。"""

    @abstractmethod
    def sync_insights(self, location_id: str, period_days: int = 28) -> dict:
        """インサイト（表示回数・アクション数など）を返す。"""


# ═══════════════════════════════════════════════════════
# Mock Implementation
# ═══════════════════════════════════════════════════════

_MOCK_REVIEWS_UPJ = [
    {"gbp_review_id": "rev_upj_001", "reviewer_name": "田中 健太", "rating": 5,
     "comment": "とても丁寧なサービスでした。スタッフの対応が素晴らしく、また利用したいと思います。",
     "status": "unanswered", "created_at": "2026-04-18 10:23:00"},
    {"gbp_review_id": "rev_upj_002", "reviewer_name": "佐藤 美咲", "rating": 4,
     "comment": "全体的に満足です。ただ待ち時間が少し長かったです。",
     "status": "unanswered", "created_at": "2026-04-16 15:47:00"},
    {"gbp_review_id": "rev_upj_003", "reviewer_name": "鈴木 一郎", "rating": 2,
     "comment": "期待していたほどではありませんでした。説明が不足していると感じました。",
     "status": "unanswered", "created_at": "2026-04-14 09:12:00"},
    {"gbp_review_id": "rev_upj_004", "reviewer_name": "山田 花子", "rating": 5,
     "comment": "最高のサービスです！毎回対応が丁寧で信頼できます。",
     "reply": "山田様、嬉しいお言葉ありがとうございます。またのご来店をお待ちしております。",
     "status": "answered", "created_at": "2026-04-10 14:30:00"},
    {"gbp_review_id": "rev_upj_005", "reviewer_name": "中村 太郎", "rating": 1,
     "comment": "スタッフの態度が悪く、二度と行きたくありません。完全に時間の無駄でした。",
     "status": "unanswered", "created_at": "2026-04-08 11:55:00"},
    {"gbp_review_id": "rev_upj_006", "reviewer_name": "伊藤 明", "rating": 3,
     "comment": "普通です。特別良くも悪くもありません。",
     "status": "answered", "reply": "伊藤様、ご利用いただきありがとうございます。",
     "created_at": "2026-04-05 16:20:00"},
]

_MOCK_REVIEWS_DSC = [
    {"gbp_review_id": "rev_dsc_001", "reviewer_name": "高橋 奈々", "rating": 5,
     "comment": "マーケティングのサポートが非常に充実していました。費用対効果が高いです。",
     "status": "answered", "reply": "高橋様、ありがとうございます！引き続き全力でサポートいたします。",
     "created_at": "2026-04-17 13:00:00"},
    {"gbp_review_id": "rev_dsc_002", "reviewer_name": "渡辺 隆", "rating": 4,
     "comment": "良いサービスだと思います。もう少し説明資料があるとなお良いかと。",
     "status": "unanswered", "created_at": "2026-04-15 10:00:00"},
    {"gbp_review_id": "rev_dsc_003", "reviewer_name": "小林 誠", "rating": 2,
     "comment": "返信が遅い。問い合わせから3日経っても連絡がありませんでした。",
     "status": "unanswered", "created_at": "2026-04-12 08:30:00"},
    {"gbp_review_id": "rev_dsc_004", "reviewer_name": "加藤 由美", "rating": 5,
     "comment": "SNS運用を任せて売上が2倍になりました。本当に感謝しています。",
     "status": "unanswered", "created_at": "2026-04-11 09:45:00"},
]

_MOCK_REVIEWS_BPG = [
    {"gbp_review_id": "rev_bpg_001", "reviewer_name": "松本 浩二", "rating": 5,
     "comment": "バンコクでこれほど充実したサービスは初めてです。スタッフも日本語対応で安心。",
     "status": "unanswered", "created_at": "2026-04-19 07:30:00"},
    {"gbp_review_id": "rev_bpg_002", "reviewer_name": "井上 裕子", "rating": 3,
     "comment": "場所がわかりにくかったです。案内表示を増やしてほしいです。",
     "status": "unanswered", "created_at": "2026-04-18 14:00:00"},
    {"gbp_review_id": "rev_bpg_003", "reviewer_name": "木村 亮", "rating": 1,
     "comment": "予約したのに待たされました。時間管理をしっかりしてください。",
     "status": "unanswered", "created_at": "2026-04-17 18:00:00"},
    {"gbp_review_id": "rev_bpg_004", "reviewer_name": "林 さくら", "rating": 5,
     "comment": "最高でした！友達にも紹介したいと思います。",
     "reply": "林様、嬉しいお言葉をありがとうございます！ぜひまたお越しください。",
     "status": "answered", "created_at": "2026-04-14 12:00:00"},
]

_MOCK_LOCATIONS = [
    {
        "gbp_location_id": "accounts/123456/locations/upj-shibuya",
        "location_name": "UPJ 渋谷オフィス",
        "brand": "upjapan",
        "address": "東京都渋谷区道玄坂1-12-1",
        "city": "東京",
        "phone": "03-1234-5678",
        "website": "https://upjapan.co.jp/",
        "avg_rating": 3.8,
        "total_reviews": 6,
        "photos_count": 4,
    },
    {
        "gbp_location_id": "accounts/123456/locations/dsc-shinjuku",
        "location_name": "DSc Marketing 新宿",
        "brand": "dsc-marketing",
        "address": "東京都新宿区西新宿2-1-1",
        "city": "東京",
        "phone": "03-9876-5432",
        "website": "https://dsc-marketing.com/",
        "avg_rating": 4.0,
        "total_reviews": 4,
        "photos_count": 12,
    },
    {
        "gbp_location_id": "accounts/123456/locations/bpg-bangkok",
        "location_name": "Bangkok Peach Group",
        "brand": "bangkok-peach",
        "address": "123 Sukhumvit Rd, Bangkok 10110",
        "city": "Bangkok",
        "phone": "+66-2-123-4567",
        "website": "https://bangkok-peach-group.com/",
        "avg_rating": 3.5,
        "total_reviews": 4,
        "photos_count": 2,
    },
]

_MOCK_REVIEWS_BY_LOCATION = {
    "accounts/123456/locations/upj-shibuya":  _MOCK_REVIEWS_UPJ,
    "accounts/123456/locations/dsc-shinjuku": _MOCK_REVIEWS_DSC,
    "accounts/123456/locations/bpg-bangkok":  _MOCK_REVIEWS_BPG,
}

_MOCK_INSIGHTS = {
    "accounts/123456/locations/upj-shibuya": {
        "views_search": 312, "views_maps": 189,
        "actions_website": 47, "actions_directions": 28, "actions_phone": 15,
        "photos_views": 203,
    },
    "accounts/123456/locations/dsc-shinjuku": {
        "views_search": 528, "views_maps": 341,
        "actions_website": 93, "actions_directions": 41, "actions_phone": 22,
        "photos_views": 451,
    },
    "accounts/123456/locations/bpg-bangkok": {
        "views_search": 744, "views_maps": 512,
        "actions_website": 128, "actions_directions": 87, "actions_phone": 56,
        "photos_views": 89,
    },
}


class MockGBPConnector(GBPConnector):
    """開発・デモ用モック。本番 API は呼び出さない。"""

    def sync_locations(self) -> list[dict]:
        return [dict(loc) for loc in _MOCK_LOCATIONS]

    def sync_reviews(self, location_id: str) -> list[dict]:
        reviews = _MOCK_REVIEWS_BY_LOCATION.get(location_id, [])
        return [dict(r) for r in reviews]

    def reply_to_review(self, location_id: str, review_id: str, reply_text: str) -> bool:
        # モック: 常に成功
        return True

    def delete_review_reply(self, location_id: str, review_id: str) -> bool:
        return True

    def sync_posts(self, location_id: str) -> list[dict]:
        now = datetime.now()
        return [
            {"gbp_post_id": f"post_{location_id[-6:]}_001",
             "post_type": "STANDARD",
             "summary": "春の新メニューが登場しました！ぜひご来店ください。",
             "state": "LIVE", "published_at": (now - timedelta(days=3)).strftime("%Y-%m-%d")},
            {"gbp_post_id": f"post_{location_id[-6:]}_002",
             "post_type": "OFFER",
             "summary": "GW限定10%オフキャンペーン実施中。5月6日まで。",
             "state": "LIVE", "published_at": (now - timedelta(days=7)).strftime("%Y-%m-%d")},
        ]

    def create_post(self, location_id: str, post_data: dict) -> dict:
        return {"gbp_post_id": f"post_new_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                **post_data, "state": "LIVE"}

    def sync_media(self, location_id: str) -> list[dict]:
        loc = next((l for l in _MOCK_LOCATIONS if l["gbp_location_id"] == location_id), None)
        count = loc["photos_count"] if loc else 0
        return [{"media_id": f"photo_{i}", "category": "EXTERIOR",
                 "url": f"https://placeholder.example.com/photo_{i}.jpg"}
                for i in range(count)]

    def upload_media(self, location_id: str, media_path: str, category: str = "EXTERIOR") -> dict:
        return {"media_id": f"photo_new_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "category": category, "url": media_path}

    def sync_insights(self, location_id: str, period_days: int = 28) -> dict:
        base = _MOCK_INSIGHTS.get(location_id, {})
        now = datetime.now()
        return {
            "period_start": (now - timedelta(days=period_days)).strftime("%Y-%m-%d"),
            "period_end": now.strftime("%Y-%m-%d"),
            **base,
        }


# ═══════════════════════════════════════════════════════
# Factory
# ═══════════════════════════════════════════════════════

def get_connector() -> GBPConnector:
    """
    環境変数 GBP_CLIENT_ID が設定されていれば本番コネクタ（未実装）を返す。
    未設定の場合はモックを返す。

    本番接続ポイント:
      GBP_CLIENT_ID / GBP_CLIENT_SECRET / GBP_REFRESH_TOKEN を .env に設定し、
      GBPRealConnector を実装してここで返すこと。
    """
    if os.environ.get("GBP_CLIENT_ID"):
        raise NotImplementedError(
            "GBPRealConnector is not yet implemented. "
            "Implement it in connectors/gbp_real.py and wire it here."
        )
    return MockGBPConnector()
