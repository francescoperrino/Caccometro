"""Users are identified by their Telegram user ID: a missing username is not a problem."""
import asyncio

import caccometro
import database
from conftest import make_context, make_tg_user, make_update, uid


def run(coro):
    return asyncio.run(coro)


def today():
    return database.now_rome().strftime("%Y-%m-%d")


def test_poop_from_user_without_username_is_counted_by_user_id(chat_id):
    upd = make_update(text="💩", username=None, user_id=777, full_name="Anna Rossi")
    run(caccometro.handle_message(upd, make_context()))
    assert database.get_count(777, today(), chat_id) == 1
    assert "Complimenti Anna Rossi" in upd.message.reply_text.call_args[0][0]


def test_sticker_from_user_without_username_is_counted(chat_id):
    run(caccometro.handle_message(
        make_update(sticker_emoji="💩", username=None, user_id=777, full_name="Anna Rossi"), make_context()))
    assert database.get_count(777, today(), chat_id) == 1


def test_plain_message_registers_the_user_and_stays_silent(chat_id):
    upd = make_update(text="ciao", username=None, user_id=777, full_name="Anna Rossi")
    run(caccometro.handle_message(upd, make_context()))
    upd.message.reply_text.assert_not_called()
    assert database.get_user(chat_id, 777) == database.User(777, None, "Anna Rossi")


def test_message_without_sender_is_ignored():
    upd = make_update(text="💩", has_from_user=False)
    run(caccometro.handle_message(upd, make_context()))
    upd.message.reply_text.assert_not_called()


def test_messages_from_bots_are_ignored(chat_id):
    upd = make_update(text="💩", username="GroupAnonymousBot", user_id=1087968824, is_bot=True)
    run(caccometro.handle_message(upd, make_context()))
    upd.message.reply_text.assert_not_called()
    assert database.get_user(chat_id, 1087968824) is None


def test_two_users_with_the_same_display_name_are_kept_apart(chat_id):
    for user_id in (101, 102):
        run(caccometro.handle_message(
            make_update(text="💩", username=None, user_id=user_id, full_name="Marco"), make_context()))
    run(caccometro.handle_message(
        make_update(text="💩", username=None, user_id=102, full_name="Marco"), make_context()))
    rank = database.get_rank(chat_id, "month", database.now_rome().strftime("%m-%Y"))
    assert [(user.user_id, count) for user, count in rank] == [(102, 2), (101, 1)]


def test_username_change_keeps_the_history(chat_id, seed):
    seed({"mario": {"2024-03-10": 2}})
    # same Telegram account (same ID), new username
    run(caccometro.handle_message(
        make_update(text="ciao", username="mario_new", user_id=uid("mario"), full_name="Mario"), make_context()))
    assert database.get_count(uid("mario"), "2024-03-10", chat_id) == 2
    ((user, count),) = database.get_rank(chat_id, "year", "2024")
    assert (user.username, count) == ("mario_new", 2)


def test_commands_work_for_users_without_username(chat_id):
    sender = dict(username=None, user_id=777, full_name="Anna Rossi")
    run(caccometro.handle_message(make_update(text="💩", **sender), make_context()))
    upd = make_update(**sender)
    run(caccometro.record_command(upd, make_context()))
    assert "Record per Anna Rossi" in upd.message.reply_text.call_args[0][0]
    upd = make_update(**sender)
    run(caccometro.costipazione_command(upd, make_context()))
    assert "Anna Rossi oggi hai fatto" in upd.message.reply_text.call_args[0][0]
    upd = make_update(**sender)
    run(caccometro.classifica_mese_command(upd, make_context()))
    assert "Anna Rossi" in upd.message.reply_text.call_args[0][0]


def test_markdown_characters_in_names_are_escaped(chat_id):
    upd = make_update(text="💩", username=None, user_id=5, full_name="Mario_*[x")
    run(caccometro.handle_message(upd, make_context()))
    assert "Mario\\_\\*\\[x" in upd.message.reply_text.call_args[0][0]


def test_target_by_username_requires_a_known_user(seed):
    upd = make_update()
    run(caccometro.aggiungi_command(upd, make_context("@sconosciuto", "10-03-2024")))
    assert "Non conosco @sconosciuto" in upd.message.reply_text.call_args[0][0]


def test_target_by_reply_works_for_users_without_username(chat_id):
    replied = make_tg_user(username=None, user_id=888, full_name="Giulia Bianchi")
    upd = make_update(reply_to=replied)
    run(caccometro.aggiungi_command(upd, make_context("10-03-2024")))
    assert database.get_count(888, "2024-03-10", chat_id) == 1
    assert "Giulia Bianchi" in upd.message.reply_text.call_args[0][0]


def test_reply_to_a_bot_message_falls_back_to_the_sender(chat_id):
    replied = make_tg_user(username="some_bot", user_id=999, is_bot=True)
    upd = make_update(reply_to=replied)
    run(caccometro.aggiungi_command(upd, make_context("10-03-2024")))
    assert database.get_count(uid("mario"), "2024-03-10", chat_id) == 1
    assert database.get_user(chat_id, 999) is None
