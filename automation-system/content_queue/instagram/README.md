# Instagram 投稿キュー

このフォルダに投稿ファイルを入れると、スケジューラーが自動で投稿します。

## ファイル形式

ファイル名: `YYYY-MM-DD_HHmm_タイトル.yaml`

```yaml
# 画像投稿の例
media_type: image
image_url: https://example.com/image.jpg
caption: |
  キャプション本文をここに書く。

  改行もそのまま使えます。

  #ハッシュタグ #DSCMarketing #集客
posted: false   # 投稿済みなら true になる（自動更新）
```

```yaml
# リール投稿の例
media_type: reel
video_url: https://example.com/video.mp4
cover_url: https://example.com/cover.jpg   # サムネイル（任意）
caption: |
  リールのキャプション

  #リール #マーケティング
posted: false
```

## 注意
- image_url / video_url は **公開アクセス可能なURL** が必要
- ローカルファイルは不可。Google Drive の公開リンク、S3、Cloudflare R2 等を使う
- posted: true のファイルは再投稿されない
