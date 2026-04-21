# 環境変数

## 設定方法

`.env` ファイル（`automation-system/` 直下）または Railway / Heroku の環境変数で設定。

```bash
cp automation-system/.env.example automation-system/.env
# 各値を編集
```

## 必須変数

| 変数名 | 説明 | 例 |
|--------|------|-----|
| `ANTHROPIC_API_KEY` | Claude API キー。未設定時は AI 機能が無効化される | `sk-ant-...` |
| `DASHBOARD_PASSWORD` | ダッシュボードのログインパスワード。**未設定時は認証スキップ** | `your-strong-password` |

## オプション変数

### Flask / サーバー

| 変数名 | デフォルト | 説明 |
|--------|-----------|------|
| `FLASK_SECRET_KEY` | ランダム生成 | セッション暗号化キー。**本番では必ず設定** |
| `PORT` | `8080` | サーバーポート |
| `FLASK_DEBUG` | `false` | デバッグモード（`true` で有効化） |

### LINE Bot

| 変数名 | 説明 |
|--------|------|
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Messaging API チャンネルアクセストークン |
| `LINE_CHANNEL_SECRET` | LINE チャンネルシークレット（Webhook 署名検証） |

### Instagram / Meta

| 変数名 | 説明 |
|--------|------|
| `META_APP_ID` | Meta アプリ ID |
| `META_APP_SECRET` | Meta アプリシークレット |
| `INSTAGRAM_ACCESS_TOKEN` | Instagram Graph API アクセストークン |
| `INSTAGRAM_BUSINESS_ACCOUNT_ID` | ビジネスアカウント ID |

### Google

| 変数名 | 説明 |
|--------|------|
| `GOOGLE_OAUTH_CLIENT_ID` | Google OAuth クライアント ID |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Google OAuth クライアントシークレット |
| `GOOGLE_REFRESH_TOKEN` | Google リフレッシュトークン（GBP・Drive 共通） |
| `GBP_LOCATION_ID` | Google Business Profile のロケーション ID |

### Twitter / X

| 変数名 | 説明 |
|--------|------|
| `TWITTER_API_KEY` | Twitter API キー |
| `TWITTER_API_SECRET` | Twitter API シークレット |
| `TWITTER_ACCESS_TOKEN` | アクセストークン |
| `TWITTER_ACCESS_SECRET` | アクセストークンシークレット |

### TikTok

| 変数名 | 説明 |
|--------|------|
| `TIKTOK_ACCESS_TOKEN` | TikTok API アクセストークン |

### WordPress

| 変数名 | 説明 |
|--------|------|
| `WORDPRESS_URL` | WordPress サイト URL |
| `WORDPRESS_USERNAME` | 管理者ユーザー名 |
| `WORDPRESS_APP_PASSWORD` | WordPress アプリケーションパスワード |

### メール

| 変数名 | 説明 |
|--------|------|
| `SMTP_HOST` | SMTP サーバーホスト |
| `SMTP_PORT` | SMTP ポート（通常 587） |
| `SMTP_USER` | SMTP ユーザー名 |
| `SMTP_PASS` | SMTP パスワード |

## 環境変数チェック

```python
# ダッシュボード内での確認
import os
print(os.environ.get("ANTHROPIC_API_KEY", "未設定"))
```

ダッシュボードの `/health` エンドポイントで稼働確認が可能。AI 接続状態は `/api/stats` の `ai_enabled` フィールドで確認できる。

## .env.example テンプレート

```bash
# ── 必須 ──────────────────────────────
ANTHROPIC_API_KEY=
DASHBOARD_PASSWORD=

# ── Flask ──────────────────────────────
FLASK_SECRET_KEY=
PORT=8080
FLASK_DEBUG=false

# ── LINE ──────────────────────────────
LINE_CHANNEL_ACCESS_TOKEN=
LINE_CHANNEL_SECRET=

# ── Meta / Instagram ──────────────────
META_APP_ID=
META_APP_SECRET=
INSTAGRAM_ACCESS_TOKEN=
INSTAGRAM_BUSINESS_ACCOUNT_ID=

# ── Google / GBP ──────────────────────
GOOGLE_OAUTH_CLIENT_ID=
GOOGLE_OAUTH_CLIENT_SECRET=
GOOGLE_REFRESH_TOKEN=
GBP_LOCATION_ID=

# ── Twitter ───────────────────────────
TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_SECRET=

# ── WordPress ─────────────────────────
WORDPRESS_URL=
WORDPRESS_USERNAME=
WORDPRESS_APP_PASSWORD=
```
