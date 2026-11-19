"""Deploy files to the hosting through its HTTP API: local backup, upload, reload, check.

Usage (from the repository root, with the virtual environment active):
    python tools/deploy.py caccometro/*.py                       # dry run
    python tools/deploy.py caccometro/*.py --yes                 # real deploy
    python tools/deploy.py caccometro/*.py --wsgi <file> --yes   # also the WSGI file
    python tools/deploy.py assets/fonts/* assets/emoji/* caccometro/*.py --yes   # with the chart assets
    python tools/deploy.py --rollback backups/<stamp> --yes

Allowed: top-level .py, caccometro/*.py, scripts/*.py, any file in assets/fonts/ and assets/emoji/ (uploaded
first: charts.py loads them at import), and the WSGI file (--wsgi, uploaded to WSGI below).
A rollback restores the .py files of the backup; it does not delete files the deploy created.

Settings: HOSTING_USERNAME in the .env of the repository; the API token in the environment variable
HOSTING_API_TOKEN (never in .env, never printed).
Nothing runs on the server: backups go to the local backups/ folder, not to the disk quota.
"""
import os
import re
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path

import httpx
from dotenv import load_dotenv

REPO = Path(__file__).resolve().parent.parent  # backups/, logs/ and the code are found from here, not from the working directory
load_dotenv(REPO / ".env")
os.umask(0o077)  # backups/ and logs/ hold copies of the databases: owner only (also for backup_db.py and fetch_logs.py, which import this)
USER = os.environ.get("HOSTING_USERNAME") or sys.exit("HOSTING_USERNAME is not set (.env).")
HOST = "https://www.pythonanywhere.com"
DOMAIN = f"{USER}.pythonanywhere.com"
REMOTE_HOME = f"/home/{USER}"
FILES = f"{HOST}/api/v0/user/{USER}/files/path{REMOTE_HOME}"
ROOT = f"{HOST}/api/v0/user/{USER}/files/path"
WSGI = f"/var/www/{DOMAIN.replace('.', '_')}_wsgi.py"
FOLDERS = ("caccometro", "scripts")
ASSET_FOLDERS = ("assets/fonts", "assets/emoji")


def url(remote):
    """Absolute remote paths (the WSGI file) start at /, the others at the home folder."""
    return f"{ROOT}{remote}" if remote.startswith("/") else f"{FILES}/{remote}"


def allowed(remote):
    if remote.rsplit("/", 1)[0] in ASSET_FOLDERS:
        return True
    parts = remote.split("/")
    return remote.endswith(".py") and (remote == WSGI or len(parts) == 1 or (len(parts) == 2 and parts[0] in FOLDERS))


def token():
    names = ("HOSTING_API_TOKEN", "PYTHONANYWHERE_TOKEN")  # the second is the old name, kept for existing setups
    value = next((os.environ[n] for n in names if os.environ.get(n)), None)
    if not value and sys.platform == "win32":
        import winreg  # setx writes here; a terminal opened before setx does not see it
        for name in names:
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
                    value = winreg.QueryValueEx(key, name)[0]
                break
            except OSError:
                continue
    if not value:
        sys.exit("HOSTING_API_TOKEN is not set.")
    return value


def expiry_warning(client):
    """Print how many days the free web app has left (the hosting API cannot extend it)."""
    expiry = client.get(f"{HOST}/api/v0/user/{USER}/webapps/{DOMAIN}/").json().get("expiry")
    if expiry:
        days = (date.fromisoformat(expiry) - date.today()).days
        mark = "  !!! " if days <= 14 else "  "
        print(f"{mark}web app expires on {expiry} ({days} days): Web tab, 'Run until 1 month from today'")


def download(client, remote, local):
    r = client.get(url(remote))
    if r.status_code == 404:
        return False
    r.raise_for_status()
    local.parent.mkdir(parents=True, exist_ok=True)
    local.write_bytes(r.content)
    return True


def backup(client, names):
    folder = REPO / "backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
    for name in names:
        found = download(client, name, folder / name.lstrip("/"))
        print(f"  backup {name}: {'ok' if found else 'not on server (new file)'}")
    dbs = client.get(f"{FILES}/db/")
    dbs.raise_for_status()
    db_names = [n for n, info in dbs.json().items() if info["type"] == "file" and n.endswith(".db")]
    for n in db_names:
        download(client, f"db/{n}", folder / "db" / n)
    print(f"  backup db/: {len(db_names)} databases")
    return folder


def upload(client, local, remote):
    r = client.post(url(remote), files={"content": (Path(remote).name, local.read_bytes())})
    if r.status_code not in (200, 201):
        sys.exit(f"Upload of {remote} failed: {r.status_code} {r.text[:200]}")
    print(f"  uploaded {remote}")


def local_version():
    text = (REPO / "caccometro" / "__init__.py").read_text(encoding="utf-8")
    return re.search(r'__version__ = "([^"]+)"', text).group(1)


def record(folder, version, names):
    """Append the deploy to backups/deploys.log: which version and commit run on the server."""
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"],
                           cwd=REPO, capture_output=True, text=True).stdout.strip()
    line = f"{folder.name}\t{version}\t{commit}{' +local changes' if dirty else ''}\t{' '.join(names)}\n"
    with open(REPO / "backups" / "deploys.log", "a", encoding="utf-8") as log:
        log.write(line)
    print(f"  recorded in backups/deploys.log: version {version}, commit {commit}")


def reload_and_check(client):
    """Reload, then return the version the home page reports."""
    r = client.post(f"{HOST}/api/v0/user/{USER}/webapps/{DOMAIN}/reload/")
    if r.status_code != 200:
        sys.exit(f"Reload failed: {r.status_code} {r.text[:200]}")
    print("  web app reloaded")
    for _ in range(3):  # the home page answers only if the caccometro package imports without errors
        time.sleep(3)
        try:
            page = httpx.get(f"https://{DOMAIN}/", timeout=30)
            if page.status_code == 200 and "Caccometro" in page.text:
                found = re.search(r"versione (\S+?)\.? ", page.text)
                version = found.group(1) if found else "unknown"
                print(f"  check: the bot answers on its home page, version {version}")
                return version
        except httpx.HTTPError:
            pass
    sys.exit("CHECK FAILED: the home page does not answer. Look at the error log, or roll back.")


def main(argv):
    real = "--yes" in argv
    argv = [a for a in argv if a != "--yes"]
    rollback = argv[:1] == ["--rollback"]
    if rollback:
        folder = Path(argv[1])
        pairs = []
        for p in folder.rglob("*.py"):
            rel = p.relative_to(folder).as_posix()
            pairs.append((p, "/" + rel if "/" + rel == WSGI else rel))
    else:
        wsgi = []
        if "--wsgi" in argv:
            i = argv.index("--wsgi")
            wsgi = [(Path(argv[i + 1]), WSGI)]
            del argv[i:i + 2]
        # WSGI last: changing it may restart the web app, the modules it imports must already be there
        # assets before the modules that load them
        pairs = sorted(((Path(name), Path(name).as_posix()) for name in argv), key=lambda p: p[1].endswith(".py")) + wsgi
    if not pairs:
        sys.exit(__doc__)
    for local, remote in pairs:
        if not local.is_file() or not allowed(remote):
            sys.exit(f"Not an allowed file: {local} -> {remote}")

    print(f"{'DEPLOY' if real else 'DRY RUN'} to {DOMAIN}: {', '.join(r for _, r in pairs)}")
    if not real:
        print("Nothing changed. Add --yes to deploy.")
        return
    with httpx.Client(headers={"Authorization": f"Token {token()}"}, timeout=60) as client:
        folder = backup(client, [r for _, r in pairs])
        print(f"  backup saved in {folder}")
        for local, remote in pairs:
            upload(client, local, remote)
        version = reload_and_check(client)
        record(folder, version, [r for _, r in pairs])
        expiry_warning(client)
        if not rollback and version != local_version():
            sys.exit(f"CHECK FAILED: the server runs version {version}, the local code is {local_version()}.")
    print(f"Done. Rollback: tools/deploy.py --rollback {folder} --yes")


if __name__ == "__main__":
    main(sys.argv[1:])
