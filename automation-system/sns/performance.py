from __future__ import annotations

"""
投稿パフォーマンストラッキング
- Instagram インサイトを定期取得してYAMLログに蓄積
- 蓄積データをAI生成時のフィードバックとして活用
- 最適投稿時間の自動算出
"""

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

import yaml

log = logging.getLogger(__name__)

PERF_LOG = Path(__file__).parent.parent / "logs" / "performance_log.yaml"
MAX_ENTRIES = 500  # 保持する最大エントリ数


# ─── 記録 ────────────────────────────────────────────────────

def log_post(
    brand: str,
    platform: str,
    topic: str,
    post_id: str,
    caption: str = "",
    metrics: dict | None = None,
    posted_hour: int | None = None,
) -> dict:
    """
    投稿パフォーマンスを記録する

    Args:
        brand:       "dsc-marketing" / "upjapan" / "cashflowsupport"
        platform:    "instagram" / "tiktok" / "youtube" / "line" etc.
        topic:       投稿のトピック（AI生成時に渡したテーマ）
        post_id:     プラットフォーム側のメディアID
        caption:     投稿キャプション（先頭80文字まで保存）
        metrics:     {"likes": int, "reach": int, "comments": int, "saves": int, "plays": int}
        posted_hour: 投稿した時間（0〜23）

    Returns:
        記録したエントリdict
    """
    PERF_LOG.parent.mkdir(exist_ok=True)
    existing: list[dict] = []
    if PERF_LOG.exists():
        existing = yaml.safe_load(PERF_LOG.read_text(encoding="utf-8")) or []

    metrics = metrics or {}
    likes    = metrics.get("likes", 0)
    reach    = max(metrics.get("reach", 1), 1)
    comments = metrics.get("comments", 0)
    saves    = metrics.get("saves", 0)
    plays    = metrics.get("plays", 0)

    # エンゲージメント率 = (いいね+コメント+保存) / リーチ × 100
    engagement_rate = round((likes + comments + saves) / reach * 100, 2)

    # 動画再生率（リール・Shorts・TikTok用）
    play_rate = round(plays / reach * 100, 1) if plays else 0.0

    entry: dict = {
        "brand":            brand,
        "platform":         platform,
        "topic":            topic,
        "post_id":          post_id,
        "caption_head":     caption[:80],
        "metrics":          metrics,
        "engagement_rate":  engagement_rate,
        "play_rate":        play_rate,
        "posted_hour":      posted_hour if posted_hour is not None else datetime.now().hour,
        "logged_at":        datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    existing.append(entry)
    if len(existing) > MAX_ENTRIES:
        existing = existing[-MAX_ENTRIES:]

    PERF_LOG.write_text(
        yaml.dump(existing, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )
    log.info(f"パフォーマンス記録: {platform}/{brand} topic='{topic[:20]}' eng={engagement_rate}%")
    return entry


def update_metrics(post_id: str, metrics: dict) -> bool:
    """
    既存エントリのメトリクスを更新する（投稿翌日などにインサイトが確定した後に呼ぶ）
    """
    if not PERF_LOG.exists():
        return False
    data = yaml.safe_load(PERF_LOG.read_text(encoding="utf-8")) or []
    updated = False
    for entry in data:
        if entry.get("post_id") == post_id:
            entry["metrics"] = metrics
            likes    = metrics.get("likes", 0)
            reach    = max(metrics.get("reach", 1), 1)
            comments = metrics.get("comments", 0)
            saves    = metrics.get("saves", 0)
            plays    = metrics.get("plays", 0)
            entry["engagement_rate"] = round((likes + comments + saves) / reach * 100, 2)
            entry["play_rate"]       = round(plays / reach * 100, 1) if plays else 0.0
            entry["updated_at"]      = datetime.now().strftime("%Y-%m-%d %H:%M")
            updated = True
            break
    if updated:
        PERF_LOG.write_text(
            yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )
    return updated


# ─── 分析・サマリー ───────────────────────────────────────────

def get_performance_summary(brand: str, platform: str = "instagram", days: int = 30) -> str:
    """
    AI生成プロンプトに埋め込むパフォーマンスサマリーを返す

    Returns:
        サマリー文字列（データがなければ空文字）
    """
    if not PERF_LOG.exists():
        return ""
    try:
        data = yaml.safe_load(PERF_LOG.read_text(encoding="utf-8")) or []
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        filtered = [
            p for p in data
            if p.get("brand") == brand
            and p.get("platform") == platform
            and p.get("logged_at", "") >= cutoff
        ]
        if not filtered:
            return ""

        avg_eng = sum(p.get("engagement_rate", 0) for p in filtered) / len(filtered)
        top3    = sorted(filtered, key=lambda x: x.get("engagement_rate", 0), reverse=True)[:3]
        bot2    = sorted(filtered, key=lambda x: x.get("engagement_rate", 0))[:2]

        lines = [f"【直近{len(filtered)}投稿の傾向 | 平均エンゲージメント率: {avg_eng:.1f}%】"]
        lines.append("▲ 伸びたトピック: " + " / ".join(p.get("topic", "")[:20] for p in top3))
        if bot2 and bot2[0].get("engagement_rate", 0) < avg_eng * 0.5:
            lines.append("▼ 伸びなかったトピック: " + " / ".join(p.get("topic", "")[:20] for p in bot2))
        return "\n".join(lines)
    except Exception as e:
        log.error(f"performance summary error: {e}")
        return ""


def get_top_performing_posts(
    brand: str,
    platform: str = "instagram",
    limit: int = 5,
    days: int = 90,
) -> list[dict]:
    """エンゲージメント上位の投稿一覧を返す"""
    if not PERF_LOG.exists():
        return []
    try:
        data = yaml.safe_load(PERF_LOG.read_text(encoding="utf-8")) or []
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        filtered = [
            p for p in data
            if p.get("brand") == brand
            and p.get("platform") == platform
            and p.get("logged_at", "") >= cutoff
        ]
        return sorted(filtered, key=lambda x: x.get("engagement_rate", 0), reverse=True)[:limit]
    except Exception:
        return []


# ─── 最適投稿時間 ─────────────────────────────────────────────

def get_optimal_post_time(brand: str, platform: str = "instagram") -> str:
    """
    過去パフォーマンスデータから最適な投稿時間帯を算出する。
    データ不足時はプラットフォームのデフォルト値を返す。

    Returns:
        "HH:MM" 形式の文字列
    """
    defaults = {
        "instagram": "12:00",
        "threads":   "12:00",
        "tiktok":    "19:00",
        "youtube":   "17:00",
        "line":      "10:00",
        "facebook":  "12:00",
        "twitter":   "08:00",
    }

    if not PERF_LOG.exists():
        return defaults.get(platform, "12:00")

    try:
        data = yaml.safe_load(PERF_LOG.read_text(encoding="utf-8")) or []
        filtered = [
            p for p in data
            if p.get("brand") == brand
            and p.get("platform") == platform
            and p.get("posted_hour") is not None
        ]
        if len(filtered) < 10:
            return defaults.get(platform, "12:00")

        # 時間帯別の平均エンゲージメント率を集計
        hour_scores: dict[int, list[float]] = {}
        for p in filtered:
            h = p["posted_hour"]
            hour_scores.setdefault(h, []).append(p.get("engagement_rate", 0))

        best_hour = max(hour_scores, key=lambda h: sum(hour_scores[h]) / len(hour_scores[h]))
        return f"{best_hour:02d}:00"

    except Exception as e:
        log.error(f"optimal post time error: {e}")
        return defaults.get(platform, "12:00")


def get_engagement_report(brand: str, days: int = 28) -> dict:
    """
    ダッシュボード用の総合エンゲージメントレポートを返す

    Returns:
        {
          "total_posts": int,
          "avg_engagement_rate": float,
          "best_platform": str,
          "top_topics": [str],
          "by_platform": {platform: {"posts": int, "avg_eng": float}},
        }
    """
    if not PERF_LOG.exists():
        return {"total_posts": 0, "avg_engagement_rate": 0.0, "best_platform": "-", "top_topics": [], "by_platform": {}}

    try:
        data = yaml.safe_load(PERF_LOG.read_text(encoding="utf-8")) or []
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        filtered = [
            p for p in data
            if p.get("brand") == brand and p.get("logged_at", "") >= cutoff
        ]
        if not filtered:
            return {"total_posts": 0, "avg_engagement_rate": 0.0, "best_platform": "-", "top_topics": [], "by_platform": {}}

        by_platform: dict[str, list[float]] = {}
        for p in filtered:
            pl = p.get("platform", "unknown")
            by_platform.setdefault(pl, []).append(p.get("engagement_rate", 0))

        platform_summary = {
            pl: {
                "posts":   len(rates),
                "avg_eng": round(sum(rates) / len(rates), 2),
            }
            for pl, rates in by_platform.items()
        }
        best_platform = max(platform_summary, key=lambda pl: platform_summary[pl]["avg_eng"])

        top_topics = [
            p.get("topic", "")
            for p in sorted(filtered, key=lambda x: x.get("engagement_rate", 0), reverse=True)[:5]
        ]

        overall_avg = round(sum(p.get("engagement_rate", 0) for p in filtered) / len(filtered), 2)

        return {
            "total_posts":          len(filtered),
            "avg_engagement_rate":  overall_avg,
            "best_platform":        best_platform,
            "top_topics":           top_topics,
            "by_platform":          platform_summary,
        }
    except Exception as e:
        log.error(f"engagement report error: {e}")
        return {"total_posts": 0, "avg_engagement_rate": 0.0, "best_platform": "-", "top_topics": [], "by_platform": {}}
