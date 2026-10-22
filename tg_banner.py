#!/usr/bin/env python3
"""
tg_banner.py  —  Telegram account mass-report banner

Subcommands:
  add-session                     interactively log in and save a session file
  list-sessions                   show all saved sessions
  report  --target <user>         mass-report a target across all saved sessions
           [--reason <reason>]
           [--message <text>]
           [--rounds <n>]
           [--delay <s>]
           [--sessions <file1,file2,...>]

Report reasons:
  spam | violence | porn | drugs | personal | child | fake | other

Example:
  python3 tg_banner.py add-session
  python3 tg_banner.py report --target @target_user --reason spam --rounds 3
"""

import os, sys, json, asyncio, argparse, time, re
from pathlib import Path
from datetime import datetime

try:
    from telethon import TelegramClient, errors
    from telethon.tl.functions.account import ReportPeerRequest
    from telethon.tl.functions.contacts import ResolveUsernameRequest
    from telethon.tl.types import (
        InputReportReasonSpam,
        InputReportReasonViolence,
        InputReportReasonPornography,
        InputReportReasonIllegalDrugs,
        InputReportReasonPersonalDetails,
        InputReportReasonChildAbuse,
        InputReportReasonOther,
        InputReportReasonFake,
    )
except ImportError:
    print("[-] Run:  pip install telethon")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────────────────────────────────────
SESSIONS_DIR  = Path("sessions")
CONFIG_FILE   = Path("api_config.json")

REASONS = {
    "spam":     InputReportReasonSpam(),
    "violence": InputReportReasonViolence(),
    "porn":     InputReportReasonPornography(),
    "drugs":    InputReportReasonIllegalDrugs(),
    "personal": InputReportReasonPersonalDetails(),
    "child":    InputReportReasonChildAbuse(),
    "fake":     InputReportReasonFake(),
    "other":    InputReportReasonOther(),
}

# ─────────────────────────────────────────────────────────────────────────────
#  COLOR OUTPUT
# ─────────────────────────────────────────────────────────────────────────────
class C:
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    BOLD   = "\033[1m"
    RESET  = "\033[0m"

def ok(msg):    print(f"{C.GREEN}[+]{C.RESET} {msg}")
def err(msg):   print(f"{C.RED}[-]{C.RESET} {msg}")
def info(msg):  print(f"{C.CYAN}[*]{C.RESET} {msg}")
def warn(msg):  print(f"{C.YELLOW}[!]{C.RESET} {msg}")

BANNER = f"""{C.BOLD}{C.CYAN}
  ████████╗ ██████╗     ██████╗  █████╗ ███╗  ██╗███╗  ██╗███████╗██████╗
     ██╔══╝██╔════╝     ██╔══██╗██╔══██╗████╗ ██║████╗ ██║██╔════╝██╔══██╗
     ██║   ██║  ███╗    ██████╦╝███████║██╔██╗██║██╔██╗██║█████╗  ██████╔╝
     ██║   ██║   ██║    ██╔══██╗██╔══██║██║╚████║██║╚████║██╔══╝  ██╔══██╗
     ██║   ╚██████╔╝    ██████╦╝██║  ██║██║ ╚███║██║ ╚███║███████╗██║  ██║
     ╚═╝    ╚═════╝     ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚══╝╚═╝  ╚══╝╚══════╝╚═╝  ╚═╝
{C.RESET}"""

# ─────────────────────────────────────────────────────────────────────────────
#  API CREDENTIALS
# ─────────────────────────────────────────────────────────────────────────────
def load_api_config() -> tuple[int, str]:
    """
    Load API_ID / API_HASH from api_config.json.
    If not found, prompt user to create one.
    Get yours at: https://my.telegram.org/apps
    """
    if CONFIG_FILE.exists():
        cfg = json.loads(CONFIG_FILE.read_text())
        return int(cfg["api_id"]), cfg["api_hash"]

    print(f"\n{C.YELLOW}[!] No api_config.json found.{C.RESET}")
    print("    Get your API credentials at: https://my.telegram.org/apps\n")
    api_id   = input("    API_ID   : ").strip()
    api_hash = input("    API_HASH : ").strip()
    cfg = {"api_id": int(api_id), "api_hash": api_hash}
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))
    ok(f"Saved to {CONFIG_FILE}")
    return int(api_id), api_hash

# ─────────────────────────────────────────────────────────────────────────────
#  SESSION MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────
async def cmd_add_session(args):
    """Interactively add a new Telegram session."""
    api_id, api_hash = load_api_config()
    SESSIONS_DIR.mkdir(exist_ok=True)

    phone = input("\n  Phone number (intl format, e.g. +12125550100): ").strip()
    safe  = re.sub(r"[^\d]", "", phone)
    sess  = SESSIONS_DIR / safe

    client = TelegramClient(str(sess), api_id, api_hash)
    await client.start(phone=phone)

    me = await client.get_me()
    ok(f"Logged in as: {me.first_name} ({me.username or 'no username'})")
    await client.disconnect()
    ok(f"Session saved: {sess}.session")


def cmd_list_sessions(args):
    """Print all saved .session files."""
    SESSIONS_DIR.mkdir(exist_ok=True)
    files = list(SESSIONS_DIR.glob("*.session"))
    if not files:
        warn("No sessions found. Run: python3 tg_banner.py add-session")
        return
    info(f"{len(files)} session(s):")
    for f in files:
        size = f.stat().st_size
        print(f"  {C.GREEN}•{C.RESET} {f.stem:<20s}  ({size:,} bytes)")


def get_all_sessions() -> list[Path]:
    SESSIONS_DIR.mkdir(exist_ok=True)
    return list(SESSIONS_DIR.glob("*.session"))

# ─────────────────────────────────────────────────────────────────────────────
#  CORE — single-account report worker
# ─────────────────────────────────────────────────────────────────────────────
async def report_worker(
    session_path: Path,
    api_id: int,
    api_hash: str,
    target: str,
    reason_obj,
    message: str,
    rounds: int,
    delay: float,
    results: dict,
):
    label = session_path.stem
    client = TelegramClient(str(session_path), api_id, api_hash)

    try:
        await client.connect()
        if not await client.is_user_authorized():
            err(f"[{label}] not authorized — run add-session first")
            results[label] = {"ok": 0, "fail": 1, "error": "not authorized"}
            return

        # resolve target once
        target_clean = target.lstrip("@")
        try:
            resolved = await client(ResolveUsernameRequest(target_clean))
            peer = resolved.users[0] if resolved.users else resolved.chats[0]
        except Exception as e:
            err(f"[{label}] cannot resolve '{target}': {e}")
            results[label] = {"ok": 0, "fail": rounds, "error": str(e)}
            return

        ok_count = fail_count = 0

        for r in range(1, rounds + 1):
            try:
                result = await client(ReportPeerRequest(
                    peer    = peer,
                    reason  = reason_obj,
                    message = message,
                ))
                if result:
                    ok_count += 1
                    print(f"  {C.GREEN}✓{C.RESET} [{label}] round {r}/{rounds}")
                else:
                    fail_count += 1
                    print(f"  {C.YELLOW}?{C.RESET} [{label}] round {r}/{rounds} — returned False")

            except errors.FloodWaitError as e:
                warn(f"[{label}] FloodWait {e.seconds}s — sleeping...")
                await asyncio.sleep(e.seconds + 2)
                fail_count += 1

            except errors.PeerIdInvalidError:
                err(f"[{label}] PeerIdInvalid — cannot report this target")
                fail_count += rounds - r + 1
                break

            except errors.UserPrivacyRestrictedError:
                err(f"[{label}] UserPrivacyRestricted — target has privacy lock")
                fail_count += rounds - r + 1
                break

            except Exception as e:
                err(f"[{label}] round {r} failed: {e}")
                fail_count += 1

            if r < rounds and delay > 0:
                await asyncio.sleep(delay)

        results[label] = {"ok": ok_count, "fail": fail_count}

    finally:
        await client.disconnect()

# ─────────────────────────────────────────────────────────────────────────────
#  CORE — multi-account orchestrator
# ─────────────────────────────────────────────────────────────────────────────
async def cmd_report(args):
    api_id, api_hash = load_api_config()

    # ── pick sessions ─────────────────────────────────────────────────────
    if args.sessions:
        session_paths = [SESSIONS_DIR / (s.strip() + ".session")
                         for s in args.sessions.split(",")]
        session_paths = [p for p in session_paths if p.exists()]
    else:
        session_paths = get_all_sessions()

    if not session_paths:
        err("No sessions available. Run: python3 tg_banner.py add-session")
        sys.exit(1)

    reason_key = (args.reason or "spam").lower()
    if reason_key not in REASONS:
        err(f"Unknown reason '{reason_key}'. Valid: {', '.join(REASONS)}")
        sys.exit(1)

    reason_obj = REASONS[reason_key]
    message    = args.message or ""
    rounds     = max(1, args.rounds)
    delay      = max(0.0, args.delay)
    target     = args.target

    total_possible = len(session_paths) * rounds

    print(BANNER)
    info(f"Target      : {C.BOLD}{target}{C.RESET}")
    info(f"Reason      : {C.BOLD}{reason_key}{C.RESET}")
    info(f"Rounds/acct : {C.BOLD}{rounds}{C.RESET}")
    info(f"Delay/round : {C.BOLD}{delay}s{C.RESET}")
    info(f"Sessions    : {C.BOLD}{len(session_paths)}{C.RESET}")
    info(f"Max reports : {C.BOLD}{total_possible}{C.RESET}")
    print()

    results: dict = {}
    start = time.time()

    # ── run all accounts concurrently ─────────────────────────────────────
    tasks = [
        report_worker(
            session_path = sp,
            api_id       = api_id,
            api_hash     = api_hash,
            target       = target,
            reason_obj   = reason_obj,
            message      = message,
            rounds       = rounds,
            delay        = delay,
            results      = results,
        )
        for sp in session_paths
    ]

    await asyncio.gather(*tasks)

    # ── summary ───────────────────────────────────────────────────────────
    elapsed   = time.time() - start
    total_ok  = sum(v["ok"]   for v in results.values())
    total_err = sum(v["fail"] for v in results.values())

    print()
    print(f"{'═' * 55}")
    info(f"Done in {elapsed:.1f}s")
    ok(f"Reports sent : {C.BOLD}{total_ok}{C.RESET}")
    if total_err:
        err(f"Failed       : {C.BOLD}{total_err}{C.RESET}")

    print()
    print(f"  {'SESSION':<22}  {'OK':>4}  {'FAIL':>4}")
    print(f"  {'─'*22}  {'─'*4}  {'─'*4}")
    for label, v in sorted(results.items()):
        col = C.GREEN if v['fail'] == 0 else (C.YELLOW if v['ok'] > 0 else C.RED)
        print(f"  {col}{label:<22}{C.RESET}  {v['ok']:>4}  {v['fail']:>4}")
    print(f"{'═' * 55}")

# ─────────────────────────────────────────────────────────────────────────────
#  ARGPARSE + ENTRY
# ─────────────────────────────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="tg_banner.py",
        description="Telegram mass-report banner",
    )
    sub = p.add_subparsers(dest="command")

    # add-session
    sub.add_parser("add-session",
                   help="log in and save a new session file")

    # list-sessions
    sub.add_parser("list-sessions",
                   help="show all saved sessions")

    # report
    rp = sub.add_parser("report",
                        help="mass-report a target account")
    rp.add_argument("--target",   required=True,
                    help="@username or user ID to report")
    rp.add_argument("--reason",   default="spam",
                    choices=list(REASONS.keys()),
                    help="report reason (default: spam)")
    rp.add_argument("--message",  default="",
                    help="optional message to include in report")
    rp.add_argument("--rounds",   type=int, default=1,
                    help="reports per account (default: 1)")
    rp.add_argument("--delay",    type=float, default=1.0,
                    help="seconds between rounds per account (default: 1.0)")
    rp.add_argument("--sessions", default=None,
                    help="comma-separated session names to use (default: all)")

    return p


def main():
    parser = build_parser()
    args   = parser.parse_args()

    if args.command == "add-session":
        asyncio.run(cmd_add_session(args))

    elif args.command == "list-sessions":
        cmd_list_sessions(args)

    elif args.command == "report":
        asyncio.run(cmd_report(args))

    else:
        print(BANNER)
        parser.print_help()


if __name__ == "__main__":
    main()
