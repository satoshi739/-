"""
WordPress REST API からブログ記事を取得するモジュール。
"""

import os
import re
import requests
import logging
from typing import Optional

log = logging.getLogger(__name__)


class BlogFetcher:
    """WordPress REST API v2 からブログ記事を取得"""

    # ブランドごとのWP設定（.envの変数名プレフィックスに対応）
    BRAND_MAP = {
        "satoshi-blog": {
            "url_env": "SATOSHI_BLOG_WP_URL",
            "user_env": "SATOSHI_BLOG_WP_USER",
            "pass_env": "SATOSHI_BLOG_WP_APP_PASSWORD",
        },
        "dsc-marketing": {
            "url_env": "DSC_MARKETING_WP_URL",
            "user_env": "DSC_MARKETING_WP_USER",
            "pass_env": "DSC_MARKETING_WP_APP_PASSWORD",
        },
        "cashflowsupport": {
            "url_env": "CASHFLOWSUPPORT_WP_URL",
            "user_env": "CASHFLOWSUPPORT_WP_USER",
            "pass_env": "CASHFLOWSUPPORT_WP_APP_PASSWORD",
        },
    }

    def __init__(self, brand: str = "satoshi-blog"):
        cfg = self.BRAND_MAP.get(brand, self.BRAND_MAP["satoshi-blog"])
        self.base_url = os.environ.get(cfg["url_env"], "").rstrip("/")
        self.user = os.environ.get(cfg["user_env"], "")
        self.password = os.environ.get(cfg["pass_env"], "")
        self.brand = brand

    def _auth(self):
        if self.user and self.password:
            return (self.user, self.password)
        return None

    def _strip_html(self, html: str) -> str:
        """HTMLタグを除去してプレーンテキストに変換"""
        text = re.sub(r"<[^>]+>", "", html)
        text = re.sub(r"&nbsp;", " ", text)
        text = re.sub(r"&amp;", "&", text)
        text = re.sub(r"&lt;", "<", text)
        text = re.sub(r"&gt;", ">", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def fetch_by_url(self, url: str) -> dict:
        """記事URLからコンテンツを取得"""
        # slug or post_id を URL から抽出してAPIで取得
        api = f"{self.base_url}/wp-json/wp/v2/posts"

        # post IDがURLに含まれている場合
        id_match = re.search(r"[?&]p=(\d+)", url)
        if id_match:
            post_id = id_match.group(1)
            r = requests.get(f"{api}/{post_id}", auth=self._auth(), timeout=30)
            r.raise_for_status()
            return self._parse_post(r.json())

        # slugがURLに含まれている場合
        r = requests.get(api, params={"link": url}, auth=self._auth(), timeout=30)
        r.raise_for_status()
        posts = r.json()
        if not posts:
            raise ValueError(f"記事が見つかりません: {url}")
        return self._parse_post(posts[0])

    def fetch_latest(self, count: int = 1) -> dict:
        """最新記事を取得"""
        api = f"{self.base_url}/wp-json/wp/v2/posts"
        r = requests.get(api, params={"per_page": count, "orderby": "date", "order": "desc"}, auth=self._auth(), timeout=30)
        r.raise_for_status()
        posts = r.json()
        if not posts:
            raise ValueError("記事が見つかりません")
        return self._parse_post(posts[0])

    def _parse_post(self, post: dict) -> dict:
        return {
            "id": post.get("id"),
            "title": self._strip_html(post.get("title", {}).get("rendered", "")),
            "content": self._strip_html(post.get("content", {}).get("rendered", "")),
            "excerpt": self._strip_html(post.get("excerpt", {}).get("rendered", "")),
            "url": post.get("link", ""),
            "date": post.get("date", ""),
        }
