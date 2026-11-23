"""Conquest game (#128): after a 💩 a location conquers the h3 hexagon it falls in; most tiles held = king of the hill."""
import h3

RESOLUTION = 7               # hexagons of about 5 km², 2.6 km wide
WINDOW_SECONDS = 15 * 60     # a location conquers only within 15 minutes of the 💩


def cell_of(lat, lon):
    """The tile (h3 cell at RESOLUTION) of a point."""
    return h3.latlng_to_cell(lat, lon, RESOLUTION)


def holdings(history):
    """Replay the conquests [(user_id, cell)] in order: ({user_id: tiles held}, king).

    A tile belongs to its last conqueror. The king holds the most tiles; on a tie the current king keeps the crown.
    """
    owners, counts, king = {}, {}, None
    for user_id, cell in history:
        previous = owners.get(cell)
        if previous == user_id:
            continue
        if previous is not None:
            counts[previous] -= 1
        owners[cell] = user_id
        counts[user_id] = counts.get(user_id, 0) + 1
        best = max(counts.values())
        if king is None or counts[king] < best:
            king = user_id if counts[user_id] == best else max(counts, key=counts.get)
    return {user_id: n for user_id, n in counts.items() if n}, king


def visited(history, user_id):
    """Number of different tiles the user has ever conquered."""
    return len({cell for owner, cell in history if owner == user_id})


def mention_of(users, user_id):
    """Name for messages of a user of the chat; the user ID when the bot does not know it."""
    return users[user_id].mention if user_id in users else str(user_id)
