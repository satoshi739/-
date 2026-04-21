#!/bin/bash
# UPJ Autonomous Brand OS — Mac 常時起動セットアップ
# 実行方法: bash setup_launchd.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$(which python3)"
PLIST_DIR="$HOME/Library/LaunchAgents"
LOG_DIR="$SCRIPT_DIR/logs"

echo "📁 ディレクトリ確認..."
mkdir -p "$PLIST_DIR"
mkdir -p "$LOG_DIR"

# .env から環境変数を読み込んでエクスポート用の文字列を生成
ENV_FILE="$SCRIPT_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  .env ファイルが見つかりません: $ENV_FILE"
    echo "   .env を作成してから再実行してください"
    exit 1
fi

echo "🔐 .env を確認..."

# .env から有効なKEY=VALUE行だけを抽出するヘルパー関数テキスト
# （日本語コメント・空行・スペースのみの行を除外）
LOAD_ENV_SNIPPET='
# .env を安全に読み込む（コメント行・日本語行を除外）
while IFS= read -r line || [ -n "$line" ]; do
    # 空行・#コメント・ASCII以外を含む行をスキップ
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]] || continue
    export "$line" 2>/dev/null || true
done < "'"$ENV_FILE"'"
'

# launchd 用ラッパースクリプトを生成
# ── スケジューラー ──
cat > "$SCRIPT_DIR/run_scheduler.sh" << WRAPPER
#!/bin/bash
cd "$SCRIPT_DIR"
$LOAD_ENV_SNIPPET
exec "$PYTHON" "$SCRIPT_DIR/scheduler.py"
WRAPPER
chmod +x "$SCRIPT_DIR/run_scheduler.sh"

# ── Webhookサーバー ──
cat > "$SCRIPT_DIR/run_server.sh" << WRAPPER
#!/bin/bash
cd "$SCRIPT_DIR"
$LOAD_ENV_SNIPPET
export PORT=5001
exec "$PYTHON" "$SCRIPT_DIR/server.py"
WRAPPER
chmod +x "$SCRIPT_DIR/run_server.sh"

# ── ダッシュボード ──
cat > "$SCRIPT_DIR/run_dashboard.sh" << WRAPPER
#!/bin/bash
cd "$SCRIPT_DIR"
$LOAD_ENV_SNIPPET
export PYTHONPATH="$SCRIPT_DIR/dashboard:$SCRIPT_DIR"
exec "$PYTHON" "$SCRIPT_DIR/dashboard/app.py"
WRAPPER
chmod +x "$SCRIPT_DIR/run_dashboard.sh"

echo "📝 plist を生成..."

# 既存をアンロード
for label in jp.upjapan.scheduler jp.upjapan.webhook jp.upjapan.dashboard; do
    launchctl unload "$PLIST_DIR/${label}.plist" 2>/dev/null || true
done

# ── スケジューラー plist ──
cat > "$PLIST_DIR/jp.upjapan.scheduler.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>jp.upjapan.scheduler</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$SCRIPT_DIR/run_scheduler.sh</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$SCRIPT_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    <key>ThrottleInterval</key>
    <integer>30</integer>
    <key>StandardOutPath</key>
    <string>$LOG_DIR/scheduler.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/scheduler_err.log</string>
</dict>
</plist>
EOF

# ── Webhook plist ──
cat > "$PLIST_DIR/jp.upjapan.webhook.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>jp.upjapan.webhook</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$SCRIPT_DIR/run_server.sh</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$SCRIPT_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    <key>ThrottleInterval</key>
    <integer>10</integer>
    <key>StandardOutPath</key>
    <string>$LOG_DIR/server.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/server_err.log</string>
</dict>
</plist>
EOF

# ── ダッシュボード plist ──
cat > "$PLIST_DIR/jp.upjapan.dashboard.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>jp.upjapan.dashboard</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$SCRIPT_DIR/run_dashboard.sh</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$SCRIPT_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    <key>ThrottleInterval</key>
    <integer>10</integer>
    <key>StandardOutPath</key>
    <string>$LOG_DIR/dashboard.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/dashboard_err.log</string>
</dict>
</plist>
EOF

echo "🚀 起動..."
launchctl load "$PLIST_DIR/jp.upjapan.scheduler.plist"
launchctl load "$PLIST_DIR/jp.upjapan.webhook.plist"
launchctl load "$PLIST_DIR/jp.upjapan.dashboard.plist"

sleep 3

echo ""
echo "============================================"
echo "✅ 常時起動セットアップ完了"
echo "============================================"
echo ""
echo "稼働状況:"
launchctl list | grep upjapan || echo "  （起動中...）"
echo ""
echo "アクセス先:"
echo "  ダッシュボード  : http://localhost:8080"
echo "  Webhook サーバー: http://localhost:5001/webhook"
echo ""
echo "ログ確認コマンド:"
echo "  tail -f $LOG_DIR/scheduler.log"
echo "  tail -f $LOG_DIR/scheduler_err.log"
echo "  tail -f $LOG_DIR/dashboard.log"
echo "  tail -f $LOG_DIR/dashboard_err.log"
echo "  tail -f $LOG_DIR/server.log"
echo ""
echo "手動操作:"
echo "  停止: launchctl unload ~/Library/LaunchAgents/jp.upjapan.scheduler.plist"
echo "  再起動: launchctl kickstart -k gui/\$(id -u)/jp.upjapan.scheduler"
echo "  状態確認: launchctl list | grep upjapan"
echo ""
echo "Mac 再起動後も自動的に全サービスが起動します。"
