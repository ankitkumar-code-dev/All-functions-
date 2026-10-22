# ---------------------------
# 𝐆ᴀᴜʀᴀᴠ !! 𝐇ᴀᴄᴋᴇʀs
# ---------------------------
import subprocess
import importlib
import sys
#======================
# Packages auto-installer
#======================
REQUIRED_PACKAGES = {
    "telegram": "python-telegram-bot",
    "gtts": "gTTS",
    "requests": "requests",
    "httpx": "httpx",    
}

for module_name, package_name in REQUIRED_PACKAGES.items():
    try:
        importlib.import_module(module_name)
    except ImportError:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        except Exception:
            sys.exit(1) 

def check_branding():
    try:
        with open(__file__, 'r', encoding='utf-8') as f:
            content = f.read()
            
            if "𝐆ᴀᴜʀᴀᴠ !! 𝐇ᴀᴄᴋᴇʀs" not in content:
                print("Error: Unauthorized Modification Detected!")
                print("Original branding missing. Closing script...")
                sys.exit()
    except Exception:
        sys.exit()

check_branding()

print("Script started successfully!")

import os
import re
import asyncio
import sys
import shutil
import random
import requests
import base64
import json
import time
from gtts import gTTS
import getpass
from typing import Dict, List
import logging
from urllib.parse import quote
from datetime import datetime, timezone, timedelta

sys.stdout.reconfigure(encoding='utf-8')
from telegram.constants import ParseMode
from telegram import error as telegram_error
from telegram import InputFile, Update, Bot, ChatPermissions

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ChatMemberHandler,
    filters
)

IST = timezone(timedelta(hours=5, minutes=30))
# ==================
#        A D D   U S E R  I D
# ==================
OWNER_ID = 8824267480
# ==================
#       A D D   T O K E N'S
# ==================
TOKENS = [ "8605187927:AAGj2J5BndV05qGuqVLztSOXuyapaJY9Lro",
"8882930755:AAEQIn7U8ccf98ZEFRI5ZPawGN7LFbYEm64",
"8839273794:AAEkvlfaTIRcSDBCVUBJOJcjZTS0MdRaF38",
"8888451529:AAEBcKIHFUaRZBzgz33v6QeV6dErdH5isS0",
"8988987607:AAF32ZCvUsbrg6qyhjS9i5pi9np4g01dhW0",
"8757885679:AAGcS35Q66QXCdDsAkSJhgQ2-dBDASsSGd4",
"8957107690:AAFhfsXR3erLGbQoVmhkUF9FEJ2JazcVQpw",
"8847021681:AAH4ASoWven3Y9gINVSIj9K0cVp84X4EErU",
"8987230818:AAHfJJevnL7nQXcfyjxRrz90AzN-pP8eaWo",
"8763541141:AAGUcL2w5sMQS7w2IFO4XLsh9Pr5ZP8BKeQ",
"8671637643:AAHKxZPmSbxpDDXYha_tLMd4BLio6t8g6Zo",
"8816944532:AAGxP4JBp5Rfa8A87-CU6AdVQdGXLsHymFQ",
"8002208559:AAE_1zSGgbPU0GomyOR6FajqceGxiXL9020",
"8651141953:AAG9lD4bdryl18lQlVPD46rA9hpCoiAtFN0",
"8895467627:AAG9XQApH1bwRW7faUFQnuCtmZg5PD_geZw",
"8639903172:AAH5BmXg7tOGIvbincI_ZpV3RB5wertQbkI",
"8971084905:AAGjTxB17E8tuYn37c0-UQ6F4KhNTWJM1iI",
"8954881655:AAHzS8a5kouO1y9hc_p-ecCSypWhU3RMlko",
"8937218693:AAHu_Ud9Xn2ZvzMdHTNedwrbrhDa4Mhp91A",
"8974881887:AAHXBN9WJf24qL9isdlExcYn-DomPXAgfM4",
"8910179231:AAFjxaHig-TdVMYinEqrFx0ywWVmxPwO7SM",
] 
# ---------------------------
# Add Here Gc link
# ---------------------------
GC_LINKS = [
    "add link 1",
    "add link 2",
    "add link 3",
    "add link 4",
    "add link 5",
    "add link 6",
    "add link 7",
    "add link 8",
    "add link 9",
    "add link 10"
]
# ==================
#       Normal Nc Emo
# ==================
Emoji_list = [
"〘🇮🇳〙", "〘🇮🇷〙", "〘🇯🇵〙", "〘🇰🇷〙", "〘🇰🇼〙", "〘🇸🇦〙", "〘🇺🇳〙", "〘🇱🇰〙", "〘🇮🇶〙", "〘🇬🇧〙", "〘🇨🇳〙", "〘🇦🇴〙", "〘🇦🇪〙", "〘🇦🇷〙", "〘🇦🇹〙", "〘🇦🇽〙", "〘🇮🇸〙", "〘🇲🇺〙", "〘🇧🇩〙", "〘🇱🇺〙", "〘🇱🇻〙", "〘🇲🇱〙", "〘🇲🇨〙", "〘🇷🇺〙", "〘🇺🇲〙", "〘🇾🇪〙", "〘🇵🇰〙", "〘🇮🇱〙", "〘🇦🇫〙", "〘🇸🇬〙", "〘🇭🇰〙", "〘🇦🇺〙", "〘🇧🇸〙", "〘🇨🇾〙", "〘🇬🇭〙", "〘🇱🇷〙", "〘🇲🇶〙", "〘🇸🇧〙", "〘🇵🇭〙", "〘🇹🇻〙", "〘🇹🇿〙", "〘🇻🇨〙", "〘🇬🇲〙", "〘🇬🇳〙", "〘🇬🇫〙", "〘🇨🇽〙", "〘🇱🇸〙", "〘🇵🇭〙"
]
# ==================
#       Speed Nc Emo
# ==================
Emojis_list = [
"〘🇬🇺〙", "〘🇬🇼〙", "〘🇭🇰〙", "〘🇭🇳〙", "〘🇭🇷〙", "〘🇭🇹〙", "〘🇮🇨〙", "〘🇯🇪〙", "〘🇰🇮〙", "〘🇰🇬〙", "〘🇱🇸〙", "〘🇱🇦〙", "〘🇰🇿〙", "〘🇰🇾〙", "〘🇱🇾〙", "〘🇱🇨〙", "〘🇲🇪〙", "〘🇲🇴〙", "〘🇲🇵〙", "〘🇳🇬〙", "〘🇳🇺〙", "〘🇸🇴〙", "〘🇸🇳〙", "〘🇾🇹〙", "〘🇹🇱〙", "〘🇹🇳〙", "〘🇹🇴〙", "〘🇻🇮〙", "〘🇻🇺〙", "〘🇭🇰〙", "〘🇹🇰〙", "〘🇸🇲〙", "〘🇸🇰〙", "〘🇸🇹〙", "〘🇸🇸〙", "〘🇸🇨〙", "〘🇷🇸〙", "〘🇵🇼〙", "〘🇵🇷〙", "〘🇵🇦〙", "〘🇴🇲〙", "〘🇵🇬〙", "〘🇳🇷〙", "〘🇲🇼〙"
]
reply_list = ["#𝐆ᴀᴜʀᴀᴠ !! 🪽 𝐊ᴏ 𝐁ᴀᴀᴘ 𝐁ᴀɴᴀ 𝐋ᴇ 𝐑ᴀɴᴅɪ 𝐊ᴇ  𝐁ᴀᴄʜᴇ", "𝐌ᴜᴊʜᴇ 𝐏ᴀᴘᴀ  𝐁ᴏʟ 𝐑ᴀɴᴅɪ 🤣", "𝐓ᴇʀɪ 𝐌ᴀᴀ 𝐂ʜᴜᴅᴡᴀ 𝐋ᴇ 𝐘ᴀʜᴀ 😀", "𝐑ʀ 𝐊ᴀʀ 𝐑ᴀɴᴅɪ 𝐊ᴇ 𝐁ᴀᴄʜᴇ 😃", "𝐌ᴇʀᴇ 𝐒ᴇ 𝐌ᴀᴀ 𝐂ʜ𝐮ᴅᴡᴀ 𝐋ᴇ 𝐒ʟɪᴅᴇ 𝐊ᴀʀ 𝐊ᴇ !!", "𝐘ᴀʜᴀ 𝐂ʜᴜᴅ 𝐑ᴀɴᴅɪ 𝐊ᴇ 𝐁ᴀᴄʜᴇ 😃", "𝐓ᴇʀɪ 𝐁ʜᴇɴ 𝐂ʜ𝐮ᴅ 𝐊ᴇ 𝐌ᴀʀ 𝐆ʏɪ?", "𝐌ᴀᴀ 𝐂ʜ𝐝ᴡᴀ 𝐋ᴇ 𝐓ᴇʀɪ 🤣", "𝐌ᴜᴊʜᴇ 𝐏ᴀᴘᴀ  𝐁ᴏʟ 𝐑ᴀɴᴅɪ 🤣",
    "𝐓ᴇʀɪ 𝐌ᴀᴀ 𝐂ʜᴜᴅᴡᴀ 𝐋ᴇ 𝐘ᴀʜᴀ 😀",
    "𝐑ʀ 𝐊ᴀʀ 𝐑ᴀɴᴅɪ 𝐊ᴇ 𝐁ᴀᴄʜᴇ 😃",
    "𝐌ᴇʀᴇ 𝐒ᴇ 𝐌ᴀᴀ 𝐂ʜ𝐮ᴅᴡᴀ 𝐋ᴇ 𝐒ʟɪᴅᴇ 𝐊ᴀʀ 𝐊ᴇ !!",
    "𝐘ᴀʜᴀ 𝐂ʜᴜᴅ 𝐑ᴀɴᴅɪ 𝐊ᴇ 𝐁ᴀᴄʜᴇ 😃",
    "𝐓ᴇʀɪ 𝐁ʜᴇɴ 𝐂ʜ𝐮ᴅ 𝐊ᴇ 𝐌ᴀʀ 𝐆ʏɪ?",
    "𝐌ᴀᴀ 𝐂ʜ𝐝ᴡᴀ 𝐋ᴇ 𝐓ᴇʀɪ 🤣", "𝑯𝒂𝒘𝒂𝒃𝒂𝒂𝒛𝒊 𝒌𝒂𝒓 𝒇𝒂𝒎𝒆 𝒎𝒊𝒍𝒆 𝒈𝒂!", "𝐓𝐦𝐤𝐜 𝐎𝐤", "𝐓𝐞𝐫𝐢 𝐦𝐚𝐚 150𝐫𝐬 𝐦𝐞 𝐝𝐞𝐭𝐢 𝐡𝐚𝐢 😃", "𝑺𝒍𝒊𝒅𝒆 𝒌𝒂𝒓 𝒎𝒂𝒅𝒓𝒄𝒉𝒐𝒅!", "𝑪𝒉𝒖𝒅 𝒐𝒏𝒍𝒊𝒏𝒆 𝒇𝒚𝒕𝒓!", "𝑩𝒉𝒂𝒘 𝒅𝒖 𝒓𝒓 𝒘𝒉𝒚 𝑹𝒂𝒏𝒅𝒊?", "𝑳𝒐𝒍 𝒂𝒊𝒔𝒆 𝒓𝒐𝒚𝒆 𝒈𝒂 😀", "𝑹𝒐 𝑹𝒐 𝑹𝒐 𝒕𝒆𝒓𝒊 𝒎𝒂𝒂 𝒕𝒐𝒉 𝒄𝒉𝒖𝒅 𝒌𝒊 𝒉𝒂𝒔𝒉 𝒓𝒉𝒊 😃", "𝐂𝐡𝐮𝐝 𝐠𝐚𝐫𝐞𝐞𝐛!", "𝐌𝐤𝐜 𝐧𝐨 𝐛𝐡𝐚𝐰 𝐭𝐚𝐭𝐭𝐞!", "𝐋𝐨𝐥 𝐜𝐡𝐮𝐝 𝐤𝐢 𝐫𝐨 𝐫𝐡𝐚 𝐚𝐛𝐡 𝐡𝐚𝐰𝐚𝐛𝐚𝐚𝐳 🤣", "𝐀𝐰𝐰 𝐑𝐚𝐧𝐝𝐢 𝐭𝐞𝐫𝐢 𝐦𝐚𝐚 𝐭𝐨𝐡 𝐜𝐡𝐮𝐝 𝐠𝐲𝐢!", "𝑩𝒐𝒉𝒐𝒕 𝒄𝒉𝒖𝒅𝒊 𝒕𝒉𝒊 𝑻𝒆𝒓𝒊 𝒎𝒂𝒂 𝒓𝒂𝒂𝒕 𝒌𝒐 𝒎𝒆𝒓𝒆 𝒔𝒆 😀", "𝐇ᴀsʏ ʜᴀsʏ 𝐂ʜᴜᴅ ᴄʜᴜᴅ 𝐊ɪ 𝐓ᴇʀɪ ᴍᴀᴀ 𝐇ᴀsʏ 😄", "𝐍𝐡𝐢 𝐧𝐡𝐢 𝐧𝐡𝐢 𝐚𝐛𝐡 𝐭𝐨𝐡 𝐭𝐞𝐫𝐢 𝐦𝐚𝐚 𝐜𝐡𝐮𝐝 𝐤𝐢 𝐫𝐚𝐡𝐞 𝐠𝐢 ! 😗", "𝐍𝐡𝐢 𝐧𝐡𝐢 𝐧𝐡𝐢 𝐚𝐛𝐡𝐢𝐣𝐞𝐞𝐭 𝐢𝐬𝐬 𝐭𝐚𝐭𝐭𝐞 𝐤𝐢 𝐦𝐚𝐚 𝐭𝐨𝐡 𝐜𝐡𝐮𝐝𝐢 𝐠𝐢 ! 🙂‍↔️", "𝐊𝐘𝐔 𝐅𝐘𝐓𝐑 𝐁𝐀𝐍 𝐊𝐈 𝐌𝐀𝐀 𝐂𝐇𝐔𝐃𝐖𝐀 𝐋𝐄 ? 😀", "𝐍𝐇𝐈 𝐍𝐇𝐈 𝐀𝐁𝐇 𝐊𝐔𝐂𝐇 𝐍𝐇𝐈 𝐇𝐎 𝐒𝐀𝐊𝐓𝐀 𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐈 𝐂𝐇𝐔𝐃𝐀𝐈 𝐊𝐈 𝐒𝐂𝐑𝐈𝐏𝐓 𝐑𝐄𝐀𝐃𝐘 𝐇𝐎 𝐆𝐘𝐈 𝐇𝐀𝐈 𝐀𝐁𝐇 𝐁𝐀𝐒 𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐂𝐇𝐔𝐃 𝐇𝐄 𝐒𝐀𝐊𝐓𝐈 𝐇𝐀𝐈 ! 😃", "𝐁𝐄𝐓𝐀 𝐘𝐀𝐀𝐃 𝐍𝐇𝐈 𝐀𝐀𝐑𝐀 𝐖𝐎𝐇 𝐊𝐎𝐍𝐒𝐀 𝐉𝐀𝐃𝐔 𝐓𝐇𝐀 𝐉𝐎 𝐔𝐒𝐒 𝐑𝐀𝐀𝐓 𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐈 𝐒𝐀𝐓𝐇 𝐊𝐈𝐘𝐀 𝐓𝐇𝐀 𝐉𝐎 𝐓𝐔 𝐀𝐀𝐘𝐀 𝐃𝐔𝐍𝐈𝐘𝐀 𝐌𝐄 🙂‍↔️", "𝐂𝐎𝐎𝐋 𝐁𝐀𝐍 𝐆𝐀𝐘𝐀 𝐁𝐄𝐓𝐀 𝐁𝐀𝐀𝐏 𝐊𝐈 𝐂𝐎𝐏𝐘 𝐇𝐀𝐀 𝐀𝐀𝐊𝐄𝐑 𝐁𝐄𝐓𝐀 𝐌𝐄𝐑𝐀 𝐇𝐀𝐈! 🥳", "𝐀𝐑𝐄 𝐂𝐇𝐔𝐃 𝐊𝐈 𝐁𝐇𝐀𝐆 𝐊𝐘𝐔 𝐑𝐇𝐈 𝐇𝐎 𝐑𝐀𝐍𝐃𝐈 𝐓𝐇𝐎𝐃𝐈 𝐆𝐀𝐍𝐃 𝐇𝐀𝐌 𝐒𝐄 𝐁𝐇𝐈 𝐌𝐀𝐀𝐑𝐖𝐀 𝐋𝐎 😁", "𝐇𝐀𝐌 𝐂𝐈𝐃 𝐒𝐄 𝐇𝐀𝐈 𝐓𝐔𝐌𝐀𝐑𝐄 𝐌𝐀𝐀 𝐊𝐈 𝐋𝐄𝐍𝐄 𝐀𝐀𝐘𝐄 𝐇𝐀𝐈 𝐁𝐀𝐃𝐄 𝐃𝐈𝐍𝐎 𝐁𝐀𝐀𝐃 😔", "𝐊𝐘𝐀 𝐇𝐔𝐀 𝐑𝐀𝐍𝐃𝐈 𝐓𝐇𝐎𝐃𝐈 𝐁𝐊𝐂 𝐇𝐀𝐌𝐍𝐄 𝐊𝐘𝐀 𝐊𝐀𝐑 𝐋𝐄 𝐓𝐔𝐌 𝐓𝐎𝐇 𝐑𝐎𝐍𝐄 𝐋𝐀𝐆 𝐆𝐘𝐀 🤗", "𝐑𝐀𝐍𝐃𝐈 𝐂𝐕𝐑 𝐊𝐀𝐑𝐍𝐀 𝐉𝐀𝐑𝐔𝐑𝐈 𝐇𝐀𝐈 𝐍𝐇𝐈 𝐓𝐎𝐇 𝐀𝐀𝐏 𝐊𝐈 𝐌𝐀𝐀 9 𝐌𝐎𝐍𝐓𝐇𝐒 𝐂𝐕𝐑 𝐍𝐇𝐈 𝐊𝐀𝐑 𝐏𝐀𝐘𝐄 𝐆𝐈 🤭", "𝐊𝐘𝐔 𝐑𝐄𝐄 𝐌𝐀𝐃𝐀𝐑𝐂𝐇𝐎𝐃 𝐘𝐀𝐇𝐀 𝐂𝐇𝐎𝐏 𝐊𝐈 𝐌𝐀𝐀 𝐂𝐇𝐔𝐃𝐖𝐀 𝐑𝐀𝐇𝐀 𝐇𝐀𝐈 𝐁𝐇𝐄𝐍𝐂𝐇𝐎𝐃 🙂‍↕️", "𝐌𝐄𝐈𝐍 𝐇𝐔 𝐀𝐊𝐄𝐋𝐀 𝐌𝐄𝐑𝐄 𝐏𝐀𝐒𝐒 𝐇𝐀𝐈 𝐊𝐀𝐋𝐀 𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐎 𝐏𝐈𝐋𝐄 𝐑𝐀𝐀𝐓 𝐃𝐈𝐍 𝐓𝐇𝐀𝐊𝐄𝐋𝐀 😄", "𝐀𝐀𝐉𝐀 𝐑𝐀𝐍𝐃𝐈 𝐅𝐘𝐓𝐑 𝐁𝐀𝐍𝐀𝐓𝐀 𝐇𝐔 𝐀𝐁𝐇𝐈𝐉𝐄𝐄𝐓 𝐈𝐒 𝐑𝐀𝐍𝐃𝐈 𝐊𝐎 𝐅𝐘𝐓 𝐒𝐈𝐊𝐇𝐀𝐎 😃", "𝐀𝐀𝐉 𝐊𝐈 𝐓𝐀𝐉𝐀 𝐊𝐇𝐀𝐁𝐀𝐑 𝐈𝐒 𝐓𝐀𝐓𝐓𝐀 𝐊𝐈 𝐌𝐀𝐀  𝐂𝐇𝐔𝐃𝐄 𝐆𝐇𝐀𝐑 𝐆𝐇𝐀𝐑 ! 😀", "𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐂𝐇𝐔𝐃 𝐆𝐘𝐈 𝐓𝐎𝐇 𝐈𝐒𝐌𝐄 𝐁𝐇𝐈 𝐌𝐄𝐑𝐈 𝐆𝐀𝐋𝐓𝐈 ! 😙", "𝐀𝐑𝐄𝐄 𝐁𝐄𝐓𝐀 𝐓𝐔 𝐓𝐎𝐇 𝐁𝐊𝐂 𝐁𝐊𝐂 𝐌𝐄 𝐇𝐄 𝐂𝐇𝐔𝐃 𝐆𝐀𝐘𝐀??"]
# ==================
#          S U D O   F I L E
# ==================
SUDO_FILE = "admin_data.json"

def load_sudo():
    try:
        with open(SUDO_FILE, "r") as f:
            data = json.load(f)

        if not isinstance(data, list):
            data = []

    except:
        data = []

    if OWNER_ID not in data:
        data.append(OWNER_ID)
        save_sudo(data)

    return data

def save_sudo(data):
    with open(SUDO_FILE, "w") as f:
        json.dump(data, f, indent=4)

admins_USERS = load_sudo()

def refresh_sudo():
    global admins_USERS
    admins_USERS = load_sudo()

def is_sudo(user_id):
    return user_id == OWNER_ID or user_id in admins_USERS
# =========================
# Helper: Save JSON
# =========================
def save_json(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
# =========================
#                           img api
# =========================
def generate_image(prompt: str) -> str:
    return "https://image.pollinations.ai/prompt/" + quote(prompt)  
# ---------------------------
#        Video (URLs)
# ---------------------------
HELP_VIDEO_URL = "https://files.catbox.moe/oj0fxa.mp4"
EASY_VIDEO_URL = "https://files.catbox.moe/86wgir.mp4"
STATUS_VIDEO_URL = "https://files.catbox.moe/8dy8gz.mp4"
GAME_VIDEO_URL = "https://files.catbox.moe/iz1hmi.mp4"
GUN_VIDEO_URL = "https://files.catbox.moe/vzjmae.mp4"
LOAD_VIDEO_URL = "https://files.catbox.moe/5c186z.mp4"
SAFE_VIDEO_URL = "https://files.catbox.moe/ki1847.mp4" 
OVER_VIDEO_URL = "https://files.catbox.moe/2pltx5.mp4"
NCS_VIDEO_URL = "https://files.catbox.moe/pftth4.mp4"
INFO_VIDEO_URL = "https://files.catbox.moe/hdm7g9.mp4"
LIST_SUDO_VIDEO_URL = "https://files.catbox.moe/vtlpsa.mp4"
MYHOST_VIDEO_URL = "https://files.catbox.moe/q11g7k.mp4" 
# ==================
#                 M A I N
# ==================
def only_sudo(func):
    async def wrapper(update, context):
        if not is_sudo(update.effective_user.id):
            return await update.message.reply_text("")
        return await func(update, context)
    return wrapper

def only_owner(func):
    async def wrapper(update, context):
        if update.effective_user.id != OWNER_ID:
            return await update.message.reply_text("𝑂𝑛𝑙𝑦 𝑌𝑜𝑢𝑟𝑠 𝐶𝑎𝑛 𝐷𝑜 𝑇𝒉𝑖𝑠 𝑂𝑘 𝑁𝑖𝑔𝑔𝑎 𝑠𝒉𝑖𝑡'𝑠...' ♥️ ~")
        return await func(update, context)
    return wrapper
# ==================
#               T A S K'S
# ==================
nc_tasks = {}
speed_tasks = {}
spam_tasks = {}
reply_tasks = {}
sticker_tasks = {}
photo_tasks = {}
pfp_tasks = {}
folder_messages = {}
host_db = {}          
running_process = {}
ROULETTE_GAMES = {}
ttt_games = {}
nc_success_count = 0
nc_error_count = 0
EMOJIS = Emojis_list
admins_USERS = load_sudo()

DELAY = 2
SPAM_DELAY = 0.8
custom_speed_delay = 1.0

bots = []

for token in TOKENS:
    try:
        bots.append(Bot(token))
    except:
        pass
        
def key(context, chat_id):
    return (context.bot.id, chat_id)
# ==================
#          Group Leave
# ==================
async def left_member_handler(update, context):
    
    if context.bot.token != TOKENS[0]:
        return

    if not update.message or not update.message.left_chat_member:
        return

    chat_id = update.effective_chat.id
    group_name = update.effective_chat.title or "Group"
    user = update.message.left_chat_member
    
    first_name = user.first_name if user.first_name else "User"
    username = f"@{user.username}" if user.username else "N/A"
    
  
    msg_date = update.message.date.astimezone(IST)
    time_str = msg_date.strftime("%I:%M %p")
    date_str = msg_date.strftime("%d/%m/%Y")
    day_str = msg_date.strftime("%A")

    leave_msg_text = (
        "╔═════════════════╗\n"
        "‎                              \n"
        "‎           𝐆ᴀᴜʀᴀᴠ !! 𝐇ᴀᴄᴋᴇʀs\n"
        "‎                             \n"
        "╚═════════════════╝\n"
        f"𝐓ɪᴍᴇ: {time_str} {date_str}\n"
        f"𝐃ᴀʏ: {day_str}\n"
        f"𝐍ᴀᴍᴇ: {first_name}\n"
        f"𝐔sᴇʀɴᴀᴍᴇ: {username}\n"
        f"𝐆ʀᴏᴜᴘ: {group_name}\n"
        "╔═════════════════╗\n\n"
        "             𝐅ᴇᴀʀ𝐎ғ𝐆ᴀᴜʀᴀᴠ\n\n"
        "‎╚═════════════════╝"
    )

    try:
       
        sent_msg = await update.message.reply_text(
            leave_msg_text
        )

     
        await context.bot.pin_chat_message(
            chat_id=chat_id,
            message_id=sent_msg.message_id,
            disable_notification=True
        )

    except Exception:
        pass
# ==================
#              N C  T A S K
# ==================
async def nc_loop(k, prefix, context):
    global nc_success_count, nc_error_count
    while k in nc_tasks:
        try:
            new_title = f"{random.choice(Emoji_list)} {prefix}"
            await context.bot.set_chat_title(k[1], new_title)
                        
            nc_success_count += 1
            print(f"\r YoUrSsS V17 Active ~ | Changes: ({nc_success_count}) | Errors: ({nc_error_count})", end="", flush=True)
            
            await asyncio.sleep(DELAY)
        except Exception:
            nc_error_count += 1
            print(f"\r NC ERROR Occurred ({nc_error_count}) | Still Trying...", end="", flush=True)
            await asyncio.sleep(5) 
# ==================
#              N C   C M D 
# ==================
@only_sudo
async def nc(update, context):
    if not context.args:
        if context.bot.token == TOKENS[0]:
            await update.message.reply_text("𝐃ᴇᴀʀ 𝐍ɪɢɢᴀ 𝐔sᴇ /Nc <Nᴀᴍᴇ> ~ 𝐔sᴇ /Text 𝐅ᴏʀ 𝐍c 𝐓ᴇxᴛ")
        return
    k = key(context, update.effective_chat.id)
    if k in nc_tasks: return
    prefix = " ".join(context.args)
    nc_tasks[k] = asyncio.create_task(nc_loop(k, prefix, context))
    if context.bot.token == TOKENS[0]:
        await update.message.reply_text("Hᴇʏ 𝐍ɪɢɢᴀ 𝐍c Is Sᴛᴀʀᴛᴇᴅ... ~")    
        
@only_sudo
async def stop(update, context):
    k = key(context, update.effective_chat.id)
    if k in nc_tasks:
        nc_tasks[k].cancel()
        del nc_tasks[k]
    if context.bot.token == TOKENS[0]:
        await update.message.reply_text("𝐍ɪɢɢᴀ F4ᴄᴋᴇᴛ Bʏ 𝐍c ♥️ ~")
# ==================
#                   B Y Y 
# ==================
@only_sudo
async def byy(update, context):
    chat_id = update.effective_chat.id
    k = key(context, chat_id)
    is_main_bot = (context.bot.token == TOKENS[0])
     
    for task_dict in [nc_tasks, spam_tasks, reply_tasks]:
        if k in task_dict:
            task_dict[k].cancel()
            del task_dict[k]

    try:
        
        if is_main_bot:
            await update.message.reply_text("Cʟᴏsɪɴɢ 𝐀ʟʟ Tᴀsᴋ's Aɴᴅ Lᴇᴀᴠɪɴɢ Bʏᴇ...🕊️~")
        
        await context.bot.leave_chat(chat_id)
        
    except Exception as e:
       
        print(f"Lᴇᴀᴠᴇ Eʀʀᴏʀ Fᴏʀ ᗷOT ♥️ ~ {e}")
# ==================
#          B O T  A D M I N
# ==================
@only_sudo
async def admin(update, context):
    chat_id = update.effective_chat.id
    main_bot_id = context.bot.id
        
    if context.bot.token != TOKENS[0]:
        return

    await update.message.reply_text("Mᴀᴋɪɴɢ 𝐀ʟʟ Bᴏᴛs 𝐀ᴅᴍɪɴ... ♥️ ~")

    success_count = 0
    for token in TOKENS:
        try:
            
            temp_app = Application.builder().token(token).build()
            bot_user = await temp_app.bot.get_me()
            target_bot_id = bot_user.id
                        
            if target_bot_id == main_bot_id:
                continue

            await context.bot.promote_chat_member(
                chat_id=chat_id,
                user_id=target_bot_id,
                can_change_info=True,
                can_post_messages=True,
                can_edit_messages=True,
                can_delete_messages=True,
                can_invite_users=True,
                can_restrict_members=True,
                can_pin_messages=True,
                can_promote_members=True,
                can_manage_chat=True,
                can_manage_video_chats=True
            )
            success_count += 1
            
        except Exception as e:
            print(f"𝐀ᴅᴍɪɴ Eʀʀᴏʀ Fᴏʀ ᴀ Bᴏᴛ ♥️ ~ {e}")

    await update.message.reply_text(f"𝐍ᴏᴡ {success_count} Bᴏᴛs 𝐀ᴅᴍɪɴ 𝐃ᴏɴᴇ ♥️ ~")
# ==================
# S P A M  R E P L Y  L O O P
# ==================
async def spam_loop(k, text, context):
    while k in spam_tasks:
        try:
            
            await context.bot.send_message(k[1], text)
            await asyncio.sleep(SPAM_DELAY)
        except Exception as e:
            await asyncio.sleep(1)

async def reply_loop(k, msg_id, context):
    while k in reply_tasks:
        try:
            for _ in range(15):
                
                await context.bot.send_message(
                    k[1],
                    random.choice(reply_list),
                    reply_to_message_id=msg_id
                )
                await asyncio.sleep(0.2)
        except Exception as e:
            await asyncio.sleep(1)
# ==================
#                S P A M
# ==================
@only_sudo
async def spam(update, context):
    if not context.args:
        if context.bot.token == TOKENS[0]:
            await update.message.reply_text("𝐃ᴇᴀʀ 𝐍ɪɢɢᴀ 𝐔sᴇ /Spam <Tᴇxᴛ> ~ 𝐔sᴇ /Text 𝐅ᴏʀ 𝐒ᴘᴀᴍ 𝐓ᴇxᴛ")
        return
    k = key(context, update.effective_chat.id)
    spam_tasks[k] = asyncio.create_task(spam_loop(k, " ".join(context.args), context))
    if context.bot.token == TOKENS[0]:
        await update.message.reply_text("Hᴇʏ 𝐍ɪɢɢᴀ Sᴘᴀᴍ Is Sᴛᴀʀᴛᴇᴅ... ~")

@only_sudo
async def unspam(update, context):
    k = key(context, update.effective_chat.id)
    if k in spam_tasks:
        spam_tasks[k].cancel()
        del spam_tasks[k]
    if context.bot.token == TOKENS[0]:
        await update.message.reply_text("𝐍ɪɢɢᴀ F4ᴄᴋᴇᴛ Bʏ Sᴘᴀᴍ ♥️ ~")
# ==================
#                R E P L Y
# ==================
@only_sudo
async def reply(update, context):
    if not update.message.reply_to_message:
        if context.bot.token == TOKENS[0]:
            await update.message.reply_text("𝐃ᴇᴀʀ 𝐍ɪɢɢᴀ 𝐔sᴇ /Rᴇᴘʟʏ <Rᴇᴘʟʏ> ~")
        return
    k = key(context, update.effective_chat.id)
    msg_id = update.message.reply_to_message.message_id
    reply_tasks[k] = asyncio.create_task(reply_loop(k, msg_id, context))
    if context.bot.token == TOKENS[0]:
        await update.message.reply_text("Hᴇʏ 𝐍ɪɢɢᴀ 𝐑ᴇᴘʟʏ Is Sᴛᴀʀᴛᴇᴅ... ~")

@only_sudo
async def unreply(update, context):
    k = key(context, update.effective_chat.id)
    if k in reply_tasks:
        reply_tasks[k].cancel()
        del reply_tasks[k]
    if context.bot.token == TOKENS[0]:
        await update.message.reply_text("𝐍ɪɢɢᴀ F4ᴄᴋᴇᴛ Bʏ 𝐑ᴇᴘʟʏ ♥️ ~")
# ==================
#                D E L A Y
# ==================
@only_sudo
async def delay(update, context):
    global DELAY
    try:
        sec = float(context.args[0])
        if 0.1 <= sec <= 20:
            DELAY = sec
            if context.bot.token == TOKENS[0]:
                await update.message.reply_text(f"⏱ 𝐍ɪɢɢᴀ Sᴇᴛ ᴀ Dᴇʟᴀʏ Tɪᴍᴇ : {sec}s ~")
        else:
            if context.bot.token == TOKENS[0]:
                await update.message.reply_text("𝕽𝖆𝖓𝖌𝖊: 0.1 - 20 ♥️ ~")
    except:
        if context.bot.token == TOKENS[0]:
            await update.message.reply_text("𝐃ᴇᴀʀ 𝐍ɪɢɢᴀ 𝐔sᴇ /Dᴇʟᴀʏ <sᴇᴄ> ~")
# ==================
#                 S U D O 
# ==================
@only_owner
async def sudo(update, context):
    
    if context.bot.token != TOKENS[0]:
        return

    if not update.message.reply_to_message:
        return await update.message.reply_text(
            "𝐃ᴇᴀʀ 𝐍ɪɢɢᴀ 𝐔sᴇ /Sᴜᴅᴏ |Rᴇᴘʟʏ|"
        )
    
    user_id = update.message.reply_to_message.from_user.id

    s = load_sudo()

    if user_id not in s:

        s.append(user_id)

        save_sudo(s)

        admins_USERS.clear()
        admins_USERS.extend(s)

    await update.message.reply_text(
        "Tʜᴇ 𝐍ᴇᴡ 𝐍ɪɢɢᴀ Is 𝐀ᴅᴅᴇᴅ Iɴ Sᴜᴅᴏ Lɪsᴛ ♥️"
    )
# ==================
#             U N S U D O
# ==================
@only_owner
async def unsudo(update, context):
    
    if context.bot.token != TOKENS[0]:
        return

    if not update.message.reply_to_message:
        return await update.message.reply_text(
            "𝐃ᴇᴀʀ 𝐍ɪɢɢᴀ 𝐔sᴇ /Uɴsᴜᴅᴏ |Rᴇᴘʟʏ|"
        )
    
    user_id = update.message.reply_to_message.from_user.id

    s = load_sudo()

    if user_id in s:

        s.remove(user_id)
     
        if OWNER_ID not in s:
            s.append(OWNER_ID)

        save_sudo(s)

        admins_USERS.clear()
        admins_USERS.extend(s)

    await update.message.reply_text(
        "Tʜᴇ F4ᴄᴋɪɴɢ 𝐍ɪɢɢᴀ Is 𝐑ᴇᴍᴏᴠᴇ Fʀᴏᴍ Sᴜᴅᴏ Lɪsᴛ ♥️"
    )
# ==================
#            R E F R E S H 
# ==================
@only_owner
async def refresh(update, context):

    global admins_USERS

    if context.bot.token != TOKENS[0]:
        return

    admins_USERS = [OWNER_ID]

    save_sudo(admins_USERS)

    await update.message.reply_text(
        "𝐑ᴇғʀᴇsʜ 𝐍ɪɢɢᴀ's Lɪsᴛ ♥️ ~\n"
        "𝐀ʟʟ Sᴜᴅᴏ 𝐑ᴇᴍᴏᴠᴇᴅ ~"
    )
# ==================
#                   L I S T
# ==================
@only_owner
async def list_sudo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if context.bot.token != TOKENS[0]:
        return

    s = load_sudo()
    chat_id = update.effective_chat.id

    text = "𝔖𝔲𝔡𝔬 𝔲𝔰𝔢𝔯𝔰 ♥️ ~\n\n"

    for x in s:
        try:
            
            member = await context.bot.get_chat_member(chat_id=chat_id, user_id=int(x))
            user = member.user
            if user.username:
                text += f"➤ @{user.username}\n"
            else:
                text += f'➤ <a href="tg://user?id={user.id}">{user.first_name}</a>\n'
        except Exception:
            
            text += f"➤ `{x}` (ID)\n"

    try:
        
        await update.message.reply_video(
            video=LIST_SUDO_VIDEO_URL,
            caption=text,
            parse_mode="HTML"
        )
    except Exception:
        
        await update.message.reply_text(text, parse_mode="HTML")      
# ==================
#                  I N F O
# ==================
@only_sudo
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if context.bot.token != TOKENS[0]:
        return

    if not update.message.reply_to_message:
        return await update.message.reply_text(
            "𝐑ᴇᴘʟᴀʏ Tᴏ 𝐔sᴇʀ Wɪᴛʜ /Iɴғᴏ ~"
        )

    user = update.message.reply_to_message.from_user
    chat = update.effective_chat

    emoji_pattern = re.compile(
        "["
        "\U0001F300-\U0001F5FF"
        "\U0001F600-\U0001F64F"
        "\U0001F680-\U0001F6FF"
        "\U0001F700-\U0001F77F"
        "\U0001F780-\U0001F7FF"
        "\U0001F800-\U0001F8FF"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FAFF"
        "]+",
        flags=re.UNICODE
    )

    cmd_user = update.effective_user.first_name

    clean_group = emoji_pattern.sub(
        "",
        chat.title
    ).strip()

    username = (
        f"@{user.username}"
        if user.username else
        "𝐍ᴏ 𝐔sʀɴᴀᴍᴇ"
    )

    text = f"""
╔═══════════════╗
             𝐔sᴇʀ 𝐈ɴғᴏ ~ 💮
╚═══════════════╝

𝑵𝒂𝒎𝒆 ~ {user.first_name}

𝑭𝒖𝒍𝒍 𝑵𝒂𝒎𝒆 ~ {user.full_name}

𝑼𝒔𝒆𝒓𝒏𝒂𝒎𝒆 ~ {username}

𝑼𝒔𝒆𝒓 𝑰𝑫 ~ `{user.id}`

𝑮𝒓𝒐𝒖𝒑 𝑰𝑫 ~ `{chat.id}`

𝑮𝒓𝒐𝒖𝒑 ~ {clean_group}

╔═══════════════╗
               {cmd_user}
╚═══════════════╝
"""

    try:
        
        await update.message.reply_video(
            video=INFO_VIDEO_URL,
            caption=text,
            parse_mode="Markdown"
        )
    except Exception:
        
        await update.message.reply_text(
            text,
            parse_mode="Markdown"
        )
        
X = base64.b64decode(
    "8J2QjuG0ocm04bSHyoAg4p6gIPCdkJjhtI/htJzwnZCR6pyx8J2QkuqcsSAhISDwn6q9"
).decode()

async def owr(update, context):

    await update.message.reply_text(X)    
# ==================
#                  P I N G
# ==================
@only_sudo
async def ping(update, context):
    start = time.time()
    msg = await update.message.reply_text("𝘗𝘪𝘯𝘨𝘪𝘯𝘨...")
    end = time.time()
    await msg.edit_text(f"🏓 {round((end-start)*1000)} ms")

@only_sudo
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
   
    if context.bot.token != TOKENS[0]:
        return

    user = update.effective_user
    full_name = user.full_name

    emoji_pattern = re.compile(
        "["
        "\U0001F300-\U0001F5FF"
        "\U0001F600-\U0001F64F"
        "\U0001F680-\U0001F6FF"
        "\U0001F700-\U0001F77F"
        "\U0001F780-\U0001F7FF"
        "\U0001F800-\U0001F8FF"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FAFF"
        "]+",
        flags=re.UNICODE
    )

    emojis = "".join(emoji_pattern.findall(full_name))
    name = emoji_pattern.sub("", full_name).strip()

    header_line = f"{name}  𝐆ᴀʟᴀxʏ"
    if emojis:
        header_line += f" {emojis}"

    text = f"""
╔═════════════════╗

        {header_line}

╚═════════════════╝

 𝐍ᴄ ➠ {len(nc_tasks)}
 𝐒ᴘᴇᴇᴅ 𝐍ᴄ ➠ {len(speed_tasks)}
 𝐒ᴘᴀ𝐌 ➠ {len(spam_tasks)}
 𝐑ᴇᴘʟʏ ➠ {len(reply_tasks)}
 𝐒ᴛɪᴄᴋᴇʀ ➠ {len(sticker_tasks)}
 𝐏ʜᴏᴛᴏ ➠ {len(photo_tasks)}
 𝐏ғᴘ ➠ {len(pfp_tasks)}

╔═════════════════╗

            𝐅ᴇᴀʀ𝐎ғ{name}

╚═════════════════╝
"""

    try:
        
        await update.message.reply_video(
            video=STATUS_VIDEO_URL,
            caption=text,
            parse_mode="Markdown"
        )
    except Exception:
        
        await update.message.reply_text(text)

async def my(update, context):
    
    if context.bot.token != TOKENS[0]:
        return

    await update.message.reply_text(
        f"𝕴𝕯 ♥️ ~ {update.effective_user.id}"
    )
# ==================
#                   G C
# ==================
@only_sudo
async def folder(update, context):

    if context.bot.token != TOKENS[0]:
        return

    chat_id = update.effective_chat.id

    sent_msgs = []

    for link in GC_LINKS:

        msg = await update.message.reply_text(
            f"𝐆𝐜 ~ {link}",
            disable_web_page_preview=True
        )

        sent_msgs.append(msg.message_id)

        await asyncio.sleep(0.5)

    folder_messages[chat_id] = sent_msgs

@only_sudo
async def unfolder(update, context):

    if context.bot.token != TOKENS[0]:
        return

    chat_id = update.effective_chat.id

    if chat_id not in folder_messages:

        return await update.message.reply_text(
            "𝐋ɪɴᴋs 𝐀ʟʀᴇᴀᴅʏ 𝐎ғғ ~"
        )

    for msg_id in folder_messages[chat_id]:

        try:

            await context.bot.delete_message(
                chat_id=chat_id,
                message_id=msg_id
            )

        except:
            pass

    del folder_messages[chat_id]

    await update.message.reply_text(
        "𝐋ɪɴᴋs 𝐃ᴇʟᴇᴛᴇᴅ ~"
    )

@only_sudo
async def gcs(update, context):

    if context.bot.token != TOKENS[0]:
        return

    total = len(GC_LINKS)

    await update.message.reply_text(
        f"𝐓ᴏᴛᴀʟ GCs ~ {total}"
    )    
# ==================
#                V O I C E
# ==================
@only_sudo
async def voice(update, context):

    if context.bot.token != TOKENS[0]:
        return

    if not context.args:

        return await update.message.reply_text(
            "𝐃ᴇᴀʀ 𝐍ɪɢɢᴀ 𝐔sᴇ +Vᴏɪᴄᴇ |Tᴇxᴛ| ~"
        )

    text = " ".join(context.args)

    await update.message.reply_voice(
        voice=f"https://translate.google.com/translate_tts?ie=UTF-8&q={text}&tl=en&client=tw-ob"
    ) 
# ==================
#             S T I C K E R
# ==================
async def sticker_loop(k, context, sticker_id):

    while k in sticker_tasks:

        try:

            await context.bot.send_sticker(
                chat_id=k[1],
                sticker=sticker_id
            )

            await asyncio.sleep(1)

        except:
            await asyncio.sleep(2)

@only_sudo
async def sticker(update, context):

    k = key(context, update.effective_chat.id)
# =========================
# START MODE (/sticker)
# =========================
    if not context.args:
        return await update.message.reply_text(
            "𝐃ᴇᴀʀ 𝐍ɪɢɢᴀ 𝐔sᴇ +Sᴛɪcᴋᴇʀ  |Rᴇᴘʟᴀʏ| ~"
        )

    msg = update.message.reply_to_message

    if not msg:
        return await update.message.reply_text(
            "𝐑ᴇᴘʟᴀʏ Tᴏ Sᴛɪcᴋᴇʀ ~"
        )

    if not msg.sticker:
        return await update.message.reply_text(
            "𝐑ᴇᴘʟᴀʏ Tᴏ Vᴀʟɪᴅ Sᴛɪcᴋᴇʀ ~"
        )

    if k in sticker_tasks:
        return await update.message.reply_text(
            "Sᴛɪcᴋᴇʀ 𝐀ʀᴇᴀᴅʏ 𝐎ɴ ~"
        )

    sticker_id = msg.sticker.file_id

    sticker_tasks[k] = asyncio.create_task(
        sticker_loop(
            k,
            context,
            sticker_id
        )
    )

    return await update.message.reply_text(
        "Sᴛɪcᴋᴇʀ Sᴘᴀᴍ Sᴛᴀʀᴛᴇᴅ ~"
    )

@only_sudo
async def unsticker(update, context):

    k = key(context, update.effective_chat.id)

    if k not in sticker_tasks:

        return await update.message.reply_text(
            "Sᴛɪcᴋᴇʀ 𝐀ʟʀᴇᴀᴅʏ 𝐎ғғ ~"
        )

    sticker_tasks[k].cancel()
    del sticker_tasks[k]

    await update.message.reply_text(
        "-Sᴛɪcᴋᴇʀ Sᴛᴏᴘᴘᴇᴅ ~"
    )
# ---------------------------
# PHOTO SPAM MODE
# ---------------------------
@only_sudo
async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id
# =========================
# START MODE (/photo)
# =========================
    if not update.message.reply_to_message:

        return await update.message.reply_text(
            "𝐑ᴇᴘʟʏ Tᴏ 𝐏ʜᴏᴛᴏ ~"
        )

    msg = update.message.reply_to_message

    if not msg.photo:

        return await update.message.reply_text(
            "𝐑ᴇᴘʟʏ Tᴏ Vᴀʟɪᴅ 𝐏ʜᴏᴛᴏ ~"
        )

    file_id = msg.photo[-1].file_id

    async def spam_photo():

        while True:

            try:

                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=file_id
                )

                await asyncio.sleep(1)

            except:
                break

    if chat_id in photo_tasks:

        photo_tasks[chat_id].cancel()

    photo_tasks[chat_id] = asyncio.create_task(
        spam_photo()
    )

    return await update.message.reply_text(
        "𝐏ʜᴏᴛᴏ 𝐌ᴏᴅᴇ 𝐎ɴ... ~"
    )

@only_sudo
async def unphoto(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id

    if chat_id not in photo_tasks:

        return await update.message.reply_text(
            "𝐏ʜᴏᴛᴏ 𝐌ᴏᴅᴇ 𝐀ʟʀᴇᴀᴅʏ 𝐎ғғ ~"
        )

    photo_tasks[chat_id].cancel()
    del photo_tasks[chat_id]

    return await update.message.reply_text(
        "𝐏ʜᴏᴛᴏ 𝐌ᴏᴅᴇ 𝐎ғғ... ~"
    )
# ---------------------------
# GROUP DP ROTATE MODE
# ---------------------------
@only_sudo
async def pfp(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id
# =========================
# START MODE (/pic)
# =========================

    if not update.message.reply_to_message:

        return await update.message.reply_text(
            "𝐑ᴇᴘʟʏ Tᴏ 𝐏ʜᴏᴛᴏ ~"
        )

    msg = update.message.reply_to_message

    if not msg.photo:

        return await update.message.reply_text(
            "𝐑ᴇᴘʟʏ Tᴏ Vᴀʟɪᴅ 𝐏ʜᴏᴛᴏ ~"
        )

    photo = await msg.photo[-1].get_file()

    path = f"{chat_id}.jpg"

    await photo.download_to_drive(path)

    async def pfp_loop():

        while True:

            try:

                with open(path, "rb") as p:

                    await context.bot.set_chat_photo(
                        chat_id=chat_id,
                        photo=p
                    )

                await asyncio.sleep(5)

            except:
                break

    if chat_id in pfp_tasks:
        pfp_tasks[chat_id].cancel()

    pfp_tasks[chat_id] = asyncio.create_task(pfp_loop())

    return await update.message.reply_text(
        "𝐏ғᴘ 𝐌ᴏᴅᴇ 𝐎ɴ... ~"
    )

@only_sudo
async def unpfp(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id

    if chat_id not in pfp_tasks:

        return await update.message.reply_text(
            "𝐏ғᴘ 𝐌ᴏᴅᴇ 𝐀ʟʀᴇᴀᴅʏ 𝐎ғғ ~"
        )

    pfp_tasks[chat_id].cancel()
    del pfp_tasks[chat_id]

    return await update.message.reply_text(
        "𝐏ғᴘ 𝐌ᴏᴅᴇ 𝐎ғғ... ~"
    )
# ---------------------------
# OVER MODE
# ---------------------------
@only_sudo
async def over(update: Update, context: ContextTypes.DEFAULT_TYPE):

    current_time = time.strftime("%A, %d | %B %Y | %H:%M:%S")
    group_name = update.effective_chat.title
  
    user = update.effective_user
    name = user.full_name
   
    target = " ".join(context.args)

    if not target:
        target = "Uɴᴋɴᴏᴡɴ"

    text = (
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"𝐆ᴀ𝐌ᴇ 𝐎ᴠ𝐄ʀ 𝐓ɪ𝐌ᴇ - {current_time}\n\n"
        f"{target} αвн ααкє нαωαвααzι \n"
        f"мαт кαяηα внαω ηнι мιℓηє ωαℓα \n\n"
        f"𝐆ʀᴏᴜ𝐏 - {group_name}\n\n"
        f"𝐆ᴀ𝐌ᴇ 𝐎ᴠ𝐄ʀ 𝐁ʏ {name}\n"
        f"━━━━━━━━━━━━━━━━━━━"
    )

    try:
       
        await update.message.reply_video(
            video=OVER_VIDEO_URL,
            caption=text,
            parse_mode="Markdown"
        )
    except Exception:
       
        await update.message.reply_text(text)
# ---------------------------
# Ncs SPEED MODES
# ---------------------------
async def auto_rotate_loop(bot, chat_id, mode, name):

    global custom_speed_delay

    while True:

        try:

            if mode == "medium":
                await asyncio.sleep(custom_speed_delay)

            elif mode == "fast":
                await asyncio.sleep(0.3)

            elif mode == "high":
                await asyncio.sleep(0.1)

            elif mode == "super":
                await asyncio.sleep(0.08)

            elif mode == "god":
                await asyncio.sleep(0.01)

            emoji = random.choice(EMOJIS)

            title_text = (
                f"{emoji}"
                f" {name}"
            )

            await bot.set_chat_title(
                chat_id=chat_id,
                title=title_text
            )

        except asyncio.CancelledError:

            return

        except Exception as e:

            if "Flood control exceeded" in str(e):

                await asyncio.sleep(5)

            continue

@only_sudo
async def speed(update, context):

    global custom_speed_delay

    if not context.args:

        return await update.message.reply_text(
            "Nɪɢɢᴀ Usᴇ /Sᴘᴇᴇᴅ |Dᴇʟᴀʏ| ~"
        )

    try:

        delay = float(context.args[0])

        if delay < 0.005:
            delay = 0.005

        custom_speed_delay = delay

        await update.message.reply_text(
            f"Sᴘᴇᴇᴅ Dᴇʟᴀʏ Sᴇᴛ Tᴏ {custom_speed_delay} ~"
        )

    except:

        await update.message.reply_text(
            "Vᴀʟɪᴅ Dᴇʟᴀʏ Usᴇ Kᴀʀ ~"
        )

@only_sudo
async def speed_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_id = update.effective_chat.id

    cmd = (
        update.message.text
        .split()[0]
        .replace("/", "")
        .replace("/", "")
        .lower()
    )
# =========================
# STOP ALL MODES
# =========================
    if cmd == "unspeed":

        if chat_id in speed_tasks:

            for task in speed_tasks[chat_id]:

                if not task.done():
                    task.cancel()

            del speed_tasks[chat_id]

        return await update.message.reply_text(
            f"Nɪɢɢᴀ F4ᴄᴋᴇᴛ Bʏ Sᴘᴇᴇᴅ Mᴏᴅᴇ ~"
        )
# =========================
# VALID MODES
# =========================
    valid_modes = [
        "medium",
        "fast",
        "high",
        "super",
        "god"
    ]

    if cmd not in valid_modes:
        return

    if not context.args:

        return await update.message.reply_text(
            f"Dᴇᴀʀ Nɪɢɢᴀ Usᴇ /{cmd} |Tᴇxᴛ| ~"
        )

    name = " ".join(context.args)
    
    if chat_id in speed_tasks:

        for task in speed_tasks[chat_id]:

            if not task.done():
                task.cancel()

        del speed_tasks[chat_id]

    tasks = []

    for bot in bots:

        task = asyncio.create_task(
            auto_rotate_loop(
                bot,
                chat_id,
                cmd,
                name
            )
        )

        tasks.append(task)

    speed_tasks[chat_id] = tasks

    await update.message.reply_text(
        f"Hᴇʏ Nɪɢɢᴀ {cmd.upper()} Mᴏᴅᴇ Is Sᴛᴀʀᴛᴇᴅ ~"
    )
# ==================
#        G R U O P   B O T 
# ==================  
@only_sudo
async def mute(update, context):

    if context.bot.token != TOKENS[0]:
        return

    if not update.message.reply_to_message:
        return

    user = update.message.reply_to_message.from_user

    await context.bot.restrict_chat_member(
        update.effective_chat.id,
        user.id,
        permissions=ChatPermissions(
            can_send_messages=False
        )
    )

    if context.bot.token == TOKENS[0]:
        await update.message.reply_text(
            f"🔇 {user.first_name} 𝐌ᴜᴛᴇᴅ"
        )
        
@only_sudo
async def unmute(update, context):

    if context.bot.token != TOKENS[0]:
        return

    if not update.message.reply_to_message:
        return

    user = update.message.reply_to_message.from_user

    await context.bot.restrict_chat_member(
        update.effective_chat.id,
        user.id,
        permissions=ChatPermissions(
            can_send_messages=True
        )
    )

    if context.bot.token == TOKENS[0]:
        await update.message.reply_text(
            f"🔊 {user.first_name} 𝐔ɴᴍᴜᴛᴇᴅ"
        )
        
@only_sudo
async def ban(update, context):

    if context.bot.token != TOKENS[0]:
        return

    if not update.message.reply_to_message:
        return

    user = update.message.reply_to_message.from_user

    await context.bot.ban_chat_member(
        update.effective_chat.id,
        user.id
    )

    if context.bot.token == TOKENS[0]:
        await update.message.reply_text(
            f"🚫 {user.first_name} 𝐁ᴀɴɴᴇᴅ"
        )
        
@only_sudo
async def unban(update, context):

    if context.bot.token != TOKENS[0]:
        return

    if len(context.args) < 1:
        return

    user_id = int(context.args[0])

    await context.bot.unban_chat_member(
        update.effective_chat.id,
        user_id
    )

    if context.bot.token == TOKENS[0]:
        await update.message.reply_text(
            "✅ 𝐔ɴʙᴀɴɴᴇᴅ"
        )   
             
@only_sudo
async def pin(update, context):

    if context.bot.token != TOKENS[0]:
        return

    if not update.message.reply_to_message:
        return

    await context.bot.pin_chat_message(
        update.effective_chat.id,
        update.message.reply_to_message.message_id
    )

    if context.bot.token == TOKENS[0]:
        await update.message.reply_text(
            "📌 𝐏ɪɴɴᴇᴅ"
        )
                 
@only_sudo
async def unpin(update, context):

    if context.bot.token != TOKENS[0]:
        return

    await context.bot.unpin_all_chat_messages(
        update.effective_chat.id
    )

    if context.bot.token == TOKENS[0]:
        await update.message.reply_text(
            "📍 𝐔ɴᴘɪɴɴᴇᴅ"
        )
        
@only_sudo
async def lock(update, context):

    if context.bot.token != TOKENS[0]:
        return

    await context.bot.set_chat_permissions(
        update.effective_chat.id,
        ChatPermissions(
            can_send_messages=False
        )
    )

    if context.bot.token == TOKENS[0]:
        await update.message.reply_text(
            "🔒 𝐆ʀᴏᴜᴘ 𝐋ᴏᴄᴋᴇᴅ"
        )
        
@only_sudo
async def unlock(update, context):

    if context.bot.token != TOKENS[0]:
        return

    await context.bot.set_chat_permissions(
        update.effective_chat.id,
        ChatPermissions(
            can_send_messages=True
        )
    )

    if context.bot.token == TOKENS[0]:
        await update.message.reply_text(
            "🔓 𝐆ʀᴏᴜᴘ 𝐔ɴʟᴏᴄᴋᴇᴅ"
        )
        
@only_sudo
async def promote(update, context):

    if context.bot.token != TOKENS[0]:
        return

    if not update.message.reply_to_message:
        return

    user = update.message.reply_to_message.from_user

    await context.bot.promote_chat_member(
        update.effective_chat.id,
        user.id,
        can_manage_chat=True,
        can_delete_messages=True,
        can_restrict_members=True,
        can_pin_messages=True
    )

    if context.bot.token == TOKENS[0]:
        await update.message.reply_text(
            f"👑 {user.first_name} 𝐏ʀᴏᴍᴏᴛᴇᴅ"
        )
        
@only_sudo
async def demote(update, context):

    if context.bot.token != TOKENS[0]:
        return

    if not update.message.reply_to_message:
        return

    user = update.message.reply_to_message.from_user

    await context.bot.promote_chat_member(
        update.effective_chat.id,
        user.id,
        can_manage_chat=False,
        can_delete_messages=False,
        can_restrict_members=False,
        can_pin_messages=False
    )

    if context.bot.token == TOKENS[0]:
        await update.message.reply_text(
            f"❌ {user.first_name} 𝐃ᴇᴍᴏᴛᴇᴅ"
        )
#=========================
# HOST
# ========================= 
@only_sudo
async def host(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if context.bot.token != TOKENS[0]:
        return

    user = update.effective_user
    user_id = str(user.id)

    if user.id != OWNER_ID:
        return await update.message.reply_text("❌ 𝐎ᴡɴᴇʀ 𝐎ɴʟʏ")

    if not update.message.document:
        return

    document = update.message.document
    filename = document.file_name

   
    if not filename.endswith(".py"):
        return await update.message.reply_text("❌ 𝐎ɴʟʏ .𝐩𝐲 𝐅ɪʟᴇs 𝐀ʀᴇ 𝐀ʟʟᴏᴡᴇᴅ")

    user_folder = f"hosted/{user_id}"
    os.makedirs(user_folder, exist_ok=True)

    file_path = f"{user_folder}/{filename}"

    if user_id not in host_db:
        host_db[user_id] = []

  
    if len(host_db[user_id]) >= 20:
        return await update.message.reply_text("⚠️ 𝐌ᴀx 20 𝐅ɪʟᴇs 𝐑ᴜɴɴɪɴɢ")

    tg_file = await document.get_file()
    await tg_file.download_to_drive(file_path)

    try:
        
        log_file = f"{user_folder}/{filename}.log"
        
       
        with open(log_file, 'w') as f:
            f.write(f"=== Started {filename} at {datetime.now()} ===\n")

        
        process = await asyncio.create_subprocess_exec(
            "python",
            file_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        running_process.setdefault(user_id, {})[filename] = process

        host_db[user_id].append({
            "file": filename,
            "path": file_path,
            "pid": process.pid,
            "log_file": log_file
        })

        save_json(host_db, "host.json")

        
        asyncio.create_task(capture_logs(user_id, filename, process, log_file))

        await update.message.reply_text(
            f"✅ 𝐅ɪʟᴇ 𝐇ᴏsᴛᴇᴅ\n\n📂 {filename}\n🆔 𝐏ɪᴅ: {process.pid}\n📝 𝐋ᴏɢ: {log_file}"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ 𝐄ʀʀᴏʀ\n\n{e}")
# =========================
# CAPTURE LOGS (Background Task)
# =========================
async def capture_logs(user_id, filename, process, log_file):
    """Capture stdout and stderr from process and write to log file"""
    try:
        while True:
            
            stdout_line = await process.stdout.readline()
            stderr_line = await process.stderr.readline()
            
            if not stdout_line and not stderr_line:
               
                if process.returncode is not None:
                    break
                await asyncio.sleep(0.1)
                continue
            
            with open(log_file, 'a') as f:
                if stdout_line:
                    f.write(f"[STDOUT] {stdout_line.decode()}")
                if stderr_line:
                    f.write(f"[STDERR] {stderr_line.decode()}")
                    
    except Exception as e:
        with open(log_file, 'a') as f:
            f.write(f"[ERROR] Log capture failed: {e}\n")
# =========================
# DEL HOST (Delete All)
# =========================         
@only_sudo
async def delete_host(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if context.bot.token != TOKENS[0]:
        return

    user = update.effective_user
    user_id = str(user.id)

    if user.id != OWNER_ID:
        return await update.message.reply_text("𝐎ᴡɴᴇʀ 𝐎ɴʟʏ")

    if user_id not in host_db or not host_db[user_id]:
        return await update.message.reply_text("𝐍ᴏ 𝐑ᴜɴɴɪɴɢ 𝐅ɪʟᴇ")

    try:
        if user_id in running_process:
            for proc in running_process[user_id].values():
                try:
                    proc.kill()
                except:
                    pass
            del running_process[user_id]

        user_folder = f"hosted/{user_id}"
        if os.path.exists(user_folder):
            shutil.rmtree(user_folder)

        host_db[user_id] = []
        save_json(host_db, "host.json")

        await update.message.reply_text("𝐀ʟʟ 𝐅ɪʟᴇs 𝐃ᴇʟᴇᴛᴇᴅ")

    except Exception as e:
        await update.message.reply_text(f"𝐄ʀʀᴏʀ\n\n{e}")
# =========================
# DEL PID (Delete Specific)
# =========================
@only_sudo
async def delete_pid(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if context.bot.token != TOKENS[0]:
        return

    user = update.effective_user
    user_id = str(user.id)

    if user.id != OWNER_ID:
        return await update.message.reply_text("𝐎ᴡɴᴇʀ 𝐎ɴʟʏ")

    if not context.args:
        return await update.message.reply_text("𝐏ʀᴏᴠɪᴅᴇ 𝐏𝐈𝐃\n𝐄xᴀᴍᴘʟᴇ: /unhost 12345")

    try:
        pid_to_delete = int(context.args[0])
    except ValueError:
        return await update.message.reply_text("𝐈ɴᴠᴀʟɪᴅ 𝐏𝐈𝐃")

    if user_id not in host_db or not host_db[user_id]:
        return await update.message.reply_text("𝐍ᴏ 𝐑ᴜɴɴɪɴɢ 𝐅ɪʟᴇ")

   
    file_to_delete = None
    for item in host_db[user_id]:
        if item['pid'] == pid_to_delete:
            file_to_delete = item
            break

    if not file_to_delete:
        return await update.message.reply_text(f"𝐍ᴏ 𝐅ɪʟᴇ 𝐅ᴏᴜɴᴅ 𝐖ɪᴛʜ 𝐏𝐈𝐃: {pid_to_delete}")

    try:
        
        if user_id in running_process and file_to_delete['file'] in running_process[user_id]:
            proc = running_process[user_id][file_to_delete['file']]
            try:
                proc.kill()
            except:
                pass
            del running_process[user_id][file_to_delete['file']]
            
            if not running_process[user_id]:
                del running_process[user_id]

      
        if os.path.exists(file_to_delete['path']):
            os.remove(file_to_delete['path'])

     
        if os.path.exists(file_to_delete.get('log_file', '')):
            os.remove(file_to_delete['log_file'])

     
        host_db[user_id] = [item for item in host_db[user_id] if item['pid'] != pid_to_delete]
        save_json(host_db, "host.json")

        await update.message.reply_text(
            f"✅ 𝐅ɪʟᴇ 𝐃ᴇʟᴇᴛᴇᴅ\n"
            f"📂 {file_to_delete['file']}\n"
            f"🆔 𝐏𝐈𝐃: {pid_to_delete}"
        )

    except Exception as e:
        await update.message.reply_text(f"𝐄ʀʀᴏʀ\n\n{e}")
# =========================
# LOG (View Logs)
# =========================
@only_sudo
async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if context.bot.token != TOKENS[0]:
        return

    user = update.effective_user
    user_id = str(user.id)

    if user.id != OWNER_ID:
        return await update.message.reply_text("𝐎ᴡɴᴇʀ 𝐎ɴʟʏ")

    if not context.args:
        return await update.message.reply_text("𝐏ʀᴏᴠɪᴅᴇ 𝐏𝐈𝐃\n𝐄xᴀᴍᴘʟᴇ: /log 12345")

    try:
        pid_to_log = int(context.args[0])
    except ValueError:
        return await update.message.reply_text("𝐈ɴᴠᴀʟɪᴅ 𝐏𝐈𝐃")

    if user_id not in host_db or not host_db[user_id]:
        return await update.message.reply_text("𝐍ᴏ 𝐑ᴜɴɴɪɴɢ 𝐅ɪʟᴇ")

    
    file_to_log = None
    for item in host_db[user_id]:
        if item['pid'] == pid_to_log:
            file_to_log = item
            break

    if not file_to_log:
        return await update.message.reply_text(f"𝐍ᴏ 𝐅ɪʟᴇ 𝐅ᴏᴜɴᴅ 𝐖ɪᴛʏ 𝐏𝐈𝐃: {pid_to_log}")

    try:
        log_file = file_to_log.get('log_file')
        if not log_file or not os.path.exists(log_file):
            return await update.message.reply_text("📝 𝐍ᴏ 𝐋ᴏɢ𝐬 𝐅ᴏᴜɴᴅ 𝐘ᴇᴛ")

        
        with open(log_file, 'r') as f:
            lines = f.readlines()
            
        if not lines:
            return await update.message.reply_text("📝 𝐋ᴏɢ 𝐅ɪʟᴇ 𝐈𝐬 𝐄ᴍᴘᴛʏ")

      
        log_lines = lines[-50:] if len(lines) > 50 else lines
        log_text = ''.join(log_lines)

        
        if len(log_text) > 4000:
            for i in range(0, len(log_text), 4000):
                await update.message.reply_text(
                    f"📝 𝐋ᴏɢ𝐬 𝐅ᴏʀ 𝐏𝐈𝐃: {pid_to_log}\n"
                    f"📂 {file_to_log['file']}\n\n"
                    f"```\n{log_text[i:i+4000]}\n```",
                    parse_mode="Markdown"
                )
        else:
            await update.message.reply_text(
                f"📝 𝐋ᴏɢ𝐬 𝐅ᴏʀ 𝐏𝐈𝐃: {pid_to_log}\n"
                f"📂 {file_to_log['file']}\n\n"
                f"```\n{log_text}\n```",
                parse_mode="Markdown"
            )

    except Exception as e:
        await update.message.reply_text(f"❌ ??ʀʀᴏʀ 𝐑ᴇᴀᴅɪɴɢ 𝐋ᴏɢ\n\n{e}") 
# =========================
# MYHOST
# =========================  
@only_sudo
async def myhost(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if context.bot.token != TOKENS[0]:
        return

    user = update.effective_user
    user_id = str(user.id)

    if user_id not in host_db or not host_db[user_id]:
        return await update.message.reply_text("❌ 𝐍ᴏ 𝐇ᴏsᴛᴇᴅ 𝐅ɪʟᴇ")

    text_files = ""
    for i, item in enumerate(host_db[user_id], start=1):
      
        is_running = "✅" 
        try:
            if user_id in running_process and item['file'] in running_process[user_id]:
                proc = running_process[user_id][item['file']]
                if proc.returncode is not None:
                    is_running = "❌"
            else:
                is_running = "❌"
        except:
            is_running = "❌"
            
        text_files += (
            f"\n{i}. 📂 {item['file']}\n"
            f"   🆔 𝐏ɪᴅ ➜ {item['pid']}\n"
            f"   ⚡𝐒ᴛᴀᴛᴜ𝐬 ➜ {is_running}\n"
        )

    caption_text = (
        "╔═════════════════╗\n"        
        "         𝐌ʏ 𝐇ᴏsᴛ〘𝐆ᴀᴜʀᴀᴠ〙\n"        
        "‎╚═════════════════╝\n"        
        f"{text_files}"                
        "╔═════════════════╗\n"        
        "             𝐅ᴇᴀʀ𝐎ғ𝐆ᴀᴜʀᴀᴠ\n"        
        "‎╚═════════════════╝\n"
    ) 

    try:
        await update.message.reply_video(
            video=MYHOST_VIDEO_URL,
            caption=caption_text,
            parse_mode="Markdown"
        )
    except Exception:
        await update.message.reply_text(caption_text)
# =========================
#                             img 
# =========================
@only_sudo
async def img_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
   
    if context.bot.token != TOKENS[0]:
        return

    if not context.args:
        return await update.message.reply_text(
            "❌ 𝐔sᴀɢᴇ: /ɪᴍɢ <prompt>"
        )

    prompt = " ".join(context.args)

    img_url = generate_image(prompt)

    caption = (
        "══════════════════\n"
     "🖼️ 𝐈ᴍᴀɢᴇ 𝐆ᴇɴ\n"
        "══════════════════\n\n"
    f"🎨 𝐏ʀᴏᴍᴘᴛ ➜ {prompt}\n\n"
     "⚡ 𝐈ᴍᴀɢᴇ 𝐆ᴇɴᴇʀᴀᴛᴇᴅ\n\n"
        "══════════════════\n"
        " 𝐁ᴏᴛ 𝐑ᴇsᴜʟᴛ\n"
        "══════════════════"
    )

    try:
        await update.message.reply_photo(
            photo=img_url,
            caption=caption
        )

    except Exception as e:
        await update.message.reply_text(
            f"❌ 𝐄ʀʀᴏʀ\n\n{e}"
        )

# ========================
# GAME'S'
# ========================   
@only_sudo
async def game_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    if context.bot.token != TOKENS[0]:
        return
    
    HELP_MENU = """━━━━━━━━━━━━━━━━━━━

〔 🎮 𝐆ᴀᴍᴇ 𝐙ᴏɴᴇ  〕

⟡ ᴛᴛᴛ
⟡ ᴍᴏᴠᴇ

〔 🔫 𝐆ᴜɴ 𝐆ᴀᴍᴇ  〕

⟡ sʜᴏᴏᴛ
⟡ ʀᴇʟᴏᴀᴅ

━━━━━━━━━━━━━━━━━━━"""
        
    await update.message.reply_video(video=GAME_VIDEO_URL, caption=HELP_MENU, parse_mode="HTML")

def reset_roulette(chat_id):   
    cylinder = [0, 0, 0, 0, 0, 0]
    bullet_slot = random.randint(0, 5) 
    cylinder[bullet_slot] = 1
    ROULETTE_GAMES[chat_id] = {
        "cylinder": cylinder,
        "current_slot": 0,
        "active": True
    }

@only_sudo
async def load_roulette_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    if context.bot.token != TOKENS[0]:
        return
    chat_id = update.effective_chat.id
    reset_roulette(chat_id)
    
    msg = (
        "<b>🔫 Russian Roulette: Gun is Loaded! 🔫</b>\n\n"
        "Revolver me 6 slots hain aur 1 asli goli daal di gayi hai.\n"
        "Trigger dabane ke liye command bhejo:\n"
        "👉 <code>/shoot</code>"
    )
    
  
    try:
        if 'LOAD_VIDEO_URL' in globals() and LOAD_VIDEO_URL:
            await context.bot.send_video(
                chat_id=chat_id,
                video=LOAD_VIDEO_URL,
                caption=msg,
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(msg, parse_mode="HTML")
    except Exception:
        await update.message.reply_text(msg, parse_mode="HTML")


@only_sudo
async def shoot_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    if context.bot.token != TOKENS[0]:
        return
        
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    if not update.message:
        return

    user_mention = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'
    
   
    if chat_id not in ROULETTE_GAMES or not ROULETTE_GAMES[chat_id]["active"]:
        reset_roulette(chat_id)
        
    game = ROULETTE_GAMES[chat_id]
    current_slot = game["current_slot"]
    is_bullet = game["cylinder"][current_slot]
    game["current_slot"] += 1
       
    u_name = f"@{user.username}" if user.username else user.first_name
    status_msg = await update.message.reply_text(f"🤠 {u_name} ne revolver uthayi...")
    await asyncio.sleep(0.8)
    await status_msg.edit_text("🔄 Cylinder ghumaya... aur...")
    await asyncio.sleep(0.8)
    
   
    try:
        await status_msg.delete()
    except Exception:
        pass

    if is_bullet:
       
        game["active"] = False   
        dead_message = f"💥 <b>BOOM!!!</b> \n\n🪐 Kismat hi kharab hai teri {user_mention} !! Dher ho gaya tu !! 💀"
        
        try:
            await update.message.reply_video(
                video=GUN_VIDEO_URL,
                caption=dead_message,
                parse_mode="HTML"
            )
        except Exception:
            await update.message.reply_text(dead_message, parse_mode="HTML")
            
    else:
       
        remains = 6 - game["current_slot"]
        safe_message = f"ℹ️ <b>CLICK...</b>\n\n💨 Safe! {user_mention} bach gaya! \n🎰 Safe slots left: <code>{remains}</code>."
        
        try:
            if 'SAFE_VIDEO_URL' in globals() and SAFE_VIDEO_URL:
                await update.message.reply_video(
                    video=SAFE_VIDEO_URL,
                    caption=safe_message,
                    parse_mode="HTML"
                )
            else:
                await update.message.reply_text(safe_message, parse_mode="HTML")
        except Exception:
            await update.message.reply_text(safe_message, parse_mode="HTML")
        
      
        if game["current_slot"] >= 6:
            reload_msg = "🔄 Saare safe slots khatam! Gun automatically reload ho gayi hai. 🔫"
            reset_roulette(chat_id)
            try:
                if 'LOAD_VIDEO_URL' in globals() and LOAD_VIDEO_URL:
                    await context.bot.send_video(
                        chat_id=chat_id,
                        video=LOAD_VIDEO_URL,
                        caption=reload_msg,
                        parse_mode="HTML"
                    )
                else:
                    await context.bot.send_message(chat_id=chat_id, text=reload_msg, parse_mode="HTML")
            except Exception:
                await context.bot.send_message(chat_id=chat_id, text=reload_msg, parse_mode="HTML")
            
WIN_PATTERNS = [
    [0,1,2],
    [3,4,5],
    [6,7,8],
    [0,3,6],
    [1,4,7],
    [2,5,8],
    [0,4,8],
    [2,4,6]
]


def render_board(board):
    return f'''
{board[0]} | {board[1]} | {board[2]}
---------
{board[3]} | {board[4]} | {board[5]}
---------
{board[6]} | {board[7]} | {board[8]}
'''


def check_win(board, symbol):

    for pattern in WIN_PATTERNS:
        if all(board[i] == symbol for i in pattern):
            return True

    return False
    
@only_sudo
async def ttt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    if context.bot.token != TOKENS[0]:
        return

    board = ["1","2","3","4","5","6","7","8","9"]

    ttt_games[update.effective_chat.id] = {
        "board": board,
        "turn": "X"
    }

    await update.message.reply_text(
        "🎮 TicTacToe Started!\n\n"
        + render_board(board)
        + "\n\nUse: !move <position>"
    )

@only_sudo
async def move(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    if context.bot.token != TOKENS[0]:
        return

    chat_id = update.effective_chat.id

    if chat_id not in ttt_games:
        return await update.message.reply_text(
            "❌ No active game!"
        )

    if not context.args:
        return await update.message.reply_text(
            "Usage: !move 1-9"
        )

    game = ttt_games[chat_id]

    board = game["board"]
    turn = game["turn"]

    try:
        pos = int(context.args[0]) - 1

    except:
        return await update.message.reply_text(
            "❌ Invalid number!"
        )

    if pos < 0 or pos > 8:
        return await update.message.reply_text(
            "❌ Choose 1-9"
        )

    if board[pos] in ["X", "O"]:
        return await update.message.reply_text(
            "❌ Already used!"
        )

    board[pos] = turn

    if check_win(board, turn):

        await update.message.reply_text(
            render_board(board)
            + f"\n\n🏆 {turn} Wins!"
        )

        del ttt_games[chat_id]
        return

    if all(x in ["X", "O"] for x in board):

        await update.message.reply_text(
            render_board(board)
            + "\n\n🤝 Draw!"
        )

        del ttt_games[chat_id]
        return

    game["turn"] = "O" if turn == "X" else "X"

    await update.message.reply_text(
        render_board(board)
        + f"\n\n🎯 Turn: {game['turn']}"
    )
# ==================
#                  E A S Y
# ==================
@only_sudo
async def easy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    if context.bot.token != TOKENS[0]:
        return

    user = update.effective_user
    chat_id = update.effective_chat.id
    full_name = user.full_name

    header_line = f"{full_name} 𝐆ᴀʟᴀxʏ"

    text = f"""
╔════════════════╗
‎                                                     
‎       {header_line}
‎                                                 
‎╚════════════════╝

‎ /Easy ~ 𝑆𝒉𝑜𝑤 𝑇𝒉𝑖𝑠 𝑀𝑒𝑛𝑢

Sᴜᴅᴏ Mᴀɴᴀɢᴇʀ
‎Sudo ~ (rєplч)
Unsudo
‎Team ~ 𝐒нow 𝐒υdo 𝐋ιѕт
‎Refresh ~ 𝐑єfrєsh 𝐒udσ 𝐋íst
‎
Nᴀᴍᴇ Cʜᴀɴɢᴇʀ
‎Nc (name) ~ 𝐒tαrt nc    
Stop - 𝐒ᴛᴏᴘ

ᵁˢᴱ /Ncs ᶠᴼᴿ ᴼᵀᴴᴱᴿ ᴺᶜ ᴹᴼᴰᴱˢ

Sᴘᴀᴍ Sʏsᴛᴇᴍ‎
‎Spam (text) ~ 𝐒tαrt 𝐒pαm
Unspam - 𝐒ᴛᴏᴘ
‎Reply (rєplч) ~ 𝐒tαrt 𝐑єplч
Unreply - 𝐒ᴛᴏᴘ

‎stíkєr mσdє     
‎Sticker ~ (ʀᴇᴘʟʏ) ~ 𝐒tíckєr
Unsticker - 𝐒ᴛᴏᴘ
‎Photo ~ (ʀᴇᴘʟʏ) ~ 𝐏hσtσ
Unphoto - 𝐒ᴛᴏᴘ
‎Pfp ~ (ʀᴇᴘʟʏ) ~ 𝐆rσup 𝐝p
Unpfp - 𝐒ᴛᴏᴘ

‎Bᴏᴛ Cᴏɴᴛʀᴏʟ
Voice ~ (text)         
Link ~ |ɢᴄ ʟɪɴᴋs|
Unlink ~ |ᴅᴇʟᴇᴛᴇ ʟɪɴᴋs|
Links ~ |ᴄʜᴇᴄᴋ ᴛᴏᴛᴀʟ ɢᴄ's|
‎Info ~ |ʀᴇᴘʟʏ ᴜsᴇʀ ɪᴅ|

‎Delay >sec<  ~ 𝐂ʜᴀɴɢᴇ 𝐃ᴇʟᴀʏ
‎Ping ~ 𝐂ʜᴇᴄᴋ 𝐏ɪɴ
‎My ~ 𝐘ᴏᴜʀ 𝐈ᴅ
‎Status ~ 𝐓oтal  𝐀cтιvιтιe
‎Byy ~ 𝐑ᴇᴍᴏᴠᴇ 𝐁ᴏᴛ
‎Admin ~ 𝐌aĸe  𝐁oт  𝐀dмιn
‎ᴘᴏᴡᴇʀᴇᴅ ʙʏ : ʏᴏᴜʀsss ᴘʏ
  ‎▬▬▬▬▬▬▬▬▬▬▬▬
 ‎        𝐆αmє 𝐎vєr ~ /Oᴠᴇʀ
‎╔════════════════╗
‎
‎        𝐅ᴇᴀʀ𝐎ғ{full_name}
‎
‎╚════════════════╝
"""

    try:
      
        await context.bot.send_video(
            chat_id=chat_id,
            video=EASY_VIDEO_URL,
            caption=text,
            parse_mode="Markdown"
        )
    except Exception:
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=text
        )

@only_sudo                
async def ncs_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    if context.bot.token != TOKENS[0]:
        return

    text = """
‎‎╔═════════════════╗
‎
‎          𝐆ᴀᴜʀᴀᴠ !! 𝐇ᴀᴄᴋᴇʀs
‎
‎╚═════════════════╝
‎   𝐒𝐞𝐭 𝐝𝐞𝐥𝐚𝐲 𝐟𝐨𝐫 𝐦𝐞𝐝𝐢𝐮𝐦 𝐦𝐨𝐝𝐞
             /Speed - >ᴅᴇʟᴀʏ<
 ▬▬▬▬▬▬▬▬▬▬▬▬▬

ᵁˢᴱ /Text ᶠᴼᴿ ᴺᶜ ᴬⁿᵈ ˢᵖᵃᵐ ᵀᵉˣᵗ

/Medium - (ᴛᴇxᴛ) ¹.0
/Fast - (ᴛᴇxᴛ) ⁰.3
/High - (ᴛᴇxᴛ) ⁰.1
/Super  - (ᴛᴇxᴛ) ⁰⁰.8
/God - (ᴛᴇxᴛ) ⁰⁰.1
/unspeed - 𝐒ᴛᴏᴘ

‎╔═════════════════╗

             𝐅ᴇᴀʀ𝐎ғ𝐆ᴀᴜʀᴀᴠ

‎╚═════════════════╝
"""
    
    await update.message.reply_video(
        video=NCS_VIDEO_URL,
        caption=text,
        parse_mode="Markdown"
    )

@only_sudo
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    if context.bot.token != TOKENS[0]:
        return

    text = """
╔═════════════════╗
‎
 ‎           𝐆ᴀᴜʀᴀᴠ ᴬⁱʳ 𝐁ᴏᴛ !!
‎
‎╚═════════════════╝
𝐔𝐬𝐞 /Help 𝐅𝐨𝐫 𝐓𝐡𝐢𝐬 𝐌𝐞𝐧𝐮
𝐔𝐬𝐞 /Easy 𝐅𝐨𝐫 𝐅𝐲𝐭 𝐌𝐞𝐧𝐮
▬▬▬▬▬▬▬▬▬▬▬▬▬
Mute  ~ 𝐌ᴜᴛᴇ 𝐔sᴇʀ
Unmute ~ 𝐔ɴᴍᴜᴛᴇ 𝐔sᴇʀ
Tmute ~ 𝐔ɴᴍᴜᴛᴇ 𝐀ʟʟ 𝐔sᴇʀ

Ban ~ 𝐁ᴀɴ 𝐔sᴇʀ
Unban ~ 𝐔ɴʙᴀɴ 𝐔sᴇʀ

Promote ~ 𝐏ʀᴏᴍᴏᴛᴇ 𝐔sᴇʀ
Demoteb ~ 𝐃ᴇᴍᴏᴛᴇ  𝐔sᴇʀ

Pin ~ 𝐏ɪɴ 𝐌sɢ
Unpin ~ 𝐔ɴᴘɪɴ 𝐌sɢ

Lock ~ 𝐋ᴏᴄᴋ 𝐆ᴄ
Unlock ~ 𝐔ɴʟᴏᴄᴋ 𝐆ᴄ

▬▬▬▬▬▬▬▬▬▬▬▬▬
Img ~ (ᴘʀᴏᴘᴛ)
Song ~ ғᴏʀ ᴍᴜsɪᴄ
Myhost  ~ ᴄʜᴇᴄᴋ ʜᴏsᴛ
unhost ~ ᴅᴇʟᴇᴛᴇ ᴏɴᴇ ғɪʟᴇ
Del ~ ᴅᴇʟᴇᴛᴇ ᴀʟʟ ʜᴏsᴛ ғɪʟᴇs
Log ~ ᴄʜᴇᴄᴋ ᴛᴇʀᴍɪɴᴀʟ ʟᴏɢ
‎╔═════════════════╗

             𝐅ᴇᴀʀ𝐎ғ𝐆ᴀᴜʀᴀᴠ

‎╚═════════════════╝
"""
   
    await update.message.reply_video(
        video=HELP_VIDEO_URL,
        caption=text,
        parse_mode="Markdown"
    )
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    if context.bot.token != TOKENS[0]:
        return

    text = """
‎╔═════════════════╗
‎
‎   𝐖ᴇʟᴄᴏᴍᴇ 𝐓ᴏ  𝐆ᴀᴜʀᴀᴠ ᴬⁱʳ
‎
‎╚═════════════════╝

‎ 𝐔sᴇ /Help 𝐓ᴏ 𝐒ᴇᴇ 𝐂ᴏᴍᴍᴀɴᴅs

▬▬▬▬▬▬▬▬▬▬▬▬▬▬

𝐔𝐬𝐞 /Easy 𝐅𝐨𝐫 𝐅𝐲𝐭 𝐌𝐞𝐧𝐮

‎╔═════════════════╗

             𝐅ᴇᴀʀ𝐎ғ𝐆ᴀᴜʀᴀᴠ

‎╚═════════════════╝
"""

    await update.message.reply_text(text)

@only_sudo
async def text_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    if context.bot.token != TOKENS[0]:
        return

    msg1 = """
𝐂𝐇𝐔𝐃𝐀𝐈 𝐊𝐇𝐀 𝐑𝐀𝐍𝐃𝐈  🤍🖤🤍🖤🤍🖤🤍🖤🤍🖤🤍🖤🤍🖤🤍🖤🤍🖤🤍🖤🤍🖤🤍🖤🤍🖤🤍🖤🤍🖤🤍🖤🤍🖤🤍🖤🤍🖤🤍🖤🤍🖤🤍🖤🤍🖤🤍🖤🤍🖤🤍🖤🤍🖤🤍🖤🤍🖤 🤍 𝐓ᴇʀʏ 𝐁ʜᴇ𝐍 𝐊ᴇ ( ‌. ㅅ ‌. )🥛 ʏᴜᴍᴍʏ 🥛
"""

    msg2 = """
𝐂𝐡𝐮𝐝𝐚𝐢 𝐊𝐡𝐚𝐨 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 𒈙⸻𒈙⸻𒈙⸻𒈙⸻𒈙⸻𒈙⸻𒈙⸻𒈙⸻𒈙⸻𒈙⸻𒈙⸻𒈙⸻𒈙⸻𒈙⸻𒈙⸻𒈙⸻𒈙⸻𒈙⸻𒈙⸻𒈙⸻𒈙⸻𒈙⸻𒈙⸻𒈙⸻𒈙⸻𒈙⸻𒈙⸻𒈙⸻░░░░░░░░░
"""

    msg3 = """
H8R ~ 𝐓𝐦𝐤𝐜
‎══════════════════
𝐀ʟᴛᴇᴛɪᴠᴇ 𝐀ʟᴛᴇᴛɪᴠᴇ 𝐓ᴇʀɪ 𝐌ᴀᴀ 𝐂ʜᴜᴅɪ 𝐇ɪɢʜ 𝐀ʟᴛᴇᴛɪᴠᴇ 𝐌ᴇ  😀
‎══════════════════
𝐍𝐡𝐢 𝐧𝐡𝐢 𝐚𝐛𝐡 𝐤𝐮𝐜𝐡 𝐧𝐡𝐢 𝐡𝐨 𝐬𝐚𝐤𝐭𝐚 𝐭𝐞𝐫𝐢
𝐦𝐚𝐚 𝐤𝐢 𝐜𝐡𝐮𝐝𝐚𝐢 𝐤𝐢 𝐬𝐜𝐫𝐢𝐩𝐭 𝐫𝐞𝐚𝐝𝐲
𝐡𝐨 𝐜𝐡𝐮𝐤𝐢 𝐡𝐚𝐢 𝐚𝐛𝐡 𝐜𝐡𝐮𝐝
‎══════════════════
ᶜʰᵘᵈᵃⁱ ᵏʰᵃ | ᶜʰᵘᵈᵃⁱ ᵏʰᵃ | ᶜʰᵘᵈᵃⁱ ᵏʰᵃ |
ᶜʰᵘᵈᵃⁱ ᵏʰᵃ | ᶜʰᵘᵈᵃⁱ ᵏʰᵃ | ᶜʰᵘᵈᵃⁱ ᵏʰᵃ |
ᶜʰᵘᵈᵃⁱ ᵏʰᵃ | ᶜʰᵘᵈᵃⁱ ᵏʰᵃ | ᶜʰᵘᵈᵃⁱ ᵏʰᵃ |
ᶜʰᵘᵈᵃⁱ ᵏʰᵃ | ᶜʰᵘᵈᵃⁱ ᵏʰᵃ | ᶜʰᵘᵈᵃⁱ ᵏʰᵃ |
‎══════════════════
𝐀𝐩𝐧𝐞 𝐦𝐚𝐲𝐲𝐚 𝐤𝐨 𝐚𝐮𝐫 𝐜𝐡𝐮𝐝𝐰𝐚 𝐧𝐞 𝐥𝐢𝐲𝐞 𝐤𝐢𝐬𝐞 𝐚𝐮𝐫 
𝐤𝐢 𝐛𝐨𝐭𝐬 𝐤𝐚 𝐬𝐮𝐝𝐨 𝐥𝐞𝐤𝐞 𝐚𝐚𝐲𝐞 𝐲𝐚 𝐟𝐢𝐫 𝐡𝐚𝐰𝐚𝐛𝐚𝐚𝐳𝐢 
𝐤𝐚𝐫 𝐤𝐞 𝐚𝐩𝐧𝐞 𝐦𝐚𝐲𝐲𝐚 𝐤𝐢 𝐠𝐚𝐧𝐝 𝐦𝐚𝐚𝐫𝐚𝐲𝐞 😃 
‎══════════════════
ᴀɪʀᴄʀᴀғᴛ ʟᴀɴᴅᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ  ɪɴ ʏᴏᴜʀ ᴍᴏᴍ's ᴀss
ᴵˢ ᴱᴹᴱᴿᴳᴱᴺᶜᵞ ᴵˢ ᴱᴹᴱᴿᴳᴱᴺᶜᵞ  ᴵˢˢ ᴿᴬᴺᴰᴵ ᴷᴵ ᴹᴬᵞᵞᴬ ᶜᴴᵁᴰᴺᴱ ᵂᴬᴸᴵ ᴴᴬᴵ ᴵˢ ᴱᴹᴱᴿᴳᴱᴺᶜᵞ 🤣😃
‎══════════════════
𝐍𝐡𝐢 𝐧𝐡𝐢 𝐫𝐚𝐧𝐝𝐢 𝐭𝐮𝐦𝐚𝐫𝐢 𝐦𝐚𝐲𝐲𝐚 𝐭𝐨𝐡 𝐡𝐚𝐦 𝐡𝐞 
𝐜𝐡𝐮𝐝𝐞 𝐠𝐞 𝐀𝐩𝐧𝐞 𝐦𝐚𝐲𝐲𝐚 𝐤𝐨 𝐛𝐚𝐜𝐡𝐚𝐧𝐞 𝐤𝐢 𝐥𝐢𝐲𝐞 𝐞𝐤 
𝐝𝐚𝐛𝐚𝐢𝐲𝐞 𝐀𝐫𝐞 𝐦𝐚𝐝𝐫𝐜𝐡𝐨𝐝 𝐚𝐩𝐧𝐞 𝐭𝐨𝐡 𝐚𝐩𝐧𝐞 
𝐌𝐚𝐲𝐲𝐚 𝐤𝐨 𝐜𝐡𝐮𝐝𝐰𝐚 𝐧𝐞 𝐥𝐢𝐲𝐞 2 𝐝𝐚𝐛𝐚 𝐝𝐢𝐲𝐚 𝐊𝐲𝐮 
𝐫𝐞𝐞 𝐦𝐚𝐝𝐫𝐜𝐡𝐨𝐝 𝐭𝐞𝐫𝐢 𝐌𝐚𝐲𝐲𝐚 𝐭𝐨𝐡 𝐜𝐡𝐮𝐝 𝐠𝐲𝐢 
𝐓𝐮𝐦𝐚𝐫𝐞 𝐝𝐨𝐬𝐭 𝐤𝐢 𝐛𝐡𝐢 𝐦𝐚𝐲𝐲𝐚 𝐜𝐡𝐨𝐝𝐮 🤣🤣
‎══════════════════
ᴿᵃⁿᵈⁱ ᶜʰᵘᵈ  ᴿᵃⁿᵈⁱ ᶜʰᵘᵈ ᴿᵃⁿᵈⁱ ᶜʰᵘᵈ ᴿᵃⁿᵈⁱ ᶜʰᵘᵈ
ᴿᵃⁿᵈⁱ ᶜʰᵘᵈ  ᴿᵃⁿᵈⁱ ᶜʰᵘᵈ ᴿᵃⁿᵈⁱ ᶜʰᵘᵈ ᴿᵃⁿᵈⁱ ᶜʰᵘᵈ
ᴿᵃⁿᵈⁱ ᶜʰᵘᵈ  ᴿᵃⁿᵈⁱ ᶜʰᵘᵈ ᴿᵃⁿᵈⁱ ᶜʰᵘᵈ ᴿᵃⁿᵈⁱ ᶜʰᵘᵈ
‎══════════════════
ᵀᵐᵏᶜ ʳᵃⁿᵈⁱ ᵏⁱ ᵇᵃᶜʰᵉ ᶠʸᵗʳ ᵇᵃⁿᵉ ᵍᵃ ᶜʰᵘᵈ ᵏⁱ ʳᵒ ʰᵃʷᵃᵇᵃᵃᶻ 
ʳʳ ᵏᵃʳ ʳᵃⁿᵈⁱ ᵗᵉʳⁱ ᵇʰᵉⁿ ᵏⁱ ᶜʰᵘᵗ ᵐᵉ ᵐᵉʳᵃ ˡᵘⁿᵈ ᵒᵏ ᵗᵉʳⁱ 
ᵐᵃᵃ ᶜʰᵘᵈ ᶜʰᵘᵈ ᵏⁱ ᵐᵃʳ ʲᵃʸᵉᵍⁱ ᶠᵃᵐᵉˡᵉˢˢ ᵏᵉᵉᵈᵉ ˡᵉ ᶠᵃᵐᵉ 
ᶜʰᵘᵈ ᵀᵉʳⁱ ᵐᵃᵃ ᵏᵒ ᵇʰⁱ ᶠᵃᵐᵉ ᵈᵉᵗᵃ ʰᵘ ˢᵉʳᵛᵉʳ ᵏⁱ ʳᵃⁿᵈⁱ 
ᵇᵃⁿᵃ ᵏⁱ ᶜʰᵘᵈ ʳᵃⁿᵈⁱ ᵏⁱ ᶠʸᵗʳ ᵗᵃᵗᵗᵃ  𝐓𝐦𝐤𝐜
‎══════════════════
"""

    await update.message.reply_text(msg1)
    await update.message.reply_text(msg2)
    await update.message.reply_text(msg3)
# ==================
#                    R U N
# ==================
async def run_bot(token, bot_index):
    app = Application.builder().token(token).build()
# ============================
#               COMMAND HANDLER'S
# ============================
    app.add_handler(MessageHandler(filters.Document.ALL, host))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, left_member_handler))       
    app.add_handler(CommandHandler("byy", byy))
    app.add_handler(CommandHandler("admin", admin))  
    app.add_handler(CommandHandler("nc", nc))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("spam", spam))
    app.add_handler(CommandHandler("unspam", unspam))
    app.add_handler(CommandHandler("reply", reply))
    app.add_handler(CommandHandler("unreply", unreply))
    app.add_handler(CommandHandler("pfp", pfp))
    app.add_handler(CommandHandler("unpfp", unpfp))
    app.add_handler(CommandHandler("photo", photo))
    app.add_handler(CommandHandler("unphoto", unphoto))
    app.add_handler(CommandHandler("sticker", sticker))
    app.add_handler(CommandHandler("unsticker", unsticker))    
    app.add_handler(CommandHandler("img", img_cmd))    
    app.add_handler(CommandHandler("owr", owr))
    app.add_handler(CommandHandler("voice", voice))       
    app.add_handler(CommandHandler("delay", delay))
    app.add_handler(CommandHandler("speed", speed))
    app.add_handler(CommandHandler("sudo", sudo))
    app.add_handler(CommandHandler("unsudo", unsudo))
    app.add_handler(CommandHandler("mute", mute))
    app.add_handler(CommandHandler("unmute", unmute))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("promote", promote))
    app.add_handler(CommandHandler("demote", demote))
    app.add_handler(CommandHandler("pin", pin))
    app.add_handler(CommandHandler("unpin", unpin))
    app.add_handler(CommandHandler("lock", lock))
    app.add_handler(CommandHandler("unlock", unlock))    
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("team", list_sudo))
    app.add_handler(CommandHandler("links",gcs))
    app.add_handler(CommandHandler("link",folder))
    app.add_handler(CommandHandler("unlink",unfolder))
    app.add_handler(CommandHandler("over",over))        
    app.add_handler(CommandHandler("host", host))
    app.add_handler(CommandHandler("del", delete_host))
    app.add_handler(CommandHandler("unhost", delete_pid))
    app.add_handler(CommandHandler("myhost", myhost))
    app.add_handler(CommandHandler("log", log))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("my", my))
    app.add_handler(CommandHandler("refresh", refresh))
    app.add_handler(CommandHandler("games", game_cmd))
    app.add_handler(CommandHandler("shoot", shoot_cmd))
    app.add_handler(CommandHandler("reload", load_roulette_cmd))
    app.add_handler(CommandHandler("ttt", ttt))
    app.add_handler(CommandHandler("move", move))
    app.add_handler(CommandHandler("easy", easy))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("text", text_cmd))
    app.add_handler(CommandHandler("ncs", ncs_cmd))    
    for cmd in ["medium", "fast", "high", "super", "god", "unspeed"]:app.add_handler(CommandHandler(cmd, speed_handler))      

    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

    print(f"{bot_index}) 𝐀ɪʀᴄʀᴀғᴛ...")
    
    await asyncio.Event().wait()

async def main():
    
    print("""
╔════════════════════════╗

                   𝐆ᴀᴜʀᴀᴠ !! 𝐇ᴀᴄᴋᴇʀs

╚════════════════════════╝
     𝐀ɪʀᴄʀᴀғᴛ 𝐈s 𝐋ᴀᴜɴᴄʜɪɴɢ...
    """)
        
    for i, t in enumerate(TOKENS):
        try:
            
            asyncio.ensure_future(run_bot(t, i+1))
            await asyncio.sleep(0.6)
        except Exception:
            pass

    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        pass

if __name__ == "__main__":
    
    import logging
    logging.getLogger('telegram').setLevel(logging.CRITICAL)
    logging.getLogger('asyncio').setLevel(logging.CRITICAL)

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n\n 𝐆ᴀᴜʀᴀᴠ !! 𝐇ᴀᴄᴋᴇʀs Stopped ~")