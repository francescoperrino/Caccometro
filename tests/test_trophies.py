"""Trophies (#6): streaks every 15 days, 💩 of the month and of the year, /trofei and the midnight announcement."""
import asyncio
from datetime import date, datetime, timedelta

from caccometro import announce, commands, messages
from caccometro.analysis import Period
from caccometro.formatting import format_group_trophies, format_new_period, format_user_trophies
from caccometro.trophies import (UserTrophies, Winners, monthly_winners, new_streak_trophy, streak_runs,
                                 trophies_by_user, yearly_winners)
from conftest import make_context, make_update, uid


def run(coro):
    return asyncio.run(coro)


def days_from(start, n, count=1):
    """n consecutive days from `start` ('YYYY-MM-DD'), each with `count` 💩, as stored rows."""
    first = date.fromisoformat(start)
    return [((first + timedelta(days=i)).isoformat(), count) for i in range(n)]


# ---------------------------------------------------------------- pure functions

def test_streak_runs_keep_only_runs_of_at_least_15_days():
    rows = days_from("2026-01-01", 14) + days_from("2026-02-01", 47)
    runs = streak_runs(rows)
    assert [days for _, days in runs] == [47]
    assert UserTrophies(runs, [], []).streak_trophies == 3


def test_days_without_poop_break_the_streak():
    rows = days_from("2026-01-01", 10) + [("2026-01-11", 0)] + days_from("2026-01-12", 10)
    assert streak_runs(rows) == []


def test_new_streak_trophy_on_every_multiple_of_15():
    rows = days_from("2026-01-01", 30)
    assert new_streak_trophy(rows, date(2026, 1, 15)) == 15
    assert new_streak_trophy(rows, date(2026, 1, 30)) == 30
    assert new_streak_trophy(rows, date(2026, 1, 16)) is None
    assert new_streak_trophy(rows, date(2026, 2, 1)) is None   # no 💩 today


def test_monthly_winners_skip_the_current_month_and_keep_ties():
    users_rows = {
        1: [("2026-09-01", 3), ("2026-10-01", 2), ("2026-11-01", 9)],
        2: [("2026-09-02", 1), ("2026-10-05", 2)],
    }
    winners = monthly_winners(users_rows, date(2026, 11, 16))
    assert winners == {(2026, 9): Winners(3, [1]), (2026, 10): Winners(2, [1, 2])}


def test_yearly_winners_only_completed_years():
    users_rows = {1: [("2025-03-01", 5), ("2026-01-01", 50)], 2: [("2025-07-01", 7)]}
    assert yearly_winners(users_rows, date(2026, 11, 16)) == {2025: Winners(7, [2])}


def test_trophies_by_user_leaves_out_users_without_trophies():
    users_rows = {1: days_from("2026-09-01", 15), 2: [("2026-09-03", 1)], 3: []}
    trophies = trophies_by_user(users_rows, date(2026, 11, 16))
    assert set(trophies) == {1}
    assert trophies[1].months == [(2026, 9)]
    assert trophies[1].streak_trophies == 1


# ---------------------------------------------------------------- messages

def test_group_trophies_ranks_years_then_months_then_streaks():
    trophies = {
        1: UserTrophies([], [(2026, 1), (2026, 2)], []),
        2: UserTrophies([], [(2026, 3)], [2025]),
    }
    text = format_group_trophies(trophies, {1: "@mario", 2: "@luigi"})
    assert text.index("@luigi") < text.index("@mario")
    assert "*@luigi*: 👑 1 · 🏅 1" in text
    assert "*@mario*: 🏅 2" in text


def test_group_trophies_without_any_trophy():
    assert "Ancora nessun trofeo" in format_group_trophies({}, {})


def test_user_trophies_lists_months_and_streaks_and_the_next_goal():
    trophies = UserTrophies([(Period(date(2026, 1, 1), date(2026, 2, 16)), 47)],
                            [(2026, 9), (2026, 10)], [2025])
    text = format_user_trophies("@mario", trophies, current_streak=7)
    assert "👑 💩 dell'anno: 2025" in text
    assert "🏅 💩 del mese (2): ottobre 2026, settembre 2026" in text
    assert "🔥 Serie: 3 trofei" in text
    assert "47 giorni: 01-01-2026 - 16-02-2026" in text
    assert "7 giorni di fila, ne mancano 8 al prossimo trofeo" in text


def test_user_without_trophies_and_without_streak():
    text = format_user_trophies("@mario", None, current_streak=0)
    assert "Ancora nessun trofeo." in text
    assert "Nessuna serie in corso" in text


def test_new_month_message():
    text = format_new_period(date(2026, 11, 1), Winners(52, [1, 2]), None, {1: "@mario", 2: "@luigi"})
    assert "ottobre 2026 è finito" in text
    assert "*@mario* e *@luigi* con 52 💩 a testa" in text
    assert "buon novembre" in text


def test_new_year_message():
    text = format_new_period(date(2027, 1, 1), Winners(31, [1]), Winners(400, [2]), {1: "@mario", 2: "@luigi"})
    assert "Buon anno! Benvenuto 2027!" in text
    assert "💩 di dicembre: *@mario* con 31 💩" in text
    assert "💩 dell'anno 2026: *@luigi* con 400 💩" in text


def test_no_message_when_nobody_won():
    assert format_new_period(date(2026, 11, 1), None, None, {}) is None


# ---------------------------------------------------------------- the reply to a 💩

def test_poop_completing_15_days_announces_the_trophy(seed, monkeypatch):
    seed({"mario": dict(days_from("2026-11-01", 14))})
    monkeypatch.setattr(messages, "now_rome", lambda: datetime(2026, 11, 15, 9, 0))
    first, second = make_update(text="💩"), make_update(text="💩")
    run(messages.handle_message(first, make_context()))
    run(messages.handle_message(second, make_context()))
    assert "Nuovo trofeo!* 15 giorni di fila" in first.message.reply_text.call_args[0][0]
    assert "trofeo" not in second.message.reply_text.call_args[0][0]   # only the first 💩 of the day


def test_poop_without_milestone_has_no_trophy(seed, monkeypatch):
    seed({"mario": dict(days_from("2026-11-01", 3))})
    monkeypatch.setattr(messages, "now_rome", lambda: datetime(2026, 11, 4, 9, 0))
    upd = make_update(text="💩")
    run(messages.handle_message(upd, make_context()))
    assert "trofeo" not in upd.message.reply_text.call_args[0][0]


# ---------------------------------------------------------------- /trofei

def trofei_text(*args, **update_kwargs):
    upd = make_update(**update_kwargs)
    run(commands.trofei_command(upd, make_context(*args)))
    return upd.message.reply_text.call_args[0][0]


def test_trofei_group_board(seed):
    seed({"mario": {"2024-01-01": 3}, "luigi": {"2024-01-02": 1}})
    text = trofei_text()
    assert "Bacheca dei trofei" in text
    assert "*@mario*: 👑 1 · 🏅 1" in text
    assert "@luigi" not in text


def test_trofei_of_another_user(seed):
    seed({"mario": {"2024-01-01": 3}, "luigi": {"2024-01-02": 1}})
    assert "Trofei di @mario" in trofei_text("@mario", username="luigi")


def test_trofei_io_without_data(chat_id):
    text = trofei_text("io")
    assert "Trofei di @mario" in text
    assert "Ancora nessun trofeo." in text


def test_trofei_rejects_extra_arguments(seed):
    seed({"mario": {"2024-01-01": 3}})
    assert "Formato non valido" in trofei_text("@mario", "boh")


# ---------------------------------------------------------------- midnight announcement

def test_chat_ids_from_the_database_files(chat_id, isolated_folders):
    (isolated_folders / "db" / "-1001_bot_data.db.v1.bak").write_bytes(b"")
    (isolated_folders / "db" / "42_bot_data.db").write_bytes(b"")
    assert announce.chat_ids() == [chat_id, 42]


def test_announcement_of_the_month_just_ended(seed, chat_id):
    seed({"mario": {"2026-10-03": 4}, "luigi": {"2026-10-04": 2, "2026-11-01": 9}})
    text = announce.announcement(chat_id, date(2026, 11, 1))
    assert "ottobre 2026 è finito" in text
    assert "*@mario* con 4 💩" in text


def test_no_announcement_when_the_month_had_no_poop(seed, chat_id):
    seed({"mario": {"2026-09-03": 4}})
    assert announce.announcement(chat_id, date(2026, 11, 1)) is None


def test_dry_run_prints_without_sending(seed, capsys, monkeypatch):
    seed({"mario": {"2026-12-03": 4}})
    monkeypatch.setattr(announce, "application", None)   # any use of the bot would fail
    announce.main(["--date", "2027-01-01", "--dry-run"])
    out = capsys.readouterr().out
    assert "Buon anno! Benvenuto 2027!" in out
    assert "💩 dell'anno 2026: *@mario* con 4 💩" in out


def test_nothing_happens_when_it_is_not_the_first_day(seed, monkeypatch):
    seed({"mario": {"2026-10-03": 4}})
    monkeypatch.setattr(announce, "application", None)
    monkeypatch.setattr(announce.asyncio, "run", lambda *a: (_ for _ in ()).throw(AssertionError("no announce")))
    announce.main(["--date", "2026-11-02"])


def test_wait_for_midnight_only_when_it_is_close(monkeypatch):
    slept = []
    monkeypatch.setattr(announce.time, "sleep", slept.append)
    announce.wait_for_midnight(datetime(2026, 11, 30, 23, 0))   # winter: the task starts at 23:00
    announce.wait_for_midnight(datetime(2026, 7, 1, 0, 0, 5))   # summer: it is already midnight
    assert slept == [3600]


def test_send_failures_do_not_stop_the_other_chats(seed, chat_id, monkeypatch, isolated_folders):
    seed({"mario": {"2026-10-03": 4}})
    (isolated_folders / "db" / "42_bot_data.db").write_bytes(b"")   # not a database: reading it fails

    sent = []

    class FakeBot:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def send_message(self, chat, text, parse_mode=None):
            sent.append(chat)

    monkeypatch.setattr(announce, "application", type("App", (), {"bot": FakeBot()})())
    run(announce.announce(date(2026, 11, 1)))
    assert sent == [chat_id]
