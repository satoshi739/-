"""
DB バックアップ → Google Drive アップロード

ENV:
  DB_BACKUP_DRIVE_FOLDER_ID  — バックアップ先の Google Drive フォルダID（必須）
  ALERT_LINE_CHANNEL_ACCESS_TOKEN / OWNER_LINE_USER_ID — 失敗時LINE通知

スケジューラーから呼び出す:
  from db_backup import backup_and_upload
  backup_and_upload()
"""

from __future__ import annotations

import logging
import os
import shutil
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / "data" / "upj.db"
BACKUP_DIR = Path(__file__).parent / "data" / "backups"
CREDENTIALS_PATH = Path(__file__).parent / "credentials.json"
KEEP_LOCAL_DAYS = 7
KEEP_DRIVE_COUNT = 30  # Drive上に保持するバックアップ数


def _line_alert(message: str) -> None:
    try:
        import requests
        token = os.environ.get("ALERT_LINE_CHANNEL_ACCESS_TOKEN", "")
        user_id = os.environ.get("OWNER_LINE_USER_ID", "")
        if token and user_id:
            requests.post(
                "https://api.line.me/v2/bot/message/push",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"to": user_id, "messages": [{"type": "text", "text": f"[DBバックアップ]\n{message}"}]},
                timeout=5,
            )
    except Exception as exc:
        logger.error("LINE通知失敗: %s", exc)


def _get_drive_service():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    creds = service_account.Credentials.from_service_account_file(
        str(CREDENTIALS_PATH),
        scopes=["https://www.googleapis.com/auth/drive.file"],
    )
    return build("drive", "v3", credentials=creds)


def _make_local_backup() -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = BACKUP_DIR / f"upj_{ts}.db"
    shutil.copy2(DB_PATH, dest)
    # 古いローカルバックアップを削除
    cutoff = datetime.now().timestamp() - KEEP_LOCAL_DAYS * 86400
    for f in BACKUP_DIR.glob("upj_*.db"):
        if f.stat().st_mtime < cutoff:
            f.unlink(missing_ok=True)
    return dest


def _upload_to_drive(local_path: Path, folder_id: str) -> str:
    from googleapiclient.http import MediaFileUpload
    service = _get_drive_service()
    file_metadata = {
        "name": local_path.name,
        "parents": [folder_id],
    }
    media = MediaFileUpload(str(local_path), mimetype="application/octet-stream")
    result = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id,name",
    ).execute()
    # 古いバックアップを Drive から削除（KEEP_DRIVE_COUNT 件を超えたら古い順に削除）
    _prune_drive_backups(service, folder_id)
    return result["id"]


def _prune_drive_backups(service, folder_id: str) -> None:
    try:
        results = service.files().list(
            q=f"'{folder_id}' in parents and name contains 'upj_' and trashed=false",
            orderBy="createdTime",
            fields="files(id,name,createdTime)",
        ).execute()
        files = results.get("files", [])
        if len(files) > KEEP_DRIVE_COUNT:
            for f in files[:len(files) - KEEP_DRIVE_COUNT]:
                service.files().delete(fileId=f["id"]).execute()
                logger.info("古いDriveバックアップを削除: %s", f["name"])
    except Exception as exc:
        logger.warning("Driveバックアップ整理失敗（無視）: %s", exc)


def backup_and_upload() -> dict:
    """
    メイン処理: ローカルバックアップ → Drive アップロード。
    成功/失敗を dict で返す。失敗時は LINE 通知。
    """
    folder_id = os.environ.get("DB_BACKUP_DRIVE_FOLDER_ID", "")
    if not folder_id:
        logger.warning("DB_BACKUP_DRIVE_FOLDER_ID 未設定 — ローカルバックアップのみ実行")

    if not DB_PATH.exists():
        msg = f"DBファイルが見つかりません: {DB_PATH}"
        logger.error(msg)
        _line_alert(f"失敗: {msg}")
        return {"ok": False, "error": msg}

    try:
        local_path = _make_local_backup()
        logger.info("ローカルバックアップ完了: %s (%.1f KB)", local_path.name, local_path.stat().st_size / 1024)
    except Exception as exc:
        msg = f"ローカルバックアップ失敗: {exc}"
        logger.error(msg, exc_info=True)
        _line_alert(f"失敗: {msg}")
        return {"ok": False, "error": msg}

    if not folder_id:
        return {"ok": True, "local": str(local_path), "drive_id": None}

    try:
        drive_id = _upload_to_drive(local_path, folder_id)
        logger.info("Drive アップロード完了: %s → %s", local_path.name, drive_id)
        return {"ok": True, "local": str(local_path), "drive_id": drive_id}
    except Exception as exc:
        msg = f"Drive アップロード失敗: {exc}"
        logger.error(msg, exc_info=True)
        _line_alert(f"失敗: {msg}")
        return {"ok": False, "local": str(local_path), "error": msg}
