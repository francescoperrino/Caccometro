"""One database read per command instead of one per user and day; atomic count updates."""
import asyncio
import threading

import pytest

import caccometro
import database
import utils
from conftest import make_context, make_update, uid


def run(coro):
    return asyncio.run(coro)


@pytest.fixture
def connections(monkeypatch):
    """Counts how many database connections are opened."""
    counter = {"n": 0}
    real_connect = database._connect

    def counting_connect(chat):
        counter["n"] += 1
        return real_connect(chat)

    monkeypatch.setattr(database, "_connect", counting_connect)
    return counter


def seed_busy_chat(seed, names=("mario", "luigi", "anna", "giulia", "carlo")):
    seed({name: {"2024-03-10": 2, "2024-03-20": 1, "2024-07-01": 3, "2024-12-31": 1} for name in names})


# ---------------------------------------------------------------- get_daily_counts

def test_daily_counts_for_a_month(seed, chat_id):
    seed({"mario": {"2024-03-10": 2, "2024-03-20": 1, "2024-04-01": 5}, "luigi": {"2024-03-11": 4}})
    daily = database.get_daily_counts(chat_id, "month", "03-2024")
    assert daily == {uid("mario"): {"2024-03-10": 2, "2024-03-20": 1}, uid("luigi"): {"2024-03-11": 4}}


def test_daily_counts_for_a_year_include_first_and_last_day(seed, chat_id):
    seed({"mario": {"2023-12-31": 9, "2024-01-01": 1, "2024-12-31": 2, "2025-01-01": 9}})
    assert database.get_daily_counts(chat_id, "year", "2024") == {uid("mario"): {"2024-01-01": 1, "2024-12-31": 2}}


def test_daily_counts_of_an_empty_period(seed, chat_id):
    seed({"mario": {"2024-03-10": 2}})
    assert database.get_daily_counts(chat_id, "month", "05-2024") == {}


def test_daily_counts_accept_month_without_leading_zero(seed, chat_id):
    seed({"mario": {"2024-03-10": 2}})
    assert database.get_daily_counts(chat_id, "month", "3-2024") == {uid("mario"): {"2024-03-10": 2}}


# ---------------------------------------------------------------- number of database accesses

def test_statistics_read_the_database_once(seed, chat_id, connections):
    seed_busy_chat(seed)
    connections["n"] = 0
    database.get_statistics(chat_id, "year", "2024")
    assert connections["n"] == 1


def test_daily_counts_and_rank_read_the_database_once_each(seed, chat_id, connections):
    seed_busy_chat(seed)
    connections["n"] = 0
    database.get_daily_counts(chat_id, "year", "2024")
    database.get_rank(chat_id, "year", "2024")
    assert connections["n"] == 2


@pytest.mark.parametrize("command,arg", [
    (caccometro.classifica_anno_command, "2024"),
    (caccometro.classifica_mese_command, "03-2024"),
    (caccometro.statistiche_anno_command, "2024"),
    (caccometro.statistiche_mese_command, "03-2024"),
])
def test_chart_commands_use_a_handful_of_connections(seed, connections, command, arg):
    seed_busy_chat(seed)
    upd = make_update()
    connections["n"] = 0
    run(command(upd, make_context(arg)))
    upd.message.reply_photo.assert_called_once()
    assert connections["n"] <= 5   # it used to be hundreds (month) or thousands (year)


# ---------------------------------------------------------------- charts built from the daily counts

def table_of_rank_chart(monkeypatch, rank, daily, period, date, chat_id):
    """Run generate_rank_chart and return the text of its table."""
    captured = {}
    real_savefig = utils.plt.savefig

    def capture(*args, **kwargs):
        cells = utils.plt.gcf().axes[0].tables[0].get_celld()
        rows = max(r for r, _ in cells) + 1
        cols = max(c for _, c in cells) + 1
        captured["table"] = [[cells[(r, c)].get_text().get_text() for c in range(cols)] for r in range(rows)]
        return real_savefig(*args, **kwargs)

    monkeypatch.setattr(utils.plt, "savefig", capture)
    utils.generate_rank_chart(rank, daily, chat_id, period, date)
    return captured["table"]


def test_year_table_shows_monthly_and_total_counts(seed, chat_id, monkeypatch):
    seed({"mario": {"2024-03-10": 2, "2024-03-20": 1, "2024-04-01": 5, "2023-12-31": 9}})
    rank = database.get_rank(chat_id, "year", "2024")
    daily = database.get_daily_counts(chat_id, "year", "2024")
    table = table_of_rank_chart(monkeypatch, rank, daily, "year", "2024", chat_id)
    header, row = table[0], table[1]
    assert header[0] == "" and header[-1] == "Total"
    assert row[0] == "mario"
    assert row[1:-1] == ["0", "0", "3", "5", "0", "0", "0", "0", "0", "0", "0", "0"]   # Jan..Dec
    assert row[-1] == "8"


def test_month_table_shows_daily_and_total_counts(seed, chat_id, monkeypatch):
    seed({"mario": {"2024-03-10": 2, "2024-03-20": 1}})
    rank = database.get_rank(chat_id, "month", "03-2024")
    daily = database.get_daily_counts(chat_id, "month", "03-2024")
    row = table_of_rank_chart(monkeypatch, rank, daily, "month", "03-2024", chat_id)[1]
    assert row[10] == "2" and row[20] == "1"       # columns are days 1..31
    assert row[-1] == "3"


def test_rank_chart_tolerates_a_user_without_daily_counts(chat_id, isolated_folders):
    rank = [(database.User(uid("mario"), "mario", "Mario"), 0)]
    utils.generate_rank_chart(rank, {}, chat_id, "month", "03-2024")


# ---------------------------------------------------------------- add_count

def test_add_count_increments_and_returns_old_and_new(chat_id):
    assert database.add_count(1, "2024-03-10", 1, chat_id) == (0, 1)
    assert database.add_count(1, "2024-03-10", 1, chat_id) == (1, 2)
    assert database.get_count(1, "2024-03-10", chat_id) == 2


def test_add_count_decrements_and_removes_the_row_at_zero(chat_id):
    database.add_count(1, "2024-03-10", 1, chat_id)
    assert database.add_count(1, "2024-03-10", -1, chat_id) == (1, 0)
    assert database.get_record(1, chat_id) == []


def test_add_count_never_goes_below_zero_and_creates_no_row(chat_id):
    assert database.add_count(1, "2024-03-10", -1, chat_id) == (0, 0)
    assert database.get_record(1, chat_id) == []


def test_add_count_keeps_users_and_days_separate(chat_id):
    database.add_count(1, "2024-03-10", 1, chat_id)
    database.add_count(2, "2024-03-10", 1, chat_id)
    database.add_count(1, "2024-03-11", 1, chat_id)
    assert database.get_count(1, "2024-03", chat_id) == 2
    assert database.get_count(2, "2024-03", chat_id) == 1


def test_concurrent_increments_are_not_lost(chat_id):
    threads_n, per_thread = 8, 15
    errors = []

    def worker():
        try:
            for _ in range(per_thread):
                database.add_count(1, "2024-03-10", 1, chat_id)
        except Exception as exc:  # pragma: no cover - reported below
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(threads_n)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert not errors
    assert database.get_count(1, "2024-03-10", chat_id) == threads_n * per_thread


# ---------------------------------------------------------------- handlers on top of add_count

def test_togli_from_one_goes_to_zero(chat_id, seed):
    seed({"mario": {"2024-03-10": 1}})
    upd = make_update()
    run(caccometro.togli_command(upd, make_context("10-03-2024")))
    assert "aggiornato a 0" in upd.message.reply_text.call_args[0][0]
    assert database.get_count(uid("mario"), "2024-03-10", chat_id) == 0


def test_togli_at_zero_is_refused(chat_id, seed):
    seed({"mario": {}})
    upd = make_update()
    run(caccometro.togli_command(upd, make_context("10-03-2024")))
    assert "era già 0" in upd.message.reply_text.call_args[0][0]
    assert database.get_record(uid("mario"), chat_id) == []


def test_aggiungi_reports_the_new_count(chat_id, seed):
    seed({"mario": {"2024-03-10": 2}})
    upd = make_update()
    run(caccometro.aggiungi_command(upd, make_context("10-03-2024")))
    assert "aggiornato a 3" in upd.message.reply_text.call_args[0][0]


def test_poop_messages_sent_at_the_same_time_are_all_counted(chat_id):
    today = database.now_rome().strftime("%Y-%m-%d")
    sender = caccometro.User(uid("mario"), "mario", "Mario")
    threads = [threading.Thread(target=caccometro.record_poop, args=(sender, chat_id)) for _ in range(12)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert database.get_count(uid("mario"), today, chat_id) == 12
