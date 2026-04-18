#!/bin/bash
# Mac 起動時に自動起動する設定スクリプト
# 実行方法: bash setup_launchd.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="/usr/bin/python3"
PLIST_DIR="$HOME/Library/LaunchAgents"

mkdir -p "$PLIST_DIR"
mkdir -p "$SCRIPT_DIR/logs"

# 既存の plist をアンロード（再登録のため）
for label in jp.upjapan.scheduler jp.upjapan.webhook jp.upjapan.dashboard; do
    launchctl unload "$PLIST_DIR/${label}.plist" 2>/dev/null || true
done

# --- スケジューラー ---
cat > "$PLIST_DIR/jp.upjapan.scheduler.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>jp.upjapan.scheduler</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON</string>
        <string>$SCRIPT_DIR/scheduler.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$SCRIPT_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$SCRIPT_DIR/logs/scheduler.log</string>
    <key>StandardErrorPath</key>
    <string>$SCRIPT_DIR/logs/scheduler_err.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/Users/satoshi/Library/Python/3.9/bin</string>
    </dict>
</dict>
</plist>
EOF

# --- Webhookサーバー（PORT=5001: macOS AirPlay が 5000 を使用）---
cat > "$PLIST_DIR/jp.upjapan.webhook.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>jp.upjapan.webhook</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON</string>
        <string>$SCRIPT_DIR/server.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$SCRIPT_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$SCRIPT_DIR/logs/server.log</string>
    <key>StandardErrorPath</key>
    <string>$SCRIPT_DIR/logs/server_err.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/Users/satoshi/Library/Python/3.9/bin</string>
        <key>PORT</key>
        <string>5001</string>
    </dict>
</dict>
</plist>
EOF

# --- ダッシュボード（port 8080）---
cat > "$PLIST_DIR/jp.upjapan.dashboard.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>jp.upjapan.dashboard</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON</string>
        <string>$SCRIPT_DIR/dashboard/app.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$SCRIPT_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$SCRIPT_DIR/logs/dashboard.log</string>
    <key>StandardErrorPath</key>
    <string>$SCRIPT_DIR/logs/dashboard_err.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/Users/satoshi/Library/Python/3.9/bin</string>
    </dict>
</dict>
</plist>
EOF

# 起動
launchctl load "$PLIST_DIR/jp.upjapan.scheduler.plist"
launchctl load "$PLIST_DIR/jp.upjapan.webhook.plist"
launchctl load "$PLIST_DIR/jp.upjapan.dashboard.plist"

sleep 2

echo "✅ 自動起動の設定が完了しました"
echo ""
echo "稼働状況:"
launchctl list | grep upjapan
echo ""
echo "アクセス先:"
echo "  ダッシュボード: http://localhost:8080"
echo "  Webhook サーバー: http://localhost:5001/webhook  (LINE の Webhook URL に設定)"
echo ""
echo "ログ確認:"
echo "  tail -f $SCRIPT_DIR/logs/scheduler.log"
echo "  tail -f $SCRIPT_DIR/logs/server.log"
echo "  tail -f $SCRIPT_DIR/logs/dashboard.log"
echo ""
echo "停止:"
echo "  launchctl unload ~/Library/LaunchAgents/jp.upjapan.scheduler.plist"
echo "  launchctl unload ~/Library/LaunchAgents/jp.upjapan.webhook.plist"
echo "  launchctl unload ~/Library/LaunchAgents/jp.upjapan.dashboard.plist"
