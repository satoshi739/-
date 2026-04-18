# マーケティング自動化システム（プロダクト核）

このフォルダは、**営業がそのまま説明・デモできる品質**を前提にした「中身」の置き場です。  
コードより先に、**何を約束し、何を自動化し、どこで人が触るか**を固定します。

## 読む順番

1. [`docs/PRODUCT_SPEC.md`](docs/PRODUCT_SPEC.md) — 販売する「v1」の範囲と成果物
2. [`docs/QUALITY_BAR.md`](docs/QUALITY_BAR.md) — 出荷前に満たす品質基準
3. [`docs/PIPELINE.md`](docs/PIPELINE.md) — 日次の流れ（ボタン一つに近づける単位）
4. [`sales/WHAT_WE_SELL.md`](sales/WHAT_WE_SELL.md) — 営業が言っていいこと／言わないこと

## テンプレとプロンプト

| 用途 | ファイル |
|------|-----------|
| 1本の設計書（編集・撮影の指示書） | [`templates/reel-brief.md`](templates/reel-brief.md) |
| 日次の運用チェック | [`templates/daily-run.md`](templates/daily-run.md) |
| LLM 用ステップ | [`prompts/`](prompts/) 内を番号順に |

Cursor 上では [`.cursor/rules/marketing-reel-agent.mdc`](../.cursor/rules/marketing-reel-agent.mdc) がマーケ担当の振る舞いを固定します。
