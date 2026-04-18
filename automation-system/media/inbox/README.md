# 写真インボックス（現実の写真を入れる場所）

## 使い方

1. **ブランドのフォルダに写真・動画をドロップするだけ**

```
media/inbox/
├── dsc-marketing/    ← DSc Marketing の写真
├── upjapan/          ← UPJ の写真
└── cashflowsupport/  ← CashflowSupport の写真
```

2. **1時間以内に自動で処理される**
   - AIがキャプション＋ハッシュタグを自動生成
   - Google Drive にアップロード（公開URL取得）
   - `content_queue/instagram/` に投稿ファイルが追加される
   - 翌朝の投稿ジョブで自動投稿

## ファイル命名のコツ

ファイル名にヒントを入れると、AIがより適切なキャプションを生成します。

| ファイル名の例 | AIが生成するキャプション |
|---|---|
| `IMG_1234.jpg` | ブランドのデフォルトトーンで生成 |
| `セミナー_集合写真.jpg` | セミナー・イベント系のキャプション |
| `新オフィス_内装.jpg` | オフィス・会社紹介系のキャプション |
| `reel_SNS活用事例.mp4` | リール動画として処理（`reel_` プレフィックスで判定） |

## 処理後

- 処理済みの写真は `media/processed/{brand}/` に移動されます
- `content_queue/instagram/` のYAMLを開いてキャプションを確認・編集できます
- `posted: false` → 未投稿、`posted: true` → 投稿済み
