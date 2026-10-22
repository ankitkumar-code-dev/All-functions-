import re
import sqlite3
import requests
import telebot
import time
from telebot import types
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging
import os
from datetime import date
import datetime
from threading import Thread
from flask import Flask
#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99
        #Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99
                #Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99
                #Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99
                #Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99
                #Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99
                #Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99
                #Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99
                #Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99
                #Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99
                #Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99
                #Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99
                #Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99
                #Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99
                #Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99
                #Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99
                #Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99
                #Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99
#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99
        
# ========== BOT INITIALIZATION ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
bot = telebot.TeleBot(BOT_TOKEN)

# ========== CONFIG ==========
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8284008909"))
DB_FILE = "users.db"

# ========== CHANNEL CONFIG ==========
CHANNEL_USERNAME = "JOIN ALL CHANEL AND RESTART THE BOT 🫣"  # अपना channel username without @
#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99

CHANNEL_LINK = "https://t.me/KPBOTMAKER"  # अपना channel link
CHANNEL_ID = "-1003296237197"  # Channel username या ID

# ========== LOGGING SETUP ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== DATABASE SETUP ==========
class Database:
    def __init__(self, db_file):
        self.db_file = db_file
        self._create_tables()
    
    def get_cursor(self):
        conn = sqlite3.connect(self.db_file)
        return conn.cursor()
    
    def _create_tables(self):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        # Users table
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (user_id INTEGER PRIMARY KEY, credits INTEGER DEFAULT 5, 
                      last_credit_date TEXT, is_blocked INTEGER DEFAULT 0)''')
        
        # History table
        c.execute('''CREATE TABLE IF NOT EXISTS history
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, 
                      query TEXT, api_type TEXT, ts TEXT)''')
        
        # Blocked users table
        c.execute('''CREATE TABLE IF NOT EXISTS blocked_users
                     (user_id INTEGER PRIMARY KEY, blocked_by INTEGER, 
                      reason TEXT, blocked_at TEXT)''')
        
        # Profile views table
        c.execute('''CREATE TABLE IF NOT EXISTS profile_views 
                     (user_id INTEGER, date TEXT, count INTEGER, PRIMARY KEY (user_id, date))''')
        
        conn.commit()
        conn.close()

db = Database(DB_FILE)

# ========== SPECIAL USERS ==========
SPECIAL_USERS = [
    {"id": 8170649372, "name": "Admin"},
    {"id": 1234567890, "name": "Test User"}
]

# ========== UTILITY FUNCTIONS ==========
def is_admin(user_id):
    return user_id == ADMIN_ID

def is_special_user(user_id):
    return any(user["id"] == user_id for user in SPECIAL_USERS)

def init_user(user_id):
    cur = db.get_cursor()
    cur.execute("INSERT OR IGNORE INTO users (user_id, credits) VALUES (?, 5)", (user_id,))
    cur.connection.commit()

def get_credits(user_id):
    cur = db.get_cursor()
    cur.execute("SELECT credits FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    return row[0] if row else 0

def set_credits(user_id, credits):
    cur = db.get_cursor()
    cur.execute("UPDATE users SET credits=? WHERE user_id=?", (credits, user_id))
    cur.connection.commit()

def change_credits(user_id, amount):
    cur = db.get_cursor()
    cur.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (amount, user_id))
    cur.connection.commit()
    return get_credits(user_id)

def add_history(user_id, query, api_type):
    cur = db.get_cursor()
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("INSERT INTO history (user_id, query, api_type, ts) VALUES (?, ?, ?, ?)",
                (user_id, query, api_type, ts))
    cur.connection.commit()

def refund_credit(user_id):
    cur = db.get_cursor()
    cur.execute("UPDATE users SET credits = credits + 1 WHERE user_id=?", (user_id,))
    cur.connection.commit()

def is_user_blocked(user_id):
    cur = db.get_cursor()
    cur.execute("SELECT is_blocked FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    return row and row[0] == 1

def block_user(user_id, blocked_by, reason=""):
    try:
        cur = db.get_cursor()
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("INSERT OR REPLACE INTO blocked_users (user_id, blocked_by, reason, blocked_at) VALUES (?, ?, ?, ?)",
                    (user_id, blocked_by, reason, ts))
        cur.execute("UPDATE users SET is_blocked=1 WHERE user_id=?", (user_id,))
        cur.connection.commit()
        return True
    except Exception as e:
        logger.error(f"Error blocking user {user_id}: {e}")
        return False

def unblock_user(user_id):
    try:
        cur = db.get_cursor()
        cur.execute("DELETE FROM blocked_users WHERE user_id=?", (user_id,))
        cur.execute("UPDATE users SET is_blocked=0 WHERE user_id=?", (user_id,))
        cur.connection.commit()
        return True
    except Exception as e:
        logger.error(f"Error unblocking user {user_id}: {e}")
        return False

def get_last_credit_date(user_id):
    cur = db.get_cursor()
    cur.execute("SELECT last_credit_date FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    return row[0] if row else None

def check_and_give_daily_credits(user_id):
    today = date.today().isoformat()
    last_date = get_last_credit_date(user_id)
    
    if last_date != today:
        cur = db.get_cursor()
        cur.execute("UPDATE users SET credits=credits+10, last_credit_date=? WHERE user_id=?", 
                   (today, user_id))
        cur.connection.commit()
        return True
    return False

def send_long(chat_id, text, max_length=4096):
    if len(text) <= max_length:
        bot.send_message(chat_id, text, parse_mode="HTML")
    else:
        parts = [text[i:i+max_length] for i in range(0, len(text), max_length)]
        for part in parts:
            bot.send_message(chat_id, part, parse_mode="HTML")
            time.sleep(0.1)

def make_request(url, timeout=30):
    try:
        session = requests.Session()
        retry = Retry(total=3, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = session.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        try:
            return response.json()
        except ValueError:
            return response.text
            
    except Exception as e:
        logger.error(f"Request error for {url}: {e}")
        return None

def handle_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            try:
                if len(args) > 0 and hasattr(args[0], 'chat') and hasattr(args[0].chat, 'id'):
                    bot.send_message(args[0].chat.id, "❌ An error occurred. Please try again later.")
            except:
                pass
    return wrapper

def clean(text):
    if text is None:
        return None
    
    text = str(text).strip()
    
    if not text or text.lower() in ['null', 'none', 'nil', 'nan', '']:
        return None
    
    return text

# ========== CHANNEL FORCE JOIN FUNCTIONS ==========
def check_channel_membership(user_id):
    try:
        chat_member = bot.get_chat_member(CHANNEL_ID, user_id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Error checking channel membership for {user_id}: {e}")
        return False

def send_channel_join_message(chat_id):
    keyboard = types.InlineKeyboardMarkup()
    join_button = types.InlineKeyboardButton("📢 Join Our Channel", url=CHANNEL_LINK)
    check_button = types.InlineKeyboardButton("✅ I've Joined", callback_data="check_join")
    keyboard.add(join_button)
    keyboard.add(check_button)
    
    message_text = f"""
🔒 <b>Channel Membership Required</b>

▀▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▀

┊  JOIN OUR CHANNEL  ┊

▄▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▄


♿ Bot Source Code https://t.me/KP_INFORMER_BOT
👇 Click the button below to join our channel, then click "I've Joined" to verify.
    """
    
    bot.send_message(chat_id, message_text, reply_markup=keyboard, parse_mode="HTML")

# ========== CHANNEL JOIN CALLBACK HANDLER ==========
@bot.callback_query_handler(func=lambda call: call.data == "check_join")
@handle_errors
def check_join_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    if check_channel_membership(user_id):
        bot.answer_callback_query(call.id, "✅ Verification successful! Welcome to InfoBot!")
        bot.delete_message(chat_id, call.message.message_id)
        cmd_start(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ You haven't joined the channel yet. Please join and try again.")

# ========== MODIFIED ENSURE AND CHARGE FUNCTION ==========
@handle_errors
def ensure_and_charge(uid: int, chat_id: int) -> bool:
    if not is_admin(uid) and not is_special_user(uid) and not check_channel_membership(uid):
        send_channel_join_message(chat_id)
        return False
        
    if is_user_blocked(uid):
        bot.send_message(chat_id, "⚠️ <b>Your account has been blocked.</b>\n\nPlease contact admin for more information.")
        return False
        
    init_user(uid)
    
    if is_special_user(uid):
        return True
        
    credits = get_credits(uid)
    if credits <= 0:
        kb = types.InlineKeyboardMarkup(row_width=1)
        btn1 = types.InlineKeyboardButton("💳 Buy Credits", callback_data="buy_credits")
        kb.add(btn1)
        
        message_text = "❌ <b>No credits left.</b>\n\nYou can purchase more credits using the button below."
        
        bot.send_message(chat_id, message_text, reply_markup=kb)
        return False
    set_credits(uid, credits - 1)
    return True

# ========== MODIFIED START COMMAND ==========
@bot.message_handler(commands=["start"])
@handle_errors
def cmd_start(m):
    try:
        uid = m.from_user.id
        chat_id = m.chat.id
        
        logger.info(f"Start command received from user {uid}")
        
        # Check if user is blocked
        try:
            if is_user_blocked(uid):
                bot.send_message(chat_id, "⚠️ <b>Your account has been blocked.</b>\n\nPlease contact admin for more information.")
                return
        except Exception as e:
            logger.error(f"Error checking user block status: {e}")
            # Continue even if block check fails

        # Check channel membership for non-admin and non-special users
        try:
            if not is_admin(uid) and not is_special_user(uid):
                if not check_channel_membership(uid):
                    send_channel_join_message(chat_id)
                    return
        except Exception as e:
            logger.error(f"Error checking channel membership: {e}")
            # Continue even if channel check fails

        # Initialize user in database
        try:
            init_user(uid)
        except Exception as e:
            logger.error(f"Error initializing user: {e}")
            # Continue even if init fails

        # Set unlimited credits for special users
        try:
            if is_special_user(uid):
                set_credits(uid, 999)
                logger.info(f"Set unlimited credits for special user {uid}")
        except Exception as e:
            logger.error(f"Error setting special user credits: {e}")

        # Give daily credits to regular users
        try:
            if not is_special_user(uid):
                if check_and_give_daily_credits(uid):
                    logger.info(f"Daily credits given to user {uid}")
        except Exception as e:
            logger.error(f"Error giving daily credits: {e}")

        # Get current credits
        try:
            credits = get_credits(uid)
        except Exception as e:
            logger.error(f"Error getting credits: {e}")
            credits = 0

        # Create keyboard layout - SIMPLIFIED VERSION
        try:
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            
            # Add buttons in rows
            kb.add(
                types.KeyboardButton("👤 Telegram ID Info"),
                types.KeyboardButton("🇮🇳 India Number Info")
            )
            kb.add(
                types.KeyboardButton("📱 Pakistan Number Info"), 
                types.KeyboardButton("📮 Pincode Info")
            )
            kb.add(
                types.KeyboardButton("🚘 Vehicle Info"),
                types.KeyboardButton("🆔 Aadhaar Info")
            )
            kb.add(
                types.KeyboardButton("🧪 ICMR Number Info"),
                types.KeyboardButton("🏦 IFSC Code Info")
            )
            kb.add(
                types.KeyboardButton("💸 UPI ID Info"),
                types.KeyboardButton("📋 Ration Card Info")
            )
            kb.add(
                types.KeyboardButton("🌐 IP Info"),
                types.KeyboardButton("🎮 Free Fire Info")
            )
            kb.add(
                types.KeyboardButton("👀 Free Fire Views"),
                types.KeyboardButton("💳 My Credits")
            )
            kb.add(
                types.KeyboardButton("💳 Buy Credits"),
                types.KeyboardButton("🎁 Get Daily Credits"),
                types.KeyboardButton("📜 My History")
            )
            kb.add(
                types.KeyboardButton("📞 Contact Admin"),
                types.KeyboardButton("🆔 My ID")
            )
            
            # Admin panel only for admin users
            if is_admin(uid):
                kb.add(types.KeyboardButton("⚙️ Admin Panel"))
                
        except Exception as e:
            logger.error(f"Error creating keyboard: {e}")
            # Create a simple keyboard as fallback
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(types.KeyboardButton("🆔 My ID"))
            kb.add(types.KeyboardButton("💳 My Credits"))

        # Start message text
        start_text = f"""
━━━━━━━━━━━━━━━━━━
🤖 <b>@KP_INFORMER_BOT</b>
<i>Your Digital Info Assistant 🚀</i>
━━━━━━━━━━━━━━━━━━

🔍 <b>Available Services:</b>
• 👤 Telegram ID Info
• 🇮🇳 India Number Info  
• 📱 Pakistan Number Info
• 📮 Pincode Details
• 🚘 Vehicle Info
• 🆔 Aadhaar Info
• 🧪 ICMR Number Info
• 🏦 IFSC Code Info
• 💸 UPI ID Info
• 📋 Ration Card Info
• 🌐 IP Info
• 🎮 Free Fire Info
• 👀 Free Fire Views

💳 <b>Your Credits:</b> <code>{credits}</code>
🎁 <b>Daily Credits:</b> Get 10 free credits every day!

⚠️ Each search costs <b>1 credit</b>.
Credits are refunded if no results found.

✅ <b>Choose an option below to begin!</b>

━━━━━━━━━━━━━━━━━━
© 2025 <b>@KP_INFORMER_BOT</b> | All Rights Reserved
━━━━━━━━━━━━━━━━━━
"""
        # Send message with better error handling
        try:
            bot.send_message(
                chat_id, 
                start_text, 
                reply_markup=kb, 
                disable_web_page_preview=True, 
                parse_mode="HTML"
            )
            logger.info(f"Start message sent successfully to user {uid}")
            
        except Exception as send_error:
            logger.error(f"Error sending start message: {send_error}")
            # Try without HTML formatting
            try:
                simple_text = "🤖 InfoBot - Your Digital Info Assistant\n\nUse the buttons below to get started!"
                bot.send_message(chat_id, simple_text, reply_markup=kb)
            except Exception as final_error:
                logger.error(f"Final error sending message: {final_error}")
                bot.send_message(chat_id, "Welcome! Please use the buttons to interact with the bot.")
        
    except Exception as e:
        logger.error(f"Critical error in start command: {e}", exc_info=True)
        try:
            bot.send_message(m.chat.id, "🚀 Welcome to InfoBot! Please use the menu buttons to get started.")
        except:
            pass  # Final fallback



# ========== TRUECALLER INFO ==========
import re
import requests
import logging
from typing import Optional, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

@bot.message_handler(func=lambda c: c.text == "🌐 IP Info")
@handle_errors
def ask_ip_address(m):
    """Ask user to input IP address for information lookup"""
    bot.send_message(m.chat.id, "🌐 Send IP address to get information (e.g., 8.8.8.8):")
    bot.register_next_step_handler(m, handle_ip_info)

@handle_errors
def handle_ip_info(m):
    """Handle IP information request with comprehensive error handling"""
    user_id = m.from_user.id
    chat_id = m.chat.id
    
    try:
        # Validate message content
        if not m.text or not m.text.strip():
            return bot.send_message(chat_id, "⚠️ Please send a valid IP address.")
        
        ip = m.text.strip()
        
        # Validate IP address format
        validation_result = validate_ip_address(ip)
        if not validation_result["valid"]:
            return bot.send_message(chat_id, f"⚠️ {validation_result['error']}")
        
        # Check user credits
        if not ensure_and_charge(user_id, chat_id):
            return
        
        # Show progress message
        progress_msg = bot.send_message(chat_id, "🔍 Searching IP information...")
        
        # Try multiple IP API services with fallback
        data = get_ip_info_with_fallback(ip)
        
        # Clean up progress message
        try:
            bot.delete_message(chat_id, progress_msg.message_id)
        except Exception:
            pass  # Ignore if deletion fails
        
        # Handle API errors
        if not data or data.get('error'):
            refund_credit(user_id)
            error_msg = data.get('error', 'Unable to retrieve IP information from available services')
            logger.warning(f"IP API error for {ip}: {error_msg}")
            return bot.send_message(chat_id, f"❌ {error_msg}")
        
        # Format and send successful response
        response = format_ip_response(data, ip)
        bot.send_message(chat_id, response, parse_mode="HTML")
        
        # Add to user history
        add_history(user_id, ip, "IP_INFO")
        
    except Exception as e:
        refund_credit(user_id)
        logger.error(f"Error in handle_ip_info: {e}", exc_info=True)
        bot.send_message(chat_id, "❌ An unexpected error occurred. Please try again later.")

def get_ip_info_with_fallback(ip_address: str) -> Optional[Dict[str, Any]]:
    """
    Try multiple IP API services with fallback mechanism
    """
    apis = [
        get_ip_info_ipapi_com,    # Most reliable free API
        get_ip_info_ipapi_co,     # Alternative ipapi.co
        get_ip_info_ipwhois,      # ipwhois.app
        get_ip_info_iphub,        # iphub.info as last resort
    ]
    
    for api_func in apis:
        try:
            logger.info(f"Trying API: {api_func.__name__} for IP: {ip_address}")
            data = api_func(ip_address)
            
            if data and not data.get('error'):
                # Verify we have at least some useful data
                if any(data.get(field) for field in ['country', 'city', 'isp', 'region']):
                    logger.info(f"Success with API: {api_func.__name__}")
                    return data
                else:
                    logger.warning(f"API {api_func.__name__} returned empty data")
            else:
                error_msg = data.get('error') if data else 'No data'
                logger.warning(f"API {api_func.__name__} failed: {error_msg}")
                
        except Exception as e:
            logger.error(f"API {api_func.__name__} error: {e}")
            continue
    
    return {'error': 'All IP information services are currently unavailable. Please try again later.'}

def get_ip_info_ipapi_com(ip_address: str) -> Optional[Dict[str, Any]]:
    """
    Use ip-api.com API (Free, reliable, no API key needed)
    """
    try:
        url = f"ADD_YOUR_IP_INFO_API?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        logger.info(f"ip-api.com response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"ip-api.com data: {data}")
            
            if data.get('status') == 'success':
                return {
                    'ip': data.get('query', ip_address),
                    'country': data.get('country'),
                    'countryCode': data.get('countryCode'),
                    'region': data.get('regionName'),
                    'city': data.get('city'),
                    'zip': data.get('zip'),
                    'lat': data.get('lat'),
                    'lon': data.get('lon'),
                    'timezone': data.get('timezone'),
                    'isp': data.get('isp'),
                    'org': data.get('org'),
                    'as': data.get('as'),
                    'status': 'success'
                }
            else:
                return {'error': data.get('message', 'API returned error')}
        else:
            return {'error': f'HTTP {response.status_code}'}
            
    except Exception as e:
        logger.error(f"ip-api.com error: {e}")
        return {'error': str(e)}

def get_ip_info_ipapi_co(ip_address: str) -> Optional[Dict[str, Any]]:
    """
    Use ipapi.co API (Free tier available)
    """
    try:
        url = f"ADD_YOUR_IP_INFO_API"#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99
        
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        logger.info(f"ipapi.co response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"ipapi.co data: {data}")
            
            if not data.get('error'):
                return {
                    'ip': data.get('ip', ip_address),
                    'country': data.get('country_name'),
                    'countryCode': data.get('country_code'),
                    'region': data.get('region'),
                    'city': data.get('city'),
                    'zip': data.get('postal'),
                    'lat': data.get('latitude'),
                    'lon': data.get('longitude'),
                    'timezone': data.get('timezone'),
                    'isp': data.get('org'),
                    'org': data.get('org'),
                    'as': data.get('asn'),
                    'status': 'success'
                }
            else:
                return {'error': data.get('reason', 'API returned error')}
        else:
            return {'error': f'HTTP {response.status_code}'}
            
    except Exception as e:
        logger.error(f"ipapi.co error: {e}")
        return {'error': str(e)}

def get_ip_info_ipwhois(ip_address: str) -> Optional[Dict[str, Any]]:
    """
    Use ipwhois.app API (Free, no API key needed)
    """
    try:
        url = f"ADD_YOUR_IP_INFO_API"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        logger.info(f"ipwhois response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"ipwhois data: {data}")
            
            if data.get('success') is not False:
                return {
                    'ip': data.get('ip', ip_address),
                    'country': data.get('country'),
                    'countryCode': data.get('country_code'),
                    'region': data.get('region'),
                    'city': data.get('city'),
                    'zip': data.get('postal'),
                    'lat': data.get('latitude'),
                    'lon': data.get('longitude'),
                    'timezone': data.get('timezone', {}).get('name'),
                    'isp': data.get('isp'),
                    'org': data.get('org'),
                    'as': data.get('asn'),
                    'status': 'success'
                }
            else:
                return {'error': data.get('message', 'API returned error')}
        else:
            return {'error': f'HTTP {response.status_code}'}
            
    except Exception as e:
        logger.error(f"ipwhois error: {e}")
        return {'error': str(e)}

def get_ip_info_iphub(ip_address: str) -> Optional[Dict[str, Any]]:
    """
    Use iphub.info as last resort (Free tier available)
    """
    try:
        # This is a basic fallback, may need API key for full access
        url = f"ADD_YOUR_IP_INFO_API"  # Using ip-api.com again as reliable fallback
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('status') == 'success':
                return {
                    'ip': data.get('query', ip_address),
                    'country': data.get('country'),
                    'countryCode': data.get('countryCode'),
                    'region': data.get('regionName'),
                    'city': data.get('city'),
                    'zip': data.get('zip'),
                    'lat': data.get('lat'),
                    'lon': data.get('lon'),
                    'timezone': data.get('timezone'),
                    'isp': data.get('isp'),
                    'org': data.get('org'),
                    'as': data.get('as'),
                    'status': 'success'
                }
        
        return {'error': 'Service unavailable'}
            
    except Exception as e:
        logger.error(f"iphub error: {e}")
        return {'error': str(e)}

def validate_ip_address(ip: str) -> Dict[str, Any]:
    """
    Validate IP address format and ranges
    """
    # Basic format validation
    if not re.fullmatch(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
        return {"valid": False, "error": "Invalid IP address format. Please use format like 8.8.8.8"}
    
    # Octet range validation
    octets = ip.split('.')
    for i, octet in enumerate(octets, 1):
        try:
            octet_num = int(octet)
            if not 0 <= octet_num <= 255:
                return {"valid": False, "error": f"Invalid IP address. Octet {i} must be between 0-255."}
        except ValueError:
            return {"valid": False, "error": f"Invalid IP address. Octet {i} must be a number."}
    
    # Check for private IP ranges
    first_octet = int(octets[0])
    second_octet = int(octets[1])
    
    if (first_octet == 10 or
        (first_octet == 172 and 16 <= second_octet <= 31) or
        (first_octet == 192 and second_octet == 168)):
        return {"valid": False, "error": "Private IP addresses cannot be looked up"}
    
    if first_octet == 127:
        return {"valid": False, "error": "Loopback address (127.x.x.x) cannot be looked up"}
    
    return {"valid": True}

def format_ip_response(data: Dict[str, Any], original_ip: str) -> str:
    """Format the IP information response with proper fallbacks"""
    
    # Extract and clean data with better fallbacks
    ip = clean(data.get('ip')) or original_ip
    country = clean(data.get('country')) or 'Unknown'
    country_code = clean(data.get('countryCode')) or 'N/A'
    region = clean(data.get('region')) or 'Unknown'
    city = clean(data.get('city')) or 'Unknown'
    zip_code = clean(data.get('zip')) or 'Unknown'
    lat = clean(data.get('lat')) or 'Unknown'
    lon = clean(data.get('lon')) or 'Unknown'
    timezone = clean(data.get('timezone')) or 'Unknown'
    isp = clean(data.get('isp')) or 'Unknown'
    org = clean(data.get('org')) or 'Unknown'
    as_number = clean(data.get('as')) or 'Unknown'
    
    # Format coordinates nicely
    coordinates = f"{lat}, {lon}"
    if lat == 'Unknown' or lon == 'Unknown':
        coordinates = 'Unknown'
    
    # Create formatted output
    response = f"""
🌐 <b>IP Address Information</b>
━━━━━━━━━━━━━━━━━━━━━━
🖥️ <b>IP Address:</b> <code>{ip}</code>
🌍 <b>Country:</b> {country} ({country_code})
🏙️ <b>Region:</b> {region}
🏠 <b>City:</b> {city}
📮 <b>ZIP Code:</b> {zip_code}
📍 <b>Coordinates:</b> {coordinates}
🕐 <b>Timezone:</b> {timezone}
📡 <b>ISP:</b> {isp}
🏢 <b>Organization:</b> {org}
🔢 <b>AS Number:</b> {as_number}
━━━━━━━━━━━━━━━━━━━━━━
✅ <i>Information retrieved successfully</i>
"""

    return response.strip()

def clean(text: Any) -> Optional[str]:
    """Clean and format text data"""
    if text is None:
        return None
    
    text = str(text).strip()
    
    # Remove None, null, empty strings
    if not text or text.lower() in ['null', 'none', 'nil', 'nan', '']:
        return None
    
    return text

# ========== ADMIN PANEL ==========
@bot.message_handler(func=lambda c: c.text == "⚙️ Admin Panel")
@handle_errors
def admin_panel(m):
    if not is_admin(m.from_user.id):
        return
    
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("💳 Add Credits", "💸 Remove Credits")
    kb.row("👥 All Users", "📋 User History")
    kb.row("📢 Broadcast", "🌟 Special Users")
    kb.row("🚫 Block User", "✅ Unblock User", "📋 Blocked Users")
    kb.row("🔙 Back to Main Menu")
    
    bot.send_message(m.chat.id, "⚙️ <b>Admin Panel</b>\n\nChoose an option:", reply_markup=kb, parse_mode="HTML")

# Add Credits Handler
@bot.message_handler(func=lambda c: c.text == "💳 Add Credits")
@handle_errors
def add_credits_btn(m):
    if not is_admin(m.from_user.id):
        return
    
    msg = bot.send_message(m.chat.id, "💳 Send user ID and credits to add (format: user_id credits):")
    bot.register_next_step_handler(m, process_add_credits)

@handle_errors
def process_add_credits(m):
    try:
        if not is_admin(m.from_user.id):
            return
        
        parts = m.text.strip().split()
        if len(parts) != 2:
            return bot.send_message(m.chat.id, "❌ Invalid format. Please use: user_id credits")
        
        try:
            uid = int(parts[0])
            credits = int(parts[1])
        except ValueError:
            return bot.send_message(m.chat.id, "❌ Invalid user ID or credits value.")
        
        if credits <= 0:
            return bot.send_message(m.chat.id, "❌ Credits must be a positive number.")
        
        init_user(uid)
        current_credits = get_credits(uid)
        new_credits = change_credits(uid, credits)
        
        bot.send_message(m.chat.id, f"✅ Successfully added {credits} credits to user {uid}.\nPrevious balance: {current_credits}\nNew balance: {new_credits}")
        
        # Notify user
        try:
            bot.send_message(uid, f"🎉 {credits} credits have been added to your account!\nYour current balance: {new_credits}")
        except Exception as e:
            logger.error(f"Could not notify user {uid}: {e}")
    except Exception as e:
        logger.error(f"Error in process_add_credits: {e}")
        bot.send_message(m.chat.id, f"⚠️ Error: <code>{str(e)}</code>", parse_mode="HTML")

# Remove Credits Handler
@bot.message_handler(func=lambda c: c.text == "💸 Remove Credits")
@handle_errors
def remove_credits_btn(m):
    if not is_admin(m.from_user.id):
        return
    
    msg = bot.send_message(m.chat.id, "💸 Send user ID and credits to remove (format: user_id credits):")
    bot.register_next_step_handler(m, process_remove_credits)

@handle_errors
def process_remove_credits(m):
    try:
        if not is_admin(m.from_user.id):
            return
        
        parts = m.text.strip().split()
        if len(parts) != 2:
            return bot.send_message(m.chat.id, "❌ Invalid format. Please use: user_id credits")
        
        try:
            uid = int(parts[0])
            credits = int(parts[1])
        except ValueError:
            return bot.send_message(m.chat.id, "❌ Invalid user ID or credits value.")
        
        if credits <= 0:
            return bot.send_message(m.chat.id, "❌ Credits must be a positive number.")
        
        init_user(uid)
        current_credits = get_credits(uid)
        new_credits = change_credits(uid, -credits)
        
        bot.send_message(m.chat.id, f"✅ Successfully removed {credits} credits from user {uid}.\nPrevious balance: {current_credits}\nNew balance: {new_credits}")
        
        # Notify user
        try:
            bot.send_message(uid, f"❌ {credits} credits have been removed from your account.\nYour current balance: {new_credits}")
        except Exception as e:
            logger.error(f"Could not notify user {uid}: {e}")
    except Exception as e:
        logger.error(f"Error in process_remove_credits: {e}")
        bot.send_message(m.chat.id, f"⚠️ Error: <code>{str(e)}</code>", parse_mode="HTML")

# All Users Handler
@bot.message_handler(func=lambda c: c.text == "👥 All Users")
@handle_errors
def all_users_btn(m):
    if not is_admin(m.from_user.id):
        return
    
    cur = db.get_cursor()
    cur.execute("SELECT user_id FROM users ORDER BY user_id")
    users = [row[0] for row in cur.fetchall()]
    
    if not users:
        return bot.send_message(m.chat.id, "❌ No users found.")
    
    total_users = len(users)
    special_count = len(SPECIAL_USERS)
    normal_count = total_users - special_count
    
    out = f"""
👥 <b>All Users</b>
━━━━━━━━━━━━━━━━━━
📊 <b>Total Users:</b> {total_users}
🌟 <b>Special Users:</b> {special_count}
👤 <b>Normal Users:</b> {normal_count}

📋 <b>User List:</b>
"""
    
    # Show first 50 users to avoid message too long
    for i, uid in enumerate(users[:50], 1):
        special = " 🌟" if is_special_user(uid) else ""
        credits = get_credits(uid)
        out += f"\n{i}. <code>{uid}</code> - {credits} credits{special}"
    
    if len(users) > 50:
        out += f"\n\n... and {len(users) - 50} more users."
    
    send_long(m.chat.id, out)

# User History Handler
@bot.message_handler(func=lambda c: c.text == "📋 User History")
@handle_errors
def user_history_btn(m):
    if not is_admin(m.from_user.id):
        return
    
    msg = bot.send_message(m.chat.id, "📋 Send user ID to view history:")
    bot.register_next_step_handler(m, process_user_history)

@handle_errors
def process_user_history(m):
    try:
        if not is_admin(m.from_user.id):
            return
        
        try:
            uid = int(m.text.strip())
        except ValueError:
            return bot.send_message(m.chat.id, "❌ Invalid user ID.")
        
        cur = db.get_cursor()
        cur.execute("SELECT query, api_type, ts FROM history WHERE user_id=? ORDER BY id DESC LIMIT 50", (uid,))
        rows = cur.fetchall()
        
        if not rows:
            return bot.send_message(m.chat.id, f"❌ No history found for user {uid}.")
        
        out = f"""
📋 <b>User History for {uid}</b>
━━━━━━━━━━━━━━━━━━
"""
        
        for q, t, ts in rows:
            out += f"\n[{ts}] ({t}) {q}"
        
        send_long(m.chat.id, out)
    except Exception as e:
        logger.error(f"Error in process_user_history: {e}")
        bot.send_message(m.chat.id, f"⚠️ Error: <code>{str(e)}</code>", parse_mode="HTML")

# Broadcast Handler
@bot.message_handler(func=lambda c: c.text == "📢 Broadcast")
@handle_errors
def broadcast_btn(m):
    if not is_admin(m.from_user.id):
        return
    
    msg = bot.send_message(m.chat.id, "📢 Send the message to broadcast to all users:")
    bot.register_next_step_handler(m, process_broadcast)

@handle_errors
def process_broadcast(m):
    try:
        if not is_admin(m.from_user.id):
            return
        
        broadcast_message = m.text.strip()
        if not broadcast_message:
            return bot.send_message(m.chat.id, "❌ Message cannot be empty.")
        
        cur = db.get_cursor()
        cur.execute("SELECT user_id FROM users")
        users = [row[0] for row in cur.fetchall()]
        
        if not users:
            return bot.send_message(m.chat.id, "❌ No users found.")
        
        success_count = 0
        failed_count = 0
        
        progress_msg = bot.send_message(m.chat.id, f"📢 Broadcasting message to {len(users)} users...")
        
        for uid in users:
            try:
                # Skip blocked users
                if is_user_blocked(uid):
                    failed_count += 1
                    continue
                
                bot.send_message(uid, f"📢 <b>Broadcast Message</b>\n\n{broadcast_message}", parse_mode="HTML")
                success_count += 1
                time.sleep(0.1)  # Small delay to avoid flood limits
            except Exception as e:
                logger.error(f"Failed to send broadcast to {uid}: {e}")
                failed_count += 1
        
        try:
            bot.delete_message(m.chat.id, progress_msg.message_id)
        except:
            pass
        
        result_msg = f"""
✅ <b>Broadcast Completed</b>
━━━━━━━━━━━━━━━━━━
📊 <b>Total Users:</b> {len(users)}
✅ <b>Successful:</b> {success_count}
❌ <b>Failed:</b> {failed_count}
"""
        bot.send_message(m.chat.id, result_msg, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in process_broadcast: {e}")
        bot.send_message(m.chat.id, f"⚠️ Error: <code>{str(e)}</code>", parse_mode="HTML")

# Special Users Handler
@bot.message_handler(func=lambda c: c.text == "🌟 Special Users")
@handle_errors
def special_users_btn(m):
    if not is_admin(m.from_user.id):
        return
    
    kb = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("➕ Add Special User", callback_data="add_special")
    btn2 = types.InlineKeyboardButton("➖ Remove Special User", callback_data="remove_special")
    kb.add(btn1, btn2)
    
    # Show current special users
    out = "🌟 <b>Special Users</b>\n━━━━━━━━━━━━━━━━━━\n"
    for user in SPECIAL_USERS:
        out += f"🆔 <code>{user['id']}</code> - {user['name']}\n"
    
    bot.send_message(m.chat.id, out, reply_markup=kb, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data in ["add_special", "remove_special"])
@handle_errors
def handle_special_user_callback(call):
    if not is_admin(call.from_user.id):
        return
    
    if call.data == "add_special":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "➕ Send user ID and name to add as special user (format: user_id name):")
        bot.register_next_step_handler(msg, process_add_special_user)
    elif call.data == "remove_special":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "➖ Send user ID to remove from special users:")
        bot.register_next_step_handler(msg, process_remove_special_user)

@handle_errors
def process_add_special_user(m):
    try:
        if not is_admin(m.from_user.id):
            return
        
        parts = m.text.strip().split(maxsplit=1)
        if len(parts) < 2:
            return bot.send_message(m.chat.id, "❌ Invalid format. Please use: user_id name")
        
        try:
            uid = int(parts[0])
            name = parts[1]
        except ValueError:
            return bot.send_message(m.chat.id, "❌ Invalid user ID.")
        
        # Check if already special
        if is_special_user(uid):
            return bot.send_message(m.chat.id, "❌ User is already a special user.")
        
        # Add to special users list
        SPECIAL_USERS.append({"id": uid, "name": name})
        
        # Set credits to 999
        init_user(uid)
        set_credits(uid, 999)
        
        bot.send_message(m.chat.id, f"✅ Successfully added {name} (ID: {uid}) as a special user.")
        
        # Notify user
        try:
            bot.send_message(uid, f"🌟 You have been added as a special user with unlimited credits!")
        except Exception as e:
            logger.error(f"Could not notify user {uid}: {e}")
    except Exception as e:
        logger.error(f"Error in process_add_special_user: {e}")
        bot.send_message(m.chat.id, f"⚠️ Error: <code>{str(e)}</code>", parse_mode="HTML")

@handle_errors
def process_remove_special_user(m):
    try:
        if not is_admin(m.from_user.id):
            return
        
        try:
            uid = int(m.text.strip())
        except ValueError:
            return bot.send_message(m.chat.id, "❌ Invalid user ID.")
        
        # Find and remove from special users list
        for i, user in enumerate(SPECIAL_USERS):
            if user["id"] == uid:
                SPECIAL_USERS.pop(i)
                
                # Reset credits to normal (5)
                init_user(uid)
                set_credits(uid, 5)
                
                bot.send_message(m.chat.id, f"✅ Successfully removed user {uid} from special users.")
                
                # Notify user
                try:
                    bot.send_message(uid, "❌ You have been removed from special users. Your credits have been reset to normal.")
                except Exception as e:
                    logger.error(f"Could not notify user {uid}: {e}")
                return
        
        bot.send_message(m.chat.id, "❌ User not found in special users list.")
    except Exception as e:
        logger.error(f"Error in process_remove_special_user: {e}")
        bot.send_message(m.chat.id, f"⚠️ Error: <code>{str(e)}</code>", parse_mode="HTML")

# Block/Unblock User Handlers
@bot.message_handler(func=lambda c: c.text=="🚫 Block User")
@handle_errors
def block_user_btn(m):
    if not is_admin(m.from_user.id): 
        return
    bot.send_message(m.chat.id,"🚫 Send user ID to block:")
    bot.register_next_step_handler(m,process_block_user)

@handle_errors
def process_block_user(m):
    try:
        uid=int(m.text.strip())
        
        cur = db.get_cursor()
        cur.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
        if not cur.fetchone():
            return bot.send_message(m.chat.id, "❌ User not found in database.")
        
        if is_user_blocked(uid):
            return bot.send_message(m.chat.id, "❌ User is already blocked.")
        
        msg = bot.send_message(m.chat.id, "🚫 Please provide a reason for blocking (optional):")
        bot.register_next_step_handler(msg, lambda msg: process_block_reason(msg, uid))
    except Exception as e:
        logger.error(f"Error in process_block_user: {e}")
        bot.send_message(m.chat.id, "❌ Invalid user ID.")

@handle_errors
def process_block_reason(m, uid):
    reason = m.text.strip()
    admin_id = m.from_user.id
    
    if block_user(uid, admin_id, reason):
        bot.send_message(m.chat.id, f"✅ User {uid} has been blocked successfully.\nReason: {reason}")
        
        try:
            bot.send_message(uid, f"⚠️ Your account has been blocked by admin.\nReason: {reason}\n\nContact admin for more information.")
        except Exception as e:
            logger.error(f"Could not notify blocked user {uid}: {e}")
    else:
        bot.send_message(m.chat.id, "❌ Failed to block user.")

@bot.message_handler(func=lambda c: c.text=="✅ Unblock User")
@handle_errors
def unblock_user_btn(m):
    if not is_admin(m.from_user.id): 
        return
    bot.send_message(m.chat.id,"✅ Send user ID to unblock:")
    bot.register_next_step_handler(m,process_unblock_user)

@handle_errors
def process_unblock_user(m):
    try:
        uid=int(m.text.strip())
        
        if not is_user_blocked(uid):
            return bot.send_message(m.chat.id, "❌ User is not blocked.")
        
        if unblock_user(uid):
            bot.send_message(m.chat.id, f"✅ User {uid} has been unblocked successfully.")
            
            try:
                bot.send_message(uid, "✅ Your account has been unblocked. You can now use the bot again.")
            except Exception as e:
                logger.error(f"Could not notify unblocked user {uid}: {e}")
        else:
            bot.send_message(m.chat.id, "❌ Failed to unblock user.")
    except Exception as e:
        logger.error(f"Error in process_unblock_user: {e}")
        bot.send_message(m.chat.id, "❌ Invalid user ID.")

@bot.message_handler(func=lambda c: c.text=="📋 Blocked Users")
@handle_errors
def blocked_users_btn(m):
    if not is_admin(m.from_user.id): 
        return
    
    blocked_users = get_blocked_users()
    if not blocked_users:
        return bot.send_message(m.chat.id, "✅ No blocked users found.")
    
    out = "📋 <b>Blocked Users List:</b>\n\n"
    for user in blocked_users:
        user_id = user[0]
        blocked_by = user[1]
        reason = user[2] if user[2] else "No reason provided"
        blocked_at = user[3]
        out += f"🆔 <b>User ID:</b> {user_id}\n"
        out += f"👤 <b>Blocked By:</b> {blocked_by}\n"
        out += f"📝 <b>Reason:</b> {reason}\n"
        out += f"📅 <b>Blocked At:</b> {blocked_at}\n"
        out += "━━━━━━━━━━━━━━━━━━\n"
    
    send_long(m.chat.id, out)

# Back to main menu handler
@bot.message_handler(func=lambda c: c.text == "🔙 Back to Main Menu")
@handle_errors
def back_to_main(m):
    cmd_start(m)

# ========== BUY CREDITS FEATURE ==========
@bot.message_handler(func=lambda c: c.text == "💳 Buy Credits")
@handle_errors
def buy_credits_btn(m):
    uid = m.from_user.id
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("💎 100 Credits - ₹200", callback_data="buy_100")
    btn2 = types.InlineKeyboardButton("💎 200 Credits - ₹300", callback_data="buy_200")
    btn3 = types.InlineKeyboardButton("💎 500 Credits - ₹500", callback_data="buy_500")
    btn4 = types.InlineKeyboardButton("🔄 Custom Amount", callback_data="buy_custom")
    
    kb.add(btn1, btn2, btn3, btn4)
    
    buy_text = f"""
💳 <b>Credit Packs & Pricing</b>
━━━━━━━━━━━━━━━━━━━━━━━

💎 <b>1 – 100 Credits</b> 
👉 ₹2 per Credit 
✔️ Example: 50 Credits = ₹100 

💎 <b>101 – 499 Credits</b> 
👉 ₹1.5 per Credit 
✔️ Example: 200 Credits = ₹300 

💎 <b>500+ Credits</b> 
👉 ₹1 per Credit 
✔️ Example: 500 Credits = ₹500 

━━━━━━━━━━━━━━━━━━━━━━━
📥 <b>Payment Method:</b> 
DM→ @DIPALI_654 

⚠️ After payment, send screenshot to admin for quick approval.

💳 <b>Your Current Credits:</b> {get_credits(uid)}
"""
    
    bot.send_message(m.chat.id, buy_text, reply_markup=kb, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
@handle_errors
def handle_buy_callback(call):
    uid = call.from_user.id
    
    if call.data == "buy_100":
        amount = "100 Credits for ₹200"
    elif call.data == "buy_200":
        amount = "200 Credits for ₹300"
    elif call.data == "buy_500":
        amount = "500 Credits for ₹500"
    elif call.data == "buy_custom":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "Please contact admin directly for custom credit amounts.")
        return
    
    payment_text = f"""
💳 <b>Payment Instructions</b>
━━━━━━━━━━━━━━━━━━━━━━━

You've selected: {amount}

📥 <b>Payment Method:</b> DM→ @DIPALI_654 

⚠️ <b>Steps:</b>
1. Send payment of the selected amount
2. Take a screenshot of the payment confirmation
3. Send the screenshot to admin with your user ID: <code>{uid}</code>
4. Admin will add credits to your account after verification

Thank you for your purchase!
"""
    
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, payment_text, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "buy_credits")
@handle_errors
def handle_buy_credits_callback(call):
    uid = call.from_user.id
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("💎 100 Credits - ₹200", callback_data="buy_100")
    btn2 = types.InlineKeyboardButton("💎 200 Credits - ₹300", callback_data="buy_200")
    btn3 = types.InlineKeyboardButton("💎 500 Credits - ₹500", callback_data="buy_500")
    btn4 = types.InlineKeyboardButton("🔄 Custom Amount", callback_data="buy_custom")
    
    kb.add(btn1, btn2, btn3, btn4)
    
    buy_text = f"""
💳 <b>Credit Packs & Pricing</b>
━━━━━━━━━━━━━━━━━━━━━━━

💎 <b>1 – 100 Credits</b> 
👉 ₹2 per Credit 
✔️ Example: 50 Credits = ₹100 

💎 <b>101 – 499 Credits</b> 
👉 ₹1.5 per Credit 
✔️ Example: 200 Credits = ₹300 

💎 <b>500+ Credits</b> 
👉 ₹1 per Credit 
✔️ Example: 500 Credits = ₹500 

━━━━━━━━━━━━━━━━━━━━━━━
📥 <b>Payment Method:</b> 
DM → @DIPALI_654 

⚠️ After payment, send screenshot to admin for quick approval.

💳 <b>Your Current Credits:</b> {get_credits(uid)}
"""
    
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, buy_text, reply_markup=kb, parse_mode="HTML")

# ========== MY HISTORY FEATURE ==========
@bot.message_handler(func=lambda c: c.text == "📜 My History")
@handle_errors
def my_history_btn(m):
    uid = m.from_user.id
    cur = db.get_cursor()
    cur.execute("SELECT query, api_type, ts FROM history WHERE user_id=? ORDER BY id DESC", (uid,))
    rows = cur.fetchall()
    
    if not rows:
        return bot.send_message(m.chat.id, "❌ No search history found.")
    
    out = "📜 <b>Your Complete Search History:</b>\n\n"
    for q, t, ts in rows:
        out += f"[{ts}] ({t}) {q}\n"
    
    send_long(m.chat.id, out)

# ========== BASIC BUTTON HANDLERS ==========
@bot.message_handler(func=lambda c: c.text == "🆔 My ID")
@handle_errors
def btn_myid(m):
    bot.send_message(m.chat.id, f"🆔 Your Telegram ID: <code>{m.from_user.id}</code>", parse_mode="HTML")

@bot.message_handler(func=lambda c: c.text == "💳 My Credits")
@handle_errors
def my_credits_btn(m):
    uid = m.from_user.id
    credits = get_credits(uid)
    
    if is_special_user(uid):
        bot.send_message(m.chat.id, f"💳 Your Credits: <b>{credits}</b>\n\n🌟 <i>You are a special user with unlimited searches!</i>", parse_mode="HTML")
    else:
        bot.send_message(m.chat.id, f"💳 Your Credits: <b>{credits}</b>", parse_mode="HTML")

@bot.message_handler(func=lambda c: c.text == "📞 Contact Admin")
@handle_errors
def contact_admin_btn(m):
    kb = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("📞 Contact Admin", url=f"tg://user?id={ADMIN_ID}")
    kb.add(btn)
    bot.send_message(m.chat.id, "Click below to contact admin 👇", reply_markup=kb)

@bot.message_handler(func=lambda c: c.text == "🎁 Get Daily Credits")
@handle_errors
def daily_credits_btn(m):
    uid = m.from_user.id
    init_user(uid)
    
    if is_special_user(uid):
        return bot.send_message(m.chat.id, "🌟 You are a special user with unlimited credits!")
    
    if check_and_give_daily_credits(uid):
        credits = get_credits(uid)
        bot.send_message(m.chat.id, f"✅ You have received 10 daily credits!\n💳 Your current balance: {credits}")
    else:
        last_date = get_last_credit_date(uid)
        bot.send_message(m.chat.id, f"❌ You have already received your daily credits today.\n📅 Last credited: {last_date}\n\nPlease try again tomorrow.")

# ========== TELEGRAM ID INFO ==========
@bot.message_handler(func=lambda c: c.text == "👤 Telegram ID Info")
@handle_errors
def ask_tgid(m):
    bot.send_message(m.chat.id, "📩 Send Telegram User ID (numeric):")
    bot.register_next_step_handler(m, handle_tgid)

@handle_errors
def handle_tgid(m):
    progress_msg = None
    try:
        if not m.text:
            bot.send_message(m.chat.id, "⚠️ Please send a numeric Telegram User ID.")
            return
        
        q = m.text.strip()
        if not re.fullmatch(r"\d+", q):
            bot.send_message(m.chat.id, "⚠️ Invalid Telegram ID. Please enter a numeric user ID.")
            return
        
        # TEMPORARY: Skip credit check for testing - REMOVE LATER
        # if not ensure_and_charge(m.from_user.id, m.chat.id):
        #     bot.send_message(m.chat.id, "❌ Insufficient credits. Please purchase more credits.")
        #     return
        
        progress_msg = bot.send_message(m.chat.id, "🔍 Fetching Telegram user information...")
        
        # API call
        data = make_request(f"ADD_YOUR_TELEGRAM_INFO_API")
        #Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99
        
        if progress_msg:
            bot.delete_message(m.chat.id, progress_msg.message_id)
        
        # Check API response
        if not data or not data.get("success"):
            error_msg = data.get("error", "Unknown error") if data else "No response"
            bot.send_message(m.chat.id, f"❌ API Error: {error_msg}")
            return
        
        d = data.get("data", {})
        if not d:
            bot.send_message(m.chat.id, "❌ No user data found for this ID.")
            return
        
        # Format response
        first_name = d.get('first_name', 'N/A')
        last_name = d.get('last_name', '')
        full_name = f"{first_name} {last_name}".strip() if last_name else first_name
        
        is_active = d.get('is_active', False)
        is_bot = d.get('is_bot', False)
        
        activity_emoji = "✅" if is_active else "❌"
        bot_emoji = "🤖" if is_bot else "👤"
        
        out = f"""
{bot_emoji} <b>Telegram User Information</b>
━━━━━━━━━━━━━━━━━━
🆔 <b>User ID:</b> <code>{d.get('id', 'N/A')}</code>
👤 <b>Full Name:</b> {full_name}
{bot_emoji} <b>Is Bot:</b> {is_bot}
{activity_emoji} <b>Active Status:</b> {is_active}

📅 <b>First Message:</b> {d.get('first_msg_date', 'Not available')}
📅 <b>Last Message:</b> {d.get('last_msg_date', 'Not available')}

💬 <b>Total Messages:</b> {d.get('total_msg_count', '0')}
👥 <b>Total Groups:</b> {d.get('total_groups', '0')}
👨‍💼 <b>Admin in Groups:</b> {d.get('adm_in_groups', '0')}
💬 <b>Messages in Groups:</b> {d.get('msg_in_groups_count', '0')}

🔄 <b>Name Changes:</b> {d.get('names_count', '0')}
@️ <b>Username Changes:</b> {d.get('usernames_count', '0')}
━━━━━━━━━━━━━━━━━━
"""
        bot.send_message(m.chat.id, out, parse_mode="HTML")
        
    except Exception as e:
        if progress_msg:
            try:
                bot.delete_message(m.chat.id, progress_msg.message_id)
            except Exception:
                pass
        logger.error(f"Error in handle_tgid: {str(e)}")
        bot.send_message(m.chat.id, "❌ An error occurred. Please try again.")
        
        
        
# ======= INDIA NUMBER HANDLER =======


@bot.message_handler(func=lambda message: message.text == "🇮🇳 India Number Info")
@handle_errors
def ask_india_number(message):
    bot.send_message(message.chat.id, "📱 Send 10-digit Indian mobile number:")
    bot.register_next_step_handler(message, handle_india_number_response)

@handle_errors
def handle_india_number_response(message):
    progress_msg = None
    try:
        if not message.text:
            bot.send_message(message.chat.id, "⚠️ Please send a 10-digit mobile number.")
            return
        
        num = message.text.strip()
        
        if not re.fullmatch(r"\d{10}", num):
            bot.send_message(message.chat.id, "⚠️ Invalid format. Please send exactly 10 digits.")
            return
        
        # TEMPORARY: Skip credit check for testing
        # if not ensure_and_charge(message.from_user.id, message.chat.id):
        #     bot.send_message(message.chat.id, "❌ Insufficient credits. Please purchase more credits.")
        #     return
        
        progress_msg = bot.send_message(message.chat.id, "🔍 Searching for information...")
        
        # API call
        #Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99
        
        r = requests.get(
            f"ADD_YOUR_NUMBER_INFO_API",
            timeout=30
        )
        
        # Delete progress message
        if progress_msg:
            try:
                bot.delete_message(message.chat.id, progress_msg.message_id)
            except:
                pass

        if r.status_code != 200:
            # refund_credit(message.from_user.id)  # Uncomment when credit system is active
            bot.send_message(message.chat.id, "❌ API request failed. Try again later.")
            return
        
        try:
            response_json = r.json()
        except ValueError:
            # refund_credit(message.from_user.id)  # Uncomment when credit system is active
            bot.send_message(message.chat.id, "❌ Invalid API response format.")
            return
        
        data_list = response_json.get("data", [])
        if not data_list or not isinstance(data_list, list):
            # refund_credit(message.from_user.id)  # Uncomment when credit system is active
            bot.send_message(message.chat.id, "📭 No information found for this number!")
            return

        # Send header
        header = f"""
📱 <b>Indian Number Lookup Results</b>
🔍 <b>Queried Number:</b> {num}
📊 <b>Total Records Found:</b> {len(data_list)}
━━━━━━━━━━━━━━━━━━
"""
        bot.send_message(message.chat.id, header, parse_mode="HTML")
        
        # Send each record
        for i, rec in enumerate(data_list, 1):
            try:
                name = clean(rec.get("name", "N/A"))
                father = clean(rec.get("fname", "N/A"))
                mobile = clean(rec.get("mobile", "N/A"))
                alt = clean(rec.get("alt", "N/A"))
                circle = clean(rec.get("circle", "N/A"))
                email = clean(rec.get("email", "N/A"))
                rec_id = clean(rec.get("id", "N/A"))

                # Clean address
                address_raw = rec.get("address", "")
                if address_raw:
                    address_parts = [part.strip() for part in address_raw.split("!") if part.strip()]
                    address = ", ".join(dict.fromkeys(address_parts))
                else:
                    address = "N/A"

                out = f"""
📋 <b>Record #{i}</b>
━━━━━━━━━━━━━━━━━━
👤 <b>Name:</b> {name}
👨‍👩‍👦 <b>Father/Guardian:</b> {father}
📱 <b>Primary Mobile:</b> {mobile}
📞 <b>Alternate Mobile:</b> {alt}
🌐 <b>Network Circle:</b> {circle}
🏠 <b>Address:</b> {address}
📧 <b>Email:</b> {email}
🆔 <b>ID:</b> {rec_id}
"""
                bot.send_message(message.chat.id, out, parse_mode="HTML")
                time.sleep(0.1)  # Avoid flood
                
            except Exception as e:
                logger.error(f"Error processing record #{i}: {e}")
                continue

        # Send footer
        footer = f"""
━━━━━━━━━━━━━━━━━━
✅ <b>Search completed successfully!</b>
💳 <b>Credits Used:</b> 1
📊 <b>Total Records:</b> {len(data_list)}
"""
        bot.send_message(message.chat.id, footer, parse_mode="HTML")
        add_history(message.from_user.id, num, "IND_NUMBER")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error: {e}")
        if progress_msg:
            try:
                bot.delete_message(message.chat.id, progress_msg.message_id)
            except:
                pass
        # refund_credit(message.from_user.id)  # Uncomment when credit system is active
        bot.send_message(message.chat.id, "❌ Network error. Please try again later.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if progress_msg:
            try:
                bot.delete_message(message.chat.id, progress_msg.message_id)
            except:
                pass
        # refund_credit(message.from_user.id)  # Uncomment when credit system is active
        bot.send_message(message.chat.id, "❌ An unexpected error occurred. Please try again.")


# ========== PAKISTAN NUMBER INFO ==========
@bot.message_handler(func=lambda c: c.text == "📱 Pakistan Number Info")
@handle_errors
def ask_pak_number(m):
    bot.send_message(m.chat.id, "📲 Send Pakistan number with country code (923XXXXXXXXX):")
    bot.register_next_step_handler(m, handle_pak_number)

@handle_errors
def handle_pak_number(m):
    try:
        num = m.text.strip()
        if not re.fullmatch(r"923\d{9}", num):
            return bot.send_message(m.chat.id, "⚠️ Invalid Pakistan number. Please enter in format: 923XXXXXXXXX")
        
        if not ensure_and_charge(m.from_user.id, m.chat.id):
            return
        
        progress_msg = bot.send_message(m.chat.id, "🔍 Searching for Pakistan number information...")
        
        data = make_request(f"ADD_YOUR_PAKISTAN_NUMBER_INFO_API")
                #Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99
        
        try:
            bot.delete_message(m.chat.id, progress_msg.message_id)
        except:
            pass
        
        if not data or "results" not in data or not data["results"]:
            refund_credit(m.from_user.id)
            return bot.send_message(m.chat.id, "❌ No data found for this Pakistan number.")
        
        results = data.get("results", [])
        results_count = len(results)
        
        header = f"""
📱 <b>Pakistan Number Lookup Results</b>
🔍 <b>Queried Number:</b> {num}
📊 <b>Total Records Found:</b> {results_count}
━━━━━━━━━━━━━━━━━━
"""
        bot.send_message(m.chat.id, header, parse_mode="HTML")
        
        for i, rec in enumerate(results, 1):
            name = clean(rec.get('Name'))
            mobile = clean(rec.get('Mobile'))
            cnic = clean(rec.get('CNIC'))
            address = clean(rec.get('Address'))
            
            out = f"""
📋 <b>Record #{i}</b>
👤 <b>Name:</b> {name}
📱 <b>Mobile:</b> {mobile}
🇵🇰 <b>CNIC:</b> {cnic}
🏠 <b>Address:</b> {address}
━━━━━━━━━━━━━━━━━━
"""
            bot.send_message(m.chat.id, out, parse_mode="HTML")
        
        footer = f"""
✅ <b>Search completed successfully!</b>
💳 <b>Credits Used:</b> 1
📊 <b>Total Records:</b> {results_count}
"""
        bot.send_message(m.chat.id, footer, parse_mode="HTML")
        
        add_history(m.from_user.id, num, "PAK_NUMBER")
    except Exception as e:
        refund_credit(m.from_user.id)
        logger.error(f"Error in handle_pak_number: {e}")
        bot.send_message(m.chat.id, f"⚠️ Error: <code>{str(e)}</code>", parse_mode="HTML")

# ========== PINCODE INFO ==========
@bot.message_handler(func=lambda c: c.text == "📮 Pincode Info")
@handle_errors
def ask_pincode(m):
    bot.send_message(m.chat.id, "📮 Send 6-digit Indian pincode:")
    bot.register_next_step_handler(m, handle_pincode)

@handle_errors
def handle_pincode(m):
    try:
        pincode = m.text.strip()
        if not re.fullmatch(r"\d{6}", pincode):
            return bot.send_message(m.chat.id, "⚠️ Invalid pincode. Please enter a 6-digit pincode.")
        
        if not ensure_and_charge(m.from_user.id, m.chat.id):
            return
        
        progress_msg = bot.send_message(m.chat.id, "🔍 Searching for pincode information...")
        
        data = make_request(f"ADD_YOUR_PIN_CODE_INFO_API")
                #Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99
        
        try:
            bot.delete_message(m.chat.id, progress_msg.message_id)
        except:
            pass
        
        if not data or not isinstance(data, list) or len(data) == 0:
            refund_credit(m.from_user.id)
            return bot.send_message(m.chat.id, "❌ No data found for this pincode.")
        
        pincode_data = data[0]
        if pincode_data.get("Status") != "Success" or "PostOffice" not in pincode_data:
            refund_credit(m.from_user.id)
            return bot.send_message(m.chat.id, "❌ No data found for this pincode.")
        
        post_offices = pincode_data.get("PostOffice", [])
        if not post_offices:
            refund_credit(m.from_user.id)
            return bot.send_message(m.chat.id, "❌ No post office data found for this pincode.")
        
        message = pincode_data.get("Message", "")
        header = f"""
📮 <b>Pincode Information</b>
🔍 <b>Pincode:</b> {pincode}
📊 <b>{message}</b>
━━━━━━━━━━━━━━━━━━
"""
        bot.send_message(m.chat.id, header, parse_mode="HTML")
        
        for i, office in enumerate(post_offices, 1):
            name = clean(office.get("Name"))
            branch_type = clean(office.get("BranchType"))
            delivery_status = clean(office.get("DeliveryStatus"))
            district = clean(office.get("District"))
            division = clean(office.get("Division"))
            region = clean(office.get("Region"))
            block = clean(office.get("Block"))
            state = clean(office.get("State"))
            country = clean(office.get("Country"))
            
            delivery_emoji = "✅" if delivery_status == "Delivery" else "❌"
            
            out = f"""
📋 <b>Post Office #{i}</b>
🏢 <b>Name:</b> {name}
🏛️ <b>Type:</b> {branch_type}
{delivery_emoji} <b>Delivery Status:</b> {delivery_status}
📍 <b>District:</b> {district}
🗂️ <b>Division:</b> {division}
🌐 <b>Region:</b> {region}
🏘️ <b>Block:</b> {block}
🏛️ <b>State:</b> {state}
🌍 <b>Country:</b> {country}
━━━━━━━━━━━━━━━━━━
"""
             # ========== PINCODE INFO CONTINUED ==========
            bot.send_message(m.chat.id, out, parse_mode="HTML")
        
        footer = f"""
--------------------------------
✅ <b>Search completed successfully!</b>
💳 <b>Credits Used:</b> 1
📊 <b>Total Post Offices:</b> {len(post_offices)}
"""
        bot.send_message(m.chat.id, footer, parse_mode="HTML")
        
        add_history(m.from_user.id, pincode, "PINCODE")
    except Exception as e:
        refund_credit(m.from_user.id)
        logger.error(f"Error in handle_pincode: {e}")
        bot.send_message(m.chat.id, f"⚠️ Error: <code>{str(e)}</code>", parse_mode="HTML")
        
# ========== VEHICLE INFO ==========
@bot.message_handler(func=lambda c: c.text == "🚘 Vehicle Info")
@handle_errors
def ask_vehicle(m):
    bot.send_message(m.chat.id, "🚘 Send vehicle registration number (e.g., DL1CA1234, MH12AB3456):")
    bot.register_next_step_handler(m, handle_vehicle)

@handle_errors
def handle_vehicle(m):
    try:
        rc_number = m.text.strip().upper()
        
        # Improved vehicle number validation for different formats
        if not re.match(r"^[A-Z]{2}\d{1,2}[A-Z]{1,3}\d{1,4}$", rc_number):
            return bot.send_message(m.chat.id, "⚠️ Invalid vehicle registration number.\n\nPlease enter in formats like:\n• DL1CA1234\n• MH12AB3456\n• KA01AB1234")
        
        if not ensure_and_charge(m.from_user.id, m.chat.id):
            return
        
        # FIRST: Show normal details from multiple APIs
        progress_msg = bot.send_message(m.chat.id, "🔍 Searching vehicle details from multiple sources...")
        
        # Multiple APIs for basic details
        #Vehicle APIS
        #Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99
        
        api1_data = make_request(f"")
        api2_data = make_request(f"")
        api3_data = make_request(f"")
        
        # Delete progress message
        try:
            bot.delete_message(m.chat.id, progress_msg.message_id)
        except:
            pass
        
        # PROCESS BASIC DETAILS FROM ANY AVAILABLE API
        basic_details_found = False
        
        # Try API 1 first
        if api1_data and api1_data.get("rc_number"):
            try:
                rc_num = clean(api1_data.get("rc_number", ""))
                owner_name = clean(api1_data.get("owner_name", ""))
                father_name = clean(api1_data.get("father_name", ""))
                model_name = clean(api1_data.get("model_name", ""))
                vehicle_class = clean(api1_data.get("vehicle_class", ""))
                fuel_type = clean(api1_data.get("fuel_type", ""))
                registration_date = clean(api1_data.get("registration_date", ""))
                rto = clean(api1_data.get("rto", ""))
                city = clean(api1_data.get("city", ""))
                phone = clean(api1_data.get("phone", ""))
                
                fuel_emoji = "⛽" if "PETROL" in fuel_type.upper() else "🛢️" if "DIESEL" in fuel_type.upper() else "⚡" if "ELECTRIC" in fuel_type.upper() else "🔧"
                
                # Normal details message
                normal_output = f"""
🚘 <b>Vehicle Basic Information</b>
--------------------------------
📝 <b>Registration Number:</b> <code>{rc_num}</code>
👤 <b>Owner Name:</b> {owner_name}
👨‍👩‍👦 <b>Father's Name:</b> {father_name}
🏛️ <b>RTO:</b> {rto}
📍 <b>City:</b> {city}
📞 <b>Phone:</b> {phone if phone else 'Not Available'}

🚗 <b>Vehicle Details:</b>
🏭 <b>Manufacturer:</b> {model_name}
🏷️ <b>Class:</b> {vehicle_class}
{fuel_emoji} <b>Fuel Type:</b> {fuel_type}
📅 <b>Registration Date:</b> {registration_date}
--------------------------------
"""
                bot.send_message(m.chat.id, normal_output, parse_mode="HTML")
                basic_details_found = True
                
            except Exception as e:
                logger.error(f"Error processing API1 data: {e}")
        
        # If API1 failed, try API2
        if not basic_details_found and api2_data:
            try:
                if isinstance(api2_data, dict):
                    owner_name = clean(api2_data.get("owner_name", ""))
                    vehicle_model = clean(api2_data.get("vehicle_model", ""))
                    registration_date = clean(api2_data.get("registration_date", ""))
                    fuel_type = clean(api2_data.get("fuel_type", ""))
                    rto = clean(api2_data.get("rto", ""))
                    
                    fuel_emoji = "⛽" if "PETROL" in fuel_type.upper() else "🛢️" if "DIESEL" in fuel_type.upper() else "⚡" if "ELECTRIC" in fuel_type.upper() else "🔧"
                    
                    normal_output = f"""
🚘 <b>Vehicle Basic Information</b>
--------------------------------
📝 <b>Registration Number:</b> <code>{rc_number}</code>
👤 <b>Owner Name:</b> {owner_name if owner_name else 'Not Available'}
🏛️ <b>RTO:</b> {rto if rto else 'Not Available'}

🚗 <b>Vehicle Details:</b>
🏭 <b>Model:</b> {vehicle_model if vehicle_model else 'Not Available'}
{fuel_emoji} <b>Fuel Type:</b> {fuel_type if fuel_type else 'Not Available'}
📅 <b>Registration Date:</b> {registration_date if registration_date else 'Not Available'}
--------------------------------
"""
                    bot.send_message(m.chat.id, normal_output, parse_mode="HTML")
                    basic_details_found = True
                    
            except Exception as e:
                logger.error(f"Error processing API2 data: {e}")
        
        # If still no details, try API3
        if not basic_details_found and api3_data:
            try:
                if isinstance(api3_data, dict):
                    # Extract whatever fields are available
                    output_lines = [f"🚘 <b>Vehicle Basic Information</b>", "--------------------------------"]
                    output_lines.append(f"📝 <b>Registration Number:</b> <code>{rc_number}</code>")
                    
                    for key, value in api3_data.items():
                        if value and key not in ['vehicle_number', 'rc_number']:
                            field_name = key.replace('_', ' ').title()
                            if 'owner' in key.lower():
                                output_lines.append(f"👤 <b>{field_name}:</b> {clean(value)}")
                            elif 'model' in key.lower():
                                output_lines.append(f"🏭 <b>{field_name}:</b> {clean(value)}")
                            elif 'fuel' in key.lower():
                                output_lines.append(f"⛽ <b>{field_name}:</b> {clean(value)}")
                            elif 'date' in key.lower():
                                output_lines.append(f"📅 <b>{field_name}:</b> {clean(value)}")
                            elif 'rto' in key.lower():
                                output_lines.append(f"🏛️ <b>{field_name}:</b> {clean(value)}")
                            else:
                                output_lines.append(f"📋 <b>{field_name}:</b> {clean(value)}")
                    
                    output_lines.append("--------------------------------")
                    normal_output = "\n".join(output_lines)
                    bot.send_message(m.chat.id, normal_output, parse_mode="HTML")
                    basic_details_found = True
                    
            except Exception as e:
                logger.error(f"Error processing API3 data: {e}")
        
        # If no basic details found from any API, show generic info
        if not basic_details_found:
            state_codes = {
                'DL': 'Delhi', 'MH': 'Maharashtra', 'KA': 'Karnataka', 'TN': 'Tamil Nadu',
                'AP': 'Andhra Pradesh', 'TS': 'Telangana', 'KL': 'Kerala', 'GJ': 'Gujarat',
                'RJ': 'Rajasthan', 'MP': 'Madhya Pradesh', 'UP': 'Uttar Pradesh', 'WB': 'West Bengal',
                'BR': 'Bihar', 'JH': 'Jharkhand', 'OD': 'Odisha', 'PB': 'Punjab',
                'HR': 'Haryana', 'UK': 'Uttarakhand', 'HP': 'Himachal Pradesh', 'AS': 'Assam'
            }
            
            state_code = rc_number[:2]
            state_name = state_codes.get(state_code, 'Unknown State')
            
            generic_output = f"""
🚘 <b>Vehicle Basic Information</b>
--------------------------------
📝 <b>Registration Number:</b> <code>{rc_number}</code>
🏛️ <b>State:</b> {state_name} ({state_code})
📍 <b>RTO Code:</b> {rc_number[2:4]}
🚗 <b>Series:</b> {rc_number[4:6]}
🔢 <b>Unique Number:</b> {rc_number[6:]}

💡 <i>Basic vehicle details are not available in the database</i>
--------------------------------
"""
            bot.send_message(m.chat.id, generic_output, parse_mode="HTML")
        
        # SECOND: Show mobile number from main API
        mobile_progress = bot.send_message(m.chat.id, "📱 Searching for mobile number...")
        
        # Main API for mobile number
        
        #Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99
        
        flipcart_data = make_request(f"ADD_YOUR_number_INFO_API")
        
        try:
            bot.delete_message(m.chat.id, mobile_progress.message_id)
        except:
            pass
        
        # Check if main API returned data
        if not flipcart_data:
            error_msg = f"""
📱 <b>Mobile Number Search</b>
--------------------------------
🚘 <b>Vehicle:</b> <code>{rc_number}</code>
❌ <b>Result:</b> Mobile number not found
💡 <i>Mobile number may not be linked to this vehicle registration</i>
--------------------------------
"""
            bot.send_message(m.chat.id, error_msg, parse_mode="HTML")
            add_history(m.from_user.id, rc_number, "VEHICLE")
            return
        
        # PROCESS MAIN API OUTPUT FOR MOBILE NUMBER
        try:
            mobile_number = None
            vehicle_number = rc_number
            
            if isinstance(flipcart_data, dict):
                # JSON response - extract mobile number
                mobile_number = flipcart_data.get("mobile_number")
                vehicle_number = flipcart_data.get("vehicle_number", rc_number)
            
            elif isinstance(flipcart_data, str):
                # HTML response parsing (fallback)
                mobile_match = re.search(r'Mobile Number[^:]*:\s*([^<\n]+)', flipcart_data, re.IGNORECASE)
                vehicle_match = re.search(r'Vehicle Number[^:]*:\s*([^<\n]+)', flipcart_data, re.IGNORECASE)
                
                if mobile_match:
                    mobile_number = clean(mobile_match.group(1))
                if vehicle_match:
                    vehicle_number = clean(vehicle_match.group(1))
            
            # Mobile number result
            if mobile_number:
                mobile_output = f"""
📱 <b>Mobile Number Found</b>
--------------------------------
🚘 <b>Vehicle:</b> <code>{vehicle_number}</code>
📱 <b>Mobile Number:</b> <code>{mobile_number}</code>
✅ <b>Status:</b> Successfully retrieved
--------------------------------
"""
            else:
                mobile_output = f"""
📱 <b>Mobile Number Search</b>
--------------------------------
🚘 <b>Vehicle:</b> <code>{vehicle_number}</code>
❌ <b>Result:</b> Mobile number not found
💡 <i>Mobile number may not be linked to this vehicle registration</i>
--------------------------------
"""
            
            bot.send_message(m.chat.id, mobile_output, parse_mode="HTML")
            
            # Final success message
            success_msg = f"✅ <b>Search Completed - Credits Used: 1</b>"
            bot.send_message(m.chat.id, success_msg, parse_mode="HTML")
            
            add_history(m.from_user.id, rc_number, "VEHICLE")
            
        except Exception as e:
            logger.error(f"Error processing main API data: {e}")
            error_msg = f"""
📱 <b>Mobile Number Search</b>
--------------------------------
🚘 <b>Vehicle:</b> <code>{rc_number}</code>
❌ <b>Error:</b> Failed to retrieve mobile number
⚠️ <i>Please try again later</i>
--------------------------------
"""
            bot.send_message(m.chat.id, error_msg, parse_mode="HTML")
        
    except Exception as e:
        refund_credit(m.from_user.id)
        logger.error(f"Error in handle_vehicle: {e}")
        bot.send_message(m.chat.id, f"⚠️ Error processing vehicle information. Please try again later.")
        
        
        
# ========== AADHAAR INFO ==========
@bot.message_handler(func=lambda c: c.text == "🆔 Aadhaar Info")
@handle_errors
def ask_aadhar(m):
    bot.send_message(m.chat.id, "🆔 Send 12-digit Aadhaar number: AND WAIT FOR 4-5 MINUTES BECAUSE ADHAR API IS SLOW 😥")
    bot.register_next_step_handler(m, handle_aadhar)

@handle_errors
def handle_aadhar(m):
    try:
        aid = m.text.strip()
        if not re.fullmatch(r"\d{12}", aid):
            return bot.send_message(m.chat.id, "⚠️ Invalid Aadhaar number. Please enter a 12-digit Aadhaar number.")
        
        if not ensure_and_charge(m.from_user.id, m.chat.id):
            return
        
        progress_msg = bot.send_message(m.chat.id, "🔍 Searching for Aadhaar information... (This may take 4-5 minutes)")
                #Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99
        
        try:
            r = requests.get(f"ADD_YOUR_ADDHAR_INFO_API", timeout=300)
            logger.info(f"Aadhaar API Response Status: {r.status_code}")
            
            try:
                bot.delete_message(m.chat.id, progress_msg.message_id)
            except:
                pass
            
            if r.status_code != 200:
                refund_credit(m.from_user.id)
                return bot.send_message(m.chat.id, "❌ API request failed. Please try again later.")
            
            try:
                # API से आया हुआ रॉ टेक्स्ट लें
                raw_response_text = r.text
                logger.info(f"Aadhaar API Raw Response: {raw_response_text[:500]}...") # लॉग में पहले 500 कैरेक्टर सेव करें
            except Exception as e:
                logger.error(f"Error reading response text: {e}")
                refund_credit(m.from_user.id)
                return bot.send_message(m.chat.id, "❌ Could not read API response.")

            # --- यहाँ मुख्य लॉजिक बदल गया है ---
            # हम अब JSON को पार्स नहीं करेंगे, बल्कि सीधे रॉ टेक्स्ट को भेजेंगे
            # लेकिन पहले चेक करेंगे कि रेस्पॉन्स खाली तो नहीं है
            if not raw_response_text or raw_response_text.strip() == "":
                refund_credit(m.from_user.id)
                return bot.send_message(m.chat.id, "📭 No Aadhaar Data Found!")
            
            # रेस्पॉन्स को एक सुंदर फॉर्मेट में भेजने के लिए प्रीपेयर करें
            header = f"""
🔍 <b>Raw API Response for Aadhaar:</b> {aid[:4]}XXXXXXXX{aid[-2:]}
--------------------------------
<code>
"""
            
            footer = f"""
</code>
--------------------------------
✅ <b>Search completed!</b>
💳 <b>Credits Used:</b> 1
"""
            
            # हेडर और फुटर के साथ पूरा मैसेज बनाएं
            full_message = header + raw_response_text + footer

            # अब `send_long` फंक्शन का इस्तेमाल करके लंबे मैसेज को छोटे हिस्सों में भेजें
            send_long(m.chat.id, full_message)
            
            add_history(m.from_user.id, aid, "AADHAAR_RAW")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            try:
                bot.delete_message(m.chat.id, progress_msg.message_id)
            except:
                pass
            refund_credit(m.from_user.id)
            bot.send_message(m.chat.id, "❌ Network error. Please try again later.")
        except Exception as e:
            logger.error(f"Unexpected error in handle_aadhar: {e}")
            try:
                bot.delete_message(m.chat.id, progress_msg.message_id)
            except:
                pass
            refund_credit(m.from_user.id)
            bot.send_message(m.chat.id, f"⚠️ Error: <code>{str(e)}</code>", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Outer error in handle_aadhar: {e}")
        refund_credit(m.from_user.id)
        bot.send_message(m.chat.id, f"⚠️ Error: <code>{str(e)}</code>", parse_mode="HTML")

# ========== ICMR INFO ==========
@bot.message_handler(func=lambda c: c.text == "🧪 ICMR Number Info")
@handle_errors
def ask_icmr(m):
    bot.send_message(m.chat.id, "🧪 Send 10-digit number for ICMR lookup:")
    bot.register_next_step_handler(m, handle_icmr)

@handle_errors
def handle_icmr(m):
    try:
        num = m.text.strip()
        if not re.fullmatch(r"\d{10}", num):
            return bot.send_message(m.chat.id, "⚠️ Invalid 10-digit number.")
        
        if not ensure_and_charge(m.from_user.id, m.chat.id):
            return
        
        progress_msg = bot.send_message(m.chat.id, "🔍 Searching for ICMR information...")
                #Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99
        
        data = make_request(f"ADD_YOUR_ICMR_INFO_API")
        
        try:
            bot.delete_message(m.chat.id, progress_msg.message_id)
        except:
            pass
        
        if not data or data.get("status") != "success" or not data.get("data"):
            refund_credit(m.from_user.id)
            return bot.send_message(m.chat.id, "📭 No ICMR Data Found!")
        
        records = data["data"]
        results_count = data.get("count", len(records))
        
        header = f"""
🧪 <b>ICMR Information Lookup Results</b>
🔍 <b>Phone Number:</b> {num}
📊 <b>Total Records Found:</b> {results_count}
--------------------------------
"""
        bot.send_message(m.chat.id, header, parse_mode="HTML")
        
        for i, rec in enumerate(records, 1):
            name = clean(rec.get("name"))
            fathers_name = clean(rec.get("fathersName"))
            phone_number = clean(rec.get("phoneNumber"))
            aadhar_number = clean(rec.get("aadharNumber"))
            age = clean(rec.get("age"))
            gender = clean(rec.get("gender"))
            address = clean(rec.get("address"))
            district = clean(rec.get("district"))
            pincode = clean(rec.get("pincode"))
            state = clean(rec.get("state"))
            town = clean(rec.get("town"))
            
            gender_emoji = "👩" if gender.lower() == "female" else "👨" if gender.lower() == "male" else "🧑"
            
            out = f"""
📋 <b>Record #{i}</b>
{gender_emoji} <b>Name:</b> {name}
👨‍👩‍👦 <b>Father's Name:</b> {fathers_name if fathers_name else "N/A"}
📱 <b>Phone Number:</b> {phone_number}
🆔 <b>Aadhaar Number:</b> {aadhar_number if aadhar_number else "N/A"}
🎂 <b>Age:</b> {age}
{gender_emoji} <b>Gender:</b> {gender}
🏠 <b>Address:</b> {address}
📍 <b>District:</b> {district}
🏙️ <b>Town:</b> {town if town else "N/A"}
📮 <b>Pincode:</b> {pincode if pincode else "N/A"}
🏛️ <b>State:</b> {state}
--------------------------------
"""
            bot.send_message(m.chat.id, out, parse_mode="HTML")
        
        footer = f"""
✅ <b>Search completed successfully!</b>
💳 <b>Credits Used:</b> 1
📊 <b>Total Records:</b> {results_count}
"""
        bot.send_message(m.chat.id, footer, parse_mode="HTML")
        
        add_history(m.from_user.id, num, "ICMR")
    except Exception as e:
        refund_credit(m.from_user.id)
        logger.error(f"Error in handle_icmr: {e}")
        bot.send_message(m.chat.id, f"⚠️ Error: <code>{str(e)}</code>", parse_mode="HTML")

# ========== IFSC CODE INFO ==========
@bot.message_handler(func=lambda c: c.text == "🏦 IFSC Code Info")
@handle_errors
def ask_ifsc(m):
    bot.send_message(m.chat.id, "🏦 Send 11-character IFSC code (e.g., SBIN0004843):")
    bot.register_next_step_handler(m, handle_ifsc)

@handle_errors
def handle_ifsc(m):
    try:
        ifsc_code = m.text.strip().upper()
        # IFSC कोड वैलिडेशन - 4 अक्षर, 7 अंक
        if not re.fullmatch(r"[A-Z]{4}\d{7}", ifsc_code):
            return bot.send_message(m.chat.id, "⚠️ Invalid IFSC code. Please enter a valid 11-character IFSC code (e.g., SBIN0004843).")
        
        # यूजर के क्रेडिट चेक करें और काटें
        if not ensure_and_charge(m.from_user.id, m.chat.id):
            return
        
        # प्रोग्रेस मैसेज भेजें
        progress_msg = bot.send_message(m.chat.id, "🔍 Searching for IFSC code information...")
        
        data = make_request(f"ADD_YOUR_IFSC_INFO_API")
        
        # प्रोग्रेस मैसेज हटाएं
        try:
            bot.delete_message(m.chat.id, progress_msg.message_id)
        except:
            pass
        
        if not data or not data.get("IFSC"):
            refund_credit(m.from_user.id)
            return bot.send_message(m.chat.id, "❌ No data found for this IFSC code.")
        
        # डेटा निकालें
        bank = clean(data.get("BANK"))
        ifsc = clean(data.get("IFSC"))
        branch = clean(data.get("BRANCH"))
        address = clean(data.get("ADDRESS"))
        city = clean(data.get("CITY"))
        district = clean(data.get("DISTRICT"))
        state = clean(data.get("STATE"))
        contact = clean(data.get("CONTACT"))
        micr = clean(data.get("MICR"))
        centre = clean(data.get("CENTRE"))
        bankcode = clean(data.get("BANKCODE"))
        iso3166 = clean(data.get("ISO3166"))
        
        # सेवाएं निकालें
        upi = data.get("UPI", False)
        rtgs = data.get("RTGS", False)
        neft = data.get("NEFT", False)
        imps = data.get("IMPS", False)
        swift = clean(data.get("SWIFT"))
        
        # सेवाओं के लिए इमोजी
        upi_emoji = "✅" if upi else "❌"
        rtgs_emoji = "✅" if rtgs else "❌"
        neft_emoji = "✅" if neft else "❌"
        imps_emoji = "✅" if imps else "❌"
        swift_emoji = "✅" if swift else "❌"
        
        # आउटपुट फॉर्मेट करें
        out = f"""
🏦 <b>Bank Information</b>
--------------------------------
🏛️ <b>Bank Name:</b> {bank}
🆔 <b>IFSC Code:</b> <code>{ifsc}</code>
🏢 <b>Branch:</b> {branch}
🏠 <b>Address:</b> {address}
📍 <b>City:</b> {city}
🗺️ <b>District:</b> {district}
🏛️ <b>State:</b> {state}
📞 <b>Contact:</b> {contact if contact else "N/A"}
🔢 <b>MICR Code:</b> {micr}
🏛️ <b>Centre:</b> {centre}
🆔 <b>Bank Code:</b> {bankcode}
🌍 <b>ISO Code:</b> {iso3166}

💸 <b>Available Services:</b>
{upi_emoji} <b>UPI:</b> {"Available" if upi else "Not Available"}
{rtgs_emoji} <b>RTGS:</b> {"Available" if rtgs else "Not Available"}
{neft_emoji} <b>NEFT:</b> {"Available" if neft else "Not Available"}
{imps_emoji} <b>IMPS:</b> {"Available" if imps else "Not Available"}
{swift_emoji} <b>SWIFT:</b> {swift if swift else "Not Available"}
--------------------------------
"""
        bot.send_message(m.chat.id, out, parse_mode="HTML")
        add_history(m.from_user.id, ifsc_code, "IFSC")
    except Exception as e:
        refund_credit(m.from_user.id)
        logger.error(f"Error in handle_ifsc: {e}")
        bot.send_message(m.chat.id, f"⚠️ Error: <code>{str(e)}</code>", parse_mode="HTML")

# ========== UPI ID INFO ==========
@bot.message_handler(func=lambda c: c.text == "💸 UPI ID Info")
@handle_errors
def ask_upi(m):
    bot.send_message(m.chat.id, "💸 Send UPI ID (e.g., mohd.kaifu@sbi ):")
    bot.register_next_step_handler(m, handle_upi)

@handle_errors
def handle_upi(m):
    try:
        upi_id = m.text.strip()
        # UPI ID वैलिडेशन - बेसिक फॉर्मेट चेक
        if not re.fullmatch(r"[a-zA-Z0-9._-]+@[a-zA-Z0-9]+", upi_id):
            return bot.send_message(m.chat.id, "⚠️ Invalid UPI ID format. Please enter a valid UPI ID (e.g., mohd.kaifu@sbi ).")
        
        # यूजर के क्रेडिट चेक करें और काटें
        if not ensure_and_charge(m.from_user.id, m.chat.id):
            return
        
        # प्रोग्रेस मैसेज भेजें
        progress_msg = bot.send_message(m.chat.id, "🔍 Searching for UPI ID information...")
                #Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99
        
        data = make_request(f"ADD_YOUR_UPI_INFO_API")
        
        # प्रोग्रेस मैसेज हटाएं
        try:
            bot.delete_message(m.chat.id, progress_msg.message_id)
        except:
            pass
        
        if not data or not data.get("vpa_details"):
            refund_credit(m.from_user.id)
            return bot.send_message(m.chat.id, "❌ No data found for this UPI ID.")
        
        # VPA डिटेल्स निकालें
        vpa_details = data.get("vpa_details", {})
        vpa = clean(vpa_details.get("vpa"))
        name = clean(vpa_details.get("name"))
        ifsc = clean(vpa_details.get("ifsc"))
        
        # बैंक डिटेल्स निकालें
        bank_details = data.get("bank_details_raw", {})
        bank = clean(bank_details.get("BANK"))
        branch = clean(bank_details.get("BRANCH"))
        address = clean(bank_details.get("ADDRESS"))
        city = clean(bank_details.get("CITY"))
        district = clean(bank_details.get("DISTRICT"))
        state = clean(bank_details.get("STATE"))
        contact = clean(bank_details.get("CONTACT"))
        micr = clean(bank_details.get("MICR"))
        centre = clean(bank_details.get("CENTRE"))
        bankcode = clean(bank_details.get("BANKCODE"))
        iso3166 = clean(bank_details.get("ISO3166"))
        
        # सेवाएं निकालें
        upi = bank_details.get("UPI", False)
        rtgs = bank_details.get("RTGS", False)
        neft = bank_details.get("NEFT", False)
        imps = bank_details.get("IMPS", False)
        swift = clean(bank_details.get("SWIFT"))
        
        # सेवाओं के लिए इमोजी
        upi_emoji = "✅" if upi else "❌"
        rtgs_emoji = "✅" if rtgs else "❌"
        neft_emoji = "✅" if neft else "❌"
        imps_emoji = "✅" if imps else "❌"
        swift_emoji = "✅" if swift else "❌"
        
        # आउटपुट फॉर्मेट करें
        out = f"""
💸 <b>UPI ID Information</b>
--------------------------------
💳 <b>UPI ID:</b> <code>{vpa}</code>
👤 <b>Account Holder:</b> {name}
🆔 <b>IFSC Code:</b> {ifsc}

🏦 <b>Bank Details:</b>
🏛️ <b>Bank Name:</b> {bank}
🏢 <b>Branch:</b> {branch}
🏠 <b>Address:</b> {address}
📍 <b>City:</b> {city}
🗺️ <b>District:</b> {district}
🏛️ <b>State:</b> {state}
📞 <b>Contact:</b> {contact if contact else "N/A"}
🔢 <b>MICR Code:</b> {micr}
🏛️ <b>Centre:</b> {centre}
🆔 <b>Bank Code:</b> {bankcode}
🌍 <b>ISO Code:</b> {iso3166}

💸 <b>Available Services:</b>
{upi_emoji} <b>UPI:</b> {"Available" if upi else "Not Available"}
{rtgs_emoji} <b>RTGS:</b> {"Available" if rtgs else "Not Available"}
{neft_emoji} <b>NEFT:</b> {"Available" if neft else "Not Available"}
{imps_emoji} <b>IMPS:</b> {"Available" if imps else "Not Available"}
{swift_emoji} <b>SWIFT:</b> {swift if swift else "Not Available"}
--------------------------------
"""
        bot.send_message(m.chat.id, out, parse_mode="HTML")
        add_history(m.from_user.id, upi_id, "UPI")
    except Exception as e:
        refund_credit(m.from_user.id)
        logger.error(f"Error in handle_upi: {e}")
        bot.send_message(m.chat.id, f"⚠️ Error: <code>{str(e)}</code>", parse_mode="HTML")

# ========== RATION CARD INFO ==========
@bot.message_handler(func=lambda c: c.text == "📋 Ration Card Info")
@handle_errors
def ask_ration(m):
    bot.send_message(m.chat.id, "📋 Send 12-digit Aadhaar number linked to ration card:")
    bot.register_next_step_handler(m, handle_ration)

@handle_errors
def handle_ration(m):
    try:
        aadhaar = m.text.strip()
        if not re.fullmatch(r"\d{12}", aadhaar):
            return bot.send_message(m.chat.id, "⚠️ Invalid Aadhaar number. Please enter a 12-digit Aadhaar number.")
        
        # Check and charge user credits
        if not ensure_and_charge(m.from_user.id, m.chat.id):
            return
        
        # Send progress message
        progress_msg = bot.send_message(m.chat.id, "🔍 Searching for ration card information...")
        
        # Fixed the variable name from 'aadhar' to 'aadhaar'
                #Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99
        
        data = make_request(f"ADD_YOUR_RATION_INFO_API")
        
        # Delete progress message
        try:
            bot.delete_message(m.chat.id, progress_msg.message_id)
        except:
            pass
        
        if not data or not data.get("rcId"):
            refund_credit(m.from_user.id)
            return bot.send_message(m.chat.id, "❌ No ration card data found for this Aadhaar number.")
        
        # Extract basic information
        rc_id = clean(data.get("rcId"))
        scheme_id = clean(data.get("schemeId"))
        scheme_name = clean(data.get("schemeName"))
        address = clean(data.get("address"))
        home_state_name = clean(data.get("homeStateName"))
        home_dist_name = clean(data.get("homeDistName"))
        allowed_onorc = clean(data.get("allowed_onorc"))
        dup_uid_status = clean(data.get("dup_uid_status"))
        fps_id = clean(data.get("fpsId"))
        
        # Scheme emoji mapping
        scheme_emoji = "🍚" if scheme_id == "PHH" else "🍛" if scheme_id == "AY" else "📋"
        
        # Output header
        header = f"""
📋 <b>Ration Card Information</b>
--------------------------------
🆔 <b>Ration Card ID:</b> {rc_id}
{scheme_emoji} <b>Scheme:</b> {scheme_name} ({scheme_id})
🏛️ <b>State:</b> {home_state_name}
📍 <b>District:</b> {home_dist_name}
🏠 <b>Address:</b> {address}
✅ <b>Allowed ONORC:</b> {allowed_onorc}
🔄 <b>Duplicate UID Status:</b> {dup_uid_status}
🏪 <b>FPS ID:</b> {fps_id}
--------------------------------
"""
        bot.send_message(m.chat.id, header, parse_mode="HTML")
        
        # Family members information
        member_details = data.get("memberDetailsList", [])
        if member_details:
            members_header = f"""
👨‍👩‍👧‍👦 <b>Family Members ({len(member_details)})</b>
--------------------------------
"""
            bot.send_message(m.chat.id, members_header, parse_mode="HTML")
            
            for i, member in enumerate(member_details, 1):
                member_id = clean(member.get("memberId"))
                member_name = clean(member.get("memberName"))
                relationship_code = clean(member.get("relationship_code"))
                relationship_name = clean(member.get("releationship_name"))
                uid_status = clean(member.get("uid"))
                
                # UID status emoji
                uid_emoji = "✅" if uid_status == "Yes" else "❌"
                
                # Relationship emoji mapping
                rel_emoji = "👤"
                if relationship_name == "SELF":
                    rel_emoji = "👤"
                elif "SON" in relationship_name.upper():
                    rel_emoji = "👦"
                elif "DAUGHTER" in relationship_name.upper():
                    rel_emoji = "👧"
                elif "FATHER" in relationship_name.upper():
                    rel_emoji = "👨"
                elif "MOTHER" in relationship_name.upper():
                    rel_emoji = "👩"
                elif "HUSBAND" in relationship_name.upper():
                    rel_emoji = "👨"
                elif "WIFE" in relationship_name.upper():
                    rel_emoji = "👩"
                
                member_out = f"""
📋 <b>Member #{i}</b>
{rel_emoji} <b>Name:</b> {member_name}
🔗 <b>Relationship:</b> {relationship_name}
{uid_emoji} <b>Aadhaar Linked:</b> {uid_status}
--------------------------------
"""
                bot.send_message(m.chat.id, member_out, parse_mode="HTML")
        
        # Footer message
        footer = f"""
✅ <b>Search completed successfully!</b>
💳 <b>Credits Used:</b> 1
👨‍👩‍👧‍👦 <b>Total Family Members:</b> {len(member_details)}
"""
        bot.send_message(m.chat.id, footer, parse_mode="HTML")
        
        add_history(m.from_user.id, aadhaar, "RATION_CARD")
        
    except Exception as e:
        refund_credit(m.from_user.id)
        logger.error(f"Error in handle_ration: {e}")
        bot.send_message(m.chat.id, f"⚠️ Error: <code>{str(e)}</code>", parse_mode="HTML")
       
       
#ff info 
@bot.message_handler(func=lambda c: c.text == "🎮 Free Fire Info")
@handle_errors
def ask_ff_info(m):
    bot.send_message(m.chat.id, "🎮 Send Free Fire UID to get player information:")
    bot.register_next_step_handler(m, handle_ff_info)

@handle_errors
def handle_ff_info(m):
    try:
        ff_uid = m.text.strip()
        if not re.fullmatch(r"\d{5,12}", ff_uid):
            return bot.send_message(m.chat.id, "⚠️ Invalid Free Fire UID. Please enter a valid numeric UID (5-12 digits).")
        
        # Check and charge user credits
        if not ensure_and_charge(m.from_user.id, m.chat.id):
            return
        
        # Send progress message
        progress_msg = bot.send_message(m.chat.id, "🔍 Searching for Free Fire player information...")
                #Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99
        
        try:
            # New Free Fire API call
            data = make_request(f"ADD_YOUR_FF_INFO_API")
            
            # Delete progress message
            try:
                bot.delete_message(m.chat.id, progress_msg.message_id)
            except:
                pass
            
            # Debug: Log the API response
            logger.info(f"FF API Response for UID {ff_uid}: {data}")
            
            # Check if API response is valid
            if not data:
                refund_credit(m.from_user.id)
                return bot.send_message(m.chat.id, "❌ API server is not responding. Please try again later.")
            
            # Check for error responses in the new API format
            if data.get("error"):
                refund_credit(m.from_user.id)
                error_msg = data.get("message", "Player not found")
                return bot.send_message(m.chat.id, f"❌ Error: {error_msg}")
            
            if data.get("status") == "error":
                refund_credit(m.from_user.id)
                error_msg = data.get("message", "Unknown error occurred")
                return bot.send_message(m.chat.id, f"❌ Error: {error_msg}")
            
            # Extract player data from the new API response structure
            player_data = data.get("data", {})
            if not player_data:
                player_data = data  # If data is directly in root
            
            # Check if we have basic player info
            if not player_data.get("uid") and not player_data.get("name"):
                refund_credit(m.from_user.id)
                return bot.send_message(m.chat.id, "❌ No player data found for this UID.")
            
            # Extract player information with safe defaults
            uid = clean(player_data.get("uid", ff_uid))
            name = clean(player_data.get("name", "N/A"))
            level = clean(player_data.get("level", player_data.get("accountLevel", "N/A")))
            
            # Experience/EXP
            exp = clean(player_data.get("exp", player_data.get("experience", "N/A")))
            
            # Guild/Clan information
            guild = clean(player_data.get("guild", player_data.get("clan", "No Guild")))
            
            # Server/Region
            server = clean(player_data.get("server", player_data.get("region", "N/A")))
            
            # Rank information
            rank = clean(player_data.get("rank", player_data.get("rank_title", "Unranked")))
            rank_points = clean(player_data.get("rank_points", player_data.get("rp", "0")))
            max_rank = clean(player_data.get("max_rank", player_data.get("best_rank", "Unranked")))
            
            # Stats extraction - handle different possible field names
            stats = player_data.get("stats", {})
            if not stats:
                stats = player_data
            
            total_matches = clean(stats.get("total_matches", stats.get("matches", "0")))
            wins = clean(stats.get("wins", stats.get("total_wins", "0")))
            win_rate = clean(stats.get("win_rate", stats.get("win_percentage", "0")))
            kills = clean(stats.get("kills", stats.get("total_kills", "0")))
            kd_ratio = clean(stats.get("kd_ratio", stats.get("kd", "0")))
            headshots = clean(stats.get("headshots", stats.get("headshot_kills", "0")))
            headshot_rate = clean(stats.get("headshot_rate", stats.get("headshot_percentage", "0")))
            damage = clean(stats.get("damage", stats.get("total_damage", "0")))
            
            # Additional stats that might be available
            assists = clean(stats.get("assists", "0"))
            survivals = clean(stats.get("survivals", "0"))
            top_10 = clean(stats.get("top_10", "0"))
            
            # Format percentages
            win_rate_display = f"{win_rate}%" if "%" not in str(win_rate) else win_rate
            headshot_rate_display = f"{headshot_rate}%" if "%" not in str(headshot_rate) else headshot_rate
            
            # Output header
            header = f"""
🎮 <b>Free Fire Player Information</b>
--------------------------------
🆔 <b>UID:</b> {uid}
👤 <b>Name:</b> {name}
⭐ <b>Level:</b> {level}
📊 <b>EXP:</b> {exp}
{"🏅 <b>Guild:</b> " + guild if guild != "No Guild" else "🚫 <b>Guild:</b> No Guild"}
🌐 <b>Server:</b> {server}
--------------------------------
"""
            bot.send_message(m.chat.id, header, parse_mode="HTML")
            
            # Rank information
            rank_info = f"""
🏆 <b>Rank Information</b>
--------------------------------
📈 <b>Current Rank:</b> {rank}
🎯 <b>Rank Points:</b> {rank_points}
🚀 <b>Max Rank:</b> {max_rank}
--------------------------------
"""
            bot.send_message(m.chat.id, rank_info, parse_mode="HTML")
            
            # Main stats information
            stats_info = f"""
📊 <b>Player Statistics</b>
--------------------------------
🎯 <b>Total Matches:</b> {total_matches}
🏆 <b>Wins:</b> {wins}
📈 <b>Win Rate:</b> {win_rate_display}
⚔️ <b>Kills:</b> {kills}
🎯 <b>K/D Ratio:</b> {kd_ratio}
🎪 <b>Headshots:</b> {headshots}
📊 <b>Headshot Rate:</b> {headshot_rate_display}
💥 <b>Damage:</b> {damage}
"""
            # Add additional stats if available
            if assists != "0":
                stats_info += f"🤝 <b>Assists:</b> {assists}\n"
            if survivals != "0":
                stats_info += f"🛡️ <b>Survivals:</b> {survivals}\n"
            if top_10 != "0":
                stats_info += f"🎖️ <b>Top 10:</b> {top_10}\n"
            
            stats_info += "--------------------------------"
            bot.send_message(m.chat.id, stats_info, parse_mode="HTML")
            
            # Footer message
            footer = f"""
✅ <b>Free Fire Info search completed successfully!</b>
💳 <b>Credits Used:</b> 1
🎮 <b>Player:</b> {name}
"""
            bot.send_message(m.chat.id, footer, parse_mode="HTML")
            
            add_history(m.from_user.id, ff_uid, "FREE_FIRE_INFO")
            
        except Exception as api_error:
            refund_credit(m.from_user.id)
            logger.error(f"API Error in handle_ff_info: {api_error}")
            bot.send_message(m.chat.id, "❌ API service temporarily unavailable. Please try again later.")
            
    except Exception as e:
        refund_credit(m.from_user.id)
        logger.error(f"General Error in handle_ff_info: {e}")
        bot.send_message(m.chat.id, f"⚠️ System Error: <code>{str(e)}</code>", parse_mode="HTML")

# Fallback function with multiple API endpoints
def get_ff_info_fallback(uid):
    """Fallback API endpoints in case main API fails"""
            #Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99
        
    #add Your FF INFO APIs
    fallback_apis = [
        f"",
        f"",
        f"",
    ]
    
    for api_url in fallback_apis:
        try:
            data = make_request(api_url)
            if data and (data.get("data") or data.get("name")):
                return data
        except Exception as e:
            logger.error(f"Fallback API failed {api_url}: {e}")
            continue
    return None

# ========== FREE FIRE VIEWS ==========
import datetime

# Create views tracking table
def init_views_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS profile_views 
                 (user_id INTEGER, date TEXT, count INTEGER, PRIMARY KEY (user_id, date))''')
    conn.commit()
    conn.close()

init_views_db()

def check_views_limit(user_id):
    """Check if user has exceeded daily profile views limit (5 per day)"""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute("SELECT count FROM profile_views WHERE user_id = ? AND date = ?", (user_id, today))
    result = c.fetchone()
    
    if result:
        if result[0] >= 5:  # Limit reached
            conn.close()
            return False
        else:
            c.execute("UPDATE profile_views SET count = count + 1 WHERE user_id = ? AND date = ?", (user_id, today))
    else:
        c.execute("INSERT INTO profile_views (user_id, date, count) VALUES (?, ?, 1)", (user_id, today))
    
    conn.commit()
    conn.close()
    return True

def get_remaining_views(user_id):
    """Get remaining profile views for today"""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute("SELECT count FROM profile_views WHERE user_id = ? AND date = ?", (user_id, today))
    result = c.fetchone()
    
    conn.close()
    if result:
        return 5 - result[0]
    return 5

def refund_view(user_id):
    """Refund a view count if credit check fails"""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute("SELECT count FROM profile_views WHERE user_id = ? AND date = ?", (user_id, today))
    result = c.fetchone()
    
    if result and result[0] > 0:
        c.execute("UPDATE profile_views SET count = count - 1 WHERE user_id = ? AND date = ?", (user_id, today))
    
    conn.commit()
    conn.close()

@bot.message_handler(func=lambda c: c.text == "👀 Free Fire Views")
@handle_errors
def ask_ff_views(m):
    # Check remaining views first
    remaining = get_remaining_views(m.from_user.id)
    if remaining <= 0:
        return bot.send_message(m.chat.id, "❌ Daily limit reached! You can only use Free Fire Views 5 times per day. Please try again tomorrow.")
    
    bot.send_message(m.chat.id, f"👀 Send Free Fire UID to increase profile views:\n\n📊 Remaining uses today: {remaining}/5")
    bot.register_next_step_handler(m, handle_ff_views)

@handle_errors
def handle_ff_views(m):
    try:
        ff_uid = m.text.strip()
        if not re.fullmatch(r"\d{5,12}", ff_uid):
            return bot.send_message(m.chat.id, "⚠️ Invalid Free Fire UID. Please enter a valid numeric UID (5-12 digits).")
        
        # Check views limit
        if not check_views_limit(m.from_user.id):
            return bot.send_message(m.chat.id, "❌ Daily limit reached! You can only use Free Fire Views 5 times per day. Please try again tomorrow.")
        
        # Check and charge user credits
        if not ensure_and_charge(m.from_user.id, m.chat.id):
            # Refund view count if credit check fails
            refund_view(m.from_user.id)
            return
        
        # Send progress message
        progress_msg = bot.send_message(m.chat.id, "🚀 Increasing Free Fire profile views...")
                #Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99
        
        try:
            # Profile Views API call
            api_url = f"ADD_YOUR_FF_VISIT_INFO_API"
            data = make_request(api_url)
            
            # Delete progress message
            try:
                bot.delete_message(m.chat.id, progress_msg.message_id)
            except:
                pass
            
            # Debug: Log the API response
            logger.info(f"Views API Response for UID {ff_uid}: {data}")
            
            # Check if API response is valid
            if not data:
                refund_credit(m.from_user.id)
                refund_view(m.from_user.id)
                return bot.send_message(m.chat.id, "❌ Views service is not responding. Please try again later.")
            
            # Check for success response
            if data.get("success") or data.get("status") == "success" or data.get("views_added"):
                # Get remaining views
                remaining = get_remaining_views(m.from_user.id)
                
                # Success message
                success_msg = f"""
✅ <b>Profile Views Increased Successfully!</b>
--------------------------------
🎮 <b>UID:</b> {ff_uid}
👀 <b>Status:</b> Views Added
💳 <b>Credits Used:</b> 1
📊 <b>Remaining uses today:</b> {remaining}/5
--------------------------------
💡 <i>Views may take few minutes to reflect in game</i>
"""
                bot.send_message(m.chat.id, success_msg, parse_mode="HTML")
                add_history(m.from_user.id, ff_uid, "FREE_FIRE_VIEWS")
                
            else:
                # Handle error responses
                refund_credit(m.from_user.id)
                refund_view(m.from_user.id)
                
                error_msg = data.get("message", "Failed to add views")
                if "limit" in error_msg.lower():
                    error_msg = "Daily views limit reached for this UID"
                elif "invalid" in error_msg.lower():
                    error_msg = "Invalid UID or player not found"
                
                bot.send_message(m.chat.id, f"❌ {error_msg}")
            
        except Exception as api_error:
            refund_credit(m.from_user.id)
            refund_view(m.from_user.id)
            logger.error(f"Views API Error: {api_error}")
            bot.send_message(m.chat.id, "❌ Views service is currently unavailable. Please try again later.")
            
    except Exception as e:
        refund_credit(m.from_user.id)
        refund_view(m.from_user.id)
        logger.error(f"General Error in handle_ff_views: {e}")
        bot.send_message(m.chat.id, "❌ An error occurred while processing your request. Please try again.")

# ========== WEB SERVER FOR RENDER ==========
app = Flask('app')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# ========== START BOT ==========
if __name__ == "__main__":
    # Start web server for Render
    keep_alive()
    
    # Start bot polling
    logger.info("Starting bot polling...")
    bot.polling(none_stop=True)
    
#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99#Secure & Premium Digital Services: Codes, APIs, Scripts, Custom Bots — @patelkrish_99