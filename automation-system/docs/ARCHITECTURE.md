# アーキテクチャ概要

## システム全体像

```
┌─────────────────────────────────────────────────────────┐
│                   Brand OS Dashboard                    │
│              Flask (Python) + Jinja2                    │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP / REST
          ┌────────────┼────────────────┐
          ▼            ▼                ▼
  ┌──────────┐  ┌──────────────┐  ┌─────────────┐
  │  SQLite  │  │ Claude API   │  │  External   │
  │  DB      │  │ (Anthropic)  │  │  (LINE/GBP/ │
  │  upj.db  │  │              │  │  Meta等)    │
  └──────────┘  └──────────────┘  └─────────────┘
```

## レイヤー構成

| レイヤー        | 場所                        | 役割 |
|-------------|---------------------------|------|
| **Web/UI**  | `dashboard/app.py` + `templates/` | Flask ルーティング・Jinja2 テンプレート |
| **Service** | `repositories/`           | ビジネスロジック・DB アクセス |
| **DB**      | `database.py` / `org_database.py` | SQLite スキーマ定義・CRUD |
| **Models**  | `models/types.py`         | TypedDict 型定義 |
| **Agents**  | `agents/`                 | AI エージェント実行エンジン |
| **Connectors** | `connectors/`          | 外部サービス接続（GBP・Meta） |
| **SNS**     | `sns/`                    | 各 SNS プラットフォーム連携 |
| **Config**  | `config/`                 | YAML 設定ファイル |

## データフロー

```
[外部入力]
  LINE Bot webhook → sales/lead_intake.py → leads テーブル
  Meta API        → sns/instagram.py     → social_posts テーブル
  GBP API         → connectors/gbp_connector.py → business_profiles テーブル

[AI処理]
  Agent Task → agents/orchestrator.py → Claude API → output_data

[出力]
  publishing_jobs → SNS投稿 / LINE配信 / WordPress 記事
  notifications   → ダッシュボード通知
  audit_logs      → 監査証跡
```

## デプロイ構成

- **ローカル開発**: `python dashboard/app.py` (ポート 8080)
- **本番(Railway)**: `gunicorn dashboard.app:app` (Procfile / railway.toml)
- **DB**: 単一 SQLite ファイル (`data/upj.db`)
- **バックアップ**: `database.backup_db()` / `data/backups/`

## セキュリティ

- 認証: セッション + `DASHBOARD_PASSWORD` 環境変数
- RBAC: `org_database.check_permission()` でロールレベル検証
- 監査: `database.write_audit()` で全操作を記録
- 外部 API キーは `.env` ファイル / Railway 環境変数で管理

## 今後の拡張ポイント

- SQLite → PostgreSQL (本番スケール時)
- セッション認証 → JWT / OAuth (マルチユーザー時)
- Claude API → 他モデルへの切り替え対応
- Railway → Kubernetes (大規模運用時)
