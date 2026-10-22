from http.server import BaseHTTPRequestHandler
import json
import base64
import random
from urllib.parse import parse_qs, urlparse
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad, unpad
import requests

# --- HARDCODED CREDENTIALS ---
API_KEY = "VKE9PnbY5k1ZYapR5PyYQ33I26sXTX569Ed7eqyg"
RAW_DATA_STRING = "ktoF3BcqssgChOY0M7yu84kdydaruQcXgJMz4Rd2d4GtCYqp3ad7xx/CNFSjKYC3YKK1V61xksRZ61ZsN732JJmxR1oCMbbCcQle8CxnQiN9ap9KZfmXgFWuZjLYLZTLDcnXh9uZ8nczszPSvH1wzHWfoiswtQoi37T3LsoOb/bEhT6MeG7sb6+vbZF9uV1c5FLvHamXtcHFxlTjkBqWfz7qZa2OjyvuTuxjrxkXnTLiTZ/YhW/1oPU7uTkPSwBFwjRjTtRLQPo9J9f+iC7vpQrAXOnor5wnOeRd10Jm9j2JhBGb/iSEXeDPR1ol+jrqYBiFWhjHcwqlwA89CMVTOg==:Ys5lG+CTMq5+Kz0oXsQuElLMS+XmJZc4WXXEO7vUd8ng+Qgzw0qzn7gz5ZDWTTi5NmkAMxN4VwLm9Y2ocsOar0PpNwQBwbIj8hcTEFiBuAeS3uTGXIEqJ4hPZXJ87roAhFjI4YGSn7ZsKA1hNdVoHktdxrAccYfOeOcBm3lT22SBynNdW9PLrtt+XKQajCOmBsI42BYhTZdxUgLo1Mvkm9WvXJNJGBvCzUKQRrsZ8z+DkJSKxpewe8oANg3R528zgwDEgyLW8mqWWUBFdaTNbGL5Su600X7aAkKJgRayn34ENB0rvjLEWJ6ktuPOoFP3rnB1CE3kAgSd2gocMSOQVA==:aECVeb3lEVf85YWqwcTosePQ5z1k1/hSinrqeOZfHKD/+eH9Pd22XlgGZ79bMuZaptE9Vh4SMN5LxVr6fpT/o4xfilKLRnMXv4NH6GsUN+Rg8X0yeari0H9t5GWpzd2dzHHYPOHB1umewFYkhHdLBuHWM9j+RQYOhJhLvPBbGDFxdDZWppzLiPqgojMihLEYMx5JZUutBdSZT9HLT3KOKjBjz2ZGhFWFSEC3Ofncy6HNnkZRZdb4YXXzjczmOqW07OMOo8WGmomWS5Kdubm8+C1MeIqXOYcb36odIu8hKiR3n5kwwbWC4TDLXzHZJYMxF0ZQEhwGf1FmGhVI1Ttwa1UVbXu+CINCn8fYFYlc464ZMk0KxLnJ4MftRHrzhf4Yo4TigXli1sIGU8I/Gfh+HNnwrcTlR0CS3FRFyjMAoa7V4AlXGZbP4C2KB04sf4yS+K+HrFHEcvjf+icnWQ4aolUsgxZbQlonW++TlrtXD3pl412WDElbFVr/Iris9LO1"
# -----------------------------

PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEArpgmSqIv/3zYAxoNK/6e
LqjeBEHFsiGJCia5wdQuhCw54ceg6EyKc5mPrkEnK7CYgbJxSQO37HbnWIROMN6k
RQqxa1kZFFS+xQPZ9z4Gs+njypX8HNKcse2/kbwbIX4y8kcCENVVOV8URK8+znEs
uN/UCzJXv2Pg0KII5ofb8wAvYNXkZ44DhcWnyxO6JohbuMvpt096NBkdq8lWtRra
ppL3HqpTG4Fd5H4v9b7fD8rAhBB8cAbiM2nyBz51VDovS/SZheIemKjwGLGMDiMe
NcQGryOTZASX+jxe69NoFR9bQ8+5jN/88x5k53UzV8en+HRKbYjgUJzZOVfu3fL/
WQIDAQAB
-----END PUBLIC KEY-----"""

PRIVATE_KEY_PEM = """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCumCZKoi//fNgD
Gg0r/p4uqN4EQcWyIYkKJrnB1C6ELDnhx6DoTIpzmY+uQScrsJiBsnFJA7fsdudY
hE4w3qRFCrFrWRkUVL7FA9n3Pgaz6ePKlfwc0pyx7b+RvBshfjLyRwIQ1VU5XxRE
rz7OcSy439QLMle/Y+DQogjmh9vzAC9g1eRnjgOFxafLE7omiFu4y+m3T3o0GR2r
yVa1GtqmkvceqlMbgV3kfi/1vt8PysCEEHxwBuIzafIHPnVUOi9L9JmF4h6YqPAY
sYwOIx41xAavI5NkBJf6PF7r02gVH1tDz7mM3/zzHmTndTNXx6f4dEptiOBQnNk5V
+7d8v9ZAgMBAAECggEActY8iWZ4L5GL+y5Nb5x/qq0DqsUgJXQNURH7qFPJbMIyKC
FH4sNFZZehe7n666+x/8zA2oeJmAz1SbFsRJSMc6T+4V6vMkIzYB6SZR71Ba1XWM6
iDsswqY95K4AQUE1TcSvnXe8TqTKygCLMKrkh80+1hs/MC2TEYDXTqN2/e+qOBq6
/RQ4A7E+Qd1R6/mFEHZJfmvMVl0lBmowHk060/JAgeSxE5VPnP2pQXad21w/nBtS
oQDOKpAzbcSIgn4vLavtUlS87XYQ8bq3Mc4sPQe9RZ9o89aQrau0SmdgNeGYVi0t
WhP2lm3b8C3XcgDQi6LwnZpzwCo9m5fEcJM4IyQKBgQD//t26TkBC2h4trvbOID2S
N2hPiBySxjb3Eoaiy58ryF/d4Im56Xf61ksuy0od52vgNzW03As6vPjTJpqy/EeJ
rOZHLdZSOiFZzqcgXUcir2O6gM/WIU/0x/Ge7nnp0DfwTYgTNzpJA+csR9aDFhOu
9e+xogJ0lV4eCEBjjC+Q+wKBgQCumOxDZkaH9uuXSbrGTsrEMO0439oLM+Er6L+P
dpy8qY0Q5ZYp2C1ZZBz8DwH6NwwKY/JcvrVVS5D90mmqsm39ubeIrmv7C04TWBQq
YRp9dgRkUkVo9BGM6EqA2q/D2JT/sr/72h5FEsMblHSVEXbCo/QLYvCglxSs7jhx
5tDIuwKBgQC/W2epJWc50cvvQDNzP3xm+Q37LXaWbJ6Xr/x+YpFX7A9lTrwFAbVT
Bq7qisGbeusTjpGR4U5vmOSzCc9n7dcX3evA102254cYl7YsJi3PiqWUu0cg/IPF
KVS/BeqR0biO45XNL2JdRBKg8g4yrOUHywVilgUZ2rGg53AiOZ8w0wKBgQCpby/A
jI0fvwiLrXo6nhX55H0hd2LTAkqe4OSdJX8fOu7xmctq2iXQHO5f0XSazDa8EpgN
VukEWCvhlgMDKtrAoiyw0ItreWIQNaaEJe2eGRxT+t7u5gPuGTLL7u0pApI9vcq/
bsF3SKjcp+mnC+aTJqZbMm3Pei4PT7KpHlQ4pwKBgDeLXCwO6cCa+4nV4t5ktCEzQ
Piu/yEMAL0hf3RwPr7WuckwyHm3cUt7DFCEf6+bJj+hpxVXGcdgVxDZjyh4s8YE8
AAd+2iv8I61gF475KAOOMbkt21TzTI0y2R2BN3JvB1iTmf6CkV6C82b4UELlKjEO

X342756ZWQbhB8Yld1T
-----END PRIVATE KEY-----"""
def aadhar_num(uid: str) -> str:
    key = bytes.fromhex("64ca098b0a8481987615e69b0f8d43ef")
    iv = bytes.fromhex("6e696340696d70647323646564757030")
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ct_bytes = cipher.encrypt(pad(uid.encode("utf-8"), AES.block_size))
    b64_1 = base64.b64encode(ct_bytes)
    b64_2 = base64.b64encode(b64_1)
    return b64_2.decode("utf-8")


def get_ration_from_aadhar(aadhar_number: str):
    url = "https://meraration.nic.in/onorc/v1/verifyAadharNumber"
    payload = {
        "aadharNumber": aadhar_num(aadhar_number),
        "forceUpdate": ""
    }
    headers = {
        'User-Agent': "Dart/3.5 (dart:io)",
        'Accept': "application/json",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/json",
        'language': "en",
        'userid': "",
        'authorization': "Bearer",
        'key': "1a7a78f970a7a6d0a5042aebc0fbf4a67c999a87c9fde871b17017c82b477396"
    }
    response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=30)
    return response.json()


def crypto_decrypt(encrypted_string):
    parts = encrypted_string.strip().split(':')
    if len(parts) != 3:
        raise ValueError("Invalid encrypted shape. Expected 3 base64 segments separated by colons.")
    enc_key, enc_iv, enc_data = map(base64.b64decode, parts)
    private_key = RSA.import_key(PRIVATE_KEY_PEM)
    cipher_rsa = PKCS1_OAEP.new(private_key, hashAlgo=SHA256)
    cipher_aes = AES.new(cipher_rsa.decrypt(enc_key), AES.MODE_CBC, iv=cipher_rsa.decrypt(enc_iv))
    decrypted = cipher_aes.decrypt(enc_data)
    return decrypted[:-decrypted[-1]].decode('utf-8')


def crypto_encrypt(payload_dict):
    aes_key = AES.get_random_bytes(32)
    aes_iv = AES.get_random_bytes(16)
    cipher_aes = AES.new(aes_key, AES.MODE_CBC, iv=aes_iv)
    payload_bytes = json.dumps(payload_dict).encode('utf-8')
    padded = pad(payload_bytes, AES.block_size)
    encrypted_data = cipher_aes.encrypt(padded)
    public_key = RSA.import_key(PUBLIC_KEY_PEM)
    cipher_rsa = PKCS1_OAEP.new(public_key, hashAlgo=SHA256)
    return ":".join([
        base64.b64encode(cipher_rsa.encrypt(aes_key)).decode(),
        base64.b64encode(cipher_rsa.encrypt(aes_iv)).decode(),
        base64.b64encode(encrypted_data).decode()
    ])


def fetch_umang_data(ration_card_number: str):
    decrypted_json_str = crypto_decrypt(RAW_DATA_STRING)
    browser_data = json.loads(decrypted_json_str)
    active_session_id = browser_data.get('sessionId')
    active_tkn = browser_data.get('tkn')
    active_usrid = browser_data.get('usrid')

    if not active_session_id or not active_tkn:
        raise Exception("Session variables not found in decrypted payload.")

    session = requests.Session()
    url = 'https://apigw.umangapp.in/onorcApi/ws1/getrationcard'

    options_headers = {
        'accept': '*/*',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'access-control-request-headers': 'content-type,deptid,formtrkr,srvid,subsid,subsid2,tenantid,x-api-key',
        'access-control-request-method': 'POST',
        'origin': 'https://web.umang.gov.in',
        'referer': 'https://web.umang.gov.in/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'
    }
    session.options(url, headers=options_headers, timeout=10)

    new_payload = {
        "tkn": active_tkn,
        "trkr": str(random.randint(100000, 999999)),
        "lang": "en", "lat": "21", "lon": "90", "lac": "90", "usag": "90",
        "apitrkr": str(random.randint(100000, 999999)),
        "usrid": active_usrid,
        "mode": "web", "pltfrm": "linux",
        "did": str(random.randint(100000, 999999)),
        "deptid": "317", "formtrkr": "0", "srvid": "1519", "subsid": "0", "subsid2": "0",

        "id": ration_card_number,
        "sessionId": active_session_id,
        "userName": "umang", "idType": "R", "token": "Um@93259@"
    }
    encrypted_body = crypto_encrypt(new_payload)
    post_headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'deptid': '317',
        'formtrkr': '0',
        'origin': 'https://web.umang.gov.in',
        'priority': 'u=1, i',
        'referer': 'https://web.umang.gov.in/',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'srvid': '1519',
        'subsid': '0',
        'subsid2': '0',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
        'x-api-key': API_KEY
    }

    res = session.post(url, headers=post_headers, data=encrypted_body, timeout=30)

    if res.status_code != 200:
        raise Exception(f"UMANG error: HTTP {res.status_code}")

    decrypted_response = crypto_decrypt(res.text)
    return json.loads(decrypted_response)


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        aadhar = params.get('aadhar', [''])[0]

        if not aadhar or len(aadhar) != 12 or not aadhar.isdigit():
            self._send_json(400, {"success": False, "error": "Invalid Aadhaar. Must be 12 digits."})
            return

        try:
            # Step 1: Get ration card
            ration_result = get_ration_from_aadhar(aadhar)

            if not ration_result.get('success') or not ration_result.get('data'):
                self._send_json(404, {
                    "success": False,
                    "error": ration_result.get('message', 'Ration card not found')
                })
                return

            ration_card = ration_result['data']['rationCardNumber']

            # Step 2: Fetch UMANG data
            umang_data = fetch_umang_data(ration_card)

            self._send_json(200, {
                "success": True,
                "aadhar": aadhar[:4] + "********" + aadhar[-4:],
                "rationCardNumber": ration_card,
                "umangData": umang_data
            })

        except Exception as e:
            self._send_json(500, {"success": False, "error": str(e)})

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')

        try:
            data = json.loads(body) if body else {}
        except:
            data = parse_qs(body)
            data = {k: v[0] for k, v in data.items()}

        aadhar = data.get('aadhar', '') if isinstance(data, dict) else ''

        if not aadhar or len(aadhar) != 12 or not aadhar.isdigit():
            self._send_json(400, {"success": False, "error": "Invalid Aadhaar. Must be 12 digits."})
            return

        try:
            ration_result = get_ration_from_aadhar(aadhar)

            if not ration_result.get('success') or not ration_result.get('data'):
                self._send_json(404, {
                    "success": False,
                    "error": ration_result.get('message', 'Ration card not found')
                })
                return

            ration_card = ration_result['data']['rationCardNumber']
            umang_data = fetch_umang_data(ration_card)

            self._send_json(200, {
                "success": True,
                "aadhar": aadhar[:4] + "********" + aadhar[-4:],

                "rationCardNumber": ration_card,
                "umangData": umang_data
            })
        except Exception as e:
            self._send_json(500, {"success": False, "error": str(e)})
    def _send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))