#!/usr/bin/env python3
"""Check the mail settings in .env, then restart the API so they take effect.

    scripts/mailcheck.py            check the credentials, restart if they work
    scripts/mailcheck.py --send     also put a real test message through
    scripts/mailcheck.py --dry-run  check only, never restart

The order matters. The credentials are tested *before* the service is
restarted, so a mistyped password fails here and the site carries on running
with the settings it already has. Restarting first and finding out afterwards
means the contact form is broken for however long it takes to notice.

Run it after any change to the mail lines in .env. The application reads that
file once at startup, so an edit does nothing at all until something
restarts - which is the trap this exists to close.
"""

from __future__ import annotations

import argparse
import smtplib
import subprocess
import sys
import time
from email.mime.text import MIMEText
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERVICE = "fleminganalytic"

OK, BAD, INFO = "\033[32m✓\033[0m", "\033[31m✗\033[0m", "\033[2m·\033[0m"


def settings() -> dict:
    """The same resolution order main.py uses, so this tests what will run."""
    from dotenv import dotenv_values

    env = dotenv_values(ROOT / ".env")
    get = lambda *names: next((env[n] for n in names if env.get(n)), None)
    return {
        "host": get("SMTP_HOST", "ZEPTO_SERVER") or "smtp.gmail.com",
        "port": int(get("SMTP_PORT", "ZEPTO_PORT") or 587),
        "user": get("SMTP_USER", "ZEPTO_USER") or "",
        "password": get("SMTP_PASSWORD", "EMAIL_PWD"),
        "to": get("CONTACT_TO") or "",
        "sender": get("CONTACT_FROM") or "",
    }


def check_auth(s: dict) -> tuple[bool, str]:
    if not s["password"]:
        return False, "no password set (SMTP_PASSWORD or EMAIL_PWD)"
    if not s["user"]:
        return False, "no username set (SMTP_USER)"
    try:
        with smtplib.SMTP(s["host"], s["port"], timeout=25) as server:
            server.starttls()
            server.login(s["user"], s["password"])
        return True, f"{s['host']}:{s['port']} accepted {s['user']}"
    except smtplib.SMTPAuthenticationError as exc:
        detail = exc.smtp_error.decode(errors="replace")[:120]
        return False, f"rejected: {exc.smtp_code} {detail}"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {str(exc)[:120]}"


def send_test(s: dict) -> tuple[bool, str]:
    msg = MIMEText("Sent by scripts/mailcheck.py to confirm delivery works. "
                   "Nothing is wrong; this message is the test.")
    msg["Subject"] = "Fleming Analytic — mail check"
    msg["From"] = s["sender"] or s["user"]
    msg["To"] = s["to"] or s["user"]
    try:
        with smtplib.SMTP(s["host"], s["port"], timeout=30) as server:
            server.starttls()
            server.login(s["user"], s["password"])
            server.send_message(msg)
        return True, f"delivered to {msg['To']}"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {str(exc)[:120]}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--send", action="store_true", help="also send a real test message")
    ap.add_argument("--dry-run", action="store_true", help="check only, do not restart")
    args = ap.parse_args()

    s = settings()
    print(f"\n  host     {s['host']}:{s['port']}")
    print(f"  user     {s['user'] or '(unset)'}")
    print(f"  password {'<' + str(len(s['password'])) + ' chars>' if s['password'] else '(unset)'}")
    print(f"  to       {s['to'] or '(unset)'}\n")

    good, detail = check_auth(s)
    print(f"  {OK if good else BAD} auth  {detail}")
    if not good:
        print(f"\n  {INFO} nothing restarted. The site keeps running on its current "
              f"settings,\n    so fix .env and run this again.\n")
        return 1

    if args.send:
        sent, detail = send_test(s)
        print(f"  {OK if sent else BAD} send  {detail}")
        if not sent:
            return 1

    if args.dry_run:
        print(f"\n  {INFO} --dry-run: not restarting. Run without it to apply.\n")
        return 0

    print(f"  {INFO} restarting {SERVICE}…")
    r = subprocess.run(["systemctl", "restart", SERVICE], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  {BAD} restart failed: {r.stderr.strip()[:160]}\n")
        return 1

    # Being "active" the instant after a restart is not the same as being able
    # to serve; wait for the process to finish importing before saying so.
    for _ in range(20):
        time.sleep(1)
        active = subprocess.run(["systemctl", "is-active", "--quiet", SERVICE]).returncode == 0
        if not active:
            print(f"  {BAD} {SERVICE} did not stay up — check: journalctl -u {SERVICE} -n 40\n")
            return 1
        try:
            import urllib.request
            urllib.request.urlopen("http://127.0.0.1/", timeout=2)
        except Exception:
            pass
        break

    print(f"  {OK} {SERVICE} restarted and running\n")
    print(f"  {INFO} the new settings are live.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
