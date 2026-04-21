# AI CEO / AI Agent 構造

## 指揮系統

```
[社長（人間）]
      │  承認・拒否・エスカレーション解決
      ▼
[AI CEO]
  model: claude-sonnet-4-6
  role: ai_ceo
  reports_to: 社長
      │  タスク割り当て・意思決定委任
      ├──────────────────────────────────────────┐
      ▼                                          ▼
[Content Agent]                        [Sales Agent]
  - キャンペーン立案                      - リード追跡
  - アイデア生成                          - フォローアップ
  - 投稿スケジューリング                  - 成約サポート
      │
      ├──────────────────────────────────────────┐
      ▼                                          ▼
[MEO Agent]                           [Analytics Agent]
  - GBP 最適化                           - パフォーマンス分析
  - レビュー返信                          - 異常検知
  - 口コミ監視                           - 戦略メモ生成
```

## AI CEO プロファイル

```python
# org_database.ai_ceo_profiles
{
  "id": "...",
  "user_id": "...",              # users テーブルの AI ユーザー
  "reports_to_user_id": "...",   # 社長のユーザー ID
  "persona": {                   # JSON: ペルソナ設定
    "name": "...",
    "tone": "professional",
    "decision_style": "data-driven"
  },
  "decision_authority": {        # JSON: 意思決定権限
    "budget_limit_jpy": 50000,
    "auto_approve_modes": ["full_auto"],
    "escalate_modes": ["human_approval_required"]
  }
}
```

## タスクモード

| モード | 説明 | 人間の操作 |
|--------|------|-----------|
| `full_auto` | 完全自動実行 | 不要 |
| `semi_auto` | 実行後に結果を通知 | 確認のみ |
| `human_approval_required` | 実行前に承認必須 | 承認/拒否 |

## タスクライフサイクル

```
idle → running → completed
               → failed
               → escalated (human_approval_required)
```

## 承認フロー（Approval）

1. エージェントが `create_approval()` を呼び出す
2. `approval_steps` に承認者（ユーザーID）が登録される
3. ダッシュボードの「Agent Workspace」に承認依頼が表示される
4. 承認者が `decide_approval_step()` で approve / reject
5. 全ステップ完了 → `approvals.status = 'approved'` or `'rejected'`

## エスカレーション

エージェントが自律判断を超える場合に `create_escalation()` を呼ぶ。

```python
create_escalation(
    task_id="...",
    reason="予算超過が見込まれるため人間の判断が必要",
    agent_id="...",
    escalated_to_user_id="...",
    context={"budget_needed": 80000, "budget_limit": 50000}
)
```

## Agent 実行ログ（agent_runs）

各タスク実行は `agent_runs` に記録される:

```
task_id → run_id → status / log / tokens_used / cost_usd
```

## 現在の実装状態

| 機能 | 状態 |
|------|------|
| エージェント登録 (`ai_agents`) | ✅ 実装済み |
| タスク作成・ステータス更新 | ✅ 実装済み |
| 承認フロー UI | ✅ Agent Workspace に実装 |
| エスカレーション UI | ✅ Agent Workspace に実装 |
| Claude API 実呼び出し | ⚠️ `dashboard/ai.py` 経由 (要 API キー) |
| 自動スケジュール実行 | ⚠️ `agents/orchestrator.py` (手動トリガー) |
| コスト追跡 | ⚠️ `agent_runs.cost_usd` (手動入力) |

## 本番接続ポイント

詳細は `docs/PRODUCTION_CHECKLIST.md` を参照。
