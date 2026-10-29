"""Users without @username / messages without a sender must not block the bot."""
import asyncio
import sqlite3
import os

import pytest

import caccometro
import database
from conftest import make_context, make_update


def run(coro):
    return asyncio.run(coro)


def insert_null_username_row(chat_id, folder, date="2024-03-10", count=2):
    """Legacy row with a NULL username, as the old version may have written it."""
    conn = sqlite3.connect(os.path.join(folder, f"{chat_id}_bot_data.db"))
    conn.execute("INSERT INTO user_count (username, date, count) VALUES (NULL, ?, ?)", (date, count))
    conn.commit()
    conn.close()


def test_poop_from_user_without_username_is_not_stored(chat_id):
    upd = make_update(text="💩", username=None)
    run(caccometro.handle_message(upd, make_context()))
    assert database.get_rank(chat_id, "year", "2024") == []
    upd.message.reply_text.assert_called_once()
    assert "username" in upd.message.reply_text.call_args[0][0].lower()


def test_sticker_from_user_without_username_is_not_stored(chat_id):
    upd = make_update(sticker_emoji="💩", username=None)
    run(caccometro.handle_message(upd, make_context()))
    upd.message.reply_text.assert_called_once()


def test_plain_message_from_user_without_username_is_silent():
    upd = make_update(text="ciao", username=None)
    run(caccometro.handle_message(upd, make_context()))
    upd.message.reply_text.assert_not_called()


def test_message_without_sender_does_not_crash():
    upd = make_update(text="💩", has_from_user=False)
    run(caccometro.handle_message(upd, make_context()))
    upd.message.reply_text.assert_not_called()


@pytest.mark.parametrize("command,args", [
    (caccometro.classifica_mese_command, ["03-2024"]),
    (caccometro.classifica_anno_command, ["2024"]),
    (caccometro.record_command, []),
    (caccometro.costipazione_command, []),
    (caccometro.conto_giorno_command, []),
    (caccometro.aggiungi_command, ["10-03-2024"]),
    (caccometro.togli_command, ["10-03-2024"]),
])
def test_commands_from_user_without_username_reply_with_notice(command, args):
    upd = make_update(username=None)
    run(command(upd, make_context(*args)))
    upd.message.reply_text.assert_called_once()
    assert "username" in upd.message.reply_text.call_args[0][0].lower()


def test_commands_without_sender_do_not_crash():
    upd = make_update(has_from_user=False)
    run(caccometro.record_command(upd, make_context()))
    upd.message.reply_text.assert_not_called()


def test_rank_with_legacy_null_username_row_does_not_crash(chat_id, seed, isolated_folders):
    seed({"mario": {"2024-03-10": 1}})
    insert_null_username_row(chat_id, str(isolated_folders / "db"))
    upd = make_update()
    run(caccometro.classifica_mese_command(upd, make_context("03-2024")))
    assert upd.message.reply_text.called


def test_statistics_with_legacy_null_username_row_does_not_crash(chat_id, seed, isolated_folders):
    seed({"mario": {"2024-03-10": 1}})
    insert_null_username_row(chat_id, str(isolated_folders / "db"))
    upd = make_update()
    run(caccometro.statistiche_mese_command(upd, make_context("03-2024")))
    assert upd.message.reply_text.called
