#!/bin/bash
cd "/Users/satoshi/会社全体設定/automation-system"

# .env を安全に読み込む（コメント行・日本語行を除外）
while IFS= read -r line || [ -n "$line" ]; do
    # 空行・#コメント・ASCII以外を含む行をスキップ
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]] || continue
    export "$line" 2>/dev/null || true
done < "/Users/satoshi/会社全体設定/automation-system/.env"

exec "/usr/bin/python3" "/Users/satoshi/会社全体設定/automation-system/scheduler.py"
