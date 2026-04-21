# データベース概要

## ファイル構成

| ファイル | 用途 |
|---------|------|
| `database.py` | メインDB（リード・投稿・パフォーマンス・MEO・アセット等） |
| `org_database.py` | 組織DBとAIガバナンス（ユーザー・ロール・エージェント・承認） |
| `data/upj.db` | 共有 SQLite ファイル（両モジュールが同じファイルを使用） |

## テーブル一覧 (database.py)

### リード・営業

| テーブル | 説明 |
|---------|------|
| `leads` | リード管理 (L1〜L5 ファネル) |
| `decisions` | 判断待ちキュー（人間判断が必要な案件） |
| `activity_log` | 旧来の操作ログ（後方互換） |

### コンテンツ

| テーブル | 説明 |
|---------|------|
| `queue_items` | 投稿キュー（全SNS共通） |
| `viral_patterns` | NoiMos AI - バイラルパターンライブラリ |
| `viral_pattern_examples` | バイラルパターンの実例 |
| `campaigns` | キャンペーン管理 |
| `content_ideas` | コンテンツアイデア |
| `content_variants` | バリアント（フォーマット別） |
| `publishing_jobs` | 承認・公開ジョブ |
| `prompt_templates` | AI生成用プロンプトテンプレート |

### ストーリー / SNS

| テーブル | 説明 |
|---------|------|
| `social_accounts` | SNS アカウント管理 |
| `story_templates` | Story Autopilot テンプレート |
| `story_runs` | ストーリー生成実行記録 |
| `social_posts` | 公開済み投稿 |
| `social_insights` | 投稿インサイト |

### MEO

| テーブル | 説明 |
|---------|------|
| `business_profiles` | GBP 店舗プロファイル |
| `reviews` | Googleレビュー |
| `review_reply_drafts` | AI返信下書き |
| `business_profile_posts` | GBP 投稿 |
| `business_profile_insights` | 検索/マップ インサイト |

### アセット

| テーブル | 説明 |
|---------|------|
| `assets` | 写真・動画・テンプレート管理 |
| `asset_tags` | タグ定義 |
| `asset_tag_links` | アセット-タグ中間テーブル |
| `asset_usages` | アセット使用履歴 |
| `asset_collections` | アセットコレクション |

### ブログ

| テーブル | 説明 |
|---------|------|
| `blog_projects` | ブログプロジェクト |
| `blog_drafts` | 記事下書き |
| `blog_publish_jobs` | WordPress 公開ジョブ |

### アナリティクス

| テーブル | 説明 |
|---------|------|
| `performance_log` | SNS パフォーマンスログ |
| `daily_briefs` | 日次サマリー |
| `ai_recommendations` | AI 推奨アクション |
| `performance_snapshots` | KPI スナップショット |
| `anomaly_alerts` | 異常検知アラート |
| `strategy_notes` | 戦略メモ（AI CEO 発行） |

### ガバナンス（v2）

| テーブル | 説明 |
|---------|------|
| `audit_logs` | **全操作の監査ログ** |
| `notifications` | **ユーザー通知** |
| `comments` | **エンティティへのコメント** |
| `attachments` | **添付ファイル** |

## テーブル一覧 (org_database.py)

### 組織

| テーブル | 説明 |
|---------|------|
| `organizations` | 組織（会社） |
| `brands` | ブランド（組織に属する） |
| `locations` | 店舗・拠点 |
| `roles` | ロール定義（6種） |
| `users` | ユーザー（人間・AI両方） |
| `user_brand_permissions` | ブランド別権限 |

### AI ガバナンス

| テーブル | 説明 |
|---------|------|
| `ai_ceo_profiles` | AI CEO プロファイル |
| `ai_agents` | AI エージェント登録 |
| `agent_capabilities` | エージェント能力フラグ |
| `agent_assignments` | ブランド割り当て |
| `agent_tasks` | タスク管理 |
| `agent_task_dependencies` | タスク依存関係グラフ |
| `agent_runs` | 実行履歴（トークン・コスト） |
| `escalations` | 人間へのエスカレーション |
| `approvals` | 承認フロー |
| `approval_steps` | 承認ステップ（多段） |

## ロール定義

| slug | レベル | 説明 |
|------|--------|------|
| `owner` | 200 | 全権限 |
| `admin` | 150 | 管理者 |
| `operator` | 100 | 運用担当 |
| `editor` | 70 | 編集者 |
| `reviewer` | 50 | レビュアー |
| `viewer` | 10 | 閲覧のみ |

## 接続方法

```python
# メインDB
import database as db
db.init_db()  # テーブル作成
with db.get_conn() as conn:
    rows = conn.execute("SELECT * FROM leads").fetchall()

# 組織DB
import org_database as obd
obd.init_org_db()
obd.seed_default_roles()  # 6種ロール確保
level = obd.get_user_permission_level(user_id, brand_id)
ok = obd.check_permission(user_id, "operator", brand_id)
```
