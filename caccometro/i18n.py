"""Translations of the bot messages: the Italian sentences are the keys, one dictionary per other language.

Every handler sets the language of its chat first (chat.register_sender); tr() then translates in that language.
A sentence missing from a dictionary stays in Italian. tests/test_i18n.py checks that every sentence is translated.
"""
from contextvars import ContextVar

from caccometro.config import MONTH_NAMES

LANGUAGES = {'it': 'italiano', 'en': 'English'}   # code -> name shown by /language
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
    # /language
    "🌐 La lingua di questa chat è {name}. Per cambiarla: /lingua it oppure /lingua en.":
        "🌐 The language of this chat is {name}. To change it: /language en or /language it.",
    "🔒 Solo gli admin del gruppo possono cambiare la lingua.": "🔒 Only the group admins can change the language.",
    "Da ora parlo italiano 🇮🇹": "From now on I speak English 🇬🇧",
    "📱 Classifiche, statistiche e mappa delle conquiste nella Mini App.": "📱 Leaderboards, statistics and conquest map in the Mini App.",
    "Apri": "Open",

    # /start
    "Ciao, sono 🤖 *Caccometro* 🤖.\nManda 💩 quando hai fatto il tuo dovere.\n"
    "Entro 15 minuti manda una posizione per conquistare la sua zona 🚩.\n"
    "/classifica\\_mese, /record e /app per classifiche, record e mappa.\n"
    "_Versione {version}_\n\n🇬🇧 English: /language en":
        "Hi, I am 🤖 *Caccometro* 🤖.\nSend 💩 when you have done your duty.\n"
        "Within 15 minutes send a location to conquer its tile 🚩.\n"
        "/leaderboard\\_month, /records and /app for leaderboards, records and the map.\n"
        "_Version {version}_\n\n🇮🇹 Italiano: /lingua it",
    # Messages with 💩 or 🚽
    "💩 oggi: {count}": "💩 today: {count}",
    "{name} a quest'ora? La notte porta consiglio, e anche 💩.":
        "{name} at this hour? Night brings wisdom, and 💩 too.",
    "Insonnia intestinale per {name}: il turno di notte non perdona.":
        "Gut insomnia for {name}: the night shift forgives nothing.",
    "{name} fa 💩 mentre il mondo dorme. Eroe silenzioso.":
        "{name} does 💩 while the world sleeps. Silent hero.",
    "Luci spente, scarico acceso: bravo {name}.":
        "Lights off, flush on: well done {name}.",
    "{name} apre la giornata con una 💩: colazione dei campioni.":
        "{name} starts the day with a 💩: breakfast of champions.",
    "Il caffè ha fatto effetto, {name}!":
        "The coffee kicked in, {name}!",
    "Sveglia, caffè, 💩: la routine di {name} non tradisce.":
        "Alarm, coffee, 💩: {name}'s routine never fails.",
    "Buongiorno {name}, e buon alleggerimento!":
        "Good morning {name}, and happy unloading!",
    "{name} fa 💩 invece di lavorare: la scusa perfetta.":
        "{name} does 💩 instead of working: the perfect excuse.",
    "Pausa strategica in bagno per {name}, telefono incluso.":
        "Strategic bathroom break for {name}, phone included.",
    "Mattinata produttiva per {name}: almeno qualcosa è uscito.":
        "Productive morning for {name}: at least something got delivered.",
    "{name} porta a termine un compito importante.":
        "{name} completes an important task.",
    "Il pranzo è appena finito e {name} è già operativo.":
        "Lunch is barely over and {name} is already operational.",
    "{name} smaltisce il pranzo in tempo record.":
        "{name} clears lunch in record time.",
    "Digestione lampo per {name}!":
        "Lightning digestion for {name}!",
    "Dopo pranzo il dovere chiama, e {name} risponde.":
        "After lunch duty calls, and {name} answers.",
    "Pomeriggio di gloria per {name}.":
        "Afternoon of glory for {name}.",
    "{name} approfitta della pausa pomeridiana: saggio.":
        "{name} takes the afternoon break: wise.",
    "Merenda smaltita? {name} sì.":
        "Snack cleared? {name} certainly.",
    "{name} sopravvive al calo di metà pomeriggio con una 💩.":
        "{name} survives the mid-afternoon slump with a 💩.",
    "{name} chiude la giornata in bellezza.":
        "{name} closes the day in style.",
    "Dopo cena si smaltisce: ci pensa {name}.":
        "After dinner comes the cleanup: {name} is on it.",
    "Serata di relax per {name}, trono incluso.":
        "Relaxing evening for {name}, throne included.",
    "{name} va a letto più leggero.":
        "{name} goes to bed lighter.",
    "Complimenti {name}!":
        "Well done {name}!",
    "{name} ha fatto il suo dovere.":
        "{name} did their duty.",
    "Un applauso per {name}, che non si tira indietro.":
        "A round of applause for {name}, who never backs down.",
    "Missione compiuta per {name}.":
        "Mission accomplished for {name}.",
    "{name} lascia il segno.":
        "{name} leaves a mark.",
    "Che soddisfazione, {name}!":
        "What a relief, {name}!",
    "La classifica ringrazia {name}.":
        "The leaderboard thanks {name}.",
    "{name} scrive un'altra pagina di storia.":
        "{name} writes another page of history.",
    "Prima 💩 della giornata per {name}: si parte bene.":
        "First 💩 of the day for {name}: a good start.",
    "{name} inaugura la giornata.":
        "{name} opens the day.",
    "Ecco la prima di oggi, {name}!":
        "Here is the first of today, {name}!",
    "{name} è mattiniero: la prima 💩 arriva presto.":
        "{name} is an early bird: the first 💩 comes early.",
    "Prima 💩 della giornata dopo pranzo? {name} ci ha messo un po'.":
        "First 💩 of the day after lunch? {name} took a while.",
    "{name} inizia la giornata a notte fonda.":
        "{name} starts the day in the dead of night.",
    "Di nuovo {name}?! Che cosa ha mangiato?":
        "{name} again?! What did they eat?",
    "{name} non si ferma più.":
        "{name} cannot be stopped.",
    "{name} fa le cose in grande oggi.":
        "{name} is going big today.",
    "{name} nelle ore piccole e ancora 💩: serve un medico?":
        "{name} in the small hours and 💩 again: need a doctor?",
    "Il pranzo non è andato giù a {name}: ancora!":
        "Lunch did not sit well with {name}: again!",
    # Mentions of the bot
    "💬 Cosa vuoi dirmi?": "💬 What do you want to tell me?",

    # /conquests
    "Prima la 💩, poi la conquista 😏": "First the 💩, then the conquest 😏",
    "📍 Manda la posizione entro 15 minuti per conquistare la zona!": "📍 Send your location within 15 minutes to conquer the tile!",
    "🚩 {name} conquista una nuova zona! Zone: {total}": "🚩 {name} conquers a new tile! Tiles: {total}",
    "🏠 {name} difende la sua zona. Zone: {total}": "🏠 {name} defends their tile. Tiles: {total}",
    "⚔️ {name} ruba una zona a {owner}! Zone: {total}": "⚔️ {name} steals a tile from {owner}! Tiles: {total}",
    "👑 {name} è il nuovo re della collina!": "👑 {name} is the new king of the hill!",
    "/conquiste [@username | io]": "/conquests [@username | me]",
    "🗺️ {name}: {held} zone tenute, {visited} visitate.": "🗺️ {name}: {held} tiles held, {visited} visited.",
    "👑 Re della collina!": "👑 King of the hill!",
    "Nessuna zona conquistata. Dopo la 💩 manda una posizione entro 15 minuti.":
        "No tile conquered yet. After the 💩 send a location within 15 minutes.",
    "🗺️ *Conquiste*": "🗺️ *Conquests*",
    "Zona conquistata": "Tile conquered",
    "Conquiste nel mondo": "Conquests around the world",
    "Conquiste in Lombardia": "Conquests in Lombardy",
    "Conquiste in Italia": "Conquests in Italy",
    "ultima conquista": "latest conquest",
    "zone perse: {n}": "tiles lost: {n}",
    "Zona di {name}": "Tiles of {name}",
    "Zone del gruppo": "Tiles of the group",
    # Messages with "run"
    "{name} cazzo scrivi *Run*, funziono solo con i comandi specifici e non quelli che ti inventi tu.":
        "{name} what the hell are you writing *Run* for? I only work with my own commands, not with the ones you make up.",
    "{name}, *Run* non è un comando. Funziono solo con quelli veri, non con quelli che ti inventi tu.":
        "{name}, *Run* is not a command. I only work with real ones, not the ones you make up.",
    "{name}, ma sei serio? *Run*?! Guarda il menu dei comandi, poi riprova.":
        "{name}, seriously? *Run*?! Check the command menu, then try again.",

    # Shared: arguments, dates and people
    "⚠️ Formato non valido. Usa: {usage}": "⚠️ Invalid format. Use: {usage}",
    "⚠️ Errore: {error}": "⚠️ Error: {error}",
    "Data non valida. Esempi: 05-03-2026, 5/3/26, 5.3 (anno corrente), oggi, ieri.":
        "Invalid date. Examples: 05-03-2026, 5/3/26, 5.3 (current year), today, yesterday.",
    "La data selezionata è nel futuro.": "The selected date is in the future.",
    "L'anno deve essere dal {year} in poi.": "The year must be {year} or later.",
    "⚠️ Formato data non valido. Usa MM-YYYY (anche 3/2026, 03.26 o marzo 2026).":
        "⚠️ Invalid date format. Use MM-YYYY (also 3/2026, 03.26 or march 2026).",
    "⚠️ Formato anno non valido. Usa YYYY (anche 26).": "⚠️ Invalid year format. Use YYYY (also 26).",
    "🤔 Non conosco @{username}: deve scrivere almeno un messaggio nel gruppo (oppure rispondi a un suo messaggio).":
        "🤔 I do not know @{username}: they must write at least one message in the group (or reply to one of their messages).",
    "/record [@username | io]": "/records [@username | me]",
    "/trofei [@username | io]": "/trophies [@username | me]",
    "/aggiungi_cacca @username DD-MM-YYYY": "/add_poop @username DD-MM-YYYY",
    "/togli_cacca @username DD-MM-YYYY": "/remove_poop @username DD-MM-YYYY",
    "/conto_giorno @username DD-MM-YYYY": "/day_count @username DD-MM-YYYY",
    "/ultima_cacca @username": "/last_poop @username",
    "/collega_storico <username storico> (in risposta a un messaggio della persona)":
        "/link_history <old username> (as a reply to a message of the person)",
    "🤷 Nessun dato disponibile.": "🤷 No data available.",
    "🤷 Nessun dato disponibile per {name}.": "🤷 No data available for {name}.",
    "ℹ️ Ci sono dati storici ancora da collegare: usa /collega_storico.": "ℹ️ There is old history still to link: use /link_history.",

    # /leaderboard_month, /leaderboard_year
    "Nel mese {date} non sono state contate 💩.": "No 💩 was counted in the month {date}.",
    "Nell'anno {date} non sono state contate 💩.": "No 💩 was counted in the year {date}.",
    "🏆 *Classifica del mese {date}*": "🏆 *Leaderboard of the month {date}*",
    "🏆 *Classifica dell'anno {date}*": "🏆 *Leaderboard of the year {date}*",
    "_💩 finora → previsione a fine mese_": "_💩 so far → forecast at the end of the month_",
    "_💩 finora → previsione a fine anno_": "_💩 so far → forecast at the end of the year_",
    # /stats_month, /stats_year
    "🤷 Nessuna statistica disponibile per il mese {date}.": "🤷 No statistics available for the month {date}.",
    "🤷 Nessuna statistica disponibile per l'anno {date}.": "🤷 No statistics available for the year {date}.",
    "📊 *Statistiche del mese {date}*": "📊 *Statistics of the month {date}*",
    "📊 *Statistiche dell'anno {date}*": "📊 *Statistics of the year {date}*",
    "💩 al giorno: media · mediana · varianza": "💩 per day: mean · median · variance",

    # /add_poop
    "🔒 Solo gli admin del gruppo possono modificare i conteggi degli altri.":
        "🔒 Only the group admins can change the counts of somebody else.",
    # /day_count
    "il giorno {date}": "on {date}",
    "oggi": "today",
    # /last_poop
    "Nessun dato sull'ultima 💩 di {name}: si comincia oggi.": "No data on the last 💩 of {name}: it starts today.",
    "{name} oggi ha già fatto 💩: il dovere è compiuto.": "{name} already did 💩 today: duty done.",
    "{name} oggi ha già dato 💩. Riposa.": "{name} already delivered 💩 today. Resting.",
    "{name} ha fatto 💩 ieri: tutto sotto controllo.": "{name} did 💩 yesterday: all under control.",
    "L'ultima 💩 di {name} è di ieri: oggi è il giorno giusto.": "The last 💩 of {name} was yesterday: today is the day.",
    "{name} non fa 💩 da {days} giorni: inizia a farsi sentire.": "{name} has had no 💩 for {days} days: it starts to show.",
    "{name} non fa 💩 da {days} giorni: serve una prugna.": "{name} has had no 💩 for {days} days: a prune is needed.",
    "{name} non fa 💩 da {days} giorni: serve un intervento.": "{name} has had no 💩 for {days} days: time for an intervention.",
    "{name} non fa 💩 da {days} giorni?! Il bagno lo aspetta, ed è preoccupato.": "{name} has had no 💩 for {days} days?! The bathroom is waiting, and worried.",
    # /day_count
    "{name} {day} non ha fatto 💩: giornata di sciopero?": "{name} did no 💩 {day}: on strike?",
    "{name} {day}: zero 💩. Il registro è vuoto.": "{name} {day}: zero 💩. The record is empty.",
    "{name} {day} ha fatto 💩 {count} volta: nella norma.": "{name} {day} did 💩 {count} time: normal.",
    "{name} {day} ha fatto 💩 {count} volte: nella norma.": "{name} {day} did 💩 {count} times: normal.",
    "{name} {day}: {count} 💩, regolare come un orologio.": "{name} {day}: {count} 💩, regular as clockwork.",
    "{name} {day}: {count} 💩. Che cosa ha mangiato?": "{name} {day}: {count} 💩. What did they eat?",
    "{name} {day}: {count} 💩, giornata da record.": "{name} {day}: {count} 💩, record-breaking day.",
    # /add_poop
    "Fatto: {name} il {date} sale a {count} 💩. La storia è riscritta.":
        "Done: {name} goes up to {count} 💩 on {date}. History rewritten.",
    "{name} il {date} ora ha {count} 💩. Meglio tardi che mai.":
        "{name} now has {count} 💩 on {date}. Better late than never.",
    "Registrato: {name} il {date} arriva a {count} 💩.": "Recorded: {name} reaches {count} 💩 on {date}.",
    # /remove_poop
    "⚠️ Il conteggio di {name} nel giorno {date} non può essere aggiornato poiché era già 0 💩.":
        "⚠️ The count of {name} on {date} cannot be changed: it was already 0 💩.",
    "Cancellata: {name} il {date} scende a {count} 💩. Nessuno ha visto niente.":
        "Erased: {name} drops to {count} 💩 on {date}. Nobody saw anything.",
    "{name} il {date} ora ha {count} 💩. Tirato lo sciacquone sul passato.":
        "{name} now has {count} 💩 on {date}. The past has been flushed.",
    "Tolta: {name} il {date} resta con {count} 💩.": "Removed: {name} is left with {count} 💩 on {date}.",

    # /link_history
    "🤷 Non ci sono dati storici da collegare.": "🤷 There is no old history to link.",
    "Dati storici ancora da collegare:": "Old history still to link:",
    " → {name} (corrispondenza trovata)": " → {name} (match found)",
    "({orphans} registrazioni senza username non si possono collegare.)":
        "({orphans} records without a username cannot be linked.)",
    "Gli admin possono usare /collega_storico auto per collegare le corrispondenze, oppure rispondere a un messaggio della persona con /collega_storico <username storico>.":
        "The admins can use /link_history auto to link the matches, or reply to a message of the person with /link_history <old username>.",
    "🔒 Solo gli admin del gruppo possono collegare i dati storici.": "🔒 Only the group admins can link the old history.",
    "🔗 Collegati:": "🔗 Linked:",
    "• {username} → {name} ({days} giorni)": "• {username} → {name} ({days} days)",
    "🤷 Nessuna corrispondenza trovata tra lo storico e gli utenti che hanno già scritto nel gruppo.":
        "🤷 No match found between the old history and the users who have already written in the group.",
    "Da collegare a mano (rispondi a un messaggio della persona con /collega_storico <username storico>):":
        "To link by hand (reply to a message of the person with /link_history <old username>):",
    "⚠️ Rispondi a un messaggio della persona da collegare. Usa: {usage}": "⚠️ Reply to a message of the person to link. Use: {usage}",
    "🤷 Nessun dato storico trovato per «{username}» (già collegato o inesistente).":
        "🤷 No old history found for «{username}» (already linked or never recorded).",
    "🔗 Collegati {days} giorni di dati storici di «{username}» a {name}.":
        "🔗 Linked {days} days of old history of «{username}» to {name}.",

    # Shared: words used inside other sentences
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

    # /records of one person
    "Record per {name}": "Records of {name}",
    " 🔥 è il record!": " 🔥 it is the record!",
    " 🔥 già oltre il record mensile!": " 🔥 already beyond the monthly record!",
    " 🔥 record mensile eguagliato!": " 🔥 monthly record equalled!",
    " 🔥 già oltre il record!": " 🔥 already beyond the record!",
    " (fino a ieri)": " (until yesterday)",
    "🥵 Più 💩 in un giorno: {value} {times} in {count} giorni diversi (gli ultimi: {days}).":
        "🥵 Most 💩 in a day: {value} {times} on {count} different days (the latest: {days}).",
    "🥵 Più 💩 in un giorno: {value} {times} il {days}.": "🥵 Most 💩 in a day: {value} {times} on {days}.",
    "   ↳ Oggi: {count} 💩": "   ↳ Today: {count} 💩",
    "🤩 Mese migliore: {value} 💩 {label} {months}.": "🤩 Best month: {value} 💩 {label} {months}.",
    "😭 Mese peggiore: solo {value} 💩 {label} {months}.": "😭 Worst month: only {value} 💩 {label} {months}.",
    "🗓️ Il record mensile sarà disponibile dopo il primo mese completo.":
        "🗓️ The monthly record will be available after the first complete month.",
    "🗓️ Il mese peggiore sarà disponibile dopo almeno due mesi di dati.":
        "🗓️ The worst month will be available after at least two months of data.",
    "   ↳ Questo mese: {count} 💩 finora": "   ↳ This month: {count} 💩 so far",
    "🥳 Serie più lunga: {days} ({when}).": "🥳 Longest streak: {days} ({when}).",
    "   ↳ In corso: {count} {days} di fila": "   ↳ Now: {count} {days} in a row",
    "   ↳ In corso: nessuna serie": "   ↳ Now: no streak",
    "🫣 Più 💩 in una serie: {value} {times} ({when}).":
        "🫣 Most 💩 in a streak: {value} {times} ({when}).",
    "   ↳ In corso: {count} 💩 nella serie": "   ↳ Now: {count} 💩 in the streak",
    "🤢 Pausa più lunga: {days} ({when}).": "🤢 Longest pause: {days} ({when}).",
    "🤢 Non ci sono ancora giorni senza 💩 tra la prima e l'ultima registrazione.":
        "🤢 There are no days without 💩 yet between the first and the last record.",
    "   ↳ In corso: 💩 fatta oggi, nessuna pausa": "   ↳ Now: 💩 done today, no pause",
    "   ↳ In corso: {count} {days} senza 💩": "   ↳ Now: {count} {days} without 💩",

    # /records of the group
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

    # /trophies
    "🔥 *Nuovo trofeo!* {days} giorni di fila con almeno una 💩!": "🔥 *New trophy!* {days} days in a row with at least one 💩!",
    "🏆 *Bacheca dei trofei* 🏆": "🏆 *Trophy board* 🏆",
    "🤷 Ancora nessun trofeo: servono {days} giorni di fila con almeno una 💩, oppure vincere un mese.":
        "🤷 No trophy yet: it takes {days} days in a row with at least one 💩, or winning a month.",
    "👑 💩 dell'anno · 🏅 💩 del mese · 🔥 {days} giorni di fila":
        "👑 💩 of the year · 🏅 💩 of the month · 🔥 {days} days in a row",
    "I tuoi: /trofei io — di un altro: /trofei @username (o rispondi a un suo messaggio)":
        "Yours: /trophies me — somebody else's: /trophies @username (or reply to one of their messages)",
    "🚩 conquistatore della stagione · ⛰️ re della stagione": "🚩 season conqueror · ⛰️ season king",
    "🚩 Conquistatore della stagione: {seasons}": "🚩 Season conqueror: {seasons}",
    "⛰️ Re della stagione: {seasons}": "⛰️ Season king: {seasons}",
    "🚩 Stagione {season}: conquistatore {conquerors} ({n}), re {king}":
        "🚩 Season {season}: conqueror {conquerors} ({n}), king {king}",
    "Trofei di {name}": "Trophies of {name}",
    "🤷 Ancora nessun trofeo.": "🤷 No trophy yet.",
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

    # Group messages: midnight announcement
    " a testa": " each",
    "🗺️ *Stagione {season} finita!*": "🗺️ *Season {season} is over!*",
    "🚩 Conquistatore: {names} con {n} conquiste": "🚩 Conqueror: {names} with {n} conquests",
    "⛰️ Re della collina: {names}": "⛰️ King of the hill: {names}",
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
    "✨ Il tuo mese": "✨ Your month",
    "✨ Il tuo anno": "✨ Your year",

    # Mini App: image of the recap of a month or a year (#195)
    "RIEPILOGO {period}": "RECAP {period}",
    "{place}° posto su {total}!": "#{place} of {total}!",
    "che mese!": "what a month!",
    "che anno!": "what a year!",
    "su {month}": "vs {month}",
    "sul {year}": "vs {year}",
    "il {day} {month}": "on {month} {day}",
    "giorno di fila": "day streak",
    "giorni di fila": "day streak",
    "✨ Il tuo mese di {month}: inoltralo o salvalo per condividerlo.": "✨ Your {month}: forward it or save it to share it.",
    "✨ Il tuo {year}: inoltralo o salvalo per condividerlo.": "✨ Your {year}: forward it or save it to share it.",

    # Shared: charts
    "Classifica di {title}": "Leaderboard of {title}",
    "Classifica del {title}": "Leaderboard of {title}",
    "Totale": "Total",
    "Giorno": "Day",
    "Totale progressivo": "Running total",
    "Come è andata giorno per giorno": "How it went day by day",
    "Statistiche di {title}": "Statistics of {title}",
    "Statistiche del {title}": "Statistics of {title}",
    "Volte al giorno": "Times per day",
    "Giorni": "Days",
    "Distribuzione giornaliera  (◆ media, — mediana)": "Daily distribution  (◆ mean, — median)",
    # Shared: leaderboards, statistics and records compared with the group (#201)
    "In testa a pari merito con {value}: {names}.": "Tied for the lead with {value}: {names}.",
    "{name} è in testa con {value}, {gap} più di {other}.": "{name} leads with {value}, {gap} more than {other}.",
    "{name}: {place}° con {value}, a {gap} da {other}": "{name}: #{place} with {value}, {gap} behind {other}",
    ", a questo ritmo {place}° (~{value} 💩)": ", at this pace #{place} (~{value} 💩)",
    "{value} al giorno": "{value} a day",
    "{name}, come vai: {label}.": "{name}, how you are doing: {label}.",
    "molto regolare": "very regular",
    "abbastanza regolare": "fairly regular",
    "a sbalzi": "up and down",
    " (record del gruppo)": " (group record)",
    " (record del gruppo, a pari merito)": " (group record, tied)",
    " ({place}° su {total})": " (#{place} of {total})",
}

TRANSLATIONS = {'en': EN}
