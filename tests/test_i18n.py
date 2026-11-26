"""Languages (#10): /language chooses the language of a chat, every sentence has a translation."""
import ast
import asyncio
import string
from datetime import date
from pathlib import Path

import pytest

from caccometro import announce, cmd_settings, database, i18n
from conftest import make_context, make_update

ROOT = Path(__file__).resolve().parent.parent


def run(command, *args, member_status="member", chat_type="group", chat_id=None):
    """Run a command and return the text of its reply.

    Args:
        command (callable): the handler.
        *args: the arguments of the command.
        member_status (str): the status of the sender in the chat.
        chat_type (str): 'group' or 'private'.
        chat_id (int): the chat; None for the default one.

    Returns:
        str: the reply.
    """
    upd = make_update(chat_type=chat_type, **({"chat_id": chat_id} if chat_id else {}))
    asyncio.run(command(upd, make_context(*args, member_status=member_status)))
    return upd.message.reply_text.call_args[0][0]


def test_a_chat_speaks_italian_until_somebody_chooses_another_language():
    assert run(cmd_settings.language_command) == ("🌐 La lingua di questa chat è italiano. "
                                            "Per cambiarla: /lingua it oppure /lingua en.")


def test_an_admin_changes_the_language_and_the_next_replies_follow_it(chat_id):
    assert run(cmd_settings.language_command, "EN", member_status="administrator") == "From now on I speak English 🇬🇧"
    assert database.get_language(chat_id) == "en"
    assert run(cmd_settings.language_command).startswith("🌐 The language of this chat is English.")
    assert run(cmd_settings.language_command, "it", member_status="creator") == "Da ora parlo italiano 🇮🇹"


def test_a_member_cannot_change_the_language_of_a_group(chat_id):
    assert run(cmd_settings.language_command, "en") == "🔒 Solo gli admin del gruppo possono cambiare la lingua."
    assert database.get_language(chat_id) is None


def test_anybody_changes_the_language_of_a_private_chat():
    assert run(cmd_settings.language_command, "en", chat_type="private") == "From now on I speak English 🇬🇧"


def test_the_language_belongs_to_one_chat():
    run(cmd_settings.language_command, "en", member_status="administrator")
    assert run(cmd_settings.language_command, chat_id=-2002).startswith("🌐 La lingua di questa chat è italiano.")


@pytest.mark.parametrize("args", [(), ("de",), ("en", "it")])
def test_without_a_known_language_the_reply_shows_the_current_one(args):
    assert run(cmd_settings.language_command, *args, member_status="administrator").startswith("🌐 La lingua di questa chat")


def test_every_command_answers_to_its_english_and_italian_names_only():
    from caccometro import bot
    registered = {frozenset(h.commands): h.callback for h in bot.application.handlers[0] if hasattr(h, "commands")}
    for english, italian, handler in bot.COMMANDS:
        assert registered[frozenset({english, italian})] is handler, english


def test_the_midnight_announcement_follows_the_language_of_each_chat(seed, chat_id):
    seed({"mario": {"2026-10-05": 3}})
    database.set_language(chat_id, "en")
    assert "October 2026 is over!" in announce._announcement(chat_id, date(2026, 11, 1))
    assert announce._announcement(-2002, date(2026, 11, 1)) is None   # another chat: nobody to celebrate, and Italian
    assert i18n.current() == "it"


def test_an_unknown_stored_language_falls_back_to_italian():
    i18n.use("xx")
    assert i18n.current() == "it"


# ---------------------------------------------------------------- the dictionaries

def translated_sentences():
    """Every literal sentence passed to tr() in the bot code.

    Returns:
        set: the sentences.
    """
    found = set()
    for source in (ROOT / "caccometro").glob("*.py"):
        for node in ast.walk(ast.parse(source.read_text(encoding="utf-8"))):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "tr"
                    and node.args and isinstance(node.args[0], ast.Constant)):
                found.add(node.args[0].value)
    return found


def fields(text):
    """The names of the {fields} of a sentence.

    Args:
        text (str): the sentence.

    Returns:
        list: the names, sorted.
    """
    return sorted(name for _, name, _, _ in string.Formatter().parse(text) if name is not None)


@pytest.mark.parametrize("language", [code for code in i18n.LANGUAGES if code != i18n.DEFAULT_LANGUAGE])
def test_every_sentence_has_a_translation_with_the_same_placeholders(language):
    dictionary = i18n.TRANSLATIONS[language]
    sentences = translated_sentences()
    assert sentences, "no tr() call was found"
    assert sorted(sentences - dictionary.keys()) == [], "sentences without a translation"
    assert sorted(dictionary.keys() - sentences) == [], "translations of sentences the code no longer uses"
    for italian, translated in dictionary.items():
        assert fields(italian) == fields(translated), italian
