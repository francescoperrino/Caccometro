"""Write the local version at the end of the bot descriptions (Italian and English), on the production and development bots.

Usage, after a release: python tools/bot_version.py (settings: see deploy.py)
Production token: read from the server .env through the hosting API; development token: local .env. Never printed.
"""
import re

import httpx

from deploy import FILES, REPO, local_version, token


VERSION_LINE = {'': "Versione", 'en': "Version"}   # language_code of the description ('' = default, Italian) -> word


def bot_token(env):
    return re.search(r"BOT_TOKEN\s*=\s*['\"]?([^'\"\s]+)", env).group(1)


def main():
    prod_env = httpx.get(f"{FILES}/.env", headers={"Authorization": f"Token {token()}"}, timeout=60)
    prod_env.raise_for_status()
    version = local_version()
    for tk in (bot_token(prod_env.text), bot_token((REPO / ".env").read_text(encoding="utf-8"))):
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
