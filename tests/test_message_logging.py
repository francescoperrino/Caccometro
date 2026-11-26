"""The log never contains what the members of a group write (issue #38)."""
import asyncio
import logging

from caccometro import messages
from conftest import make_context, make_update


def handle(text, caplog):
    """Handle a message and return what was logged.

    Args:
        text (str): the text of the message.
        caplog (pytest.LogCaptureFixture): pytest's fixture.

    Returns:
        str: the log text.
    """
    with caplog.at_level(logging.INFO, logger="caccometro"):
        asyncio.run(messages.handle_message(make_update(text=text), make_context()))
    return caplog.text


def test_messages_the_bot_does_not_answer_are_not_logged(caplog):
    assert "segreto" not in handle("ci vediamo stasera, è un segreto", caplog)
    assert caplog.records == []


def test_answered_messages_are_logged_without_their_text_or_the_reply(caplog):
    log = handle("💩 dopo il pranzo segreto", caplog)
    assert "segreto" not in log
    assert "💩 oggi" not in log  # nor the reply: the "done" line of the update is enough (#168)
