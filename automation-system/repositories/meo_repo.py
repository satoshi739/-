"""
MEO Repository
==============
business_profiles / reviews / review_reply_drafts /
business_profile_posts / business_profile_insights の CRUD。
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import database as db


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ════════════════════════════════════════════════
# BUSINESS PROFILES
# ════════════════════════════════════════════════

def upsert_profile(data: dict) -> str:
    now = _now()
    gbp_loc_id = data.get("gbp_location_id")

    # 既存レコードを gbp_location_id で検索（あれば id を使い回す）
    existing_id = None
    if gbp_loc_id:
        with db.get_conn() as conn:
            row = conn.execute(
                "SELECT id FROM business_profiles WHERE gbp_location_id=?", (gbp_loc_id,)
            ).fetchone()
        if row:
            existing_id = row["id"]

    pid = existing_id or data.get("id") or str(uuid.uuid4())[:8]
    with db.get_conn() as conn:
        conn.execute("""
            INSERT INTO business_profiles
                (id, brand, location_name, address, city, phone, website,
                 gbp_location_id, avg_rating, total_reviews, unanswered_reviews,
                 photos_count, photo_alert, last_synced_at, meo_score, status,
                 created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET
                brand=excluded.brand,
                location_name=excluded.location_name,
                address=excluded.address,
                city=excluded.city,
                phone=excluded.phone,
                website=excluded.website,
                gbp_location_id=excluded.gbp_location_id,
                avg_rating=excluded.avg_rating,
                total_reviews=excluded.total_reviews,
                unanswered_reviews=excluded.unanswered_reviews,
                photos_count=excluded.photos_count,
                photo_alert=excluded.photo_alert,
                last_synced_at=excluded.last_synced_at,
                meo_score=excluded.meo_score,
                status=excluded.status,
                updated_at=excluded.updated_at
        """, (
            pid, data.get("brand"), data.get("location_name"),
            data.get("address"), data.get("city"), data.get("phone"),
            data.get("website"), gbp_loc_id,
            data.get("avg_rating", 0), data.get("total_reviews", 0),
            data.get("unanswered_reviews", 0), data.get("photos_count", 0),
            data.get("photo_alert", 0), data.get("last_synced_at"),
            data.get("meo_score", 0), data.get("status", "active"),
            data.get("created_at", now), now,
        ))
    return pid


def get_profile(profile_id: str) -> dict | None:
    with db.get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM business_profiles WHERE id=?", (profile_id,)
        ).fetchone()
    return dict(row) if row else None


def list_profiles(brand: str = "") -> list[dict]:
    sql = "SELECT * FROM business_profiles WHERE status='active'"
    params: list = []
    if brand:
        sql += " AND brand=?"; params.append(brand)
    sql += " ORDER BY meo_score DESC"
    with db.get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def compute_meo_score(profile: dict, unanswered_count: int) -> int:
    """MEOスコアを 0–100 で算出する。"""
    score = 0
    # 評価点 (40点満点)
    avg = profile.get("avg_rating", 0) or 0
    score += int(avg / 5.0 * 40)
    # レビュー数 (20点満点、50件で満点)
    total = profile.get("total_reviews", 0) or 0
    score += min(int(total / 50 * 20), 20)
    # 写真数 (20点満点、10枚で満点)
    photos = profile.get("photos_count", 0) or 0
    score += min(int(photos / 10 * 20), 20)
    # インサイトアクション (20点満点)
    score += 15  # デフォルトで基礎点
    # 未返信ペナルティ (-5点/件、最大-20点)
    score -= min(unanswered_count * 5, 20)
    return max(0, min(100, score))


# ════════════════════════════════════════════════
# REVIEWS
# ════════════════════════════════════════════════

def upsert_review(profile_id: str, data: dict) -> str:
    rid = data.get("id") or str(uuid.uuid4())[:12]
    now = _now()
    with db.get_conn() as conn:
        conn.execute("""
            INSERT INTO reviews
                (id, profile_id, gbp_review_id, reviewer_name, reviewer_photo_url,
                 rating, comment, reply, reply_updated_at, status, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(gbp_review_id) DO UPDATE SET
                reviewer_name=excluded.reviewer_name,
                rating=excluded.rating,
                comment=excluded.comment,
                reply=excluded.reply,
                reply_updated_at=excluded.reply_updated_at,
                status=excluded.status,
                updated_at=excluded.updated_at
        """, (
            rid, profile_id, data.get("gbp_review_id"),
            data.get("reviewer_name"), data.get("reviewer_photo_url"),
            data.get("rating"), data.get("comment"),
            data.get("reply"), data.get("reply_updated_at"),
            data.get("status", "unanswered"),
            data.get("created_at", now), now,
        ))
    with db.get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM reviews WHERE gbp_review_id=?",
            (data.get("gbp_review_id"),)
        ).fetchone()
    return row["id"] if row else rid


def get_review(review_id: str) -> dict | None:
    with db.get_conn() as conn:
        row = conn.execute("SELECT * FROM reviews WHERE id=?", (review_id,)).fetchone()
    return dict(row) if row else None


def list_reviews(profile_id: str = "", status: str = "",
                 max_rating: int = 0, limit: int = 200) -> list[dict]:
    sql = "SELECT r.*, bp.location_name FROM reviews r JOIN business_profiles bp ON r.profile_id=bp.id WHERE 1=1"
    params: list = []
    if profile_id:
        sql += " AND r.profile_id=?"; params.append(profile_id)
    if status:
        sql += " AND r.status=?"; params.append(status)
    if max_rating:
        sql += " AND r.rating<=?"; params.append(max_rating)
    sql += " ORDER BY r.created_at DESC LIMIT ?"
    params.append(limit)
    with db.get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def set_review_replied(review_id: str, reply_text: str):
    now = _now()
    with db.get_conn() as conn:
        conn.execute("""
            UPDATE reviews SET reply=?, reply_updated_at=?, status='answered', updated_at=?
            WHERE id=?
        """, (reply_text, now, now, review_id))


def count_unanswered(profile_id: str = "") -> int:
    sql = "SELECT COUNT(*) FROM reviews WHERE status='unanswered'"
    params: list = []
    if profile_id:
        sql += " AND profile_id=?"; params.append(profile_id)
    with db.get_conn() as conn:
        return conn.execute(sql, params).fetchone()[0]


def count_low_rating(profile_id: str = "", threshold: int = 2) -> int:
    sql = "SELECT COUNT(*) FROM reviews WHERE rating<=?"
    params: list = [threshold]
    if profile_id:
        sql += " AND profile_id=?"; params.append(profile_id)
    with db.get_conn() as conn:
        return conn.execute(sql, params).fetchone()[0]


# ════════════════════════════════════════════════
# REVIEW REPLY DRAFTS
# ════════════════════════════════════════════════

def add_draft(review_id: str, draft_text: str, source: str = "ai") -> int:
    now = _now()
    with db.get_conn() as conn:
        cur = conn.execute("""
            INSERT INTO review_reply_drafts (review_id, draft_text, source, created_at, updated_at)
            VALUES (?,?,?,?,?)
        """, (review_id, draft_text, source, now, now))
    return cur.lastrowid


def get_drafts(review_id: str) -> list[dict]:
    with db.get_conn() as conn:
        rows = conn.execute("""
            SELECT d.*, r.comment, r.rating, r.reviewer_name, r.profile_id,
                   bp.location_name
            FROM review_reply_drafts d
            JOIN reviews r ON d.review_id = r.id
            JOIN business_profiles bp ON r.profile_id = bp.id
            WHERE d.review_id=?
            ORDER BY d.created_at DESC
        """, (review_id,)).fetchall()
    return [dict(r) for r in rows]


def list_pending_drafts(limit: int = 50) -> list[dict]:
    with db.get_conn() as conn:
        rows = conn.execute("""
            SELECT d.*, r.comment, r.rating, r.reviewer_name, r.profile_id,
                   bp.location_name
            FROM review_reply_drafts d
            JOIN reviews r ON d.review_id = r.id
            JOIN business_profiles bp ON r.profile_id = bp.id
            WHERE d.approved=0 AND d.sent=0
            ORDER BY d.created_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
    return [dict(r) for r in rows]


def approve_draft(draft_id: int):
    now = _now()
    with db.get_conn() as conn:
        conn.execute(
            "UPDATE review_reply_drafts SET approved=1, updated_at=? WHERE id=?",
            (now, draft_id)
        )


def mark_draft_sent(draft_id: int):
    now = _now()
    with db.get_conn() as conn:
        conn.execute(
            "UPDATE review_reply_drafts SET sent=1, updated_at=? WHERE id=?",
            (now, draft_id)
        )


# ════════════════════════════════════════════════
# BUSINESS PROFILE POSTS
# ════════════════════════════════════════════════

def upsert_bp_post(profile_id: str, data: dict) -> str:
    pid = data.get("id") or str(uuid.uuid4())[:12]
    now = _now()
    with db.get_conn() as conn:
        conn.execute("""
            INSERT INTO business_profile_posts
                (id, profile_id, gbp_post_id, post_type, summary, cta_type, cta_url,
                 media_url, state, scheduled_at, published_at, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(gbp_post_id) DO UPDATE SET
                summary=excluded.summary, state=excluded.state,
                published_at=excluded.published_at, updated_at=excluded.updated_at
        """, (
            pid, profile_id, data.get("gbp_post_id"), data.get("post_type", "STANDARD"),
            data.get("summary"), data.get("cta_type"), data.get("cta_url"),
            data.get("media_url"), data.get("state", "draft"),
            data.get("scheduled_at"), data.get("published_at"),
            data.get("created_at", now), now,
        ))
    return pid


def list_bp_posts(profile_id: str = "", state: str = "") -> list[dict]:
    sql = "SELECT * FROM business_profile_posts WHERE 1=1"
    params: list = []
    if profile_id:
        sql += " AND profile_id=?"; params.append(profile_id)
    if state:
        sql += " AND state=?"; params.append(state)
    sql += " ORDER BY created_at DESC"
    with db.get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


# ════════════════════════════════════════════════
# INSIGHTS
# ════════════════════════════════════════════════

def upsert_insights(profile_id: str, data: dict):
    now = _now()
    with db.get_conn() as conn:
        conn.execute("""
            INSERT INTO business_profile_insights
                (profile_id, period_start, period_end,
                 views_search, views_maps, actions_website,
                 actions_directions, actions_phone, photos_views, logged_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (
            profile_id, data.get("period_start"), data.get("period_end"),
            data.get("views_search", 0), data.get("views_maps", 0),
            data.get("actions_website", 0), data.get("actions_directions", 0),
            data.get("actions_phone", 0), data.get("photos_views", 0), now,
        ))


def get_latest_insights(profile_id: str) -> dict | None:
    with db.get_conn() as conn:
        row = conn.execute("""
            SELECT * FROM business_profile_insights
            WHERE profile_id=? ORDER BY logged_at DESC LIMIT 1
        """, (profile_id,)).fetchone()
    return dict(row) if row else None


# ════════════════════════════════════════════════
# SYNC HELPER
# ════════════════════════════════════════════════

def sync_from_connector(connector) -> dict:
    """コネクタからデータを取得し DB に書き込む。同期件数を返す。"""
    counts = {"profiles": 0, "reviews": 0, "insights": 0, "posts": 0}

    locations = connector.sync_locations()
    for loc in locations:
        # プロファイル作成/更新
        loc_id = loc["gbp_location_id"]
        reviews_raw = connector.sync_reviews(loc_id)
        unanswered = sum(1 for r in reviews_raw if r.get("status") == "unanswered")

        total = len(reviews_raw)
        avg = (sum(r["rating"] for r in reviews_raw) / total) if total else 0
        photo_alert = 1 if loc.get("photos_count", 0) < 5 else 0

        profile_data = {
            **loc,
            "total_reviews": total,
            "avg_rating": round(avg, 2),
            "unanswered_reviews": unanswered,
            "photo_alert": photo_alert,
            "last_synced_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        pid = upsert_profile(profile_data)

        # MEOスコア計算・更新
        profile = get_profile(pid)
        score = compute_meo_score(profile, unanswered)
        with db.get_conn() as conn:
            conn.execute(
                "UPDATE business_profiles SET meo_score=? WHERE id=?", (score, pid)
            )
        counts["profiles"] += 1

        # レビュー同期
        for rev in reviews_raw:
            upsert_review(pid, rev)
            counts["reviews"] += 1

        # インサイト同期
        insights = connector.sync_insights(loc_id)
        upsert_insights(pid, insights)
        counts["insights"] += 1

        # 投稿同期
        posts = connector.sync_posts(loc_id)
        for post in posts:
            upsert_bp_post(pid, post)
            counts["posts"] += 1

    return counts
