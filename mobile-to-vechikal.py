from flask import Flask, request, jsonify
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64, json, time, re, requests

app = Flask(__name__)

BASE = "https://delhigw.napix.gov.in/nic/parivahan"

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


def aes_encrypt_ecb_pkcs7(plaintext, key):
    key = key.encode() if isinstance(key, str) else key
    cipher = AES.new(key, AES.MODE_ECB)
    return base64.b64encode(cipher.encrypt(pad(plaintext.encode(), AES.block_size))).decode()


def aes_decrypt_ecb_pkcs7(encrypted_text, key):
    key = key.encode() if isinstance(key, str) else key
    encrypted_data = base64.b64decode(encrypted_text)
    cipher = AES.new(key, AES.MODE_ECB)
    return unpad(cipher.decrypt(encrypted_data), AES.block_size).decode()


def post_encrypted(url, plain_json, access_token, label):
    ctime, key = make_key()
    payload = json.dumps({
        "data": base64.b64encode(aes_encrypt_ecb_pkcs7(plain_json, key).encode()).decode()
    })
    headers = dict(COMMON_HEADERS)
    headers['Content-Type'] = "application/json; charset=utf-8"
    headers['timestamp'] = ctime
    headers['Authorization'] = f"Bearer {access_token}"

    try:
        r = requests.post(url, data=payload, headers=headers, timeout=15)
        if not r.text.strip():
            return None
        j = r.json()
        data = j.get("data")
        if not data:
            return None
        return aes_decrypt_ecb_pkcs7(base64.b64decode(data).decode(), key)
    except Exception as e:
        print(f"[!] {label} error: {e}")
        return None


def get_access_token():
    url = f"{BASE}/oauth2/token"
    payload = ("grant_type=client_credentials&scope=napix"
               "&client_id=b91c303443f61b37106750823881cd2f"
               "&client_secret=de83eeeb148878ae375f28756492e8a0")
    headers = {
        'User-Agent': "okhttp/4.9.2",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/x-www-form-urlencoded"
    }
    try:
        r = requests.post(url, data=payload, headers=headers, timeout=15)
        return r.json().get("access_token")
    except Exception as e:
        print(f"[!] Token error: {e}")
        return None


def get_vehicle_by_number(number, access_token):
    url = f"{BASE}/mparivahan/wrapperapi/vahan/vahancapi/common/getvehiclevalidity"
    return post_encrypted(url, '{"mobileNo":"' + number + '"}', access_token, "vehicle")


# Vehicle number pattern: DL01AB1234, MH12DE1433, etc.
VEHICLE_REGEX = re.compile(r'\b[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{4}\b')


def extract_vehicle_numbers(obj, found=None):
    """Recursively scan any JSON structure for vehicle numbers."""
    if found is None:
        found = set()
    if obj is None:
        return found
    if isinstance(obj, str):
        for m in VEHICLE_REGEX.findall(obj.upper()):
            found.add(m)
    elif isinstance(obj, list):
        for item in obj:
            extract_vehicle_numbers(item, found)
    elif isinstance(obj, dict):
        for v in obj.values():
            extract_vehicle_numbers(v, found)
    return found


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "Parivahan Vehicle API",
        "usage": "/api/vehicle?mobile=10DIGITNUMBER"
    })


@app.route('/api/vehicle', methods=['GET'])
def vehicle():
    mobile = request.args.get('mobile', '').strip()

    if not mobile or len(mobile) != 10 or not mobile.isdigit():
        return jsonify({
            "success": False,
            "error": "Invalid mobile number. Provide 10-digit number."
        }), 400

    access_token = get_access_token()
    if not access_token:
        return jsonify({
            "success": False,
            "error": "Failed to get access token"
        }), 500

    result = get_vehicle_by_number(mobile, access_token)

    if not result:
        return jsonify({
            "success": False,
            "error": "No data found or API error"
        }), 404

    try:
        data = json.loads(result)
    except json.JSONDecodeError:
        data = result

    # ---- Extract vehicle numbers ----
    vnums = sorted(extract_vehicle_numbers(data))

    return jsonify({
        "success": True,
        "mobile": mobile,
        "vehicle_numbers": vnums,       # <-- vehicle numbers array
        "vehicle_count": len(vnums),    # <-- count
        "data": data
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)