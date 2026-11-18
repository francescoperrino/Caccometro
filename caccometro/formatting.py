"""Text of the bot messages built from the results of analysis.py.

The functions return Telegram (legacy) Markdown. Names must already be escaped by the caller.
"""
import re

from caccometro.analysis import GroupBoard, Leaders, Period, UserRecords
from caccometro.config import DISPLAY_FORMAT
from caccometro.i18n import month_name, tr
from caccometro.trophies import STREAK_STEP


ESCAPED = re.compile(r"(\\[_*`\[])")


def bold(text):
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


def format_user_record(name, records: UserRecords):
    """The /records message of one user: every record followed by where the user stands right now.

    name: the user's name, already escaped for Markdown.
    """
    status = records.status
    lines = [f"📊 {bold(tr('Record per {name}').format(name=name))} 📊\n"]
    record_flag = tr(" 🔥 è il tuo record!")
    no_streak = tr("   ↳ In corso: nessuna serie")

    # most 💩 in a day
    daily = records.daily
    if len(daily.when) > RECENT:     # with small counts a record is often tied on dozens of days
        lines.append(tr("🥵 Hai fatto 💩 {value} {times} in {count} giorni diversi (gli ultimi: {days}).").format(
            value=daily.value, times=_times(daily.value), count=len(daily.when),
            days=', '.join(_date(d) for d in daily.when[-RECENT:][::-1])))
    else:
        lines.append(tr("🥵 Hai fatto 💩 {value} {times} il {days}.").format(
            value=daily.value, times=_times(daily.value), days=_recent(daily.when, _date)))
    flag = record_flag if _matches_record(status.today_count, daily.value) else ""
    lines.append(tr("   ↳ Oggi: {count} 💩").format(count=status.today_count) + flag)

    # months: records only exist for completed months
    best, worst = records.best_month, records.worst_month
    if best is not None:
        lines.append(tr("🤩 Hai fatto 💩 {value} {times} {label} {months}.").format(
            value=best.value, times=_times(best.value), label=_month_label(best.when), months=_recent(best.when, _month)))
    else:
        lines.append(tr("🗓️ Il record mensile sarà disponibile dopo il primo mese completo."))
    if worst is not None:
        lines.append(tr("😭 Hai fatto solo 💩 {value} {times} {label} {months}.").format(
            value=worst.value, times=_times(worst.value), label=_month_label(worst.when), months=_recent(worst.when, _month)))
    else:
        lines.append(tr("🗓️ Il mese peggiore sarà disponibile dopo almeno due mesi di dati."))
    flag = ""
    if best is not None and status.month_count > best.value:
        flag = tr(" 🔥 già oltre il tuo record mensile!")
    elif best is not None and _matches_record(status.month_count, best.value):
        flag = tr(" 🔥 record mensile eguagliato!")
    lines.append(tr("   ↳ Questo mese: {count} 💩 finora").format(count=status.month_count) + flag)

    # longest run of consecutive days
    streak = records.streak_days
    lines.append(tr("🥳 Hai fatto 💩 per {days} ({when}).").format(
        days=_consecutive_days(streak.value), when=_recent(streak.when, _period)))
    if status.streak_days > 0:
        until = "" if status.streak_active_today else tr(" (fino a ieri)")
        flag = record_flag if _matches_record(status.streak_days, streak.value) else ""
        lines.append(tr("   ↳ In corso: {count} {days} di fila").format(count=status.streak_days, days=_days(status.streak_days))
                     + until + flag)
    else:
        lines.append(no_streak)

    # most 💩 in a run
    streak_count = records.streak_count
    lines.append(tr("🫣 Hai fatto 💩 {value} {times} in una serie di giorni consecutivi ({when}).").format(
        value=streak_count.value, times=_times(streak_count.value), when=_recent(streak_count.when, _period)))
    if status.streak_count > 0:
        flag = record_flag if _matches_record(status.streak_count, streak_count.value) else ""
        lines.append(tr("   ↳ In corso: {count} 💩 nella serie").format(count=status.streak_count) + flag)
    else:
        lines.append(no_streak)

    # longest pause
    gap = records.gap_days
    if gap is not None:
        lines.append(tr("🤢 Non hai fatto 💩 per {days} ({when}).").format(
            days=_consecutive_days(gap.value), when=_recent(gap.when, _period)))
    else:
        lines.append(tr("🤢 Non ci sono ancora giorni senza 💩 tra la prima e l'ultima registrazione."))
    if status.gap_days == 0:
        lines.append(tr("   ↳ In corso: oggi hai fatto 💩, nessuna pausa"))
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
        text = bold(names.get(holder.key, str(holder.key)))
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
    """'*@mario*', '*@mario* e *@luigi*', '*@anna*, *@mario* e *@luigi*'."""
    parts = [bold(names.get(user_id, str(user_id))) for user_id in user_ids]
    return parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + tr(" e ") + parts[-1]


def format_streak_trophy(days):
    """Line added to the reply to the 💩 that completes a multiple of STREAK_STEP consecutive days."""
    return tr("🔥 *Nuovo trofeo!* {days} giorni di fila con almeno una 💩!").format(days=days)


def format_group_trophies(trophies, names):
    """The /trophies message of the whole group: how many trophies of each kind every winner has.

    trophies: {user key: UserTrophies}; names: {user key: name already escaped for Markdown}.
    """
    lines = [tr("🏆 *Bacheca dei trofei* 🏆") + "\n"]
    if not trophies:
        lines.append(tr("Ancora nessun trofeo: servono {days} giorni di fila con almeno una 💩, "
                        "oppure vincere un mese.").format(days=STREAK_STEP))
    else:
        ranked = sorted(trophies.items(), key=lambda item: (-len(item[1].years), -len(item[1].months),
                                                            -item[1].streak_trophies, names.get(item[0], "")))
        for key, user in ranked:
            counts = (("👑", len(user.years)), ("🏅", len(user.months)), ("🔥", user.streak_trophies))
            lines.append(f"{bold(names.get(key, str(key)))}: " + " · ".join(f"{emoji} {n}" for emoji, n in counts if n))
        lines.append("\n" + tr("👑 💩 dell'anno · 🏅 💩 del mese · 🔥 {days} giorni di fila").format(days=STREAK_STEP))
    lines.append(("" if trophies else "\n")
                 + tr("I tuoi: /trofei io — di un altro: /trofei @username (o rispondi a un suo messaggio)"))
    return "\n".join(lines)


def format_user_trophies(name, trophies, current_streak):
    """The /trophies message of one user: every trophy, then how far the next streak trophy is.

    name: already escaped for Markdown; trophies: UserTrophies or None; current_streak: days of the run in progress.
    """
    lines = [f"🏆 {bold(tr('Trofei di {name}').format(name=name))} 🏆\n"]
    if trophies is None:
        lines.append(tr("Ancora nessun trofeo."))
    else:
        if trophies.years:
            lines.append(tr("👑 💩 dell'anno: {years}").format(years=', '.join(str(year) for year in reversed(trophies.years))))
        if trophies.months:
            lines.append(tr("🏅 💩 del mese ({count}): {months}").format(
                count=len(trophies.months), months=_recent(trophies.months, _month_name, MAX_LISTED)))
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


def format_new_period(today, month_winners, year_winners, names):
    """Midnight message on the first day of a month: the 💩 of the month just ended and, on January 1st, of the year.

    month_winners / year_winners: Winners or None; names: {user key: name already escaped for Markdown}.
    Returns None when there is nobody to celebrate.
    """
    if month_winners is None and year_winners is None:
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
        lines.append("\n" + tr("Complimenti! Che il {year} sia regolare come un orologio svizzero 🎉").format(year=today.year))
    else:
        ended = (today.year, today.month - 1)
        lines = [tr("🌙 *Mezzanotte: {month} è finito!*").format(month=_month_name(ended)) + "\n",
                 winner(tr("🏅 💩 del mese"), month_winners),
                 "\n" + tr("Complimenti! Si riparte da zero: buon {month} e buone 💩 🧻").format(month=month_name(today.month))]
    return "\n".join(lines)
