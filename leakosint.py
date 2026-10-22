# Api And Bot Developer By :- @GauravxcyberApi 
import sqlite3
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from telegram.error import Forbidden, BadRequest
import hashlib
import logging
import re
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ==== CONFIG ====
BOT_TOKEN = "8494530349:AAF0-WLoOqIIh70mMumX43QZ4WyN3i6Mz0"
API_KEY = "6684734209:x0DzYO39"
API_URL = "https://leakosintapi.com/"

# Channels that users MUST join to use the bot
CHANNELS = [
    {"id": -1003717621110, "url": "https://t.me/+pYj6aI14OvpmYTM1", "name": "📢 MAIN CHANNEL"},
    {"id": -1003717621110, "url": "https://t.me/+5z5I7vpb43IwNDk1", "name": "⭐ VIP CHANNEL"}
]

# Store search results for pagination
user_searches = {}

# Create session with retry strategy
def create_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

# ==== DB Setup - Track users but no limits ====
try:
    conn = sqlite3.connect("bot.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    search_count INTEGER DEFAULT 0,
                    joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""")
    conn.commit()
except Exception as e:
    logger.error(f"DB setup error: {e}")

# ==== Helper Functions ====
async def safe_send(update: Update, text: str, reply_markup=None):
    try:
        if update.message:
            await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)
        return True
    except Exception as e:
        logger.error(f"Send error: {e}")
        return False

def add_user(user_id: int, username: str):
    try:
        c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        user = c.fetchone()
        if not user:
            c.execute("INSERT INTO users (user_id, username, search_count) VALUES (?, ?, ?)",
                      (user_id, username, 0))
            conn.commit()
            return True
        return False
    except Exception as e:
        logger.error(f"DB error: {e}")
        return False

def increment_search_count(user_id: int):
    try:
        c.execute("UPDATE users SET search_count = search_count + 1 WHERE user_id = ?", (user_id,))
        conn.commit()
    except Exception as e:
        logger.error(f"Update count error: {e}")

def get_search_count(user_id: int):
    try:
        c.execute("SELECT search_count FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        return result[0] if result else 0
    except Exception as e:
        logger.error(f"Get count error: {e}")
        return 0

# ==== Check if user joined all channels (MANDATORY) ====
async def check_channel_membership(user_id, context):
    """Check if user has joined all required channels"""
    not_joined = []
    for channel in CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=channel["id"], user_id=user_id)
            if member.status in ["left", "kicked"]:
                not_joined.append(channel)
        except Exception as e:
            logger.error(f"Channel check error for {channel['name']}: {e}")
            # If can't check, assume not joined
            not_joined.append(channel)
    return not_joined

# ==== Create join channel keyboard ====
def join_channel_keyboard(not_joined_channels):
    """Create keyboard with channels to join"""
    keyboard = []
    for channel in not_joined_channels:
        keyboard.append([InlineKeyboardButton(f"✅ JOIN {channel['name']}", url=channel["url"])])
    keyboard.append([InlineKeyboardButton("🔄 CHECK AGAIN", callback_data="check_membership")])
    return InlineKeyboardMarkup(keyboard)

# ==== MAIN MENU - Only for users who joined channels ====
def main_menu_keyboard():
    """Main menu keyboard (only shown after joining channels)"""
    main_buttons = [
        [
            InlineKeyboardButton("📞 PHONE SEARCH", callback_data="search_phone"),
            InlineKeyboardButton("📧 EMAIL SEARCH", callback_data="search_email")
        ],
        [
            InlineKeyboardButton("📊 MY STATS", callback_data="stats"),
            InlineKeyboardButton("👑 OWNER", callback_data="owner")
        ],
        [
            InlineKeyboardButton("❓ HELP", callback_data="help"),
            InlineKeyboardButton("⚖️ LEGAL", callback_data="legal")
        ],
        [
            InlineKeyboardButton("🔄 REFRESH MENU", callback_data="mainmenu")
        ]
    ]
    
    return InlineKeyboardMarkup(main_buttons)

# ==== Search Result Action Menu ====
def action_menu_keyboard(query_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📋 COPY TEXT", callback_data=f"act|copy|{query_id}"),
            InlineKeyboardButton("📤 SHARE", callback_data=f"act|share|{query_id}")
        ],
        [
            InlineKeyboardButton("🔄 NEW SEARCH", callback_data=f"act|new|{query_id}"),
            InlineKeyboardButton("🔙 BACK TO RESULTS", callback_data=f"act|back|{query_id}")
        ],
        [
            InlineKeyboardButton("🏠 MAIN MENU", callback_data="mainmenu")
        ]
    ])

# ==== Navigation Keyboard ====
def navigation_keyboard(page=1, total_pages=1, query_id=""):
    keyboard = []
    
    # Page navigation row
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("◀ PREV", callback_data=f"nav|p|{page-1}|{query_id}"))
    
    nav_buttons.append(InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="noop"))
    
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("NEXT ▶", callback_data=f"nav|n|{page+1}|{query_id}"))
    
    keyboard.append(nav_buttons)
    
    # Action buttons row
    keyboard.append([
        InlineKeyboardButton("⚙️ ACTIONS", callback_data=f"act|menu|{query_id}"),
        InlineKeyboardButton("🔍 NEW SEARCH", callback_data=f"act|new|{query_id}")
    ])
    
    # Home button row
    keyboard.append([
        InlineKeyboardButton("🏠 MAIN MENU", callback_data="mainmenu")
    ])
    
    return InlineKeyboardMarkup(keyboard)

# ==== Generate short ID for query ====
def get_query_id(query, user_id):
    query_string = f"{user_id}_{query}"
    return hashlib.md5(query_string.encode()).hexdigest()[:8]

# ==== START Command with Channel Check ====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name
        
        # Check if user joined all channels
        not_joined = await check_channel_membership(user_id, context)
        
        if not_joined:
            # User hasn't joined all channels - show join buttons
            welcome_text = f"""
⚠️ *ACCESS DENIED* ⚠️

🚫 *Hello {username}!*

To use this bot, you MUST join our channels first:

📢 *Required Channels:* {len(CHANNELS)}
"""
            
            for channel in not_joined:
                welcome_text += f"\n🔹 {channel['name']}"
            
            welcome_text += f"""

━━━━━━━━━━━━━━━━━━━━━
✅ *After joining all channels*
👉 Click *CHECK AGAIN* button below
━━━━━━━━━━━━━━━━━━━━━

⚡ *Unlimited searches after joining!*
"""
            
            await update.message.reply_text(
                welcome_text,
                parse_mode="Markdown",
                reply_markup=join_channel_keyboard(not_joined)
            )
            return
        
        # User joined all channels - add to database and show main menu
        add_user(user_id, username)
        
        welcome_text = f"""
🚀 *WELCOME TO UNLIMITED SEARCH BOT* 🚀

✨ *Hello {username}!* ✨
🎁 *UNLIMITED SEARCHES* for everyone!

✅ *Channels Joined Successfully!*

🔍 *Search Any:*
• 📞 Indian Mobile Numbers
• 📧 Email Addresses

💪 *No Limits | No Restrictions | Free Forever*

📊 *Total Users:* `{get_total_users()}`

━━━━━━━━━━━━━━━━━━━━━
🎯 *Start searching now!*
━━━━━━━━━━━━━━━━━━━━━
"""
        
        await safe_send(update, welcome_text, reply_markup=main_menu_keyboard())
    
    except Exception as e:
        logger.error(f"Start error: {e}")
        await safe_send(update, "⚠️ An error occurred. Please try again.")

# ==== Check Membership Callback Handler ====
async def check_membership_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle check membership button click"""
    try:
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        username = query.from_user.username or query.from_user.first_name
        
        # Check membership again
        not_joined = await check_channel_membership(user_id, context)
        
        if not_joined:
            # Still not joined all channels
            text = f"""
❌ *VERIFICATION FAILED* ❌

You still need to join {len(not_joined)} channel(s):

"""
            for channel in not_joined:
                text += f"\n🔹 {channel['name']}"
            
            text += """

━━━━━━━━━━━━━━━━━━━━━
✅ *Please join the channels above*
👉 Then click *CHECK AGAIN*
━━━━━━━━━━━━━━━━━━━━━
"""
            
            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=join_channel_keyboard(not_joined)
            )
        else:
            # Successfully joined all channels
            add_user(user_id, username)
            
            text = f"""
✅ *VERIFICATION SUCCESSFUL* ✅

🎉 *Congratulations {username}!*

You have joined all required channels!

━━━━━━━━━━━━━━━━━━━━━
🚀 *Now you can use the bot!*
━━━━━━━━━━━━━━━━━━━━━

🔍 *Send any:*
• 📞 Indian mobile number
• 📧 Email address

⚡ *UNLIMITED SEARCHES!*
"""
            
            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=main_menu_keyboard()
            )
    
    except Exception as e:
        logger.error(f"Check membership error: {e}")
        await query.message.reply_text("⚠️ Error checking membership. Please try again.")

# ==== Get Total Users ====
def get_total_users():
    try:
        c.execute("SELECT COUNT(*) FROM users")
        return c.fetchone()[0]
    except:
        return 0

# ==== Database descriptions with fixed order ====
DATABASE_INFO = {
    "hiteck": {
        "header": "💾 HiTeckGroop.in",
        "desc": "At the beginning of 2025, a huge leak with the data of Indian cellular operators began to spread on the network. The HITECKGROOP website is declared as a source, but this information is unverified. The data contains 1.8 billion records, however, the number of unique users below, about 300 million. Each record indicated the full name, the name of the father, and the number of the document. Most often this is the Aadhaar number, but the taxpayer's passports or numbers were also found. There were up to two phones in each line, however, since several records had several records for one user, the total number of well -known phones sometimes reached several tens. Some records also had nicknames and emails.",
        "order": 1
    },
    "truecaller": {
        "header": "🇮🇳 TrueCaller India",
        "desc": "In February 2019, \"The best application for identifying the provocative subscriber and spam blocking\" TrueCaller was leaked to data from which 286 million Indian users suffered. Phones, telephone operators, full names, gender, location, positions of companies, mail, websites, Facebook identifiers and Twitter users' names were disclosed.",
        "order": 2
    },
    "makaan": {
        "header": "📱 Makaan.com",
        "desc": "This is an Indian online portal of real estate. In March 2015, a leak, which touched more than 2 million people, was destroyed on it. Mails, phones and names of the portal users were published.",
        "order": 3
    },
    "gaadi": {
        "header": "🚗 Gaadi",
        "desc": "In May 2015, a leak occurred on the Indian automobile website Gaadi. 4.3 million records were found in it. The data contained users' names, email addresses, IP addresses, gender, city and passwords stored both in the form of a regular text and in the form of hash MD5.",
        "order": 4
    },
    "zivame": {
        "header": "👙 Zivame.com",
        "desc": "Zivame is an Indian site engaged in the sale of bras. In May 2023, the database of 1.5 million of its users began to be sold on the Internet at a price of $ 500. Data contain phones, names, mail and addresses. Most of the users are women.",
        "order": 5
    },
    "yatra": {
        "header": "🛏 Yatra",
        "desc": "In September 2013, the Indian booking website Yatra suffered from a leak that affected 5 million users. The data contained email addresses, physical addresses, date of birth, phone numbers, PIN codes and passwords in the form of simple text.",
        "order": 6
    },
    "benetton": {
        "header": "🟢 In.Benetton.com",
        "desc": "There is no information about this database in my records. Try to look for it on the Internet.",
        "order": 7
    }
}

# ==== Format entry with all fields ====
def format_entry(entry):
    """Format a single entry with all fields"""
    text = ""
    
    # Email
    if entry.get("Email"):
        text += f"📩 *Email:* `{entry['Email']}`\n"
    
    # Telephone (saare phones)
    phone_fields = ["Phone", "Phone1", "Phone2", "Phone3", "Phone4", "Phone5", "Phone6", "Phone7", "Phone8", "Phone9", "Telephone", "Mobile"]
    seen_phones = set()
    for field in phone_fields:
        if entry.get(field) and str(entry[field]) not in seen_phones:
            text += f"📞 *Phone:* `{entry[field]}`\n"
            seen_phones.add(str(entry[field]))
    
    # Address
    address_fields = ["Address", "Adres", "Address1", "Address2", "Address3"]
    for field in address_fields:
        if entry.get(field):
            text += f"🏘️ *Address:* `{entry[field]}`\n"
    
    # Document number
    if entry.get("DocNumber") or entry.get("Document number"):
        text += f"🃏 *Document:* `{entry.get('DocNumber') or entry.get('Document number')}`\n"
    
    # Full name
    if entry.get("FullName") or entry.get("Full name") or entry.get("Name"):
        text += f"👤 *Name:* `{entry.get('FullName') or entry.get('Full name') or entry.get('Name')}`\n"
    
    # Father name
    if entry.get("FatherName") or entry.get("The name of the father"):
        text += f"👨 *Father's Name:* `{entry.get('FatherName') or entry.get('The name of the father')}`\n"
    
    # Region
    if entry.get("Region"):
        text += f"🗺️ *Region:* `{entry['Region']}`\n"
    
    # Password
    if entry.get("Password"):
        text += f"🔑 *Password:* `{entry['Password']}`\n"
    
    # Date
    if entry.get("Date") or entry.get("RegistrationDate"):
        text += f"📆 *Date:* `{entry.get('Date') or entry.get('RegistrationDate')}`\n"
    
    # City
    if entry.get("City"):
        text += f"🌃 *City:* `{entry['City']}`\n"
    
    # IP
    if entry.get("IP"):
        text += f"🎯 *IP:* `{entry['IP']}`\n"
    
    # Nick
    if entry.get("Nick"):
        text += f"👤 *Nick:* `{entry['Nick']}`\n"
    
    # Indian state
    if entry.get("State") or entry.get("Indian state"):
        text += f"🇮🇳 *State:* `{entry.get('State') or entry.get('Indian state')}`\n"
    
    # Mobile operator
    if entry.get("Operator") or entry.get("MobileOperator") or entry.get("Mobile operator"):
        text += f"📡 *Operator:* `{entry.get('Operator') or entry.get('MobileOperator') or entry.get('Mobile operator')}`\n"
    
    # Postal code
    if entry.get("PostalCode") or entry.get("Postal code"):
        text += f"🏤 *Postal Code:* `{entry.get('PostalCode') or entry.get('Postal code')}`\n"
    
    # Prefix
    if entry.get("Prefix") or entry.get("Title"):
        text += f"☄ *Prefix:* `{entry.get('Prefix') or entry.get('Title')}`\n"
    
    # Surname
    if entry.get("Surname") or entry.get("LastName") or entry.get("Last Name"):
        text += f"👤 *Surname:* `{entry.get('Surname') or entry.get('LastName') or entry.get('Last Name')}`\n"
    
    # Type
    if entry.get("Type"):
        text += f"🔖 *Type:* `{entry['Type']}`\n"
    
    # Stat (Zivame specific)
    if entry.get("Stat") or entry.get("🇺🇸Stat"):
        text += f"🇺🇸 *Stat:* `{entry.get('Stat') or entry.get('🇺🇸Stat')}`\n"
    
    text += "─" * 30 + "\n"
    return text

# ==== Identify database type ====
def get_db_type(source_lower):
    if "hiteck" in source_lower or "indian" in source_lower or "cellular" in source_lower:
        return "hiteck"
    elif "truecaller" in source_lower:
        return "truecaller"
    elif "makaan" in source_lower or "real estate" in source_lower:
        return "makaan"
    elif "gaadi" in source_lower or "automobile" in source_lower:
        return "gaadi"
    elif "zivame" in source_lower:
        return "zivame"
    elif "yatra" in source_lower or "booking" in source_lower:
        return "yatra"
    elif "benetton" in source_lower:
        return "benetton"
    return None

# ==== Format Results with fixed order ====
def format_results(data, query):
    """Saare databases ka saara data fixed order mein dikhao"""
    
    # Dictionary to store data by database type
    db_data = {
        "hiteck": [],
        "truecaller": [],
        "makaan": [],
        "gaadi": [],
        "zivame": [],
        "yatra": [],
        "benetton": []
    }
    
    # Unknown databases ke liye
    unknown_dbs = {}
    
    if "List" not in data:
        return "No data found"
    
    # Process each source and organize by database type
    for source, source_data in data["List"].items():
        source_lower = source.lower()
        db_type = get_db_type(source_lower)
        
        if db_type:
            # Add all entries from this source
            for entry in source_data.get("Data", []):
                db_data[db_type].append(entry)
        else:
            # Unknown database
            if source not in unknown_dbs:
                unknown_dbs[source] = []
            for entry in source_data.get("Data", []):
                unknown_dbs[source].append(entry)
    
    result = ""
    
    # 1. HiTeckGroop.in
    if db_data["hiteck"]:
        result += f"📁 *{DATABASE_INFO['hiteck']['header']}*\n"
        result += f"📝 {DATABASE_INFO['hiteck']['desc']}\n\n"
        result += "─" * 40 + "\n\n"
        for entry in db_data["hiteck"]:
            result += format_entry(entry)
    
    # 2. TrueCaller India
    if db_data["truecaller"]:
        result += f"📁 *{DATABASE_INFO['truecaller']['header']}*\n"
        result += f"📝 {DATABASE_INFO['truecaller']['desc']}\n\n"
        result += "─" * 40 + "\n\n"
        for entry in db_data["truecaller"]:
            result += format_entry(entry)
    
    # 3. Makaan.com
    if db_data["makaan"]:
        result += f"📁 *{DATABASE_INFO['makaan']['header']}*\n"
        result += f"📝 {DATABASE_INFO['makaan']['desc']}\n\n"
        result += "─" * 40 + "\n\n"
        for entry in db_data["makaan"]:
            result += format_entry(entry)
    
    # 4. Gaadi
    if db_data["gaadi"]:
        result += f"📁 *{DATABASE_INFO['gaadi']['header']}*\n"
        result += f"📝 {DATABASE_INFO['gaadi']['desc']}\n\n"
        result += "─" * 40 + "\n\n"
        for entry in db_data["gaadi"]:
            result += format_entry(entry)
    
    # 5. Zivame.com
    if db_data["zivame"]:
        result += f"📁 *{DATABASE_INFO['zivame']['header']}*\n"
        result += f"📝 {DATABASE_INFO['zivame']['desc']}\n\n"
        result += "─" * 40 + "\n\n"
        for entry in db_data["zivame"]:
            result += format_entry(entry)
    
    # 6. Yatra
    if db_data["yatra"]:
        result += f"📁 *{DATABASE_INFO['yatra']['header']}*\n"
        result += f"📝 {DATABASE_INFO['yatra']['desc']}\n\n"
        result += "─" * 40 + "\n\n"
        for entry in db_data["yatra"]:
            result += format_entry(entry)
    
    # 7. Benetton
    if db_data["benetton"]:
        result += f"📁 *{DATABASE_INFO['benetton']['header']}*\n"
        result += f"📝 {DATABASE_INFO['benetton']['desc']}\n\n"
        result += "─" * 40 + "\n\n"
        for entry in db_data["benetton"]:
            result += format_entry(entry)
    
    # Unknown databases (if any)
    for source, entries in unknown_dbs.items():
        if entries:
            result += f"📁 *{source}*\n\n"
            for entry in entries:
                result += format_entry(entry)
    
    return result

# ==== API call with retry and better error handling ====
def call_api(query):
    """Make API call with retry logic and better error handling"""
    session = create_session()
    payload = {"token": API_KEY, "request": query, "limit": 100, "lang": "en"}
    
    for attempt in range(3):  # 3 attempts
        try:
            logger.info(f"API attempt {attempt + 1} for query: {query}")
            
            response = session.post(
                API_URL, 
                json=payload, 
                timeout=30,
                headers={'Connection': 'close'}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API returned status {response.status_code}")
                if attempt < 2:
                    time.sleep(2)
                    
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error (attempt {attempt + 1}): {e}")
            if attempt < 2:
                time.sleep(3)
                
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout error (attempt {attempt + 1}): {e}")
            if attempt < 2:
                time.sleep(2)
                
        except Exception as e:
            logger.error(f"Unexpected API error (attempt {attempt + 1}): {e}")
            if attempt < 2:
                time.sleep(2)
    
    return None

# ==== Validate Email ====
def is_valid_email(email):
    """Validate email format"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

# ==== Validate Phone Number ====
def validate_phone_number(phone):
    """Validate and format Indian phone number"""
    clean_number = re.sub(r'\D', '', phone)
    
    if clean_number.startswith('91') and len(clean_number) >= 10:
        return clean_number
    elif len(clean_number) == 10 and not clean_number.startswith('91'):
        return '91' + clean_number
    return None

# ==== Message Handler with Channel Check ====
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        message_text = update.message.text.strip()
        
        # Check if user has joined channels
        not_joined = await check_channel_membership(user_id, context)
        
        if not_joined:
            # User hasn't joined all channels - block access
            await update.message.reply_text(
                f"⚠️ *ACCESS DENIED* ⚠️\n\n"
                f"You must join our channels to use this bot!\n\n"
                f"📢 *Required Channels:* {len(CHANNELS)}\n\n"
                f"Please use /start to see the channels and join them.",
                parse_mode="Markdown"
            )
            return
        
        # User has joined all channels - proceed with search
        username = update.effective_user.username or update.effective_user.first_name
        add_user(user_id, username)
        increment_search_count(user_id)
        
        # Check if it's an email
        if is_valid_email(message_text):
            await search_by_email(update, message_text, user_id)
        else:
            # Try to process as phone number
            query = validate_phone_number(message_text)
            if query:
                await search_by_phone(update, query, user_id)
            else:
                await safe_send(update, "❌ *Invalid Input*\n\nPlease send a valid:\n📞 Indian mobile number\n📧 Email address\n\n*Examples:*\n`9876543210`\n`example@gmail.com`")
                
    except Exception as e:
        logger.error(f"Message handler error: {e}")
        await safe_send(update, f"⚠️ *Error*\n\nAn unexpected error occurred.\nPlease try again later.")

# ==== Search by Phone Number ====
async def search_by_phone(update: Update, query: str, user_id: int):
    """Handle phone number search"""
    search_count = get_search_count(user_id)
    await safe_send(update, f"🔍 *Searching*\n\n📞 Number: `{query}`\n📊 Total searches: `{search_count}`\n⏳ Please wait...")

    # Call API with retry logic
    data = call_api(query)

    # Check if API call failed
    if data is None:
        await safe_send(update, "⚠️ *Connection Error*\n\nPlease try again in a few moments.\nThe API server might be busy.")
        return

    # Check results
    if "List" not in data or not data["List"]:
        await safe_send(update, f"❌ *No Results*\n\nNo data found for number: `{query}`")
        return

    # Format results with fixed order
    result_text = format_results(data, query)
    
    # Generate query ID
    query_id = get_query_id(query, user_id)
    
    # Store in user_searches
    if user_id not in user_searches:
        user_searches[user_id] = {}
    
    # Split into pages if needed
    if len(result_text) > 3500:
        pages = []
        current_page = ""
        lines = result_text.split('\n')
        
        for line in lines:
            if len(current_page + line + '\n') > 3500:
                pages.append(current_page)
                current_page = line + '\n'
            else:
                current_page += line + '\n'
        
        if current_page:
            pages.append(current_page)
        
        search_data = {"total_pages": len(pages), "type": "phone"}
        for i, page in enumerate(pages, 1):
            search_data[f"page_{i}"] = page
        
        user_searches[user_id][query] = search_data
        
        await safe_send(
            update, 
            pages[0],
            reply_markup=navigation_keyboard(1, len(pages), query_id)
        )
    else:
        search_data = {"total_pages": 1, "page_1": result_text, "type": "phone"}
        user_searches[user_id][query] = search_data
        
        await safe_send(
            update, 
            result_text,
            reply_markup=navigation_keyboard(1, 1, query_id)
        )

# ==== Search by Email ====
async def search_by_email(update: Update, email: str, user_id: int):
    """Handle email search"""
    search_count = get_search_count(user_id)
    await safe_send(update, f"🔍 *Searching*\n\n📧 Email: `{email}`\n📊 Total searches: `{search_count}`\n⏳ Please wait...")

    # Call API with retry logic
    data = call_api(email)

    # Check if API call failed
    if data is None:
        await safe_send(update, "⚠️ *Connection Error*\n\nPlease try again in a few moments.\nThe API server might be busy.")
        return

    # Check results
    if "List" not in data or not data["List"]:
        await safe_send(update, f"❌ *No Results*\n\nNo data found for email: `{email}`")
        return

    # Format results with fixed order
    result_text = format_results(data, email)
    
    # Generate query ID
    query_id = get_query_id(email, user_id)
    
    # Store in user_searches
    if user_id not in user_searches:
        user_searches[user_id] = {}
    
    # Split into pages if needed
    if len(result_text) > 3500:
        pages = []
        current_page = ""
        lines = result_text.split('\n')
        
        for line in lines:
            if len(current_page + line + '\n') > 3500:
                pages.append(current_page)
                current_page = line + '\n'
            else:
                current_page += line + '\n'
        
        if current_page:
            pages.append(current_page)
        
        search_data = {"total_pages": len(pages), "type": "email"}
        for i, page in enumerate(pages, 1):
            search_data[f"page_{i}"] = page
        
        user_searches[user_id][email] = search_data
        
        await safe_send(
            update, 
            pages[0],
            reply_markup=navigation_keyboard(1, len(pages), query_id)
        )
    else:
        search_data = {"total_pages": 1, "page_1": result_text, "type": "email"}
        user_searches[user_id][email] = search_data
        
        await safe_send(
            update, 
            result_text,
            reply_markup=navigation_keyboard(1, 1, query_id)
        )

# ==== Callback Query Handler ====
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        # Handle membership check first
        if data == "check_membership":
            await check_membership_handler(update, context)
            return

        # For other actions, check membership first
        not_joined = await check_channel_membership(user_id, context)
        if not_joined:
            await query.edit_message_text(
                f"⚠️ *ACCESS DENIED* ⚠️\n\n"
                f"You must join our channels to use this bot!\n\n"
                f"Please use /start to join the required channels.",
                parse_mode="Markdown"
            )
            return

        if data == "owner":
            keyboard = [[InlineKeyboardButton("🏠 MAIN MENU", callback_data="mainmenu")]]
            await query.edit_message_text(
                "👑 *BOT OWNER*\n\n"
                "👤 *Developer:* [@GauravxCyber](https://t.me/GauravxCyber)\n\n"
                "🤖 *Bot Features:*\n"
                "✅ *Unlimited Searches*\n"
                "✅ *Phone & Email Search*\n"
                "✅ *7+ Indian Databases*\n"
                "✅ *24/7 Available*\n\n"
                "💡 *Support:* Contact @GauravxCyber for assistance",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        elif data == "stats":
            search_count = get_search_count(user_id)
            total_users = get_total_users()
            
            keyboard = [[InlineKeyboardButton("🏠 MAIN MENU", callback_data="mainmenu")]]
            await query.edit_message_text(
                f"📊 *YOUR STATISTICS*\n\n"
                f"🔍 *Total Searches:* `{search_count}`\n"
                f"👥 *Total Users:* `{total_users}`\n"
                f"🚀 *Status:* `Unlimited Access`\n\n"
                f"🎁 *Keep searching! No limits!*",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        elif data == "help":
            keyboard = [[InlineKeyboardButton("🏠 MAIN MENU", callback_data="mainmenu")]]
            await query.edit_message_text(
                "📖 *HELP MENU*\n\n"
                "*How to Use:*\n"
                "1️⃣ Send any Indian mobile number\n"
                "2️⃣ Or send any email address\n"
                "3️⃣ Get instant search results\n\n"
                "*Examples:*\n"
                "📞 `9876543210`\n"
                "📧 `example@gmail.com`\n\n"
                "*Commands:*\n"
                "🔹 `/start` - Start the bot\n"
                "🔹 Send number/email - Search\n\n"
                "⚡ *UNLIMITED SEARCHES!*",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        elif data == "legal":
            keyboard = [[InlineKeyboardButton("🏠 MAIN MENU", callback_data="mainmenu")]]
            await query.edit_message_text(
                "⚖️ *LEGAL DISCLAIMER*\n\n"
                "This bot is created *for educational and research purposes only*.\n\n"
                "⚠️ *Important:*\n"
                "❌ Illegal use is strictly prohibited\n"
                "✅ You are solely responsible for your actions\n"
                "📌 Data from publicly available sources\n\n"
                "🔒 *Use responsibly!*",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        elif data == "search_phone":
            keyboard = [[InlineKeyboardButton("🏠 MAIN MENU", callback_data="mainmenu")]]
            await query.edit_message_text(
                "🔍 *PHONE SEARCH*\n\n"
                "*How to Search:*\n"
                "Send any Indian mobile number in these formats:\n\n"
                "*Examples:*\n"
                "✅ `9876543210`\n\n"
                "*Features:*\n"
                "⚡ Instant results\n"
                "📊 Multiple databases\n"
                "🎁 Unlimited searches\n\n"
                "*Send a number now!*",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif data == "search_email":
            keyboard = [[InlineKeyboardButton("🏠 MAIN MENU", callback_data="mainmenu")]]
            await query.edit_message_text(
                "📧 *EMAIL SEARCH*\n\n"
                "*How to Search:*\n"
                "Send any email address:\n\n"
                "*Examples:*\n"
                "✅ `example@gmail.com`\n\n"
                "*Features:*\n"
                "⚡ Instant results\n"
                "📊 Multiple databases\n"
                "🎁 Unlimited searches\n\n"
                "*Send an email now!*",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        elif data == "mainmenu":
            await query.edit_message_text(
                "🏠 *MAIN MENU*\n\n"
                "👋 *Hello! Choose an option below:*\n\n"
                "🔍 *Search Phone Numbers*\n"
                "📧 *Search Email Addresses*\n"
                "📊 *Check Your Stats*\n\n"
                "⚡ *UNLIMITED SEARCHES!*",
                parse_mode="Markdown",
                reply_markup=main_menu_keyboard()
            )
        
        elif data == "noop":
            pass
        
        elif data.startswith("nav|"):
            parts = data.split("|")
            if len(parts) == 4:
                page = int(parts[2])
                query_id = parts[3]
                
                found = False
                for uid, searches in user_searches.items():
                    if uid == user_id:
                        for q, search_data in searches.items():
                            if get_query_id(q, user_id) == query_id:
                                total_pages = search_data.get("total_pages", 1)
                                page_content = search_data.get(f"page_{page}", "No content")
                                
                                await query.edit_message_text(
                                    page_content,
                                    parse_mode="Markdown",
                                    reply_markup=navigation_keyboard(page, total_pages, query_id)
                                )
                                found = True
                                break
                        if found:
                            break
        
        elif data.startswith("act|"):
            parts = data.split("|")
            if len(parts) >= 3:
                action = parts[1]
                query_id = parts[2] if len(parts) > 2 else ""
                
                if action == "menu":
                    # Show action menu
                    await query.edit_message_text(
                        "⚙️ *ACTION MENU*\n\nChoose an action:",
                        parse_mode="Markdown",
                        reply_markup=action_menu_keyboard(query_id)
                    )
                
                elif action == "copy":
                    await query.answer("📋 Copy feature coming soon!", show_alert=True)
                
                elif action == "share":
                    await query.answer("📤 Share feature coming soon!", show_alert=True)
                
                elif action == "new":
                    await query.message.edit_text(
                        "🔍 *NEW SEARCH*\n\n"
                        "Send a new Indian number or email address:\n\n"
                        "*Examples:*\n"
                        "📞 `9876543210`\n"
                        "📧 `example@gmail.com`",
                        parse_mode="Markdown"
                    )
                
                elif action == "back":
                    # Go back to results
                    found = False
                    for uid, searches in user_searches.items():
                        if uid == user_id:
                            for q, search_data in searches.items():
                                if get_query_id(q, user_id) == query_id:
                                    total_pages = search_data.get("total_pages", 1)
                                    page_content = search_data.get("page_1", "No content")
                                    
                                    await query.message.edit_text(
                                        page_content,
                                        parse_mode="Markdown",
                                        reply_markup=navigation_keyboard(1, total_pages, query_id)
                                    )
                                    found = True
                                    break
                            if found:
                                break
    
    except Exception as e:
        logger.error(f"Button error: {e}")
        try:
            await query.message.reply_text("⚠️ *Error*\n\nAn error occurred. Please try again.", parse_mode="Markdown")
        except:
            pass

# ==== MAIN ====
def main():
    try:
        app = Application.builder().token(BOT_TOKEN).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.add_handler(CallbackQueryHandler(button_handler))
        
        print("="*50)
        print("✅ BOT STARTED SUCCESSFULLY!")
        print("🔒 MANDATORY CHANNEL JOIN REQUIRED!")
        print("📢 Users MUST join all channels to use the bot")
        print("📱 Users can send after joining:")
        print("   📞 Indian numbers: 9876543210")
        print("   📧 Email addresses: example@gmail.com")
        print("\n🎁 FEATURES:")
        print("   ✅ UNLIMITED searches for all users")
        print("   ✅ Mandatory channel join verification")
        print("   ✅ Auto-check membership on every action")
        print("   ✅ Search count tracking")
        print("   ✅ Phone & Email both supported")
        print("   ✅ 7+ Indian databases")
        print("   ✅ Auto-retry on network errors")
        print("="*50)
        print("\nPress Ctrl+C to stop")
        
        app.run_polling()
    
    except Exception as e:
        logger.error(f"Main error: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()