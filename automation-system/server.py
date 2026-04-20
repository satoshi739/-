from __future__ import annotations

"""
LINE Webhook サーバー
- LINEからのメッセージを受け取り、自動返信する
- 新規ユーザーのリードを自動起票する

起動方法:
  python server.py

外部公開が必要:
  ngrok http 5000  （開発・テスト用）
  または Render / Railway にデプロイ（本番用）
"""

import logging
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from flask import Flask, abort, request

from sales.lead_intake import create_lead_from_line, load_lead_by_line_id
from sns.line_api import LINEMessenger

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
_messenger: LINEMessenger | None = None

SCENARIOS_PATH = Path(__file__).parent / "config" / "line_scenarios.yaml"


def _get_messenger() -> LINEMessenger:
    global _messenger
    if _messenger is None:
        _messenger = LINEMessenger()
    return _messenger


def _load_scenarios() -> dict:
    with open(SCENARIOS_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _find_keyword_reply(message: str, scenarios: dict) -> str | None:
    """メッセージにマッチするキーワード返信を探す"""
    for item in scenarios.get("keyword_replies", []):
        for kw in item.get("keywords", []):
            if kw in message:
                return item["reply"]
    return None


@app.route("/webhook", methods=["POST"])
def webhook():
    # 署名検証
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data()
    if not _get_messenger().verify_signature(body, signature):
        logger.warning("署名検証失敗")
        abort(400)

    data = request.get_json()
    scenarios = _load_scenarios()

    for event in data.get("events", []):
        event_type = event.get("type")
        source = event.get("source", {})
        user_id = source.get("userId", "")

        # --- 友だち追加 ---
        if event_type == "follow":
            _handle_follow(user_id, scenarios)

        # --- メッセージ受信 ---
        elif event_type == "message" and event["message"]["type"] == "text":
            text = event["message"]["text"]
            reply_token = event.get("replyToken", "")
            _handle_message(user_id, text, reply_token, scenarios)

    return "OK"


def _handle_follow(user_id: str, scenarios: dict):
    """友だち追加時の処理"""
    messenger = _get_messenger()
    profile = messenger.get_profile(user_id)
    display_name = profile.get("displayName", "")

    # ウェルカムメッセージを送信
    welcome = scenarios.get("welcome_message", "ご登録ありがとうございます！")
    messenger.push(user_id, welcome)
    logger.info(f"ウェルカムメッセージ送信: {display_name} ({user_id})")


def _handle_message(user_id: str, text: str, reply_token: str, scenarios: dict):
    """メッセージ受信時の処理"""
    # 既存リードか確認
    existing = load_lead_by_line_id(user_id)

    messenger = _get_messenger()
    if not existing:
        # 新規リード → 自動起票
        profile = messenger.get_profile(user_id)
        display_name = profile.get("displayName", "")
        lead_path = create_lead_from_line(user_id, display_name, text)
        logger.info(f"新規リード起票: {lead_path}")

    # キーワード返信を探す
    reply = _find_keyword_reply(text, scenarios)
    if reply:
        messenger.reply(reply_token, reply)
    else:
        # デフォルト返信
        default_reply = (
            "メッセージありがとうございます！\n"
            "内容を確認して、担当者からご返信します。\n"
            "（平日10:00〜17:00 受付）"
        )
        messenger.reply(reply_token, default_reply)


@app.route("/", methods=["GET"])
def index():
    return {"status": "ok", "service": "upjapan-automation"}


@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    logger.info(f"LINE Webhookサーバー起動: port={port}")
    app.run(host="0.0.0.0", port=port, debug=False)
