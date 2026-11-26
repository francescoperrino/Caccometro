"""Register the global command menus of the code (caccometro/menus.py) on one bot, then read them back.

Usage: python tools/register_menus.py dev|prod [mini app URL]  (settings: see deploy.py)
Italian menus are the default ones, English ones have language_code=en; each language on four scopes: default,
private chats, groups, group administrators (the only one with /link_history). The menu of a chat that chose a
language with /language is set by the bot itself. Production token: read from the server .env through the hosting
API; development token: local .env. Never printed.
The menu button of the private chats opens the Mini App: https://<web app domain>/app for prod, the given URL for
dev (a temporary tunnel); dev without a URL leaves the button as it is.
"""
import sys

import httpx

from deploy import DOMAIN, REPO, bot_token, server_env

sys.path.insert(0, str(REPO))
from caccometro.menus import menu  # noqa: E402

LANGUAGE_CODES = {'it': '', 'en': 'en'}   # Italian is the default menu
SCOPES = ('default', 'all_private_chats', 'all_group_chats', 'all_chat_administrators')


def main(which, app_url=None):
    """Register the menus on one bot and read them back; set the menu button if there is a URL for it.

    Args:
        which (str): 'dev' or 'prod'.
        app_url (str): the URL of the Mini App for the menu button; None for the one of production, or none for dev.
    """
    if which == 'prod':
        env = server_env()
    else:
        env = (REPO / ".env").read_text(encoding="utf-8")
    api = f"https://api.telegram.org/bot{bot_token(env)}/"

    def call(method, **body):
        """Call a method of the Bot API; exit with an error message when it fails.

        Args:
            method (str): the method name.
            **body: the JSON parameters.

        Returns:
            The result of the method.
        """
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

    app_url = app_url or (f"https://{DOMAIN}/app" if which == 'prod' else None)
    if app_url:
        button = {"type": "web_app", "text": "Caccometro", "web_app": {"url": app_url}}
        call("setChatMenuButton", menu_button=button)
        print(f"menu button: {app_url}, {'ok' if call('getChatMenuButton') == button else 'DIFFERENT'}")


if __name__ == "__main__":
    if sys.argv[1:2] not in (['dev'], ['prod']) or len(sys.argv) > 3:
        sys.exit("Usage: python tools/register_menus.py dev|prod [mini app URL]")
    main(*sys.argv[1:])
