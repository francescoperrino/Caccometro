"""Recap of the Mini App (#195): the facts of the month (or year) just ended, the API that gives them and the picture to share."""
from datetime import date, datetime

import pytest
from telegram.error import Forbidden

from caccometro import analysis, announce, bot, charts, database, miniapp, webhook
from caccometro.config import ROME_TZ
from conftest import BOT_USER, CHAT_ID, uid
from test_miniapp import USER_ID, init_data

FIRST_DAYS = {1: "2026-01-01", 2: "2026-01-01", 3: "2026-01-01"}


def october(days, count=1):
    """The counts of some days of October 2026.

    Args:
        days (iterable): the days of the month.
        count (int): the 💩 of each day.

    Returns:
        dict: {'YYYY-MM-DD': count}.
    """
    return {f"2026-10-{d:02d}": count for d in days}


def test_the_recap_tells_the_facts_of_the_month():
    daily = {1: {**october(range(1, 8)), **october([12, 13, 14, 15, 16, 17, 18, 19], 1), "2026-10-20": 3, "2026-10-25": 3,
                 "2026-09-30": 5, "2026-09-10": 2, "2026-11-01": 9},   # around the month: not counted in it
             2: october(range(1, 31), 2), 3: october([5], 23)}
    recap = analysis.recap(daily, 1, 2026, 10, FIRST_DAYS)
    assert (recap.year, recap.month, recap.total, recap.days) == (2026, 10, 21, 31)
    assert (recap.best_day, recap.best_count) == (date(2026, 10, 20), 3)               # the earliest of the ties
    assert (recap.streak, recap.streak_days) == (analysis.Period(date(2026, 10, 12), date(2026, 10, 20)), 9)
    assert (recap.place, recap.people, recap.ahead, recap.ahead_gap) == (3, 3, 3, 2)   # 3 is the closest one above
    assert recap.previous_total == 7


def test_a_streak_across_the_end_of_the_month_counts_its_days_inside_only():
    daily = {1: {"2026-09-29": 1, "2026-09-30": 1, **october([1, 2]), "2026-11-01": 1}}
    recap = analysis.recap(daily, 1, 2026, 10, FIRST_DAYS)
    assert recap.streak_days == 2 and recap.place == 1 and recap.ahead is None and recap.people == 1


def test_ties_share_the_place():
    daily = {1: october([1, 2]), 2: october([3, 4]), 3: october([5, 6, 7])}
    recap = analysis.recap(daily, 2, 2026, 10, FIRST_DAYS)
    assert (recap.place, recap.ahead, recap.ahead_gap) == (2, 3, 1)


def test_no_recap_without_poops_in_the_month():
    assert analysis.recap({1: {"2026-09-30": 4}, 2: october([1])}, 1, 2026, 10, FIRST_DAYS) is None


@pytest.mark.parametrize("today, shown", [(date(2026, 11, 1), True), (date(2026, 11, 7), True), (date(2026, 11, 8), False)])
def test_the_recap_shows_in_the_first_week_only(seed, today, shown):
    seed({"mario": {"2026-10-10": 2}})
    assert (miniapp.recap_data(CHAT_ID, uid("mario"), today) is not None) == shown


def test_the_recap_of_a_year_counts_the_whole_year():
    daily = {1: {"2025-06-01": 4, "2026-02-27": 1, "2026-02-28": 1, "2026-03-01": 2, "2026-12-31": 1, "2027-01-01": 9},
             2: {"2026-05-05": 9}}
    recap = analysis.recap(daily, 1, 2026, None, FIRST_DAYS)
    assert (recap.year, recap.month, recap.total, recap.days, recap.previous_total) == (2026, None, 5, 365, 4)
    assert (recap.best_day, recap.best_count) == (date(2026, 3, 1), 2)
    assert (recap.streak, recap.streak_days) == (analysis.Period(date(2026, 2, 27), date(2026, 3, 1)), 3)   # across months
    assert (recap.place, recap.people, recap.ahead, recap.ahead_gap) == (2, 2, 2, 4)


@pytest.mark.parametrize("today, recaps", [(date(2026, 1, 3), [(2025, None), (2025, 12)]), (date(2026, 1, 8), [(2025, None)]),
                                            (date(2026, 1, 14), [(2025, None)]), (date(2026, 1, 15), []), (date(2026, 2, 3), [(2026, 1)])])
def test_in_january_the_year_shows_for_two_weeks_and_december_for_one(seed, today, recaps):
    seed({"mario": {"2025-12-31": 2, "2025-03-01": 1, "2024-07-01": 3, "2026-01-02": 1}})
    assert [(r["year"], r["month"]) for r in miniapp.recaps(CHAT_ID, uid("mario"), today)] == recaps


def test_the_recap_of_the_year_compares_with_the_year_before(seed):
    seed({"mario": {"2025-12-31": 2, "2025-03-01": 1, "2024-07-01": 3}})
    recap = miniapp.recap_data(CHAT_ID, uid("mario"), date(2026, 1, 3), yearly=True)
    assert (recap.year, recap.month, recap.total, recap.previous_total) == (2025, None, 3, 3)


@pytest.mark.parametrize("people, month, style", [(1, 10, "generated"), (3, 10, "code"), (3, None, "generated"), (1, None, "code")])
def test_the_picture_is_a_png_of_4_by_5(monkeypatch, people, month, style):
    monkeypatch.setattr(charts, "RECAP_STYLE", style)
    daily = {1: october([1, 2, 3]), 2: october([4]), 3: october(range(1, 20))}
    if people == 1:
        daily = {1: daily[1]}
    recap = analysis.recap(daily, 1, 2026, month, FIRST_DAYS)
    png = charts.generate_recap_image(recap, "Mario")
    assert png.startswith(b"\x89PNG") and int.from_bytes(png[16:20], "big") == 1080 and int.from_bytes(png[20:24], "big") == 1350


def test_every_month_and_the_year_have_a_background_in_both_styles():
    for style in ("generated", "code"):
        assert sorted(p.name for p in (charts.ASSETS / "recap" / style).glob("*.jpg")) == [f"{m:02d}.jpg" for m in range(1, 13)] + ["year.jpg"]


# ---------------------------------------------------------------- the API

@pytest.fixture
def telegram(monkeypatch):
    """Telegram for the API: a member, and sendPhoto recorded (or refused with `refuse`).

    Args:
        monkeypatch (pytest.MonkeyPatch): pytest's fixture.

    Returns:
        dict: the state, with the 'photos' sent and the 'refuse' switch.
    """
    state = {"photos": [], "refuse": False}

    async def fake_post(endpoint, data=None, **kwargs):
        if endpoint == "getMe":
            return BOT_USER
        if endpoint == "getChat":
            return {"id": data["chat_id"], "type": "supergroup", "title": "Amici"}
        if endpoint == "getChatMember":
            return {"status": "member", "user": {"id": USER_ID, "is_bot": False, "first_name": "Mario"}}
        if endpoint == "sendPhoto":
            if state["refuse"]:
                raise Forbidden("bot can't initiate conversation with a user")
            state["photos"].append(data["chat_id"])
            return {"message_id": 1, "date": 0, "chat": {"id": data["chat_id"], "type": "private"}}
        raise AssertionError(endpoint)

    monkeypatch.setattr(bot.application.bot, "_post", fake_post)
    monkeypatch.setattr(bot.application.bot, "_bot_user", None)
    monkeypatch.setattr(webhook, "now_rome", lambda: datetime(2026, 11, 2, 9, tzinfo=ROME_TZ))
    miniapp._members.clear()
    webhook._shared.clear()
    database.upsert_user(CHAT_ID, USER_ID, "mario", "Mario")
    database.add_count(USER_ID, "2026-10-10", 2, CHAT_ID)
    return state


def call(method, path, user_id=USER_ID):
    """Call the API as a Mini App user.

    Args:
        method (str): 'get' or 'post'.
        path (str): the path.
        user_id (int): the user.

    Returns:
        flask.Response: the response.
    """
    return getattr(webhook.app.test_client(), method)(path, headers={"Authorization": "tma " + init_data(user_id=user_id)})


def test_api_chat_carries_the_recap_of_who_opens_it(telegram):
    assert [r["total"] for r in call("get", f"/api/chat?chat={CHAT_ID}").get_json()["recaps"]] == [2]
    assert call("get", f"/api/chat?chat={CHAT_ID}", user_id=99).get_json()["recaps"] == []   # no 💩 in October


def test_the_summary_screen_shows_the_same_picture_that_is_shared(telegram):
    response = call("get", f"/api/recap?chat={CHAT_ID}")
    assert response.mimetype == "image/png" and response.data.startswith(b"\x89PNG")
    assert telegram["photos"] == []   # showing it sends nothing


def test_share_sends_the_picture_in_the_chat_once_every_30_seconds(telegram):
    assert call("post", f"/api/recap?chat={CHAT_ID}").get_json() == {"sent": True}
    assert telegram["photos"] == [CHAT_ID]   # in the group the Mini App was opened from
    assert call("post", f"/api/recap?chat={CHAT_ID}").status_code == 429
    assert telegram["photos"] == [CHAT_ID]


def test_share_tells_when_the_bot_cannot_write_in_the_group(telegram):
    telegram["refuse"] = True
    response = call("post", f"/api/recap?chat={CHAT_ID}")
    assert response.status_code == 403 and response.get_json()["error"] == "chat"
    telegram["refuse"] = False
    assert call("post", f"/api/recap?chat={CHAT_ID}").status_code == 200   # a refused send does not count for the 30 seconds


def test_share_in_private_asks_to_start_the_bot_first(telegram):
    database.add_count(USER_ID, "2026-10-10", 1, USER_ID)   # the private chat with the bot
    telegram["refuse"] = True
    response = call("post", f"/api/recap?chat={USER_ID}")
    assert response.status_code == 403 and response.get_json()["error"] == "start"
    telegram["refuse"] = False
    assert call("post", f"/api/recap?chat={USER_ID}").status_code == 200 and telegram["photos"] == [USER_ID]


def test_the_link_downloads_the_picture_without_initdata(telegram):
    url = call("post", f"/api/recap?chat={CHAT_ID}&to=link").get_json()["url"]
    assert url.startswith("https://") and telegram["photos"] == []
    response = webhook.app.test_client().get("/" + url.split("/", 3)[3])
    assert response.status_code == 200 and response.data.startswith(b"\x89PNG")
    assert response.headers["Content-Disposition"].startswith("attachment")
    assert response.headers["Access-Control-Allow-Origin"] == "https://web.telegram.org"


@pytest.mark.parametrize("change", ["forged", "expired", "junk"])
def test_a_forged_or_expired_link_finds_nothing(telegram, change):
    name = miniapp.recap_link(CHAT_ID, USER_ID, False, webhook.BOT_TOKEN, now=1 if change == "expired" else None)
    name = {"forged": name.replace(f"{CHAT_ID}.", "-42.", 1), "expired": name, "junk": "a.b"}[change]
    assert webhook.app.test_client().get(f"/api/recap/{name}.png").status_code == 404


def test_share_needs_a_recap_and_a_signature(telegram):
    assert call("post", f"/api/recap?chat={CHAT_ID}", user_id=99).status_code == 404
    assert webhook.app.test_client().post(f"/api/recap?chat={CHAT_ID}", headers={"Authorization": "tma x"}).status_code == 401
    assert telegram["photos"] == []


def test_direct_link_to_the_recap():
    assert miniapp.direct_link("caccometro_bot", -1001, "recap") == "https://t.me/caccometro_bot/app?startapp=-1001_recap"
    assert miniapp.direct_link("caccometro_bot", -1001, "year") == "https://t.me/caccometro_bot/app?startapp=-1001_year"


def test_the_picture_of_the_year_has_its_own_address(telegram, monkeypatch):
    monkeypatch.setattr(webhook, "now_rome", lambda: datetime(2027, 1, 10, 9, tzinfo=ROME_TZ))
    database.add_count(USER_ID, "2026-12-30", 1, CHAT_ID)
    assert call("get", f"/api/recap?chat={CHAT_ID}&year=1").mimetype == "image/png"
    assert call("get", f"/api/recap?chat={CHAT_ID}").status_code == 404       # December shows from the 1st to the 7th only


@pytest.mark.parametrize("name, status", [("10", 200), ("year", 200), ("13", 404), ("..%2Fbrand%2Fmascot", 404)])
def test_the_screens_get_the_drawn_background_of_the_month(name, status):
    assert webhook.app.test_client().get(f"/app/recap/{name}.jpg").status_code == status


def test_on_the_first_of_january_the_announcement_opens_the_year_too():
    urls = lambda today: [b.url.rsplit("_", 1)[1] for b in announce._recap_button(-1001, today).inline_keyboard[0]]
    assert urls(date(2027, 1, 1)) == ["year", "recap"] and urls(date(2026, 11, 1)) == ["recap"]
