"""Funny replies (#160): the sentence around the count depends on the Italian hour and on the count of the day."""
import asyncio
from datetime import datetime

import pytz

from caccometro import database, formatting, messages
from caccometro.formatting import poop_pool, poop_sentence
from conftest import make_context, make_update

SENTENCES = formatting._poop_sentences()
ROME = pytz.timezone("Europe/Rome")


def test_the_time_slots_start_at_the_right_hour():
    slots = {h: formatting._slot(h) for h in (0, 4, 5, 8, 9, 11, 12, 14, 15, 18, 19, 23)}
    assert slots == {0: "night", 4: "night", 5: "early", 8: "early", 9: "morning", 11: "morning", 12: "lunch",
                     14: "lunch", 15: "afternoon", 18: "afternoon", 19: "evening", 23: "evening"}


def test_the_second_poop_is_answered_by_the_slot_and_the_generic_sentences():
    assert poop_pool(13, 2) == SENTENCES["lunch"] + SENTENCES["any"]


def test_the_first_and_the_third_poop_use_their_own_sentences_of_the_slot_when_there_are_some():
    assert poop_pool(3, 1) == SENTENCES[("first", "night")]
    assert poop_pool(13, 3) == SENTENCES[("third", "lunch")]
    assert poop_pool(13, 7) == SENTENCES[("third", "lunch")]


def test_otherwise_they_add_their_count_sentences_to_those_of_the_slot():
    assert poop_pool(10, 1) == SENTENCES["morning"] + SENTENCES["any"] + SENTENCES[("first", None)]
    assert poop_pool(20, 3) == SENTENCES["evening"] + SENTENCES["any"] + SENTENCES[("third", None)]


def test_every_sentence_has_the_name_and_every_pool_is_used_in_full():
    assert all("{name}" in s for pool in SENTENCES.values() for s in pool)
    seen = {poop_sentence("X", 10, 2) for _ in range(300)}
    assert seen == {s.format(name="X") for s in poop_pool(10, 2)}


def reply_at(hour, text="💩"):
    sent = ROME.localize(datetime(2026, 11, 19, hour, 30))
    upd = make_update(text=text, date=sent)
    asyncio.run(messages.handle_message(upd, make_context()))
    return upd.message.reply_text.call_args[0][0]


def test_the_reply_always_has_the_count_and_the_reminder(chat_id):
    for count in (1, 2, 3):
        reply = reply_at(7)
        assert f"💩 oggi: {count}\n" in reply and reply.endswith("conquistare la zona!")
        assert reply.split("\n")[0].format(name="") != ""


def test_the_reply_follows_the_italian_hour_of_the_message(chat_id):
    first_line = reply_at(3).split("\n")[0]  # the first 💩 at 3:30 has only night sentences
    assert first_line in {s.format(name="@mario") for s in SENTENCES[("first", "night")]}


def test_the_english_reply(chat_id):
    database.set_language(chat_id, "en")
    assert "💩 today: 1\n" in reply_at(10)
