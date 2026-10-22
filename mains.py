#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║  🪪  ENI's Unified Ration API — Final v10.0                    ║
║  Step 1: NIC → Aadhaar → Ration Card Number (AES double-B64)   ║
║  Step 2: Umang → Ration# → Full Details (RSA+AES encrypted)    ║
║  GET/POST | Single/Bulk | Full Pipeline                         ║
╚══════════════════════════════════════════════════════════════════╝
"""

import requests
import json
import base64
import random
import string
import time
import threading
import os
import sys
import uuid
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# ─── NIC Encryption (pycryptodome) ───
from Crypto.Cipher import AES as AES_NIC
from Crypto.Util.Padding import pad as pad_nic

# ─── Umang Encryption (cryptography.hazmat) ───
from cryptography.hazmat.primitives import hashes, padding as umang_padding
from cryptography.hazmat.primitives.asymmetric import rsa, padding as rsa_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_pem_private_key

from flask import Flask, request, jsonify
app = Flask(__name__)

# ============================================================
#  SOURCE 1: NIC Mera Ration — Aadhaar → Ration Card Number
# ============================================================
NIC_URL = "https://meraration.nic.in/onorc/v1/verifyAadharNumber"
NIC_API_KEY = "1a7a78f970a7a6d0a5042aebc0fbf4a67c999a87c9fde871b17017c82b477396"
NIC_AES_KEY = bytes.fromhex("64ca098b0a8481987615e69b0f8d43ef")
NIC_AES_IV  = bytes.fromhex("6e696340696d70647323646564757030")

# ============================================================
#  SOURCE 2: Umang — Ration Card Number → Full Details
# ============================================================
UMANG_URL = "https://apigw.umangapp.in/onorcApi/ws1/getrationcard"
UMANG_X_API_KEY = "VKE9PnbY5k1ZYapR5PyYQ33I26sXTX569Ed7eqyg"

UMANG_PRIVATE_KEY_PEM = """-----BEGIN PRIVATE KEY-----
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

UMANG_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "x-api-key": UMANG_X_API_KEY,
    "deptid": "317",
    "srvid": "1519",
    "subsid": "0",
    "subsid2": "0",
    "formtrkr": "0",
    "tenantid": "",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Origin": "https://web.umang.gov.in",
    "Referer": "https://web.umang.gov.in/",
    "x-requested-with": "mark.via.gp"
}

# ============================================================
#  TUNING
# ============================================================
MAX_WORKERS = 3
STAGGER = 1.5
BATCH_SIZE = 50

# ============================================================
#  PER-AADHAAR COOLDOWN TRACKER
# ============================================================
cooldown_lock = threading.Lock()
cooldowns = {}

def cd_check(aadhaar):
    with cooldown_lock:
        e = cooldowns.get(aadhaar)
        if e and e.get("until") and datetime.now() < e["until"]:
            return int((e["until"] - datetime.now()).total_seconds() // 60) + 1
    return 0

def cd_tick(aadhaar, limited=False):
    with cooldown_lock:
        now = datetime.now()
        e = cooldowns.get(aadhaar, {"n": 0, "until": None, "last": None})
        if e["last"] and (now - e["last"]).total_seconds() > 86400:
            e = {"n": 0, "until": None, "last": None}
        e["n"] += 1
        e["last"] = now
        if limited or e["n"] >= 5:
            e["until"] = now + timedelta(hours=1)
        cooldowns[aadhaar] = e

# ============================================================
#  NIC ENCRYPTION — Aadhaar → Double Base64 AES-CBC
# ============================================================
def nic_encrypt(uid: str) -> str:
    cipher = AES_NIC.new(NIC_AES_KEY, AES_NIC.MODE_CBC, NIC_AES_IV)
    ct = cipher.encrypt(pad_nic(uid.encode(), AES_NIC.block_size))
    return base64.b64encode(base64.b64encode(ct)).decode()

# ============================================================
#  UMANG ENCRYPTION — RSA + AES for Ration Card Lookup
# ============================================================
_umang_private_key = None

def _get_private_key():
    global _umang_private_key
    if _umang_private_key is None:
        _umang_private_key = load_pem_private_key(
            UMANG_PRIVATE_KEY_PEM.encode(), password=None, backend=default_backend()
        )
    return _umang_private_key

def umang_encrypt(plaintext: str) -> str:
    """RSA-OAEP + AES-256-CBC encrypt — matches Umang API format."""
    aes_key = os.urandom(32)
    iv = os.urandom(16)

    # AES-CBC encrypt
    padder = umang_padding.PKCS7(128).padder()
    padded = padder.update(plaintext.encode()) + padder.finalize()
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
    encrypted = cipher.encryptor().update(padded) + cipher.encryptor().finalize()

    # RSA-OAEP encrypt AES key + IV
    pub_key = _get_private_key().public_key()
    enc_key = pub_key.encrypt(aes_key, rsa_padding.OAEP(
        mgf=rsa_padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None
    ))
    enc_iv = pub_key.encrypt(iv, rsa_padding.OAEP(
        mgf=rsa_padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None
    ))

    return f"{base64.b64encode(enc_key).decode()}:{base64.b64encode(enc_iv).decode()}:{base64.b64encode(encrypted).decode()}"

def umang_decrypt(encrypted_str: str) -> str:
    """RSA-OAEP + AES-256-CBC decrypt — matches Umang API response format."""
    parts = encrypted_str.split(":")
    if len(parts) != 3:
        raise ValueError(f"Invalid encrypted format, got {len(parts)} parts")

    key = _get_private_key()
    aes_key = key.decrypt(base64.b64decode(parts[0]), rsa_padding.OAEP(
        mgf=rsa_padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None
    ))
    iv = key.decrypt(base64.b64decode(parts[1]), rsa_padding.OAEP(
        mgf=rsa_padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None
    ))

    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
    decrypted = cipher.decryptor().update(base64.b64decode(parts[2])) + cipher.decryptor().finalize()

    # Remove PKCS7 padding
    unpadder = umang_padding.PKCS7(128).unpadder()
    data = unpadder.update(decrypted) + unpadder.finalize()
    return data.decode()

# ============================================================
#  RANDOM IDENTITY — NIC calls only
# ============================================================
def r_imei(): return "".join(random.choices(string.digits, k=15))
def r_dev():  return "android-" + "".join(random.choices("abcdef0123456789", k=16))
def r_ua():  return random.choice([
    "Dart/3.5 (dart:io)", "Dart/3.6 (dart:io)", "Dart/3.4 (dart:io)",
    "okhttp/4.12.0", "Dalvik/2.1.0 (Linux; Android 14; Pixel 8 Pro)",
])

def mask(a): return a[:3] + "****" + a[-2:] if len(a) >= 6 else a

# ============================================================
#  STEP 1: NIC — Aadhaar → Ration Card Number
# ============================================================
def step1_nic_verify(aadhaar: str) -> dict:
    w = cd_check(aadhaar)
    if w:
        return {"success": False, "rationCardNumber": None, "message": f"Cooldown {w}min", "cooldown": True}

    for attempt in range(2):
        headers = {
            "User-Agent": r_ua(), "Accept": "application/json",
            "Accept-Encoding": "gzip", "Content-Type": "application/json",
            "language": "en", "userid": "", "authorization": "Bearer",
            "key": NIC_API_KEY, "imeiNo": r_imei(), "deviceId": r_dev(),
        }
        payload = {"aadharNumber": nic_encrypt(aadhaar), "forceUpdate": ""}
        try:
            resp = requests.post(NIC_URL, data=json.dumps(payload), headers=headers, timeout=20)
            data = resp.json()
            msg = data.get("message", "").lower()
            limited = any(kw in msg for kw in ["limit", "exceeded"])
            cd_tick(aadhaar, limited)
            if not data.get("success") and "went wrong" in msg and attempt < 1:
                time.sleep(2)
                continue
            return {
                "success": data.get("success", False),
                "rationCardNumber": (data.get("data") or {}).get("rationCardNumber"),
                "txnId": (data.get("data") or {}).get("txnId"),
                "message": data.get("message", ""),
                "cooldown": limited,
            }
        except Exception as e:
            if attempt < 1:
                time.sleep(2)
                continue
            return {"success": False, "rationCardNumber": None, "message": str(e)[:200], "cooldown": False}
    return {"success": False, "rationCardNumber": None, "message": "Max retries", "cooldown": False}

# ============================================================
#  STEP 2: Umang — Ration Card Number → Full Details
# ============================================================
def step2_umang_details(ration_card_number: str) -> dict:
    """Encrypted call to Umang API — returns full ration card details."""
    req_body = {
        "id": str(ration_card_number),
        "userName": "umang",
        "idType": "R",
        "token": "Um@93259@",
        "sessionId": str(int(time.time() * 1000)) + uuid.uuid4().hex[:8],
        "tkn": "du0e9f52a2-6bb7-4282-af99-5328f702538e/2",
        "trkr": "213132",
        "lang": "en",
        "lat": "21",
        "lon": "90",
        "lac": "90",
        "usag": "90",
        "apitrkr": "123234",
        "usrid": "test_user_123",
        "mode": "web",
        "pltfrm": "web",
        "did": "123234",
        "deptid": "317",
        "formtrkr": "0",
        "srvid": "1519",
        "subsid": "0",
        "subsid2": "0"
    }

    for attempt in range(2):
        try:
            encrypted_body = umang_encrypt(json.dumps(req_body))
            resp = requests.post(UMANG_URL, data=encrypted_body, headers=UMANG_HEADERS, timeout=40)

            if resp.status_code != 200:
                if attempt < 1:
                    time.sleep(3)
                    continue
                return {"success": False, "message": f"Umang HTTP {resp.status_code}", "raw": resp.text[:300]}

            decrypted = umang_decrypt(resp.text)
            data = json.loads(decrypted)

            # Extract meaningful fields
            inner = data.get("data", data)
            return {
                "success": True,
                "headOfFamily": inner.get("headOfFamily") or inner.get("hofName") or inner.get("name"),
                "cardType": inner.get("cardType") or inner.get("type"),
                "state": inner.get("state") or inner.get("stateName"),
                "district": inner.get("district") or inner.get("districtName"),
                "block": inner.get("block") or inner.get("taluka") or inner.get("tehsil"),
                "village": inner.get("village") or inner.get("ward"),
                "fpsId": inner.get("fpsId") or inner.get("fpsCode") or inner.get("shopNo"),
                "fpsName": inner.get("fpsName") or inner.get("shopName") or inner.get("dealerName"),
                "familyMembers": inner.get("familyMembers") or inner.get("members") or inner.get("memberList") or [],
                "entitlement": inner.get("entitlements") or inner.get("monthlyQuota") or inner.get("entitlement") or {},
                "lastTransaction": inner.get("lastTransaction") or inner.get("lastTxnDate"),
                "raw": data
            }
        except Exception as e:
            if attempt < 1:
                time.sleep(3)
                continue
            return {"success": False, "message": f"Umang error: {str(e)[:200]}"}
    return {"success": False, "message": "Max retries"}

# ============================================================
#  FULL PIPELINE: Aadhaar → Full Ration Details
# ============================================================
def full_lookup(aadhaar: str) -> dict:
    result = {"aadhaar": mask(aadhaar)}

    # Step 1: NIC verify
    s1 = step1_nic_verify(aadhaar)
    result.update({
        "step1_success": s1["success"],
        "rationCardNumber": s1.get("rationCardNumber"),
        "txnId": s1.get("txnId"),
        "verify_message": s1.get("message"),
        "cooldown": s1.get("cooldown", False),
    })

    if not s1["success"] or not s1.get("rationCardNumber"):
        result["success"] = False
        result["message"] = s1.get("message", "Aadhaar verification failed")
        return result

    # Step 2: Umang details
    s2 = step2_umang_details(s1["rationCardNumber"])
    result.update({
        "step2_success": s2["success"],
        "headOfFamily": s2.get("headOfFamily"),
        "cardType": s2.get("cardType"),
        "state": s2.get("state"),
        "district": s2.get("district"),
        "block": s2.get("block"),
        "village": s2.get("village"),
        "fpsId": s2.get("fpsId"),
        "fpsName": s2.get("fpsName"),
        "familyMembers": s2.get("familyMembers", []),
        "familyCount": len(s2.get("familyMembers", [])),
        "entitlement": s2.get("entitlement", {}),
        "lastTransaction": s2.get("lastTransaction"),
        "raw_ration_data": s2.get("raw"),
    })

    result["success"] = s2["success"]
    result["message"] = "Full ration details retrieved" if s2["success"] else s2.get("message", "Ration lookup failed")
    return result

# ============================================================
#  BULK ENGINE
# ============================================================
def bulk_full_lookup(aadhaars: list) -> dict:
    clean = [str(a).strip() for a in aadhaars if str(a).strip().isdigit() and len(str(a).strip()) == 12]
    bad = [{"aadhaar": mask(str(a)), "success": False, "message": "Invalid format"}
           for a in aadhaars if not (str(a).strip().isdigit() and len(str(a).strip()) == 12)]

    results = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {}
        for i, a in enumerate(clean):
            if i > 0: time.sleep(STAGGER)
            futures[ex.submit(full_lookup, a)] = a
        for f in as_completed(futures):
            try: results.append(f.result())
            except: results.append({"aadhaar": mask(futures[f]), "success": False, "message": "Thread error"})

    results.extend(bad)
    results.sort(key=lambda r: (not r.get("success"), not r.get("cooldown")))
    return {
        "success": True,
        "total": len(aadhaars),
        "hits": sum(1 for r in results if r.get("success")),
        "cooldowns": sum(1 for r in results if r.get("cooldown")),
        "misses": sum(1 for r in results if not r.get("success") and not r.get("cooldown")),
        "time_seconds": round(time.time() - t0, 2),
        "results": results,
    }

# ============================================================
#  REQUEST EXTRACTORS
# ============================================================
def get_aadhaar():
    a = request.args.get("aadhaar", "").strip()
    if a: return a
    body = request.get_json(silent=True) or {}
    a = str(body.get("aadhaar", "")).strip()
    return a if a else None

def get_aadhaars():
    q = request.args.get("aadhaars", "").strip()
    if q: return [x.strip() for x in q.split(",") if x.strip()]
    body = request.get_json(silent=True) or {}
    arr = body.get("aadhaars", [])
    if arr and isinstance(arr, list): return [str(x).strip() for x in arr]
    return None

def get_card():
    c = request.args.get("card", "").strip()
    if c: return c
    body = request.get_json(silent=True) or {}
    c = str(body.get("card", "")).strip()
    return c if c else None

# ============================================================
#  ROUTES
# ============================================================
@app.route("/", methods=["GET"])
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "service": "Aadhaar → Full Ration Details — Unified API v10.0",
        "pipeline": "NIC (Aadhaar→RC#) + Umang (RC#→Family+FPS+Quota)",
        "endpoints": {
            "single_full_GET":  "/api?aadhaar=427333287607",
            "single_full_POST": "/api/aadhaar  {\"aadhaar\":\"427333287607\"}",
            "bulk_full_GET":    "/api/bulk?aadhaars=xxx,yyy,zzz",
            "bulk_full_POST":   "/api/bulk  {\"aadhaars\":[\"xxx\",\"yyy\"]}",
            "ration_direct_GET": "/api/ration?card=110003015026710",
            "verify_only":      "/api/verify?aadhaar=427333287607",
        },
    })

# ── Full Pipeline (Aadhaar → Everything) ──
@app.route("/api", methods=["GET"])
@app.route("/api/aadhaar", methods=["POST"])
@app.route("/api/aadhaar-lookup", methods=["GET", "POST"])
def single_full():
    a = get_aadhaar()
    if not a or not (a.isdigit() and len(a) == 12):
        return jsonify({"success": False, "message": "12-digit Aadhaar required. GET: ?aadhaar=  POST: {\"aadhaar\":}"}), 400
    result = full_lookup(a)
    code = 200 if result.get("success") else (429 if result.get("cooldown") else 502)
    return jsonify(result), code

# ── Bulk Full Pipeline ──
@app.route("/api/bulk", methods=["GET", "POST"])
@app.route("/api/bulk-aadhaar-lookup", methods=["GET", "POST"])
def bulk_full():
    arr = get_aadhaars()
    if not arr: return jsonify({"success": False, "message": "Provide ?aadhaars=a,b,c or {\"aadhaars\":[...]}"}), 400
    if len(arr) > BATCH_SIZE: return jsonify({"success": False, "message": f"Max {BATCH_SIZE}"}), 400
    return jsonify(bulk_full_lookup(arr))

# ── Direct Ration Card Lookup (Umang only, no Aadhaar needed) ──
@app.route("/api/ration", methods=["GET", "POST"])
def ration_direct():
    card = get_card()
    if not card:
        return jsonify({"success": False, "message": "Provide ration card number. GET: ?card=  POST: {\"card\":}"}), 400
    result = step2_umang_details(card)
    return jsonify({"rationCardNumber": card, **result}), 200 if result["success"] else 502

# ── Verify Only (Step 1, no Umang) ──
@app.route("/api/verify", methods=["GET", "POST"])
def verify_only():
    a = get_aadhaar()
    if not a or not (a.isdigit() and len(a) == 12): return jsonify({"success": False}), 400
    s1 = step1_nic_verify(a)
    return jsonify({"aadhaar": mask(a), **s1})

# ============================================================
#  MAIN
# ============================================================
if __name__ == "__main__":
    print(r"""
╔══════════════════════════════════════════════════════════════╗
║  🪪  Unified Ration API v10.0                              ║
║                                                            ║
║  Pipeline: Aadhaar → Ration# → Family + FPS + Entitlement  ║
║                                                            ║
║  GET  /api?aadhaar=427333287607                            ║
║  POST /api/aadhaar  {"aadhaar":"427333287607"}             ║
║  GET  /api/bulk?aadhaars=xxx,yyy                           ║
║  POST /api/bulk  {"aadhaars":["xxx","yyy"]}                ║
║  GET  /api/ration?card=110003015026710                     ║
║  GET  /api/verify?aadhaar=427333287607                     ║
║                                                            ║
║  http://0.0.0.0:5000                                       ║
╚══════════════════════════════════════════════════════════════╝
""")
    app.run(host="0.0.0.0", port=5000, debug=False)