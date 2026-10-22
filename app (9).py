from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64, json, time, binascii
import requests

BASE = "https://delhigw.napix.gov.in/nic/parivahan"
DEBUG = True

COMMON_HEADERS = {
    'User-Agent': "okhttp/4.9.2",
    'Connection': "Keep-Alive",
    'Accept': "application/json",
    'Accept-Encoding': "gzip",
    'Param2': "2.0.142",
    'Param1': "abcd"
}

def make_key():
    ctime = str(int(time.time() * 1000))
    return ctime, ctime[-4:][::-1] + ctime[:4][::-1] + '!~)#@*&^'

def dbg(label, r):
    if DEBUG:
        print(f"\n[{label}] status={r.status_code}")
        print(f"[{label}] headers={dict(r.headers)}")
        print(f"[{label}] body={r.text[:800]!r}")

def aes_encrypt_ecb_pkcs7(plaintext, key):
    key = key.encode() if isinstance(key, str) else key
    cipher = AES.new(key, AES.MODE_ECB)
    return base64.b64encode(cipher.encrypt(pad(plaintext.encode(), AES.block_size))).decode()

def aes_decrypt_ecb_pkcs7(encrypted_text, key):
    key = key.encode() if isinstance(key, str) else key
    encrypted_data = base64.b64decode(encrypted_text)
    cipher = AES.new(key, AES.MODE_ECB)
    return unpad(cipher.decrypt(encrypted_data), AES.block_size).decode()

def aes_cbc_decrypt_base64(data_base64, key_hex, iv_str):
    cipher = AES.new(binascii.unhexlify(key_hex), AES.MODE_CBC, iv_str.encode('utf-8'))
    return unpad(cipher.decrypt(base64.b64decode(data_base64)), AES.block_size)

def post_encrypted(url, plain_json, access_token, label):
    """Encrypt -> b64 -> send -> b64decode -> decrypt. Sab errors cleanly handle karta hai."""
    ctime, key = make_key()
    payload = json.dumps({"data": base64.b64encode(aes_encrypt_ecb_pkcs7(plain_json, key).encode()).decode()})
    headers = dict(COMMON_HEADERS)
    headers['Content-Type'] = "application/json; charset=utf-8"
    headers['timestamp'] = ctime
    headers['Authorization'] = f"Bearer {access_token}"

    r = requests.post(url, data=payload, headers=headers)
    dbg(label, r)

    if not r.text.strip():
        raise SystemExit(f"[{label}] Server ne khali response diya (status {r.status_code}). "
                         f"Token/whitelisting/Param2 version check karo.")
    try:
        j = r.json()
    except ValueError:
        raise SystemExit(f"[{label}] JSON nahi mila (status {r.status_code}). Body upar print hui hai.")

    if j.get("status") not in (None, "success", "Success") and "data" not in j:
        raise SystemExit(f"[{label}] API error: {j}")

    data = j.get("data")
    if not data:
        raise SystemExit(f"[{label}] Response me 'data' key nahi: {j}")

    return aes_decrypt_ecb_pkcs7(base64.b64decode(data).decode(), key)

def getAccesToken():
    url = f"{BASE}/oauth2/token"
    payload = ("grant_type=client_credentials&scope=napix"
               "&client_id=b91c303443f61b37106750823881cd2f"
               "&client_secret=de83eeeb148878ae375f28756492e8a0")
    headers = {'User-Agent': "okhttp/4.9.2", 'Connection': "Keep-Alive",
               'Accept-Encoding': "gzip", 'Content-Type': "application/x-www-form-urlencoded"}
    r = requests.post(url, data=payload, headers=headers)
    dbg("token", r)

    try:
        j = r.json()
    except ValueError:
        raise SystemExit(f"[token] JSON nahi mila (status {r.status_code}): {r.text[:300]!r}")

    token = j.get("access_token")
    if not token:
        raise SystemExit(f"[token] access_token nahi mila: {j}")
    return token

def getStateOfficeCode(access_token, plate_number):
    url = f"{BASE}/mparivahan/wrapperapi/vahan/vahancapi/masterconfig/getstate_cdOffcd"
    return post_encrypted(url, '{"regNo":"' + plate_number + '"}', access_token, "stateoff")

def getVehicleByNumber(number, access_token):
    url = f"{BASE}/mparivahan/wrapperapi/vahan/vahancapi/common/getvehiclevalidity"
    return post_encrypted(url, '{"mobileNo":"' + number + '"}', access_token, "vehicle")

def getMobileNumber(plate_number, stateCd, chassis_number, offCd, access_token):
    url = f"{BASE}/mparivahan/wrapperapi/vahan/vahancapi/updatemobile/getMobileNo"
    body = ('{"regnNo":"' + plate_number + '","stateCode":"' + stateCd +
            '","chassisNo":"' + str(chassis_number) + '","officeCode":"' + str(offCd) + '"}')
    return post_encrypted(url, body, access_token, "mobileno")

if __name__ == "__main__":
    mobile_number = input("Enter 10 Digit Mobile Number: ").replace(" ", "").strip()
    if len(mobile_number) != 10 or not mobile_number.isdigit():
        raise SystemExit("10 digit number daalo")

    access_token = getAccesToken()
    print("\nToken OK, vehicle validity fetch ho raha hai...\n")

    result = getVehicleByNumber(mobile_number, access_token)
    print("\nRESULT:")
    try:
        print(json.dumps(json.loads(result), indent=2))
    except ValueError:
        print(result)

    """
    # Registration number se flow (chalu karna ho toh uncomment karo):
    vehicle_number = input("Enter Vehicle Number: ").replace(" ", "").upper()
    resj = json.loads(getStateOfficeCode(access_token, vehicle_number))
    print(json.dumps(resj, indent=2))
    stateCd = resj.get("stateCd")
    offCd = resj.get("offCd")
    chassis_number = input("Enter Chassis Number: ").strip()
    details = getMobileNumber(vehicle_number, stateCd, chassis_number, offCd, access_token)
    print(details)
    """