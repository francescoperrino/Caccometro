"""Register the global command menus of the code (caccometro/menus.py) on one bot, then read them back.

Usage: python tools/register_menus.py dev|prod  (settings: see deploy.py)
Italian menus are the default ones, English ones have language_code=en; each language on four scopes: default,
private chats, groups, group administrators (the only one with /link_history). The menu of a chat that chose a
language with /language is set by the bot itself. Production token: read from the server .env through the hosting
API; development token: local .env. Never printed.
"""
import sys

import httpx

from bot_version import bot_token
from deploy import FILES, REPO, token

sys.path.insert(0, str(REPO))
from caccometro.menus import menu  # noqa: E402

LANGUAGE_CODES = {'it': '', 'en': 'en'}   # Italian is the default menu
SCOPES = ('default', 'all_private_chats', 'all_group_chats', 'all_chat_administrators')


def main(which):
    if which == 'prod':
        env = httpx.get(f"{FILES}/.env", headers={"Authorization": f"Token {token()}"}, timeout=60)
        env.raise_for_status()
        env = env.text
    else:
        env = (REPO / ".env").read_text(encoding="utf-8")
    api = f"https://api.telegram.org/bot{bot_token(env)}/"

    def call(method, **body):
        answer = httpx.post(api + method, json=body, timeout=30).json()
        if not answer["ok"]:
            sys.exit(f"{method} failed: {answer.get('description')}")
        return answer["result"]

    print("bot:", call("getMe")["username"])
    for language, code in LANGUAGE_CODES.items():
        for scope in SCOPES:
            commands = [{"command": name, "description": text}
                        for name, text in menu(language, admins=scope == 'all_chat_administrators')]
            call("setMyCommands", commands=commands, scope={"type": scope}, language_code=code)
            read_back = call("getMyCommands", scope={"type": scope}, language_code=code)
            print(f"{language} {scope}: {len(commands)} commands, {'ok' if read_back == commands else 'DIFFERENT'}")


if __name__ == "__main__":
    if sys.argv[1:] not in (['dev'], ['prod']):
        sys.exit("Usage: python tools/register_menus.py dev|prod")
    main(sys.argv[1])
