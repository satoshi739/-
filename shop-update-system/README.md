# 店舗更新自動化システム

「今あるお店」の情報を **1か所で更新**し、各チャネルへ反映するための設計置き場です。  
Claude Code では、まず **マスタデータの型** と **更新パイプライン** を実装し、API 連携はチャネルごとにモジュール化します。

## ビジネスコンテキスト（日本）

いま取り込んでいるマスタは **日本の法人・国内向けサイト** を前提にしています（住所・電話・受付時間・表記ゆれの注意書きなど）。  
実データの例は [`shops/`](shops/)（例：`upjapan-co-jp`、`dsc-marketing`、`cashflowsupport-jp`）。タイ向け・越境表記がある案件は `profile.yaml` の `regions_note` や `compliance_note` で明示する。

## 読む順番

1. [`docs/PRODUCT_SPEC.md`](docs/PRODUCT_SPEC.md) — v1 で売る範囲
2. [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) — 店舗マスタの項目
3. [`docs/PIPELINE.md`](docs/PIPELINE.md) — 更新の流れ
4. [`docs/INTEGRATIONS.md`](docs/INTEGRATIONS.md) — チャネル別（手動/API/将来）

## テンプレ

- [`templates/shop-profile.schema.yaml`](templates/shop-profile.schema.yaml) — 1店舗のマスタ例
- [`templates/update-run-checklist.md`](templates/update-run-checklist.md) — 更新作業のチェックリスト

## 営業

- [`sales/WHAT_WE_SELL.md`](sales/WHAT_WE_SELL.md)

## Cursor

`shop-update-system/**` 編集時は [`.cursor/rules/shop-update-agent.mdc`](../.cursor/rules/shop-update-agent.mdc) を参照。
