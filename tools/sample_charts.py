"""Draw the charts shown in the README with the bot's own code, from fixed fake data, in Italian and English.

Usage: python tools/sample_charts.py  (the pre-commit hook runs it, so the images follow the code)
Writes assets/screenshots/<chart>_<language>.png. Same code and same library versions give the same bytes.
"""
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from caccometro import charts, i18n  # noqa: E402
from caccometro.analysis import FORECAST_WINDOW_DAYS, forecast_totals, period_statistics  # noqa: E402
from caccometro.database import User  # noqa: E402

OUT = REPO / "assets" / "screenshots"
TODAY = date(2026, 3, 20)   # mid-month, so the ranking shows the forecast
MONTH, START, END = "03-2026", "2026-03-01", "2026-03-31"
PEOPLE = [User(1, "giulia", "Giulia"), User(2, "marco", "Marco"), User(3, None, "Anna"),   # Anna: no username
          User(4, "luca", "Luca"), User(5, "sara", "Sara")]
RATES = [1.6, 1.3, 1.1, 0.8, 0.5]   # mean 💩 per day of each person


def fake_counts():
    """{user_id: {'YYYY-MM-DD': count}} from 30 days before the month to TODAY, the same on every run."""
    rng = random.Random(143)
    first = date.fromisoformat(START) - timedelta(days=FORECAST_WINDOW_DAYS)
    days = [first + timedelta(days=n) for n in range((TODAY - first).days + 1)]
    counts = {}
    for person, rate in zip(PEOPLE, RATES):
        counts[person.user_id] = {d.isoformat(): c for d in days
                                  if (c := sum(rng.random() < rate / 2 for _ in range(2)) + (rng.random() < rate - 1))}
    return counts


def main():
    charts.now_rome = lambda: datetime(TODAY.year, TODAY.month, TODAY.day, 12)  # fixed "today", naive like now_rome
    counts = fake_counts()
    month = {uid: {d: c for d, c in days.items() if d >= START} for uid, days in counts.items()}
    window_start = (TODAY - timedelta(days=FORECAST_WINDOW_DAYS - 1)).isoformat()
    recent = {uid: {d: c for d, c in days.items() if d >= window_start} for uid, days in counts.items()}
    rank = sorted(((p, sum(month[p.user_id].values())) for p in PEOPLE), key=lambda pair: -pair[1])
    forecast = forecast_totals({p.user_id: total for p, total in rank}, recent, TODAY, END)
    statistics = period_statistics(month, {p.user_id: p for p in PEOPLE}, START, END, TODAY)

    OUT.mkdir(exist_ok=True)
    for language in i18n.LANGUAGES:
        i18n.use(language)
        (OUT / f"leaderboard_month_{language}.png").write_bytes(charts.generate_rank_chart(rank, month, "month", MONTH, forecast))
        (OUT / f"stats_month_{language}.png").write_bytes(charts.generate_statistics_chart(statistics, month, "month", MONTH))
    print(f"Charts written to {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
