"""Names with Markdown characters in bold (issue #122).

Checked on the development bot (Telegram sends the parsed text back): legacy Markdown does not allow an escaped
character inside bold (the backslash is shown) and an unescaped `*` breaks the message. bold() closes the bold
around each escaped character instead.
"""
import asyncio

import pytest

from caccometro import cmd_records, database, formatting
from caccometro.chat import escape_md
from caccometro.formatting import ESCAPED, _bold
from conftest import make_context, make_update

NAME = "Mario_*[x"


def bold_segments(text):
    """The bold segments of a legacy Markdown text; fails if an escaped character is inside one or a `*` is left open."""
    segments, current = [], None
    for part in ESCAPED.split(text):
        if ESCAPED.fullmatch(part):
            assert current is None, f"escaped character inside bold: {text!r}"
            continue
        for i, piece in enumerate(part.split("*")):
            if i and current is None:
                current = ""
            elif i:
                segments.append(current)
                current = None
            if current is not None:
                current += piece
    assert current is None, f"bold not closed: {text!r}"
    return segments


def test_the_escaped_character_stays_outside_the_bold():
    assert _bold(escape_md("@mario_rossi")) == "*@mario*\\_*rossi*"
    assert _bold(escape_md(NAME)) == "*Mario*\\_\\*\\[*x*"
    assert _bold("plain") == "*plain*"


@pytest.mark.parametrize("name", ["@mario_rossi", "a*b", "a`b", "a[b", "_x_", "**", "[x](y)", "a_ _b", NAME])
def test_bold_is_well_formed(name):
    bold_segments(f"🥇 {_bold(escape_md(name))}: 5")


def run(command, *args):
    upd = make_update(username=None, user_id=5, full_name=NAME)
    asyncio.run(command(upd, make_context(*args)))
    return upd.message.reply_text.call_args[0][0]


def test_messages_with_the_name_in_bold_are_well_formed(chat_id):
    database.upsert_user(chat_id, 5, None, NAME)
    database.add_count(5, "2024-03-10", 2, chat_id)
    bold_segments(formatting.ranked_line(1, escape_md(NAME), 2))
    for command, args in ((cmd_records.records_command, ()), (cmd_records.records_command, ("io",)),
                          (cmd_records.trophies_command, ()), (cmd_records.trophies_command, ("io",))):
        assert bold_segments(run(command, *args)), (command, args)
