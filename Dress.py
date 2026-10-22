# API DEVELOPER:- @GauravxcyberApi
# ALL API AVAILABLE DM ID :- @GauravxcyberApi
import requests
import asyncio
import logging
import base64
import aiohttp   # ✅ added
import os        # ✅ added
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --------------------- ULTRA PROTECTED API ---------------------
ENCODED_API = "aHR0cHM6Ly9qdWJheWVyLWRyZXNzLWFwaS52ZXJjZWwuYXBwL3BsYXllci1kcmVzcy1zaW1wbGU="

YOUR_API_URL = base64.b64decode(ENCODED_API).decode('utf-8')

BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

API_TIMEOUT = 20
# -----------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        text="🎮 *FREE FIRE PLAYER DRESS BOT*\n\n"
             "*Commands:*\n"
             "/help - Show help\n"
             "/dress <UID> - Get player dresses\n\n"
             "*Example:* `/dress 5682151559`",
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        text="📚 *HOW TO USE:*\n\n"
             "*1.* *Get dresses with UID:*\n"
             "`/dress 5682151559`\n\n"
             "*2.* *Example:*\n"
             "`/dress 5682151559`\n\n"
             "*Bot Status:* Active ✅",
        parse_mode='Markdown'
    )

async def dress_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logging.info(f"User {user.id} requested dress for UID: {context.args}")

    if not context.args:
        await update.message.reply_text(
            text="❌ *PLEASE PROVIDE A UID!*\n\n*Example:* `/dress 5682151559`",
            parse_mode='Markdown'
        )
        return

    uid = context.args[0]

    if not uid.isdigit():
        await update.message.reply_text(
            text=f"❌ *INVALID UID FORMAT!*\n\n*Example:* `/dress 5682151559`",
            parse_mode='Markdown'
        )
        return

    loading_msg = await update.message.reply_text(
        text=f"🔄 *FETCHING DRESSES FOR UID:* `{uid}`...\n\n*Please wait* ⏳",
        parse_mode='Markdown'
    )

    try:
        # ✅ FIXED: async request
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{YOUR_API_URL}?uid={uid}", timeout=API_TIMEOUT) as response:

                if response.status == 200:
                    try:
                        data = await response.json()
                    except:
                        await loading_msg.edit_text("❌ *Invalid API response*", parse_mode='Markdown')
                        return

                    if data.get('status') == 'success':
                        player = data['player']
                        dress = data['dress']

                        info_text = (
                            f"🎮 *{player['name']}*\n"
                            f"🆔 *UID:* `{player['uid']}`\n"
                            f"📍 *Region:* {player['region']}\n"
                            f"⭐ *Level:* {player['level']}\n"
                            f"📦 *Total Items:* {data['total']}\n\n"
                            f"👕 *Clothes:* {len(dress['clothes'])} items\n"
                            f"🔫 *Weapons:* {len(dress['weapons'])} items"
                        )
                        await loading_msg.edit_text(text=info_text, parse_mode='Markdown')

                        if dress['clothes']:
                            await update.message.reply_text(text="👕 *PLAYER CLOTHES:*", parse_mode='Markdown')
                            for idx, url in enumerate(dress['clothes'], 1):
                                try:
                                    await update.message.reply_photo(photo=url, caption=f"Cloth {idx}/{len(dress['clothes'])}")
                                    await asyncio.sleep(0.3)
                                except Exception as e:
                                    print(e)
                                    await update.message.reply_text(text=f"⚠️ *Could not load cloth {idx}*", parse_mode='Markdown')

                        if dress['weapons']:
                            await update.message.reply_text(text="🔫 *PLAYER WEAPONS:*", parse_mode='Markdown')
                            for idx, url in enumerate(dress['weapons'], 1):
                                try:
                                    await update.message.reply_photo(photo=url, caption=f"Weapon {idx}/{len(dress['weapons'])}")
                                    await asyncio.sleep(0.3)
                                except Exception as e:
                                    print(e)
                                    await update.message.reply_text(text=f"⚠️ *Could not load weapon {idx}*", parse_mode='Markdown')

                        await update.message.reply_text(text="✅ *COMPLETE!*", parse_mode='Markdown')

                    else:
                        await loading_msg.edit_text(text=f"❌ *FAILED!*\n\n*Check UID:* `{uid}`", parse_mode='Markdown')
                else:
                    await loading_msg.edit_text(text=f"❌ *API ERROR*", parse_mode='Markdown')

    except asyncio.TimeoutError:
        await loading_msg.edit_text(text="⏰ *TIMEOUT!*\n\n*Try again*", parse_mode='Markdown')
    except Exception as e:
        print(e)
        await loading_msg.edit_text(text=f"❌ *ERROR*", parse_mode='Markdown')


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Error: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            text="⚠️ *ERROR OCCURRED*\n\n*Try again later*",
            parse_mode='Markdown'
        )

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("dress", dress_command))
    application.add_error_handler(error_handler)

    print("🤖 Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()