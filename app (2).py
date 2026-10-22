import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
import aiohttp
from telethon import TelegramClient, events, Button
from telethon.tl import functions, types
from telethon.tl.functions.users import GetFullUserRequest
from telethon.errors import UserNotParticipantError

# ----------------- CONFIG ----------------- #
API_ID = int(os.getenv("API_ID", "27293496"))
API_HASH = os.getenv("API_HASH", "d722d4a9b3a05b313f532762475a421b")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8256234791:AAF9C7vSQdp7bIhf1cCypulEWkxS3bYI4fU")
ADMIN_ID = 8307647862

NOTIFICATION_CHANNEL = "@SrcTgNotificationChannel"
FILE_STORAGE_CHANNEL = "@tgstore_file_storage"   # private channel — bot must be admin
CHANNEL_LINK = "https://t.me/SrcTgNotificationChannel"

DB_FILE = "db.json"
DEFAULT_BANNER = "https://i.etsystatic.com/29790149/r/il/94f53d/3615031331/il_1080xN.3615031331_4ate.jpg"
DEFAULT_QR = "https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=upi://pay?pa=kumarchx@fam%26pn=Store%26cu=INR"

SELLER_TAX = 15.0
MIN_WITHDRAW = 50.0
CHAT_DURATION_MIN = 3
HEART_EFFECT_ID = "5159385139981059251"   # animated heart effect

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ----------------- HELPERS ----------------- #
def now_str():
    return datetime.now().strftime("%d %b %Y, %I:%M %p")

def short_time():
    return datetime.now().strftime("%H:%M")

# ----------------- DATABASE ----------------- #
def default_user(full_name="", username=""):
    return {
        "name": full_name, "username": username or "None",
        "balance": 0.0, "money_used": 0.0, "funds_added": 0.0,
        "purchased_count": 0, "joined_at": now_str(),
        "is_seller": False, "seller_status": "none",
        "seller_since": "", "seller_balance": 0.0,
        "seller_earnings": 0.0, "seller_withdrawn": 0.0,
        "warnings": [], "transactions": [], "purchased_items": [],
        "given_reviews": []           # product ids user has reviewed
    }

def load_db():
    if not os.path.exists(DB_FILE):
        data = {"users": {}, "products": [], "used_txns": [], "withdrawals": [],
                "reports": [], "reviews": [], "offers": []}
        save_db(data)
        return data
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)
        for k in ["users", "products", "used_txns", "withdrawals", "reports", "reviews", "offers"]:
            db.setdefault(k, {} if k == "users" else [])
        return db
    except Exception as e:
        logging.error(f"DB read error: {e}")
        return {"users": {}, "products": [], "used_txns": [], "withdrawals": [],
                "reports": [], "reviews": [], "offers": []}

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_user(user_id, full_name="", username=""):
    db = load_db()
    uid = str(user_id)
    is_new = False
    if uid not in db["users"]:
        is_new = True
        db["users"][uid] = default_user(full_name, username)
        save_db(db)
        return db["users"][uid], is_new
    base = default_user(full_name, username)
    changed = False
    for k, v in base.items():
        if k not in db["users"][uid]:
            db["users"][uid][k] = v
            changed = True
    if changed:
        save_db(db)
    return db["users"][uid], is_new

def update_user(user_id, **kwargs):
    db = load_db()
    uid = str(user_id)
    if uid in db["users"]:
        for k, v in kwargs.items():
            db["users"][uid][k] = v
        save_db(db)

def log_txn(user_id, kind, amount, note=""):
    db = load_db()
    uid = str(user_id)
    if uid in db["users"]:
        db["users"][uid].setdefault("transactions", []).append({
            "type": kind, "amount": amount, "note": note, "time": now_str()
        })
        save_db(db)

# ----------------- TELETHON CLIENT ----------------- #
bot = TelegramClient("bot_session", API_ID, API_HASH).start(bot_token=BOT_TOKEN)
USER_STATES = {}
TEMP_CHATS = {}

# ----------------- FORCE JOIN ----------------- #
async def is_user_joined(user_id):
    try:
        await bot.get_permissions(NOTIFICATION_CHANNEL, user_id)
        return True
    except UserNotParticipantError:
        return False
    except Exception as e:
        logging.warning(f"Join check failed: {e}")
        return True

def join_required_keyboard():
    return [
        [Button.url("📢 Join Channel", CHANNEL_LINK)],
        [Button.inline("✅ I Joined – Verify", data="verify_join")]
    ]

# ----------------- FILE STORAGE ----------------- #
async def upload_to_storage(file_path, caption=""):
    """Upload file to the private storage channel; return file_id."""
    try:
        msg = await bot.send_file(FILE_STORAGE_CHANNEL, file_path, caption=caption)
        return msg.id, msg.document.id if msg.document else (msg.photo.id if msg.photo else None)
    except Exception as e:
        logging.error(f"Storage upload failed: {e}")
        return None, None

async def send_from_storage(chat_id, file_id, caption=""):
    try:
        await bot.send_file(chat_id, file_id, caption=caption)
        return True
    except Exception as e:
        logging.error(f"Send from storage failed: {e}")
        return False

# ----------------- NOTIFICATIONS ----------------- #
async def notify_channel(text, image=None):
    try:
        if image:
            await bot.send_file(NOTIFICATION_CHANNEL, image, caption=text)
        else:
            await bot.send_message(NOTIFICATION_CHANNEL, text)
    except Exception as e:
        logging.error(f"Channel notify failed: {e}")

async def notify_admin(text):
    try:
        await bot.send_message(ADMIN_ID, text)
    except Exception as e:
        logging.error(f"Admin notify failed: {e}")

async def react_message(chat_id, message_id, emoji="🔥", custom_emoji_id=None, big=False):
    """
    Set a message reaction (MTProto messages.sendReaction / Bot API setMessageReaction,
    added Bot API 7.0). Pass custom_emoji_id (a Premium custom-emoji document id) to
    react with a Premium emoji instead of a plain unicode one — to find a document id,
    send yourself the emoji you want in an official client, then read message.entities
    with Telethon. Falls back to the plain `emoji` automatically if the custom emoji
    reaction is rejected (e.g. chat doesn't allow Premium reactions).
    """
    reaction = ([types.ReactionCustomEmoji(document_id=int(custom_emoji_id))]
                if custom_emoji_id else [types.ReactionEmoji(emoticon=emoji)])
    try:
        await bot(functions.messages.SendReactionRequest(
            peer=chat_id, msg_id=message_id, reaction=reaction, big=big
        ))
    except Exception as e:
        if custom_emoji_id:
            logging.warning(f"Custom emoji reaction failed, falling back to plain emoji: {e}")
            try:
                await bot(functions.messages.SendReactionRequest(
                    peer=chat_id, msg_id=message_id,
                    reaction=[types.ReactionEmoji(emoticon=emoji)], big=big
                ))
            except Exception as e2:
                logging.warning(f"Reaction fallback also failed: {e2}")
        else:
            logging.warning(f"Reaction failed: {e}")

# ----------------- PREMIUM EMOJI TEXT ----------------- #
def premium_emoji_text(placeholder, document_id):
    """
    Build (text, entities) to render one Premium custom emoji inline in a message.
    `placeholder` must be the real fallback unicode emoji (e.g. "🔥") — Telegram overlays
    `document_id`'s custom emoji on top of it. This only renders as the Premium emoji if
    the bot's linked account has Telegram Premium (Bot API 9.4); otherwise the plain
    placeholder emoji is shown, so it always degrades safely. Concatenate the returned
    text/entities into a bigger message by offsetting entity positions yourself.
    """
    return placeholder, [types.MessageEntityCustomEmoji(0, len(placeholder), int(document_id))]

# ----------------- RICH MESSAGE (Bot API 10.1+, HTTP-only, no TL yet) ----------------- #
BOT_API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

async def send_rich_message(chat_id, markdown_text, inline_keyboard=None):
    """
    Send a structured Rich Message via sendRichMessage (added Bot API 10.1, June 2026).
    Telethon is an MTProto client and has no TL wrapper for this Bot-API-only method,
    so this calls the HTTP Bot API directly with the same BOT_TOKEN via aiohttp (already
    imported). Uses InputRichMessage's `markdown` field (plain formatted text) rather
    than the newer structured `blocks` field — the per-block JSON schema (RichBlockParagraph,
    RichBlockSectionHeading, etc.) is too new/undocumented in field-level detail to hardcode
    reliably; `markdown` covers headings/dividers/bold text fine via normal Markdown syntax.
    Falls back to a normal text message on any failure (old server, feature not yet on this
    bot, etc.) so the bot never breaks because of it.
    """
    payload = {"chat_id": chat_id, "rich_message": {"markdown": markdown_text}}
    if inline_keyboard:
        payload["reply_markup"] = {"inline_keyboard": inline_keyboard}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{BOT_API_BASE}/sendRichMessage", json=payload, timeout=10) as resp:
                data = await resp.json()
                if not data.get("ok"):
                    raise RuntimeError(data.get("description", "unknown sendRichMessage error"))
                return data["result"]
    except Exception as e:
        logging.warning(f"sendRichMessage failed, falling back to plain message: {e}")
        try:
            await bot.send_message(chat_id, markdown_text, parse_mode="markdown")
        except Exception as e2:
            logging.error(f"Rich message fallback also failed: {e2}")
        return None

# ----------------- KEYBOARDS (colored buttons) ----------------- #
COPY_BUTTON_SUPPORTED = hasattr(types, "KeyboardButtonCopy")
if not COPY_BUTTON_SUPPORTED:
    logging.warning(
        "telethon.tl.types.KeyboardButtonCopy not found — your installed Telethon "
        "predates TL layer 188 / Bot API 7.11 support for it. Run "
        "`pip install -U telethon` for a real one-tap clipboard button; falling "
        "back to an alert-popup copy button in the meantime."
    )

def copy_button(text, copy_text):
    """
    Raw TL clipboard button (real one-tap copy-to-clipboard). Requires a Telethon
    build that has KeyboardButtonCopy in its generated schema — if not, transparently
    falls back to a normal callback button that shows the text in a tap alert instead,
    so the bot never crashes on older installs (see the "copyfallback_" branch below).
    """
    if COPY_BUTTON_SUPPORTED:
        return types.KeyboardButtonCopy(text=text, copy_text=copy_text)
    return Button.inline(text, data=f"copyfallback_{copy_text}")

def build_markup(rows):
    """
    Wrap rows into a ReplyInlineMarkup manually — needed when a real KeyboardButtonCopy
    is mixed in, since Telethon's auto-detection (build_reply_markup -> Button._is_inline)
    doesn't recognise it as inline (see LonamiWebs/Telethon#4588). In fallback mode every
    button is already a plain Button.inline(), which Telethon handles natively either way.
    """
    if COPY_BUTTON_SUPPORTED:
        return types.ReplyInlineMarkup([types.KeyboardButtonRow(row) for row in rows])
    return rows

def main_menu_keyboard(first_name):
    return [
        [Button.inline(f"👤 {first_name}", data="profile_self", style="primary")],
        [Button.inline("🪎 Balance", data="view_balance", style="success"),
         Button.inline("👤 Profile", data="view_profile", style="primary")],
        [Button.inline("🪙 Earn", data="view_earn"),
         Button.inline("🏪 Store", data="view_store", style="primary"),
         Button.inline("💳 Deposit", data="view_deposit", style="success")],
        [Button.inline("📊 Dashboard", data="view_dashboard", style="primary"),
         Button.inline("📞 Contact", data="view_contact")],
        [Button.url("📢 Updates", CHANNEL_LINK)]
    ]

def back_keyboard():
    return [[Button.inline("🔙 Back", data="back_home", style="primary")]]

def profile_keyboard(uid, first_name, user):
    btn = [
        [Button.inline(first_name, data="profile_self", style="primary")],
        [Button.inline(f"Balance: ₹{user['balance']:.2f}", data="view_balance", style="success"),
         Button.inline("🪙 Earn", data="view_earn")],
        [Button.inline("📁 My SRCs", data="my_srcs", style="primary"),
         Button.inline("📜 Transactions", data="my_txns")],
        [Button.inline("⭐ My Reviews", data="my_reviews", style="primary")],
    ]
    if uid == ADMIN_ID:
        btn.append([Button.inline("👑 Admin Panel", data="admin_home", style="danger")])
    elif user.get("seller_status") == "approved":
        btn.append([Button.inline("🏪 Seller Panel", data="seller_home", style="success")])
    elif user.get("seller_status") == "pending":
        btn.append([Button.inline("⏳ Seller Pending", data="seller_pending")])
    else:
        btn.append([Button.inline("🏪 Become a Seller", data="seller_become", style="primary")])
    btn.append([Button.inline("🔙 Back", data="back_home")])
    return btn

# ================================================================
#                     START HANDLER (with heart effect + rich)
# ================================================================
@bot.on(events.NewMessage(pattern=r"^/start"))
async def start_handler(event):
    sender = await event.get_sender()
    first_name = sender.first_name or "User"
    full_name = f"{first_name} {sender.last_name or ''}".strip()
    username = f"@{sender.username}" if sender.username else "No Username"

    user_data, is_new = get_user(sender.id, full_name, username)

    if not await is_user_joined(sender.id):
        await event.respond(
            "🚫 **Access Denied!**\n\nJoin our channel first.",
            buttons=join_required_keyboard()
        )
        return

    if is_new:
        db = load_db()
        await notify_admin(
            f"🎉 **New User**\n• {full_name}\n• {username}\n• `{sender.id}`\n\n"
            f"👥 Total: `{len(db['users'])}`"
        )

    # animated heart effect welcome
    msg = await event.respond("🚀")
    await asyncio.sleep(0.5)
    for s in ["▰▱▱▱▱▱▱▱▱ 15%", "▰▰▰▱▱▱▱▱▱ 40%", "▰▰▰▰▰▰▱▱▱ 70%",
              "▰▰▰▰▰▰▰▰▰ 100%"]:
        try:
            await msg.edit(s)
            await asyncio.sleep(0.25)
        except Exception:
            pass
    await msg.delete()

    welcome_text = (
        f"╭━━━ ✦ WELCOME ✦ ━━━╮\n"
        f"  Hey **{first_name}** 👋\n"
        f"╰━━━━━━━━━━━━━━━━━━╯\n\n"
        f"🏪 **Digital Marketplace** — Buy & Sell SRCs instantly!\n\n"
        f"• 🛒 Browse the store\n• 💰 Deposit funds\n"
        f"• 🏪 Become a seller\n• 📞 24/7 Support\n\n"
        f"☘️ Use the buttons below."
    )
    # send with heart effect via raw API
    menu_msg = await event.respond(welcome_text, buttons=main_menu_keyboard(first_name),
                                   file=DEFAULT_BANNER)
    # "mast" reaction whenever the main menu shows — swap emoji="⭐" for
    # custom_emoji_id="<document_id>" once you have a Premium emoji id to use
    await react_message(event.chat_id, menu_msg.id, emoji="🔥", big=True)

# ================================================================
#              VERIFY JOIN
# ================================================================
@bot.on(events.CallbackQuery(data="verify_join"))
async def verify_join_handler(event):
    sender = await event.get_sender()
    if await is_user_joined(sender.id):
        await event.answer("✅ Verified!")
        first_name = sender.first_name or "User"
        try:
            await event.edit(
                f"╭━━━ ✦ WELCOME ✦ ━━━╮\n  Hey **{first_name}** 👋\n╰━━━━━━━━━━━━━━━━━━╯\n\n"
                f"🏪 **Digital Marketplace**\n☘️ Explore below.",
                buttons=main_menu_keyboard(first_name)
            )
            await react_message(event.chat_id, event.message_id, emoji="🔥", big=True)
        except Exception:
            pass
    else:
        await event.answer("❌ Join the channel first!", alert=True)

# ================================================================
#                     CALLBACK HANDLER (edit instead of delete)
# ================================================================
@bot.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode("utf-8")
    sender = await event.get_sender()
    first_name = sender.first_name or "User"
    full_name = f"{first_name} {sender.last_name or ''}".strip()
    uid = sender.id

    # ---------- COPY BUTTON FALLBACK (old Telethon without KeyboardButtonCopy) ---------- #
    if data.startswith("copyfallback_"):
        value = data[len("copyfallback_"):]
        await event.answer(f"📋 {value}\n\n(Tap-and-hold the text above to copy it manually.)",
                           alert=True)
        return

    if data != "verify_join" and not await is_user_joined(uid):
        await event.answer("🚫 Join the channel first!", alert=True)
        try:
            await event.edit("🚫 **Access Denied!**\nJoin the channel.",
                             buttons=join_required_keyboard())
        except Exception:
            pass
        return

    user, _ = get_user(uid, full_name)

    # ---------- BACK HOME ---------- #
    if data in ("back_home", "open_menu"):
        welcome_text = (
            f"╭━━━ ✦ WELCOME ✦ ━━━╮\n  Hey **{first_name}** 👋\n╰━━━━━━━━━━━━━━━━━━╯\n\n"
            f"🏪 **Digital Marketplace**\n☘️ Explore below."
        )
        try:
            await event.edit(welcome_text, buttons=main_menu_keyboard(first_name))
            await react_message(event.chat_id, event.message_id, emoji="🔥", big=True)
        except Exception:
            sent = await event.respond(welcome_text, buttons=main_menu_keyboard(first_name))
            await react_message(event.chat_id, sent.id, emoji="🔥", big=True)
        return

    # ---------- DASHBOARD (Rich Message demo) ---------- #
    if data == "view_dashboard":
        dashboard_md = (
            f"👋 *Welcome back, {first_name}!*\n\n"
            f"### Dashboard\n\n"
            f"💰 Balance: ₹{user['balance']:.2f}\n"
            f"📦 Orders: {user.get('purchased_count', 0)}\n"
            f"🟢 Status: Active\n\n"
            f"---\n"
            f"Choose an option below:"
        )
        inline_kb = [[{"text": "🔙 Home", "callback_data": "back_home"}]]
        try:
            await event.answer()
        except Exception:
            pass
        await send_rich_message(event.chat_id, dashboard_md, inline_keyboard=inline_kb)
        return

    # ---------- BALANCE ---------- #
    if data == "view_balance":
        text = (
            f"╭──── 💰 BALANCE ────╮\n"
            f"👤 {user['name']}\n"
            f"💰 Balance      : **₹{user['balance']:.2f}**\n"
            f"💳 Spent        : ₹{user['money_used']:.2f}\n"
            f"🪙 Total Added  : ₹{user['funds_added']:.2f}\n"
            f"╰───────────────────╯"
        )
        try:
            await event.edit(text, buttons=[
                [Button.inline("🪙 Earn", data="view_earn"), Button.inline("💳 Deposit", data="view_deposit", style="success")],
                [Button.inline("🔙 Back", data="back_home")]
            ])
        except Exception:
            pass
        return

    # ---------- PROFILE ---------- #
    if data in ("view_profile", "profile_self"):
        try:
            full_user = await bot(GetFullUserRequest(uid))
            bio = full_user.about if full_user.about else "None"
        except Exception:
            bio = "None"

        seller_tag = ""
        if user.get("seller_status") == "approved":
            seller_tag = "🏪 Verified Seller"
        elif user.get("seller_status") == "pending":
            seller_tag = "⏳ Pending Seller"

        profile_text = (
            f"╭──── 👤 PROFILE ────╮\n"
            f"• Name     : {user['name']}\n"
            f"• User ID  : `{uid}`\n"
            f"• Bio      : {bio}\n"
            f"• Balance  : ₹{user['balance']:.2f}\n"
            f"• Purchased : {user['purchased_count']}\n"
            + (f"• Status   : {seller_tag}\n" if seller_tag else "") +
            f"╰───────────────────╯\n"
            f"📅 Joined: {user['joined_at']}"
        )
        try:
            await event.edit(profile_text, buttons=profile_keyboard(uid, first_name, user))
        except Exception:
            pass
        return

    # ---------- MY SRCs ---------- #
    if data == "my_srcs":
        db = load_db()
        purchased = user.get("purchased_items", [])
        if not purchased:
            try:
                await event.edit("📁 No SRCs purchased yet.",
                                 buttons=[[Button.inline("🏪 Store", data="view_store", style="primary")],
                                          [Button.inline("🔙 Back", data="view_profile")]])
            except Exception:
                pass
            return
        try:
            await event.edit(f"📁 **My SRCs** ({len(purchased)}) — click below to re-download:",
                             buttons=[[Button.inline("📥 Re-download", data="redeliver_list")],
                                      [Button.inline("🔙 Back", data="view_profile")]])
        except Exception:
            pass
        return

    if data == "redeliver_list":
        db = load_db()
        purchased = user.get("purchased_items", [])
        for pid in purchased:
            p = next((x for x in db["products"] if str(x["id"]) == str(pid)), None)
            if not p:
                continue
            txt = f"📦 **{p['name']}**\n💵 ₹{p['price']}\n📝 {p['desc']}"
            btns = [[Button.inline("📥 Get File", data=f"redeliver_{pid}", style="success")],
                    [Button.inline("⭐ Review", data=f"review_{pid}"),
                     Button.inline("🚩 Report", data=f"report_{pid}", style="danger")]]
            try:
                await bot.send_file(uid, p.get("storage_file_id") or DEFAULT_BANNER,
                                    caption=txt, buttons=btns)
            except Exception:
                await bot.send_message(uid, txt, buttons=btns)
        return

    if data.startswith("redeliver_"):
        pid = data.split("_")[1]
        db = load_db()
        p = next((x for x in db["products"] if str(x["id"]) == str(pid)), None)
        if not p:
            await event.answer("Product not found!", alert=True)
            return
        if str(pid) not in [str(x) for x in user.get("purchased_items", [])]:
            await event.answer("Not purchased!", alert=True)
            return
        fid = p.get("storage_file_id")
        if fid:
            ok = await send_from_storage(uid, fid, caption=f"📁 **{p['name']}**")
            await event.answer("File sent!" if ok else "Send failed.", alert=not ok)
        else:
            await bot.send_message(uid, f"📦 Content:\n`{p.get('content','N/A')}`")
        return

    # ---------- MY REVIEWS ---------- #
    if data == "my_reviews":
        db = load_db()
        mine = [r for r in db.get("reviews", []) if str(r["user_id"]) == str(uid)]
        if not mine:
            try:
                await event.edit("⭐ You haven't given any reviews yet.",
                                 buttons=[[Button.inline("🔙 Back", data="view_profile")]])
            except Exception:
                pass
            return
        txt = "⭐ **Your Reviews**\n━━━━━━━━━━━━━━━━\n"
        for r in mine[-10:]:
            stars = "⭐" * r["rating"]
            txt += f"{stars} — **{r['product_name']}**\n  └ _{r['text'][:80]}_\n  └ {r['time']}\n\n"
        try:
            await event.edit(txt, buttons=[[Button.inline("🔙 Back", data="view_profile")]])
        except Exception:
            pass
        return

    # ---------- MY TRANSACTIONS ---------- #
    if data == "my_txns":
        txns = user.get("transactions", [])[-20:]
        if not txns:
            txt = "📜 No transactions."
        else:
            txt = "📜 **Recent Transactions**\n━━━━━━━━━━━━━━━━\n"
            for t in reversed(txns):
                sign = "➕" if t["amount"] > 0 else "➖"
                txt += f"{sign} ₹{abs(t['amount']):.2f} | {t['type']}\n  └ {t.get('note','')}\n"
        try:
            await event.edit(txt, buttons=[[Button.inline("🔙 Back", data="view_profile")]])
        except Exception:
            pass
        return

    # ---------- DEPOSIT (with copy button for UPI) ---------- #
    if data == "view_deposit":
        deposit_text = (
            "╭──── 💳 DEPOSIT ────╮\n\n"
            "1️⃣ Pay to UPI:\n"
            "   `kumarchx@fam`\n\n"
            "2️⃣ Copy the **TXN ID / UTR**\n\n"
            "3️⃣ Send it here — auto-verified.\n"
            "╰────────────────────╯"
        )
        buttons = build_markup([
            [copy_button("📋 Copy UPI ID", "kumarchx@fam")],
            [Button.inline("🪎 Balance", data="view_balance"),
             Button.inline("🔙 Back", data="back_home")]
        ])
        try:
            await event.edit(deposit_text, buttons=buttons)
        except Exception:
            pass
        return

    # ---------- EARN ---------- #
    if data == "view_earn":
        try:
            await event.edit("⚠️ Coming soon in the next update!",
                             buttons=back_keyboard())
        except Exception:
            pass
        return

    # ---------- CONTACT ---------- #
    if data == "view_contact":
        USER_STATES[uid] = {"action": "awaiting_support_message"}
        try:
            await event.edit("📞 **Contact Support**\n\nType your query below:",
                             buttons=back_keyboard())
        except Exception:
            pass
        return

    # ============================================================
    #                     STORE (with reviews + chat before buy)
    # ============================================================
    if data == "view_store":
        db = load_db()
        products = db["products"]
        if not products:
            try:
                await event.edit("🏪 Store is empty.",
                                 buttons=[[Button.inline("🔙 Back", data="back_home")]])
            except Exception:
                pass
            return
        # Show list first
        buttons = []
        for p in products[:8]:
            buttons.append([Button.inline(
                f"🏷️ {p['name']} — ₹{p['price']}",
                data=f"open_{p['id']}", style="primary"
            )])
        buttons.append([Button.inline("🔙 Back", data="back_home")])
        try:
            await event.edit("🏪 **Store** — pick a product:", buttons=buttons)
        except Exception:
            pass
        return

    if data.startswith("open_"):
        prod_id = data.split("_", 1)[1]
        db = load_db()
        p = next((x for x in db["products"] if str(x["id"]) == prod_id), None)
        if not p:
            await event.answer("Missing!", alert=True)
            return

        seller_display = p.get("seller_display", "anonymous")
        seller_label = "anonymous" if seller_display == "anonymous" else f"@{seller_display.lstrip('@')}"
        already = str(p["id"]) in [str(x) for x in user.get("purchased_items", [])]

        # average rating
        revs = [r for r in db.get("reviews", []) if str(r["product_id"]) == str(p["id"])]
        if revs:
            avg = sum(r["rating"] for r in revs) / len(revs)
            rating_line = f"⭐ {avg:.1f}/5  ({len(revs)} reviews)"
        else:
            rating_line = "⭐ No reviews yet"

        p_text = (
            f"╭─── 🛍️ PRODUCT ───╮\n"
            f"🏷️ **{p['name']}**\n"
            f"💵 ₹{p['price']}\n"
            f"👤 Seller: {seller_label}\n"
            f"{rating_line}\n"
            f"📝 {p['desc']}\n"
            f"╰────────────────╯"
        )

        btns = []
        if already:
            btns.append([Button.inline("✅ Already Bought", data="noop", style="success")])
            btns.append([Button.inline("📁 My SRCs", data="my_srcs"),
                         Button.inline("💬 Chat Seller", data=f"chat_{p['id']}")])
            btns.append([Button.inline("⭐ Review", data=f"review_{p['id']}"),
                         Button.inline("🚩 Report", data=f"report_{p['id']}", style="danger")])
        else:
            btns.append([Button.inline("🧾 Buy Now", data=f"buy_{p['id']}", style="success")])
            btns.append([Button.inline("💰 Make Offer", data=f"offer_{p['id']}", style="primary"),
                         Button.inline("💬 Chat Seller", data=f"chat_{p['id']}")])
            btns.append([Button.inline("⭐ Reviews", data=f"view_reviews_{p['id']}"),
                         Button.inline("🚩 Report", data=f"report_{p['id']}", style="danger")])
        btns.append([Button.inline("🔙 Store", data="view_store")])

        try:
            await event.edit(p_text, buttons=btns)
        except Exception:
            pass
        return

    if data.startswith("view_reviews_"):
        pid = data.split("_")[2]
        db = load_db()
        revs = [r for r in db.get("reviews", []) if str(r["product_id"]) == str(pid)]
        if not revs:
            try:
                await event.edit("⭐ No reviews yet. Be the first!",
                                 buttons=[[Button.inline("🔙 Back", data=f"open_{pid}")]])
            except Exception:
                pass
            return
        txt = f"⭐ **Reviews** ({len(revs)})\n━━━━━━━━━━━━━━━━\n"
        for r in revs[-10:]:
            txt += f"{'⭐'*r['rating']} — {r['user_name']}\n  └ _{r['text'][:120]}_\n\n"
        try:
            await event.edit(txt, buttons=[[Button.inline("🔙 Back", data=f"open_{pid}")]])
        except Exception:
            pass
        return

    # ============================================================
    #                       BUY FLOW
    # ============================================================
    if data.startswith("buy_"):
        prod_id = data.split("_", 1)[1]
        db = load_db()
        product = next((p for p in db["products"] if str(p["id"]) == prod_id), None)
        if not product:
            await event.answer("❌ Not found!", alert=True)
            return
        if str(prod_id) in [str(x) for x in user.get("purchased_items", [])]:
            await event.answer("✅ Already purchased!", alert=True)
            return
        price = float(product["price"])
        if user["balance"] < price:
            await event.answer("⚠️ Insufficient balance!", alert=True)
            return

        new_balance = user["balance"] - price
        update_user(uid, balance=new_balance,
                    money_used=user["money_used"] + price,
                    purchased_count=user["purchased_count"] + 1,
                    purchased_items=user.get("purchased_items", []) + [int(prod_id)])
        log_txn(uid, "purchase", -price, f"Bought {product['name']}")

        seller_id = product.get("seller_id", "admin")
        if seller_id != "admin":
            s_db = load_db()
            if str(seller_id) in s_db["users"]:
                s = s_db["users"][str(seller_id)]
                share = max(0.0, price - SELLER_TAX)
                s["seller_balance"] = s.get("seller_balance", 0.0) + share
                s["seller_earnings"] = s.get("seller_earnings", 0.0) + share
                s.setdefault("transactions", []).append({
                    "type": "sale", "amount": share,
                    "note": f"Sold {product['name']} (Tax ₹{SELLER_TAX})",
                    "time": now_str()
                })
                save_db(s_db)
                try:
                    await bot.send_message(int(seller_id),
                        f"💰 **Sale!** {product['name']}\n+ ₹{share} (after ₹{SELLER_TAX} tax)")
                except Exception:
                    pass

        # deliver
        try:
            await event.edit(
                f"✅ **Purchased!**\n\n📦 **{product['name']}**\n💰 ₹{price}\n\n"
                f"🔗 `{product.get('content','Delivered')}`",
                buttons=[[Button.inline("⭐ Leave Review", data=f"review_{prod_id}", style="success")],
                         [Button.inline("📁 My SRCs", data="my_srcs"),
                          Button.inline("🔙 Home", data="back_home")]]
            )
        except Exception:
            pass

        fid = product.get("storage_file_id")
        if fid:
            await send_from_storage(uid, fid, caption=f"📁 **{product['name']}**")

        await event.answer("Purchased!")
        await notify_channel(
            f"🎉 **New Purchase!**\n📦 {product['name']}\n💵 ₹{price}\n👤 {first_name}\n🕒 {short_time()}"
        )
        return

    # ============================================================
    #                  PRICE NEGOTIATION (NEW)
    # ============================================================
    if data.startswith("offer_"):
        pid = data.split("_")[1]
        db = load_db()
        p = next((x for x in db["products"] if str(x["id"]) == pid), None)
        if not p:
            await event.answer("Missing!", alert=True)
            return
        if str(pid) in [str(x) for x in user.get("purchased_items", [])]:
            await event.answer("Already bought!", alert=True)
            return
        USER_STATES[uid] = {"action": "awaiting_offer_amount", "pid": pid}
        try:
            await event.edit(
                f"💰 **Make an Offer**\n\n"
                f"Product: **{p['name']}**\n"
                f"Listed Price: ₹{p['price']}\n\n"
                f"Type your offer amount (₹):",
                buttons=[[Button.inline("❌ Cancel", data=f"open_{pid}", style="danger")]]
            )
        except Exception:
            pass
        return

    if data.startswith("offer_accept_"):
        oid = data.split("_")[2]
        db = load_db()
        offer = next((o for o in db.get("offers", []) if str(o["id"]) == oid), None)
        if not offer or offer["status"] != "pending":
            await event.answer("Offer already processed!", alert=True)
            return
        if str(offer["seller_id"]) != str(uid) and uid != ADMIN_ID:
            await event.answer("Not your offer!", alert=True)
            return
        offer["status"] = "accepted"
        offer["processed_at"] = now_str()
        save_db(db)
        # notify buyer
        buyer_id = int(offer["buyer_id"])
        try:
            await bot.send_message(
                buyer_id,
                f"✅ **Offer Accepted!**\n\n"
                f"📦 {offer['product_name']}\n"
                f"💰 Your offer: ₹{offer['amount']}\n\n"
                f"Tap below to buy at this price.",
                buttons=[[Button.inline("🧾 Buy Now", data=f"buy_offer_{offer['id']}", style="success")]]
            )
        except Exception:
            pass
        await event.edit(f"✅ Offer accepted for ₹{offer['amount']:.2f}")
        return

    if data.startswith("offer_reject_"):
        oid = data.split("_")[2]
        db = load_db()
        offer = next((o for o in db.get("offers", []) if str(o["id"]) == oid), None)
        if not offer or offer["status"] != "pending":
            await event.answer("Already processed!", alert=True)
            return
        if str(offer["seller_id"]) != str(uid) and uid != ADMIN_ID:
            await event.answer("Not your offer!", alert=True)
            return
        offer["status"] = "rejected"
        offer["processed_at"] = now_str()
        save_db(db)
        try:
            await bot.send_message(int(offer["buyer_id"]),
                f"❌ Seller rejected your offer of ₹{offer['amount']:.2f}.")
        except Exception:
            pass
        await event.edit(f"❌ Offer rejected.")
        return

    if data.startswith("buy_offer_"):
        oid = data.split("_")[2]
        db = load_db()
        offer = next((o for o in db.get("offers", []) if str(o["id"]) == oid), None)
        if not offer or offer["status"] != "accepted":
            await event.answer("Offer not valid!", alert=True)
            return
        if str(offer["buyer_id"]) != str(uid):
            await event.answer("Not your offer!", alert=True)
            return
        # reuse buy flow with negotiated price
        user, _ = get_user(uid, full_name)
        amount = offer["amount"]
        if user["balance"] < amount:
            await event.answer("⚠️ Insufficient balance!", alert=True)
            return
        update_user(uid, balance=user["balance"] - amount,
                    money_used=user["money_used"] + amount,
                    purchased_count=user["purchased_count"] + 1,
                    purchased_items=user.get("purchased_items", []) + [int(offer["product_id"])])
        log_txn(uid, "purchase_offer", -amount, f"Bought {offer['product_name']} via offer")
        seller_id = offer["seller_id"]
        if seller_id != "admin":
            s_db = load_db()
            if str(seller_id) in s_db["users"]:
                s = s_db["users"][str(seller_id)]
                share = max(0.0, amount - SELLER_TAX)
                s["seller_balance"] = s.get("seller_balance", 0.0) + share
                s["seller_earnings"] = s.get("seller_earnings", 0.0) + share
                save_db(s_db)
        db = load_db()
        p = next((x for x in db["products"] if str(x["id"]) == str(offer["product_id"])), None)
        try:
            await event.edit(f"✅ **Purchased!** {offer['product_name']} at ₹{amount:.2f}",
                             buttons=[[Button.inline("🔙 Home", data="back_home")]])
        except Exception:
            pass
        if p and p.get("storage_file_id"):
            await send_from_storage(uid, p["storage_file_id"], caption=f"📁 {offer['product_name']}")
        return

    # ============================================================
    #                     REVIEWS (NEW)
    # ============================================================
    if data.startswith("review_"):
        pid = data.split("_")[1]
        if str(pid) not in [str(x) for x in user.get("purchased_items", [])]:
            await event.answer("Buy the product first!", alert=True)
            return
        if str(pid) in [str(x) for x in user.get("given_reviews", [])]:
            await event.answer("Already reviewed!", alert=True)
            return
        db = load_db()
        p = next((x for x in db["products"] if str(x["id"]) == pid), None)
        if not p:
            await event.answer("Missing!", alert=True)
            return
        USER_STATES[uid] = {"action": "awaiting_review", "pid": pid, "rating": 0}
        buttons = [
            [Button.inline("⭐1", data=f"rate_1_{pid}", style="danger"),
             Button.inline("⭐2", data=f"rate_2_{pid}", style="danger"),
             Button.inline("⭐3", data=f"rate_3_{pid}", style="primary")],
            [Button.inline("⭐4", data=f"rate_4_{pid}", style="success"),
             Button.inline("⭐5", data=f"rate_5_{pid}", style="success")],
            [Button.inline("❌ Cancel", data=f"open_{pid}", style="danger")]
        ]
        try:
            await event.edit(f"⭐ **Review {p['name']}**\n\nPick a rating:",
                             buttons=buttons)
        except Exception:
            pass
        return

    if data.startswith("rate_"):
        parts = data.split("_")
        rating = int(parts[1])
        pid = parts[2]
        state = USER_STATES.get(uid, {})
        if state.get("action") != "awaiting_review":
            await event.answer("Session expired!", alert=True)
            return
        state["rating"] = rating
        USER_STATES[uid] = state
        try:
            await event.edit(
                f"⭐ You picked {rating}/5.\n\nNow type your review text:",
                buttons=[[Button.inline("❌ Cancel", data=f"open_{pid}", style="danger")]]
            )
        except Exception:
            pass
        return

    # ============================================================
    #                  TEMP CHAT WITH SELLER (before buy too)
    # ============================================================
    if data.startswith("chat_"):
        prod_id = data.split("_", 1)[1]
        db = load_db()
        product = next((p for p in db["products"] if str(p["id"]) == prod_id), None)
        if not product:
            await event.answer("Product missing!", alert=True)
            return
        seller_id = product.get("seller_id", "admin")
        if seller_id == "admin":
            await event.answer("No seller to chat with.", alert=True)
            return
        if str(seller_id) == str(uid):
            await event.answer("You are the seller!", alert=True)
            return

        # allow chat even before buying
        try:
            await bot.send_message(
                int(seller_id),
                f"💬 **Chat Request**\n\n"
                f"{first_name} wants to discuss **{product['name']}**.\n"
                f"Session: **{CHAT_DURATION_MIN} min**.",
                buttons=[[
                    Button.inline("✅ Accept", data=f"accept_chat_{uid}_{prod_id}", style="success"),
                    Button.inline("❌ Reject", data=f"reject_chat_{uid}", style="danger")
                ]]
            )
            await event.answer("Request sent to seller!", alert=True)
        except Exception as e:
            await event.answer(f"Couldn't reach seller: {e}", alert=True)
        return

    if data.startswith("accept_chat_"):
        parts = data.split("_")
        buyer_id = int(parts[2])
        prod_id = parts[3]
        db = load_db()
        product = next((p for p in db["products"] if str(p["id"]) == prod_id), None)
        pname = product["name"] if product else "product"
        expires = datetime.now() + timedelta(minutes=CHAT_DURATION_MIN)
        TEMP_CHATS[uid] = {"partner": buyer_id, "expires": expires, "product": pname}
        TEMP_CHATS[buyer_id] = {"partner": uid, "expires": expires, "product": pname}
        try:
            await event.edit(f"✅ Chat accepted! Active for {CHAT_DURATION_MIN} min.")
        except Exception:
            pass
        try:
            await bot.send_message(buyer_id,
                f"✅ **Chat started** — {CHAT_DURATION_MIN} minutes.\n"
                f"Just type messages. Use `/endchat` to end.")
        except Exception:
            pass
        return

    if data.startswith("reject_chat_"):
        buyer_id = int(data.split("_")[2])
        try:
            await event.edit("❌ Chat rejected.")
        except Exception:
            pass
        try:
            await bot.send_message(buyer_id, "❌ Seller rejected your chat request.")
        except Exception:
            pass
        return

    # ============================================================
    #                     REPORT
    # ============================================================
    if data.startswith("report_"):
        pid = data.split("_")[1]
        USER_STATES[uid] = {"action": "report_reason", "pid": pid}
        try:
            await event.edit("🚩 **Report this SRC**\n\nDescribe the issue:",
                             buttons=[[Button.inline("❌ Cancel", data=f"open_{pid}", style="danger")]])
        except Exception:
            pass
        return

    # ============================================================
    #                     SELLER SECTION
    # ============================================================
    if data == "seller_become":
        if user.get("seller_status") == "approved":
            await event.answer("Already a seller!", alert=True)
            return
        if user.get("seller_status") == "pending":
            await event.answer("Pending approval.", alert=True)
            return
        try:
            await event.edit(
                "🏪 **Become a Seller**\n\n"
                f"📌 Tax: ₹{SELLER_TAX:.0f} per sale\n"
                f"📌 Min withdrawal: ₹{MIN_WITHDRAW:.0f}\n"
                f"📌 Admin approval required\n\nSend request?",
                buttons=[[Button.inline("✅ Send", data="seller_send_req", style="success"),
                          Button.inline("❌ Cancel", data="back_home", style="danger")]]
            )
        except Exception:
            pass
        return

    if data == "seller_send_req":
        update_user(uid, seller_status="pending")
        try:
            await event.edit("✅ Request sent! Wait for approval.", buttons=back_keyboard())
        except Exception:
            pass
        await notify_admin(f"🏪 Seller Request\n• {full_name}\n• `{uid}`")
        try:
            await bot.send_message(ADMIN_ID, "Approve?",
                buttons=[[Button.inline("✅ Approve", data=f"admin_sr_ok_{uid}", style="success"),
                          Button.inline("❌ Reject", data=f"admin_sr_no_{uid}", style="danger")]])
        except Exception:
            pass
        return

    if data == "seller_pending":
        await event.answer("⏳ Pending approval.", alert=True)
        return

    if data == "seller_home":
        if user.get("seller_status") != "approved":
            await event.answer("Not a seller!", alert=True)
            return
        text = (
            f"╭──── 🏪 SELLER ────╮\n"
            f"👤 {user['name']}\n"
            f"💰 Balance   : ₹{user.get('seller_balance',0):.2f}\n"
            f"📈 Earnings  : ₹{user.get('seller_earnings',0):.2f}\n"
            f"💸 Withdrawn : ₹{user.get('seller_withdrawn',0):.2f}\n"
            f"🧾 Tax/sale  : ₹{SELLER_TAX:.0f}\n"
            f"╰─────────────────╯"
        )
        try:
            await event.edit(text, buttons=[
                [Button.inline("➕ Add Product", data="seller_add_product", style="success"),
                 Button.inline("📦 My Products", data="seller_my_products")],
                [Button.inline("💰 Funds", data="seller_funds"),
                 Button.inline("💸 Withdraw", data="seller_withdraw", style="primary")],
                [Button.inline("🔙 Back", data="back_home")]
            ])
        except Exception:
            pass
        return

    if data == "seller_add_product":
        if user.get("seller_status") != "approved":
            return
        USER_STATES[uid] = {"action": "sell_item_image", "item_data": {}}
        try:
            await event.edit("📸 Send **Product Image** (Photo or URL):",
                             buttons=[[Button.inline("❌ Cancel", data="seller_home", style="danger")]])
        except Exception:
            pass
        return

    if data == "seller_my_products":
        if user.get("seller_status") != "approved":
            return
        db = load_db()
        my = [p for p in db["products"] if str(p.get("seller_id", "admin")) == str(uid)]
        if not my:
            try:
                await event.edit("📦 No products yet.",
                                 buttons=[[Button.inline("🔙 Back", data="seller_home")]])
            except Exception:
                pass
            return
        buttons = []
        for p in my:
            buttons.append([Button.inline(f"📦 {p['name']} — ₹{p['price']}",
                                          data=f"seller_edit_{p['id']}", style="primary")])
        buttons.append([Button.inline("🔙 Back", data="seller_home")])
        try:
            await event.edit("📦 **My Products** — tap to edit:", buttons=buttons)
        except Exception:
            pass
        return

    if data.startswith("seller_edit_"):
        pid = data.split("_")[2]
        db = load_db()
        p = next((x for x in db["products"] if str(x["id"]) == pid), None)
        if not p or str(p.get("seller_id")) != str(uid):
            await event.answer("Not allowed!", alert=True)
            return
        buttons = [
            [Button.inline("✏️ Name", data=f"se_field_name_{pid}"),
             Button.inline("💵 Price", data=f"se_field_price_{pid}")],
            [Button.inline("📝 Desc", data=f"se_field_desc_{pid}"),
             Button.inline("📦 Content", data=f"se_field_content_{pid}")],
            [Button.inline("🖼️ Image", data=f"se_field_image_{pid}"),
             Button.inline("📁 File", data=f"se_field_file_{pid}")],
            [Button.inline("👤 Display", data=f"se_field_seller_display_{pid}")],
            [Button.inline("🗑️ Delete", data=f"seller_del_{pid}", style="danger")],
            [Button.inline("🔙 Back", data="seller_my_products")]
        ]
        try:
            await event.edit(f"✏️ Edit **{p['name']}**:", buttons=buttons)
        except Exception:
            pass
        return

    if data.startswith("seller_del_"):
        pid = data.split("_")[2]
        db = load_db()
        p = next((x for x in db["products"] if str(x["id"]) == pid), None)
        if not p or str(p.get("seller_id")) != str(uid):
            await event.answer("Not allowed!", alert=True)
            return
        db["products"] = [x for x in db["products"] if str(x["id"]) != pid]
        save_db(db)
        try:
            await event.edit("✅ Deleted.", buttons=[[Button.inline("🔙 Back", data="seller_my_products")]])
        except Exception:
            pass
        return

    if data.startswith("se_field_"):
        rest = data[len("se_field_"):]
        if rest.startswith("seller_display_"):
            pid = rest[len("seller_display_"):]
            field = "seller_display"
        else:
            field, pid = rest.split("_", 1)
        db = load_db()
        p = next((x for x in db["products"] if str(x["id"]) == pid), None)
        if not p or str(p.get("seller_id")) != str(uid):
            await event.answer("Not allowed!", alert=True)
            return
        USER_STATES[uid] = {"action": "seller_edit_field", "pid": pid, "field": field}
        msg = "👤 Send new display name or `anonymous`:" if field == "seller_display" else f"✍️ Send new **{field}**:"
        try:
            await event.edit(msg, buttons=[[Button.inline("❌ Cancel", data=f"seller_edit_{pid}", style="danger")]])
        except Exception:
            pass
        return

    if data == "seller_funds":
        try:
            await event.edit(
                f"╭──── 💰 FUNDS ────╮\n"
                f"Available    : ₹{user.get('seller_balance',0):.2f}\n"
                f"Total Earned : ₹{user.get('seller_earnings',0):.2f}\n"
                f"Withdrawn    : ₹{user.get('seller_withdrawn',0):.2f}\n"
                f"Min: ₹{MIN_WITHDRAW:.0f}\n"
                f"╰────────────────╯",
                buttons=[[Button.inline("💸 Withdraw", data="seller_withdraw", style="primary")],
                         [Button.inline("🔙 Back", data="seller_home")]]
            )
        except Exception:
            pass
        return

    if data == "seller_withdraw":
        bal = user.get("seller_balance", 0.0)
        if bal < MIN_WITHDRAW:
            await event.answer(f"⚠️ Min ₹{MIN_WITHDRAW:.0f}", alert=True)
            return
        USER_STATES[uid] = {"action": "seller_withdraw_amount"}
        try:
            await event.edit(f"💸 Amount? (Available: ₹{bal:.2f})",
                             buttons=[[Button.inline("❌ Cancel", data="seller_home", style="danger")]])
        except Exception:
            pass
        return

    # ============================================================
    #                     ADMIN PANEL
    # ============================================================
    if data == "admin_home":
        if uid != ADMIN_ID:
            await event.answer("Unauthorized!", alert=True)
            return
        db = load_db()
        users = db["users"]
        pending_wd = [w for w in db.get("withdrawals", []) if w["status"] == "pending"]
        pending_sr = [u for u in users.values() if u.get("seller_status") == "pending"]
        pending_reports = [r for r in db.get("reports", []) if r["status"] == "pending"]
        pending_offers = [o for o in db.get("offers", []) if o["status"] == "pending"]

        text = (
            f"╭──── 👑 ADMIN ────╮\n"
            f"👥 Users      : `{len(users)}`\n"
            f"📦 Products   : `{len(db['products'])}`\n"
            f"💸 Withdrawals: `{len(pending_wd)}`\n"
            f"🏪 Seller Req : `{len(pending_sr)}`\n"
            f"🚩 Reports    : `{len(pending_reports)}`\n"
            f"💬 Offers     : `{len(pending_offers)}`\n"
            f"╰────────────────╯"
        )
        try:
            await event.edit(text, buttons=[
                [Button.inline("📢 Broadcast", data="admin_broadcast"),
                 Button.inline("📊 Stats", data="admin_stats")],
                [Button.inline("👥 Users", data="admin_users"),
                 Button.inline("🛍️ Products", data="admin_products")],
                [Button.inline(f"💸 WD ({len(pending_wd)})", data="admin_withdrawals"),
                 Button.inline(f"🏪 SR ({len(pending_sr)})", data="admin_seller_reqs")],
                [Button.inline(f"🚩 Reports ({len(pending_reports)})", data="admin_reports"),
                 Button.inline(f"💬 Offers ({len(pending_offers)})", data="admin_offers")],
                [Button.inline("➕ Add Product", data="admin_add_item", style="success")],
                [Button.inline("🔙 Back", data="back_home")]
            ])
        except Exception:
            pass
        return

    if data == "admin_broadcast":
        if uid != ADMIN_ID: return
        USER_STATES[ADMIN_ID] = {"action": "broadcast_mode"}
        try:
            await event.edit("📢 Send broadcast message:",
                             buttons=[[Button.inline("❌ Cancel", data="admin_home", style="danger")]])
        except Exception:
            pass
        return

    if data == "admin_stats":
        if uid != ADMIN_ID: return
        db = load_db()
        users = db["users"]
        total_balance = sum(u["balance"] for u in users.values())
        total_added = sum(u.get("funds_added", 0) for u in users.values())
        total_spent = sum(u.get("money_used", 0) for u in users.values())
        total_sellers = sum(1 for u in users.values() if u.get("seller_status") == "approved")
        total_reviews = len(db.get("reviews", []))
        text = (
            f"╭──── 📊 STATS ────╮\n"
            f"👥 Users         : `{len(users)}`\n"
            f"🏪 Sellers       : `{total_sellers}`\n"
            f"📦 Products      : `{len(db['products'])}`\n"
            f"⭐ Reviews       : `{total_reviews}`\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"💰 Balance       : ₹{total_balance:.2f}\n"
            f"🪙 Funds Added   : ₹{total_added:.2f}\n"
            f"💳 Money Spent   : ₹{total_spent:.2f}\n"
            f"╰────────────────╯"
        )
        try:
            await event.edit(text, buttons=[[Button.inline("🔙 Back", data="admin_home")]])
        except Exception:
            pass
        return

    if data == "admin_users":
        if uid != ADMIN_ID: return
        await show_users_page(event, 0)
        return

    if data.startswith("admin_users_page_"):
        if uid != ADMIN_ID: return
        await show_users_page(event, int(data.split("_")[3]))
        return

    if data.startswith("admin_user_"):
        if uid != ADMIN_ID: return
        await show_user_detail(event, data.split("_")[2])
        return

    if data.startswith("admin_bal_"):
        if uid != ADMIN_ID: return
        parts = data.split("_")
        op, target = parts[2], parts[3]
        USER_STATES[ADMIN_ID] = {"action": "admin_bal_edit", "op": op, "target": target}
        try:
            await event.edit(f"✍️ Amount to **{op}** for `{target}`:",
                             buttons=[[Button.inline("❌ Cancel", data="admin_home", style="danger")]])
        except Exception:
            pass
        return

    if data.startswith("admin_warn_"):
        if uid != ADMIN_ID: return
        target = data.split("_")[2]
        USER_STATES[ADMIN_ID] = {"action": "admin_warn_user", "target": target}
        try:
            await event.edit(f"⚠️ Warning for `{target}`:",
                             buttons=[[Button.inline("❌ Cancel", data="admin_home", style="danger")]])
        except Exception:
            pass
        return

    if data.startswith("admin_demote_"):
        if uid != ADMIN_ID: return
        target = data.split("_")[2]
        db = load_db()
        if target in db["users"]:
            db["users"][target]["seller_status"] = "none"
            db["users"][target]["is_seller"] = False
            save_db(db)
        await event.answer("✅ Demoted!", alert=True)
        await show_user_detail(event, target)
        return

    if data.startswith("admin_promote_"):
        if uid != ADMIN_ID: return
        target = data.split("_")[2]
        db = load_db()
        if target in db["users"]:
            db["users"][target]["seller_status"] = "approved"
            db["users"][target]["is_seller"] = True
            db["users"][target]["seller_since"] = now_str()
            save_db(db)
        await event.answer("✅ Promoted!", alert=True)
        await show_user_detail(event, target)
        return

    if data.startswith("admin_sr_ok_"):
        if uid != ADMIN_ID: return
        target = data.split("_")[3]
        db = load_db()
        if target in db["users"]:
            db["users"][target]["seller_status"] = "approved"
            db["users"][target]["is_seller"] = True
            db["users"][target]["seller_since"] = now_str()
            save_db(db)
        await event.edit("✅ Seller approved.")
        try:
            await bot.send_message(int(target), "🎉 You're now a seller!")
        except Exception:
            pass
        return

    if data.startswith("admin_sr_no_"):
        if uid != ADMIN_ID: return
        target = data.split("_")[3]
        db = load_db()
        if target in db["users"]:
            db["users"][target]["seller_status"] = "rejected"
            save_db(db)
        await event.edit("❌ Seller rejected.")
        return

    if data == "admin_seller_reqs":
        if uid != ADMIN_ID: return
        db = load_db()
        pending = [(k, v) for k, v in db["users"].items() if v.get("seller_status") == "pending"]
        if not pending:
            try:
                await event.edit("✅ No pending.",
                                 buttons=[[Button.inline("🔙 Back", data="admin_home")]])
            except Exception:
                pass
            return
        buttons = []
        for k, v in pending:
            buttons.append([Button.inline(f"🏪 {v['name'][:20]}", data=f"admin_user_{k}", style="primary")])
        buttons.append([Button.inline("🔙 Back", data="admin_home")])
        try:
            await event.edit("🏪 Pending seller requests:", buttons=buttons)
        except Exception:
            pass
        return

    if data == "admin_products":
        if uid != ADMIN_ID: return
        db = load_db()
        if not db["products"]:
            try:
                await event.edit("📦 No products.",
                                 buttons=[[Button.inline("🔙 Back", data="admin_home")]])
            except Exception:
                pass
            return
        buttons = []
        for p in db["products"]:
            buttons.append([Button.inline(f"📦 {p['name'][:20]} — ₹{p['price']}",
                                          data=f"admin_prod_{p['id']}", style="primary")])
        buttons.append([Button.inline("🔙 Back", data="admin_home")])
        try:
            await event.edit("📦 Products:", buttons=buttons)
        except Exception:
            pass
        return

    if data.startswith("admin_prod_"):
        if uid != ADMIN_ID: return
        pid = data.split("_")[2]
        db = load_db()
        p = next((x for x in db["products"] if str(x["id"]) == pid), None)
        if not p:
            await event.answer("Missing!", alert=True)
            return
        txt = f"📦 **{p['name']}**\n💵 ₹{p['price']}\n📝 {p['desc']}\n👤 Seller: `{p.get('seller_id','admin')}`"
        try:
            await event.edit(txt, buttons=[
                [Button.inline("🗑️ Delete", data=f"del_item_{pid}", style="danger")],
                [Button.inline("🔙 Back", data="admin_products")]
            ])
        except Exception:
            pass
        return

    if data.startswith("del_item_"):
        if uid != ADMIN_ID: return
        pid = data.split("_")[2]
        db = load_db()
        db["products"] = [p for p in db["products"] if str(p["id"]) != pid]
        save_db(db)
        await event.answer("✅ Deleted!", alert=True)
        return

    if data == "admin_add_item":
        if uid != ADMIN_ID: return
        USER_STATES[uid] = {"action": "add_item_image", "item_data": {}}
        try:
            await event.edit("📸 Send **Product Image** (Photo or URL):",
                             buttons=[[Button.inline("❌ Cancel", data="admin_home", style="danger")]])
        except Exception:
            pass
        return

    if data == "admin_reports":
        if uid != ADMIN_ID: return
        db = load_db()
        reps = [r for r in db.get("reports", []) if r["status"] == "pending"]
        if not reps:
            try:
                await event.edit("✅ No pending reports.",
                                 buttons=[[Button.inline("🔙 Back", data="admin_home")]])
            except Exception:
                pass
            return
        txt = "🚩 **Pending Reports**\n━━━━━━━━━━━━━━━━\n"
        for r in reps[-5:]:
            txt += f"#{r['id']} — {r['product_name']}\n  └ {r['reason'][:60]}\n\n"
        try:
            await event.edit(txt, buttons=[[Button.inline("🔙 Back", data="admin_home")]])
        except Exception:
            pass
        return

    if data == "admin_withdrawals":
        if uid != ADMIN_ID: return
        db = load_db()
        pending = [w for w in db.get("withdrawals", []) if w["status"] == "pending"]
        if not pending:
            try:
                await event.edit("✅ No pending withdrawals.",
                                 buttons=[[Button.inline("🔙 Back", data="admin_home")]])
            except Exception:
                pass
            return
        buttons = []
        for w in pending:
            uinfo = db["users"].get(str(w["user_id"]), {})
            buttons.append([Button.inline(f"💸 ₹{w['amount']:.0f} — {uinfo.get('name','?')[:15]}",
                                          data=f"admin_wd_{w['id']}", style="primary")])
        buttons.append([Button.inline("🔙 Back", data="admin_home")])
        try:
            await event.edit("💸 Pending withdrawals:", buttons=buttons)
        except Exception:
            pass
        return

    if data.startswith("admin_wd_"):
        if uid != ADMIN_ID: return
        wid = data.split("_")[2]
        db = load_db()
        w = next((x for x in db["withdrawals"] if x["id"] == wid), None)
        if not w:
            await event.answer("Missing!", alert=True)
            return
        uinfo = db["users"].get(str(w["user_id"]), {})
        txt = (f"💸 **Withdrawal** `{wid}`\n"
               f"• Seller: {uinfo.get('name','?')}\n"
               f"• Amount: ₹{w['amount']:.2f}")
        try:
            await event.edit(txt, buttons=[
                [Button.inline("✅ Accept", data=f"wd_ok_{wid}", style="success"),
                 Button.inline("❌ Reject", data=f"wd_no_{wid}", style="danger")],
                [Button.inline("🔙 Back", data="admin_withdrawals")]
            ])
        except Exception:
            pass
        return

    if data.startswith("wd_ok_"):
        if uid != ADMIN_ID: return
        wid = data.split("_")[2]
        db = load_db()
        w = next((x for x in db["withdrawals"] if x["id"] == wid), None)
        if not w or w["status"] != "pending":
            await event.answer("Done already!", alert=True)
            return
        w["status"] = "approved"
        w["processed_at"] = now_str()
        save_db(db)
        try:
            await event.edit("✅ Approved. Send note or `skip`:",
                             buttons=[[Button.inline("⏭️ Skip", data=f"wd_skip_{wid}", style="primary")]])
        except Exception:
            pass
        USER_STATES[ADMIN_ID] = {"action": "wd_note", "wid": wid,
                                 "target": w["user_id"], "amount": w["amount"]}
        return

    if data.startswith("wd_skip_"):
        if uid != ADMIN_ID: return
        wid = data.split("_")[2]
        db = load_db()
        w = next((x for x in db["withdrawals"] if x["id"] == wid), None)
        if not w: return
        target = str(w["user_id"])
        if target in db["users"]:
            db["users"][target]["seller_balance"] = max(0.0, db["users"][target].get("seller_balance", 0) - w["amount"])
            db["users"][target]["seller_withdrawn"] = db["users"][target].get("seller_withdrawn", 0) + w["amount"]
        w["admin_note"] = "skip"
        save_db(db)
        USER_STATES.pop(ADMIN_ID, None)
        try:
            await bot.send_message(int(target),
                f"🎉 **Withdrawal Approved**\n💰 ₹{w['amount']:.2f}\nPayment processed.")
        except Exception:
            pass
        try:
            await event.edit("✅ Processed (skip note).")
        except Exception:
            pass
        return

    if data.startswith("wd_no_"):
        if uid != ADMIN_ID: return
        wid = data.split("_")[2]
        db = load_db()
        w = next((x for x in db["withdrawals"] if x["id"] == wid), None)
        if not w or w["status"] != "pending":
            await event.answer("Done already!", alert=True)
            return
        w["status"] = "rejected"
        w["processed_at"] = now_str()
        target = str(w["user_id"])
        if target in db["users"]:
            db["users"][target]["seller_balance"] = db["users"][target].get("seller_balance", 0) + w["amount"]
        save_db(db)
        try:
            await event.edit("❌ Rejected. Amount refunded.")
        except Exception:
            pass
        try:
            await bot.send_message(int(target), f"❌ Withdrawal of ₹{w['amount']:.2f} rejected. Refunded.")
        except Exception:
            pass
        return

    if data == "admin_offers":
        if uid != ADMIN_ID: return
        db = load_db()
        offs = [o for o in db.get("offers", []) if o["status"] == "pending"]
        if not offs:
            try:
                await event.edit("✅ No pending offers.",
                                 buttons=[[Button.inline("🔙 Back", data="admin_home")]])
            except Exception:
                pass
            return
        txt = "💬 **Pending Offers**\n━━━━━━━━━━━━━━━━\n"
        for o in offs[-8:]:
            txt += f"#{o['id']} — {o['product_name']}\n  Listed: ₹{o['listed_price']} → Offer: ₹{o['amount']}\n\n"
        try:
            await event.edit(txt, buttons=[[Button.inline("🔙 Back", data="admin_home")]])
        except Exception:
            pass
        return

    if data.startswith("reply_user_"):
        target_uid = int(data.split("_")[2])
        if uid != ADMIN_ID:
            await event.answer("Unauthorized!", alert=True)
            return
        USER_STATES[uid] = {"action": "admin_replying", "target_uid": target_uid}
        try:
            await event.edit(f"✍️ Reply for `{target_uid}`:",
                             buttons=[[Button.inline("❌ Cancel", data="admin_home", style="danger")]])
        except Exception:
            pass
        return

    if data.startswith("reject_user_"):
        target_uid = int(data.split("_")[2])
        if uid != ADMIN_ID:
            await event.answer("Unauthorized!", alert=True)
            return
        await event.answer("Rejected!")
        try:
            await event.edit(f"❌ Ticket `{target_uid}` rejected.")
        except Exception:
            pass
        try:
            await bot.send_message(target_uid, "⚠️ Your ticket was closed.")
        except Exception:
            pass
        return

    await event.answer()

# ----------------- ADMIN USER PAGES ----------------- #
async def show_users_page(event, page, per_page=8):
    db = load_db()
    users = list(db["users"].items())
    total = len(users)
    start = page * per_page
    end = start + per_page
    sl = users[start:end]
    total_pages = max(1, (total + per_page - 1) // per_page)

    buttons = []
    for k, v in sl:
        tag = "🏪" if v.get("seller_status") == "approved" else ""
        buttons.append([Button.inline(
            f"{tag} {v['name'][:22]} | ₹{v['balance']:.0f}",
            data=f"admin_user_{k}", style="primary"
        )])
    nav = []
    if page > 0:
        nav.append(Button.inline("⬅️", data=f"admin_users_page_{page-1}"))
    nav.append(Button.inline(f"{page+1}/{total_pages}", data="noop"))
    if end < total:
        nav.append(Button.inline("➡️", data=f"admin_users_page_{page+1}"))
    if nav:
        buttons.append(nav)
    buttons.append([Button.inline("🔙 Back", data="admin_home")])
    try:
        await event.edit(f"👥 Users – {page+1}/{total_pages} (total {total})", buttons=buttons)
    except Exception:
        pass

async def show_user_detail(event, target_uid):
    db = load_db()
    u = db["users"].get(str(target_uid))
    if not u:
        await event.answer("Not found!", alert=True)
        return
    txns = u.get("transactions", [])[-10:]
    txn_txt = "\n".join([f"  • {t['type']}: ₹{t['amount']:.2f} – {t.get('note','')}" for t in txns]) or "  None"
    warns = u.get("warnings", [])
    warn_txt = "\n".join([f"  ⚠️ {w}" for w in warns[-5:]]) or "  None"
    seller_info = ""
    if u.get("seller_status") == "approved":
        seller_info = (f"\n🏪 SELLER\n• Bal: ₹{u.get('seller_balance',0):.2f}"
                       f"\n• Earn: ₹{u.get('seller_earnings',0):.2f}"
                       f"\n• Withd: ₹{u.get('seller_withdrawn',0):.2f}")

    text = (
        f"👤 **{u['name']}**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"• UID: `{target_uid}`\n"
        f"• Username: {u.get('username','None')}\n"
        f"• Joined: {u['joined_at']}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 Balance: ₹{u['balance']:.2f}\n"
        f"🪙 Added: ₹{u.get('funds_added',0):.2f}\n"
        f"💳 Used: ₹{u.get('money_used',0):.2f}\n"
        f"🛒 Purchases: {u.get('purchased_count',0)}\n"
        f"{seller_info}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📜 Recent TXNs:\n{txn_txt}\n"
        f"⚠️ Warnings:\n{warn_txt}"
    )
    row1 = [
        Button.inline("➕ Add", data=f"admin_bal_add_{target_uid}", style="success"),
        Button.inline("➖ Rem", data=f"admin_bal_rem_{target_uid}", style="danger"),
        Button.inline("🔄 Set", data=f"admin_bal_set_{target_uid}")
    ]
    row2 = [Button.inline("⚠️ Warn", data=f"admin_warn_{target_uid}")]
    if u.get("seller_status") == "approved":
        row2.append(Button.inline("⬇️ Demote", data=f"admin_demote_{target_uid}", style="danger"))
    elif u.get("seller_status") in ("none", "rejected"):
        row2.append(Button.inline("⬆️ Promote", data=f"admin_promote_{target_uid}", style="success"))
    buttons = [row1, row2, [Button.inline("🔙 Back", data="admin_users")]]
    try:
        await event.edit(text, buttons=buttons)
    except Exception:
        pass

# ================================================================
#                     /chx  &  /broadcast
# ================================================================
@bot.on(events.NewMessage(pattern=r"^/chx"))
async def admin_panel_handler(event):
    if event.sender_id != ADMIN_ID:
        return
    db = load_db()
    users = db["users"]
    pending_wd = [w for w in db.get("withdrawals", []) if w["status"] == "pending"]
    pending_sr = [u for u in users.values() if u.get("seller_status") == "pending"]
    pending_reports = [r for r in db.get("reports", []) if r["status"] == "pending"]
    pending_offers = [o for o in db.get("offers", []) if o["status"] == "pending"]

    text = (
        f"╭──── 👑 ADMIN ────╮\n"
        f"👥 Users: `{len(users)}`\n"
        f"📦 Products: `{len(db['products'])}`\n"
        f"💸 WD: `{len(pending_wd)}`\n"
        f"🏪 SR: `{len(pending_sr)}`\n"
        f"🚩 Reports: `{len(pending_reports)}`\n"
        f"💬 Offers: `{len(pending_offers)}`\n"
        f"╰────────────────╯"
    )
    await event.respond(text, buttons=[
        [Button.inline("📢 Broadcast", data="admin_broadcast"),
         Button.inline("📊 Stats", data="admin_stats")],
        [Button.inline("👥 Users", data="admin_users"),
         Button.inline("🛍️ Products", data="admin_products")],
        [Button.inline(f"💸 WD ({len(pending_wd)})", data="admin_withdrawals"),
         Button.inline(f"🏪 SR ({len(pending_sr)})", data="admin_seller_reqs")],
        [Button.inline(f"🚩 Reports ({len(pending_reports)})", data="admin_reports"),
         Button.inline(f"💬 Offers ({len(pending_offers)})", data="admin_offers")],
        [Button.inline("➕ Add Product", data="admin_add_item", style="success")]
    ])

@bot.on(events.NewMessage(pattern=r"^/broadcast(?:\s+(.*))?"))
async def broadcast_handler(event):
    if event.sender_id != ADMIN_ID:
        return
    text = event.pattern_match.group(1)
    if not text:
        USER_STATES[ADMIN_ID] = {"action": "broadcast_mode"}
        await event.respond("📢 Send the broadcast message:")
        return
    db = load_db()
    users = db.get("users", {})
    sent = 0
    status_msg = await event.respond(f"🚀 Broadcasting to {len(users)}…")
    for uid_ in users:
        try:
            await bot.send_message(int(uid_), text)
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
    await status_msg.edit(f"✅ Done. Sent: {sent}/{len(users)}")

# ================================================================
#                     MESSAGE DISPATCHER
# ================================================================
@bot.on(events.NewMessage)
async def message_handler(event):
    if event.text and event.text.startswith("/"):
        if event.text.strip() == "/endchat":
            uid = event.sender_id
            if uid in TEMP_CHATS:
                partner = TEMP_CHATS[uid]["partner"]
                TEMP_CHATS.pop(uid, None)
                TEMP_CHATS.pop(partner, None)
                await event.respond("🔚 Chat ended.")
                try:
                    await bot.send_message(partner, "🔚 Other user ended the chat.")
                except Exception:
                    pass
            else:
                await event.respond("❌ Not in a chat.")
        return

    uid = event.sender_id
    state = USER_STATES.get(uid, {})
    sender = await event.get_sender()
    full_name = f"{sender.first_name or ''} {sender.last_name or ''}".strip() or "User"
    user, _ = get_user(uid, full_name)

    # ---------- TEMP CHAT ROUTING ---------- #
    if uid in TEMP_CHATS:
        chat = TEMP_CHATS[uid]
        if datetime.now() > chat["expires"]:
            partner = chat["partner"]
            TEMP_CHATS.pop(uid, None)
            TEMP_CHATS.pop(partner, None)
            await event.respond("⏰ Temp chat expired.")
        else:
            partner = chat["partner"]
            try:
                await bot.send_message(partner, f"💬 **{full_name}**: {event.text or '[non-text]'}")
                await event.respond("✅ Sent")
            except Exception as e:
                await event.respond(f"❌ Failed: {e}")
            return

    # ---------- FORCE JOIN FALLBACK ---------- #
    if not await is_user_joined(uid):
        await event.respond("🚫 Join the channel first.", buttons=join_required_keyboard())
        return

    # ---------- BROADCAST ---------- #
    if uid == ADMIN_ID and state.get("action") == "broadcast_mode":
        USER_STATES.pop(uid, None)
        db = load_db()
        users = db["users"]
        sent = 0
        status_msg = await event.respond(f"🚀 Broadcasting to {len(users)}…")
        for target_id in users:
            try:
                await bot.send_message(int(target_id), event.message)
                sent += 1
                await asyncio.sleep(0.05)
            except Exception:
                pass
        await status_msg.edit(f"✅ Sent: {sent}/{len(users)}")
        return

    # ---------- ADMIN BAL EDIT ---------- #
    if uid == ADMIN_ID and state.get("action") == "admin_bal_edit":
        target = state["target"]; op = state["op"]
        USER_STATES.pop(uid, None)
        try:
            amt = float(event.text.strip())
        except Exception:
            await event.respond("❌ Invalid.")
            return
        db = load_db()
        if target not in db["users"]:
            await event.respond("❌ Not found.")
            return
        cur = db["users"][target]["balance"]
        if op == "add":
            new = cur + amt; note = f"Admin added ₹{amt:.2f}"
        elif op == "rem":
            new = max(0.0, cur - amt); note = f"Admin removed ₹{amt:.2f}"
        else:
            new = amt; note = f"Admin set ₹{amt:.2f}"
        db["users"][target]["balance"] = new
        db["users"][target].setdefault("transactions", []).append({
            "type": "admin_edit", "amount": amt, "note": note, "time": now_str()
        })
        save_db(db)
        await event.respond(f"✅ New balance: ₹{new:.2f}")
        return

    # ---------- ADMIN WARN ---------- #
    if uid == ADMIN_ID and state.get("action") == "admin_warn_user":
        target = state["target"]
        USER_STATES.pop(uid, None)
        db = load_db()
        if target in db["users"]:
            db["users"][target].setdefault("warnings", []).append(
                f"{event.text.strip()} ({now_str()})"
            )
            save_db(db)
        await event.respond("✅ Warning sent.")
        try:
            await bot.send_message(int(target), f"⚠️ **Warning:**\n{event.text.strip()}")
        except Exception:
            pass
        return

    # ---------- WD NOTE ---------- #
    if uid == ADMIN_ID and state.get("action") == "wd_note":
        USER_STATES.pop(uid, None)
        wid = state["wid"]; target = state["target"]; amount = state["amount"]
        note = event.text.strip() if event.text else "skip"
        db = load_db()
        for w in db.get("withdrawals", []):
            if w["id"] == wid:
                w["admin_note"] = note
                break
        if str(target) in db["users"]:
            u = db["users"][str(target)]
            u["seller_balance"] = max(0.0, u.get("seller_balance", 0) - amount)
            u["seller_withdrawn"] = u.get("seller_withdrawn", 0) + amount
        save_db(db)
        await event.respond("✅ Processed.")
        try:
            await bot.send_message(int(target),
                f"🎉 **Withdrawal Approved**\n💰 ₹{amount:.2f}\n📝 {note}")
        except Exception:
            pass
        return

    # ---------- ADMIN REPLY ---------- #
    if uid == ADMIN_ID and state.get("action") == "admin_replying":
        target_uid = state["target_uid"]
        USER_STATES.pop(uid, None)
        try:
            await bot.send_message(target_uid, f"💬 **From Admin:**\n{event.text}")
            await event.respond(f"✅ Sent to `{target_uid}`!")
        except Exception as e:
            await event.respond(f"❌ Failed: {e}")
        return

    # ============================================================
    #        PRODUCT ADD FLOW (admin + seller)
    # ============================================================
    actions_add = ("add_item_", "sell_item_")
    if state.get("action", "").startswith(actions_add):
        action = state["action"]
        is_seller = action.startswith("sell_item_")
        item_data = state.get("item_data", {})
        prefix = "sell_item_" if is_seller else "add_item_"
        stage = action[len(prefix):]

        if stage == "image":
            if event.photo:
                # upload to storage channel
                msg_id, fid = await upload_to_storage(await event.download_media(), caption="Product Image")
                item_data["storage_msg_id"] = msg_id
                item_data["storage_file_id"] = fid
                item_data["image"] = fid
            elif event.text:
                item_data["image"] = event.text.strip()
            else:
                item_data["image"] = DEFAULT_BANNER
            USER_STATES[uid] = {"action": prefix + "name", "item_data": item_data}
            await event.respond("📝 **Product Name**:")
            return

        if stage == "name":
            item_data["name"] = event.text.strip()
            USER_STATES[uid] = {"action": prefix + "price", "item_data": item_data}
            await event.respond("💰 **Price (₹)**:")
            return

        if stage == "price":
            try:
                item_data["price"] = float(event.text.strip())
            except ValueError:
                await event.respond("❌ Invalid.")
                return
            USER_STATES[uid] = {"action": prefix + "desc", "item_data": item_data}
            await event.respond("📄 **Description**:")
            return

        if stage == "desc":
            item_data["desc"] = event.text.strip()
            USER_STATES[uid] = {"action": prefix + "content", "item_data": item_data}
            await event.respond("📦 **Delivery Content** (text/code):")
            return

        if stage == "content":
            item_data["content"] = event.text.strip()
            USER_STATES[uid] = {"action": prefix + "display", "item_data": item_data}
            await event.respond("👤 Send your public name or `anonymous`:")
            return

        if stage == "display":
            val = event.text.strip()
            item_data["seller_display"] = "anonymous" if val.lower() == "anonymous" else val.lstrip("@")
            USER_STATES[uid] = {"action": prefix + "file", "item_data": item_data}
            await event.respond("📁 Now send the actual file (or `skip`):")
            return

        if stage == "file":
            if event.document:
                # upload to storage channel
                dl = await event.download_media()
                msg_id, fid = await upload_to_storage(dl, caption=item_data.get("name", "Product File"))
                item_data["storage_msg_id"] = msg_id
                item_data["storage_file_id"] = fid
                try:
                    item_data["file_name"] = event.document.attributes[0].file_name
                except Exception:
                    item_data["file_name"] = "file"
            elif event.text and event.text.strip().lower() == "skip":
                pass
            else:
                await event.respond("⚠️ Send a file or `skip`.")
                return

            item_data["seller_id"] = str(uid) if is_seller else "admin"
            USER_STATES[uid] = {"action": prefix + "confirm", "item_data": item_data}
            preview = (
                f"**Preview:**\n\n"
                f"🏷️ {item_data['name']}\n"
                f"💵 ₹{item_data['price']}\n"
                f"📝 {item_data['desc']}\n"
                f"👤 {item_data.get('seller_display','anonymous')}\n"
                f"📁 {item_data.get('file_name') or 'None'}"
            )
            try:
                await bot.send_file(uid, item_data.get("image", DEFAULT_BANNER),
                                    caption=preview,
                                    buttons=[[Button.inline("🚀 Publish", data="apply_sale_now", style="success")]])
            except Exception:
                await event.respond(preview)
            return

    # ---------- SELLER EDIT FIELD ---------- #
    if state.get("action") == "seller_edit_field":
        pid = state["pid"]; field = state["field"]
        USER_STATES.pop(uid, None)
        db = load_db()
        p = next((x for x in db["products"] if str(x["id"]) == pid), None)
        if not p or str(p.get("seller_id")) != str(uid):
            await event.respond("❌ Not allowed.")
            return
        if field == "price":
            try:
                p["price"] = float(event.text.strip())
            except Exception:
                await event.respond("❌ Invalid.")
                return
        elif field == "image":
            if event.photo:
                dl = await event.download_media()
                _, fid = await upload_to_storage(dl, caption="Product Image")
                p["image"] = fid
            elif event.text:
                p["image"] = event.text.strip()
        elif field == "file":
            if event.document:
                dl = await event.download_media()
                _, fid = await upload_to_storage(dl, caption="Product File")
                p["storage_file_id"] = fid
            else:
                await event.respond("❌ Send a file.")
                return
        elif field == "seller_display":
            val = event.text.strip()
            p["seller_display"] = "anonymous" if val.lower() == "anonymous" else val.lstrip("@")
        else:
            p[field] = event.text.strip()
        save_db(db)
        await event.respond("✅ Updated.")
        return

    # ---------- SELLER WITHDRAW ---------- #
    if state.get("action") == "seller_withdraw_amount":
        USER_STATES.pop(uid, None)
        try:
            amt = float(event.text.strip())
        except Exception:
            await event.respond("❌ Invalid.")
            return
        if amt < MIN_WITHDRAW:
            await event.respond(f"❌ Min ₹{MIN_WITHDRAW:.0f}")
            return
        db = load_db()
        u = db["users"].get(str(uid))
        if not u or u.get("seller_status") != "approved":
            await event.respond("❌ Not a seller.")
            return
        if amt > u.get("seller_balance", 0):
            await event.respond("❌ Not enough.")
            return
        wid = f"WD{int(datetime.now().timestamp())}"
        db.setdefault("withdrawals", []).append({
            "id": wid, "user_id": uid, "amount": amt, "status": "pending",
            "requested_at": now_str(), "processed_at": "", "admin_note": ""
        })
        save_db(db)
        await event.respond(f"✅ Request `{wid}` of ₹{amt:.2f} sent.")
        try:
            await bot.send_message(ADMIN_ID,
                f"💸 **Withdrawal**\n• {full_name} (`{uid}`)\n• ₹{amt:.2f}\n• `{wid}`",
                buttons=[[Button.inline("✅ Accept", data=f"wd_ok_{wid}", style="success"),
                          Button.inline("❌ Reject", data=f"wd_no_{wid}", style="danger")]])
        except Exception:
            pass
        return

    # ---------- REVIEW TEXT ---------- #
    if state.get("action") == "awaiting_review":
        pid = state["pid"]; rating = state.get("rating", 0)
        USER_STATES.pop(uid, None)
        if rating < 1:
            await event.respond("❌ Pick a rating first.")
            return
        db = load_db()
        p = next((x for x in db["products"] if str(x["id"]) == pid), None)
        pname = p["name"] if p else "unknown"
        db.setdefault("reviews", []).append({
            "product_id": pid, "product_name": pname,
            "user_id": uid, "user_name": full_name,
            "rating": rating, "text": event.text.strip(),
            "time": now_str()
        })
        save_db(db)
        update_user(uid, given_reviews=user.get("given_reviews", []) + [int(pid)])
        await event.respond(f"⭐ **Review saved!** {rating}/5\nThanks for your feedback.",
                            buttons=[[Button.inline("🔙 Home", data="back_home")]])
        return

    # ---------- REPORT REASON ---------- #
    if state.get("action") == "report_reason":
        pid = state["pid"]
        USER_STATES.pop(uid, None)
        db = load_db()
        p = next((x for x in db["products"] if str(x["id"]) == pid), None)
        pname = p["name"] if p else "unknown"
        rid = int(datetime.now().timestamp())
        db.setdefault("reports", []).append({
            "id": rid, "reporter": uid, "product_id": pid,
            "product_name": pname, "reason": event.text.strip(),
            "status": "pending", "time": now_str()
        })
        save_db(db)
        await event.respond("🚩 Report submitted.", buttons=[[Button.inline("🔙 Home", data="back_home")]])
        await notify_admin(f"🚩 **Report #{rid}**\n• {pname}\n• {event.text.strip()}")
        return

    # ---------- OFFER AMOUNT (buyer side) ----------
    if state.get("action") == "awaiting_offer_amount":
        pid = state["pid"]
        USER_STATES.pop(uid, None)
        try:
            amount = float(event.text.strip())
        except Exception:
            await event.respond("❌ Invalid amount.")
            return
        db = load_db()
        p = next((x for x in db["products"] if str(x["id"]) == pid), None)
        if not p:
            await event.respond("❌ Product missing.")
            return
        if amount >= float(p["price"]):
            await event.respond("❌ Offer must be lower than listed price.")
            return
        if amount <= 0:
            await event.respond("❌ Amount must be positive.")
            return
        seller_id = p.get("seller_id", "admin")
        oid = str(int(datetime.now().timestamp()))
        db.setdefault("offers", []).append({
            "id": oid, "buyer_id": uid, "seller_id": seller_id,
            "product_id": pid, "product_name": p["name"],
            "listed_price": p["price"], "amount": amount,
            "status": "pending", "created_at": now_str()
        })
        save_db(db)
        await event.respond(
            f"✅ **Offer Sent!**\n\n💰 Your offer: ₹{amount:.2f}\n"
            f"📦 {p['name']}\n\nSeller will respond shortly.",
            buttons=[[Button.inline("🔙 Home", data="back_home")]]
        )
        # notify seller
        if seller_id != "admin":
            try:
                await bot.send_message(
                    int(seller_id),
                    f"💰 **New Offer**\n\n"
                    f"📦 {p['name']}\n"
                    f"Listed: ₹{p['price']}\n"
                    f"Offer: ₹{amount:.2f}\n"
                    f"Buyer: {full_name}",
                    buttons=[[
                        Button.inline("✅ Accept", data=f"offer_accept_{oid}", style="success"),
                        Button.inline("❌ Reject", data=f"offer_reject_{oid}", style="danger")
                    ]]
                )
            except Exception as e:
                logging.error(f"Notify seller offer failed: {e}")
        else:
            try:
                await bot.send_message(ADMIN_ID,
                    f"💰 **Offer** (admin product)\n📦 {p['name']}\n₹{amount:.2f}",
                    buttons=[[Button.inline("✅ Accept", data=f"offer_accept_{oid}", style="success"),
                              Button.inline("❌ Reject", data=f"offer_reject_{oid}", style="danger")]])
            except Exception:
                pass
        return

    # ---------- SUPPORT ---------- #
    if state.get("action") == "awaiting_support_message":
        USER_STATES.pop(uid, None)
        query = event.text or "Media"
        await event.respond("✅ Query delivered!", buttons=back_keyboard())
        try:
            await bot.send_message(ADMIN_ID,
                f"📩 **Support**\n• {full_name} (`{uid}`)\n• {query}",
                buttons=[[Button.inline("✉️ Reply", data=f"reply_user_{uid}"),
                          Button.inline("❌ Reject", data=f"reject_user_{uid}", style="danger")]])
        except Exception:
            pass
        return

    # ---------- AUTO DEPOSIT ---------- #
    if event.text:
        candidate = event.text.strip()
        if len(candidate) >= 6:
            api_url = f"https://fmapi-5llh.onrender.com/search?q={candidate}"
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(api_url, timeout=10) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get("count", 0) > 0 and "results" in data:
                                r = data["results"][0]
                                key = data.get("query") or r.get("txn_id") or r.get("utr") or candidate
                                db = load_db()
                                if key in db.get("used_txns", []):
                                    await event.respond("⚠️ Already redeemed!")
                                    return
                                money = float(r.get("money", 0))
                                if money > 0:
                                    db.setdefault("used_txns", []).append(key)
                                    save_db(db)
                                    new_balance = user["balance"] + money
                                    update_user(uid, balance=new_balance,
                                                funds_added=user["funds_added"] + money)
                                    log_txn(uid, "deposit", money, f"Ref: {key}")
                                    await event.respond(
                                        f"🎉 **Payment Verified!**\n💰 ₹{money:.2f}\n"
                                        f"💳 New: ₹{new_balance:.2f}",
                                        buttons=back_keyboard())
                                    await notify_channel(f"💸 **Deposit** {full_name} — ₹{money:.2f}")
                                    return
            except Exception as e:
                logging.error(f"Payment API: {e}")

# ================================================================
#                     APPLY SALE
# ================================================================
@bot.on(events.CallbackQuery(data="apply_sale_now"))
async def apply_sale_handler(event):
    uid = event.sender_id
    if uid != ADMIN_ID:
        user, _ = get_user(uid)
        if user.get("seller_status") != "approved":
            await event.answer("Not allowed!", alert=True)
            return
    state = USER_STATES.get(uid, {})
    item_data = state.get("item_data")
    if not item_data:
        await event.answer("Expired!", alert=True)
        return
    db = load_db()
    item_data["id"] = int(datetime.now().timestamp())
    item_data.setdefault("seller_id", "admin")
    item_data.setdefault("seller_display", "anonymous")
    item_data["created_at"] = now_str()
    db.setdefault("products", []).append(item_data)
    save_db(db)
    USER_STATES.pop(uid, None)
    try:
        await event.edit(f"✅ **{item_data['name']}** is LIVE!")
    except Exception:
        pass
    seller_label = item_data.get("seller_display", "anonymous")
    await notify_channel(
        f"🆕 **New SRC Listed!**\n\n"
        f"📦 **{item_data['name']}**\n"
        f"💵 ₹{item_data['price']}\n"
        f"📝 {item_data['desc']}\n"
        f"👤 Seller: {seller_label}\n"
        f"🕒 {short_time()}",
        image=item_data.get("storage_file_id") or item_data.get("image")
    )

# ----------------- RUN ----------------- #
if __name__ == "__main__":
    print("🚀 Bot started — all features active!")
    bot.run_until_disconnected()