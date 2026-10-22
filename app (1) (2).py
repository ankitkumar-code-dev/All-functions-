import argparse
import base64
import json
import os
import re
import sys

import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad


BASE         = "https://sederp.educationportal3.in"
LOGIN_PAGE   = f"{BASE}/UserLogin/Login"
CAPTCHA_URL  = f"{BASE}/UserLogin/GetCaptchaImage"
CREDS_URL    = f"{BASE}/UserLogin/GetUserCredentials"
POST_URL     = BASE
SAMAGRA_URL  = f"{BASE}/StudentRegistration/GetSamagraData"

DEFAULT_EMAIL    = "23300606508"
DEFAULT_PASSWORD = "Abc@1234"
DEFAULT_SAMAGRA  = "172922998"

COOKIE_FILE = "session_dump/cookies.json"
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36")

COMMON_HEADERS = {
    "User-Agent": UA,
    "Accept-Language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7,hi;q=0.6",
    "sec-ch-ua": '"Chromium";v="152", "Not?A_Brand";v="24", "Google Chrome";v="152"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
}

RVT_RE = re.compile(
    r'name="__RequestVerificationToken"[^>]*value="([^"]+)"',
    re.IGNORECASE,
)



def aes_cbc_b64(plaintext: str, key: str, iv: str) -> str:
    cipher = AES.new(key.encode("utf-8"), AES.MODE_CBC, iv.encode("utf-8"))
    ct = cipher.encrypt(pad(plaintext.encode("utf-8"), AES.block_size))
    return base64.b64encode(ct).decode("utf-8")



def _scrape_rvt(session) -> str | None:
    for url in (LOGIN_PAGE, BASE, f"{BASE}/UserLogin/Login/Index"):
        try:
            r = session.get(url, headers={
                **COMMON_HEADERS,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Upgrade-Insecure-Requests": "1",
            }, allow_redirects=True, timeout=20)
        except requests.RequestException as e:
            print(f"[!] GET {url} failed: {e}")
            continue
        m = RVT_RE.search(r.text)
        if m:
            return m.group(1)
        m2 = re.search(
            r'id="__RequestVerificationToken"[^>]*value="([^"]+)"',
            r.text, re.IGNORECASE,
        )
        if m2:
            return m2.group(1)
    return None


def _fetch_captcha(session):
    r = session.post(CAPTCHA_URL, data="", headers={
        **COMMON_HEADERS,
        "X-Requested-With": "XMLHttpRequest",
        "Origin": BASE,
        "Referer": LOGIN_PAGE,
        "Accept": "*/*",
        "Content-Length": "0",
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
    }, timeout=20)
    r.raise_for_status()
    return r.json()


def _fetch_creds(session, email: str):
    r = session.post(CREDS_URL, data={"email": email}, headers={
        **COMMON_HEADERS,
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": BASE,
        "Referer": LOGIN_PAGE,
        "Accept": "*/*",
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
    }, timeout=20)
    r.raise_for_status()
    return r.json()


def login(email: str, password: str) -> requests.Session | None:
    s = requests.Session()
    s.headers.update(COMMON_HEADERS)

    # 1. rvt
    rvt = _scrape_rvt(s)
    if not rvt:
        print("[!] rvt not found")
        return None
    print(f"[+] rvt: {rvt[:48]}...")

    # 2. captcha (cpvalue = plaintext answer)
    cap = _fetch_captcha(s)
    answer = str(cap.get("cpvalue", "")).strip()
    if not answer:
        print("[!] no cpvalue in captcha response")
        print(json.dumps(cap, indent=2)[:400])
        return None
    print(f"[+] captcha answer: {answer}")

    creds = _fetch_creds(s, email)
    print(f"[+] creds response: {creds}")
    key, iv = str(creds["key"]), str(creds["iv"])

    enc_pw  = aes_cbc_b64(password, key, iv)
    enc_cap = aes_cbc_b64(answer,   key, iv)

    r = s.post(POST_URL, data={
        "Email": email,
        "Password": enc_pw,
        "hfCaptcha": enc_cap,
        "__RequestVerificationToken": rvt,
    }, headers={
        **COMMON_HEADERS,
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "null",
        "Upgrade-Insecure-Requests": "1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": LOGIN_PAGE,
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "navigate",
        "sec-fetch-user": "?1",
        "sec-fetch-dest": "document",
    }, allow_redirects=True, timeout=30)

    print(f"[+] login status : {r.status_code}")
    print(f"[+] final url    : {r.url}")

    low = r.text.lower()
    ok = r.status_code == 200 and any(
        k in low for k in ("dashboard", "logout", "welcome", "profile", "student")
    )
    if not ok:
        print("[!] login likely FAILED — body[:600]:")
        print(r.text[:600])
        return None

    print("[+] LOGIN OK")
    _save_cookies(s)
    return s



def _save_cookies(s: requests.Session) -> None:
    os.makedirs("session_dump", exist_ok=True)
    data = {c.name: c.value for c in s.cookies}
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"[+] cookies saved -> {COOKIE_FILE}  ({len(data)} cookies)")


def _load_cookies() -> dict | None:
    if not os.path.exists(COOKIE_FILE):
        return None
    try:
        with open(COOKIE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None



def get_samagra_data(session: requests.Session, samagra_id: str) -> dict | None:
    payload = {"SamagraId": samagra_id}
    r = session.post(SAMAGRA_URL, data=json.dumps(payload), headers={
        **COMMON_HEADERS,
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Content-Type": "application/json",
        "Origin": BASE,
        "Referer": f"{BASE}/StudentRegistration/Index",
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "priority": "u=1, i",
    }, timeout=30)

    print(f"[+] samagra status: {r.status_code}")
    print(f"[+] samagra body  : {r.text[:1000]}")

    try:
        return r.json()
    except ValueError:
        return {"_raw": r.text, "_status": r.status_code}



def main():
    ap = argparse.ArgumentParser(description="SEDER login + Samagra lookup")
    ap.add_argument("samagra", nargs="?", default=DEFAULT_SAMAGRA,
                    help="Samagra ID to query")
    ap.add_argument("--email",    default=DEFAULT_EMAIL)
    ap.add_argument("--password", default=DEFAULT_PASSWORD)
    ap.add_argument("--no-login", action="store_true",
                    help="skip login, reuse cookies from session_dump/")
    ap.add_argument("--out",      default="samagra_result.json")
    args = ap.parse_args()

    s = requests.Session()
    s.headers.update(COMMON_HEADERS)

    if args.no_login:
        ck = _load_cookies()
        if not ck:
            print("[!] no saved cookies; run once with login")
            sys.exit(1)
        for k, v in ck.items():
            s.cookies.set(k, v, domain="sederp.educationportal3.in")
        print(f"[+] loaded {len(ck)} cookies from {COOKIE_FILE}")
    else:
        s = login(args.email, args.password)
        if s is None:
            sys.exit(1)

    result = get_samagra_data(s, args.samagra)
    if result is None:
        sys.exit(1)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"[+] saved -> {args.out}")


if __name__ == "__main__":
    main()