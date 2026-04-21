# 環境変数設定ガイド — UPJ Autonomous Brand OS

このガイドに従って `.env` を設定すると、全自動化が有効になります。

---

## 優先順位

| 優先度 | キー | 効果 |
|---|---|---|
| ★★★ 最優先 | `DASHBOARD_PASSWORD` | ダッシュボードログインを有効化 |
| ★★★ 最優先 | `META_ACCESS_TOKEN` | Instagram 全機能（投稿・Story・インサイト） |
| ★★★ 最優先 | `LINE_CHANNEL_ACCESS_TOKEN` | LINE通知・朝のサマリー・一斉配信 |
| ★★ 重要 | `ANTHROPIC_API_KEY` | AI文章生成・NoiMos・キャプション自動生成 |
| ★ あれば便利 | `INSTAGRAM_BUSINESS_ACCOUNT_ID` | 複数アカウント管理時に明示指定 |
| ★ あれば便利 | WordPress系 | ブログ自動公開 |

---

## 1. ダッシュボード認証

```env
DASHBOARD_PASSWORD=任意のパスワード
```

設定しないとダッシュボードに誰でもアクセスできます。**必ず設定してください。**

---

## 2. Meta / Instagram（最重要）

Instagram の投稿・Story・インサイト取得に必要です。

### 取得手順

1. [Meta for Developers](https://developers.facebook.com/) にログイン
2. 「マイアプリ」→「アプリを作成」→「ビジネス」を選択
3. 「Instagram Graph API」を製品に追加
4. 左メニュー「ツール」→「Graph API エクスプローラー」を開く
5. 「ユーザートークンを生成」をクリック
6. 権限を選択（下記すべてにチェック）:
   - `instagram_basic`
   - `instagram_content_publish`
   - `instagram_manage_insights`
   - `pages_read_engagement`
7. 「アクセストークンを生成」→ コピー
8. **長期トークンに変換**（60日間有効）:
   ```
   https://graph.facebook.com/v21.0/oauth/access_token
     ?grant_type=fb_exchange_token
     &client_id={アプリID}
     &client_secret={アプリシークレット}
     &fb_exchange_token={上記トークン}
   ```

### IG User ID の確認

```
https://graph.facebook.com/v21.0/me/accounts?access_token={トークン}
```
→ 返ってきた `id` の中から Instagram Business Account の ID を使用

```env
META_ACCESS_TOKEN=EAAxxxxxxxxxxxxxxxx
INSTAGRAM_BUSINESS_ACCOUNT_ID=17841400000000000
```

---

## 3. LINE Messaging API

朝のサマリー通知・一斉配信・Webhook受信に必要です。

### 取得手順

1. [LINE Developers Console](https://developers.line.biz/console/) にログイン
2. 「プロバイダー」→「チャネル作成」→「Messaging API」
3. チャネル基本設定 →「チャネルシークレット」をコピー
4. Messaging API設定 →「チャネルアクセストークン（長期）」を発行してコピー
5. Webhook URL を設定:
   - Railway の場合: `https://あなたのapp.railway.app/webhook`
   - Mac ローカルの場合: `https://ngrok のURL/webhook`

```env
LINE_CHANNEL_ACCESS_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LINE_CHANNEL_SECRET=xxxxxxxxxxxxxxxxxxxxxxxx
OWNER_LINE_USER_ID=Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> `OWNER_LINE_USER_ID`: 朝のサマリーを受け取る自分のLINE User ID。
> LINE Developers Console の「ユーザーID」または Webhook で受信した `source.userId` から確認。

---

## 4. Anthropic API（AI生成）

NoiMos・キャプション自動生成・週次カレンダー生成に必要です。

### 取得手順

1. [console.anthropic.com](https://console.anthropic.com/) にログイン
2. 「API Keys」→「Create Key」

```env
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 5. WordPress（ブログ自動公開）

各ブランドのWordPressブログに自動投稿する場合に設定します。

```env
# Satoshi Life Blog
SATOSHI_BLOG_WP_URL=https://satoshi-life.site
SATOSHI_BLOG_WP_USER=satoshi0107
SATOSHI_BLOG_WP_PASSWORD=アプリパスワード

# DSC Marketing
DSC_MARKETING_WP_URL=https://dsc-marketing.com
DSC_MARKETING_WP_USER=admin
DSC_MARKETING_WP_PASSWORD=アプリパスワード
```

> **アプリパスワードの取得**: WordPress管理画面 → ユーザー → プロフィール → 「アプリケーションパスワード」→ 新規追加

---

## 6. Google（MEO・Drive連携）

```env
# Google Drive（素材自動同期）
GOOGLE_DRIVE_FOLDER_ID=1xxxxxxxxxxxxxxxxxxxxxxxxx

# Google Business Profile（MEO管理）
# サービスアカウントのJSONキーファイルのパス
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

---

## 設定後の確認方法

```bash
# ダッシュボードを再起動
bash setup_launchd.sh

# Instagram接続テスト
python3 -c "
from connectors.meta_connector import get_meta_connector
c = get_meta_connector('auto')
print(type(c).__name__)  # MetaRealConnector なら本番接続OK
"

# スケジューラーログ確認
tail -f logs/scheduler.log
```

---

## 接続状況の見方（ダッシュボード）

- ブランド設定画面（`/settings/upjapan`）で各APIの接続テストができます
- ブランド運転席（`/brands/upjapan`）でリアルタイムの稼働状況を確認できます
- AI組織画面（`/agents`）でエージェントの稼働状態を確認できます

---

## DRY_RUN モード（テスト用）

```env
DRY_RUN=true
```

`true` にすると、実際の投稿・送信をせずにログだけ出力します。
本番稼働前の動作確認に使ってください。設定後は必ず `false` に戻してください。
