M = "chat_id"
L = print
K = Exception
H = "document"
G = "encoded.py"
F = "1.py"
C = "result"
import os as A, requests as B, time as I
import pystyle
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

J = "T O K E N:"
E = f"https://api.telegram.org/bot{J}"
N = 404800

# Admin configuration
ADMIN_ID = '7132632561'
active_users = {}  
banned_users = set()  
REQUIRED_CHANNELS = ["Pokie_Tool", "pokie_backup"]

def D(chat_id, text, reply_markup=None):
    if reply_markup:
        B.post(f"{E}/sendMessage", data={M: chat_id, "text": text}, json={"reply_markup": reply_markup.to_dict()})
    else:
        B.post(f"{E}/sendMessage", data={M: chat_id, "text": text})

def O(chat_id, file_path):
    with open(file_path, "rb") as A:
        B.post(f"{E}/sendDocument", data={M: chat_id}, files={H: A})

def P(file_id, chat_id):
    A = chat_id
    try:
        G = B.get(f"{E}/getFile?file_id={file_id}").json()
        H = G[C]["file_path"]
        I = f"https://api.telegram.org/file/bot{J}/{H}"
        if not H.endswith(".py"):
            D(A, "❌ Only Python files are allowed.")
            return
        L = G[C]["file_size"]
        if L > N:
            D(A, "❌ File size above 400KB is not allowed.")
            return
        with open(F, "wb") as M:
            M.write(B.get(I).content)
        return F
    except K:
        D(A, "❌ Error downloading file.")
        return

def Q():
    A.system("python3.11 x1.py")

def R(chat_id, file_id):
    B = chat_id
    C = P(file_id, B)
    if C:
        Q()
        if A.path.exists(G):
            O(B, G)
            S()
        else:
            D(B, "❌ Error: 1.py was not created.")

def S():
    try:
        if A.path.exists(F):
            A.remove(F)
        if A.path.exists(G):
            A.remove(G)
    except K as B:
        L(f"Error during cleanup: {B}")

def is_user_in_channels(chat_id):
    """Check if a user is a member of all required channels."""
    for channel in REQUIRED_CHANNELS:
        try:
            response = B.get(f"{E}/getChatMember", params={"chat_id": f"@{channel}", "user_id": chat_id}).json()
            status = response.get("result", {}).get("status")
            if status not in ("member", "administrator", "creator"):
                return False
        except K:
            return False
    return True

def T(updates):
    for E in updates.get(C, []):
        A = E.get("message", {})
        B = A.get("chat", {}).get("id")
        username = A.get("chat", {}).get("username", "Unknown")
        
        # Check if user is banned
        if B in banned_users:
            D(B, "❌ You are banned from using this bot.")
            continue

        # Enforce channel membership
        if not is_user_in_channels(B):
            channel_message = (
                "🔰 Must Join All Channels First :-\n\n"
                "➤ @Pokie_Tool\n"
                "➤ @pokie_backup\n\n"
                "✅ Send /Start to continue"
            )
            D(B, channel_message)
            continue

        # Add user to active users
        active_users[B] = username

        if "text" in A:
            if A["text"] == "/start":
                welcome_message = (
                    "🔐 ENCRYPTION BOT\n"
                    "👤 By: @PokiePy\n\n"
                    "📤 Please send a .py file to encode.\n"
                    "⚠️ Max file size: 400KB\n\n"
                    "✅ You are verified!"
                )
                D(B, welcome_message)
            elif B == ADMIN_ID and A["text"].startswith("/users"):
                send_active_users()
            elif B == ADMIN_ID and A["text"].startswith("/ban"):
                handle_ban(A["text"])
            elif B == ADMIN_ID and A["text"].startswith("/unban"):
                handle_unban(A["text"])
        elif H in A:
            F = A[H]["file_id"]
            message_id = A.get("message_id")
            
            D(B, "📤 File Received, Please Wait...!!")
            R(B, F)

def send_active_users():
    """Send the list of active users to the admin."""
    if not active_users:
        D(ADMIN_ID, "📊 No users have interacted with the bot yet.")
        return

    user_list = "\n".join([f"• {uid}: @{uname}" for uid, uname in active_users.items()])
    D(ADMIN_ID, f"📊 Active Users:\n\n{user_list}")

def handle_ban(command):
    """Ban a user."""
    try:
        _, user_id = command.split()
        user_id = int(user_id)
        banned_users.add(user_id)
        D(ADMIN_ID, f"✅ User {user_id} has been banned.")
    except (ValueError, IndexError):
        D(ADMIN_ID, "❌ Invalid command. Use /ban <user_id>.")

def handle_unban(command):
    """Unban a user."""
    try:
        _, user_id = command.split()
        user_id = int(user_id)
        if user_id in banned_users:
            banned_users.remove(user_id)
            D(ADMIN_ID, f"✅ User {user_id} has been unbanned.")
        else:
            D(ADMIN_ID, f"ℹ️ User {user_id} is not in the banned list.")
    except (ValueError, IndexError):
        D(ADMIN_ID, "❌ Invalid command. Use /unban <user_id>.")

def U(offset=None):
    return B.get(f"{E}/getUpdates", params={"offset": offset}).json()

def V():
    D = None
    while True:
        try:
            A = U(D)
            if C in A and A[C]:
                D = A[C][-1]["update_id"] + 1
                T(A)
            I.sleep(2)
        except B.exceptions.RequestException as E:
            L(f"Connection error: {E}. Retrying in 5 seconds...")
            I.sleep(5)

if __name__ == "__main__":
    V()