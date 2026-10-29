"""Command argument validation and case-insensitive usernames."""
import asyncio

import pytest

import caccometro
import database
from conftest import make_context, make_update


def run(coro):
    return asyncio.run(coro)


def reply_of(command, *args, username="mario"):
    upd = make_update(username=username)
    run(command(upd, make_context(*args)))
    assert upd.message.reply_text.called, "il comando deve rispondere, non sollevare eccezioni"
    return upd.message.reply_text.call_args[0][0]


@pytest.mark.parametrize("command", [caccometro.record_command, caccometro.costipazione_command])
def test_username_argument_requires_at_sign(command):
    assert "Formato non valido" in reply_of(command, "luigi")
    assert "Formato non valido" in reply_of(command, "@")


@pytest.mark.parametrize("command", [
    caccometro.classifica_mese_command, caccometro.statistiche_mese_command])
@pytest.mark.parametrize("arg", ["13-2024", "00-2024", "abc", "2024", "03-24", "03-2024-01"])
def test_invalid_month_argument_replies_with_error(command, arg):
    assert "Formato data non valido" in reply_of(command, arg)


@pytest.mark.parametrize("command", [
    caccometro.classifica_anno_command, caccometro.statistiche_anno_command])
@pytest.mark.parametrize("arg", ["abc", "24", "20245", "-2024", "1800"])
def test_invalid_year_argument_replies_with_error(command, arg):
    assert "Formato anno non valido" in reply_of(command, arg)


def test_month_argument_without_leading_zero_is_still_accepted(seed):
    seed({"mario": {"2024-03-10": 2}})
    upd = make_update()
    run(caccometro.classifica_mese_command(upd, make_context("3-2024")))
    upd.message.reply_photo.assert_called_once()


def test_username_lookup_is_case_insensitive(seed, chat_id):
    seed({"mario": {"2024-03-10": 2}})
    assert database.get_count("MARIO", "2024-03-10", chat_id) == 2
    assert database.get_record("Mario", chat_id) == [("2024-03-10", 2)]


def test_update_count_keeps_stored_spelling_and_does_not_duplicate(seed, chat_id):
    seed({"mario": {"2024-03-10": 2}})
    database.update_count("MARIO", "2024-03-10", 3, chat_id)
    assert database.get_rank(chat_id, "year", "2024") == [("mario", 3)]


def test_aggiungi_with_different_case_updates_same_user(seed, chat_id):
    seed({"mario": {"2024-03-10": 1}})
    run(caccometro.aggiungi_command(make_update(), make_context("@Mario", "10-03-2024")))
    assert database.get_rank(chat_id, "year", "2024") == [("mario", 2)]


def test_costipazione_with_different_case(seed):
    from datetime import datetime
    import pytz
    today = datetime.now(pytz.timezone("Europe/Rome")).strftime("%Y-%m-%d")
    seed({"luigi": {today: 1}})
    assert "oggi hai fatto" in reply_of(caccometro.costipazione_command, "@LUIGI")
