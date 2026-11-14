"""Text of the bot messages built from the results of analysis.py.

The functions return Telegram (legacy) Markdown. Names must already be escaped by the caller.
"""
from analysis import Period, UserRecords

DISPLAY_FORMAT = "%d-%m-%Y"


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
    lines = [f"📊 *Record per {name}* 📊\n"]

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

