import json
import requests
import asyncio
from collections import defaultdict
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    CallbackQueryHandler, MessageHandler, filters
)
from telegram.constants import ChatType

# ================== CONFIG ==================
BOT_TOKEN = "AAPNA BOT TOKEN ADD KRO BROTHER"
ADMIN_IDS = {CHAT ID ADD KRO}  # <-- YAHAN APNA TELEGRAM USER ID DALO
AUTO_DELETE_TIME = 300  # 5 minutes
# ===========================================

# In-memory storage (restart pe reset)
USERS = set()
SEARCH_COUNT = defaultdict(int)
BANNED_USERS = set()
BROADCAST_MODE = {}  # admin_id -> "text"/"photo"

# ---------------- BUTTONS (COMMON) ----------------
def common_buttons(botname):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➡️ ADD ME TO YOUR GROUP",
         url=f"https://t.me/{botname}?startgroup=true")],
        [InlineKeyboardButton("USE ME SECRETLY 🤫",
         url=f"https://t.me/GauravxCyber")]
    ])

# ---------------- ADMIN PANEL BUTTONS ----------------
def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 User Management", callback_data="admin_users")],
        [InlineKeyboardButton("🚫 Ban / Unban User", callback_data="admin_ban")],
        [InlineKeyboardButton("📣 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("❌ Close", callback_data="admin_close")]
    ])

# ---------------- AUTO DELETE ----------------
async def auto_delete(context, chat_id, msg_id):
    await asyncio.sleep(AUTO_DELETE_TIME)
    try:
        await context.bot.delete_message(chat_id, msg_id)
    except:
        pass

# ---------------- HELPERS ----------------
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

async def group_guard(update, context):
    chat = update.effective_chat
    uid = update.effective_user.id

    if uid in BANNED_USERS:
        return False

    if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        msg = await update.message.reply_text(
            "❌ Ye bot sirf GROUP me kaam karta hai.",
            reply_markup=common_buttons(context.bot.username)
        )
        context.application.create_task(
            auto_delete(context, msg.chat.id, msg.message_id)
        )
        return False

    member = await context.bot.get_chat_member(chat.id, context.bot.id)
    if member.status not in ["administrator", "creator"]:
        msg = await update.message.reply_text(
            "⚠️ Bot ko GROUP me ADMIN banana zaroori hai.",
            reply_markup=common_buttons(context.bot.username)
        )
        context.application.create_task(
            auto_delete(context, msg.chat.id, msg.message_id)
        )
        return False

    return True

# ---------------- START ----------------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    USERS.add(uid)

    msg = await update.message.reply_text(
        "❌ Ye bot PRIVATE chat me kaam nahi karta.\n"
        "👉 Neeche button se mujhe GROUP me add karo.",
        reply_markup=common_buttons(context.bot.username)
    )
    context.application.create_task(
        auto_delete(context, msg.chat.id, msg.message_id)
    )

# ---------------- HELP ----------------
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await group_guard(update, context):
        return

    USERS.add(update.effective_user.id)

    text = f"""Hello {update.effective_user.full_name} 👋

🛠️ Bot Commands List:

/num <number> - Mobile Number Info
/num_name <number> - Number to Name Info
/bommber <number> - Phone Bomber (Use with caution!)
/veh <plate> - Vehicle Info
/upi <upi_id> - UPI Info
/ip <ip> - IP Info
/tg <number> - Telegram Info
/ifsc <code> - IFSC Info
/imei <number> - IMEI Info
/family <aadhaar> - Aadhaar Family Info
/aadhar <aadhaar> - Aadhaar Card Info (NEW)
/gst <number> - GST Info
/pan <number> - PAN Card Info
/pak <number> - Pakistan Number Info
/insta <username> - Instagram User Info
/ffinfo <uid> - Free Fire Info
/ff_ban <uid> - Free Fire Ban Status
/github_info <username> - GitHub User Info
/email <email> - Email Address Info

All messages auto-delete after 5 minutes.
"""

    msg = await update.message.reply_text(
        text,
        reply_markup=common_buttons(context.bot.username)
    )
    context.application.create_task(
        auto_delete(context, msg.chat.id, msg.message_id)
    )

# ---------------- ADMIN PANEL COMMAND ----------------
async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    msg = await update.message.reply_text(
        "🔐 ADMIN PANEL",
        reply_markup=admin_menu()
    )
    context.application.create_task(
        auto_delete(context, msg.chat.id, msg.message_id)
    )

# ---------------- ADMIN CALLBACKS ----------------
async def admin_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        return

    if query.data == "admin_users":
        text = (
            f"👥 User Management\n\n"
            f"Total Users: {len(USERS)}\n\n"
            f"Search Stats:\n" +
            "\n".join([f"{uid}: {cnt}" for uid, cnt in SEARCH_COUNT.items()])[:3500]
        )
        await query.edit_message_text(text, reply_markup=admin_menu())

    elif query.data == "admin_ban":
        await query.edit_message_text(
            "🚫 Ban / Unban\n\n"
            "Use commands:\n"
            "/ban <user_id>\n"
            "/unban <user_id>",
            reply_markup=admin_menu()
        )

    elif query.data == "admin_broadcast":
        BROADCAST_MODE[query.from_user.id] = "text"
        await query.edit_message_text(
            "📣 Broadcast Mode\n\n"
            "Ab TEXT bhejo.\n"
            "Photo bhejna ho to photo ke sath caption bhejo.",
            reply_markup=admin_menu()
        )

    elif query.data == "admin_close":
        await query.edit_message_text("❌ Closed")

# ---------------- BAN / UNBAN ----------------
async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        return
    try:
        uid = int(context.args[0])
        BANNED_USERS.add(uid)
        await update.message.reply_text(f"🚫 User {uid} banned.")
    except ValueError:
        await update.message.reply_text("⚠️ Invalid user ID. Please provide a numeric ID.")

async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        return
    try:
        uid = int(context.args[0])
        BANNED_USERS.discard(uid)
        await update.message.reply_text(f"✅ User {uid} unbanned.")
    except ValueError:
        await update.message.reply_text("⚠️ Invalid user ID. Please provide a numeric ID.")

# ---------------- BROADCAST HANDLER ----------------
async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in BROADCAST_MODE:
        return
    if not is_admin(uid):
        return

    sent = 0
    failed = 0
    for user_id in USERS:
        try:
            if update.message.photo:
                await context.bot.send_photo(
                    user_id,
                    update.message.photo[-1].file_id,
                    caption=update.message.caption
                )
            else:
                await context.bot.send_message(user_id, update.message.text)
            sent += 1
        except:
            failed += 1

    BROADCAST_MODE.pop(uid, None)
    await update.message.reply_text(f"📣 Broadcast sent to {sent} users. Failed: {failed}")

# ---------------- REMOVE CREDIT FROM DATA ----------------
def clean_data(data):
    """Remove unwanted fields from the API response data"""
    if isinstance(data, dict):
        # Remove specific unwanted keys
        unwanted_keys = ['credit', 'Time', 'time', 'channel', 'developer', 'Channel', 'Developer', 'AnkuCode', 'trybyte']
        
        for key in unwanted_keys:
            if key in data:
                del data[key]
        
        # Also check for case variations
        for key in list(data.keys()):
            if any(unwanted in str(key).lower() for unwanted in ['credit', 'time', 'channel', 'developer', 'anku', 'trybyte']):
                del data[key]
        
        # Recursively clean nested dictionaries
        for key, value in list(data.items()):
            if isinstance(value, dict):
                data[key] = clean_data(value)
            elif isinstance(value, list):
                # Clean each item in list
                data[key] = [clean_data(item) if isinstance(item, dict) else item for item in value]
    
    return data

# ---------------- API HANDLER (PLEASE WAIT 🙏) ----------------
async def api_call(update, context, url_template, example):
    if not await group_guard(update, context):
        return

    uid = update.effective_user.id
    USERS.add(uid)

    if len(context.args) == 0:
        warn = await update.message.reply_text(
            f"⚠️ Galat use\nExample:\n{example}",
            reply_markup=common_buttons(context.bot.username)
        )
        context.application.create_task(
            auto_delete(context, warn.chat.id, warn.message_id)
        )
        return

    SEARCH_COUNT[uid] += 1

    wait_msg = await update.message.reply_text("⏳ Please wait 10 seconds between requests!")

    value = context.args[0]
    url = url_template.format(value)

    try:
        # Special handling for certain APIs
        if "ff-info" in url or "ff-ban" in url or "github" in url or "pan" in url or "pakistan" in url or "instagram" in url or "num-name" in url or "bomm" in url or "email" in url:
            r = requests.get(url, timeout=30)
        else:
            r = requests.get(url, timeout=20)
        data = r.json()
    except requests.exceptions.Timeout:
        data = {"status": "error", "message": "API timeout - server not responding"}
    except requests.exceptions.RequestException:
        data = {"status": "error", "message": "API connection failed"}
    except json.JSONDecodeError:
        data = {"status": "error", "message": "Invalid JSON response from API"}
    except:
        data = {"status": "error", "message": "Unknown error occurred"}

    try:
        await wait_msg.delete()
    except:
        pass

    # Clean the data by removing credit and other unwanted fields
    cleaned_data = clean_data(data)

    response = {
        "requested_by": "@GauravxCyber",
        "command": update.message.text.split()[0],
        "input": value,
        "result": cleaned_data
    }

    try:
        msg = await update.message.reply_text(
            f"```json\n{json.dumps(response, indent=2)}\n```",
            parse_mode="Markdown",
            reply_markup=common_buttons(context.bot.username)
        )
        context.application.create_task(
            auto_delete(context, msg.chat.id, msg.message_id)
        )
    except:
        # If message is too long, truncate it
        response_str = json.dumps(response, indent=2)
        if len(response_str) > 4000:
            response_str = response_str[:4000] + "\n... (truncated)"
        
        msg = await update.message.reply_text(
            f"```json\n{response_str}\n```",
            parse_mode="Markdown",
            reply_markup=common_buttons(context.bot.username)
        )
        context.application.create_task(
            auto_delete(context, msg.chat.id, msg.message_id)
        )

# ---------------- COMMANDS ----------------
async def num(update, ctx):
    await api_call(update, ctx,
        "https://number={}",
        "/num 9876543210"
    )

async def num_name(update, ctx):
    await api_call(update, ctx,
        "https://number={}",
        "/num_name 9876543210"
    )

async def bommber(update, ctx):
    await api_call(update, ctx,
        "https://phone={}",
        "/bommber 9876543210"
    )

async def veh(update, ctx):
    await api_call(update, ctx,
        "https://vehicle={}",
        "/veh MH02AB1234"
    )

async def upi(update, ctx):
    await api_call(update, ctx,
        "https://upi_id={}",
        "/upi 9999565653@ybl"
    )

async def ip_cmd(update, ctx):
    await api_call(update, ctx,
        "https://={}",
        "/ip 49.47.132.108"
    )

async def tg(update, ctx):
    await api_call(update, ctx,
        "https://Tguserid={}",
        "/tg 7628460325"
    )

async def ifsc(update, ctx):
    await api_call(update, ctx,
        "https://ifsc={}",
        "/ifsc SBIN0000001"
    )

async def imei(update, ctx):
    await api_call(update, ctx,
        "https://-imei{}",
        "/imei 356938035643809"
    )

async def family(update, ctx):
    await api_call(update, ctx,
        "https://{}",
        "/family 123412341234"
    )

# ---------------- NEW AADHAR COMMAND ----------------
async def aadhar(update, ctx):
    await api_call(update, ctx,
        "https://aadhar={}",
        "/aadhar 123456789012"
    )

async def gst(update, ctx):
    await api_call(update, ctx,
        "https://gst={}",
        "/gst 07AAFCB8520Q1Z8"
    )

async def pan(update, ctx):
    await api_call(update, ctx,
        "https://pan={}",
        "/pan ABCDE1234F"
    )

async def pak(update, ctx):
    await api_call(update, ctx,
        "https://number={}",
        "/pak 923001234567"
    )

async def insta(update, ctx):
    await api_call(update, ctx,
        "https://username={}",
        "/insta instagram"
    )

async def ffinfo(update, ctx):
    await api_call(update, ctx,
        "https://uid={}",
        "/ffinfo 1234567890"
    )

async def ff_ban(update, ctx):
    await api_call(update, ctx,
        "https://uid={}",
        "/ff_ban 1234567890"
    )

async def github_info(update, ctx):
    await api_call(update, ctx,
        "https://username={}",
        "/github_info octocat"
    )

async def email(update, ctx):
    await api_call(update, ctx,
        "https://mail={}",
        "/email example@domain.com"
    )

# ---------------- RUN ----------------
app = ApplicationBuilder().token(BOT_TOKEN).build()

# Basic commands
app.add_handler(CommandHandler("start", start_cmd))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(CommandHandler("admin", admin_cmd))
app.add_handler(CommandHandler("ban", ban_cmd))
app.add_handler(CommandHandler("unban", unban_cmd))

# Info commands
app.add_handler(CommandHandler("num", num))
app.add_handler(CommandHandler("num_name", num_name))
app.add_handler(CommandHandler("bommber", bommber))
app.add_handler(CommandHandler("veh", veh))
app.add_handler(CommandHandler("upi", upi))
app.add_handler(CommandHandler("ip", ip_cmd))
app.add_handler(CommandHandler("tg", tg))
app.add_handler(CommandHandler("ifsc", ifsc))
app.add_handler(CommandHandler("imei", imei))
app.add_handler(CommandHandler("family", family))
app.add_handler(CommandHandler("aadhar", aadhar))  # NEW AADHAR COMMAND
app.add_handler(CommandHandler("gst", gst))
app.add_handler(CommandHandler("pan", pan))
app.add_handler(CommandHandler("pak", pak))
app.add_handler(CommandHandler("insta", insta))
app.add_handler(CommandHandler("ffinfo", ffinfo))
app.add_handler(CommandHandler("ff_ban", ff_ban))
app.add_handler(CommandHandler("github_info", github_info))
app.add_handler(CommandHandler("email", email))

# Callback and message handlers
app.add_handler(CallbackQueryHandler(admin_callbacks))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_handler))

print("🔥 Gaurav Cyber Bot Devloper...")
app.run_polling()