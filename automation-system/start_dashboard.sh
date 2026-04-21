#!/bin/bash
# Railway / 本番サーバー用ダッシュボード起動スクリプト
cd "$(dirname "$0")"
export PYTHONPATH="$(pwd)/dashboard:$(pwd)"
exec gunicorn "app:app" \
    --bind "0.0.0.0:${PORT:-8080}" \
    --workers 2 \
    --timeout 120 \
    --chdir "$(pwd)/dashboard" \
    --access-logfile - \
    --error-logfile -
