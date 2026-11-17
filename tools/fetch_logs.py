"""Download the current logs of the bot and of the web server into logs/ (read only on the server).

Usage: python tools/fetch_logs.py (settings: see deploy.py)
Old rotated logs (*.gz) stay on the server; they are rarely needed.
"""
from pathlib import Path

import httpx

from deploy import DOMAIN, FILES, HOST, REPO, USER, expiry_warning, token

LOGS = {
    "caccometro.log": f"{FILES}/caccometro.log",
    "error.log": f"{HOST}/api/v0/user/{USER}/files/path/var/log/{DOMAIN}.error.log",
    "server.log": f"{HOST}/api/v0/user/{USER}/files/path/var/log/{DOMAIN}.server.log",
    "access.log": f"{HOST}/api/v0/user/{USER}/files/path/var/log/{DOMAIN}.access.log",
}

def main():
    """Download the logs; return the names that could not be downloaded."""
    (REPO / "logs").mkdir(exist_ok=True)
    failed = []
    with httpx.Client(headers={"Authorization": f"Token {token()}"}, timeout=120) as client:
        for name, url in LOGS.items():
            r = client.get(url)
            if r.status_code != 200:
                print(f"  {name}: {r.status_code}")
                failed.append(name)
                continue
            (REPO / "logs" / name).write_bytes(r.content)
            print(f"  {name}: {len(r.content) // 1024} KB")
        expiry_warning(client)
    return failed


if __name__ == "__main__":
    main()
