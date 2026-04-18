"""
TikTok 投稿モジュール
TikTok Content Posting API

必要なもの:
- TikTok for Developers でアプリを登録
- video.publish スコープ
- アクセストークン（OAuth2）
"""

import os, logging, requests
log = logging.getLogger(__name__)


class TikTokPoster:
    BASE = "https://open.tiktokapis.com/v2"

    def __init__(self, brand: str = "dsc-marketing"):
        prefix = brand.upper().replace("-","_")
        self.token = os.environ.get(f"{prefix}_TIKTOK_ACCESS_TOKEN","")
        self.dry_run = os.environ.get("DRY_RUN","false").lower() == "true"

    def _h(self):
        return {"Authorization": f"Bearer {self.token}","Content-Type":"application/json"}

    def upload_video_url(
        self,
        video_url: str,
        title: str,
        privacy: str = "PUBLIC_TO_EVERYONE",   # or SELF_ONLY for testing
    ) -> dict:
        """動画URLからTikTokに投稿（URL pull upload）"""
        if self.dry_run:
            log.info(f"[DRY RUN] TikTok投稿: {title}")
            return {"status":"dry_run"}
        if not self.token:
            raise ValueError("TikTok アクセストークンが未設定です")

        # Step1: Initialize
        init = requests.post(
            f"{self.BASE}/post/publish/video/init/",
            headers=self._h(),
            json={
                "post_info": {
                    "title": title,
                    "privacy_level": privacy,
                    "disable_duet": False,
                    "disable_comment": False,
                    "disable_stitch": False,
                },
                "source_info": {
                    "source": "PULL_FROM_URL",
                    "video_url": video_url,
                }
            }
        )
        init.raise_for_status()
        publish_id = init.json()["data"]["publish_id"]
        log.info(f"TikTok投稿完了: publish_id={publish_id}")
        return {"status":"posted","publish_id":publish_id}
