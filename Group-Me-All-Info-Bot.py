import json
import requests
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.constants import ChatType

BOT_TOKEN = "AAPNA BOT TOKEN ADD KRO"
AUTO_DELETE_TIME = 300  # 5 minutes

# ---------------- BUTTONS (PHOTO STYLE) ----------------
def buttons(botname):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "➡️ ADD ME TO YOUR GROUP",
                url=f"https://t.me/{botname}?startgroup=true"
            )
        ],
        [
            InlineKeyboardButton(
                "USE ME SECRETLY 🤫",
                url=f"https://t.me/GauravxCyber{botname}"
            )
        ]
    ])

# ---------------- AUTO DELETE ----------------
async def auto_delete(context, chat_id, msg_id):
    await asyncio.sleep(AUTO_DELETE_TIME)
    try:
        await context.bot.delete_message(chat_id, msg_id)
    except:
        pass

# ---------------- GROUP + ADMIN CHECK ----------------
async def group_guard(update, context):
    chat = update.effective_chat

    if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        msg = await update.message.reply_text(
            "❌ Ye bot sirf GROUP me kaam karta hai.\n"
            "👉 Neeche button se mujhe group me add karo.",
            reply_markup=buttons(context.bot.username)
        )
        context.application.create_task(
            auto_delete(context, msg.chat.id, msg.message_id)
        )
        return False

    member = await context.bot.get_chat_member(chat.id, context.bot.id)
    if member.status not in ["administrator", "creator"]:
        msg = await update.message.reply_text(
            "⚠️ Bot ko GROUP me ADMIN banana zaroori hai.",
            reply_markup=buttons(context.bot.username)
        )
        context.application.create_task(
            auto_delete(context, msg.chat.id, msg.message_id)
        )
        return False

    return True

# ---------------- START ----------------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE:
        msg = await update.message.reply_text(
            "❌ Ye bot PRIVATE chat me kaam nahi karta.\n\n"
            "👉 Neeche diye button se mujhe GROUP me add karo.",
            reply_markup=buttons(context.bot.username)
        )
        context.application.create_task(
            auto_delete(context, msg.chat.id, msg.message_id)
        )
    else:
        msg = await update.message.reply_text(
            "✅ Bot active hai.\n/help likho commands ke liye.",
            reply_markup=buttons(context.bot.username)
        )
        context.application.create_task(
            auto_delete(context, msg.chat.id, msg.message_id)
        )

# ---------------- HELP ----------------
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await group_guard(update, context):
        return

    text = f"""Hello {update.effective_user.full_name} 👋

🛠️ Bot Commands List:

/num <number> - Mobile Number Info
/veh <plate> - Vehicle Info
/upiinfo <upi> - UPI Info
/fam <id> - FAM Info
/insta <username> - Instagram Info
/ip <ip> - IP Info
/email <email> - Email Info
/tg <number> - Telegram Info
/ifsc <code> - IFSC Info
/adhar <number> - Aadhaar Info
/imei <number> - IMEI Info
/pak <number> - Pak Number Info
/family <aadhaar> - Aadhaar Family Info
/gst <number> - GST Info

All messages auto-delete after 5 minutes.
"""

    msg = await update.message.reply_text(
        text,
        reply_markup=buttons(context.bot.username)
    )
    context.application.create_task(
        auto_delete(context, msg.chat.id, msg.message_id)
    )

# ---------------- API HANDLER ----------------
async def api_call(update, context, url_template, example):
    if not await group_guard(update, context):
        return

    if len(context.args) == 0:
        warn = await update.message.reply_text(
            f"⚠️ Galat use\nExample:\n{example}",
            reply_markup=buttons(context.bot.username)
        )
        context.application.create_task(
            auto_delete(context, warn.chat.id, warn.message_id)
        )
        return

    value = context.args[0]
    url = url_template.format(value)

    try:
        r = requests.get(url, timeout=15)
        data = r.json()
    except:
        data = {"status": "error", "message": "API not responding"}

    response = {
        "requested_by": update.effective_user.full_name,
        "command": update.message.text.split()[0],
        "input": value,
        "result": data
    }

    msg = await update.message.reply_text(
        f"```json\n{json.dumps(response, indent=2)}\n```",
        parse_mode="Markdown",
        reply_markup=buttons(context.bot.username)
    )

    context.application.create_task(
        auto_delete(context, msg.chat.id, msg.message_id)
    )

# ---------------- COMMANDS ----------------
async def num(update, ctx):
    await api_call(update, ctx,
        "https://{}",
        "/num 9876543210"
    )

async def veh(update, ctx):
    await api_call(update, ctx,
        "https://{}",
        "/veh MH02AB1234"
    )

async def tg(update, ctx):
    await api_call(update, ctx,
        "https://{}",
        "/tg 7628460325"
    )

async def ifsc(update, ctx):
    await api_call(update, ctx,
        "https://{}",
        "/ifsc SBIN0000001"
    )

async def imei(update, ctx):
    await api_call(update, ctx,
        "https://{}",
        "/imei 356938035643809"
    )

async def family(update, ctx):
    await api_call(update, ctx,
        "https://{}",
        "/family 123412341234"
    )

async def gst(update, ctx):
    await api_call(update, ctx,
        "https://{}",
        "/gst 07AAFCB8520Q1Z8"
    )

# ---------------- RUN ----------------
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start_cmd))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(CommandHandler("num", num))
app.add_handler(CommandHandler("veh", veh))
app.add_handler(CommandHandler("tg", tg))
app.add_handler(CommandHandler("ifsc", ifsc))
app.add_handler(CommandHandler("imei", imei))
app.add_handler(CommandHandler("family", family))
app.add_handler(CommandHandler("gst", gst))

print("🔥 Gaurav Cyber Bot Devloper...")
app.run_polling()