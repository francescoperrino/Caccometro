"""/conquests: the tiles held by each member, or by one person, with the maps."""
from telegram import Update
from telegram.ext import ContextTypes

from caccometro import maps
from caccometro.arguments import resolve_optional_target
from caccometro.chat import escape_md, register_sender, reply_charts
from caccometro.config import now_rome
from caccometro.conquest import holdings, mention_of, visited
from caccometro.database import get_timed_conquests, get_users
from caccometro.formatting import format_season_line, ranked_line, tie_positions
from caccometro.i18n import tr
from caccometro.trophies import season_of, season_results


async def conquests_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /conquests command: tiles held by each member, king first; or one person (io, @username or a reply)."""
    sender = register_sender(update)
    if sender is None:
        return
    chat_id = update.message.chat_id
    target, error = resolve_optional_target(update, context, sender, tr("/conquiste [@username | io]"))
    if error:
        await update.message.reply_text(error)
        return
    timed = get_timed_conquests(chat_id)
    history = [(user_id, cell) for user_id, _, cell in timed]
    counts, king = holdings(history)
    users = get_users(chat_id)
    if target is not None:
        message = tr("🗺️ {name}: {held} zone tenute, {visited} visitate.").format(
            name=escape_md(target.mention), held=counts.get(target.user_id, 0), visited=visited(history, target.user_id))
        if target.user_id == king:
            message += "\n" + tr("👑 Re della collina!")
    elif not counts:
        message = tr("Nessuna zona conquistata. Dopo la 💩 manda una posizione entro 15 minuti.")
    else:
        ranking = sorted(counts.items(), key=lambda item: (-item[1], item[0] != king))  # on a tie the king first
        message = tr("🗺️ *Conquiste*") + "\n\n" + "".join(
            ranked_line(position, escape_md(mention_of(users, user_id)) + (" 👑" if user_id == king else ""), f"{held} 🚩")
            for position, (user_id, held) in zip(tie_positions([held for _, held in ranking]), ranking))
        season = season_of(now_rome().date())
        if season in (results := season_results(timed)):
            message += "\n" + format_season_line(season, results[season], {u: escape_md(mention_of(users, u)) for u in users})
    # With a person: only that person's tiles, and no maps for someone who never conquered one
    shown = target.user_id if target is not None else None
    drawable = visited(history, target.user_id) if target is not None else counts
    # From the closest view to the widest: the real tiles first (the person's own, or the group's), then the regions
    views = (maps.person_zoom_map if target is not None else maps.group_zoom_map, maps.region_map, maps.country_map,
             maps.world_map)
    maps_drawn = [maps.render(view, history, users, shown) for view in views if drawable]
    await reply_charts(update, maps_drawn, message)
