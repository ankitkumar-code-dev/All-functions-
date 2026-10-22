import base64, json, os, random, requests
from flask import Flask, request, jsonify
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# ---------- RSA Keys ----------
PUB_B64 = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEArpgmSqIv/3zYAxoNK/6eLqjeBEHFsiGJCia5wdQuhCw54ceg6EyKc5mPrkEnK7CYgbJxSQO37HbnWIROMN6kRQqxa1kZFFS+xQPZ9z4Gs+njypX8HNKcse2/kbwbIX4y8kcCENVVOV8URK8+znEsuN/UCzJXv2Pg0KII5ofb8wAvYNXkZ44DhcWnyxO6JohbuMvpt096NBkdq8lWtRrappL3HqpTG4Fd5H4v9b7fD8rAhBB8cAbiM2nyBz51VDovS/SZheIemKjwGLGMDiMeNcQGryOTZASX+jxe69NoFR9bQ8+5jN/88x5k53UzV8en+HRKbYjgUJzZOVfu3fL/WQIDAQAB"
PRIV_B64 = "MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCumCZKoi//fNgDGg0r/p4uqN4EQcWyIYkKJrnB1C6ELDnhx6DoTIpzmY+uQScrsJiBsnFJA7fsdudYhE4w3qRFCrFrWRkUVL7FA9n3Pgaz6ePKlfwc0pyx7b+RvBshfjLyRwIQ1VU5XxRErz7OcSy439QLMle/Y+DQogjmh9vzAC9g1eRnjgOFxafLE7omiFu4y+m3T3o0GR2ryVa1GtqmkvceqlMbgV3kfi/1vt8PysCEEHxwBuIzafIHPnVUOi9L9JmF4h6YqPAYsYwOIx41xAavI5NkBJf6PF7r02gVH1tDz7mM3/zzHmTndTNXx6f4dEptiOBQnNk5V+7d8v9ZAgMBAAECggEActY8iWZ4L5GL+y5Nb5x/qq0DqsUgJXQNURH7qFPJbMIyKCFH4sNFZZehe7n666+x/8zA2oeJmAz1SbFsRJSMc6T+4V6vMkIzYB6SZR71Ba1XWM6iDsswqY95K4AQUE1TcSvnXe8TqTKygCLMKrkh80+1hs/MC2TEYDXTqN2/e+qOBq6/RQ4A7E+Qd1R6/mFEHZJfmvMVl0lBmowHk060/JAgeSxE5VPnP2pQXad21w/nBtSoQDOKpAzbcSIgn4vLavtUlS87XYQ8bq3Mc4sPQe9RZ9o89aQrau0SmdgNeGYVi0tWhP2lm3b8C3XcgDQi6LwnZpzwCo9m5fEcJM4IyQKBgQD//t26TkBC2h4trvbOID2SN2hPiBySxjb3Eoaiy58ryF/d4Im56Xf61ksuy0od52vgNzW03As6vPjTJpqy/EeJrOZHLdZSOiFZzqcgXUcir2O6gM/WIU/0x/Ge7nnp0DfwTYgTNzpJA+csR9aDFhOu9e+xogJ0lV4eCEBjjC+Q+wKBgQCumOxDZkaH9uuXSbrGTsrEMO0439oLM+Er6L+Pdpy8qY0Q5ZYp2C1ZZBz8DwH6NwwKY/JcvrVVS5D90mmqsm39ubeIrmv7C04TWBQqYRp9dgRkUkVo9BGM6EqA2q/D2JT/sr/72h5FEsMblHSVEXbCo/QLYvCglxSs7jhx5tDIuwKBgQC/W2epJWc50cvvQDNzP3xm+Q37LXaWbJ6Xr/x+YpFX7A9lTrwFAbVTBq7qisGbeusTjpGR4U5vmOSzCc9n7dcX3evA102254cYl7YsJi3PiqWUu0cg/IPFKVS/BeqR0biO45XNL2JdRBKg8g4yrOUHywVilgUZ2rGg53AiOZ8w0wKBgQCpby/AjI0fvwiLrXo6nhX55H0hd2LTAkqe4OSdJX8fOu7xmctq2iXQHO5f0XSazDa8EpgNVukEWCvhlgMDKtrAoiyw0ItreWIQNaaEJe2eGRxT+t7u5gPuGTLL7u0pApI9vcq/bsF3SKjcp+mnC+aTJqZbMm3Pei4PT7KpHlQ4pwKBgDeLXCwO6cCa+4nV4t5ktCEzQPiu/yEMAL0hf3RwPr7WuckwyHm3cUt7DFCEf6+bJj+hpxVXGcdgVxDZjyh4s8YE8AAd+2iv8I61gF475KAOOMbkt21TzTI0y2R2BN3JvB1iTmf6CkV6C82b4UELlKjEOX342756ZWQbhB8Yld1T"

_pub = serialization.load_der_public_key(base64.b64decode(PUB_B64))
_priv = serialization.load_der_private_key(base64.b64decode(PRIV_B64), None)
_OAEP = padding.OAEP(padding.MGF1(hashes.SHA256()), hashes.SHA256(), None)


def enc_triple(obj: dict) -> str:
    pt = json.dumps(obj, separators=(",", ":")).encode()
    pad = 16 - len(pt) % 16
    pt += bytes([pad]) * pad
    k, iv = os.urandom(32), os.urandom(16)
    e = Cipher(algorithms.AES(k), modes.CBC(iv)).encryptor()
    ct = e.update(pt) + e.finalize()
    ek = _pub.encrypt(k, _OAEP)
    eiv = _pub.encrypt(iv, _OAEP)
    return (
        base64.b64encode(ek).decode() + ":"
        + base64.b64encode(eiv).decode() + ":"
        + base64.b64encode(ct).decode()
    )


def dec_triple(blob: str) -> str:
    blob = blob.strip()
    if blob.startswith('"') and blob.endswith('"'):
        blob = json.loads(blob)
    a, b, c = [base64.b64decode(p) for p in blob.split(":")]
    k = _priv.decrypt(a, _OAEP)
    iv = _priv.decrypt(b, _OAEP)
    d = Cipher(algorithms.AES(k), modes.CBC(iv)).decryptor()
    pt = d.update(c) + d.finalize()
    return (pt[:-pt[-1]]).decode()


UMANG_URL = "https://apigw.umangapp.in/onorcApi/ws1/getrationcard"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Mobile Safari/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "subsid": "0",
    "deptid": "317",
    "tenantid": "",
    "formtrkr": "0",
    "x-api-key": "VKE9PnbY5k1ZYapR5PyYQ33I26sXTX569Ed7eqyg",
    "srvid": "1519",
    "subsid2": "0",
    "origin": "https://web.umang.gov.in",
    "referer": "https://web.umang.gov.in/",
}


def fetch_ration(rc_id: str):
    sess = "".join(str(random.randint(0, 9)) for _ in range(15))
    payload_obj = {
        "tkn": "uk7643bdc3-049e-440d-822b-7c4266e5106c/1",
        "trkr": "213132",
        "lang": "en",
        "lat": "21",
        "lon": "90",
        "lac": "90",
        "usag": "90",
        "apitrkr": "123234",
        "usrid": "4092833136",
        "mode": "web",
        "pltfrm": "android",
        "did": "123234",
        "deptid": "317",
        "formtrkr": "0",
        "srvid": "1519",
        "subsid": "0",
        "subsid2": "0",
        "id": str(rc_id),
        "sessionId": sess,
        "userName": "umang",
        "idType": "R",
        "token": "Um@93259@",
    }
    encrypted = enc_triple(payload_obj)
    r = requests.post(UMANG_URL, data=encrypted, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return json.loads(dec_triple(r.text))


# ---------- Flask App ----------
app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": True,
        "message": "Ration to info API is live 🚀",
        "endpoints": {
            "/ration?info=<ration_id>": "Get ration card details by ID"
        },
        "example": "/ration?info=219541296139"
    })


@app.route("/ration", methods=["GET"])
def ration():
    rc_id = (
        request.args.get("info")
        or request.args.get("id")
        or request.args.get("ration_id")
    )
    if not rc_id:
        return jsonify({
            "status": False,
            "error": "Missing 'info' query parameter",
            "example": "/ration?info=219541296139"
        }), 400

    try:
        data = fetch_ration(rc_id.strip())
        return jsonify({
            "status": True,
            "ration_id": rc_id,
            "data": data
        })
    except requests.exceptions.HTTPError as e:
        return jsonify({
            "status": False,
            "error": f"Upstream HTTP error: {e}",
            "ration_id": rc_id
        }), 502
    except requests.exceptions.RequestException as e:
        return jsonify({
            "status": False,
            "error": f"Network error: {e}",
            "ration_id": rc_id
        }), 502
    except Exception as e:
        return jsonify({
            "status": False,
            "error": str(e),
            "ration_id": rc_id
        }), 500


# ---------- Local / Termux run ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)