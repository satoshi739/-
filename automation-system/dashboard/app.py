"""
管理ダッシュボード v2
起動: python dashboard/app.py
ブラウザで http://localhost:8080 を開く
"""

import os
import sys
import json
import logging
import secrets
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from collections import defaultdict

import yaml
from flask import Flask, jsonify, redirect, render_template, request, session, url_for, send_from_directory
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv(Path(__file__).parent.parent / ".env")

import database as db

app = Flask(__name__)
# セッション用シークレットキー（.envの FLASK_SECRET_KEY で上書き可）
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
log = logging.getLogger(__name__)

ROOT         = Path(__file__).parent.parent.parent
AUTO         = Path(__file__).parent.parent
LEADS_DIR    = ROOT / "sales-system" / "leads"
FINANCE_DIR  = ROOT / "finance-system" / "logs"
PROJECTS_DIR = ROOT / "project-system" / "projects"
DECISION_DIR = AUTO / "decision_queue"
IG_QUEUE     = AUTO / "content_queue" / "instagram"
LINE_QUEUE   = AUTO / "content_queue" / "line"
QUEUE_ROOT   = AUTO / "content_queue"
LOGS_DIR     = AUTO / "logs"
BRANDS_CFG    = AUTO / "config" / "brands.yaml"

INBOX_DIR     = AUTO.parent / "media" / "inbox"
PROCESSED_DIR = AUTO.parent / "media" / "processed"
PERF_LOG_PATH = AUTO / "logs" / "performance_log.yaml"
CALENDAR_DIR  = AUTO / "content_queue" / "calendar"

PLATFORMS = ["instagram","threads","facebook","twitter","youtube","tiktok","line","wordpress"]
PLATFORM_ICONS = {
    "instagram":"📷","threads":"🧵","facebook":"📘","twitter":"𝕏","youtube":"▶️",
    "tiktok":"🎵","line":"📱","wordpress":"🌐",
}

# ── 認証 ──────────────────────────────────────────────────

@app.before_request
def require_login():
    """DASHBOARD_PASSWORD が設定されている場合、ログイン必須"""
    pw = os.environ.get("DASHBOARD_PASSWORD", "")
    if not pw:
        return  # パスワード未設定 → 認証スキップ
    # ログイン不要なパス
    exempt = ("/login", "/static", "/favicon.ico", "/health", "/webhook")
    if any(request.path.startswith(e) for e in exempt):
        return
    if not session.get("logged_in"):
        return redirect(url_for("login", next=request.path))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        pw_input = request.form.get("password", "")
        pw_env   = os.environ.get("DASHBOARD_PASSWORD", "")
        if pw_env and pw_input == pw_env:
            session["logged_in"] = True
            next_url = request.args.get("next") or url_for("index")
            return redirect(next_url)
        error = "パスワードが違います"
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── ヘルスチェック ─────────────────────────────────────────

@app.route("/health")
def health():
    try:
        stats = db.get_stats()
        return jsonify({"status": "ok", "db": "ok", "stats": stats})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.context_processor
def inject_globals():
    """全テンプレートに共通変数を注入"""
    return {
        "nav_brands":         load_brands(),
        "nav_platform_icons": PLATFORM_ICONS,
    }


def load_brands() -> dict:
    if not BRANDS_CFG.exists():
        return {}
    return yaml.safe_load(BRANDS_CFG.read_text(encoding="utf-8")).get("brands", {})


# ── ユーティリティ ────────────────────────────────────────

def load_yamls(d: Path) -> list[dict]:
    if not d.exists():
        return []
    out = []
    for f in sorted(d.glob("*.yaml"), reverse=True):
        try:
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
            if data:
                data["_file"] = f.name
                out.append(data)
        except Exception:
            pass
    return out


def save_yaml(d: Path, name: str, data: dict):
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(
        yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )


def log_tail(name: str, n=60) -> list[str]:
    p = LOGS_DIR / name
    if not p.exists():
        return []
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    return lines[-n:]


def ai_available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


# ── 統計ヘルパー（DB版）────────────────────────────────────

def get_stats() -> dict:
    """SQLiteから全統計を取得（YAMLファイルは不使用）"""
    s = db.get_stats()
    # MRRは財務YAMLから補完（まだDBにない）
    finances = load_yamls(FINANCE_DIR)
    s["mrr"] = sum(f.get("mrr_end", 0) for f in finances[-1:]) or 0
    return s


def get_funnel_data() -> dict:
    stats = db.get_stats()
    funnel = dict(stats.get("funnel", {}))
    # 'lost' は別途カウント
    with db.get_conn() as conn:
        lost = conn.execute(
            "SELECT COUNT(*) FROM leads WHERE outcome='lost'"
        ).fetchone()[0]
    funnel["lost"] = lost
    return funnel


def get_monthly_leads() -> dict:
    """直近6ヶ月の月別リード数（DB版）"""
    data = db.get_monthly_leads(6)
    # DBに無い月は0で補完
    months = []
    now = datetime.now()
    for i in range(5, -1, -1):
        d = now - timedelta(days=30*i)
        months.append(d.strftime("%Y-%m"))
    month_map = dict(zip(data["labels"], data["values"]))
    return {"labels": months, "values": [month_map.get(m, 0) for m in months]}


def get_channel_data() -> dict:
    with db.get_conn() as conn:
        rows = conn.execute("""
            SELECT COALESCE(source,'other') as ch, COUNT(*) as cnt
            FROM leads GROUP BY ch
        """).fetchall()
    if not rows:
        return {"labels": [], "values": []}
    labels = [r["ch"] for r in rows]
    values = [r["cnt"] for r in rows]
    return {"labels": labels, "values": values}


# ── ページ ────────────────────────────────────────────────

@app.route("/")
def index():
    stats    = get_stats()
    recent   = db.list_leads(outcome="active", limit=6)
    decisions= db.list_decisions(resolved=False)[:5]
    funnel   = get_funnel_data()
    monthly  = get_monthly_leads()
    channels = get_channel_data()
    now_str  = datetime.now().strftime("%Y年%m月%d日（%A）%H:%M")
    return render_template("index.html",
        stats=stats, recent=recent, decisions=decisions,
        funnel=funnel, monthly=monthly, channels=channels,
        now=now_str, ai=ai_available())


@app.route("/leads")
def leads_page():
    sf      = request.args.get("stage","")
    brand_f = request.args.get("brand","")
    leads   = db.list_leads(brand=brand_f, stage=sf, outcome="active", limit=200)
    return render_template("leads.html", leads=leads, stage_filter=sf, brand_filter=brand_f)


@app.route("/leads/kanban")
def leads_kanban():
    all_leads = db.list_leads(outcome="active", limit=500)
    kanban = {"L1":[],"L2":[],"L3":[],"L4":[]}
    for l in all_leads:
        s = l.get("stage","L1")
        if s in kanban:
            kanban[s].append(l)
    return render_template("leads_kanban.html", kanban=kanban,
                           now_date=datetime.now().strftime("%Y-%m-%d"))


@app.route("/leads/<lead_id>", methods=["GET","POST"])
def lead_detail(lead_id):
    if request.method == "POST":
        existing = db.get_lead(lead_id) or {}
        for f in ["stage","next_action","next_action_date","notes","outcome","lost_reason",
                  "current_situation","goals","budget_range","concerns"]:
            v = request.form.get(f)
            if v is not None:
                existing[f] = v
        existing["lead_id"]      = lead_id
        existing["last_contact"] = datetime.now().strftime("%Y-%m-%d")
        db.upsert_lead(existing)
        # YAMLも更新（スケジューラーとの後方互換）
        path = LEADS_DIR / f"{lead_id}.yaml"
        if path.exists():
            save_yaml(LEADS_DIR, f"{lead_id}.yaml", existing)
        return redirect(url_for("leads_page"))
    lead = db.get_lead(lead_id)
    if not lead:
        # YAMLファイルから試みる（未移行データ対応）
        path = LEADS_DIR / f"{lead_id}.yaml"
        if not path.exists():
            return "Not found", 404
        lead = yaml.safe_load(path.read_text(encoding="utf-8"))
        db.upsert_lead(lead)  # 遅延移行
    return render_template("lead_detail.html", lead=lead, lead_id=lead_id, ai=ai_available())


@app.route("/queue")
def queue_page():
    # DBからキューを取得
    brands = load_brands()
    queue_data = {}
    for brand_id in brands:
        queue_data[brand_id] = {}
        for platform in PLATFORMS:
            items = db.list_queue(brand=brand_id, channel=platform, pending_only=True)
            # DBになければYAMLから読む（後方互換）
            if not items:
                q_dir = QUEUE_ROOT / brand_id / platform
                items = [i for i in load_yamls(q_dir) if not i.get("posted")]
            if items:
                queue_data[brand_id][platform] = pending
    # 旧キューも表示（後方互換）
    ig_queue   = load_yamls(IG_QUEUE)
    line_queue = load_yamls(LINE_QUEUE)
    return render_template("queue.html",
        queue_data=queue_data, brands=brands,
        ig_queue=ig_queue, line_queue=line_queue,
        platform_icons=PLATFORM_ICONS)


@app.route("/queue/add", methods=["GET","POST"])
def queue_add():
    brands = load_brands()
    if request.method == "POST":
        brand   = request.form.get("brand","dsc-marketing")
        ch      = request.form.get("channel","instagram")
        ts      = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        entry   = {"brand":brand,"channel":ch,"posted":False,"source":"dashboard"}

        if ch == "instagram":
            mt = request.form.get("media_type","image")
            entry["media_type"] = mt
            entry["caption"]    = request.form.get("caption","")
            entry["image_url" if mt!="reel" else "video_url"] = request.form.get("image_url","") or request.form.get("video_url","")
        elif ch == "threads":
            entry["text"]      = request.form.get("text","")
            entry["image_url"] = request.form.get("image_url","")
        elif ch == "facebook":
            entry["text"]      = request.form.get("fb_text","")
            entry["image_url"] = request.form.get("fb_image_url","")
        elif ch == "twitter":
            entry["text"]      = request.form.get("text","")
        elif ch == "youtube":
            entry["title"]       = request.form.get("title","")
            entry["description"] = request.form.get("description","")
            entry["video_url"]   = request.form.get("video_url","")
            entry["tags"]        = request.form.get("tags","").split(",")
        elif ch == "tiktok":
            entry["title"]     = request.form.get("title","")
            entry["video_url"] = request.form.get("video_url","")
        elif ch == "line":
            entry["message"]   = request.form.get("message","")
            entry["image_url"] = request.form.get("image_url","")
        elif ch == "wordpress":
            entry["title"]       = request.form.get("title","")
            entry["content"]     = request.form.get("content","")
            entry["status"]      = request.form.get("wp_status","draft")
            entry["image_url"]   = request.form.get("image_url","")

        # 投稿予約日時（空なら自動投稿に委ねる）
        sched = request.form.get("schedule_at", "").strip()
        if sched:
            entry["scheduled_at"] = sched

        # DBに保存（主ストア）
        entry["filename"] = f"{ts}_manual.yaml"
        db.enqueue(entry)
        db.log_activity("queue_add", brand=brand, platform=ch,
                        detail=f"手動追加: {entry.get('caption','')[:40] or entry.get('title','')[:40] or entry.get('message','')[:40]}")
        # YAMLにも保存（スケジューラーとの後方互換）
        save_yaml(QUEUE_ROOT / brand / ch, f"{ts}_manual.yaml", entry)
        if ch == "instagram": save_yaml(IG_QUEUE, f"{ts}_manual.yaml", entry)
        if ch == "line":      save_yaml(LINE_QUEUE, f"{ts}_manual.yaml", entry)
        return redirect(url_for("queue_page"))
    return render_template("queue_add.html", ai=ai_available(), brands=brands,
                           platform_icons=PLATFORM_ICONS)


@app.route("/calendar")
def calendar_page():
    brands   = load_brands()
    events   = []
    brand_colors = {bid: b.get("color","#6366f1") for bid, b in brands.items()}
    platform_icons = PLATFORM_ICONS

    for bid, brand in brands.items():
        color = brand.get("color", "#6366f1")
        for p in PLATFORMS:
            if not brand.get("channels", {}).get(p):
                continue
            items = load_yamls(QUEUE_ROOT / bid / p)
            for item in items:
                fname   = item.get("_file", "")
                # ファイル名から日付推定（YYYY-MM-DD_HHmmSS_*.yaml）
                date_str = fname[:10] if len(fname) >= 10 else datetime.now().strftime("%Y-%m-%d")
                content  = item.get("caption") or item.get("text") or item.get("title") or item.get("message") or ""
                posted   = item.get("posted", False)
                events.append({
                    "title":           f"{platform_icons.get(p,'')} {content[:28]}{'…' if len(content)>28 else ''}",
                    "start":           date_str,
                    "backgroundColor": "#34d399" if posted else color,
                    "borderColor":     "#34d399" if posted else color,
                    "textColor":       "#fff",
                    "extendedProps": {
                        "brand_id":      bid,
                        "brand_name":    brand.get("name_short", bid),
                        "platform":      p,
                        "platform_icon": platform_icons.get(p, ""),
                        "content":       content,
                        "posted":        posted,
                        "file":          fname,
                    }
                })

    return render_template("calendar.html",
        events=events, brand_colors=brand_colors)


@app.route("/generate")
def generate_page():
    if not ai_available():
        return render_template("no_api.html", feature="AI生成", key="ANTHROPIC_API_KEY")
    return render_template("generate.html")


@app.route("/analytics")
def analytics():
    funnel   = get_funnel_data()
    monthly  = get_monthly_leads()
    channels = get_channel_data()
    stats    = get_stats()
    finances = load_yamls(FINANCE_DIR)
    mrr_history = {"labels":[], "values":[]}
    for f in finances[-6:]:
        mrr_history["labels"].append(f.get("month",""))
        mrr_history["values"].append(f.get("mrr_end", 0))

    # ブランド別サイトアクセス（GA4）
    brands = load_brands()
    brand_traffic = {}
    for bid, b in brands.items():
        ga = _get_ga_data(bid)
        ov = ga.get("overview", {})
        brand_traffic[bid] = {
            "name":     b.get("name_short", bid),
            "color":    b.get("color", "#6366f1"),
            "url":      b.get("url", ""),
            "sessions": ov.get("sessions", 0),
            "pageviews": ov.get("pageviews", 0),
            "users":    ov.get("users", 0),
            "avg_duration": ov.get("avg_duration", 0),
            "bounce_rate":  ov.get("bounce_rate", 0),
            "configured": bool(ov.get("sessions", None) is not None and not ov.get("error")),
        }

    return render_template("analytics.html",
        funnel=funnel, monthly=monthly, channels=channels,
        stats=stats, mrr_history=mrr_history, brand_traffic=brand_traffic)


@app.route("/brands")
def brands_page():
    brands = load_brands()
    # 各ブランドのキュー件数を集計
    brand_stats = {}
    for bid, bcfg in brands.items():
        pending = sum(
            len([i for i in load_yamls(QUEUE_ROOT/bid/p) if not i.get("posted")])
            for p in PLATFORMS
        )
        brand_stats[bid] = {"pending": pending}
    return render_template("brands.html", brands=brands, brand_stats=brand_stats,
                           platform_icons=PLATFORM_ICONS)


@app.route("/brands/<brand_id>")
def brand_detail(brand_id):
    brands = load_brands()
    brand = brands.get(brand_id)
    if not brand:
        return "Brand not found", 404

    # チャンネル別キュー（テンプレートが期待するフォーマットで構築）
    platforms = {}
    for p in PLATFORMS:
        if brand.get("channels", {}).get(p):
            items = load_yamls(QUEUE_ROOT / brand_id / p)
            platforms[p] = {
                "icon":          PLATFORM_ICONS.get(p, ""),
                "posts":         items,
                "pending_count": sum(1 for i in items if not i.get("posted")),
            }

    # アナリティクス（GA4 / Search Console）
    ga_data  = _get_ga_data(brand_id)
    gsc_data = _get_gsc_data(brand_id)

    # WordPressの下書き一覧
    wp_drafts = _get_wp_drafts(brand_id)

    return render_template("brand_detail.html",
        brand_id=brand_id, brand=brand,
        platforms=platforms,
        ga_data=ga_data, gsc_data=gsc_data,
        wp_drafts=wp_drafts,
        platform_icons=PLATFORM_ICONS)


def _get_ga_data(brand_id: str) -> dict:
    """GA4データを取得（APIキー未設定の場合は空）"""
    env_key = f"{brand_id.upper().replace('-','_')}_GA4_PROPERTY_ID"
    if not os.environ.get(env_key):
        return {}
    try:
        from sns.analytics import GA4Client
        client = GA4Client(env_key)
        overview = client.get_overview(28)
        series   = client.get_daily_series(28)
        pages    = client.get_top_pages(28, 5)
        return {"overview": overview, "series": series, "pages": pages}
    except Exception as e:
        return {"error": str(e)}


def _get_gsc_data(brand_id: str) -> dict:
    """Search Consoleデータを取得"""
    env_key = f"{brand_id.upper().replace('-','_')}_GSC_SITE_URL"
    if not os.environ.get(env_key):
        return {}
    try:
        from sns.analytics import SearchConsoleClient
        client = SearchConsoleClient(env_key)
        return {
            "overview": client.get_overview(28),
            "queries":  client.get_top_queries(28, 10),
        }
    except Exception as e:
        return {"error": str(e)}


def _get_wp_drafts(brand_id: str) -> list:
    """WordPress下書き一覧を取得"""
    env_key = f"{brand_id.upper().replace('-','_')}_WP_URL"
    if not os.environ.get(env_key):
        return []
    try:
        from sns.wordpress import WordPressPoster
        wp = WordPressPoster(brand_id)
        return wp.get_posts("draft", 5)
    except Exception as e:
        return []


@app.route("/brands/<brand_id>/publish_draft/<int:post_id>", methods=["POST"])
def publish_wp_draft(brand_id, post_id):
    """WordPress下書きを公開"""
    try:
        from sns.wordpress import WordPressPoster
        WordPressPoster(brand_id).publish_post(post_id)
    except Exception as e:
        pass
    return redirect(url_for("brand_detail", brand_id=brand_id))


@app.route("/api/analytics/<brand_id>")
def api_analytics(brand_id):
    return jsonify({
        "ga":  _get_ga_data(brand_id),
        "gsc": _get_gsc_data(brand_id),
    })


@app.route("/decisions")
def decisions_page():
    decisions = db.list_decisions(resolved=False)
    return render_template("decisions.html", decisions=decisions)


@app.route("/decisions/resolve/<int:decision_id>", methods=["POST"])
def resolve_decision(decision_id):
    db.resolve_decision(decision_id)
    return redirect(url_for("decisions_page"))


@app.route("/decisions/resolve_file/<filename>", methods=["POST"])
def resolve_decision_file(filename):
    """後方互換: ファイル名ベースで判断待ちを解決"""
    with db.get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM decisions WHERE filename=?", (filename,)
        ).fetchone()
    if row:
        db.resolve_decision(row["id"])
    # YAMLファイルも更新
    path = DECISION_DIR / filename
    if path.exists():
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            data.update(resolved=True,
                        resolved_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        resolved_note=request.form.get("note",""))
            save_yaml(DECISION_DIR, filename, data)
        except Exception:
            pass
    return redirect(url_for("decisions_page"))


@app.route("/logs")
def logs_page():
    return render_template("logs.html",
        scheduler_log=log_tail("scheduler.log"),
        morning_log  =log_tail("morning.log"),
        server_log   =log_tail("server.log"))


# ── API ──────────────────────────────────────────────────

@app.route("/api/stats")
def api_stats():
    s = get_stats()
    s["updated_at"] = datetime.now().isoformat()
    s["ai_enabled"] = ai_available()
    return jsonify(s)


@app.route("/api/leads/stage", methods=["POST"])
def api_lead_stage():
    """カンバンのドラッグ&ドロップ後のステージ更新"""
    d        = request.get_json()
    lead_id  = d.get("lead_id","")
    new_stage= d.get("stage","")
    lead = db.get_lead(lead_id)
    if not lead:
        return jsonify({"ok":False,"error":"not found"}), 404
    db.update_lead_stage(lead_id, new_stage)
    # YAMLファイルも更新（後方互換）
    path = LEADS_DIR / f"{lead_id}.yaml"
    if path.exists():
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            data["stage"] = new_stage
            data["last_contact"] = datetime.now().strftime("%Y-%m-%d")
            save_yaml(LEADS_DIR, f"{lead_id}.yaml", data)
        except Exception:
            pass
    return jsonify({"ok":True})


@app.route("/api/ai/generate_post", methods=["POST"])
def api_generate_post():
    if not ai_available():
        return jsonify({"error":"ANTHROPIC_API_KEY未設定"}), 400
    from dashboard.ai import generate_instagram_post
    d = request.get_json()
    try:
        result = generate_instagram_post(
            topic =d.get("topic",""),
            target=d.get("target",""),
            tone  =d.get("tone","実務的"),
            brand =d.get("brand","dsc-marketing"),
            extra =d.get("extra",""),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ai/generate_line", methods=["POST"])
def api_generate_line():
    if not ai_available():
        return jsonify({"error":"ANTHROPIC_API_KEY未設定"}), 400
    from dashboard.ai import generate_line_message
    d = request.get_json()
    try:
        msg = generate_line_message(
            topic  =d.get("topic",""),
            brand  =d.get("brand","dsc-marketing"),
            purpose=d.get("purpose","集客・認知"),
        )
        return jsonify({"message": msg})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/queue/delete/<brand_id>/<platform>/<filename>", methods=["POST"])
def queue_delete(brand_id, platform, filename):
    """キューアイテムを削除（DB + YAML）"""
    import re
    # パストラバーサル対策
    if not re.match(r'^[\w\-. ]+$', filename):
        return "Invalid filename", 400
    # DBから削除
    with db.get_conn() as conn:
        conn.execute("DELETE FROM queue_items WHERE brand=? AND channel=? AND filename=?",
                     (brand_id, platform, filename))
    # YAMLファイルも削除
    path = QUEUE_ROOT / brand_id / platform / filename
    if path.exists() and str(path).startswith(str(QUEUE_ROOT)):
        path.unlink()
    return redirect(url_for("queue_page"))


@app.route("/api/ai/suggest_topics/<brand_id>", methods=["POST"])
def api_suggest_topics(brand_id):
    """今日のトピックをAIが3つ提案"""
    if not ai_available():
        return jsonify({"error": "ANTHROPIC_API_KEY未設定"}), 400
    brands = load_brands()
    brand = brands.get(brand_id, {})
    from dashboard.ai import BRAND_CONTEXTS
    import anthropic
    brand_ctx = BRAND_CONTEXTS.get(brand_id, "")
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    today = datetime.now().strftime("%Y年%m月%d日")
    prompt = f"""{brand_ctx}
今日（{today}）のSNS投稿に最適なテーマを3つ提案してください。
旬のビジネストレンド、季節感、ターゲットの関心に合わせてください。

JSON形式で返してください:
{{"topics": ["テーマ1（20文字以内）", "テーマ2（20文字以内）", "テーマ3（20文字以内）"]}}
JSONのみ返す。"""
    try:
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001", max_tokens=200,
            messages=[{"role":"user","content":prompt}]
        )
        import json as _json
        raw = resp.content[0].text.strip()
        if "```" in raw:
            raw = raw.split("```")[1].lstrip("json").strip()
        data = _json.loads(raw)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ai/generate_all/<brand_id>", methods=["POST"])
def api_generate_all(brand_id):
    """全プラットフォーム一括生成"""
    if not ai_available():
        return jsonify({"error": "ANTHROPIC_API_KEY未設定"}), 400
    from dashboard.ai import generate_all_platforms
    d = request.get_json()
    topic = d.get("topic", "")
    extra = d.get("extra", "")
    if not topic:
        return jsonify({"error": "トピックを入力してください"}), 400
    try:
        result = generate_all_platforms(topic=topic, brand=brand_id, extra_context=extra)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ai/generate_reel/<brand_id>", methods=["POST"])
def api_generate_reel(brand_id):
    """リール用スライド画像を生成してキューに保存"""
    if not ai_available():
        return jsonify({"error": "ANTHROPIC_API_KEY未設定"}), 400

    from dashboard.ai import generate_reel_script
    from sns.image_generator import generate_reel_slides, save_slides, slides_to_video

    brands = load_brands()
    brand  = brands.get(brand_id, {})
    brand_color = brand.get("color", "#5b8af5")
    brand_name  = brand.get("name_short", brand_id)

    d     = request.get_json()
    topic = d.get("topic", "")
    reel_data = d.get("reel")  # AI生成済みのreel dictがあれば使う

    if not reel_data:
        if not topic:
            return jsonify({"error": "トピックを入力してください"}), 400
        reel_data = generate_reel_script(topic, brand_id)

    try:
        slides = generate_reel_slides(
            title       = reel_data.get("title", topic),
            points      = reel_data.get("points", []),
            cta         = reel_data.get("cta", "詳しくはプロフリンクから"),
            brand_color = brand_color,
            brand_name  = brand_name,
        )
        ts     = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = f"{brand_id}_{ts}_reel"
        paths  = save_slides(slides, prefix)

        # 動画変換を試みる
        video_path = slides_to_video(paths, prefix)

        slide_urls = [str(p.relative_to(AUTO)) for p in paths]
        return jsonify({
            "ok": True,
            "slides": slide_urls,
            "video": str(video_path.relative_to(AUTO)) if video_path else None,
            "reel_data": reel_data,
        })
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


@app.route("/api/queue/save_all/<brand_id>", methods=["POST"])
def api_save_all_to_queue(brand_id):
    """一括生成したコンテンツを全プラットフォームのキューに保存"""
    brands = load_brands()
    brand  = brands.get(brand_id, {})
    if not brand:
        return jsonify({"error": "Brand not found"}), 404

    d        = request.get_json()
    content  = d.get("content", {})
    ts       = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    saved    = []
    enabled  = brand.get("channels", {})

    platform_map = {
        "instagram": lambda c: {
            "media_type": "image",
            "caption":    f"{c['caption']}\n\n{c['hashtags']}",
            "image_url":  c.get("image_url", ""),
        },
        "threads": lambda c: {"text": c["text"]},
        "facebook": lambda c: {"text": c["text"]},
        "twitter":  lambda c: {"text": c["text"]},
        "line":     lambda c: {"message": c["message"]},
        "wordpress": lambda c: {
            "title":   c["title"],
            "content": c["content"],
            "status":  "draft",
        },
    }

    for platform, builder in platform_map.items():
        if not enabled.get(platform):
            continue
        platform_content = content.get(platform)
        if not platform_content:
            continue
        try:
            entry = builder(platform_content)
            entry.update({"brand": brand_id, "channel": platform, "posted": False, "source": "ai_bulk"})
            entry["filename"] = f"{ts}_ai_bulk.yaml"
            db.enqueue(entry)
            save_yaml(QUEUE_ROOT / brand_id / platform, f"{ts}_ai_bulk.yaml", entry)
            saved.append(platform)
        except Exception as e:
            pass  # スキップして続行

    return jsonify({"ok": True, "saved": saved})


@app.route("/api/ai/lead_reply/<lead_id>")
def api_lead_reply(lead_id):
    if not ai_available():
        return jsonify({"error":"ANTHROPIC_API_KEY未設定"}), 400
    from dashboard.ai import generate_lead_reply
    lead = db.get_lead(lead_id)
    if not lead:
        return jsonify({"error":"not found"}), 404
    try:
        reply = generate_lead_reply(lead)
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/settings/<brand_id>", methods=["GET", "POST"])
def settings_page(brand_id):
    """ブランド別API設定ページ"""
    brands = load_brands()
    brand  = brands.get(brand_id)
    if not brand:
        return "Brand not found", 404

    env_path = AUTO / ".env"
    saved = False
    error = None

    # 現在の.envを読み込む
    def read_env() -> dict:
        if not env_path.exists():
            return {}
        result = {}
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, _, v = line.partition("=")
                result[k.strip()] = v.strip()
        return result

    if request.method == "POST":
        try:
            env_data = read_env()
            # フォームの値を更新（空でないもののみ）
            for key, val in request.form.items():
                val = val.strip()
                # 空欄の場合でもキーは保持（既存値を消さないため空なら既存値を使う）
                if val:
                    env_data[key] = val
                elif key not in env_data:
                    env_data[key] = ""

            # .envファイルに書き戻す
            lines = []
            written = set()
            # 既存の構造を保持しながら更新
            if env_path.exists():
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    stripped = line.strip()
                    if not stripped or stripped.startswith("#"):
                        lines.append(line)
                        continue
                    if "=" in stripped:
                        k = stripped.split("=")[0].strip()
                        if k in env_data:
                            lines.append(f"{k}={env_data[k]}")
                            written.add(k)
                        else:
                            lines.append(line)
                    else:
                        lines.append(line)
            # 新規キーを追記
            for k, v in env_data.items():
                if k not in written:
                    lines.append(f"{k}={v}")
                    written.add(k)

            env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            # プロセスの環境変数も更新
            for k, v in env_data.items():
                if v:
                    os.environ[k] = v
            saved = True
        except Exception as e:
            error = str(e)

    env_data = read_env()

    # 接続ステータスチェック（キーが設定されているか）
    prefix = brand_id.upper().replace("-", "_")
    status = {
        "anthropic":  bool(os.environ.get("ANTHROPIC_API_KEY") or env_data.get("ANTHROPIC_API_KEY")),
        "meta":       bool(env_data.get(f"{prefix}_META_ACCESS_TOKEN")),
        "twitter":    bool(env_data.get(f"{prefix}_TWITTER_API_KEY")),
        "line":       bool(env_data.get("LINE_CHANNEL_ACCESS_TOKEN") or env_data.get(f"LINE_CHANNEL_ACCESS_TOKEN_{prefix.split('_')[0]}")),
        "wordpress":  bool(env_data.get(f"{prefix}_WP_APP_PASSWORD")),
        "youtube":    bool(env_data.get(f"{prefix}_YOUTUBE_CHANNEL_ID")),
        "tiktok":     bool(env_data.get(f"{prefix}_TIKTOK_ACCESS_TOKEN")),
        "google":     bool(env_data.get(f"{prefix}_GA4_PROPERTY_ID") or (AUTO / "credentials.json").exists()),
    }

    return render_template("settings.html",
        brand_id=brand_id, brand=brand,
        env=env_data, status=status,
        saved=saved, error=error)


@app.route("/api/test_connection/<brand_id>/<conn_type>", methods=["POST"])
def api_test_connection(brand_id, conn_type):
    """API接続テスト"""
    prefix = brand_id.upper().replace("-", "_")

    if conn_type == "meta":
        token = os.environ.get(f"{prefix}_META_ACCESS_TOKEN", "")
        ig_id = os.environ.get(f"{prefix}_INSTAGRAM_ACCOUNT_ID", "")
        if not token:
            return jsonify({"ok": False, "error": "META_ACCESS_TOKENが設定されていません"})
        try:
            import urllib.request
            url = f"https://graph.facebook.com/v19.0/me?access_token={token}"
            with urllib.request.urlopen(url, timeout=8) as r:
                data = json.loads(r.read())
            return jsonify({"ok": True, "detail": f"ユーザー: {data.get('name', data.get('id', ''))}"})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)[:100]})

    elif conn_type == "twitter":
        try:
            import tweepy
            client = tweepy.Client(
                consumer_key=os.environ.get(f"{prefix}_TWITTER_API_KEY"),
                consumer_secret=os.environ.get(f"{prefix}_TWITTER_API_SECRET"),
                access_token=os.environ.get(f"{prefix}_TWITTER_ACCESS_TOKEN"),
                access_token_secret=os.environ.get(f"{prefix}_TWITTER_ACCESS_SECRET"),
            )
            me = client.get_me()
            return jsonify({"ok": True, "detail": f"@{me.data.username}"})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)[:100]})

    elif conn_type == "wordpress":
        try:
            sys.path.insert(0, str(AUTO))
            from sns.wordpress import WordPressPoster
            wp = WordPressPoster(brand_id)
            posts = wp.get_posts("draft", 1)
            return jsonify({"ok": True, "detail": f"接続OK（下書き{len(posts)}件）"})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)[:100]})

    elif conn_type == "line":
        try:
            token_key = "LINE_CHANNEL_ACCESS_TOKEN" if brand_id == "dsc-marketing" else f"LINE_CHANNEL_ACCESS_TOKEN_{prefix.split('_')[0]}"
            token = os.environ.get(token_key, "")
            if not token:
                return jsonify({"ok": False, "error": "LINE_CHANNEL_ACCESS_TOKENが設定されていません"})
            import urllib.request
            req = urllib.request.Request(
                "https://api.line.me/v2/bot/info",
                headers={"Authorization": f"Bearer {token}"}
            )
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read())
            return jsonify({"ok": True, "detail": f"Bot名: {data.get('displayName','')}"})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)[:100]})

    elif conn_type == "google":
        cred_path = AUTO / "credentials.json"
        if not cred_path.exists():
            return jsonify({"ok": False, "error": "credentials.json が見つかりません"})
        try:
            import json as _json
            cred = _json.loads(cred_path.read_text())
            email = cred.get("client_email", "不明")
            return jsonify({"ok": True, "detail": f"サービスアカウント: {email}"})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)[:100]})

    return jsonify({"ok": False, "error": "Unknown connection type"})


@app.route("/settings")
def settings_index():
    """設定トップ（ブランド選択）"""
    brands = load_brands()
    return render_template("brands.html", brands=brands,
                           brand_stats={}, platform_icons=PLATFORM_ICONS,
                           settings_mode=True)


@app.route("/media/<path:filename>")
def serve_media(filename):
    """生成されたメディアファイルを配信"""
    media_dir = AUTO / "generated_media"
    return send_from_directory(str(media_dir), filename)


@app.route("/inbox")
def inbox_page():
    """写真インボックスページ"""
    brands = load_brands()
    inbox_data = {}
    for bid in brands:
        inbox_dir = INBOX_DIR / bid
        processed_dir = PROCESSED_DIR / bid
        files = sorted(inbox_dir.glob("*")) if inbox_dir.exists() else []
        media_exts = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".mp4", ".mov", ".m4v"}
        inbox_files = [
            {
                "name": f.name,
                "size": round(f.stat().st_size / 1024, 1),
                "is_video": f.suffix.lower() in {".mp4", ".mov", ".m4v"},
                "brand": bid,
            }
            for f in files if f.is_file() and f.suffix.lower() in media_exts
        ]
        processed_count = len(list(processed_dir.glob("*"))) if processed_dir.exists() else 0
        inbox_data[bid] = {
            "files": inbox_files,
            "processed_count": processed_count,
            "path": str(INBOX_DIR / bid),
        }
    return render_template("inbox.html", inbox_data=inbox_data, brands=brands)


@app.route("/api/inbox/process", methods=["POST"])
def api_inbox_process():
    """インボックス手動処理トリガー"""
    d = request.get_json() or {}
    brand = d.get("brand")
    dry_run = d.get("dry_run", False)
    try:
        from sns.photo_importer import process_inbox
        count = process_inbox(brand=brand, dry_run=dry_run)
        return jsonify({"ok": True, "processed": count})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/performance")
def performance_page():
    """パフォーマンス分析ページ"""
    brands = load_brands()
    perf_data = {}
    if PERF_LOG_PATH.exists():
        try:
            from sns.performance import get_engagement_report, get_top_performing_posts
            for bid in brands:
                report = get_engagement_report(bid, days=28)
                top_posts = get_top_performing_posts(bid, "instagram", limit=5, days=90)
                perf_data[bid] = {"report": report, "top_posts": top_posts}
        except Exception as e:
            log.error(f"performance data error: {e}")
    return render_template("performance.html", brands=brands, perf_data=perf_data)


@app.route("/weekly")
def weekly_page():
    """週次AIカレンダービューア"""
    brands = load_brands()
    calendars = {}
    if CALENDAR_DIR.exists():
        for f in sorted(CALENDAR_DIR.glob("*.yaml"), reverse=True):
            try:
                cal = yaml.safe_load(f.read_text(encoding="utf-8"))
                if cal:
                    brand_key = cal.get("brand", f.stem.split("_")[1] if "_" in f.stem else "unknown")
                    if brand_key not in calendars:
                        cal["_file"] = f.name
                        calendars[brand_key] = cal
            except Exception:
                pass
    return render_template("weekly.html", brands=brands, calendars=calendars, ai=ai_available())


@app.route("/api/queue/schedule_week/<brand_id>", methods=["POST"])
def api_schedule_week(brand_id):
    """週次カレンダーのアイテムを予約キューに一括登録"""
    brands = load_brands()
    if brand_id not in brands:
        return jsonify({"error": "Brand not found"}), 404

    d     = request.get_json() or {}
    items = d.get("items", [])  # [{date, time, platform, caption_draft, hashtags, topic, format}]

    scheduled = 0
    for i, item in enumerate(items):
        platform    = item.get("platform", "instagram")
        date_str    = item.get("date", "")
        time_str    = item.get("time", "12:00")
        scheduled_at = f"{date_str} {time_str}"
        caption     = item.get("caption_draft", item.get("caption", "")).strip()
        hashtags    = item.get("hashtags", "").strip()
        topic       = item.get("topic", "")
        fmt         = item.get("format", "image")

        # ファイル名: 日付_時刻_プラットフォーム.yaml（重複防止に連番）
        fname = f"{date_str}_{time_str.replace(':','')}_{platform}_{i:02d}.yaml"

        base = {"brand": brand_id, "channel": platform, "posted": False,
                "source": "weekly_calendar", "topic": topic, "scheduled_at": scheduled_at}

        if platform == "instagram":
            full_caption = f"{caption}\n\n{hashtags}".strip() if hashtags else caption
            entry = {**base, "media_type": fmt, "caption": full_caption, "image_url": ""}
            save_yaml(QUEUE_ROOT / brand_id / platform, fname, entry)
            save_yaml(IG_QUEUE, fname, entry)
        elif platform == "line":
            entry = {**base, "message": item.get("message_draft", caption)}
            save_yaml(QUEUE_ROOT / brand_id / platform, fname, entry)
            save_yaml(LINE_QUEUE, fname, entry)
        else:
            full_caption = f"{caption}\n\n{hashtags}".strip() if hashtags else caption
            entry = {**base, "text": full_caption}
            save_yaml(QUEUE_ROOT / brand_id / platform, fname, entry)

        scheduled += 1

    return jsonify({"ok": True, "scheduled": scheduled})


@app.route("/api/ai/blog_post", methods=["POST"])
def api_generate_blog_post():
    """個人ブログ記事をAIで生成（+ オプションでWordPressに下書き保存）"""
    if not ai_available():
        return jsonify({"error": "ANTHROPIC_API_KEY未設定"}), 400
    from dashboard.ai import generate_blog_post
    d = request.get_json() or {}
    topic       = d.get("topic", "")
    style       = d.get("style", "体験談・実践寄り")
    word_count  = int(d.get("word_count", 1200))
    save_to_wp  = d.get("save_to_wp", False)   # Trueで下書き保存
    publish     = d.get("publish", False)       # Trueで即公開

    if not topic:
        return jsonify({"error": "topic は必須です"}), 400
    try:
        post = generate_blog_post(topic=topic, style=style, word_count=word_count)

        wp_result = None
        if save_to_wp:
            from sns.wordpress import WordPressPoster
            wp = WordPressPoster(brand="satoshi-blog")
            status = "publish" if publish else "draft"
            wp_result = wp.create_post(
                title=post["title"],
                content=post["content_html"],
                status=status,
            )

        # キューにも保存
        ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        entry = {
            "brand": "satoshi-blog", "channel": "wordpress",
            "title": post["title"], "content": post["content_html"],
            "status": "publish" if publish else "draft",
            "meta_description": post.get("meta_description", ""),
            "tags": post.get("tags", []),
            "posted": bool(wp_result and wp_result.get("status") in ("draft","publish","published")),
            "source": "ai_blog",
        }
        save_yaml(QUEUE_ROOT / "satoshi-blog" / "wordpress", f"{ts}_blog.yaml", entry)

        return jsonify({"ok": True, "post": post, "wp": wp_result})
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


@app.route("/api/ai/weekly_calendar/<brand_id>", methods=["POST"])
def api_generate_weekly_calendar(brand_id):
    """週次カレンダーをAIで生成してYAMLに保存"""
    if not ai_available():
        return jsonify({"error": "ANTHROPIC_API_KEY未設定"}), 400
    from dashboard.ai import generate_weekly_calendar, save_weekly_calendar
    d = request.get_json() or {}
    try:
        calendar = generate_weekly_calendar(brand=brand_id, week_start=d.get("week_start"))
        saved_path = save_weekly_calendar(calendar, brand=brand_id)
        return jsonify({"ok": True, "path": str(saved_path), "calendar": calendar})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ai/trending_topics/<brand_id>", methods=["POST"])
def api_trending_topics(brand_id):
    """トレンドトピックをAIがリサーチして提案"""
    if not ai_available():
        return jsonify({"error": "ANTHROPIC_API_KEY未設定"}), 400
    from dashboard.ai import research_trending_topics
    try:
        topics = research_trending_topics(brand=brand_id, n=5)
        return jsonify({"ok": True, "topics": topics})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ai/generate_variants/<brand_id>", methods=["POST"])
def api_generate_variants(brand_id):
    """3バリアント生成＋AI自動選択"""
    if not ai_available():
        return jsonify({"error": "ANTHROPIC_API_KEY未設定"}), 400
    from dashboard.ai import generate_instagram_post_variants
    d = request.get_json() or {}
    try:
        result = generate_instagram_post_variants(
            topic=d.get("topic", ""),
            target=d.get("target", "中小企業経営者"),
            tone=d.get("tone", "実務的"),
            brand=brand_id,
            extra=d.get("extra", ""),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ai/reel_rich/<brand_id>", methods=["POST"])
def api_reel_rich(brand_id):
    """豪華リール台本（BGM・テロップ・シーン割り）"""
    if not ai_available():
        return jsonify({"error": "ANTHROPIC_API_KEY未設定"}), 400
    from dashboard.ai import generate_reel_script_rich
    d = request.get_json() or {}
    try:
        result = generate_reel_script_rich(
            topic=d.get("topic", ""),
            brand=brand_id,
            duration_sec=int(d.get("duration_sec", 30)),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ai/shorts/<brand_id>", methods=["POST"])
def api_shorts(brand_id):
    """YouTube Shorts専用コンテンツ生成"""
    if not ai_available():
        return jsonify({"error": "ANTHROPIC_API_KEY未設定"}), 400
    from dashboard.ai import generate_shorts_content
    d = request.get_json() or {}
    try:
        result = generate_shorts_content(topic=d.get("topic", ""), brand=brand_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ai/tiktok/<brand_id>", methods=["POST"])
def api_tiktok_content(brand_id):
    """TikTok専用コンテンツ生成"""
    if not ai_available():
        return jsonify({"error": "ANTHROPIC_API_KEY未設定"}), 400
    from dashboard.ai import generate_tiktok_content
    d = request.get_json() or {}
    try:
        result = generate_tiktok_content(topic=d.get("topic", ""), brand=brand_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── リール・ストーリー ────────────────────────────────────

@app.route("/reels")
def reels_page():
    brands = load_brands()
    return render_template("reels.html", brands=brands, ai=ai_available())


@app.route("/stories")
def stories_page():
    brands = load_brands()
    return render_template("stories.html", brands=brands, ai=ai_available())


@app.route("/api/ai/reel_v2/<brand_id>", methods=["POST"])
def api_reel_v2(brand_id):
    """リール台本 v2（スタイル・ナレーション付き）"""
    if not ai_available():
        return jsonify({"error": "ANTHROPIC_API_KEY未設定"}), 400
    from dashboard.ai import generate_reel_script_v2
    d = request.get_json() or {}
    try:
        result = generate_reel_script_v2(
            topic=d.get("topic", ""),
            brand=brand_id,
            duration=int(d.get("duration", 30)),
            style=d.get("style", "教育系"),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ai/story/<brand_id>", methods=["POST"])
def api_story(brand_id):
    """ストーリーコンテンツ生成"""
    if not ai_available():
        return jsonify({"error": "ANTHROPIC_API_KEY未設定"}), 400
    from dashboard.ai import generate_story_content
    d = request.get_json() or {}
    try:
        result = generate_story_content(
            topic=d.get("topic", ""),
            brand=brand_id,
            story_type=d.get("story_type", "promotion"),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/queue/save_reel/<brand_id>", methods=["POST"])
def api_save_reel(brand_id):
    """生成したリール台本をキューに保存"""
    brands = load_brands()
    if brand_id not in brands:
        return jsonify({"error": "Brand not found"}), 404
    d    = request.get_json() or {}
    data = d.get("reel", {})
    ts   = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    entry = {
        "brand": brand_id, "channel": "instagram", "media_type": "reel",
        "title": data.get("title", ""), "caption": data.get("caption", ""),
        "hashtags": data.get("hashtags", ""), "video_url": "",
        "source": "ai_reel", "topic": d.get("topic", ""),
        "filename": f"{ts}_reel.yaml",
        "reel_script": data,
    }
    db.enqueue(entry)
    save_yaml(QUEUE_ROOT / brand_id / "instagram", f"{ts}_reel.yaml", entry)
    db.log_activity("queue_add", brand=brand_id, platform="instagram",
                    detail=f"リール追加: {data.get('title','')}")
    return jsonify({"ok": True})


@app.route("/api/queue/save_story/<brand_id>", methods=["POST"])
def api_save_story(brand_id):
    """生成したストーリーをキューに保存"""
    brands = load_brands()
    if brand_id not in brands:
        return jsonify({"error": "Brand not found"}), 404
    d    = request.get_json() or {}
    data = d.get("story", {})
    ts   = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    entry = {
        "brand": brand_id, "channel": "instagram", "media_type": "story",
        "caption": data.get("caption", ""), "hashtags": data.get("hashtags", ""),
        "source": "ai_story", "topic": d.get("topic", ""),
        "filename": f"{ts}_story.yaml",
        "story_frames": data.get("frames", []),
    }
    db.enqueue(entry)
    save_yaml(QUEUE_ROOT / brand_id / "instagram", f"{ts}_story.yaml", entry)
    db.log_activity("queue_add", brand=brand_id, platform="instagram",
                    detail=f"ストーリー追加: {d.get('topic','')}")
    return jsonify({"ok": True})


@app.route("/webhook", methods=["POST"])
def webhook():
    from sns.line_api import LINEMessenger
    from sales.lead_intake import create_lead_from_line, load_lead_by_line_id
    import yaml as _yaml
    from flask import abort
    scenarios_path = AUTO / "config" / "line_scenarios.yaml"
    messenger = LINEMessenger()
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data()
    if not messenger.verify_signature(body, signature):
        abort(400)
    data = request.get_json()
    scenarios = _yaml.safe_load(scenarios_path.read_text(encoding="utf-8")) if scenarios_path.exists() else {}
    for event in data.get("events", []):
        event_type = event.get("type")
        user_id = event.get("source", {}).get("userId", "")
        if event_type == "follow":
            welcome = scenarios.get("welcome_message", "ご登録ありがとうございます！")
            messenger.push(user_id, welcome)
        elif event_type == "message" and event["message"]["type"] == "text":
            text = event["message"]["text"]
            reply_token = event.get("replyToken", "")
            existing = load_lead_by_line_id(user_id)
            if not existing:
                profile = messenger.get_profile(user_id)
                create_lead_from_line(user_id, profile.get("displayName", ""), text)
            reply = None
            for item in scenarios.get("keyword_replies", []):
                if any(kw in text for kw in item.get("keywords", [])):
                    reply = item["reply"]
                    break
            if reply:
                messenger.reply(reply_token, reply)
            else:
                messenger.reply(reply_token, "メッセージありがとうございます！\n内容を確認して、担当者からご返信します。\n（平日10:00〜17:00 受付）")
    return "OK"


def startup():
    """アプリ起動時の初期化処理（gunicorn 起動時もここで初期化される）"""
    # 必要なディレクトリを作成
    for d in [LEADS_DIR, FINANCE_DIR, PROJECTS_DIR, DECISION_DIR,
              IG_QUEUE, LINE_QUEUE, QUEUE_ROOT, LOGS_DIR, CALENDAR_DIR,
              INBOX_DIR, PROCESSED_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    # DBを初期化
    db.init_db()
    # YAMLデータをDBに移行（初回のみ）
    try:
        migrated = db.migrate_from_yaml()
        if any(v > 0 for v in migrated.values()):
            log.info(f"YAML→DB移行完了: {migrated}")
    except Exception as e:
        log.warning(f"YAML移行スキップ: {e}")
    log.info("✅ ダッシュボード初期化完了")


startup()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(str(AUTO / "logs" / "dashboard.log"), encoding="utf-8"),
        ]
    )
    startup()
    port = int(os.environ.get("PORT", os.environ.get("DASHBOARD_PORT", 8080)))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    print(f"\n✅ ダッシュボード起動: http://localhost:{port}")
    if os.environ.get("DASHBOARD_PASSWORD"):
        print("🔒 認証有効 (DASHBOARD_PASSWORD 設定済み)")
    print()
    app.run(host="0.0.0.0", port=port, debug=debug)
