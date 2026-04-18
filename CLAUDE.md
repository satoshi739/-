# このリポジトリで Claude Code がやること

## 目的

1. **自動化本体** — `automation-system/`：SNS自動投稿・LINE自動返信・リード起票・フォローアップ・朝のサマリー通知
2. **マーケ** — `marketing-system/`：リール設計・文案・品質ゲート（コンテンツ制作）
3. **店舗更新の自動化** — `shop-update-system/`：お店情報の一元管理と、各チャネルへの反映
4. **営業〜継続** — `sales-system/` → `project-system/` → `finance-system/` → `customer-success-system/`。各 `sales/WHAT_WE_SELL.md` に沿い、過剰約束をしない

## 前提（日本ビジネス）

- 実在マスタの正は `**shop-update-system/shops/`**（日本法人・国内サイト表記）。越境・多言語は各 `profile.yaml` のメモで区別する。
- 店舗更新の文脈説明は `[shop-update-system/README.md](shop-update-system/README.md)` の「ビジネスコンテキスト（日本）」を参照。

## 作業の優先順位

- 仕様とデータの型（YAML/テンプレ）を先に固める → スクリプト・API は後から足す
- 「全部自動」は最終形。v1 は **単一の正（マスタ）** と **更新チェックリスト** までを製品とする

## 触る場所


| 領域              | パス                         |
| --------------- | -------------------------- |
| **自動化（SNS・営業）** | `automation-system/`       |
| マーケ             | `marketing-system/`        |
| 店舗更新            | `shop-update-system/`      |
| 営業              | `sales-system/`            |
| 案件・納品           | `project-system/`          |
| 財務・請求           | `finance-system/`          |
| カスタマーサクセス       | `customer-success-system/` |
| Cursor ルール      | `.cursor/rules/*.mdc`      |


