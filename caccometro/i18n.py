"""Translations of the bot messages: the Italian sentences are the keys, one dictionary per other language.

Every handler sets the language of its chat first (chat.register_sender); tr() then translates in that language.
A sentence missing from a dictionary stays in Italian. tests/test_i18n.py checks that every sentence is translated.
"""
from contextvars import ContextVar

from caccometro.config import MONTH_NAMES

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


# Month names of the other languages, by number like config.MONTH_NAMES; their first 3 letters are the abbreviations
MONTHS = {'en': ['', 'January', 'February', 'March', 'April', 'May', 'June',
                 'July', 'August', 'September', 'October', 'November', 'December']}


def month_name(number):
    """Name of month `number` (1-12) in the language in use."""
    return MONTHS.get(_language.get(), MONTH_NAMES)[number]


EN = {
    # /lingua
    "La lingua di questa chat è {name}. Per cambiarla: /lingua it oppure /lingua en.":
        "The language of this chat is {name}. To change it: /language en or /language it.",
    "Solo gli admin del gruppo possono cambiare la lingua.": "Only the group admins can change the language.",
    "Da ora parlo italiano 🇮🇹": "From now on I speak English 🇬🇧",

    # /start and plain messages
    "Ciao, sono 🤖 *Caccometro* 🤖.\nManda 💩 quando hai fatto il tuo dovere.\n_Versione {version}_\n\n🇬🇧 English: /language en":
        "Hi, I am 🤖 *Caccometro* 🤖.\nSend 💩 when you have done your duty.\n_Version {version}_\n\n🇮🇹 Italiano: /lingua it",
    "Complimenti {name}, oggi hai fatto 💩 {count} volta!": "Well done {name}, today you did 💩 {count} time!",
    "Complimenti {name}, oggi hai fatto 💩 {count} volte!": "Well done {name}, today you did 💩 {count} times!",
    "Cosa vuoi dirmi?": "What do you want to tell me?",
    "{name} cazzo scrivi *Run*, funziono solo con i comandi specifici e non quelli che ti inventi tu.":
        "{name} what the hell are you writing *Run* for? I only work with my own commands, not with the ones you make up.",

    # arguments
    "Formato non valido. Usa: {usage}": "Invalid format. Use: {usage}",
    "Errore: {error}": "Error: {error}",
    "Data non valida. Esempi: 05-03-2026, 5/3/26, 5.3 (anno corrente), oggi, ieri.":
        "Invalid date. Examples: 05-03-2026, 5/3/26, 5.3 (current year), today, yesterday.",
    "La data selezionata è nel futuro.": "The selected date is in the future.",
    "L'anno deve essere dal {year} in poi.": "The year must be {year} or later.",
    "Formato data non valido. Usa MM-YYYY (anche 3/2026, 03.26 o marzo 2026).":
        "Invalid date format. Use MM-YYYY (also 3/2026, 03.26 or march 2026).",
    "Formato anno non valido. Usa YYYY (anche 26).": "Invalid year format. Use YYYY (also 26).",
    "Non conosco @{username}: deve scrivere almeno un messaggio nel gruppo (oppure rispondi a un suo messaggio).":
        "I do not know @{username}: they must write at least one message in the group (or reply to one of their messages).",
    "/record [@username | io]": "/records [@username | me]",
    "/trofei [@username | io]": "/trophies [@username | me]",
    "/aggiungi @username DD-MM-YYYY": "/add_poop @username DD-MM-YYYY",
    "/togli @username DD-MM-YYYY": "/remove_poop @username DD-MM-YYYY",
    "/conto_giorno @username DD-MM-YYYY": "/day_count @username DD-MM-YYYY",
    "/costipazione @username": "/constipation @username",
    "/collega <username storico> (in risposta a un messaggio della persona)":
        "/link_history <old username> (as a reply to a message of the person)",
    "Nessun dato disponibile.": "No data available.",
    "Nessun dato disponibile per {name}.": "No data available for {name}.",
    "ℹ️ Ci sono dati storici ancora da collegare: usa /collega.": "ℹ️ There is old history still to link: use /link_history.",

    # rankings and statistics
    "Nel mese {date} non sono state contate 💩.": "No 💩 was counted in the month {date}.",
    "Nell'anno {date} non sono state contate 💩.": "No 💩 was counted in the year {date}.",
    "🏆 *Classifica del mese {date}*": "🏆 *Ranking of the month {date}*",
    "🏆 *Classifica dell'anno {date}*": "🏆 *Ranking of the year {date}*",
    "_💩 finora → previsione a fine mese_": "_💩 so far → forecast at the end of the month_",
    "_💩 finora → previsione a fine anno_": "_💩 so far → forecast at the end of the year_",
    "Nessuna statistica disponibile per il mese {date}.": "No statistics available for the month {date}.",
    "Nessuna statistica disponibile per l'anno {date}.": "No statistics available for the year {date}.",
    "📊 *Statistiche del mese {date}*": "📊 *Statistics of the month {date}*",
    "📊 *Statistiche dell'anno {date}*": "📊 *Statistics of the year {date}*",
    "💩 al giorno: media · mediana · varianza": "💩 per day: mean · median · variance",

    # /aggiungi, /togli, /conto_giorno, /costipazione
    "Solo gli admin del gruppo possono modificare i conteggi degli altri.":
        "Only the group admins can change the counts of somebody else.",
    "Il conteggio di {name} nel giorno {date} non può essere aggiornato poiché era già 0 💩.":
        "The count of {name} on {date} cannot be changed: it was already 0 💩.",
    "Il conteggio di {name} nel giorno {date} è stato aggiornato a {count} 💩.":
        "The count of {name} on {date} is now {count} 💩.",
    "il giorno {date}": "on {date}",
    "oggi": "today",
    "{name} {day} hai fatto 💩 {count} volta.": "{name}, {day} you did 💩 {count} time.",
    "{name} {day} hai fatto 💩 {count} volte.": "{name}, {day} you did 💩 {count} times.",
    "{name} {day} non hai fatto 💩.": "{name}, {day} you did no 💩.",
    "{name} oggi hai fatto 💩.": "{name}, today you did 💩.",
    "{name} non fai 💩 da {days} giorno.": "{name}, no 💩 for {days} day.",
    "{name} non fai 💩 da {days} giorni.": "{name}, no 💩 for {days} days.",
    "{name} non ci sono dati sulla costipazione.": "{name}, there is no data about constipation.",

    # /collega
    "Non ci sono dati storici da collegare.": "There is no old history to link.",
    "Dati storici ancora da collegare:": "Old history still to link:",
    " → {name} (corrispondenza trovata)": " → {name} (match found)",
    "({orphans} registrazioni senza username non si possono collegare.)":
        "({orphans} records without a username cannot be linked.)",
    "Gli admin possono usare /collega auto per collegare le corrispondenze, oppure rispondere a un messaggio della persona con /collega <username storico>.":
        "The admins can use /link_history auto to link the matches, or reply to a message of the person with /link_history <old username>.",
    "Solo gli admin del gruppo possono collegare i dati storici.": "Only the group admins can link the old history.",
    "Collegati:": "Linked:",
    "• {username} → {name} ({days} giorni)": "• {username} → {name} ({days} days)",
    "Nessuna corrispondenza trovata tra lo storico e gli utenti che hanno già scritto nel gruppo.":
        "No match found between the old history and the users who have already written in the group.",
    "Da collegare a mano (rispondi a un messaggio della persona con /collega <username storico>):":
        "To link by hand (reply to a message of the person with /link_history <old username>):",
    "Rispondi a un messaggio della persona da collegare. Usa: {usage}": "Reply to a message of the person to link. Use: {usage}",
    "Nessun dato storico trovato per «{username}» (già collegato o inesistente).":
        "No old history found for «{username}» (already linked or never recorded).",
    "Collegati {days} giorni di dati storici di «{username}» a {name}.":
        "Linked {days} days of old history of «{username}» to {name}.",

    # words used inside other sentences
    "volta": "time",
    "volte": "times",
    "giorno": "day",
    "giorni": "days",
    "{n} giorno consecutivo": "{n} day in a row",
    "{n} giorni consecutivi": "{n} days in a row",
    " e altri {extra}": " and {extra} more",
    " e ": " and ",
    "nel mese": "in the month",
    "nei mesi": "in the months",

    # /record of one person
    "Record per {name}": "Records of {name}",
    " 🔥 è il tuo record!": " 🔥 it is your record!",
    " 🔥 già oltre il tuo record mensile!": " 🔥 already beyond your monthly record!",
    " 🔥 record mensile eguagliato!": " 🔥 monthly record equalled!",
    " 🔥 già oltre il record!": " 🔥 already beyond the record!",
    " (fino a ieri)": " (until yesterday)",
    "🥵 Hai fatto 💩 {value} {times} in {count} giorni diversi (gli ultimi: {days}).":
        "🥵 You did 💩 {value} {times} on {count} different days (the latest: {days}).",
    "🥵 Hai fatto 💩 {value} {times} il {days}.": "🥵 You did 💩 {value} {times} on {days}.",
    "   ↳ Oggi: {count} 💩": "   ↳ Today: {count} 💩",
    "🤩 Hai fatto 💩 {value} {times} {label} {months}.": "🤩 You did 💩 {value} {times} {label} {months}.",
    "😭 Hai fatto solo 💩 {value} {times} {label} {months}.": "😭 You only did 💩 {value} {times} {label} {months}.",
    "🗓️ Il record mensile sarà disponibile dopo il primo mese completo.":
        "🗓️ The monthly record will be available after the first complete month.",
    "🗓️ Il mese peggiore sarà disponibile dopo almeno due mesi di dati.":
        "🗓️ The worst month will be available after at least two months of data.",
    "   ↳ Questo mese: {count} 💩 finora": "   ↳ This month: {count} 💩 so far",
    "🥳 Hai fatto 💩 per {days} ({when}).": "🥳 You did 💩 for {days} ({when}).",
    "   ↳ In corso: {count} {days} di fila": "   ↳ Now: {count} {days} in a row",
    "   ↳ In corso: nessuna serie": "   ↳ Now: no streak",
    "🫣 Hai fatto 💩 {value} {times} in una serie di giorni consecutivi ({when}).":
        "🫣 You did 💩 {value} {times} in one streak of consecutive days ({when}).",
    "   ↳ In corso: {count} 💩 nella serie": "   ↳ Now: {count} 💩 in the streak",
    "🤢 Non hai fatto 💩 per {days} ({when}).": "🤢 You did no 💩 for {days} ({when}).",
    "🤢 Non ci sono ancora giorni senza 💩 tra la prima e l'ultima registrazione.":
        "🤢 There are no days without 💩 yet between the first and the last record.",
    "   ↳ In corso: oggi hai fatto 💩, nessuna pausa": "   ↳ Now: you did 💩 today, no pause",
    "   ↳ In corso: {count} {days} senza 💩": "   ↳ Now: {count} {days} without 💩",

    # /record of the group
    "🏆 *Record del gruppo* 🏆": "🏆 *Group records* 🏆",
    "🥵 Più 💩 in un giorno: {value} — {holders}": "🥵 Most 💩 in a day: {value} — {holders}",
    "🤩 Più 💩 in un mese: {value} — {holders}": "🤩 Most 💩 in a month: {value} — {holders}",
    "😭 Meno 💩 in un mese: {value} — {holders}": "😭 Fewest 💩 in a month: {value} — {holders}",
    "🥳 Serie più lunga: {value} — {holders}": "🥳 Longest streak: {value} — {holders}",
    "🫣 Più 💩 in una serie: {value} — {holders}": "🫣 Most 💩 in a streak: {value} — {holders}",
    "🤢 Pausa più lunga: {value} — {holders}": "🤢 Longest pause: {value} — {holders}",
    "📍 *Adesso*": "📍 *Now*",
    "💩 Oggi: {value} — {holders}": "💩 Today: {value} — {holders}",
    "🔥 Serie in corso più lunga: {value} — {holders}": "🔥 Longest streak in progress: {value} — {holders}",
    "🐢 Pausa in corso più lunga: {value} — {holders}": "🐢 Longest pause in progress: {value} — {holders}",
    "Il tuo: /record io — di un altro: /record @username (o rispondi a un suo messaggio)":
        "Yours: /records me — somebody else's: /records @username (or reply to one of their messages)",

    # /trofei
    "🔥 *Nuovo trofeo!* {days} giorni di fila con almeno una 💩!": "🔥 *New trophy!* {days} days in a row with at least one 💩!",
    "🏆 *Bacheca dei trofei* 🏆": "🏆 *Trophy board* 🏆",
    "Ancora nessun trofeo: servono {days} giorni di fila con almeno una 💩, oppure vincere un mese.":
        "No trophy yet: it takes {days} days in a row with at least one 💩, or winning a month.",
    "👑 💩 dell'anno · 🏅 💩 del mese · 🔥 {days} giorni di fila":
        "👑 💩 of the year · 🏅 💩 of the month · 🔥 {days} days in a row",
    "I tuoi: /trofei io — di un altro: /trofei @username (o rispondi a un suo messaggio)":
        "Yours: /trophies me — somebody else's: /trophies @username (or reply to one of their messages)",
    "Trofei di {name}": "Trophies of {name}",
    "Ancora nessun trofeo.": "No trophy yet.",
    "👑 💩 dell'anno: {years}": "👑 💩 of the year: {years}",
    "🏅 💩 del mese ({count}): {months}": "🏅 💩 of the month ({count}): {months}",
    "🔥 Serie: {n} trofeo": "🔥 Streaks: {n} trophy",
    "🔥 Serie: {n} trofei": "🔥 Streaks: {n} trophies",
    "   ↳ {days} giorni: {period}": "   ↳ {days} days: {period}",
    "   ↳ e altre {extra} serie": "   ↳ and {extra} more streaks",
    "📍 Serie in corso: {count} {days} di fila, ne manca 1 al prossimo trofeo":
        "📍 Streak in progress: {count} {days} in a row, 1 more to the next trophy",
    "📍 Serie in corso: {count} {days} di fila, ne mancano {missing} al prossimo trofeo":
        "📍 Streak in progress: {count} {days} in a row, {missing} more to the next trophy",
    "📍 Nessuna serie in corso: oggi è il giorno buono per iniziarne una!":
        "📍 No streak in progress: today is the right day to start one!",

    # midnight announcement
    " a testa": " each",
    "{label}: {names} con {total} 💩": "{label}: {names} with {total} 💩",
    "🎆 *Buon anno! Benvenuto {year}!* 🥂": "🎆 *Happy new year! Welcome {year}!* 🥂",
    "🏅 💩 di dicembre": "🏅 💩 of December",
    "👑 💩 dell'anno {year}": "👑 💩 of the year {year}",
    "Complimenti! Che il {year} sia regolare come un orologio svizzero 🎉":
        "Well done! May {year} be as regular as a Swiss watch 🎉",
    "🌙 *Mezzanotte: {month} è finito!*": "🌙 *Midnight: {month} is over!*",
    "🏅 💩 del mese": "🏅 💩 of the month",
    "Complimenti! Si riparte da zero: buon {month} e buone 💩 🧻":
        "Well done! Back to zero: happy {month} and happy 💩 🧻",

    # charts
    "Classifica di {title}": "Ranking of {title}",
    "Classifica del {title}": "Ranking of {title}",
    "Totale": "Total",
    "Giorno": "Day",
    "Totale progressivo": "Running total",
    "Come è andata giorno per giorno": "How it went day by day",
    "Statistiche di {title}": "Statistics of {title}",
    "Statistiche del {title}": "Statistics of {title}",
    "Volte al giorno": "Times per day",
    "Giorni": "Days",
    "Distribuzione giornaliera  (◆ media, — mediana)": "Daily distribution  (◆ mean, — median)",
}

TRANSLATIONS = {'en': EN}
