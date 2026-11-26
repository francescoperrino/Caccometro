"""Mini App (#188): the signed initData, the chats a user may see and the access checks of the API."""
import hashlib
import hmac
import json
import os
import time
from datetime import date
from urllib.parse import urlencode

import pytest
from telegram.error import Forbidden

from caccometro import __version__, bot, conquest, database, miniapp, trophies, webhook
from caccometro.model import User
from conftest import BOT_USER, CHAT_ID, uid

TOKEN = os.environ["BOT_TOKEN"]
USER_ID = 42


def init_data(user_id=USER_ID, auth_date=None, token=TOKEN, **extra):
    """initData signed like Telegram does (the test user is made up).

    Args:
        user_id (int): the user.
        auth_date (float): when it was signed; None for now.
        token (str): the token that signs it.
        **extra: more fields.

    Returns:
        str: the URL-encoded initData.
    """
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


def test_direct_link_opens_the_mini_app_on_the_chat():
    assert miniapp.direct_link("caccometro_bot", -1001) == "https://t.me/caccometro_bot/app?startapp=-1001"


@pytest.fixture
def telegram(monkeypatch):
    """Telegram answers getMe, getChat and getChatMember; `status` sets the membership.

    Args:
        monkeypatch (pytest.MonkeyPatch): pytest's fixture.

    Returns:
        dict: the state, with 'status' and the 'calls' made.
    """
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
    """The Flask test client.

    Returns:
        flask.testing.FlaskClient: the client.
    """
    return webhook.app.test_client()


def get(client, path, data=None):
    """GET a path signed as a Mini App user.

    Args:
        client (flask.testing.FlaskClient): the test client.
        path (str): the path.
        data (str): the initData; None for a valid one.

    Returns:
        flask.Response: the response.
    """
    return client.get(path, headers={"Authorization": "tma " + (data if data is not None else init_data())})


def test_api_refuses_unsigned_calls(client, telegram):
    assert get(client, f"/api/chat?chat={CHAT_ID}", "x").status_code == 401
    assert telegram["calls"] == []


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
    assert get(client, f"/api/chat?chat={USER_ID}").get_json()["language"] == "en"
    assert get(client, f"/api/chat?chat={USER_ID}").get_json()["version"] == __version__
    assert "getChatMember" not in telegram["calls"]


def test_membership_is_remembered_for_a_while(client, telegram):
    get(client, f"/api/chat?chat={CHAT_ID}")
    get(client, f"/api/chat?chat={CHAT_ID}")
    assert telegram["calls"].count("getChatMember") == 1


def test_mini_app_page_is_served(client):
    response = client.get("/app")
    assert response.status_code == 200 and b"telegram-web-app.js" in response.data
    response.close()


def test_conquest_data_sends_outlines_and_owners_at_every_zoom_but_no_locations():
    users = {1: User(1, "anna", "Anna"), 2: User(2, None, "Bruno")}
    cell = conquest.cell_of(45.46, 9.19)
    other = conquest.cell_of(45.60, 9.40)
    data = miniapp.conquest_data([(1, 1_700_000_000, cell), (2, 1_700_000_100, cell), (1, 1_700_000_200, other),
                                  (2, int(time.time()), conquest.cell_of(45.0, 9.0))], users)
    tiles = data["levels"][7]
    assert sorted(tile["owner"] for tile in tiles) == [1, 2, 2] and all(len(tile["outline"]) == 6 for tile in tiles)
    assert any(tile["seen"] == {1: 1, 2: 1} and tile["held"] == {2: 1} for tile in tiles)  # taken from member 1
    assert len(data["levels"][1]) == 1 and data["levels"][1][0]["held"] == {1: 1, 2: 2}  # the whole world in one hexagon
    assert data["names"] == {1: "@anna", 2: "Bruno"} and sorted(r["user"] for r in data["ranking"]) == [1, 2]
    assert data["season"]["conquests"] == 1 and data["season"]["conquerors"] == [2]
    assert "lat" not in str(data) and "ts" not in data


def test_conquest_data_of_an_empty_chat():
    data = miniapp.conquest_data([], {})
    assert data["levels"][7] == [] and data["king"] is None and data["season"] is None


def test_period_data_is_the_leaderboard_and_the_statistics_of_the_commands(seed, chat_id):
    seed({"mario": {"2026-10-01": 2, "2026-10-31": 1, "2026-11-01": 1}, "luigi": {"2026-10-02": 1}})
    past = miniapp.period_data(chat_id, "month", "10-2026", date(2026, 11, 20))
    assert past["leaderboard"] == [{"user": uid("mario"), "total": 3, "forecast": None},
                                   {"user": uid("luigi"), "total": 1, "forecast": None}]
    assert past["statistics"][0] == {"user": uid("mario"), "mean": round(3 / 31, 2), "median": 0.0, "variance": 0.15,
                                   "regularity": None}
    assert past["daily"][uid("mario")] == {"2026-10-01": 2, "2026-10-31": 1}
    ongoing = miniapp.period_data(chat_id, "month", "11-2026", date(2026, 11, 20))
    assert ongoing["leaderboard"][0]["forecast"] == 1 + round(2 / 30 * 10)  # 2 💩 in the last 30 days, 10 days left
    json.loads(webhook.app.json.dumps(ongoing))


def test_records_data_is_ready_for_json(seed, chat_id):
    seed({"mario": {f"2026-10-{day:02d}": 1 for day in range(1, 16)}, "luigi": {"2026-10-20": 3}})
    rows, _ = database.get_all_user_rows(chat_id)
    data = miniapp.records_data(rows, date(2026, 11, 20), [])
    assert data["group"]["daily"] == {"value": 3, "holders": [{"key": uid("luigi"), "when": ["2026-10-20"]}]}
    assert data["people"][uid("mario")]["streak_days"]["when"] == [{"start": "2026-10-01", "end": "2026-10-15"}]
    assert data["trophies"][uid("mario")]["streak_trophies"] == 1 and data["trophies"][uid("mario")]["months"] == [[2026, 10]]
    json.loads(webhook.app.json.dumps(data))


@pytest.mark.parametrize("query, code", [("year=2026&month=11", 200), ("year=2026", 200), ("year=1969", 400),
                                         ("year=2026&month=13", 400), ("year=abc", 400), ("", 400)])
def test_api_period_checks_the_period(client, telegram, query, code):
    assert get(client, f"/api/period?chat={CHAT_ID}&{query}").status_code == code


def test_api_period_only_for_members(client, telegram):
    telegram["status"] = "left"
    assert get(client, f"/api/period?chat={CHAT_ID}&year=2026").status_code == 403


def test_season_boards_follow_the_rules_of_the_season_titles():
    a, b = conquest.cell_of(45.46, 9.19), conquest.cell_of(45.60, 9.40)
    q1, q2 = 1_767_225_600 + 86_400, 1_775_000_000 + 86_400   # made-up times: January and April 2026
    timed = [(1, q1, a), (1, q1 + 1, a), (2, q1 + 2, b), (2, q2, a), (1, q2 + 1, b)]
    boards = miniapp._season_boards(timed)
    assert [(x["year"], x["quarter"]) for x in boards] == [(2026, 1), (2026, 2)]
    assert boards[0]["conquests"] == {1: 1, 2: 1} and boards[0]["held"] == {1: 1, 2: 1}  # retaking your own tile counts nothing
    assert boards[1]["conquests"] == {2: 1, 1: 1} and boards[1]["held"] == {2: 1, 1: 1}
    results = trophies.season_results(timed)
    assert all(max(x["conquests"].values()) == results[(x["year"], x["quarter"])].conquests for x in boards)
    assert all(x["king"] == results[(x["year"], x["quarter"])].king for x in boards)
