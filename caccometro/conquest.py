"""Conquest game: after a 💩 a location conquers the h3 hexagon it falls in; most tiles held = king of the hill."""
import h3

RESOLUTION = 7               # hexagons of about 5 km², 2.6 km wide
WINDOW_SECONDS = 15 * 60     # a location conquers only within 15 minutes of the 💩


def cell_of(lat, lon):
    """The tile of a point.

    Args:
        lat (float): latitude in degrees.
        lon (float): longitude in degrees.

    Returns:
        str: the h3 cell of the point at RESOLUTION.
    """
    return h3.latlng_to_cell(lat, lon, RESOLUTION)


def holdings(history):
    """Replay the conquests in order and tell who holds what.

    A tile belongs to its last conqueror. The king holds the most tiles; on a tie the current king keeps the crown.

    Args:
        history (list): [(user_id, cell)] in the order the conquests were made.

    Returns:
        (counts, king): {user_id: tiles held} without the users who lost all of them, and the king's user ID (None without conquests).
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
    """Count the different tiles a user has ever conquered.

    Args:
        history (list): [(user_id, cell)] in the order the conquests were made.
        user_id (int): the user.

    Returns:
        int: how many different cells appear with that user.
    """
    return len({cell for owner, cell in history if owner == user_id})


def mention_of(users, user_id):
    """Name for messages of a user of the chat.

    Args:
        users (dict): {user_id: User} of the chat.
        user_id (int): the user.

    Returns:
        str: the mention of the user, or the user ID when the bot does not know the user.
    """
    return users[user_id].mention if user_id in users else str(user_id)
