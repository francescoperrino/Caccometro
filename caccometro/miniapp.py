"""Mini App (#79): who opened it (signed initData), which chats they may see, and the direct link from the groups."""
import hashlib
import hmac
import json
import os
import time
from urllib.parse import parse_qsl

from telegram.constants import ChatMemberStatus

from caccometro import database

SHORT_NAME = 'app'          # short name given to /newapp on BotFather, the same on both bots
MAX_AGE_SECONDS = 24 * 3600  # older initData is refused: a copied link stops working after a day
MEMBER_SECONDS = 5 * 60      # a membership check is trusted this long, to spare calls through the proxy

_members = {}  # (user_id, chat_id) -> time of the last positive check


def direct_link(bot_username, chat_id):
    """Link that opens the Mini App already on a chat; plain URL buttons are the only kind groups accept."""
    return f"https://t.me/{bot_username}/{SHORT_NAME}?startapp={chat_id}"


def user_of(init_data, token, now=None):
    """The Telegram user (dict) who opened the Mini App, or None when initData is not signed by Telegram or too old.

    Check from the Telegram docs: HMAC-SHA256 of the sorted "key=value" lines, with HMAC("WebAppData", token) as key.
    """
    fields = dict(parse_qsl(init_data or '', keep_blank_values=True))
    received = fields.pop('hash', '')
    check = '\n'.join(f"{key}={value}" for key, value in sorted(fields.items()))
    secret = hmac.new(b'WebAppData', token.encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(hmac.new(secret, check.encode(), hashlib.sha256).hexdigest(), received):
        return None
    try:
        fresh = (now or time.time()) - int(fields['auth_date']) < MAX_AGE_SECONDS
        user = json.loads(fields['user'])
    except (KeyError, ValueError):
        return None
    return user if fresh and isinstance(user.get('id'), int) else None


def known_chats():
    """IDs of every chat that has a database: the API never opens (and so never creates) the database of another one."""
    suffix = '_bot_data.db'
    names = os.listdir(database.DB_FOLDER) if os.path.isdir(database.DB_FOLDER) else []
    return [int(name[:-len(suffix)]) for name in names if name.endswith(suffix) and name[:-len(suffix)].lstrip('-').isdigit()]


def chats_of(user_id):
    """Chats whose database knows the user, for the group picker."""
    return [chat_id for chat_id in known_chats() if user_id in database.get_users(chat_id)]


async def is_member(bot, chat_id, user_id):
    """Whether the user is still in the chat; the private chat with the bot is always theirs."""
    if chat_id == user_id:
        return True
    checked = _members.get((user_id, chat_id))
    if checked and time.time() - checked < MEMBER_SECONDS:
        return True
    member = await bot.get_chat_member(chat_id, user_id)
    ok = member.status not in (ChatMemberStatus.LEFT, ChatMemberStatus.BANNED) and getattr(member, 'is_member', True)
    if ok:
        _members[(user_id, chat_id)] = time.time()
    return ok
