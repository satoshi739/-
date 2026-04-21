# モック統合の説明

## 概要

本番 API に接続する前の開発・テスト段階では、各コネクターはモック実装を使用します。
`provider='mock'` フラグで制御されており、**DBには同じ形式でデータが入る**ため、
UI・ロジックの開発は本番接続前から進められます。

## モックが有効な箇所

| モジュール | モッククラス | 説明 |
|------------|-------------|------|
| `connectors/gbp_connector.py` | `MockGBPConnector` | 疑似 GBP データを返す |
| `connectors/meta_connector.py` | `MockMetaConnector` | 疑似 Instagram/Facebook データ |
| `dashboard/mock_service.py` | `MockService` | 各種 API のスタブ集 |
| `repositories/asset_repo.py` | `AITaggerStub` | AI画像タグ付けのスタブ |
| `repositories/story_repo.py` | `seed_mock()` 各所 | Story Autopilot デモデータ |
| `repositories/meo_repo.py` | `sync_from_connector(Mock)` | MEO 初期データ投入 |

## モックデータ投入のタイミング

`startup()` 関数（`dashboard/app.py`）でアプリ起動時に自動投入:

```python
# Asset Brain: DBが空の場合のみ
seed_mock_data()  # repositories/asset_repo.py

# MEO: business_profiles が空の場合のみ
sync_from_connector(MockGBPConnector())

# Org DB: ai_agents が空の場合のみ
seed_org.seed()  # seed_org.py
```

手動で再シードする場合:
```
POST /api/story-autopilot/templates/seed  # Story Autopilot デモデータ
POST /api/orchestrator/seed               # Org DB 再シード
```

## モックデータの見分け方

- `social_accounts.provider = 'mock'`
- `social_posts.provider = 'mock'`
- `story_runs` のログに `"[MOCK]"` プレフィックス

## 本番 API への切り替え方法

各コネクターは `provider` 引数 または 環境変数で切り替え可能:

### GBP（Google Business Profile）

```python
# connectors/gbp_connector.py
# 環境変数 GOOGLE_REFRESH_TOKEN が設定されていれば本番使用
if os.environ.get("GOOGLE_REFRESH_TOKEN"):
    connector = RealGBPConnector(...)
else:
    connector = MockGBPConnector()
```

### Meta（Instagram）

```python
# 環境変数 INSTAGRAM_ACCESS_TOKEN が設定されていれば本番使用
if os.environ.get("INSTAGRAM_ACCESS_TOKEN"):
    connector = RealMetaConnector(...)
else:
    connector = MockMetaConnector()
```

### LINE

```python
# sns/line_api.py
# LINE_CHANNEL_ACCESS_TOKEN が設定されていれば本番 API を呼び出す
```

## 注意事項

- モックデータは **DBに永続化される**。再起動しても消えない。
- 本番切り替え時は既存モックデータを削除するか、`provider='mock'` のレコードを除外するフィルタが必要。
- `social_posts.ig_media_id` がモック時は `MOCK_xxx` 形式になっている。
