# 財務・請求管理システム（Finance System）

UPJグループの**請求・入金・月次売上**を一元管理する。

## 読む順番

1. [`docs/BILLING_CYCLE.md`](docs/BILLING_CYCLE.md) — 請求〜入金のサイクル
2. [`docs/REVENUE_TRACKING.md`](docs/REVENUE_TRACKING.md) — 売上の記録と見方
3. [`templates/invoice-template.md`](templates/invoice-template.md) — 請求書のひな型
4. [`templates/monthly-finance-log.yaml`](templates/monthly-finance-log.yaml) — 月次売上記録テンプレ

## 請求ルール

- **締め日：** 毎月末日
- **支払い期日：** 翌月末（月末締め翌月末払いが基本）
- **支払い方法：** 銀行振込（三菱UFJ等）/ 口座振替は個別合意
- **消費税：** 全て税込表示・税込請求
- **請求書発行ツール：** freee / マネーフォワード（要確認）

## ブランド別の請求元

全ブランドの法人名は「株式会社ユニバースプラネットジャパン」で統一。
