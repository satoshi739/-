from __future__ import annotations

"""
YouTube 動画投稿モジュール
YouTube Data API v3

必要なもの:
- Google Cloud Console で YouTube Data API v3 を有効化
- OAuth2 認証（credentials.json）
- pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
"""

import os, logging
from pathlib import Path
log = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_PATH = Path(__file__).parent.parent / "youtube_token.json"
CREDS_PATH = Path(__file__).parent.parent / "credentials.json"


class YouTubePoster:
    def __init__(self):
        self.dry_run = os.environ.get("DRY_RUN","false").lower() == "true"

    def _service(self):
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        creds = None
        if TOKEN_PATH.exists():
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_PATH), SCOPES)
                creds = flow.run_local_server(port=0)
            TOKEN_PATH.write_text(creds.to_json())
        return build("youtube","v3",credentials=creds)

    def upload_video(
        self,
        file_path: str,
        title: str,
        description: str,
        tags: list[str] | None = None,
        category_id: str = "22",   # 22 = People & Blogs
        privacy: str = "public",
    ) -> dict:
        if self.dry_run:
            log.info(f"[DRY RUN] YouTube動画アップロード: {title}")
            return {"status":"dry_run","title":title}

        from googleapiclient.http import MediaFileUpload

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags or [],
                "categoryId": category_id,
            },
            "status": {"privacyStatus": privacy},
        }
        media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
        req = self._service().videos().insert(
            part="snippet,status", body=body, media_body=media
        )
        resp = None
        while resp is None:
            _, resp = req.next_chunk()
        video_id = resp["id"]
        log.info(f"YouTube動画アップロード完了: https://youtu.be/{video_id}")
        return {"status":"uploaded","video_id":video_id,"url":f"https://youtu.be/{video_id}"}
