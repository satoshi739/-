"""
Meta / Instagram Graph API Connector
=====================================
Abstract base + Mock implementation.

本番接続ポイント:
  - MetaRealConnector を実装し、Instagram Graph API v21+ を呼び出す。
  - 認証: Long-lived User Access Token or System User Token
  - 環境変数: META_ACCESS_TOKEN, INSTAGRAM_BUSINESS_ACCOUNT_ID

Media container flow (story / feed / reel):
  1. create_media_container() → media_container_id
  2. (poll until status == FINISHED)
  3. publish_media_container(media_container_id) → ig_media_id

現在は MockMetaConnector がリアルなサンプルデータを返す。
"""

from __future__ import annotations

import os
import random
import string
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional


# ═══════════════════════════════════════════════════════
# Data Models (plain dicts — no extra dependency)
# ═══════════════════════════════════════════════════════

def _media_id() -> str:
    return "ig_" + "".join(random.choices(string.digits, k=17))

def _container_id() -> str:
    return "cnt_" + "".join(random.choices(string.digits, k=16))

def _ts() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S+0000")


# ═══════════════════════════════════════════════════════
# Abstract Interface
# ═══════════════════════════════════════════════════════

class MetaConnector(ABC):
    """Meta / Instagram Graph API の抽象インターフェース。"""

    # ── Account ───────────────────────────────────────

    @abstractmethod
    def validate_account(self, ig_user_id: str) -> dict:
        """
        アカウントが有効か検証する。
        Returns: {"ok": bool, "name": str, "followers": int, "error": str|None}
        """

    @abstractmethod
    def get_account_info(self, ig_user_id: str) -> dict:
        """アカウント情報を返す。"""

    # ── Media Container Flow ──────────────────────────

    @abstractmethod
    def create_media_container(
        self,
        ig_user_id: str,
        media_type: str,          # IMAGE | VIDEO | REELS | STORIES
        image_url: Optional[str] = None,
        video_url: Optional[str] = None,
        caption: Optional[str] = None,
        is_carousel_item: bool = False,
    ) -> dict:
        """
        メディアコンテナを作成する（step 1）。
        Returns: {"container_id": str, "status": str, "error": str|None}
        """

    @abstractmethod
    def get_container_status(self, container_id: str) -> dict:
        """
        コンテナの処理状況を確認する。
        Returns: {"status_code": "FINISHED"|"IN_PROGRESS"|"ERROR", "error": str|None}
        """

    @abstractmethod
    def publish_media_container(
        self, ig_user_id: str, container_id: str
    ) -> dict:
        """
        コンテナを公開する（step 2）。
        Returns: {"ig_media_id": str, "permalink": str, "error": str|None}
        """

    # ── High-level publish helpers ────────────────────

    @abstractmethod
    def publish_feed_post(
        self,
        ig_user_id: str,
        image_url: str,
        caption: str,
    ) -> dict:
        """
        フィード投稿（画像）を公開する。
        Returns: {"ig_media_id": str, "permalink": str, "error": str|None}
        """

    @abstractmethod
    def publish_reel(
        self,
        ig_user_id: str,
        video_url: str,
        caption: str,
        thumbnail_url: Optional[str] = None,
    ) -> dict:
        """
        リールを公開する。
        Returns: {"ig_media_id": str, "permalink": str, "error": str|None}
        """

    @abstractmethod
    def publish_story(
        self,
        ig_user_id: str,
        media_url: str,
        media_type: str = "IMAGE",   # IMAGE | VIDEO
        sticker_config: Optional[dict] = None,
    ) -> dict:
        """
        ストーリーを公開する。
        Returns: {"ig_media_id": str, "permalink": str, "error": str|None}
        """

    # ── Insights ─────────────────────────────────────

    @abstractmethod
    def fetch_media_insights(self, ig_media_id: str) -> dict:
        """
        メディアのインサイトを取得する。
        Returns: {"impressions": int, "reach": int, "likes": int, ...}
        """

    @abstractmethod
    def fetch_account_insights(
        self, ig_user_id: str, days: int = 28
    ) -> dict:
        """
        アカウント全体のインサイトを取得する（期間指定）。
        Returns: {"followers": int, "impressions": int, "reach": int, ...}
        """


# ═══════════════════════════════════════════════════════
# Mock Implementation
# ═══════════════════════════════════════════════════════

class MockMetaConnector(MetaConnector):
    """
    開発・テスト用モック実装。
    外部 API へのリクエストは一切行わない。
    """

    MOCK_ACCOUNTS = {
        "upjapan":        {"name": "UP JAPAN",            "followers": 3_420,  "ig_user_id": "17841412345678901"},
        "dsc-marketing":  {"name": "DSc Marketing",       "followers": 8_910,  "ig_user_id": "17841498765432101"},
        "cashflowsupport":{"name": "Cash Flow Support",   "followers": 1_280,  "ig_user_id": "17841411122334401"},
        "satoshi-blog":   {"name": "Satoshi Life Blog",   "followers": 510,    "ig_user_id": "17841455566778901"},
        "bangkok-peach":  {"name": "Bangkok Peach Group", "followers": 12_800, "ig_user_id": "17841477788990011"},
    }

    def validate_account(self, ig_user_id: str) -> dict:
        for brand, info in self.MOCK_ACCOUNTS.items():
            if info["ig_user_id"] == ig_user_id or brand == ig_user_id:
                return {"ok": True, "name": info["name"], "followers": info["followers"], "error": None}
        return {"ok": True, "name": "Mock Account", "followers": random.randint(500, 10_000), "error": None}

    def get_account_info(self, ig_user_id: str) -> dict:
        for brand, info in self.MOCK_ACCOUNTS.items():
            if info["ig_user_id"] == ig_user_id or brand == ig_user_id:
                return {**info, "biography": "Mock bio", "website": f"https://{brand}.example.com"}
        return {"name": "Mock Account", "followers": 1_000, "biography": "", "website": ""}

    def create_media_container(
        self,
        ig_user_id: str,
        media_type: str,
        image_url: Optional[str] = None,
        video_url: Optional[str] = None,
        caption: Optional[str] = None,
        is_carousel_item: bool = False,
    ) -> dict:
        time.sleep(0.05)  # ネットワーク遅延シミュレーション
        return {"container_id": _container_id(), "status": "IN_PROGRESS", "error": None}

    def get_container_status(self, container_id: str) -> dict:
        return {"status_code": "FINISHED", "error": None}

    def publish_media_container(self, ig_user_id: str, container_id: str) -> dict:
        mid = _media_id()
        return {
            "ig_media_id": mid,
            "permalink":   f"https://www.instagram.com/p/{mid[:11]}/",
            "error":       None,
        }

    def publish_feed_post(self, ig_user_id: str, image_url: str, caption: str) -> dict:
        cnt = self.create_media_container(ig_user_id, "IMAGE", image_url=image_url, caption=caption)
        if cnt["error"]:
            return cnt
        return self.publish_media_container(ig_user_id, cnt["container_id"])

    def publish_reel(
        self,
        ig_user_id: str,
        video_url: str,
        caption: str,
        thumbnail_url: Optional[str] = None,
    ) -> dict:
        cnt = self.create_media_container(ig_user_id, "REELS", video_url=video_url, caption=caption)
        if cnt["error"]:
            return cnt
        return self.publish_media_container(ig_user_id, cnt["container_id"])

    def publish_story(
        self,
        ig_user_id: str,
        media_url: str,
        media_type: str = "IMAGE",
        sticker_config: Optional[dict] = None,
    ) -> dict:
        cnt = self.create_media_container(ig_user_id, "STORIES", image_url=media_url)
        if cnt["error"]:
            return cnt
        result = self.publish_media_container(ig_user_id, cnt["container_id"])
        # ストーリーのパーマリンクは特殊（一時的）
        result["permalink"] = f"https://www.instagram.com/stories/{ig_user_id}/{result['ig_media_id']}/"
        return result

    def fetch_media_insights(self, ig_media_id: str) -> dict:
        base = random.randint(800, 5_000)
        return {
            "impressions":  base,
            "reach":        int(base * random.uniform(0.7, 0.95)),
            "likes":        int(base * random.uniform(0.02, 0.08)),
            "comments":     int(base * random.uniform(0.005, 0.02)),
            "saves":        int(base * random.uniform(0.01, 0.04)),
            "shares":       int(base * random.uniform(0.005, 0.015)),
            "video_views":  int(base * random.uniform(0.3, 0.7)),
            "replies":      int(base * random.uniform(0.003, 0.01)),
            "exits":        int(base * random.uniform(0.1, 0.3)),
            "taps_forward": int(base * random.uniform(0.05, 0.15)),
            "taps_back":    int(base * random.uniform(0.01, 0.05)),
            "engagement_rate": round(random.uniform(1.5, 6.5), 2),
        }

    def fetch_account_insights(self, ig_user_id: str, days: int = 28) -> dict:
        for brand, info in self.MOCK_ACCOUNTS.items():
            if info["ig_user_id"] == ig_user_id or brand == ig_user_id:
                base = info["followers"]
                break
        else:
            base = 2_000
        return {
            "followers":    base,
            "impressions":  base * days // 2,
            "reach":        base * days // 3,
            "profile_views": int(base * 0.15 * days),
            "website_clicks": int(base * 0.02 * days),
            "new_followers": int(base * 0.05),
            "period_days":  days,
        }


# ═══════════════════════════════════════════════════════
# Real Connector Stub (implement when token is ready)
# ═══════════════════════════════════════════════════════

class MetaRealConnector(MetaConnector):
    """
    本番用 Meta Graph API コネクタ (v21.0)
    ENV:
      META_ACCESS_TOKEN              — Long-lived User/System Token
      INSTAGRAM_BUSINESS_ACCOUNT_ID — IG User ID (数字)
    """

    BASE = "https://graph.facebook.com/v21.0"
    CONTAINER_POLL_SEC = 5
    CONTAINER_POLL_MAX = 24   # 最大 2分待機

    def __init__(self, access_token: str = ""):
        import requests as _req
        self._requests = _req
        self._token = access_token or os.environ.get("META_ACCESS_TOKEN", "")
        if not self._token:
            raise ValueError("META_ACCESS_TOKEN が設定されていません")

    # ── HTTP helpers ───────────────────────────────────────

    def _get(self, path: str, params: dict = None) -> dict:
        p = dict(params or {})
        p["access_token"] = self._token
        r = self._requests.get(f"{self.BASE}/{path}", params=p, timeout=30)
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            raise RuntimeError(f"Meta API error: {data['error']}")
        return data

    def _post(self, path: str, data: dict = None) -> dict:
        d = dict(data or {})
        d["access_token"] = self._token
        r = self._requests.post(f"{self.BASE}/{path}", data=d, timeout=30)
        r.raise_for_status()
        resp = r.json()
        if "error" in resp:
            raise RuntimeError(f"Meta API error: {resp['error']}")
        return resp

    def _poll_container(self, container_id: str) -> str:
        """FINISHED になるまでポーリング。完了した status_code を返す。"""
        for _ in range(self.CONTAINER_POLL_MAX):
            status = self.get_container_status(container_id)
            code = status.get("status_code", "")
            if code == "FINISHED":
                return code
            if code == "ERROR":
                raise RuntimeError(f"コンテナ処理エラー: {status.get('error')}")
            time.sleep(self.CONTAINER_POLL_SEC)
        raise TimeoutError(f"コンテナ {container_id} の処理がタイムアウトしました")

    # ── Account ───────────────────────────────────────────

    def validate_account(self, ig_user_id: str) -> dict:
        try:
            info = self.get_account_info(ig_user_id)
            return {
                "ok": True,
                "name": info.get("name", ""),
                "username": info.get("username", ""),
                "followers": info.get("followers_count", 0),
                "error": None,
            }
        except Exception as e:
            return {"ok": False, "name": "", "followers": 0, "error": str(e)}

    def get_account_info(self, ig_user_id: str) -> dict:
        return self._get(
            ig_user_id,
            {"fields": "name,username,biography,followers_count,media_count,profile_picture_url,website"}
        )

    # ── Media Container Flow ──────────────────────────────

    def create_media_container(
        self,
        ig_user_id: str,
        media_type: str,
        image_url: Optional[str] = None,
        video_url: Optional[str] = None,
        caption: Optional[str] = None,
        is_carousel_item: bool = False,
    ) -> dict:
        payload: dict = {"media_type": media_type}
        if image_url:
            payload["image_url"] = image_url
        if video_url:
            payload["video_url"] = video_url
        if caption:
            payload["caption"] = caption
        if is_carousel_item:
            payload["is_carousel_item"] = "true"

        # STORIES は media_type パラメータが不要（自動判定）
        if media_type == "STORIES":
            payload.pop("media_type", None)

        try:
            data = self._post(f"{ig_user_id}/media", payload)
            return {"container_id": data["id"], "status": "created", "error": None}
        except Exception as e:
            return {"container_id": "", "status": "error", "error": str(e)}

    def get_container_status(self, container_id: str) -> dict:
        try:
            data = self._get(container_id, {"fields": "status_code,status"})
            return {
                "status_code": data.get("status_code", "UNKNOWN"),
                "status": data.get("status", ""),
                "error": None,
            }
        except Exception as e:
            return {"status_code": "ERROR", "status": "", "error": str(e)}

    def publish_media_container(self, ig_user_id: str, container_id: str) -> dict:
        try:
            data = self._post(f"{ig_user_id}/media_publish", {"creation_id": container_id})
            ig_media_id = data["id"]
            # permalink を取得
            info = self._get(ig_media_id, {"fields": "permalink"})
            return {
                "ig_media_id": ig_media_id,
                "permalink": info.get("permalink", ""),
                "error": None,
            }
        except Exception as e:
            return {"ig_media_id": "", "permalink": "", "error": str(e)}

    # ── High-level helpers ────────────────────────────────

    def publish_feed_post(self, ig_user_id: str, image_url: str, caption: str) -> dict:
        r = self.create_media_container(ig_user_id, "IMAGE", image_url=image_url, caption=caption)
        if r["error"]:
            return {"ig_media_id": "", "permalink": "", "error": r["error"]}
        self._poll_container(r["container_id"])
        return self.publish_media_container(ig_user_id, r["container_id"])

    def publish_reel(
        self,
        ig_user_id: str,
        video_url: str,
        caption: str,
        thumbnail_url: Optional[str] = None,
    ) -> dict:
        payload: dict = {
            "ig_user_id": ig_user_id,
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
        }
        if thumbnail_url:
            payload["thumb_offset"] = "0"
        r = self.create_media_container(ig_user_id, "REELS", video_url=video_url, caption=caption)
        if r["error"]:
            return {"ig_media_id": "", "permalink": "", "error": r["error"]}
        self._poll_container(r["container_id"])
        return self.publish_media_container(ig_user_id, r["container_id"])

    def publish_story(
        self,
        ig_user_id: str,
        media_url: str,
        media_type: str = "IMAGE",
        sticker_config: Optional[dict] = None,
    ) -> dict:
        # Stories: IMAGE または VIDEO
        if media_type == "VIDEO":
            r = self.create_media_container(ig_user_id, "STORIES", video_url=media_url)
        else:
            r = self.create_media_container(ig_user_id, "STORIES", image_url=media_url)
        if r["error"]:
            return {"ig_media_id": "", "permalink": "", "error": r["error"]}
        self._poll_container(r["container_id"])
        return self.publish_media_container(ig_user_id, r["container_id"])

    # ── Insights ─────────────────────────────────────────

    def fetch_media_insights(self, ig_media_id: str) -> dict:
        fields = "impressions,reach,likes_count,comments_count,saved,shares"
        try:
            # feed/reel と story でエンドポイントが異なる
            try:
                data = self._get(f"{ig_media_id}/insights", {"metric": fields})
            except Exception:
                # story 用フォールバック
                data = self._get(
                    f"{ig_media_id}/insights",
                    {"metric": "impressions,reach,replies,exits,taps_forward,taps_back"}
                )
            result: dict = {}
            for item in data.get("data", []):
                result[item["name"]] = item.get("values", [{}])[0].get("value", 0)
            return result
        except Exception as e:
            return {"error": str(e)}

    def fetch_account_insights(self, ig_user_id: str, days: int = 28) -> dict:
        since = int(time.time()) - days * 86400
        until = int(time.time())
        metrics = "impressions,reach,profile_views,follower_count,email_contacts,phone_call_clicks"
        try:
            data = self._get(
                f"{ig_user_id}/insights",
                {
                    "metric": metrics,
                    "period": "day",
                    "since": since,
                    "until": until,
                }
            )
            result: dict = {"days": days}
            for item in data.get("data", []):
                vals = [v.get("value", 0) for v in item.get("values", [])]
                result[item["name"]] = sum(vals)
            # フォロワー数は別途取得
            info = self.get_account_info(ig_user_id)
            result["followers"] = info.get("followers_count", 0)
            return result
        except Exception as e:
            return {"error": str(e)}


# ═══════════════════════════════════════════════════════
# Factory
# ═══════════════════════════════════════════════════════

def get_meta_connector(provider: str = "auto") -> MetaConnector:
    """
    provider="auto" → META_ACCESS_TOKEN があれば real、なければ mock（デフォルト）
    provider="mock" → MockMetaConnector（常に）
    provider="real" → MetaRealConnector（トークン必須）
    """
    if provider == "mock":
        return MockMetaConnector()
    token = os.environ.get("META_ACCESS_TOKEN", "")
    if provider == "real":
        if not token:
            raise ValueError("META_ACCESS_TOKEN が設定されていません")
        return MetaRealConnector(token)
    # auto: トークンがあればreal、なければmock
    if token:
        return MetaRealConnector(token)
    return MockMetaConnector()
