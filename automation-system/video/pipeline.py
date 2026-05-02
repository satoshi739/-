"""
Blog → Reel 自動生成パイプライン

使い方:
    python -m video.pipeline --url https://satoshi-life.site/?p=123
    python -m video.pipeline --script path/to/noimos_script.yaml
    python -m video.pipeline --latest  # WP最新記事を自動取得
    python -m video.pipeline --test    # テスト用ダミーデータで動作確認

フロー:
    1. ブログ取得 または NoimosAI台本ファイル読み込み
    2. Claude APIで台本構造化（NoimosAIファイルがない場合）
    3. シーンごとに Google Veo で映像生成（失敗時はKen Burnsフォールバック）
    4. gTTSで音声生成（完全無料）
    5. ffmpegでテロップ・音声・効果音を合成
    6. TikTok/Instagram Reelsの投稿キューに追加
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# パスを通す
_ROOT = Path(os.environ.get("AUTOMATION_ROOT", "/Users/satoshi/会社全体設定/automation-system"))
sys.path.insert(0, str(_ROOT))

load_dotenv(_ROOT / ".env")

from video.blog_fetcher import BlogFetcher
from video.script_generator import ScriptGenerator
from video.veo_generator import VeoGenerator
from video.tts_generator import TTSGenerator
from video.composer import VideoComposer

_PROJECT_ROOT = Path(os.environ.get("AUTOMATION_ROOT", "/Users/satoshi/会社全体設定/automation-system"))
OUTPUT_DIR = _PROJECT_ROOT / "generated_media" / "reels"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)


def run_pipeline(
    blog_url: str = None,
    blog_text: str = None,
    blog_title: str = None,
    script_file: Path = None,
    brand: str = "satoshi-blog",
    format_key: str = "howto",
    target_key: str = "beginner",
    dry_run: bool = False,
    post: bool = False,
) -> Path:
    """
    パイプライン実行。完成した動画ファイルのパスを返す。

    Args:
        blog_url: WordPress記事URL（blog_textが未指定の場合に使用）
        blog_text: ブログ本文テキスト
        blog_title: ブログタイトル
        script_file: NoimosAI出力YAMLファイルのパス（指定時はStep1-2をスキップ）
        brand: 投稿ブランド名（satoshi-blog, dsc-marketing, etc.）
        dry_run: 動画生成のみ、投稿しない
        post: True なら完成後に投稿キューへ追加

    Returns:
        完成動画ファイルのパス
    """
    log.info("=== Blog → Reel パイプライン 開始 ===")

    # Step 1: 台本取得
    if script_file and Path(script_file).exists():
        log.info(f"[Step 1] NoimosAI台本ファイルを読み込み: {script_file}")
        import yaml
        with open(script_file, encoding="utf-8") as f:
            script = yaml.safe_load(f)
    else:
        # ブログ本文取得
        if blog_url and not blog_text:
            log.info(f"[Step 1] ブログ記事を取得: {blog_url}")
            fetcher = BlogFetcher(brand=brand)
            post_data = fetcher.fetch_by_url(blog_url)
            blog_text = post_data["content"]
            blog_title = blog_title or post_data["title"]

        if not blog_text:
            raise ValueError("blog_url, blog_text, または script_file のいずれかが必要です")

        # Step 2: 台本生成
        log.info(f"[Step 2] 台本を生成中 (format={format_key} target={target_key})...")
        generator = ScriptGenerator()
        script = generator.generate(
            title=blog_title or "",
            body=blog_text,
            format_key=format_key,
            target_key=target_key,
        )

    log.info(f"台本: {len(script.get('scenes', []))} シーン / {script.get('title', '無題')}")

    # Step 3-5: シーンごとに動画生成
    log.info("[Step 3-5] シーン動画を生成中...")
    veo = VeoGenerator()
    tts = TTSGenerator()
    composer = VideoComposer()

    scene_clips = []
    for i, scene in enumerate(script["scenes"]):
        log.info(f"  シーン {i+1}/{len(script['scenes'])}: {scene.get('telop', '')[:20]}")

        # 動画クリップ生成（Veo or フォールバック）
        clip_path = veo.generate(
            prompt=scene.get("visual_prompt", ""),
            telop=scene.get("telop", ""),
            duration=scene.get("duration", 5),
            scene_index=i,
        )

        # TTS音声生成
        narration = scene.get("narration", "")
        audio_path = tts.generate(narration) if narration else None

        scene_clips.append({
            "clip": clip_path,
            "audio": audio_path,
            "telop": scene.get("telop", ""),
            "duration": scene.get("duration", 5),
            "se": scene.get("se", None),
        })

    # Step 6: 最終合成
    log.info("[Step 6] 最終動画を合成中...")
    title_safe = (script.get("title") or "reel").replace("/", "_").replace(" ", "_")[:40]
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = OUTPUT_DIR / f"{timestamp}_{brand}_{title_safe}.mp4"

    final_video = composer.compose(
        scenes=scene_clips,
        output_path=output_path,
        title=script.get("title", ""),
    )

    log.info(f"✓ 完成: {final_video}")

    # Step 7: 投稿キューへ追加
    if post and not dry_run:
        _add_to_queue(final_video, script, brand)

    log.info("=== パイプライン 完了 ===")
    return final_video


def _add_to_queue(video_path: Path, script: dict, brand: str):
    """完成動画を投稿キューに追加"""
    import yaml
    from datetime import datetime

    queue_dir = Path(__file__).parent.parent / "content_queue" / "instagram"
    queue_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    caption = script.get("caption", script.get("title", ""))
    hashtags = " ".join(script.get("hashtags", []))

    entry = {
        "status": "pending",
        "media_type": "REELS",
        "media_path": str(video_path),
        "caption": f"{caption}\n\n{hashtags}".strip(),
        "brand": brand,
        "created_at": timestamp,
    }

    out_file = queue_dir / f"{timestamp}_{brand}_reel.yaml"
    with open(out_file, "w", encoding="utf-8") as f:
        yaml.dump(entry, f, allow_unicode=True)
    log.info(f"投稿キューに追加: {out_file}")


def _test_data():
    return {
        "title": "テスト: 副業で月10万稼ぐ方法",
        "body": "副業で月10万円を稼ぐには、まず自分のスキルを棚卸しすることが重要です。プログラミング、デザイン、ライティングなど、現代では様々なスキルが収益化できます。",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Blog → Reel パイプライン")
    parser.add_argument("--url", help="ブログ記事URL")
    parser.add_argument("--text", help="ブログ本文テキスト")
    parser.add_argument("--title", help="ブログタイトル")
    parser.add_argument("--script", help="NoimosAI台本YAMLファイルのパス")
    parser.add_argument("--latest", action="store_true", help="最新記事を取得")
    parser.add_argument("--brand", default="satoshi-blog", help="ブランド名")
    parser.add_argument("--format", default="howto", help="動画フォーマット: profit_reveal/howto/failure_story/before_after/ranking")
    parser.add_argument("--target", default="beginner", help="ターゲット層: beginner/intermediate/advanced")
    parser.add_argument("--post", action="store_true", help="完成後に投稿キューへ追加")
    parser.add_argument("--dry-run", action="store_true", help="投稿せずに動画だけ生成")
    parser.add_argument("--test", action="store_true", help="テストデータで動作確認")
    args = parser.parse_args()

    fmt = getattr(args, "format", "howto")
    tgt = getattr(args, "target", "beginner")

    if args.test:
        d = _test_data()
        run_pipeline(blog_text=d["body"], blog_title=d["title"], brand=args.brand, format_key=fmt, target_key=tgt, dry_run=True)
    elif args.latest:
        fetcher = BlogFetcher(brand=args.brand)
        latest = fetcher.fetch_latest()
        run_pipeline(blog_text=latest["content"], blog_title=latest["title"], brand=args.brand, format_key=fmt, target_key=tgt, post=args.post)
    elif args.script:
        run_pipeline(script_file=args.script, brand=args.brand, post=args.post, dry_run=args.dry_run)
    else:
        run_pipeline(
            blog_url=args.url,
            blog_text=args.text,
            blog_title=args.title,
            brand=args.brand,
            format_key=fmt,
            target_key=tgt,
            post=args.post,
            dry_run=args.dry_run,
        )
