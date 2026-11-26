"""Write the local version at the end of the bot descriptions (Italian and English), on the production and development bots.

Usage, after a release: python tools/bot_version.py (settings: see deploy.py)
Production token: read from the server .env through the hosting API; development token: local .env. Never printed.
"""
import re

import httpx

from deploy import REPO, bot_token, local_version, server_env


VERSION_LINE = {'': "Versione", 'en': "Version"}   # language_code of the description ('' = default, Italian) -> word


def main():
    """Write the local version at the end of the description of both bots, in Italian and English."""
    prod_env = server_env()
    version = local_version()
    for tk in (bot_token(prod_env), bot_token((REPO / ".env").read_text(encoding="utf-8"))):
        api = f"https://api.telegram.org/bot{tk}/"
        name = httpx.post(api + "getMe").json()["result"]["username"]
        for language, word in VERSION_LINE.items():
            label = f"{name} ({language or 'it'})"
            text = httpx.post(api + "getMyDescription", json={"language_code": language}).json()["result"]["description"]
            if not text:  # an empty description would fall back to the default one: set the text first (README)
                print(f"{label}: no description, version NOT set")
                continue
            text = re.sub(rf"\n\n{word} \S+$", "", text) + f"\n\n{word} {version}"
            ok = httpx.post(api + "setMyDescription", json={"description": text, "language_code": language}).json()["ok"]
            print(f"{label}: description {'set to' if ok else 'NOT set to'} version {version}")


if __name__ == "__main__":
    main()
