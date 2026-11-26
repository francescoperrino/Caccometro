"""/records of the whole group: who holds each record and who leads right now."""
import asyncio
import random
from datetime import date, timedelta

from caccometro import cmd_records
from caccometro import database
from caccometro.analysis import Holder, Leaders, Period, analyze_group, analyze_user
from conftest import make_context, make_tg_user, make_update, uid
from caccometro.formatting import format_group_record

TODAY = date(2024, 4, 15)

MARIO = [("2024-01-01", 1), ("2024-01-02", 2), ("2024-01-03", 1), ("2024-01-07", 1), ("2024-02-10", 3),
         ("2024-03-01", 1), ("2024-04-14", 2), ("2024-04-15", 1)]
LUIGI = [("2024-01-10", 2), ("2024-02-10", 5), ("2024-03-10", 1), ("2024-03-11", 1), ("2024-04-13", 1), ("2024-04-14", 1)]
ANNA = [("2024-01-05", 1), ("2024-03-05", 1)]
EX = [("2023-01-05", 4), ("2023-01-06", 1)]       # left the group a year ago
ROWS = {"mario": MARIO, "luigi": LUIGI, "anna": ANNA, "ex": EX}


def run(coro):
    return asyncio.run(coro)


def keys(leaders):
    return [holder.key for holder in leaders.holders]


# ---------------------------------------------------------------- analysis

def test_records_of_all_times_include_every_user():
    board = analyze_group(ROWS, TODAY)
    assert board.daily == Leaders(5, [Holder("luigi", [date(2024, 2, 10)])])
    assert board.streak_days.value == 3 and keys(board.streak_days) == ["mario"]
    assert board.streak_count.value == 5 and keys(board.streak_count) == ["luigi", "ex"]     # a tie keeps both
    assert board.gap_days.value == 59 and keys(board.gap_days) == ["anna"]
    assert board.gap_days.holders[0].when == [Period(date(2024, 1, 6), date(2024, 3, 4))]


def test_best_month_ties_keep_every_holder_with_its_own_months():
    board = analyze_group(ROWS, TODAY)
    assert board.best_month.value == 5
    assert {h.key: h.when for h in board.best_month.holders} == {
        "mario": [(2024, 1)], "luigi": [(2024, 2)], "ex": [(2023, 1)]}


def test_worst_month_is_the_lowest_value_among_users():
    board = analyze_group(ROWS, TODAY)
    assert board.worst_month.value == 0                   # anna: nothing in February
    assert keys(board.worst_month) == ["anna"]
    assert board.worst_month.holders[0].when == [(2024, 2)]


def test_users_without_enough_months_are_left_out_of_the_worst_month():
    board = analyze_group({"new": [("2024-04-10", 1)], "old": [("2024-01-10", 2), ("2024-02-10", 1)]}, TODAY)
    assert keys(board.worst_month) == ["old"] and board.worst_month.value == 1


def test_right_now_looks_only_at_active_users():
    board = analyze_group(ROWS, TODAY)
    assert board.today == Leaders(1, [Holder("mario", [])])
    assert board.active_streak.value == 2 and keys(board.active_streak) == ["mario", "luigi"]
    assert board.active_streak.holders[0].when == [Period(date(2024, 4, 14), date(2024, 4, 15))]
    assert board.active_streak.holders[1].when == [Period(date(2024, 4, 13), date(2024, 4, 14))]   # ended yesterday
    assert board.active_gap.value == 41 and keys(board.active_gap) == ["anna"]
    # "ex" has the longest pause of all, but has not been seen for a year: not part of "right now"
    assert "ex" not in keys(board.active_gap)


def test_a_user_is_active_for_ninety_days():
    rows = {"a": [("2024-01-16", 1)], "b": [("2024-01-15", 1)]}      # 90 and 91 days before April 15
    board = analyze_group(rows, TODAY)
    assert keys(board.active_gap) == ["a"] and board.active_gap.value == 90


def test_an_empty_group_has_no_records_and_users_without_counts_are_ignored():
    board = analyze_group({"nobody": [("2024-04-10", 0)]}, TODAY)
    assert all(value is None for value in board)


def test_group_records_agree_with_the_single_user_records_on_random_data():
    rng = random.Random(9)
    for _ in range(100):
        users = {}
        for name in "abcde"[:rng.randint(1, 5)]:
            start = date(2023, 6, 1) + timedelta(days=rng.randint(0, 200))
            users[name] = [((start + timedelta(days=i)).isoformat(), rng.randint(1, 4))
                           for i in range(rng.randint(1, 250)) if rng.random() < 0.5] or [(start.isoformat(), 1)]
        today = date(2024, 6, 1)
        board = analyze_group(users, today)
        singles = {name: analyze_user(rows, today) for name, rows in users.items()}
        assert board.daily.value == max(r.daily.value for r in singles.values())
        assert board.streak_days.value == max(r.streak_days.value for r in singles.values())
        assert board.streak_count.value == max(r.streak_count.value for r in singles.values())
        for holder in board.daily.holders:
            assert singles[holder.key].daily.value == board.daily.value
        worst = [r.worst_month.value for r in singles.values() if r.worst_month]
        assert (board.worst_month.value if board.worst_month else None) == (min(worst) if worst else None)


# ---------------------------------------------------------------- message

NAMES = {"mario": "@mario", "luigi": "@luigi", "anna": "Anna R.", "ex": "@ex"}


def test_group_message():
    assert format_group_record(analyze_group(ROWS, TODAY), NAMES) == (
        "🏆 *Record del gruppo* 🏆\n"
        "\n"
        "🥵 Più 💩 in un giorno: 5 volte — *@luigi* (10-02-2024)\n"
        "🤩 Più 💩 in un mese: 5 volte — *@mario* (01-2024), *@luigi* (02-2024), *@ex* (01-2023)\n"
        "😭 Meno 💩 in un mese: 0 volte — *Anna R.* (02-2024)\n"
        "🥳 Serie più lunga: 3 giorni consecutivi — *@mario* (01-01-2024 - 03-01-2024)\n"
        "🫣 Più 💩 in una serie: 5 volte — *@luigi* (10-02-2024), *@ex* (05-01-2023 - 06-01-2023)\n"
        "🤢 Pausa più lunga: 59 giorni consecutivi — *Anna R.* (06-01-2024 - 04-03-2024)\n"
        "\n"
        "📍 *Adesso*\n"
        "💩 Oggi: 1 volta — *@mario*\n"
        "🔥 Serie in corso più lunga: 2 giorni — *@mario* (14-04-2024 - 15-04-2024), *@luigi* (13-04-2024 - 14-04-2024)\n"
        "🐢 Pausa in corso più lunga: 41 giorni — *Anna R.*\n"
        "\n"
        "Il tuo: /record io — di un altro: /record @username (o rispondi a un suo messaggio)"
    )


def test_many_holders_are_summarized():
    rows = {name: [("2024-01-10", 2), ("2024-02-10", 1)] for name in "abcdef"}
    text = format_group_record(analyze_group(rows, TODAY), {name: f"@{name}" for name in rows})
    assert "*@a* (10-01-2024), *@b* (10-01-2024), *@c* (10-01-2024) e altri 3" in text


def test_a_holder_with_many_months_is_abbreviated():
    rows = {"a": [("2023-01-10", 3), ("2024-04-10", 1)]}            # 14 empty months in between
    text = format_group_record(analyze_group(rows, date(2024, 5, 1)), {"a": "@a"})
    assert "😭 Meno 💩 in un mese: 0 volte — *@a* (03-2024; 02-2024…)" in text


def test_message_without_the_right_now_block_when_nobody_is_active():
    text = format_group_record(analyze_group({"ex": EX}, TODAY), {"ex": "@ex"})
    assert "📍" not in text
    assert "🥵 Più 💩 in un giorno: 4 volte — *@ex* (05-01-2023)" in text


# ---------------------------------------------------------------- database

def test_get_all_user_rows_groups_rows_by_user_in_date_order(seed, chat_id):
    seed({"mario": {"2024-03-10": 2, "2024-01-05": 1}, "luigi": {"2024-02-01": 4}, "anna": {}})
    rows, users = database.get_all_user_rows(chat_id)
    assert rows == {uid("mario"): [("2024-01-05", 1), ("2024-03-10", 2)], uid("luigi"): [("2024-02-01", 4)]}
    assert set(users) == {uid("mario"), uid("luigi"), uid("anna")}
    assert users[uid("anna")].name == "anna"


def test_get_all_user_rows_reads_the_database_once(seed, chat_id, monkeypatch):
    seed({"mario": {"2024-03-10": 2}})
    calls = []
    real = database._connect
    monkeypatch.setattr(database, "_connect", lambda chat: calls.append(chat) or real(chat))
    database.get_all_user_rows(chat_id)
    assert len(calls) == 1


# ---------------------------------------------------------------- command

def record(*args, reply_to=None, username="mario"):
    upd = make_update(username=username, reply_to=reply_to)
    run(cmd_records.records_command(upd, make_context(*args)))
    return upd.message.reply_text.call_args[0][0]


def seed_group(seed):
    today = database.now_rome().date()
    day = lambda n: (today - timedelta(days=n)).strftime("%Y-%m-%d")      # noqa: E731
    seed({"mario": {day(0): 2, day(1): 1, "2020-01-10": 3, "2020-02-10": 1},
          "luigi": {day(40): 1, "2020-03-10": 5, "2020-04-10": 2}})


def test_record_without_arguments_shows_the_group(seed):
    seed_group(seed)
    text = record()
    assert text.startswith("🏆 *Record del gruppo* 🏆")
    assert "@luigi" in text and "@mario" in text
    assert "📍 *Adesso*" in text


def test_record_io_shows_the_record_of_the_sender(seed):
    seed_group(seed)
    assert "Record per @mario" in record("io")
    assert "Record per @mario" in record("me")
    assert "Record per @luigi" in record("IO", username="luigi")


def test_record_of_a_username_shows_that_user(seed):
    seed_group(seed)
    text = record("@luigi")
    assert "Record per @luigi" in text and "↳ Oggi:" in text


def test_record_replying_to_a_message_shows_that_person(seed):
    seed_group(seed)
    assert "Record per @luigi" in record(reply_to=make_tg_user(username="luigi"))


def test_record_io_wins_over_a_reply(seed):
    seed_group(seed)
    assert "Record per @mario" in record("io", reply_to=make_tg_user(username="luigi"))


def test_record_in_an_empty_chat(chat_id):
    assert record() == "🤷 Nessun dato disponibile."


def test_record_of_someone_without_data_says_so(seed):
    seed({"mario": {"2024-03-10": 1}, "luigi": {}})
    assert record("@luigi") == "🤷 Nessun dato disponibile per @luigi."


def test_group_message_escapes_markdown_in_names(chat_id):
    database.upsert_user(chat_id, 5, None, "Mario_*[x")
    database.add_count(5, "2024-03-10", 2, chat_id)
    assert "*Mario*\\_\\*\\[*x*" in record()


def test_group_record_reads_the_database_a_handful_of_times(seed, monkeypatch):
    seed_group(seed)
    calls = []
    real = database._connect
    monkeypatch.setattr(database, "_connect", lambda chat: calls.append(chat) or real(chat))
    record()
    assert len(calls) <= 3      # sender registration + one read of all the rows
