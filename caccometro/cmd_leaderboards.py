"""/leaderboard_month, /leaderboard_year, /stats_month and /stats_year: totals and statistics of a period, with a chart."""
from datetime import timedelta

from telegram import Update
from telegram.ext import ContextTypes

from caccometro.analysis import FORECAST_WINDOW_DAYS, analyze_users, forecast_totals, period_regularity, period_statistics
from caccometro.arguments import period_from_args
from caccometro.charts import generate_rank_chart, generate_statistics_chart
from caccometro.chat import escape_md, legacy_hint, register_sender, reply_chart
from caccometro.config import now_rome, period_bounds
from caccometro.database import get_all_user_rows, get_daily_counts, get_daily_counts_between, get_first_days, get_rank, get_users
from caccometro.formatting import flame, ranked_line, standing_lines, tie_positions
from caccometro.i18n import tr


async def _leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE, time_period):
    """/leaderboard_month and /leaderboard_year: total 💩 per person in the period, with a chart."""
    sender = register_sender(update)
    if sender is None:
        return
    date = await period_from_args(update, context.args, time_period)
    if date is None:
        return

    month = time_period == 'month'
    rank = get_rank(update.message.chat_id, time_period, date)
    if not rank:
        empty = tr("Nel mese {date} non sono state contate 💩.") if month else tr("Nell'anno {date} non sono state contate 💩.")
        await update.message.reply_text(empty.format(date=date) + legacy_hint(update.message.chat_id))
        return

    # Ongoing period: forecast of the total at its end, next to each count, and the streaks in progress next to the names
    today = now_rome().date()
    start_period, end_period = period_bounds(time_period, date)
    forecast, flames = {}, {}
    if start_period <= today.isoformat() <= end_period:
        rows_by_user, _ = get_all_user_rows(update.message.chat_id)
        flames = {user_id: flame(records.status) for user_id, records in analyze_users(rows_by_user, today).items()}
        recent = get_daily_counts_between(update.message.chat_id,
                                          (today - timedelta(days=FORECAST_WINDOW_DAYS - 1)).isoformat(),
                                          today.isoformat())
        forecast = forecast_totals({user.user_id: total for user, total in rank}, recent, today, end_period)

    message = (tr("🏆 *Classifica del mese {date}*") if month else tr("🏆 *Classifica dell'anno {date}*")).format(date=date) + "\n"
    if forecast:
        message += (tr("_💩 finora → previsione a fine mese_") if month else tr("_💩 finora → previsione a fine anno_")) + "\n"
    names = {user.user_id: escape_md(user.mention) for user, _ in rank}
    message += "\n" + "".join(ranked_line(position, names[user.user_id] + flames.get(user.user_id, ""),
                                         f"{total_count} 💩" + (f" → {forecast[user.user_id]}" if forecast else ""))
                              for position, (user, total_count) in zip(tie_positions([t for _, t in rank]), rank))
    standing = standing_lines([(user.user_id, total) for user, total in rank], names, sender.user_id,
                              lambda n: f"{n} 💩", forecast)
    if standing:
        message += "\n" + "\n".join(standing)

    daily_counts = get_daily_counts(update.message.chat_id, time_period, date)
    await reply_chart(update, generate_rank_chart(rank, daily_counts, time_period, date, forecast), message)


async def _stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE, time_period):
    """/stats_month and /stats_year: mean, median and variance per person, with a chart."""
    sender = register_sender(update)
    if sender is None:
        return
    date = await period_from_args(update, context.args, time_period)
    if date is None:
        return

    chat_id = update.message.chat_id
    daily_counts = get_daily_counts(chat_id, time_period, date)
    statistics = period_statistics(daily_counts, get_users(chat_id), *period_bounds(time_period, date),
                                   now_rome().date())
    month = time_period == 'month'
    if not statistics:
        empty = (tr("🤷 Nessuna statistica disponibile per il mese {date}.") if month
                 else tr("🤷 Nessuna statistica disponibile per l'anno {date}."))
        await update.message.reply_text(empty.format(date=date) + legacy_hint(update.message.chat_id))
        return

    message = (tr("📊 *Statistiche del mese {date}*") if month else tr("📊 *Statistiche dell'anno {date}*")).format(date=date)
    message += "\n" + tr("💩 al giorno: media · mediana · varianza") + "\n\n"
    names = {s['user'].user_id: escape_md(s['user'].mention) for s in statistics}
    message += "".join(ranked_line(position, names[s['user'].user_id],
                                   f"{s['mean']:.2f} · {s['median']:.1f} · {s['variance']:.2f}")
                       for position, s in zip(tie_positions([round(s['mean'], 2) for s in statistics]), statistics))
    standing = standing_lines([(s['user'].user_id, round(s['mean'], 2)) for s in statistics], names, sender.user_id,
                              lambda value: tr("{value} al giorno").format(value=f"{value:.2f}"))
    if sender.user_id in names:
        start, end = period_bounds(time_period, date)
        label = period_regularity(daily_counts, get_first_days(chat_id), sender.user_id, start, end, now_rome().date())
        if label:
            labels = {'molto regolare': tr("molto regolare"), 'abbastanza regolare': tr("abbastanza regolare"),
                      'a sbalzi': tr("a sbalzi")}  # literal tr() calls: the dictionary test finds them
            standing.append(tr("{name}, come vai: {label}.").format(name=names[sender.user_id], label=labels[label]))
    if standing:
        message += "\n" + "\n".join(standing)

    await reply_chart(update, generate_statistics_chart(statistics, daily_counts, time_period, date), message)


async def leaderboard_month_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /leaderboard_month command."""
    await _leaderboard_command(update, context, 'month')


async def leaderboard_year_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /leaderboard_year command."""
    await _leaderboard_command(update, context, 'year')


async def stats_month_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /stats_month command."""
    await _stats_command(update, context, 'month')


async def stats_year_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /stats_year command."""
    await _stats_command(update, context, 'year')
