"""Only the group admins can change the counts of other members (issue #39)."""
import asyncio
import logging

import pytest

from caccometro import commands
from caccometro import database
from conftest import make_context, make_update, uid


def run(command, *args, member_status="member", chat_type="group"):
    upd = make_update(chat_type=chat_type)
    asyncio.run(command(upd, make_context(*args, member_status=member_status)))
    return upd.message.reply_text.call_args[0][0]


@pytest.mark.parametrize("command", [commands.aggiungi_command, commands.togli_command])
def test_a_member_cannot_change_the_counts_of_somebody_else(seed, chat_id, command):
    seed({"luigi": {"2024-03-10": 1}})
    reply = run(command, "@luigi", "10-03-2024")
    assert reply == "Solo gli admin del gruppo possono modificare i conteggi degli altri."
    assert database.get_count(uid("luigi"), "2024-03-10", chat_id) == 1


@pytest.mark.parametrize("status", ["administrator", "creator"])
def test_an_admin_can_change_the_counts_of_somebody_else(seed, chat_id, status):
    seed({"luigi": {"2024-03-10": 1}})
    run(commands.togli_command, "@luigi", "10-03-2024", member_status=status)
    assert database.get_count(uid("luigi"), "2024-03-10", chat_id) == 0


def test_a_member_can_change_their_own_counts(seed, chat_id):
    seed({"mario": {}})
    run(commands.aggiungi_command, "@mario", "10-03-2024")
    run(commands.aggiungi_command, "10-03-2024")
    assert database.get_count(uid("mario"), "2024-03-10", chat_id) == 2


def test_a_change_is_logged_with_target_day_and_old_and_new_count(seed, caplog):
    seed({"luigi": {"2024-03-10": 1}})
    with caplog.at_level(logging.INFO, logger="caccometro"):
        run(commands.aggiungi_command, "@luigi", "10-03-2024", member_status="administrator")
        run(commands.togli_command, "@luigi", "11-03-2024", member_status="administrator")
    lines = [r.getMessage() for r in caplog.records if r.getMessage().startswith("Count changed")]
    assert "/aggiungi @luigi 2024-03-10 1 -> 2" in lines[0]
    assert "/togli @luigi 2024-03-11 0 -> 0" in lines[1]
    assert "10-03-2024" not in caplog.text  # the text of the command is not logged
