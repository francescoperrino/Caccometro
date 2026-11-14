"""Text of the bot messages built from the results of analysis.py.

The functions return Telegram (legacy) Markdown. Names must already be escaped by the caller.
"""
from analysis import GroupBoard, Leaders, Period, UserRecords

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
        text = f"*{names.get(holder.key, str(holder.key))}*"
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
