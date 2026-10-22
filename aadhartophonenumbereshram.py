import os
import logging
import base64
import json
import hashlib
import requests
from io import BytesIO

from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5, AES
from Crypto.Util.Padding import unpad

# ===================== CONFIG =====================
TOKEN = ""  # <-- BotFather se lo

NDUW_BASE_URL = "https://registerapi.eshram.gov.in/sms-service/api/v1/nduw"
CAPTCHA_BASE_URL = "https://registerapi.eshram.gov.in/sms-service/api/v1"

SUBSCRIPTION_KEY = "6bcd8aac3822462a8574f3009c220e2a"
APP_ORIGIN = "MQC0LP"

LOGIN_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCCXsPahbbC+6pDcLO5XP7kiTKEBPX0eqH0EsdnOAwX8873EuzOnnDYJT/Q10TCKvYd49grGGZwkOSiEyinxpUPeO5VTzH88anfG1OvZ0GDOqXzc/gBmXHM4gEGsuqHCivpJwBXCrbEp7g8FNWBW9+xfxca+BcfsIZw9hQYjl2NaQIDAQAB
-----END PUBLIC KEY-----"""

AT = "jPrfcbnmk8@#oknd45qscfrkuy"
CT = "rJeeHsd12@9mkokmnxctyuicvtyjm38mngrolmbvd"
MOBILE_SAULT_VALUE = "3457782343794"
MOBILE_SAULT_CODE = "sdfi&qsvaio12@sadidf1!Rnk5"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Mobile Safari/537.36",
    "sec-ch-ua-platform": "\"Android\"",
    "sec-ch-ua": "\"Not=A?Brand\";v=\"99\", \"Brave\";v=\"151\", \"Chromium\";v=\"151\"",
    "sec-ch-ua-mobile": "?1",
    "ocp-apim-subscription-key": SUBSCRIPTION_KEY,
    "accept": "*/*",
    "apporiginbrowse": APP_ORIGIN,
    "content-type": "application/json",
    "ocp-apim-trace": "true",
    "sec-gpc": "1",
    "origin": "https://register.eshram.gov.in",
    "sec-fetch-site": "same-site",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    "referer": "https://register.eshram.gov.in/",
    "accept-language": "en-IN,en;q=0.7",
}


# ===================== UTILITY FUNCTIONS =====================
def b64decode_fix(s):
    """Base64 decode with padding fix"""
    s = s.strip()
    if len(s) % 4 == 1:
        s = s[:-1]
    missing = len(s) % 4
    if missing:
        s += '=' * (4 - missing)
    return base64.b64decode(s)


def pbkdf2_sha256(password, salt, iterations=65536, dklen=32):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations, dklen)


def aes_decrypt_cbc_zero_iv_str(encrypted_b64, secret, salt):
    """AES-CBC decrypt with zero IV (for encrypted responses)"""
    key = pbkdf2_sha256(secret, salt)
    iv = bytes(16)
    ct = b64decode_fix(encrypted_b64)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = unpad(cipher.decrypt(ct), 16)
    return decrypted.decode("utf-8", errors="ignore")


def rsa_encrypt_pkcs1v15(pem_public_key, plaintext):
    """RSA PKCS1 v1.5 encryption → hex string"""
    key = RSA.import_key(pem_public_key)
    cipher = PKCS1_v1_5.new(key)
    ct = cipher.encrypt(plaintext.encode("utf-8"))
    return ct.hex()


def process_captcha_key(captcha_key):
    """Extract actual captcha key from server response"""
    if "EXN59S" in captcha_key:
        first_part = captcha_key.split("EXN59S")[0]
        decoded = b64decode_fix(first_part)
        ckey = decoded[3:-4].decode("utf-8", errors="ignore")
        return ckey
    return captcha_key


def generate_captcha():
    """Fetch captcha from eShram API"""
    url = f"{CAPTCHA_BASE_URL}/generateImgCaptcha/"
    r = requests.post(url, headers=HEADERS, json={}, timeout=15)
    r.raise_for_status()
    return r.json()


def decrypt_captcha_image(encrypted_value):
    """
    Auto-detect captcha format:
    - NEW: direct base64 PNG (no decryption needed)
    - OLD: AES encrypted base64 PNG (fallback)
    """
    # ========== METHOD 1: Direct base64 PNG (NEW format) ==========
    try:
        png_bytes = b64decode_fix(encrypted_value)
        if png_bytes[:8] == b'\x89PNG\r\n\x1a\n':
            print("[✓] Captcha detected as direct PNG")
            return png_bytes
    except Exception as e:
        print(f"[✗] Direct PNG decode failed: {e}")
    
    # ========== METHOD 2: AES decrypt (OLD format - fallback) ==========
    try:
        base64_png_str = aes_decrypt_cbc_zero_iv_str(encrypted_value, CT, AT).strip()
        png_bytes = b64decode_fix(base64_png_str)
        if png_bytes[:8] == b'\x89PNG\r\n\x1a\n':
            print("[✓] Captcha decrypted via AES")
            return png_bytes
    except Exception as e:
        print(f"[✗] AES decrypt failed: {e}")
    
    raise Exception("Failed to decode captcha image (both methods failed)")


def decrypt_mobile(encrypted_mobile):
    """
    Auto-detect mobile format:
    - NEW: plain mobile number
    - OLD: AES encrypted (fallback)
    """
    # Try direct plain mobile first
    try:
        if encrypted_mobile.isdigit() and len(encrypted_mobile) == 10:
            print(f"[✓] Mobile is plain: {encrypted_mobile}")
            return encrypted_mobile
    except:
        pass
    
    # Fallback: AES decrypt
    try:
        mobile = aes_decrypt_cbc_zero_iv_str(encrypted_mobile, MOBILE_SAULT_CODE, MOBILE_SAULT_VALUE).strip()
        print(f"[✓] Mobile decrypted: {mobile}")
        return mobile
    except Exception as e:
        print(f"[✗] Mobile decrypt failed: {e}")
        return encrypted_mobile


def send_otp_request(payload):
    """Send OTP request to eShram"""
    try:
        r = requests.post(
            f"{NDUW_BASE_URL}/otpSendByAadhaar/",
            headers=HEADERS,
            data=json.dumps(payload),
            timeout=20
        )
        resp = r.json()
        if r.status_code == 200 and resp.get("code") == 1:
            return True, resp
        return False, resp
    except Exception as e:
        return False, {"error": str(e)}


# ===================== SESSION STORAGE =====================
user_sessions = {}


# ===================== TELEGRAM BOT HANDLERS =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_sessions.pop(update.effective_chat.id, None)
    await update.message.reply_text(
        "👋 Welcome!\n\n"
        "Send me your *12-digit Aadhaar number* to get the mobile number linked with it.\n\n"
        "Example: `123456789012`",
        parse_mode="Markdown"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text.strip()

    # ========== STEP 1: Awaiting Captcha ==========
    session = user_sessions.get(chat_id)
    if session and session.get("step") == "awaiting_captcha":
        aadhaar = session["aadhaar"]
        captcha_key = session["captcha_key"]
        captcha_value = text.strip()

        if not captcha_value:
            await update.message.reply_text("❌ Please enter a valid captcha.")
            return

        try:
            # Process captcha key
            ckey = process_captcha_key(captcha_key)

            # Encrypt Aadhaar and Captcha
            aadhaar_enc = rsa_encrypt_pkcs1v15(LOGIN_PUBLIC_KEY, aadhaar)
            captcha_obj = json.dumps(
                {"cKey": ckey, "cVal": captcha_value},
                separators=(',', ':')
            ).strip()
            captcha_enc = rsa_encrypt_pkcs1v15(LOGIN_PUBLIC_KEY, captcha_obj)

            payload = {"aadhar": aadhaar_enc, "captcha": captcha_enc}
            success, result = send_otp_request(payload)

            if not success:
                msg = result.get("message", result.get("error", "Failed"))
                await update.message.reply_text(
                    f"❌ *Server Error*\n\n`{msg}`\n\nPlease try again with /start",
                    parse_mode="Markdown"
                )
                user_sessions.pop(chat_id, None)
                return

            encrypted_mobile = result.get("data")
            if not encrypted_mobile:
                await update.message.reply_text("❌ No data received from server.")
                user_sessions.pop(chat_id, None)
                return

            # Decrypt mobile
            mobile = decrypt_mobile(encrypted_mobile)
            
            await update.message.reply_text(
                f"✅ *Mobile Number Found!*\n\n"
                f"📱 `{mobile}`\n\n"
                f"🔍 Aadhaar: `{aadhaar[:4]}XXXX{mobile[-4:] if len(aadhaar) > 8 else ''}`",
                parse_mode="Markdown"
            )
            user_sessions.pop(chat_id, None)

        except Exception as e:
            await update.message.reply_text(
                f"⚠️ *Error*\n\n`{str(e)}`\n\nPlease try again with /start",
                parse_mode="Markdown"
            )
            user_sessions.pop(chat_id, None)
        return

    # ========== STEP 2: New Request - Aadhaar Input ==========
    if len(text) == 12 and text.isdigit():
        aadhaar = text
        try:
            # Send initial message
            msg = await update.message.reply_text("⏳ Fetching captcha...")

            # Generate captcha
            captcha_data = generate_captcha()
            captcha_key = captcha_data["data"]["captchaKey"]
            captcha_value_encrypted = captcha_data["data"]["captchaValue"]

            # Decrypt captcha image
            png_bytes = decrypt_captcha_image(captcha_value_encrypted)

            # Save session
            user_sessions[chat_id] = {
                "step": "awaiting_captcha",
                "aadhaar": aadhaar,
                "captcha_key": captcha_key
            }

            # Delete loading message
            await msg.delete()

            # Send captcha image
            await update.message.reply_text(
                "📸 *Please solve the captcha*\n\n"
                "Type the characters you see in the image and send them here.",
                parse_mode="Markdown"
            )
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=BytesIO(png_bytes),
                caption="🔐 Enter the captcha text"
            )

        except Exception as e:
            await update.message.reply_text(
                f"⚠️ *Failed to generate captcha*\n\n`{str(e)}`",
                parse_mode="Markdown"
            )
            user_sessions.pop(chat_id, None)
        return

    # ========== STEP 3: Invalid Input ==========
    await update.message.reply_text(
        "❌ Please send a *valid 12-digit Aadhaar number*.\n\n"
        "Example: `123456789012`",
        parse_mode="Markdown"
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_sessions.pop(update.effective_chat.id, None)
    await update.message.reply_text("❌ Cancelled. Send /start to begin again.")


# ===================== MAIN =====================
def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    application = Application.builder().token(TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("="*60)
    print("  eShram Aadhaar Bot Running...")
    print("="*60)
    print(f"  Bot Token: {TOKEN[:20]}...")
    print(f"  Press Ctrl+C to stop")
    print("="*60)

    application.run_polling()


if __name__ == "__main__":
    main()