"""Text of the bot messages built from the results of analysis.py.

The functions return Telegram (legacy) Markdown. Names must already be escaped by the caller.
"""
import random
import re

from caccometro.analysis import GroupBoard, Leaders, Period, UserRecords
from caccometro.config import DISPLAY_FORMAT
from caccometro.i18n import month_name, tr
from caccometro.trophies import STREAK_STEP


ESCAPED = re.compile(r"(\\[_*`\[])")


def _bold(text):
    """`text` in bold. Legacy Markdown shows the backslash of an escaped character written inside an entity, and an
    unescaped `*` breaks the message, so the bold is closed and reopened around each escaped character
    (which is then not bold): '@mario\\_rossi' becomes '*@mario*\\_*rossi*'."""
    return "".join(part if ESCAPED.fullmatch(part) else f"*{part}*" for part in ESCAPED.split(text) if part)


def _times(n):
    return tr("volta") if n == 1 else tr("volte")


def _days(n):
    return tr("giorno") if n == 1 else tr("giorni")


def _matches_record(current, record_value):
    """True when the current value equals the record; a record of 1 is not worth celebrating."""
    return current >= 2 and current == record_value


def _consecutive_days(n):
    return (tr("{n} giorno consecutivo") if n == 1 else tr("{n} giorni consecutivi")).format(n=n)


def _date(day):
    return day.strftime(DISPLAY_FORMAT)


def _period(period: Period):
    if period.start == period.end:
        return _date(period.start)
    return f"{_date(period.start)} - {_date(period.end)}"


RECENT = 3   # tied days/months/periods listed in the personal message (the most recent ones)


def _recent(items, fmt, limit=RECENT):
    """The most recent items first (items are in chronological order); the others are only counted."""
    shown = items[-limit:][::-1]
    text = ", ".join(fmt(item) for item in shown)
    extra = len(items) - len(shown)
    return text + (tr(" e altri {extra}").format(extra=extra) if extra > 0 else "")


def _month(month):
    year, number = month
    return f"{number:02d}-{year}"


def _month_label(months):
    return tr("nei mesi") if len(months) > 1 else tr("nel mese")


# ---------------------------------------------------------------- leaderboards and statistics

def tie_positions(values):
    """The place of each value of a list sorted best first: equal values share the place (1, 2, 2, 4)."""
    return [1 + values.index(value) for value in values]


def flame(status):
    """' 🔥5' (' ⏳5' while today's 💩 is missing) after a name: the streak in progress, from 3 days on."""
    if status.streak_days < 3:
        return ""
    return f" {'🔥' if status.streak_active_today else '⏳'}{status.streak_days}"


def _gap(a, b):
    difference = a - b
    return str(int(difference)) if difference == int(difference) else f"{difference:.2f}"


def standing_lines(rows, names, sender_id, unit, forecast=None):
    """Who leads and where the sender is, as sentences for the whole chat (the Mini App's "answer", in the third person).

    rows: [(user_id, value)] best first; names: {user_id: name escaped for Markdown}; unit: value -> text;
    forecast: {user_id: total at the end of the period}, to add the place at this pace for the sender.
    """
    if len(rows) < 2:
        return []
    top = rows[0][1]
    leaders = [user_id for user_id, value in rows if value == top]
    if len(leaders) > 1:
        lines = [tr("In testa a pari merito con {value}: {names}.").format(
            value=unit(top), names=", ".join(names[user_id] for user_id in leaders))]
    else:
        other, below = next((user_id, value) for user_id, value in rows if value < top)
        lines = [tr("{name} è in testa con {value}, {gap} più di {other}.").format(
            name=names[leaders[0]], value=unit(top), gap=_gap(top, below), other=names[other])]
    mine = next((value for user_id, value in rows if user_id == sender_id), None)
    if mine is not None and mine < top:
        above_id, above = min(((user_id, value) for user_id, value in rows if value > mine), key=lambda row: row[1])
        line = tr("{name}: {place}° con {value}, a {gap} da {other}").format(
            name=names[sender_id], place=1 + sum(value > mine for _, value in rows), value=unit(mine),
            gap=_gap(above, mine), other=names[above_id])
        if forecast and sender_id in forecast:
            line += tr(", a questo ritmo {place}° (~{value} 💩)").format(
                place=1 + sum(total > forecast[sender_id] for total in forecast.values()), value=forecast[sender_id])
        lines.append(line + ".")
    return lines


def _place(places, key):
    """' (#2 of 5)' after a record line: where the person stands among the group; nothing when there is nobody to compare."""
    if key not in places:
        return ""
    place, total, shared = places[key]
    if place == 1:
        return tr(" (record del gruppo, a pari merito)") if shared else tr(" (record del gruppo)")
    return tr(" ({place}° su {total})").format(place=place, total=total)


def format_user_record(name, records: UserRecords, places=None):
    """The /records message of one user: every record followed by where the user stands right now.

    name: the user's name, already escaped for Markdown; places: analysis.record_places, the place among the group.
    """
    status = records.status
    places = places or {}
    lines = [f"📊 {_bold(tr('Record per {name}').format(name=name))} 📊\n"]
    record_flag = tr(" 🔥 è il record!")
    no_streak = tr("   ↳ In corso: nessuna serie")

    # most 💩 in a day
    daily = records.daily
    if len(daily.when) > RECENT:     # with small counts a record is often tied on dozens of days
        lines.append(tr("🥵 Più 💩 in un giorno: {value} {times} in {count} giorni diversi (gli ultimi: {days}).").format(
            value=daily.value, times=_times(daily.value), count=len(daily.when),
            days=', '.join(_date(d) for d in daily.when[-RECENT:][::-1])))
    else:
        lines.append(tr("🥵 Più 💩 in un giorno: {value} {times} il {days}.").format(
            value=daily.value, times=_times(daily.value), days=_recent(daily.when, _date)))
    lines[-1] += _place(places, 'daily')
    flag = record_flag if _matches_record(status.today_count, daily.value) else ""
    lines.append(tr("   ↳ Oggi: {count} 💩").format(count=status.today_count) + flag)

    # months: records only exist for completed months
    best, worst = records.best_month, records.worst_month
    if best is not None:
        lines.append(tr("🤩 Mese migliore: {value} 💩 {label} {months}.").format(
            value=best.value, label=_month_label(best.when), months=_recent(best.when, _month)))
    else:
        lines.append(tr("🗓️ Il record mensile sarà disponibile dopo il primo mese completo."))
    lines[-1] += _place(places, 'best_month')
    if worst is not None:
        lines.append(tr("😭 Mese peggiore: solo {value} 💩 {label} {months}.").format(
            value=worst.value, label=_month_label(worst.when), months=_recent(worst.when, _month)))
    else:
        lines.append(tr("🗓️ Il mese peggiore sarà disponibile dopo almeno due mesi di dati."))
    lines[-1] += _place(places, 'worst_month')
    flag = ""
    if best is not None and status.month_count > best.value:
        flag = tr(" 🔥 già oltre il record mensile!")
    elif best is not None and _matches_record(status.month_count, best.value):
        flag = tr(" 🔥 record mensile eguagliato!")
    lines.append(tr("   ↳ Questo mese: {count} 💩 finora").format(count=status.month_count) + flag)

    # longest run of consecutive days
    streak = records.streak_days
    lines.append(tr("🥳 Serie più lunga: {days} ({when}).").format(
        days=_consecutive_days(streak.value), when=_recent(streak.when, _period)))
    lines[-1] += _place(places, 'streak_days')
    if status.streak_days > 0:
        until = "" if status.streak_active_today else tr(" (fino a ieri)")
        flag = record_flag if _matches_record(status.streak_days, streak.value) else ""
        lines.append(tr("   ↳ In corso: {count} {days} di fila").format(count=status.streak_days, days=_days(status.streak_days))
                     + until + flag)
    else:
        lines.append(no_streak)

    # most 💩 in a run
    streak_count = records.streak_count
    lines.append(tr("🫣 Più 💩 in una serie: {value} {times} ({when}).").format(
        value=streak_count.value, times=_times(streak_count.value), when=_recent(streak_count.when, _period)))
    lines[-1] += _place(places, 'streak_count')
    if status.streak_count > 0:
        flag = record_flag if _matches_record(status.streak_count, streak_count.value) else ""
        lines.append(tr("   ↳ In corso: {count} 💩 nella serie").format(count=status.streak_count) + flag)
    else:
        lines.append(no_streak)

    # longest pause
    gap = records.gap_days
    if gap is not None:
        lines.append(tr("🤢 Pausa più lunga: {days} ({when}).").format(
            days=_consecutive_days(gap.value), when=_recent(gap.when, _period)))
    else:
        lines.append(tr("🤢 Non ci sono ancora giorni senza 💩 tra la prima e l'ultima registrazione."))
    lines[-1] += _place(places, 'gap_days')
    if status.gap_days == 0:
        lines.append(tr("   ↳ In corso: 💩 fatta oggi, nessuna pausa"))
    else:
        flag = tr(" 🔥 già oltre il record!") if gap is not None and status.gap_days > gap.value else ""
        lines.append(tr("   ↳ In corso: {count} {days} senza 💩").format(count=status.gap_days, days=_days(status.gap_days)) + flag)

    return "\n".join(lines)


# ---------------------------------------------------------------- the whole group

MAX_HOLDERS = 3     # holders listed for a record; the others are summarized ("e altri 2")
MAX_WHEN = 2        # dates/months/periods listed for each holder


def _when_text(when, fmt):
    """The most recent dates/months/periods first (they are in chronological order)."""
    shown = "; ".join(fmt(item) for item in when[-MAX_WHEN:][::-1])
    return shown + ("…" if len(when) > MAX_WHEN else "")


def _holders(leaders: Leaders, names, fmt=None):
    """'*@mario* (10-03-2025), *@luigi* (22-05-2025) e altri 2'."""
    parts = []
    for holder in leaders.holders[:MAX_HOLDERS]:
        text = _bold(names.get(holder.key, str(holder.key)))
        if fmt is not None and holder.when:
            text += f" ({_when_text(holder.when, fmt)})"
        parts.append(text)
    extra = len(leaders.holders) - MAX_HOLDERS
    return ", ".join(parts) + (tr(" e altri {extra}").format(extra=extra) if extra > 0 else "")


def format_group_record(board: GroupBoard, names):
    """The /records message of the whole group: who holds each record, and who leads right now.

    names: {user key: name already escaped for Markdown}.
    """
    def times(leaders):
        return f"{leaders.value} {_times(leaders.value)}"

    def days(leaders):
        return f"{leaders.value} {_days(leaders.value)}"

    lines = [tr("🏆 *Record del gruppo* 🏆") + "\n"]
    if board.daily is not None:
        lines.append(tr("🥵 Più 💩 in un giorno: {value} — {holders}").format(
            value=times(board.daily), holders=_holders(board.daily, names, _date)))
    if board.best_month is not None:
        lines.append(tr("🤩 Più 💩 in un mese: {value} — {holders}").format(
            value=times(board.best_month), holders=_holders(board.best_month, names, _month)))
    if board.worst_month is not None:
        lines.append(tr("😭 Meno 💩 in un mese: {value} — {holders}").format(
            value=times(board.worst_month), holders=_holders(board.worst_month, names, _month)))
    if board.streak_days is not None:
        lines.append(tr("🥳 Serie più lunga: {value} — {holders}").format(
            value=_consecutive_days(board.streak_days.value), holders=_holders(board.streak_days, names, _period)))
    if board.streak_count is not None:
        lines.append(tr("🫣 Più 💩 in una serie: {value} — {holders}").format(
            value=times(board.streak_count), holders=_holders(board.streak_count, names, _period)))
    if board.gap_days is not None:
        lines.append(tr("🤢 Pausa più lunga: {value} — {holders}").format(
            value=_consecutive_days(board.gap_days.value), holders=_holders(board.gap_days, names, _period)))

    now = []
    if board.today is not None:
        now.append(tr("💩 Oggi: {value} — {holders}").format(value=times(board.today), holders=_holders(board.today, names)))
    if board.active_streak is not None:
        now.append(tr("🔥 Serie in corso più lunga: {value} — {holders}").format(
            value=days(board.active_streak), holders=_holders(board.active_streak, names, _period)))
    if board.active_gap is not None:
        now.append(tr("🐢 Pausa in corso più lunga: {value} — {holders}").format(
            value=days(board.active_gap), holders=_holders(board.active_gap, names)))
    if now:
        lines.append("\n" + tr("📍 *Adesso*"))
        lines += now

    lines.append("\n" + tr("Il tuo: /record io — di un altro: /record @username (o rispondi a un suo messaggio)"))
    return "\n".join(lines)


# ---------------------------------------------------------------- trophies

MAX_LISTED = 6   # months and streaks listed in the personal trophies (the most recent ones)


def _month_name(month):
    year, number = month
    return f"{month_name(number)} {year}"


def _names(user_ids, names):
    """Bold names of the users, joined as a sentence: "A", "A and B", "A, B and C" ("and" in the chat language).

    user_ids: IDs of the users to name; names: {user ID: name already escaped for Markdown}.
    A user missing from `names` is shown by ID. Example with made-up names: "*@anna*, *@bob* and *@carl*".
    """
    parts = [_bold(names.get(user_id, str(user_id))) for user_id in user_ids]
    return parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + tr(" e ") + parts[-1]


def _season_name(season):
    """Label of a season (year, quarter) in the chat language: (2026, 4) -> "ottobre–dicembre 2026" (Italian)."""
    year, quarter = season
    return f"{month_name(3 * quarter - 2)}–{month_name(3 * quarter)} {year}"


def format_season_line(season, result, names):
    """One line of /conquests: who leads the current season so far.

    season: (year, quarter); result: SeasonResult of that season; names: {user ID: name escaped for Markdown}.
    """
    return tr("🚩 Stagione {season}: conquistatore {conquerors} ({n}), re {king}").format(
        season=_season_name(season), conquerors=_names(result.conquerors, names), n=result.conquests,
        king=_names([result.king], names))


def format_streak_trophy(days):
    """Line added to the reply to the 💩 that completes a multiple of STREAK_STEP consecutive days."""
    return tr("🔥 *Nuovo trofeo!* {days} giorni di fila con almeno una 💩!").format(days=days)


def format_group_trophies(trophies, names):
    """The /trophies message of the whole group: how many trophies of each kind every winner has.

    trophies: {user key: UserTrophies}; names: {user key: name already escaped for Markdown}.
    """
    lines = [tr("🏆 *Bacheca dei trofei* 🏆") + "\n"]
    if not trophies:
        lines.append(tr("🤷 Ancora nessun trofeo: servono {days} giorni di fila con almeno una 💩, "
                        "oppure vincere un mese.").format(days=STREAK_STEP))
    else:
        ranked = sorted(trophies.items(), key=lambda item: (-len(item[1].years), -len(item[1].months),
                                                            -item[1].streak_trophies, -len(item[1].conqueror),
                                                            -len(item[1].king), names.get(item[0], "")))
        for key, user in ranked:
            counts = (("👑", len(user.years)), ("🏅", len(user.months)), ("🔥", user.streak_trophies),
                      ("🚩", len(user.conqueror)), ("⛰️", len(user.king)))
            lines.append(f"{_bold(names.get(key, str(key)))}: " + " · ".join(f"{emoji} {n}" for emoji, n in counts if n))
        lines.append("\n" + tr("👑 💩 dell'anno · 🏅 💩 del mese · 🔥 {days} giorni di fila").format(days=STREAK_STEP))
        if any(user.conqueror or user.king for user in trophies.values()):
            lines.append(tr("🚩 conquistatore della stagione · ⛰️ re della stagione"))
    lines.append(("" if trophies else "\n")
                 + tr("I tuoi: /trofei io — di un altro: /trofei @username (o rispondi a un suo messaggio)"))
    return "\n".join(lines)


def format_user_trophies(name, trophies, current_streak):
    """The /trophies message of one user: every trophy, then how far the next streak trophy is.

    name: already escaped for Markdown; trophies: UserTrophies or None; current_streak: days of the run in progress.
    """
    lines = [f"🏆 {_bold(tr('Trofei di {name}').format(name=name))} 🏆\n"]
    if trophies is None:
        lines.append(tr("🤷 Ancora nessun trofeo."))
    else:
        if trophies.years:
            lines.append(tr("👑 💩 dell'anno: {years}").format(years=', '.join(str(year) for year in reversed(trophies.years))))
        if trophies.months:
            lines.append(tr("🏅 💩 del mese ({count}): {months}").format(
                count=len(trophies.months), months=_recent(trophies.months, _month_name, MAX_LISTED)))
        if trophies.conqueror:
            lines.append(tr("🚩 Conquistatore della stagione: {seasons}").format(
                seasons=_recent(trophies.conqueror, _season_name, MAX_LISTED)))
        if trophies.king:
            lines.append(tr("⛰️ Re della stagione: {seasons}").format(
                seasons=_recent(trophies.king, _season_name, MAX_LISTED)))
        if trophies.streaks:
            n = trophies.streak_trophies
            lines.append((tr("🔥 Serie: {n} trofeo") if n == 1 else tr("🔥 Serie: {n} trofei")).format(n=n))
            for period, days in trophies.streaks[-MAX_LISTED:][::-1]:
                lines.append(tr("   ↳ {days} giorni: {period}").format(days=days, period=_period(period)))
            extra = len(trophies.streaks) - MAX_LISTED
            if extra > 0:
                lines.append(tr("   ↳ e altre {extra} serie").format(extra=extra))
    if current_streak > 0:
        missing = STREAK_STEP - current_streak % STREAK_STEP
        lines.append("\n" + (tr("📍 Serie in corso: {count} {days} di fila, ne manca 1 al prossimo trofeo") if missing == 1
                             else tr("📍 Serie in corso: {count} {days} di fila, ne mancano {missing} al prossimo trofeo"))
                     .format(count=current_streak, days=_days(current_streak), missing=missing))
    else:
        lines.append("\n" + tr("📍 Nessuna serie in corso: oggi è il giorno buono per iniziarne una!"))
    return "\n".join(lines)


def format_new_period(today, month_winners, year_winners, names, season=None):
    """Midnight message on the first day of a month: the 💩 of the month just ended and, on January 1st, of the year.

    month_winners / year_winners: Winners or None; names: {user key: name already escaped for Markdown};
    season: ((year, quarter), SeasonResult) of the season that just ended, on the first day of a quarter, or None.
    Returns None when there is nobody to celebrate.
    """
    if month_winners is None and year_winners is None and season is None:
        return None

    def winner(label, winners):
        each = tr(" a testa") if len(winners.user_ids) > 1 else ""
        return tr("{label}: {names} con {total} 💩").format(
            label=label, names=_names(winners.user_ids, names), total=winners.total) + each

    if today.month == 1:
        lines = [tr("🎆 *Buon anno! Benvenuto {year}!* 🥂").format(year=today.year) + "\n"]
        if month_winners is not None:
            lines.append(winner(tr("🏅 💩 di dicembre"), month_winners))
        if year_winners is not None:
            lines.append(winner(tr("👑 💩 dell'anno {year}").format(year=today.year - 1), year_winners))
        closing = tr("Complimenti! Che il {year} sia regolare come un orologio svizzero 🎉").format(year=today.year)
    else:
        ended = (today.year, today.month - 1)
        lines = [tr("🌙 *Mezzanotte: {month} è finito!*").format(month=_month_name(ended)) + "\n"]
        if month_winners is not None:
            lines.append(winner(tr("🏅 💩 del mese"), month_winners))
        closing = tr("Complimenti! Si riparte da zero: buon {month} e buone 💩 🧻").format(month=month_name(today.month))
    if season is not None:
        key, result = season
        each = tr(" a testa") if len(result.conquerors) > 1 else ""
        lines += ["\n" + tr("🗺️ *Stagione {season} finita!*").format(season=_season_name(key)),
                  tr("🚩 Conquistatore: {names} con {n} conquiste").format(
                      names=_names(result.conquerors, names), n=result.conquests) + each,
                  tr("⛰️ Re della collina: {names}").format(names=_names([result.king], names))]
    lines.append("\n" + closing)
    return "\n".join(lines)


# Time slots of the Italian hour: (first hour, key); the last slot goes on until midnight
_SLOTS = ((0, "night"), (5, "early"), (9, "morning"), (12, "lunch"), (15, "afternoon"), (19, "evening"))


def _slot(hour):
    return [key for start, key in _SLOTS if hour >= start][-1]


def _poop_sentences():
    """The funny sentences, written as tr() literals (tests/test_i18n.py checks their translations) and built on
    each call, in the language in use. Keys: a time slot, "any" (good at any time), or (count class, slot or None)."""
    return {
        "night": [tr("{name} a quest'ora? La notte porta consiglio, e anche 💩."),
                  tr("Insonnia intestinale per {name}: il turno di notte non perdona."),
                  tr("{name} fa 💩 mentre il mondo dorme. Eroe silenzioso."),
                  tr("Luci spente, scarico acceso: bravo {name}.")],
        "early": [tr("{name} apre la giornata con una 💩: colazione dei campioni."),
                  tr("Il caffè ha fatto effetto, {name}!"),
                  tr("Sveglia, caffè, 💩: la routine di {name} non tradisce."),
                  tr("Buongiorno {name}, e buon alleggerimento!")],
        "morning": [tr("{name} fa 💩 invece di lavorare: la scusa perfetta."),
                    tr("Pausa strategica in bagno per {name}, telefono incluso."),
                    tr("Mattinata produttiva per {name}: almeno qualcosa è uscito."),
                    tr("{name} porta a termine un compito importante.")],
        "lunch": [tr("Il pranzo è appena finito e {name} è già operativo."),
                  tr("{name} smaltisce il pranzo in tempo record."),
                  tr("Digestione lampo per {name}!"),
                  tr("Dopo pranzo il dovere chiama, e {name} risponde.")],
        "afternoon": [tr("Pomeriggio di gloria per {name}."),
                      tr("{name} approfitta della pausa pomeridiana: saggio."),
                      tr("Merenda smaltita? {name} sì."),
                      tr("{name} sopravvive al calo di metà pomeriggio con una 💩.")],
        "evening": [tr("{name} chiude la giornata in bellezza."),
                    tr("Dopo cena si smaltisce: ci pensa {name}."),
                    tr("Serata di relax per {name}, trono incluso."),
                    tr("{name} va a letto più leggero.")],
        "any": [tr("Complimenti {name}!"),
                tr("{name} ha fatto il suo dovere."),
                tr("Un applauso per {name}, che non si tira indietro."),
                tr("Missione compiuta per {name}."),
                tr("{name} lascia il segno."),
                tr("Che soddisfazione, {name}!"),
                tr("La classifica ringrazia {name}."),
                tr("{name} scrive un'altra pagina di storia.")],
        ("first", None): [tr("Prima 💩 della giornata per {name}: si parte bene."),
                          tr("{name} inaugura la giornata."),
                          tr("Ecco la prima di oggi, {name}!")],
        ("first", "early"): [tr("{name} è mattiniero: la prima 💩 arriva presto.")],
        ("first", "lunch"): [tr("Prima 💩 della giornata dopo pranzo? {name} ci ha messo un po'.")],
        ("first", "night"): [tr("{name} inizia la giornata a notte fonda.")],
        ("third", None): [tr("Di nuovo {name}?! Che cosa ha mangiato?"),
                          tr("{name} non si ferma più."),
                          tr("{name} fa le cose in grande oggi.")],
        ("third", "night"): [tr("{name} nelle ore piccole e ancora 💩: serve un medico?")],
        ("third", "lunch"): [tr("Il pranzo non è andato giù a {name}: ancora!")],
    }


def _poop_pool(hour, count):
    """The sentences a 💩 can be answered with, by Italian hour and by count of the day.

    The first and the 3rd or more 💩 of the day have their own sentences: those of their time slot when there are
    some, else the slot's ones with the generic ones and those of that count. The 2nd has the slot and the generic ones.
    """
    sentences, slot = _poop_sentences(), _slot(hour)
    kind = "first" if count == 1 else "third" if count >= 3 else None
    if (kind, slot) in sentences:
        return sentences[(kind, slot)]
    return sentences[slot] + sentences["any"] + sentences.get((kind, None), [])


def poop_sentence(name, hour, count):
    """A random sentence for the 💩 of `name` sent at Italian `hour`, the `count`-th of the day."""
    return random.choice(_poop_pool(hour, count)).format(name=name)


def last_poop_sentence(name, days):
    """A random sentence for /last_poop: `days` since the last 💩 of `name` (0 is today, None is no data)."""
    if days is None:
        emoji, pool = "🤷", [tr("Nessun dato sull'ultima 💩 di {name}: si comincia oggi.")]
    elif days == 0:
        emoji, pool = "✅", [tr("{name} oggi ha già fatto 💩: il dovere è compiuto."),
                tr("{name} oggi ha già dato 💩. Riposa.")]
    elif days == 1:
        emoji, pool = "👀", [tr("{name} ha fatto 💩 ieri: tutto sotto controllo."),
                tr("L'ultima 💩 di {name} è di ieri: oggi è il giorno giusto.")]
    elif days <= 3:
        emoji, pool = "😬", [tr("{name} non fa 💩 da {days} giorni: inizia a farsi sentire."),
                tr("{name} non fa 💩 da {days} giorni: serve una prugna.")]
    else:
        emoji, pool = "🚨", [tr("{name} non fa 💩 da {days} giorni: serve un intervento."),
                tr("{name} non fa 💩 da {days} giorni?! Il bagno lo aspetta, ed è preoccupato.")]
    return f"{emoji} " + random.choice(pool).format(name=name, days=days)


def day_count_sentence(name, day, count):
    """A random sentence for /day_count: `count` 💩 of `name`, `day` being "oggi" or "il giorno <date>"."""
    if count == 0:
        emoji, pool = "🏖️", [tr("{name} {day} non ha fatto 💩: giornata di sciopero?"),
                tr("{name} {day}: zero 💩. Il registro è vuoto.")]
    elif count <= 2:
        once = tr("{name} {day} ha fatto 💩 {count} volta: nella norma.") if count == 1 \
            else tr("{name} {day} ha fatto 💩 {count} volte: nella norma.")
        emoji, pool = "🕰️", [once, tr("{name} {day}: {count} 💩, regolare come un orologio.")]
    else:
        emoji, pool = "🏆", [tr("{name} {day}: {count} 💩. Che cosa ha mangiato?"),
                tr("{name} {day}: {count} 💩, giornata da record.")]
    return f"{emoji} " + random.choice(pool).format(name=name, day=day, count=count)


def change_count_sentence(name, date, count, delta):
    """A random sentence for /add_poop (delta > 0) and /remove_poop (delta < 0): the new `count` of `name` on `date`."""
    if delta > 0:
        emoji, pool = "➕", [tr("Fatto: {name} il {date} sale a {count} 💩. La storia è riscritta."),
                tr("{name} il {date} ora ha {count} 💩. Meglio tardi che mai."),
                tr("Registrato: {name} il {date} arriva a {count} 💩.")]
    else:
        emoji, pool = "🧻", [tr("Cancellata: {name} il {date} scende a {count} 💩. Nessuno ha visto niente."),
                tr("{name} il {date} ora ha {count} 💩. Tirato lo sciacquone sul passato."),
                tr("Tolta: {name} il {date} resta con {count} 💩.")]
    return f"{emoji} " + random.choice(pool).format(name=name, date=date, count=count)


MEDALS = {1: '🥇', 2: '🥈', 3: '🥉'}


def ranked_line(position, name, value):
    """One line of a ranking: a medal and the name in bold for the first three."""
    if position in MEDALS:
        return f"{MEDALS[position]} {_bold(name)}: {value}\n"
    return f"{position}. {name}: {value}\n"
