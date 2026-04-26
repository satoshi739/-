from __future__ import annotations

"""
メインスケジューラー
- 毎朝 Instagram・LINE に自動投稿
- フォローアップチェックを定期実行
- 毎週月曜6:00 に週次コンテンツカレンダーを自動生成
- 投稿翌日にインサイトを取得してパフォーマンスログに蓄積
- 最適投稿時間を動的に調整（データ蓄積後に有効）

起動方法:
  python scheduler.py

常時起動推奨（Mac の場合 launchd、サーバーの場合 systemd or pm2）
"""

import logging
import os
from pathlib import Path

import schedule
import time
import yaml
from datetime import datetime
from dotenv import load_dotenv

from sns.instagram import InstagramPoster
from sns.line_api import LINEMessenger
from sns.google_drive import sync_from_drive
from sns.performance import log_post, update_metrics, get_optimal_post_time
from sns.photo_importer import process_inbox
from sales.followup import run_followup_check
from morning_operator import run as morning_run

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            Path(__file__).parent / "logs" / "scheduler.log",
            encoding="utf-8",
        ),
    ],
)
logger = logging.getLogger(__name__)

SCHEDULE_CFG  = Path(__file__).parent / "config" / "schedule.yaml"
QUEUE_DIR     = Path(__file__).parent / "content_queue"
SCENARIOS_PATH= Path(__file__).parent / "config" / "line_scenarios.yaml"
PERF_LOG_PATH = Path(__file__).parent / "logs" / "performance_log.yaml"


def _load_schedule() -> dict:
    with open(SCHEDULE_CFG, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _next_queued_post(subdir: str = "instagram") -> dict | None:
    """
    content_queue/instagram/ から次の投稿ファイルを取得
    ファイル名は YYYY-MM-DD_HHmm_[タイトル].yaml で管理
    """
    q_dir = QUEUE_DIR / subdir
    if not q_dir.exists():
        return None
    files = sorted(q_dir.glob("*.yaml"))
    for f in files:
        with open(f, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        if not data.get("posted"):
            return {"path": f, **data}
    return None


def _mark_posted(file_path: Path):
    """投稿済みフラグを立てる"""
    with open(file_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    data["posted"] = True
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def post_to_instagram():
    """Instagram投稿ジョブ（投稿後にパフォーマンスログへ記録）"""
    logger.info("=== Instagram投稿ジョブ開始 ===")
    post = _next_queued_post("instagram")
    if not post:
        logger.info("Instagram: キューに投稿がありません")
        return

    poster = InstagramPoster()
    try:
        media_type = post.get("media_type", "image")
        if media_type == "reel":
            result = poster.post_reel(
                video_url=post["video_url"],
                caption=post["caption"],
                cover_url=post.get("cover_url", ""),
            )
        elif media_type == "carousel":
            result = poster.post_carousel(
                slides=post.get("slides", []),
                caption=post["caption"],
            )
        else:
            result = poster.post_image(
                image_url=post["image_url"],
                caption=post["caption"],
            )

        _mark_posted(post["path"])
        logger.info(f"Instagram投稿完了: {result}")

        # 投稿成功時にパフォーマンスログへ記録（メトリクスは翌日更新）
        media_id = result.get("media_id", "")
        if media_id and result.get("status") == "posted":
            log_post(
                brand=post.get("brand", "dsc-marketing"),
                platform="instagram",
                topic=post.get("topic", post.get("caption", "")[:30]),
                post_id=media_id,
                caption=post.get("caption", ""),
                posted_hour=int(time.strftime("%H")),
            )
            # 次回の投稿時間を最適化（翌日のスケジュールに反映）
            _reschedule_instagram_next_day()

    except Exception as e:
        logger.error(f"Instagram投稿エラー: {e}", exc_info=True)


def fetch_instagram_insights():
    """
    前日投稿のインサイトを取得してパフォーマンスログを更新するジョブ
    毎朝6:00に実行（投稿から24時間後のデータが最も安定）
    """
    logger.info("=== Instagramインサイト取得ジョブ開始 ===")
    if not PERF_LOG_PATH.exists():
        return

    try:
        data = yaml.safe_load(PERF_LOG_PATH.read_text(encoding="utf-8")) or []
    except Exception:
        return

    poster = InstagramPoster()
    updated = 0
    for entry in data:
        if entry.get("platform") != "instagram":
            continue
        if entry.get("metrics", {}).get("reach", 0) > 0:
            continue  # 既にメトリクスあり
        post_id = entry.get("post_id", "")
        if not post_id:
            continue
        try:
            metrics = poster.get_insights_parsed(post_id)
            if metrics.get("reach", 0) > 0:
                update_metrics(post_id, metrics)
                updated += 1
        except Exception as e:
            logger.debug(f"インサイト取得スキップ ({post_id}): {e}")

    logger.info(f"インサイト更新完了: {updated}件")


def _reschedule_instagram_next_day():
    """
    パフォーマンスデータをもとに翌日のInstagram投稿時間を最適化する
    """
    try:
        brand    = os.environ.get("DEFAULT_BRAND", "dsc-marketing")
        opt_time = get_optimal_post_time(brand, "instagram")
        logger.info(f"次回Instagram最適投稿時間: {opt_time}（{brand}）")
        # schedule ライブラリの動的変更は再起動が必要なため、
        # schedule.yaml に書き出してオペレーターに通知
        schedule_path = Path(__file__).parent / "config" / "schedule.yaml"
        if schedule_path.exists():
            cfg = yaml.safe_load(schedule_path.read_text(encoding="utf-8"))
            current_times = cfg.get("instagram", {}).get("post_times", ["12:00"])
            if opt_time not in current_times:
                cfg.setdefault("instagram", {})["suggested_optimal_time"] = opt_time
                schedule_path.write_text(
                    yaml.dump(cfg, allow_unicode=True, default_flow_style=False, sort_keys=False),
                    encoding="utf-8",
                )
                logger.info(f"schedule.yaml に最適時間を記録: {opt_time}")
    except Exception as e:
        logger.debug(f"最適時間の更新スキップ: {e}")


def broadcast_line():
    """LINE一斉配信ジョブ"""
    logger.info("=== LINE一斉配信ジョブ開始 ===")
    post = _next_queued_post("line")
    if not post:
        logger.info("LINE: キューに配信がありません")
        return

    messenger = LINEMessenger()
    try:
        image_url = post.get("image_url", "")
        if image_url:
            ok = messenger.broadcast_with_image(
                message=post["message"],
                image_url=image_url,
                preview_url=post.get("preview_url", image_url),
            )
        else:
            ok = messenger.broadcast(post["message"])

        if ok:
            _mark_posted(post["path"])
            logger.info("LINE一斉配信完了")
    except Exception as e:
        logger.error(f"LINE配信エラー: {e}", exc_info=True)


def check_scheduled_posts():
    """
    予約投稿チェックジョブ（毎分実行）
    scheduled_at が設定されていて現在時刻を過ぎた投稿を自動実行する
    """
    now = datetime.now()
    brands_cfg = Path(__file__).parent / "config" / "brands.yaml"
    try:
        brands = yaml.safe_load(brands_cfg.read_text(encoding="utf-8")).get("brands", {})
    except Exception:
        return

    poster    = InstagramPoster()
    messenger = LINEMessenger()

    # 全ブランド × 全プラットフォームをスキャン
    for brand_key in brands:
        brand_queue = QUEUE_DIR / brand_key
        if not brand_queue.exists():
            continue
        for platform_dir in brand_queue.iterdir():
            if not platform_dir.is_dir():
                continue
            platform = platform_dir.name
            for f in sorted(platform_dir.glob("*.yaml")):
                try:
                    with open(f, encoding="utf-8") as fh:
                        data = yaml.safe_load(fh)
                    if not data or data.get("posted"):
                        continue
                    sched_str = data.get("scheduled_at")
                    if not sched_str:
                        continue
                    sched_dt = datetime.strptime(str(sched_str), "%Y-%m-%d %H:%M")
                    if sched_dt > now:
                        continue  # まだ予約時刻前

                    logger.info(f"予約投稿実行: {brand_key}/{platform}/{f.name} (予約:{sched_str})")

                    if platform == "instagram":
                        mt = data.get("media_type", "image")
                        if mt == "reel":
                            poster.post_reel(video_url=data["video_url"], caption=data.get("caption",""), cover_url=data.get("cover_url",""))
                        elif mt == "carousel":
                            poster.post_carousel(slides=data.get("slides",[]), caption=data.get("caption",""))
                        else:
                            poster.post_image(image_url=data["image_url"], caption=data.get("caption",""))
                        _mark_posted(f)
                        logger.info(f"予約Instagram投稿完了: {f.name}")

                    elif platform == "line":
                        image_url = data.get("image_url","")
                        if image_url:
                            messenger.broadcast_with_image(message=data.get("message",""), image_url=image_url, preview_url=data.get("preview_url", image_url))
                        else:
                            messenger.broadcast(data.get("message",""))
                        _mark_posted(f)
                        logger.info(f"予約LINE配信完了: {f.name}")

                except Exception as e:
                    logger.error(f"予約投稿エラー ({f.name}): {e}", exc_info=True)


def followup_job():
    """フォローアップ送信ジョブ"""
    logger.info("=== フォローアップチェック開始 ===")
    try:
        run_followup_check()
    except Exception as e:
        logger.error(f"フォローアップエラー: {e}", exc_info=True)


def agent_tick_job():
    """エージェントタスク実行ジョブ（5分ごと）"""
    logger.info("=== エージェントタスク実行開始 ===")
    try:
        from agents.orchestrator import tick
        summary = tick(execute=True)
        logger.info(f"エージェントtick完了: {summary}")
    except Exception as e:
        logger.error(f"エージェントtickエラー: {e}", exc_info=True)


def generate_weekly_calendar_job():
    """
    週次コンテンツカレンダー自動生成ジョブ（毎週月曜6:00）
    翌週1週間分のコンテンツ計画をAIが生成してYAMLに保存する
    """
    logger.info("=== 週次コンテンツカレンダー生成開始 ===")
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent / "dashboard"))
        from ai import generate_weekly_calendar, save_weekly_calendar

        brands_cfg = Path(__file__).parent / "config" / "brands.yaml"
        brands = yaml.safe_load(brands_cfg.read_text(encoding="utf-8")).get("brands", {})

        for brand_key in brands:
            try:
                logger.info(f"カレンダー生成中: {brand_key}")
                calendar = generate_weekly_calendar(brand=brand_key)
                saved_path = save_weekly_calendar(calendar, brand=brand_key)
                logger.info(f"カレンダー保存完了: {saved_path}")
            except Exception as e:
                logger.error(f"カレンダー生成エラー ({brand_key}): {e}", exc_info=True)

    except Exception as e:
        logger.error(f"週次カレンダー生成エラー: {e}", exc_info=True)

    logger.info("=== 週次コンテンツカレンダー生成完了 ===")


def setup_schedule():
    cfg = _load_schedule()

    # Instagram（最適投稿時間を反映）
    if cfg.get("instagram", {}).get("enabled"):
        post_times = cfg["instagram"].get("post_times", ["12:00"])
        # suggested_optimal_time があれば採用
        suggested = cfg["instagram"].get("suggested_optimal_time")
        if suggested and suggested not in post_times:
            post_times = [suggested]
            logger.info(f"最適投稿時間を採用: {suggested}")
        for t in post_times:
            schedule.every().day.at(t).do(post_to_instagram)
            logger.info(f"Instagram投稿スケジュール設定: 毎日 {t}")

    # LINE一斉配信
    line_cfg = cfg.get("line_broadcast", {})
    if line_cfg.get("enabled"):
        weekday_map = {
            "monday":    schedule.every().monday,
            "tuesday":   schedule.every().tuesday,
            "wednesday": schedule.every().wednesday,
            "thursday":  schedule.every().thursday,
            "friday":    schedule.every().friday,
            "saturday":  schedule.every().saturday,
            "sunday":    schedule.every().sunday,
        }
        t = line_cfg.get("time", "10:00")
        for day in line_cfg.get("weekdays", ["monday"]):
            weekday_map[day].at(t).do(broadcast_line)
            logger.info(f"LINE配信スケジュール設定: 毎週{day} {t}")

    # フォローアップ（2時間ごとにチェック）
    schedule.every(2).hours.do(followup_job)
    logger.info("フォローアップチェック: 2時間ごと")

    # Googleドライブ同期（1時間ごと: ナノバナナプロで書き出した素材を自動取得）
    schedule.every(1).hours.do(lambda: sync_from_drive())
    logger.info("Google Drive同期: 1時間ごと")

    # 朝のオペレーター（毎朝5:00に全自動処理＋LINEサマリー送信）
    schedule.every().day.at("05:00").do(morning_run)
    logger.info("朝のオペレーター: 毎朝5:00")

    # インサイト取得（毎朝6:00: 前日投稿のデータが確定してから取得）
    schedule.every().day.at("06:00").do(fetch_instagram_insights)
    logger.info("インサイト取得: 毎朝6:00")

    # 週次コンテンツカレンダー生成（毎週月曜6:30）
    schedule.every().monday.at("06:30").do(generate_weekly_calendar_job)
    logger.info("週次カレンダー生成: 毎週月曜6:30")

    # 写真インボックスチェック（1時間ごと）
    # media/inbox/{brand}/ に写真を入れると自動でキューに追加される
    schedule.every(1).hours.do(lambda: process_inbox())
    logger.info("写真インボックスチェック: 1時間ごと")

    # 予約投稿チェック（1分ごと: scheduled_at が設定された投稿を時刻通りに実行）
    schedule.every(1).minutes.do(check_scheduled_posts)
    logger.info("予約投稿チェック: 1分ごと")

    # Story Autopilot（5分ごとにテンプレートの実行時刻をチェック）
    schedule.every(5).minutes.do(story_autopilot_job)
    logger.info("Story Autopilot: 5分ごと")

    # エージェントタスク実行（5分ごと: キュー内タスクを自動実行）
    schedule.every(5).minutes.do(agent_tick_job)
    logger.info("エージェントタスク実行: 5分ごと")


def story_autopilot_job():
    """
    Story Autopilot: アクティブなテンプレートの run_time と active_days を確認し、
    今日・今の時刻に一致するテンプレートを自動実行する。
    """
    now = datetime.now()
    weekday_idx = now.weekday()  # 0=月, 6=日
    current_time = now.strftime("%H:%M")

    try:
        sys_path = str(Path(__file__).parent / "dashboard")
        if sys_path not in __import__("sys").path:
            __import__("sys").path.insert(0, sys_path)

        from repositories.story_repo import StoryTemplateRepo, StoryRunRepo, SocialAccountRepo
        from connectors.meta_connector import get_meta_connector
        import json

        tmpl_repo = StoryTemplateRepo()
        run_repo  = StoryRunRepo()
        acct_repo = SocialAccountRepo()

        templates = tmpl_repo.list()
        triggered = 0

        for tmpl in templates:
            if not tmpl.get("is_active"):
                continue

            # 実行時刻チェック（HH:MM が一致、±2分の許容）
            run_time = tmpl.get("run_time", "09:00")
            try:
                th, tm = map(int, run_time.split(":"))
                nh, nm = now.hour, now.minute
                diff_min = abs((nh * 60 + nm) - (th * 60 + tm))
                if diff_min > 2:
                    continue
            except Exception:
                continue

            # 曜日チェック
            active_days = tmpl.get("active_days")
            if active_days:
                try:
                    days = json.loads(active_days) if isinstance(active_days, str) else active_days
                    if weekday_idx not in days:
                        continue
                except Exception:
                    pass

            # 本日すでに実行済みかチェック
            today_str = now.strftime("%Y-%m-%d")
            existing = run_repo.list(template_id=tmpl["id"])
            if any(r.get("created_at", "")[:10] == today_str for r in existing):
                logger.info(f"Story Autopilot: tmpl={tmpl['id']} は本日実行済みのためスキップ")
                continue

            # 実行
            logger.info(f"Story Autopilot: テンプレート '{tmpl['name']}' を自動実行")
            try:
                acct = next(
                    (a for a in acct_repo.list() if a.get("brand") == tmpl["brand"] and a.get("platform") == "instagram"),
                    None
                )
                run_id = run_repo.create({
                    "template_id":     tmpl["id"],
                    "brand":           tmpl["brand"],
                    "run_mode":        tmpl.get("run_mode", "semi_auto"),
                    "status":          "generating",
                    "social_account_id": acct["id"] if acct else None,
                    "caption":         f"Story Autopilot — {tmpl['name']}",
                    "frames_json":     json.dumps([
                        {"type": "cover", "text": tmpl["name"], "bg": "#6366f1"},
                        {"type": "content", "text": tmpl.get("topic_prompt", ""), "bg": "#111118"},
                        {"type": "cta", "text": "詳しくはプロフィールへ", "bg": "#10b981"},
                    ]),
                })

                run_mode = tmpl.get("run_mode", "semi_auto")
                if run_mode == "full_auto":
                    # 即座に公開
                    run = run_repo.get(run_id)
                    connector = get_meta_connector("auto")
                    ig_uid = acct["ig_user_id"] if acct else tmpl["brand"]
                    result = connector.publish_story(ig_uid, media_url="https://placehold.co/1080x1920/png")
                    if result.get("error"):
                        run_repo.update_status(run_id, "failed", error_message=result["error"])
                    else:
                        run_repo.update_status(
                            run_id, "published",
                            ig_media_id=result.get("ig_media_id", ""),
                            ig_permalink=result.get("permalink", ""),
                        )
                        tmpl_repo.touch_last_run(tmpl["id"])
                    logger.info(f"Story full_auto 公開完了: run_id={run_id}")
                else:
                    # semi_auto / human_approval_required → 承認待ちにする
                    run_repo.update_status(run_id, "pending_approval")
                    tmpl_repo.touch_last_run(tmpl["id"])
                    logger.info(f"Story semi_auto 承認待ち: run_id={run_id}")

                triggered += 1

            except Exception as e:
                logger.error(f"Story Autopilot 実行エラー (tmpl={tmpl['id']}): {e}", exc_info=True)

        if triggered:
            logger.info(f"Story Autopilot: {triggered}件のテンプレートを実行しました")

    except Exception as e:
        logger.error(f"Story Autopilot ジョブエラー: {e}", exc_info=True)


if __name__ == "__main__":
    logger.info("スケジューラー起動")
    (Path(__file__).parent / "logs").mkdir(exist_ok=True)
    setup_schedule()

    # 起動直後に1回実行
    followup_job()

    while True:
        schedule.run_pending()
        time.sleep(60)
