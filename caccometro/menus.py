"""Command names and menu descriptions in Italian and English; the menu of a chat follows its language (#152)."""
import logging

from telegram import BotCommandScopeChat, BotCommandScopeChatAdministrators
from telegram.error import TelegramError

logger = logging.getLogger(__name__)

# English name, Italian name, English description, Italian description, in menu order
MENU = [
    ('start', 'start', "Start the bot and explain how to count 💩.",
     "Avvia il bot e spiega come contare le 💩."),
    ('leaderboard_month', 'classifica_mese', "Leaderboard of the month, current or [MM-YYYY, also march 2026].",
     "Classifica del mese, corrente o [MM-YYYY, anche marzo 2026]."),
    ('leaderboard_year', 'classifica_anno', "Leaderboard of the year, current or [YYYY or YY].",
     "Classifica dell'anno, corrente o [YYYY o YY]."),
    ('stats_month', 'statistiche_mese', "Mean, median and variance of the month, current or [MM-YYYY, also march 2026].",
     "Media, mediana e varianza del mese, corrente o [MM-YYYY, anche marzo 2026]."),
    ('stats_year', 'statistiche_anno', "Mean, median and variance of the year, current or [YYYY or YY].",
     "Media, mediana e varianza dell'anno, corrente o [YYYY o YY]."),
    ('records', 'record', "Group records; with me or @username those of one person.",
     "Record del gruppo; con io o @username quelli di una persona."),
    ('trophies', 'trofei', "Group trophies; with me or @username those of one person.",
     "Trofei del gruppo; con io o @username quelli di una persona."),
    ('day_count', 'conto_giorno', "💩 of a day: [@username] [DD-MM-YYYY, today, yesterday].",
     "💩 di un giorno: [@username] [DD-MM-YYYY, oggi, ieri]."),
    ('last_poop', 'ultima_cacca', "Days since the last 💩: [@username].",
     "Giorni dall'ultima 💩: [@username]."),
    ('add_poop', 'aggiungi_cacca', "Add 1 💩 on a day: [@username] DD-MM-YYYY, today or yesterday (others: admins only).",
     "Aggiunge 1 💩 in un giorno: [@username] DD-MM-YYYY, oggi o ieri (altri: solo admin)."),
    ('remove_poop', 'togli_cacca', "Remove 1 💩 on a day: [@username] DD-MM-YYYY, today or yesterday (others: admins only).",
     "Toglie 1 💩 in un giorno: [@username] DD-MM-YYYY, oggi o ieri (altri: solo admin)."),
    ('language', 'lingua', "Language of the bot in this chat: it or en (in groups admins only).",
     "Lingua del bot in questa chat: it o en (nei gruppi solo admin)."),
    ('link_history', 'collega_storico', "Link the history of the old usernames to the users (admins only).",
     "Collega lo storico dei vecchi username agli utenti (solo admin)."),
]
ADMIN_ONLY = {'link_history'}   # only in the administrators' menus


def menu(language, admins=False):
    """(command, description) pairs of the menu in 'en' or 'it'; the admins' menu adds the admin-only commands."""
    english = language == 'en'
    return [(en if english else it, en_text if english else it_text)
            for en, it, en_text, it_text in MENU if admins or en not in ADMIN_ONLY]


async def set_chat_menu(bot, chat_id, language, group):
    """Show the menu of one chat in `language`, whatever the app language of who opens it.

    Without a language_code the chat scope wins over the global menus of every language. A group needs the admins'
    menu too: for them the chat scope comes before all_chat_administrators, so they would lose /link_history.
    A failure leaves the global menus: it is logged, and sending /language again repairs it.
    """
    try:
        await bot.set_my_commands(menu(language), scope=BotCommandScopeChat(chat_id))
        if group:
            await bot.set_my_commands(menu(language, admins=True), scope=BotCommandScopeChatAdministrators(chat_id))
    except TelegramError as e:
        logger.warning(f"Could not set the menu of chat {chat_id} in {language}: {e}")
