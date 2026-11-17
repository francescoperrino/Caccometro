"""Text of the bot messages built from the results of analysis.py.

The functions return Telegram (legacy) Markdown. Names must already be escaped by the caller.
"""
import re

from caccometro.analysis import GroupBoard, Leaders, Period, UserRecords
from caccometro.config import DISPLAY_FORMAT, MONTH_NAMES
from caccometro.trophies import STREAK_STEP


ESCAPED = re.compile(r"(\\[_*`\[])")


def bold(text):
    """`text` in bold. Legacy Markdown shows the backslash of an escaped character written inside an entity, and an
    unescaped `*` breaks the message, so the bold is closed and reopened around each escaped character
    (which is then not bold): '@mario\\_rossi' becomes '*@mario*\\_*rossi*'."""
    return "".join(part if ESCAPED.fullmatch(part) else f"*{part}*" for part in ESCAPED.split(text) if part)


def _times(n):
    return "volta" if n == 1 else "volte"


def _days(n):
    return "giorno" if n == 1 else "giorni"


def _matches_record(current, record_value):
    """True when the current value equals the record; a record of 1 is not worth celebrating."""
    return current >= 2 and current == record_value


def _consecutive_days(n):
    return f"{n} {'giorno consecutivo' if n == 1 else 'giorni consecutivi'}"


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
    return text + (f" e altri {extra}" if extra > 0 else "")


def _month(month):
    year, number = month
    return f"{number:02d}-{year}"


def _month_label(months):
    return "nei mesi" if len(months) > 1 else "nel mese"


def format_user_record(name, records: UserRecords):
    """The /record message of one user: every record followed by where the user stands right now.

    name: the user's name, already escaped for Markdown.
    """
    status = records.status
    lines = [f"📊 {bold(f'Record per {name}')} 📊\n"]

    # most 💩 in a day
    daily = records.daily
    if len(daily.when) > RECENT:     # with small counts a record is often tied on dozens of days
        lines.append(f"🥵 Hai fatto 💩 {daily.value} {_times(daily.value)} in {len(daily.when)} giorni diversi "
                     f"(gli ultimi: {', '.join(_date(d) for d in daily.when[-RECENT:][::-1])}).")
    else:
        lines.append(f"🥵 Hai fatto 💩 {daily.value} {_times(daily.value)} il {_recent(daily.when, _date)}.")
    flag = " 🔥 è il tuo record!" if _matches_record(status.today_count, daily.value) else ""
    lines.append(f"   ↳ Oggi: {status.today_count} 💩{flag}")

    # months: records only exist for completed months
    best, worst = records.best_month, records.worst_month
    if best is not None:
        lines.append(f"🤩 Hai fatto 💩 {best.value} {_times(best.value)} {_month_label(best.when)} {_recent(best.when, _month)}.")
    else:
        lines.append("🗓️ Il record mensile sarà disponibile dopo il primo mese completo.")
    if worst is not None:
        lines.append(f"😭 Hai fatto solo 💩 {worst.value} {_times(worst.value)} {_month_label(worst.when)} {_recent(worst.when, _month)}.")
    else:
        lines.append("🗓️ Il mese peggiore sarà disponibile dopo almeno due mesi di dati.")
    flag = ""
    if best is not None and status.month_count > best.value:
        flag = " 🔥 già oltre il tuo record mensile!"
    elif best is not None and _matches_record(status.month_count, best.value):
        flag = " 🔥 record mensile eguagliato!"
    lines.append(f"   ↳ Questo mese: {status.month_count} 💩 finora{flag}")

    # longest run of consecutive days
    streak = records.streak_days
    lines.append(f"🥳 Hai fatto 💩 per {_consecutive_days(streak.value)} ({_recent(streak.when, _period)}).")
    if status.streak_days > 0:
        until = "" if status.streak_active_today else " (fino a ieri)"
        flag = " 🔥 è il tuo record!" if _matches_record(status.streak_days, streak.value) else ""
        lines.append(f"   ↳ In corso: {status.streak_days} {'giorno' if status.streak_days == 1 else 'giorni'} di fila{until}{flag}")
    else:
        lines.append("   ↳ In corso: nessuna serie")

    # most 💩 in a run
    streak_count = records.streak_count
    lines.append(f"🫣 Hai fatto 💩 {streak_count.value} {_times(streak_count.value)} in una serie di giorni consecutivi "
                 f"({_recent(streak_count.when, _period)}).")
    if status.streak_count > 0:
        flag = " 🔥 è il tuo record!" if _matches_record(status.streak_count, streak_count.value) else ""
        lines.append(f"   ↳ In corso: {status.streak_count} 💩 nella serie{flag}")
    else:
        lines.append("   ↳ In corso: nessuna serie")

    # longest pause
    gap = records.gap_days
    if gap is not None:
        lines.append(f"🤢 Non hai fatto 💩 per {_consecutive_days(gap.value)} ({_recent(gap.when, _period)}).")
    else:
        lines.append("🤢 Non ci sono ancora giorni senza 💩 tra la prima e l'ultima registrazione.")
    if status.gap_days == 0:
        lines.append("   ↳ In corso: oggi hai fatto 💩, nessuna pausa")
    else:
        flag = " 🔥 già oltre il record!" if gap is not None and status.gap_days > gap.value else ""
        lines.append(f"   ↳ In corso: {status.gap_days} {_days(status.gap_days)} senza 💩{flag}")

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
    return ", ".join(parts) + (f" e altri {extra}" if extra > 0 else "")


def format_group_record(board: GroupBoard, names):
    """The /record message of the whole group: who holds each record, and who leads right now.

    names: {user key: name already escaped for Markdown}.
    """
    lines = ["🏆 *Record del gruppo* 🏆\n"]
    if board.daily is not None:
        lines.append(f"🥵 Più 💩 in un giorno: {board.daily.value} {_times(board.daily.value)} — {_holders(board.daily, names, _date)}")
    if board.best_month is not None:
        lines.append(f"🤩 Più 💩 in un mese: {board.best_month.value} {_times(board.best_month.value)} — "
                     f"{_holders(board.best_month, names, _month)}")
    if board.worst_month is not None:
        lines.append(f"😭 Meno 💩 in un mese: {board.worst_month.value} {_times(board.worst_month.value)} — "
                     f"{_holders(board.worst_month, names, _month)}")
    if board.streak_days is not None:
        lines.append(f"🥳 Serie più lunga: {_consecutive_days(board.streak_days.value)} — "
                     f"{_holders(board.streak_days, names, _period)}")
    if board.streak_count is not None:
        lines.append(f"🫣 Più 💩 in una serie: {board.streak_count.value} {_times(board.streak_count.value)} — "
                     f"{_holders(board.streak_count, names, _period)}")
    if board.gap_days is not None:
        lines.append(f"🤢 Pausa più lunga: {_consecutive_days(board.gap_days.value)} — {_holders(board.gap_days, names, _period)}")

    now = []
    if board.today is not None:
        now.append(f"💩 Oggi: {board.today.value} {_times(board.today.value)} — {_holders(board.today, names)}")
    if board.active_streak is not None:
        now.append(f"🔥 Serie in corso più lunga: {board.active_streak.value} {_days(board.active_streak.value)} — "
                   f"{_holders(board.active_streak, names, _period)}")
    if board.active_gap is not None:
        now.append(f"🐢 Pausa in corso più lunga: {board.active_gap.value} {_days(board.active_gap.value)} — "
                   f"{_holders(board.active_gap, names)}")
    if now:
        lines.append("\n📍 *Adesso*")
        lines += now

    lines.append("\nIl tuo: /record io — di un altro: /record @username (o rispondi a un suo messaggio)")
    return "\n".join(lines)


# ---------------------------------------------------------------- trophies

MAX_LISTED = 6   # months and streaks listed in the personal trophies (the most recent ones)
TROPHY_LEGEND = f"👑 💩 dell'anno · 🏅 💩 del mese · 🔥 {STREAK_STEP} giorni di fila"


def _month_name(month):
    year, number = month
    return f"{MONTH_NAMES[number]} {year}"


def _names(user_ids, names):
    """'*@mario*', '*@mario* e *@luigi*', '*@anna*, *@mario* e *@luigi*'."""
    parts = [bold(names.get(user_id, str(user_id))) for user_id in user_ids]
    return parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " e " + parts[-1]


def format_streak_trophy(days):
    """Line added to the reply to the 💩 that completes a multiple of STREAK_STEP consecutive days."""
    return f"🔥 *Nuovo trofeo!* {days} giorni di fila con almeno una 💩!"


def format_group_trophies(trophies, names):
    """The /trofei message of the whole group: how many trophies of each kind every winner has.

    trophies: {user key: UserTrophies}; names: {user key: name already escaped for Markdown}.
    """
    lines = ["🏆 *Bacheca dei trofei* 🏆\n"]
    if not trophies:
        lines.append(f"Ancora nessun trofeo: servono {STREAK_STEP} giorni di fila con almeno una 💩, "
                     "oppure vincere un mese.")
    else:
        ranked = sorted(trophies.items(), key=lambda item: (-len(item[1].years), -len(item[1].months),
                                                            -item[1].streak_trophies, names.get(item[0], "")))
        for key, user in ranked:
            counts = (("👑", len(user.years)), ("🏅", len(user.months)), ("🔥", user.streak_trophies))
            lines.append(f"{bold(names.get(key, str(key)))}: " + " · ".join(f"{emoji} {n}" for emoji, n in counts if n))
        lines.append(f"\n{TROPHY_LEGEND}")
    lines.append(("" if trophies else "\n") + "I tuoi: /trofei io — di un altro: /trofei @username (o rispondi a un suo messaggio)")
    return "\n".join(lines)


def format_user_trophies(name, trophies, current_streak):
    """The /trofei message of one user: every trophy, then how far the next streak trophy is.

    name: already escaped for Markdown; trophies: UserTrophies or None; current_streak: days of the run in progress.
    """
    lines = [f"🏆 {bold(f'Trofei di {name}')} 🏆\n"]
    if trophies is None:
        lines.append("Ancora nessun trofeo.")
    else:
        if trophies.years:
            lines.append(f"👑 💩 dell'anno: {', '.join(str(year) for year in reversed(trophies.years))}")
        if trophies.months:
            lines.append(f"🏅 💩 del mese ({len(trophies.months)}): {_recent(trophies.months, _month_name, MAX_LISTED)}")
        if trophies.streaks:
            n = trophies.streak_trophies
            lines.append(f"🔥 Serie: {n} {'trofeo' if n == 1 else 'trofei'}")
            for period, days in trophies.streaks[-MAX_LISTED:][::-1]:
                lines.append(f"   ↳ {days} giorni: {_period(period)}")
            extra = len(trophies.streaks) - MAX_LISTED
            if extra > 0:
                lines.append(f"   ↳ e altre {extra} serie")
    if current_streak > 0:
        missing = STREAK_STEP - current_streak % STREAK_STEP
        lines.append(f"\n📍 Serie in corso: {current_streak} {_days(current_streak)} di fila, "
                     f"{'ne manca 1' if missing == 1 else f'ne mancano {missing}'} al prossimo trofeo")
    else:
        lines.append("\n📍 Nessuna serie in corso: oggi è il giorno buono per iniziarne una!")
    return "\n".join(lines)


def format_new_period(today, month_winners, year_winners, names):
    """Midnight message on the first day of a month: the 💩 of the month just ended and, on January 1st, of the year.

    month_winners / year_winners: Winners or None; names: {user key: name already escaped for Markdown}.
    Returns None when there is nobody to celebrate.
    """
    if month_winners is None and year_winners is None:
        return None

    def winner(label, winners):
        each = " a testa" if len(winners.user_ids) > 1 else ""
        return f"{label}: {_names(winners.user_ids, names)} con {winners.total} 💩{each}"

    if today.month == 1:
        lines = [f"🎆 *Buon anno! Benvenuto {today.year}!* 🥂\n"]
        if month_winners is not None:
            lines.append(winner("🏅 💩 di dicembre", month_winners))
        if year_winners is not None:
            lines.append(winner(f"👑 💩 dell'anno {today.year - 1}", year_winners))
        lines.append(f"\nComplimenti! Che il {today.year} sia regolare come un orologio svizzero 🎉")
    else:
        ended = (today.year, today.month - 1)
        lines = [f"🌙 *Mezzanotte: {_month_name(ended)} è finito!*\n",
                 winner("🏅 💩 del mese", month_winners),
                 f"\nComplimenti! Si riparte da zero: buon {MONTH_NAMES[today.month]} e buone 💩 🧻"]
    return "\n".join(lines)
