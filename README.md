# 会社全体設定

## 自動化の流れ

```
ナノバナナプロ → Googleドライブ → [自動] → Instagram / LINE
LINE問い合わせ → [自動返信・リード起票] → フォローアップ自動送信
毎朝5:00       → [朝のオペレーター]  → LINEでサマリー通知
重要な判断     → decision_queue/ → あなたが決定
```

## システム一覧

| システム | 内容 |
|----------|------|
| [automation-system/](automation-system/) | **SNS自動投稿・LINE自動返信・営業自動化の本体** |
| [marketing-system/](marketing-system/) | リール設計・文案・品質ゲート（コンテンツ制作） |
| [shop-update-system/](shop-update-system/) | 店舗情報マスタと更新の型 |
| [sales-system/](sales-system/) | リード〜商談〜見積〜契約 |
| [project-system/](project-system/) | キックオフ〜納品〜継続の案件管理 |
| [finance-system/](finance-system/) | 請求・入金・月次売上 |
| [customer-success-system/](customer-success-system/) | 定着・更新・解約時の顧客側オペ |

Claude Code / Cursor 共通の目線は [CLAUDE.md](CLAUDE.md)。
