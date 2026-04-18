#!/bin/bash
# =====================================================
# UPJ Dashboard 起動スクリプト
# 使い方: ./start.sh [dev|prod]
# =====================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

MODE="${1:-dev}"

# .env が無ければ .env.example からコピー
if [ ! -f ".env" ]; then
  if [ -f ".env.example" ]; then
    cp .env.example .env
    echo "⚠️  .env を .env.example からコピーしました。APIキーを設定してください。"
  fi
fi

# 必要なディレクトリを作成
mkdir -p data logs data/backups \
  content_queue/instagram content_queue/line \
  decision_queue media/inbox media/processed \
  generated_media

# DBを初期化 + YAML移行
echo "🗄  データベースを初期化中..."
python database.py

echo ""
if [ "$MODE" = "prod" ]; then
  echo "🚀 本番モードで起動 (gunicorn)"
  exec gunicorn \
    --bind 0.0.0.0:${DASHBOARD_PORT:-8080} \
    --workers 2 \
    --worker-class sync \
    --timeout 120 \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --log-level info \
    "dashboard.app:app"
else
  echo "🛠  開発モードで起動 (Flask)"
  exec python dashboard/app.py
fi
