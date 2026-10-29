"""The /collega command: link the old username-based history to Telegram users."""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import caccometro
import database
from conftest import make_context, make_legacy_db, make_tg_user, make_update

CHAT = -2002
ROWS = [
    ("mario", "2024-03-10", 2),
    ("Mario", "2024-03-11", 1),
    ("luigi", "2024-03-10", 4),
    (None, "2024-03-12", 3),
]


def run(coro):
    return asyncio.run(coro)


def legacy(tmp_path):
    make_legacy_db(str(tmp_path / "db"), CHAT, ROWS)


def reply_of(upd):
    return upd.message.reply_text.call_args[0][0]


# ---------------------------------------------------------------- listing

def test_list_shows_pending_history_and_matches(tmp_path):
    legacy(tmp_path)
    database.upsert_user(CHAT, 42, "mario", "Mario Rossi")
    upd = make_update(chat_id=CHAT, username="anna")
    run(caccometro.collega_command(upd, make_context()))
    text = reply_of(upd)
    assert "luigi: 4" in text
    assert "→ @mario (corrispondenza trovata)" in text
    assert "1 registrazioni senza username" in text


def test_list_with_nothing_to_link(chat_id):
    upd = make_update()
    run(caccometro.collega_command(upd, make_context()))
    assert reply_of(upd) == "Non ci sono dati storici da collegare."


def test_list_is_open_to_everybody(tmp_path):
    legacy(tmp_path)
    upd = make_update(chat_id=CHAT, username="anna")
    ctx = make_context(member_status="member")
    run(caccometro.collega_command(upd, ctx))
    ctx.bot.get_chat_member.assert_not_called()


# ---------------------------------------------------------------- permissions

def test_non_admin_cannot_link(tmp_path):
    legacy(tmp_path)
    upd = make_update(chat_id=CHAT, username="anna")
    run(caccometro.collega_command(upd, make_context("auto", member_status="member")))
    assert "Solo gli admin" in reply_of(upd)
    assert len(database.list_legacy_users(CHAT)) == 2


def test_admin_check_failure_is_treated_as_not_admin(tmp_path):
    legacy(tmp_path)
    ctx = make_context("auto")
    ctx.bot.get_chat_member = AsyncMock(side_effect=RuntimeError("telegram down"))
    upd = make_update(chat_id=CHAT, username="anna")
    run(caccometro.collega_command(upd, ctx))
    assert "Solo gli admin" in reply_of(upd)


def test_owner_can_link(tmp_path):
    legacy(tmp_path)
    database.upsert_user(CHAT, 42, "mario", "Mario")
    upd = make_update(chat_id=CHAT, username="anna")
    run(caccometro.collega_command(upd, make_context("auto", member_status="creator")))
    assert "Collegati" in reply_of(upd)


def test_private_chat_counts_as_admin(tmp_path):
    legacy(tmp_path)
    database.upsert_user(CHAT, 42, "mario", "Mario")
    upd = make_update(chat_id=CHAT, username="anna", chat_type="private")
    ctx = make_context("auto", member_status="member")
    run(caccometro.collega_command(upd, ctx))
    ctx.bot.get_chat_member.assert_not_called()
    assert "Collegati" in reply_of(upd)


# ---------------------------------------------------------------- /collega auto

def test_auto_links_matches_and_lists_the_rest(tmp_path):
    legacy(tmp_path)
    database.upsert_user(CHAT, 42, "mario", "Mario Rossi")
    upd = make_update(chat_id=CHAT, username="anna")
    run(caccometro.collega_command(upd, make_context("auto", member_status="administrator")))
    text = reply_of(upd)
    assert "→ @mario (2 giorni)" in text
    assert "Da collegare a mano" in text and "luigi: 4" in text
    assert database.get_count(42, "2024-03", CHAT) == 3


def test_auto_without_matches(tmp_path):
    legacy(tmp_path)
    upd = make_update(chat_id=CHAT, username="anna")
    run(caccometro.collega_command(upd, make_context("auto", member_status="administrator")))
    assert "Nessuna corrispondenza" in reply_of(upd)


# ---------------------------------------------------------------- link by reply

def test_admin_links_by_replying_to_the_person(tmp_path):
    legacy(tmp_path)
    person = make_tg_user(username=None, user_id=555, full_name="Luigi Verdi")
    upd = make_update(chat_id=CHAT, username="anna", reply_to=person)
    run(caccometro.collega_command(upd, make_context("luigi", member_status="administrator")))
    assert "Collegati 1 giorni di dati storici di «luigi» a Luigi Verdi" in reply_of(upd)
    assert database.get_count(555, "2024-03-10", CHAT) == 4


def test_old_username_can_be_written_with_at_sign(tmp_path):
    legacy(tmp_path)
    person = make_tg_user(username="gigi", user_id=555)
    upd = make_update(chat_id=CHAT, username="anna", reply_to=person)
    run(caccometro.collega_command(upd, make_context("@luigi", member_status="administrator")))
    assert database.get_count(555, "2024-03-10", CHAT) == 4


def test_link_without_a_reply_explains_how(tmp_path):
    legacy(tmp_path)
    upd = make_update(chat_id=CHAT, username="anna")
    run(caccometro.collega_command(upd, make_context("luigi", member_status="administrator")))
    assert "Rispondi a un messaggio" in reply_of(upd)
    assert len(database.list_legacy_users(CHAT)) == 2


def test_link_replying_to_a_bot_is_refused(tmp_path):
    legacy(tmp_path)
    upd = make_update(chat_id=CHAT, username="anna", reply_to=make_tg_user(username="x_bot", is_bot=True))
    run(caccometro.collega_command(upd, make_context("luigi", member_status="administrator")))
    assert "Rispondi a un messaggio" in reply_of(upd)


def test_link_unknown_old_username(tmp_path):
    legacy(tmp_path)
    upd = make_update(chat_id=CHAT, username="anna", reply_to=make_tg_user(username="gigi"))
    run(caccometro.collega_command(upd, make_context("nessuno", member_status="administrator")))
    assert "Nessun dato storico trovato per «nessuno»" in reply_of(upd)


def test_link_with_too_many_arguments(tmp_path):
    legacy(tmp_path)
    upd = make_update(chat_id=CHAT, username="anna", reply_to=make_tg_user(username="gigi"))
    run(caccometro.collega_command(upd, make_context("luigi", "mario", member_status="administrator")))
    assert "Formato non valido" in reply_of(upd)


# ---------------------------------------------------------------- hint in "no data" replies

def test_empty_ranking_suggests_linking_when_history_is_pending(tmp_path):
    legacy(tmp_path)
    upd = make_update(chat_id=CHAT, username="anna")
    run(caccometro.classifica_mese_command(upd, make_context("03-2024")))
    assert "/collega" in reply_of(upd)


def test_empty_ranking_has_no_hint_without_pending_history(chat_id):
    upd = make_update()
    run(caccometro.classifica_mese_command(upd, make_context("03-2024")))
    assert "/collega" not in reply_of(upd)


def test_collega_is_registered_as_a_command():
    handlers = caccometro.application.handlers[0]
    commands = {c for h in handlers if hasattr(h, "commands") for c in h.commands}
    assert "collega" in commands
