"""Command argument validation and case-insensitive usernames."""
from datetime import datetime

import pytest

from caccometro import arguments, cmd_counts, cmd_leaderboards, cmd_records
from caccometro import database
from conftest import make_context, make_update, run, uid


def reply_of(command, *args, username="mario"):
    """Run a command and return the text of its reply; fail when it does not reply.

    Args:
        command (callable): the handler.
        *args: the arguments of the command.
        username (str): the sender.

    Returns:
        str: the reply.
    """
    upd = make_update(username=username)
    run(command(upd, make_context(*args)))
    assert upd.message.reply_text.called, "il comando deve rispondere, non sollevare eccezioni"
    return upd.message.reply_text.call_args[0][0]


@pytest.mark.parametrize("command", [cmd_records.records_command, cmd_counts.last_poop_command])
def test_username_argument_requires_at_sign(command):
    assert "Formato non valido" in reply_of(command, "luigi")
    assert "Formato non valido" in reply_of(command, "@")


@pytest.mark.parametrize("command", [
    cmd_leaderboards.leaderboard_month_command, cmd_leaderboards.stats_month_command])
@pytest.mark.parametrize("arg", ["13-2024", "00-2024", "abc", "2024", "13/24", "0-24", "03-2024-01", "03_2024", "03-2o24", "1-0150", "1-1969", "1-2101", "1-9999"])
def test_invalid_month_argument_replies_with_error(command, arg):
    assert "Formato data non valido" in reply_of(command, arg)


@pytest.mark.parametrize("command", [
    cmd_leaderboards.leaderboard_year_command, cmd_leaderboards.stats_year_command])
@pytest.mark.parametrize("arg", ["abc", "2", "20245", "-2024", "1800", "0150"])
def test_invalid_year_argument_replies_with_error(command, arg):
    assert "Formato anno non valido" in reply_of(command, arg)


@pytest.mark.parametrize("arg", ["03-2026", "3-2026", "03/2026", "3.2026", "03-26", "3/26", "03.26"])
def test_month_written_in_the_common_formats(arg):
    assert arguments._parse_month_arg(arg) == "03-2026"


@pytest.mark.parametrize("arg", ["05-03-2026", "5-3-2026", "05/03/2026", "5.3.2026", "05-03-26", "5/3/26", "05.03.26"])
def test_date_written_in_the_common_formats(arg):
    assert arguments._parse_date_arg(arg) == ("05-03-2026", "2026-03-05")


@pytest.mark.parametrize("arg", ["31-02-2026", "0-3-2026", "5-13-2026", "2026-03-05", "5/3/", "5-3-202", "5_3_2026", "a/b/c"])
def test_impossible_or_unknown_date_is_refused_with_examples(arg):
    with pytest.raises(ValueError, match="Esempi"):
        arguments._parse_date_arg(arg)


@pytest.mark.parametrize("arg", ["2026", "26"])
def test_year_with_two_or_four_digits(arg):
    assert arguments._parse_year_arg(arg) == "2026"


@pytest.mark.parametrize("arg", ["marzo 2026", "Marzo 2026", "marzo 26", "MARZO 2026", "march 2026", "March 26"])
def test_month_written_with_its_italian_or_english_name(arg):
    assert arguments._parse_month_arg(arg) == "03-2026"


def test_month_name_without_a_year_is_this_year():
    assert arguments._parse_month_arg("marzo") == f"03-{arguments.now_rome().year}"


@pytest.mark.parametrize("arg", ["marzi 2026", "mar 2026", "marzo 1969", "marzo 2101", "marzo 20245", "2026 marzo"])
def test_unknown_month_name_or_year_is_refused(arg):
    assert arguments._parse_month_arg(arg) is None


def test_month_command_joins_the_arguments(seed):
    seed({"mario": {"2024-03-10": 2}})
    upd = make_update()
    run(cmd_leaderboards.leaderboard_month_command(upd, make_context("marzo", "2024")))
    upd.message.reply_photo.assert_called_once()


def test_oggi_and_ieri_are_the_current_and_the_previous_day():
    today = arguments.now_rome().date()
    assert arguments._parse_date_arg("oggi")[1] == today.isoformat()
    assert arguments._parse_date_arg("Ieri")[1] == (today - arguments.timedelta(days=1)).isoformat()


def test_today_and_yesterday_are_accepted_in_every_chat():
    today = arguments.now_rome().date()
    assert arguments._parse_date_arg("today")[1] == today.isoformat()
    assert arguments._parse_date_arg("Yesterday")[1] == (today - arguments.timedelta(days=1)).isoformat()


def test_a_day_without_the_year_is_this_year():
    year = arguments.now_rome().year
    assert arguments._parse_date_arg("1.1") == (f"01-01-{year}", f"{year}-01-01")


def test_a_day_without_the_year_in_the_future_is_refused(monkeypatch):
    monkeypatch.setattr(arguments, "now_rome", lambda: datetime(2026, 11, 17, 12, 0))
    with pytest.raises(ValueError, match="futuro"):
        arguments._parse_date_arg("31/12")


def test_add_poop_accepts_a_slash_date_and_replies_with_the_standard_format(seed):
    upd = make_update()
    run(cmd_counts.add_poop_command(upd, make_context("5/3/26")))
    assert "05-03-2026" in upd.message.reply_text.call_args[0][0]


def test_month_argument_without_leading_zero_is_still_accepted(seed):
    seed({"mario": {"2024-03-10": 2}})
    upd = make_update()
    run(cmd_leaderboards.leaderboard_month_command(upd, make_context("3-2024")))
    upd.message.reply_photo.assert_called_once()


def test_username_lookup_is_case_insensitive(seed, chat_id):
    seed({"mario": {"2024-03-10": 2}})
    assert database.find_user_by_username(chat_id, "MARIO").user_id == uid("mario")
    assert database.find_user_by_username(chat_id, "Mario").name == "mario"
    assert database.find_user_by_username(chat_id, "sconosciuto") is None


def test_add_poop_with_different_case_updates_same_user(seed, chat_id):
    seed({"mario": {"2024-03-10": 1}})
    run(cmd_counts.add_poop_command(make_update(), make_context("@Mario", "10-03-2024")))
    ((user, count),) = database.get_rank(chat_id, "year", "2024")
    assert (user.name, count) == ("mario", 2)


def test_last_poop_with_different_case(seed):
    from datetime import datetime
    import pytz
    today = datetime.now(pytz.timezone("Europe/Rome")).strftime("%Y-%m-%d")
    seed({"luigi": {today: 1}})
    assert "oggi ha già" in reply_of(cmd_counts.last_poop_command, "@LUIGI")


@pytest.mark.parametrize("command", [
    cmd_counts.add_poop_command, cmd_counts.remove_poop_command, cmd_counts.day_count_command])
@pytest.mark.parametrize("arg", ["01-01-0001", "01-01-0150", "01-01-0999", "31-12-1969"])
def test_date_before_1970_is_refused_and_not_stored(command, arg, chat_id):
    assert "Errore" in reply_of(command, arg)
    assert database.get_all_user_rows(chat_id)[0] == {}


def test_date_in_the_future_is_refused_by_comparing_dates():
    with pytest.raises(ValueError, match="futuro"):
        arguments._parse_date_arg("01-01-2100")


def test_date_is_stored_with_a_four_digit_year():
    assert arguments._parse_date_arg("01-01-1970") == ("01-01-1970", "1970-01-01")
