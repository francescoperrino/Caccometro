"""Send a private Telegram message to the maintainer, for the scripts that run by themselves."""
import os

import httpx

import deploy  # noqa: F401  loads the .env of the repository (BOT_TOKEN and ALERT_CHAT_ID)


def alert(text):
    """Tell the maintainer on Telegram; never raises and never prints the token (httpx errors carry the URL).

    The message goes through the bot of BOT_TOKEN to ALERT_CHAT_ID; nothing is sent when either is not set.

    Args:
        text (str): the message.
    """
    chat, bot = os.environ.get("ALERT_CHAT_ID"), os.environ.get("BOT_TOKEN")
    if not (chat and bot):
        return
    try:
        httpx.post(f"https://api.telegram.org/bot{bot}/sendMessage", data={"chat_id": chat, "text": text}, timeout=20)
    except httpx.HTTPError:
        pass  # the FAILED line on stderr and in the log is still there
