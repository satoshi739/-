# 本番接続チェックリスト

本番運用を開始するために必要な作業の一覧です。  
各項目を完了したら ✅ に変更してください。

---

## 1. セキュリティ（最優先）

- [ ] `DASHBOARD_PASSWORD` を強固なパスワードに変更
- [ ] `FLASK_SECRET_KEY` を本番用の32文字以上のランダム文字列に設定
- [ ] `.env` ファイルを `.gitignore` に追加済みを確認
- [ ] Railway / Heroku の環境変数に機密情報を移動（`.env` をコミットしない）
- [ ] データベースバックアップの自動化設定（`database.backup_db()` を cron で呼び出す）

## 2. AI（Claude API）

- [ ] `ANTHROPIC_API_KEY` を設定
- [ ] `/health` エンドポイントで `ai_enabled: true` を確認
- [ ] AI CEO プロファイルを `seed_org.py` または管理画面で設定
- [ ] エージェントの `system_prompt` をブランドに合わせてカスタマイズ

## 3. LINE Bot

- [ ] LINE Developers でチャンネルを作成
- [ ] `LINE_CHANNEL_ACCESS_TOKEN` / `LINE_CHANNEL_SECRET` を設定
- [ ] Webhook URL を `https://your-domain.com/webhook/line` に設定
- [ ] `sales/lead_intake.py` のシナリオを `config/line_scenarios.yaml` で調整

## 4. Instagram / Meta

- [ ] Meta Developer App を作成・承認
- [ ] `META_APP_ID` / `META_APP_SECRET` を設定
- [ ] Instagram Business アカウントをリンク
- [ ] `INSTAGRAM_ACCESS_TOKEN` / `INSTAGRAM_BUSINESS_ACCOUNT_ID` を設定
- [ ] `connectors/meta_connector.py` の `MockMetaConnector` を `RealMetaConnector` に切り替え
- [ ] `social_accounts` テーブルの `provider` を `'meta'` に更新

## 5. Google Business Profile（MEO）

- [ ] Google Cloud Console でプロジェクト・OAuth 設定
- [ ] `GOOGLE_OAUTH_CLIENT_ID` / `GOOGLE_OAUTH_CLIENT_SECRET` を設定
- [ ] OAuth フローで `GOOGLE_REFRESH_TOKEN` を取得
- [ ] `GBP_LOCATION_ID` を設定
- [ ] `connectors/gbp_connector.py` を `RealGBPConnector` に切り替え
- [ ] MEO Control Tower で最初の同期を実行

## 6. Twitter / X（オプション）

- [ ] Twitter Developer Account 申請・承認
- [ ] `TWITTER_API_KEY` / `TWITTER_API_SECRET` / `TWITTER_ACCESS_TOKEN` / `TWITTER_ACCESS_SECRET` を設定
- [ ] `sns/twitter.py` の post 関数が動作することを確認

## 7. TikTok（オプション）

- [ ] TikTok Developer App 作成
- [ ] `TIKTOK_ACCESS_TOKEN` を設定
- [ ] `sns/tiktok.py` の upload 関数をテスト

## 8. WordPress（オプション）

- [ ] WordPress にアプリケーションパスワードを作成
- [ ] `WORDPRESS_URL` / `WORDPRESS_USERNAME` / `WORDPRESS_APP_PASSWORD` を設定
- [ ] `sns/wordpress.py` の post 関数をテスト

## 9. メール通知（オプション）

- [ ] SMTP サーバー設定 (`SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASS`)
- [ ] `sales/email_responder.py` の送信者メールアドレスを設定

## 10. データ

- [ ] ブランド設定を `config/brands.yaml` で更新（実際のブランド情報）
- [ ] `config/os_config.yaml` のエージェント定義を更新
- [ ] モックデータを削除（`provider='mock'` のレコードを DB から削除）
- [ ] 既存リードデータを YAML から SQLite に移行済み確認

## 11. 監視・運用

- [ ] Railway / Heroku のログ監視設定
- [ ] エラーアラート（Sentry 等）の設定
- [ ] DB バックアップのスケジュール設定
- [ ] ダッシュボードの定期巡回スケジュールをチームで決定

## 12. 権限設定

- [ ] 社長ユーザーに `owner` ロールを付与
- [ ] 運用担当者に `operator` ロールを付与
- [ ] 各ブランドへのアクセス権限をブランド別に設定
- [ ] `org_database.seed_default_roles()` が実行済みを確認

---

## 本番移行後の初回確認フロー

1. `https://your-domain.com/health` → `{"status":"ok"}`
2. ダッシュボードにログイン
3. ホーム画面の「AI 接続」ステータスが緑であることを確認
4. `https://your-domain.com/audit-logs` で起動ログが記録されていることを確認
5. LINE Bot にメッセージを送ってリードが作成されることを確認
6. Story Autopilot でテスト投稿（`dry_run=True` モード）を実行
7. MEO Control Tower で店舗プロファイルが表示されることを確認

---

## よくあるトラブル

| 症状 | 確認箇所 |
|------|---------|
| ダッシュボードにアクセスできない | `DASHBOARD_PASSWORD` 環境変数の設定 |
| AI 機能がグレーアウト | `ANTHROPIC_API_KEY` の設定 |
| LINE が応答しない | Webhook URL / LINE_CHANNEL_SECRET の確認 |
| Instagram 投稿できない | `INSTAGRAM_ACCESS_TOKEN` の有効期限（60日で失効） |
| GBP データが取得できない | `GOOGLE_REFRESH_TOKEN` の再取得 |
| DB エラー | `data/` ディレクトリの書き込み権限 |
