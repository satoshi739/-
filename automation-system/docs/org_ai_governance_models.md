# 組織・AIガバナンス モデル仕様

## 概要

`automation-system/org_database.py` が管理する2グループのテーブル定義です。
型定義は `models/types.py`、リポジトリ骨格は `repositories/` 以下にあります。

---

## organization グループ

### organizations
会社・グループ全体の単位。

| カラム | 型 | 説明 |
|---|---|---|
| id | TEXT PK | UUID |
| name | TEXT | 正式名称 |
| slug | TEXT UNIQUE | 識別キー（例: `upj-group`） |
| description | TEXT | 説明 |

### brands
組織が持つブランド（SNS・サービス単位）。

| カラム | 型 | 説明 |
|---|---|---|
| id | TEXT PK | UUID |
| organization_id | TEXT FK | 所属組織 |
| name | TEXT | ブランド名 |
| slug | TEXT UNIQUE | 識別キー（例: `upj`, `dsc`） |
| short_name | TEXT | 略称 |
| color | TEXT | テーマカラー |
| url | TEXT | 公式URL |

**シードブランド:** UPJ / DSC / CFJ(CSF) / Bangkok Peach Group / Satoshi Life Blog

### locations
ブランドの拠点（店舗・事業所）。

| カラム | 型 | 説明 |
|---|---|---|
| id | TEXT PK | UUID |
| brand_id | TEXT FK | 所属ブランド |
| country | TEXT | 国コード（デフォルト: JP） |
| timezone | TEXT | タイムゾーン |

### roles
ロール定義。`level` で権限の強さを表す。

| slug | level | 説明 |
|---|---|---|
| human_president | 200 | 最終意思決定者 |
| ai_ceo | 100 | AI組織の最高執行責任者 |
| manager | 50 | 人間マネージャー |
| ai_agent | 10 | 専門AIエージェント |
| member | 5 | 一般メンバー |

### users
人間とAI両方を統一的に表現するユーザーテーブル。

| カラム | 型 | 説明 |
|---|---|---|
| id | TEXT PK | UUID |
| user_type | TEXT | `human` または `ai` |
| role_id | TEXT FK | ロール |

### user_brand_permissions
ユーザーがどのブランドにどの権限を持つか。

| カラム | 型 | 説明 |
|---|---|---|
| permission_level | TEXT | `read` / `write` / `admin` |

---

## ai_governance グループ

### ai_ceo_profiles
AI CEOの設定プロファイル。Human Presidentへのレポートラインを持つ。

| カラム | 型 | 説明 |
|---|---|---|
| reports_to_user_id | TEXT FK | Human President の user_id |
| persona | TEXT JSON | 性格・コミュニケーションスタイル |
| decision_authority | TEXT JSON | 自律判断の範囲と上限 |

### ai_agents
個々のAIエージェント設定。

| カラム | 型 | 説明 |
|---|---|---|
| agent_type | TEXT | エージェント種別 |
| reports_to_id | TEXT FK | AI CEO の user_id |
| model | TEXT | 使用モデル（デフォルト: claude-sonnet-4-6） |
| system_prompt | TEXT | システムプロンプト |

**シードエージェント（12体）:**
- Chief of Staff / NoiMos / Story Autopilot
- MEO / Reputation / Asset Brain
- Blog Growth / Campaign / Analytics
- Automation Runner / Approval & Compliance / Growth Lab

### agent_capabilities
各エージェントが持つ能力の一覧。

### agent_assignments
エージェントとブランドの対応付け。

### agent_tasks
AIが実行するタスクの中心テーブル。

#### mode（実行モード）
| 値 | 説明 |
|---|---|
| `full_auto` | 人間の介入なく自動実行 |
| `semi_auto` | 実行はAIだが結果は通知 |
| `human_approval_required` | 実行前に人間の承認必須 |

#### status（タスクステータス）
| 値 | 説明 |
|---|---|
| `idle` | 未着手 |
| `queued` | 実行待ちキュー |
| `running` | 実行中 |
| `blocked` | 依存タスク未完了 |
| `waiting_approval` | 承認待ち |
| `completed` | 正常完了 |
| `failed` | 失敗 |
| `escalated` | エスカレーション中 |

### agent_task_dependencies
タスク間の依存関係。DAG（有向非巡回グラフ）構造。

| dependency_type | 説明 |
|---|---|
| `finish_to_start` | 先行完了後に後続開始（デフォルト） |
| `start_to_start` | 先行開始後に後続開始可 |
| `finish_to_finish` | 先行完了と同時に後続完了 |

### agent_runs
タスクの実行ログ。1タスクに複数回のrunが可能（リトライ対応）。

### escalations
エージェントがHuman/CEOへエスカレーションした記録。

### approvals + approval_steps
多段階承認フロー。`approval_steps` で複数の承認者を順番に管理。

---

## ファイル構成

```
automation-system/
├── org_database.py          # スキーマ定義・低レベルCRUD
├── seed_org.py              # 初期データ投入（冪等）
├── models/
│   ├── __init__.py
│   └── types.py             # TypedDict型定義
└── repositories/
    ├── __init__.py
    ├── org_repo.py          # OrganizationRepo / RoleRepo
    └── ai_repo.py           # AiCeoRepo / AgentRepo / TaskRepo / RunRepo / EscalationRepo / ApprovalRepo
```

## 使い方

```python
# スキーマ初期化
import org_database as db
db.init_org_db()

# タスク作成
from repositories.ai_repo import TaskRepo
repo = TaskRepo()
tid = repo.create(
    title="UPJ Instagram投稿生成",
    mode="semi_auto",
    assigned_to_agent_id="<noimos_agent_id>",
    brand_id="<upj_brand_id>",
    input_data={"week": "2026-W17"},
)

# ステータス更新
repo.update_status(tid, "running")
repo.update_status(tid, "completed", output_data={"posts_created": 5})
```

## 再シード

```bash
cd automation-system
python3 seed_org.py
```
冪等なので何度実行しても安全。
