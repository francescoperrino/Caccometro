"""Translations of the bot messages: the Italian sentences are the keys, one dictionary per other language.

Every handler sets the language of its chat first (chat.register_sender); tr() then translates in that language.
A sentence missing from a dictionary stays in Italian. tests/test_i18n.py checks that every sentence is translated.
"""
from contextvars import ContextVar

LANGUAGES = {'it': 'italiano', 'en': 'English'}   # code -> name shown by /lingua
DEFAULT_LANGUAGE = 'it'

# One value per update: each update is handled in its own asyncio task, which has its own copy of the context
_language = ContextVar('language', default=DEFAULT_LANGUAGE)


def use(language):
    """Answer in `language` from now on, in the current update (or in the current chat of the announcement)."""
    _language.set(language if language in LANGUAGES else DEFAULT_LANGUAGE)


def current():
    """The language in use."""
    return _language.get()


def tr(text):
    """`text` (an Italian sentence) in the language in use; the Italian text when there is no translation."""
    return TRANSLATIONS.get(_language.get(), {}).get(text, text)


EN = {
    # /lingua
    "La lingua di questa chat è {name}. Per cambiarla: /lingua it oppure /lingua en.":
        "The language of this chat is {name}. To change it: /language en or /language it.",
    "Solo gli admin del gruppo possono cambiare la lingua.": "Only the group admins can change the language.",
    "Da ora parlo italiano 🇮🇹": "From now on I speak English 🇬🇧",
}

TRANSLATIONS = {'en': EN}
