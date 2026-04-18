# CS ライフサイクルと project フェーズの対応

## ステージ定義（CS）

```
[C1 オンボーディング] → [C2 定常運用] → [C3 成長・拡張] → [C4 更新判断] → [C5 終了・オフボーディング]
```

| CS | 内容 | project-system の目安 |
|----|------|------------------------|
| C1 | キックオフ直後〜初回納品までの立ち上げ | P1〜P2 |
| C2 | 月次運用・定期連絡がルーチン化 | P2〜P4 |
| C3 | 追加発注・スコープ拡大・紹介獲得 | P2〜P4 |
| C4 | 契約更新・単価見直しのタイミング | P4 中心 |
| C5 | 解約・縮小・事業譲渡などの整理 | P5 |

## 月次でやること（最低限）

- `client-health-sheet.yaml` を更新（満足度・レスポンス・未払いの有無）
- 月次レポート提出ブランドは [`project-system` の月次レポート](../../project-system/templates/monthly-report.md) とセットで確認
- 未入金があれば [`finance-system` の請求サイクル](../../finance-system/docs/BILLING_CYCLE.md) に従い、[`project-sheet.yaml`](../../project-system/templates/project-sheet.yaml) の `billing` を更新

## 四半期でやること（推奨）

- 主要アカウントは `qbr-agenda.md` に沿った振り返り（30〜45分）
- 紹介・事例掲載の許諾が取れるかを軽く確認
