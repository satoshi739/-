# UPJ Autonomous Brand OS — UI・メニュー設計書

最終更新: 2026-04-21

---

## 1. コンセプト

**「機能一覧」から「仕事の流れ」へ**

以前のダッシュボードは機能リスト型（設定が多く何から触ればいいかわからない）でした。
新設計は「役割」「判断のしやすさ」「仕事の流れ」を軸に整理しています。

> 社長が3秒で状況把握できる。AI CEOが5秒で優先順位を判断できる。

---

## 2. 色の意味（全画面統一）

| 色 | CSS変数 | 意味 | 使用場面 |
|---|---|---|---|
| 🔴 赤 | `--c-urgent` `#ef4444` | 緊急 / エラー | 未対応の判断待ち・エラー |
| 🟡 黄 | `--c-warn` `#f59e0b` | 要確認 / 警告 | 素材不足・期限近い |
| 🔵 青 | `--c-active` `#6366f1` | 進行中 / アクティブ | 実行中タスク・キュー待ち |
| 🟢 緑 | `--c-ok` `#10b981` | 正常 / 完了 | 公開済み・承認済み・稼働中 |
| 🟣 紫 | `--c-ai` `#8b5cf6` | AI提案 / 自動 | Story Autopilot・AI生成結果 |

---

## 3. 左サイドバー構成

ロゴ: **Brand OS** / AUTONOMOUS · UPJ GROUP

### 上段：毎日使う

| セクション | 役割 | 主なリンク |
|---|---|---|
| 🎯 **司令室** | 最高優先度の意思決定 | 社長 Dashboard / AI CEO / ホーム / 判断待ち |
| 🏷 **ブランド運営** | ブランド別の運転席 | UPJ / DSC / CFJ / BPG / Blog |
| 🤖 **AI組織** | エージェント制御 | Agent ステータス (LIVE) / Agent Workspace |
| ✦ **コンテンツ企画** | 企画起点の媒体展開 | Campaign Pipeline / アイデア / NoiMos AI / 承認キュー |

### 中段：実務

| セクション | 役割 | 主なリンク |
|---|---|---|
| 🖼 **素材ライブラリ** | アセット管理 | Asset Brain / インボックス |
| 📍 **MEO / 口コミ** | Google Business 管理 | MEO Control Tower / Review Center / AI 返信下書き / 低評価 |
| 📱 **ストーリー / SNS** | 投稿・自動配信 | Story Autopilot / ストーリー作成 / リール / 投稿キュー / カレンダー |
| ✒ **ブログ** | ブログ運営 | AI 記事生成 / 週次カレンダー / パフォーマンス / アナリティクス |

### 下段：管理

| セクション | 役割 | 主なリンク |
|---|---|---|
| ⚖ **承認・ログ** | 詰まり可視化 | 営業 Kanban / リード一覧 / 実行ログ |
| ⚙ **設定** | ブランド設定 | 各ブランドの設定ページ |

---

## 4. 各画面の設計原則

### 4.1 1画面1目的

各画面は1つの目的だけを持ちます。
- `/president` → 社長が会社全体を俯瞰して判断する
- `/ceo` → AI CEOが全ブランドを管理・優先順位付けする
- `/agents` → AI組織の稼働状況を確認する
- `/story-autopilot` → ストーリー自動化を管理する

### 4.2 最上段は「次に何をすべきか」

どの画面も最初に見える部分に:
- 現在の状態サマリー
- 次にすべきアクション
- アクションボタン

を配置します。

### 4.3 空状態には必ずCTA

データがゼロの時も「何をすればこの画面を活用できるか」を明示します。
- ❌ 「データがありません」で終わらせない
- ✅ 「〇〇から追加できます」+ ボタンを置く

---

## 5. 主要画面設計

### ホーム (/)
**役割**: 司令室 — 今日の最優先事項を3秒で把握

```
[優先アクション（赤: 未対応判断待ち / 黄: 素材不足 / 緑: 正常）]
[AI OS バナー: President → CEO → Agents]
[ブランドビルカード × 5]
[KPI 6枚グリッド]
[月別チャート + 営業ファネル]
[直近リード + 判断待ちリスト]
```

### 社長 Dashboard (/president)
**役割**: 承認・アラート・全体状況の最終確認

```
[朝ブリーフ]
[優先アクション（要対応のみ）]
[危険アラート（赤 / 黄 / 緑）]
[ブランド別状況]
[AI Agent 稼働状況]
[直近の自動実行結果]
```

### AI CEO (/ceo)
**役割**: 実行優先順位の管理

```
[朝ブリーフ]
[ボトルネック・エスカレーション]
[ブランド別状況]
[タスクキュー]
[承認待ち]
```

### AI組織 (/agents)
**役割**: 全エージェントの稼働状況と制御

```
[統計: 総数 / Online / 累計実行 / エラー数]
[組織図: President → AI CEO → Agents]
[Agent カード × 12体（状態・最終実行・担当ブランド）]
[空状態: 設定ガイド + CTA]
```

### Story Autopilot (/story-autopilot)
**役割**: ストーリーの自動化管理

```
[統計: 承認待ち / 公開済み / テンプレート数]
[テンプレート一覧（曜日ルール・実行モード）]
[最近の実行（承認待ちはインライン承認可能）]
[ブランド別インサイト]
```

### 承認・ログ (/decisions)
**役割**: AI が判断できなかった案件の処理

```
[統計サマリー: 未対応 / 対応済み]
[未対応（赤ボーダー、インライン対応フォーム）]
[対応済み履歴（コンパクトリスト）]
[空状態: 全て対応済み + 次のアクション CTA]
```

---

## 6. コンポーネント規則

### カード

```html
<div class="card">
  <div class="card-title">タイトル</div>
  <!-- コンテンツ -->
</div>
```

### ステータスバッジ

```html
<!-- 緊急 -->
<span style="background:rgba(239,68,68,.15);color:var(--red);border:1px solid rgba(239,68,68,.3);padding:2px 8px;border-radius:20px;">緊急</span>

<!-- AI提案 -->
<span style="background:rgba(139,92,246,.15);color:var(--purple2);border:1px solid rgba(139,92,246,.3);padding:2px 8px;border-radius:20px;">AI提案</span>
```

### 空状態テンプレート

```html
<div style="text-align:center;padding:56px 20px;background:var(--s1);border:1px dashed var(--border);border-radius:16px;">
  <div style="font-size:52px;margin-bottom:14px;">📭</div>
  <div style="font-size:16px;font-weight:700;margin-bottom:8px;">タイトル</div>
  <div style="font-size:13px;color:var(--muted2);margin-bottom:20px;line-height:1.6;">説明文</div>
  <div style="display:flex;gap:10px;justify-content:center;flex-wrap:wrap;">
    <a href="/path" class="btn btn-accent btn-sm">プライマリCTA</a>
    <a href="/path" class="btn btn-ghost btn-sm">セカンダリCTA</a>
  </div>
</div>
```

---

## 7. 対象ブランド一覧

| slug | 表示名 | 略称 | カラー |
|---|---|---|---|
| `upjapan` | UP JAPAN | UPJ | #6366f1 |
| `dsc-marketing` | DSc Marketing | DSC | #10b981 |
| `cashflowsupport` | Cash Flow Support | CFJ / CSF | #f59e0b |
| `bangkok-peach` | Bangkok Peach Group | BPG | #f472b6 |
| `satoshi-blog` | Satoshi Life Blog | Blog | #a78bfa |

> `CSF` 表記は後方互換のため維持（コード内 `cashflowsupport` スラッグで統一）

---

## 8. 組織構造

```
👤 Human President (Satoshi) — 最終意思決定
    │
    └── 🤖 AI CEO — 全ブランド統括・優先順位管理
            │
            ├── Chief of Staff
            ├── NoiMos AI
            ├── Story Autopilot
            ├── MEO Agent
            ├── Reputation Agent
            ├── Asset Brain Agent
            ├── Blog Growth Agent
            ├── Campaign Agent
            ├── Analytics Agent
            ├── Automation Runner
            ├── Approval & Compliance
            └── Growth Lab
```

---

## 9. 今後のUI改善ロードマップ

| 優先度 | 改善項目 | 対象画面 |
|---|---|---|
| 高 | ブランド別サマリーカードの充実（投稿数・MEOスコア・口コミ数） | `/brands/:id` |
| 高 | モバイル対応（サイドバーをハンバーガー化） | `base.html` |
| 中 | Story Autopilot フレームプレビューをダッシュボードに埋め込み | `/story-autopilot` |
| 中 | リアルタイム通知バー（新規判断待ち・エラー） | `base.html` |
| 低 | ダークモード切替（ライトテーマ追加） | `base.html` |
| 低 | キーボードショートカット一覧 (`?` キー) | 全画面 |
