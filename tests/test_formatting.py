"""formatting.format_user_record: the /record message of a user, with the current status of every metric."""
from datetime import date

from analysis import analyze_user
from formatting import format_user_record

ROWS = [
    ("2024-01-01", 1), ("2024-01-02", 2), ("2024-01-03", 1),
    ("2024-01-07", 1),
    ("2024-02-10", 3),
    ("2024-03-01", 1),
]
APRIL = date(2024, 4, 15)


def message(rows, today=APRIL, name="@mario"):
    return format_user_record(name, analyze_user(rows, today))


def test_full_message_with_nothing_in_progress():
    assert message(ROWS) == (
        "📊 *Record per @mario* 📊\n"
        "\n"
        "🥵 Hai fatto 💩 3 volte il 10-02-2024.\n"
        "   ↳ Oggi: 0 💩\n"
        "🤩 Hai fatto 💩 5 volte nel mese 01-2024.\n"
        "😭 Hai fatto solo 💩 1 volta nel mese 03-2024.\n"
        "   ↳ Questo mese: 0 💩 finora\n"
        "🥳 Hai fatto 💩 per 3 giorni consecutivi (01-01-2024 - 03-01-2024).\n"
        "   ↳ In corso: nessuna serie\n"
        "🫣 Hai fatto 💩 4 volte in una serie di giorni consecutivi (01-01-2024 - 03-01-2024).\n"
        "   ↳ In corso: nessuna serie\n"
        "🤢 Non hai fatto 💩 per 33 giorni consecutivi (08-01-2024 - 09-02-2024).\n"
        "   ↳ In corso: 45 giorni senza 💩 🔥 già oltre il record!"
    )


def test_every_metric_has_a_current_status_line():
    lines = message(ROWS).split("\n")
    record_lines = [i for i, line in enumerate(lines) if line and line[0] in "🥵🤩😭🥳🫣🤢"]
    status_lines = [line for line in lines if line.startswith("   ↳")]
    assert len(record_lines) == 6
    assert len(status_lines) == 5          # one per metric; the two monthly records share one line


def test_new_user_gets_no_celebration_for_records_of_one():
    text = message([("2024-04-15", 1)])
    assert "🔥" not in text
    assert "Il record mensile sarà disponibile dopo il primo mese completo." in text
    assert "Il mese peggiore sarà disponibile dopo almeno due mesi di dati." in text
    assert "per 1 giorno consecutivo" in text and "1 volta" in text


def test_current_streak_is_celebrated_when_it_matches_the_record():
    rows = ROWS + [("2024-04-13", 1), ("2024-04-14", 2), ("2024-04-15", 1)]
    text = message(rows)
    assert "↳ In corso: 3 giorni di fila 🔥 è il tuo record!" in text
    assert "↳ In corso: 4 💩 nella serie 🔥 è il tuo record!" in text
    assert "↳ In corso: oggi hai fatto 💩, nessuna pausa" in text
    assert "↳ Oggi: 1 💩" in text and "↳ Questo mese: 4 💩 finora" in text


def test_a_streak_that_ended_yesterday_says_so():
    rows = ROWS + [("2024-04-12", 1), ("2024-04-13", 1), ("2024-04-14", 1)]
    text = message(rows)
    assert "↳ In corso: 3 giorni di fila (fino a ieri) 🔥 è il tuo record!" in text
    assert "↳ In corso: 1 giorno senza 💩" in text


def test_a_pause_longer_than_the_record_is_flagged_only_when_it_beats_it():
    assert "già oltre il record" in message(ROWS, date(2024, 4, 15))          # 45 days > 33
    assert "già oltre il record" not in message(ROWS, date(2024, 3, 20))     # 19 days < 33


def test_month_beating_the_monthly_record():
    rows = [("2024-01-10", 2), ("2024-02-10", 1)] + [(f"2024-03-{d:02d}", 1) for d in range(1, 6)]
    text = message(rows, date(2024, 3, 20))
    assert "↳ Questo mese: 5 💩 finora 🔥 già oltre il tuo record mensile!" in text


def test_month_matching_the_monthly_record():
    rows = [("2024-01-10", 2), ("2024-01-11", 1), ("2024-02-01", 1), ("2024-03-01", 1), ("2024-03-02", 1), ("2024-03-03", 1)]
    text = message(rows, date(2024, 3, 20))
    assert "↳ Questo mese: 3 💩 finora 🔥 record mensile eguagliato!" in text


def test_tied_months_use_the_plural():
    rows = [("2024-01-10", 2), ("2024-02-10", 2), ("2024-03-10", 1)]
    text = message(rows)
    assert "nei mesi 02-2024, 01-2024" in text          # most recent first
    assert "nel mese 03-2024" in text


def test_tied_streaks_list_every_period():
    rows = [("2024-01-01", 1), ("2024-01-02", 1), ("2024-02-01", 1), ("2024-02-02", 1)]
    assert "(01-02-2024 - 02-02-2024, 01-01-2024 - 02-01-2024)" in message(rows)    # most recent first


def test_name_is_used_as_given():
    assert "*Record per Anna Rossi*" in message(ROWS, name="Anna Rossi")


def test_a_daily_record_tied_on_many_days_does_not_list_them_all():
    rows = [(f"2024-02-{d:02d}", 2) for d in (1, 3, 5, 7, 9, 11)] + [("2024-03-01", 1)]
    daily_line = message(rows).split("\n")[2]
    assert daily_line == "🥵 Hai fatto 💩 2 volte in 6 giorni diversi (gli ultimi: 11-02-2024, 09-02-2024, 07-02-2024)."


def test_a_daily_record_tied_on_a_few_days_lists_them_most_recent_first():
    rows = [("2024-02-01", 2), ("2024-02-05", 2), ("2024-02-09", 2), ("2024-03-01", 1)]
    assert message(rows).split("\n")[2] == "🥵 Hai fatto 💩 2 volte il 09-02-2024, 05-02-2024, 01-02-2024."


def test_tied_months_and_periods_beyond_three_are_summarized():
    # five single-day runs, five different months, all with the same total
    rows = [(f"2023-{m:02d}-10", 2) for m in range(1, 6)] + [("2024-01-10", 1)]
    text = message(rows)
    assert "nei mesi 05-2023, 04-2023, 03-2023 e altri 2." in text
    assert "(10-01-2024, 10-05-2023, 10-04-2023 e altri 3)." in text         # longest run: 6 one-day runs tied
    assert "in una serie di giorni consecutivi (10-05-2023, 10-04-2023, 10-03-2023 e altri 2)." in text
