# Brand OS — ドキュメントインデックス

## 目次

| ドキュメント | 内容 |
|-------------|------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | システム全体像・レイヤー構成・デプロイ |
| [DATABASE.md](DATABASE.md) | 全テーブル一覧・スキーマ・ロール定義 |
| [AI_CEO_AGENT_STRUCTURE.md](AI_CEO_AGENT_STRUCTURE.md) | AI CEO / Agent 指揮系統・承認フロー |
| [MODULES.md](MODULES.md) | ディレクトリ構成・主要モジュール説明 |
| [ENV_VARS.md](ENV_VARS.md) | 環境変数一覧・.env テンプレート |
| [MOCK_INTEGRATION.md](MOCK_INTEGRATION.md) | モック統合の仕組みと本番切り替え方法 |
| [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md) | 本番運用開始のチェックリスト |

## クイックスタート

```bash
cd automation-system
cp .env.example .env        # 環境変数を設定
pip install -r requirements.txt
python dashboard/app.py     # ブラウザで http://localhost:8080
```

## 最低限の設定

本番運用に最低限必要な環境変数:
- `ANTHROPIC_API_KEY` — AI 機能
- `DASHBOARD_PASSWORD` — ログイン認証
- `FLASK_SECRET_KEY` — セッション暗号化

詳細は [ENV_VARS.md](ENV_VARS.md) を参照。
