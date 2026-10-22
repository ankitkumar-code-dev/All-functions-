from flask import Flask, jsonify, request
from flask_cors import CORS
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Hash import SHA256
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import requests
import base64
import os
import json

app = Flask(__name__)
CORS(app)

GATEWAY = "https://apigw.umangapp.in/ioclApi/ws1/consumervalidate"

# ====================== KEYS ======================
PUB_PEM = b"""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEArpgmSqIv/3zYAxoNK/6e
LqjeBEHFsiGJCia5wdQuhCw54ceg6EyKc5mPrkEnK7CYgbJxSQO37HbnWIROMN6k
RQqxa1kZFFS+xQPZ9z4Gs+njypX8HNKcse2/kbwbIX4y8kcCENVVOV8URK8+znEs
uN/UCzJXv2Pg0KII5ofb8wAvYNXkZ44DhcWnyxO6JohbuMvpt096NBkdq8lWtRra
ppL3HqpTG4Fd5H4v9b7fD8rAhBB8cAbiM2nyBz51VDovS/SZheIemKjwGLGMDiMe
NcQGryOTZASX+jxe69NoFR9bQ8+5jN/88x5k53UzV8en+HRKbYjgUJzZOVfu3fL/
WQIDAQAB
-----END PUBLIC KEY-----"""

PRIV_PEM = b"""-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCumCZKoi//fNgD
Gg0r/p4uqN4EQcWyIYkKJrnB1C6ELDnhx6DoTIpzmY+uQScrsJiBsnFJA7fsdudY
hE4w3qRFCrFrWRkUVL7FA9n3Pgaz6ePKlfwc0pyx7b+RvBshfjLyRwIQ1VU5XxRE
rz7OcSy439QLMle/Y+DQogjmh9vzAC9g1eRnjgOFxafLE7omiFu4y+m3T3o0GR2r
yVa1GtqmkvceqlMbgV3kfi/1vt8PysCEEHxwBuIzafIHPnVUOi9L9JmF4h6YqPAY
sYwOIx41xAavI5NkBJf6PF7r02gVH1tDz7mM3/zzHmTndTNXx6f4dEptiOBQnNk5
V+7d8v9ZAgMBAAECggEActY8iWZ4L5GL+y5Nb5x/qq0DqsUgJXQNURH7qFPJbMIy
KCFH4sNFZZehe7n666+x/8zA2oeJmAz1SbFsRJSMc6T+4V6vMkIzYB6SZR71Ba1X
WM6iDsswqY95K4AQUE1TcSvnXe8TqTKygCLMKrkh80+1hs/MC2TEYDXTqN2/e+qO
Bq6/RQ4A7E+Qd1R6/mFEHZJfmvMVl0lBmowHk060/JAgeSxE5VPnP2pQXad21w/n
BtSoQDOKpAzbcSIgn4vLavtUlS87XYQ8bq3Mc4sPQe9RZ9o89aQrau0SmdgNeGYV
i0tWhP2lm3b8C3XcgDQi6LwnZpzwCo9m5fEcJM4IyQKBgQD//t26TkBC2h4trvbO
ID2SN2hPiBySxjb3Eoaiy58ryF/d4Im56Xf61ksuy0od52vgNzW03As6vPjTJpqy
/EeJrOZHLdZSOiFZzqcgXUcir2O6gM/WIU/0x/Ge7nnp0DfwTYgTNzpJA+csR9aD
FhOu9e+xogJ0lV4eCEBjjC+Q+wKBgQCumOxDZkaH9uuXSbrGTsrEMO0439oLM+Er
6L+Pdpy8qY0Q5ZYp2C1ZZBz8DwH6NwwKY/JcvrVVS5D90mmqsm39ubeIrmv7C04T
WBQqYRp9dgRkUkVo9BGM6EqA2q/D2JT/sr/72h5FEsMblHSVEXbCo/QLYvCglxSs
7jhx5tDIuwKBgQC/W2epJWc50cvvQDNzP3xm+Q37LXaWbJ6Xr/x+YpFX7A9lTrwF
AbVTBq7qisGbeusTjpGR4U5vmOSzCc9n7dcX3evA102254cYl7YsJi3PiqWUu0cg
/IPFKVS/BeqR0biO45XNL2JdRBKg8g4yrOUHywVilgUZ2rGg53AiOZ8w0wKBgQCp
by/AjI0fvwiLrXo6nhX55H0hd2LTAkqe4OSdJX8fOu7xmctq2iXQHO5f0XSazDa8
EpgNVukEWCvhlgMDKtrAoiyw0ItreWIQNaaEJe2eGRxT+t7u5gPuGTLL7u0pApI9
vcq/bsF3SKjcp+mnC+aTJqZbMm3Pei4PT7KpHlQ4pwKBgDeLXCwO6cCa+4nV4t5k
tCEzQPiu/yEMAL0hf3RwPr7WuckwyHm3cUt7DFCEf6+bJj+hpxVXGcdgVxDZjyh4
s8YE8AAd+2iv8I61gF475KAOOMbkt21TzTI0y2R2BN3JvB1iTmf6CkV6C82b4UEL
lKjEOX342756ZWQbhB8Yld1T
-----END PRIVATE KEY-----"""
# ==================================================

_pub_key = RSA.import_key(PUB_PEM)
_priv_key = RSA.import_key(PRIV_PEM)

# Decrypted Payload Parameters
SESSION = {
    "tkn": "ch23c03f1e-7aca-4ac1-ad09-8e5d82379102/3",
    "trkr": "213132",
    "lang": "en",
    "lat": "21",
    "lon": "90",
    "lac": "90",
    "usag": "90",
    "apitrkr": "123234",
    "usrid": "4066805236",
    "mode": "web",
    "pltfrm": "android",
    "did": "123234",
    "deptid": "186",
    "formtrkr": "0",
    "srvid": "1123",
    "subsid": "0",
    "subsid2": "0",
    "trackingId": "",
    "source": "UMANG",
    "partnerCode": ""
}

HEADERS = {
    "host": "apigw.umangapp.in",
    "subsid": "0",
    "sec-ch-ua-platform": '"Android"',
    "deptid": "186",
    "tenantid": "",
    "sec-ch-ua": '"Not;A=Brand";v="8", "Chromium";v="150", "Android WebView";v="150"',
    "formtrkr": "0",
    "x-api-key": "VKE9PnbY5k1ZYapR5PyYQ33I26sXTX569Ed7eqyg",
    "sec-ch-ua-mobile": "?1",
    "srvid": "1123",
    "accept": "application/json",
    "subsid2": "0",
    "content-type": "application/json",
    "user-agent": "Mozilla/5.0 (Linux; Android 10; M2006C3LI Build/QP1A.190711.020) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.7871.184 Mobile Safari/537.36",
    "origin": "https://web.umang.gov.in",
    "x-requested-with": "mark.via.gp",
    "sec-fetch-site": "cross-site",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    "referer": "https://web.umang.gov.in/",
    "accept-language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7"
}

def umang_encrypt(plaintext: str) -> str:
    aes_key = get_random_bytes(32)
    iv = get_random_bytes(16)

    padded = pad(plaintext.encode('utf-8'), AES.block_size)
    cipher_aes = AES.new(aes_key, AES.MODE_CBC, iv)
    ct = cipher_aes.encrypt(padded)

    cipher_rsa = PKCS1_OAEP.new(_pub_key, hashAlgo=SHA256)
    ek = cipher_rsa.encrypt(aes_key)
    eiv = cipher_rsa.encrypt(iv)

    return ":".join(base64.b64encode(x).decode() for x in (ek, eiv, ct))

def umang_decrypt(blob: str) -> str:
    parts = blob.strip().split(":")
    cipher_rsa = PKCS1_OAEP.new(_priv_key, hashAlgo=SHA256)

    if len(parts) == 3:
        ek = base64.b64decode(parts[0])
        eiv = base64.b64decode(parts[1])
        ct = base64.b64decode(parts[2])

        aes_key = cipher_rsa.decrypt(ek)
        iv = cipher_rsa.decrypt(eiv)
    elif len(parts) == 2:
        ek = base64.b64decode(parts[0])
        ct = base64.b64decode(parts[1])

        aes_key = cipher_rsa.decrypt(ek)
        iv = ct[:16]
        ct = ct[16:]
    else:
        raise ValueError(f"Unexpected number of parts: {len(parts)}")

    cipher_aes = AES.new(aes_key, AES.MODE_CBC, iv)
    decrypted_padded = cipher_aes.decrypt(ct)
    raw = unpad(decrypted_padded, AES.block_size)
    
    return raw.decode("utf-8", errors="replace")

@app.get("/")
def home():
    return jsonify({
        "status": True,
        "endpoint": "/umang_lpg?num=<mobile_or_consumer_number>"
    })

@app.get("/umang_lpg")
def umang_lpg():
    num = request.args.get("num")
    if not num:
        return jsonify({"ok": False, "error": "Query parameter 'num' missing. Use /umang_lpg?num=XXXXXXXXXX"}), 400

    body = dict(SESSION)
    
    # 10 digit number par mobile field set hogi, otherwise consumerNumber/consumerId
    if len(num) == 10 and num.isdigit():
        body["mobile"] = num
        body["consumerId"] = ""
        body["consumerNumber"] = ""
    else:
        body["mobile"] = ""
        body["consumerId"] = num
        body["consumerNumber"] = num

    payload = umang_encrypt(json.dumps(body, separators=(",", ":")))

    try:
        r = requests.post(GATEWAY, data=payload, headers=HEADERS, timeout=20)
    except Exception as e:
        return jsonify({"ok": False, "error": f"gateway: {e}"}), 502

    # Plain JSON response fallback
    try:
        data = json.loads(r.text)
        return jsonify(data)
    except Exception:
        pass

    # Encrypted payload decryption
    try:
        plain = umang_decrypt(r.text)
        data = json.loads(plain)
        return jsonify(data)
    except Exception as e:
        return jsonify({
            "ok": False,
            "gateway_status": r.status_code,
            "error": f"decrypt: {str(e)}",
            "raw": r.text[:800]
        }), 502

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
    