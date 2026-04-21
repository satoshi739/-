# モジュール説明

## ディレクトリ構成

```
automation-system/
├── dashboard/          # Web UI (Flask)
│   ├── app.py          # メインアプリ・全ルート定義 (~2900行)
│   ├── ai.py           # Claude API ラッパー
│   ├── mock_service.py # モックサービス（外部API代替）
│   └── templates/      # Jinja2 テンプレート (~45ファイル)
├── agents/             # AI エージェント実行エンジン
│   ├── orchestrator.py # タスクスケジューラー・実行制御
│   ├── task_service.py # タスク作成・管理ヘルパー
│   └── assignment_service.py # エージェント割り当てロジック
├── connectors/         # 外部サービス接続
│   ├── gbp_connector.py   # Google Business Profile API
│   └── meta_connector.py  # Meta (Instagram/Facebook) API
├── repositories/       # DB アクセス層
│   ├── org_repo.py     # 組織・ロール・ユーザー
│   ├── ai_repo.py      # AI CEO・エージェント・タスク
│   ├── asset_repo.py   # アセット Brain
│   ├── story_repo.py   # Story Autopilot
│   └── meo_repo.py     # MEO・レビュー
├── models/
│   └── types.py        # TypedDict 型定義（全エンティティ）
├── sns/                # SNS プラットフォーム連携
│   ├── instagram.py    # Instagram Graph API
│   ├── line_api.py     # LINE Messaging API
│   ├── twitter.py      # Twitter/X API
│   ├── tiktok.py       # TikTok API
│   ├── facebook.py     # Facebook API
│   ├── youtube.py      # YouTube Data API
│   ├── threads.py      # Threads API
│   ├── wordpress.py    # WordPress REST API
│   ├── analytics.py    # 横断分析
│   ├── performance.py  # パフォーマンス集計
│   ├── image_generator.py  # 画像生成（DALL-E等）
│   ├── photo_importer.py   # 写真インポート
│   └── google_drive.py     # Google Drive 連携
├── sales/              # 営業自動化
│   ├── lead_intake.py  # リード受付（LINE/フォーム）
│   ├── followup.py     # フォローアップ自動送信
│   └── email_responder.py  # メール自動返信
├── config/             # 設定ファイル
│   ├── brands.yaml     # ブランド定義（色・チャンネル）
│   ├── os_config.yaml  # AI OS 設定（エージェント定義）
│   ├── schedule.yaml   # スケジュール設定
│   ├── line_scenarios.yaml  # LINE シナリオ
│   └── brands/         # ブランド別設定
├── docs/               # ドキュメント（本ディレクトリ）
├── database.py         # メイン DB スキーマ・CRUD
├── org_database.py     # 組織DB・RBAC・AIガバナンス
├── seed_org.py         # 初期データ投入スクリプト
├── data/               # SQLite ファイル・バックアップ
├── logs/               # アプリケーションログ
├── content_queue/      # 投稿待ちコンテンツ (YAML)
├── generated_media/    # AI生成メディア
└── decision_queue/     # 判断待ちYAML (旧来互換)
```

## 主要モジュール詳細

### `dashboard/app.py`

Flask アプリの本体。全ルートを1ファイルに定義（意図的なモノリス設計）。

- **認証**: `require_login()` before_request フック
- **コンテキスト**: `inject_globals()` で全テンプレートにブランド・通知数を注入
- **起動**: `startup()` でDB初期化・シード・YAML移行を実行

主要ルートグループ:
- `/` `/president` `/ceo` — ダッシュボード系
- `/leads/*` — 営業CRM
- `/agents` `/agent-workspace` — AI エージェント管理
- `/campaigns` `/ideas` `/noimos` `/publishing` — コンテンツ企画
- `/meo` `/reviews` — MEO・口コミ管理
- `/assets` `/inbox` — アセット管理
- `/story-autopilot` `/stories` `/reels` — SNS コンテンツ
- `/queue` `/calendar` — 投稿スケジュール
- `/performance` `/analytics` — 分析
- `/notifications` `/audit-logs` `/logs` — ガバナンス・ログ
- `/api/*` — REST API エンドポイント

### `agents/orchestrator.py`

AIエージェントの実行スケジューラー。

```python
tick()        # 1回の実行サイクル（定期呼び出し）
get_overview() # 全エージェント状態サマリー
resolve_escalation() # エスカレーション解決
```

### `repositories/`

DB アクセスを Repository パターンで抽象化。

| クラス | 役割 |
|--------|------|
| `OrganizationRepo` | 組織・ブランド CRUD |
| `AgentRepo` | エージェント登録・更新 |
| `TaskRepo` | タスク作成・依存チェック |
| `RunRepo` | 実行ログ |
| `AssetRepo` | アセット管理 + AI タグ付け stub |
| `StoryRepo` | Story Autopilot 全体 |
| `MeoRepo` | GBP データ sync + MEO スコア計算 |

### `database.py` の主要関数

```python
# 監査ログ
write_audit(action, resource, resource_id, user_name, detail)
list_audit_logs(resource, action, limit, offset)

# 通知
push_notification(title, body, link, type_, priority)
list_notifications(unread_only)
count_unread_notifications()
mark_all_notifications_read()

# コメント
add_comment(resource, resource_id, body, author_name)
list_comments(resource, resource_id)

# 添付ファイル
add_attachment(resource, resource_id, file_name, file_path)
list_attachments(resource, resource_id)
```

### `org_database.py` の権限チェック

```python
seed_default_roles()                       # 6種ロール初期化
check_permission(user_id, "operator", brand_id)  # Bool 返却
get_user_permission_level(user_id, brand_id)     # Int 返却
list_roles()                               # ロール一覧
```
