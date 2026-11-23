"""Mini App (#188): the signed initData, the chats a user may see and the access checks of the API."""
import hashlib
import hmac
import json
import os
import time
from urllib.parse import urlencode

import pytest
from telegram.error import Forbidden

from caccometro import bot, database, miniapp, webhook
from conftest import CHAT_ID

TOKEN = os.environ["BOT_TOKEN"]
USER_ID = 42
BOT_USER = {"id": 7, "is_bot": True, "first_name": "Caccometro", "username": "caccometro_test_bot"}


def init_data(user_id=USER_ID, auth_date=None, token=TOKEN, **extra):
    """initData signed like Telegram does (the test user is made up)."""
    fields = {"auth_date": str(int(auth_date or time.time())),
              "user": json.dumps({"id": user_id, "first_name": "Mario"}), **extra}
    check = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


def test_signed_init_data_gives_the_user():
    assert miniapp.user_of(init_data(start_param="-1001"), TOKEN)["id"] == USER_ID


@pytest.mark.parametrize("data", [
    init_data(token="999:OTHER"),                         # signed by another bot
    init_data(auth_date=time.time() - 2 * 24 * 3600),     # two days old
    init_data().replace("Mario", "Luigi"),                # changed after signing
    "", "hash=abc", "hash=%C3%A8",                        # empty, wrong, non-ASCII
])
def test_bad_init_data_gives_no_user(data):
    assert miniapp.user_of(data, TOKEN) is None


def test_chats_of_lists_only_chats_whose_database_knows_the_user():
    database.upsert_user(CHAT_ID, USER_ID, "mario", "Mario")
    database.upsert_user(-2002, 99, "luigi", "Luigi")
    assert miniapp.chats_of(USER_ID) == [CHAT_ID]


def test_direct_link_opens_the_mini_app_on_the_chat():
    assert miniapp.direct_link("caccometro_bot", -1001) == "https://t.me/caccometro_bot/app?startapp=-1001"


@pytest.fixture
def telegram(monkeypatch):
    """Telegram answers getMe, getChat and getChatMember; `status` sets the membership."""
    state = {"status": "member", "calls": []}

    async def fake_post(endpoint, data=None, **kwargs):
        state["calls"].append(endpoint)
        if endpoint == "getMe":
            return BOT_USER
        if endpoint == "getChat":
            if state["status"] == "gone":
                raise Forbidden("bot was kicked")
            return {"id": data["chat_id"], "type": "supergroup", "title": "Amici"}
        if endpoint == "getChatMember":
            extra = {"kicked": {"until_date": 0}, "creator": {"is_anonymous": False}}.get(state["status"], {})
            return {"status": state["status"], "user": {"id": USER_ID, "is_bot": False, "first_name": "Mario"}, **extra}
        raise AssertionError(endpoint)

    monkeypatch.setattr(bot.application.bot, "_post", fake_post)
    monkeypatch.setattr(bot.application.bot, "_bot_user", None)
    miniapp._members.clear()
    return state


@pytest.fixture
def client():
    return webhook.app.test_client()


def get(client, path, data=None):
    return client.get(path, headers={"Authorization": "tma " + (data if data is not None else init_data())})


def test_api_refuses_unsigned_calls(client, telegram):
    assert get(client, "/api/chats", "").status_code == 401
    assert get(client, f"/api/chat?chat={CHAT_ID}", "x").status_code == 401
    assert telegram["calls"] == []


def test_api_chats_lists_groups_with_titles_and_the_private_chat(client, telegram):
    database.upsert_user(CHAT_ID, USER_ID, "mario", "Mario")
    database.upsert_user(USER_ID, USER_ID, "mario", "Mario")
    body = get(client, "/api/chats").get_json()
    assert sorted(body["chats"], key=lambda c: c["id"]) == [{"id": CHAT_ID, "title": "Amici"},
                                                            {"id": USER_ID, "title": None}]
    assert body["language"] == "it"


def test_api_chats_skips_groups_the_bot_left(client, telegram):
    database.upsert_user(CHAT_ID, USER_ID, "mario", "Mario")
    telegram["status"] = "gone"
    assert get(client, "/api/chats").get_json()["chats"] == []


@pytest.mark.parametrize("status, code", [("member", 200), ("creator", 200), ("left", 403), ("kicked", 403)])
def test_api_chat_only_for_members(client, telegram, status, code):
    telegram["status"] = status
    assert get(client, f"/api/chat?chat={CHAT_ID}").status_code == code


def test_api_chat_never_creates_a_database(client, telegram):
    assert get(client, "/api/chat?chat=-777").status_code == 404
    assert get(client, "/api/chat?chat=abc").status_code == 400
    assert -777 not in miniapp.known_chats()
    assert "getChatMember" not in telegram["calls"]


def test_api_chat_private_chat_needs_no_membership_check(client, telegram):
    database.init_database(USER_ID)
    database.set_language(USER_ID, "en")
    assert get(client, f"/api/chat?chat={USER_ID}").get_json() == {"chat": USER_ID, "language": "en"}
    assert "getChatMember" not in telegram["calls"]


def test_membership_is_remembered_for_a_while(client, telegram):
    get(client, f"/api/chat?chat={CHAT_ID}")
    get(client, f"/api/chat?chat={CHAT_ID}")
    assert telegram["calls"].count("getChatMember") == 1


def test_mini_app_page_is_served(client):
    response = client.get("/app")
    assert response.status_code == 200 and b"telegram-web-app.js" in response.data
    response.close()
