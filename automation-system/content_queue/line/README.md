# LINE 配信キュー

このフォルダにファイルを入れると、スケジューラーが自動で一斉配信します。

## ファイル形式

```yaml
# テキストのみ
message: |
  こんにちは！DSc Marketing です。

  今週の集客ヒント💡
  〇〇をするだけで問い合わせが増える方法をまとめました。

  詳しくはプロフィールリンクから👆
posted: false
```

```yaml
# 画像付き
image_url: https://example.com/banner.jpg
preview_url: https://example.com/banner_thumb.jpg  # 任意
message: |
  画像の説明やメッセージ本文
posted: false
```
