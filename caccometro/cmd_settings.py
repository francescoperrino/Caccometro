"""/start, /app, /language and /link_history: the bot, its Mini App and the settings of the chat."""
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from caccometro import __version__, i18n, miniapp
from caccometro.arguments import invalid_format, replied_person
from caccometro.chat import is_chat_admin, register_sender, register_user, where
from caccometro.database import (count_legacy_orphans, find_user_by_username, init_database, link_legacy_by_username,
                                 link_legacy_username, list_legacy_users, set_language)
from caccometro.i18n import tr
from caccometro.menus import set_chat_menu

logger = logging.getLogger(__name__)


# Command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command."""
    sender = register_sender(update)
    if sender is None:
        return
    init_database(update.message.chat_id)
    await update.message.reply_text(tr("Ciao, sono 🤖 *Caccometro* 🤖.\n"
                                       "Manda 💩 quando hai fatto il tuo dovere.\n"
                                       "Entro 15 minuti manda una posizione per conquistare la sua zona 🚩.\n"
                                       "/classifica\\_mese, /record e /app per classifiche, record e mappa.\n"
                                       "_Versione {version}_\n\n"
                                       "🇬🇧 English: /language en").format(version=__version__), parse_mode='Markdown')


async def app_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /app command: a button that opens the Mini App on this chat.

    A plain URL button with the direct link: groups refuse web_app buttons.
    """
    sender = register_sender(update)
    if sender is None:
        return
    link = miniapp.direct_link(context.bot.username, update.message.chat_id)
    await update.message.reply_text(tr("📱 Classifiche, statistiche e mappa delle conquiste nella Mini App."),
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tr("Apri"), url=link)]]))


async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /language command: show the language of the chat or, for the admins, change it (/language en)."""
    sender = register_sender(update)
    if sender is None:
        return
    language = context.args[0].lower() if len(context.args) == 1 else None
    if language not in i18n.LANGUAGES:
        await update.message.reply_text(tr("🌐 La lingua di questa chat è {name}. Per cambiarla: /lingua it oppure /lingua en.")
                                        .format(name=i18n.LANGUAGES[i18n.current()]))
        return
    if not await is_chat_admin(update, context):
        await update.message.reply_text(tr("🔒 Solo gli admin del gruppo possono cambiare la lingua."))
        return
    set_language(update.message.chat_id, language)
    i18n.use(language)
    logger.info(f"Language changed by {sender.mention} in {where(update)}: {language}")
    await update.message.reply_text(tr("Da ora parlo italiano 🇮🇹"))
    await set_chat_menu(context.bot, update.message.chat_id, language, update.message.chat.type != 'private')


async def link_history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /link_history command: link the old username-based history to Telegram users.

    /link_history               list the history that is still to be linked (everybody)
    /link_history auto          link every old username that matches a known user (admins)
    /link_history <old username>as a reply to a message of the person: link that history to them (admins)
    """
    sender = register_sender(update)
    if sender is None:
        return
    chat_id = update.message.chat_id
    args = context.args

    if not args:
        legacy = list_legacy_users(chat_id)
        if not legacy:
            await update.message.reply_text(tr("🤷 Non ci sono dati storici da collegare."))
            return
        lines = [tr("Dati storici ancora da collegare:")]
        for legacy_username, total in legacy:
            match = find_user_by_username(chat_id, legacy_username)
            lines.append(f"• {legacy_username}: {total} 💩"
                         + (tr(" → {name} (corrispondenza trovata)").format(name=match.mention) if match else ""))
        orphans = count_legacy_orphans(chat_id)
        if orphans:
            lines.append(tr("({orphans} registrazioni senza username non si possono collegare.)").format(orphans=orphans))
        lines.append("\n" + tr("Gli admin possono usare /collega_storico auto per collegare le corrispondenze, "
                               "oppure rispondere a un messaggio della persona con /collega_storico <username storico>."))
        await update.message.reply_text("\n".join(lines))
        return

    if not await is_chat_admin(update, context):
        await update.message.reply_text(tr("🔒 Solo gli admin del gruppo possono collegare i dati storici."))
        return

    # 'auto' is the keyword; an old username that is literally 'auto' can be written as '@auto'
    if len(args) == 1 and args[0] == 'auto':
        linked = link_legacy_by_username(chat_id)
        for legacy_username, user, days in linked:
            logger.info(f"History linked by {sender.mention} in {where(update)}: "
                        f"{legacy_username} -> {user.mention}, {days} days")
        remaining = list_legacy_users(chat_id)
        lines = []
        if linked:
            lines.append(tr("🔗 Collegati:"))
            lines += [tr("• {username} → {name} ({days} giorni)").format(username=legacy_username, name=user.mention, days=days)
                      for legacy_username, user, days in linked]
        else:
            lines.append(tr("🤷 Nessuna corrispondenza trovata tra lo storico e gli utenti che hanno già scritto nel gruppo."))
        if remaining:
            lines.append("\n" + tr("Da collegare a mano (rispondi a un messaggio della persona con /collega_storico <username storico>):"))
            lines += [f"• {legacy_username}: {total} 💩" for legacy_username, total in remaining]
        await update.message.reply_text("\n".join(lines))
        return

    usage = tr("/collega_storico <username storico> (in risposta a un messaggio della persona)")
    if len(args) != 1:
        await update.message.reply_text(invalid_format(usage))
        return
    replied = replied_person(update)
    if replied is None:
        await update.message.reply_text(tr("⚠️ Rispondi a un messaggio della persona da collegare. Usa: {usage}").format(usage=usage))
        return
    legacy_username = args[0].lstrip('@')
    target = register_user(chat_id, replied)
    days = link_legacy_username(chat_id, legacy_username, target.user_id)
    logger.info(f"History linked by {sender.mention} in {where(update)}: {legacy_username} -> {target.mention}, {days} days")
    if days == 0:
        await update.message.reply_text(tr("🤷 Nessun dato storico trovato per «{username}» (già collegato o inesistente).")
                                        .format(username=legacy_username))
    else:
        await update.message.reply_text(tr("🔗 Collegati {days} giorni di dati storici di «{username}» a {name}.")
                                        .format(days=days, username=legacy_username, name=target.mention))
