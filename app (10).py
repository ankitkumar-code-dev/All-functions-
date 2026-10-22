import requests
import json
import time

REFRESH_URL = "https://user.mufinpay.com/user-service/user/refresh-token"
REFRESH_TOKEN = "762080ee-fa17-4614-82b4-d3fd060f135d"

API_URL = "https://apps-payment.mufinpay.com/payment/api/transaction/validate/vpa"
MOBILE_NO = "9303661877"


def refresh_jwt():
    """Fetch new JWT token automatically using refresh-token API."""
    payload = {"refToken": REFRESH_TOKEN}

    try:
        res = requests.post(
            REFRESH_URL,
            json=payload,
            headers={'User-Agent': "okhttp/4.12.0", "Content-Type": "application/json"},
        )

        data = res.json()
        
        # REAL KEY:
        if res.status_code == 200 and data.get("data", {}).get("authToken"):
            new_token = data["data"]["authToken"]
            print("\n🔄 Token Refreshed Successfully!\n")
            return new_token

        print("\n⚠️ Refresh response not matched:", res.text)
        return None

    except Exception as e:
        print("\n❌ Refresh Error:", e)
        return None


# Load token first time
AUTH_TOKEN = refresh_jwt()


def make_request(upi):
    global AUTH_TOKEN

    headers = {
        'User-Agent': "okhttp/4.12.0",
        'Content-Type': "application/json",
        'authorization': AUTH_TOKEN
    }

    payload = {"mobileNo": MOBILE_NO, "vpa": upi}
    response = requests.post(API_URL, json=payload, headers=headers)

    # If token expired → refresh and retry
    if "expired" in response.text.lower() or response.status_code == 401:
        print("\n⚠️ Token expired — refreshing...\n")
        AUTH_TOKEN = refresh_jwt()
        headers["authorization"] = AUTH_TOKEN
        response = requests.post(API_URL, json=payload, headers=headers)

    return response


while True:
    upi = input("UPI: ").strip()

    if upi.lower() in ["exit", ""]:
        print("\n👋 Exiting...\n")
        break

    # ✅ ADD THIS LOGIC
    if "@" not in upi and upi.isdigit() and len(upi) == 10:
        upi = upi + "@mapper.npci"
        print(f"➡️ UPI: {upi}")

    response = make_request(upi)

    try:
        data = response.json()
    except:
        print("\n⚠️ Server error or blocked response.\n")
        continue

    if data.get("code") != "0000":
        print("\n❌ Invalid or Not Supported\n")
        continue

    res = data["data"]["response"]

    name = res.get("name")
    accType = res.get("payeeAccType")
    ifsc = res.get("payeeIfsc")
    final_upi = res.get("payeeVpa")

    bank = requests.get(f"https://ifsc.razorpay.com/{ifsc}")
    try:
        bank_info = bank.json()
    except:
        bank_info = {}

    print(f"""
Name: {name}
UPI: {final_upi}
Account Type: {accType}
IFSC: {ifsc}
Bank: {bank_info.get('BANK', 'N/A')}
Branch: {bank_info.get('BRANCH', 'N/A')}
City: {bank_info.get('CITY', 'N/A')}
State: {bank_info.get('STATE', 'N/A')}
Address: {bank_info.get('ADDRESS', 'N/A')}
----------------------------------
""")