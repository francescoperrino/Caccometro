# Architecture

How the bot is built: the modules, the path of a message, the database and the translations. For running it, see [CONTRIBUTING.md](../CONTRIBUTING.md) and [deployment.md](deployment.md).

## Modules

```
caccometro/          the bot, as a Python package
  __init__.py        version (__version__)
  __main__.py        python -m caccometro: start in polling mode
  config.py          environment variables, date formats, Italian time
  bot.py             python-telegram-bot Application, logging, send retries, command registration
  webhook.py         Flask app that receives the updates from Telegram (production)
  commands.py        the commands (/leaderboard_month, /records, ...) and the permission checks
  messages.py        counting the 💩 in messages and stickers, conquests from locations
  chat.py            shared helpers on Telegram users and messages
  i18n.py            translations: the Italian sentences are the keys, one dictionary per language
  menus.py           command names and menu descriptions in both languages, menu of a chat
  database.py        SQLite database: schema, migration, queries
  analysis.py        records, streaks, statistics and forecasts (pure functions, no database)
  conquest.py        conquest game: h3 tiles, 15 minute window, ownership and king of the hill (pure functions)
  trophies.py        trophies: 15-day streaks, 💩 of the month and of the year, conquest seasons (pure functions)
  formatting.py      texts of /records, /trophies and the midnight announcement
  announce.py        midnight announcement of the 💩 of the month (scheduled task)
  charts.py          ranking and statistics charts (PNG in memory)
  maps.py            conquest maps over OpenStreetMap tiles (JPEG in memory, tile cache in tile_cache/)
  miniapp.py         Mini App: signed initData, the chats of a user, membership checks, direct link
assets/webapp/       the Mini App page (static HTML and JavaScript, libraries from a CDN)
scripts/set_webhook.py   registers the webhook on Telegram (once)
tools/               service scripts: deploy, database backups, log download and summary, bot version, command menus, README charts and maps
.githooks/           git hooks (pre-commit, commit-msg), enabled with core.hooksPath
.gitattributes       line endings of the .py files (CRLF) and of the hooks (LF)
tests/               pytest tests
.github/workflows/tests.yml   CI: pytest on Python 3.10 on every pull request and every push to main
requirements.txt     bot dependencies (requirements-dev.txt: the test ones too)
wsgi.py              template of the WSGI file for the hosting
assets/              avatar, animation, fonts, medal images of the charts, README charts (screenshots/)
```

`analysis.py`, `trophies.py` and `conquest.py` do not touch the database or Telegram: they receive the counts and return records, statistics and trophies, which makes them the easiest parts to test.

`maps.py` draws the conquest maps: OpenStreetMap raster tiles fetched with `httpx` (User-Agent with the project name and repository, two attempts, 10 seconds for all the tiles of an image), kept 7 days in `tile_cache/` (at most 3000 files, the oldest dropped first), joined with Pillow and drawn with matplotlib in Web Mercator. The zoom around a conquest, the only map that follows the location, shows the real tiles (h3 resolution 6); `/conquests` shows fixed boxes: Lombardy at resolution 5, Italy at resolution 4 and the world at resolution 1, where a hexagon goes to the member holding most tiles inside it, on a tie the latest conqueror. When the tiles cannot be fetched, `maps.render` returns None and the reply goes out as text. `tools/sample_maps.py` draws the README maps (by hand: it needs the network).

## Path of a message

From sending to reply. In production Telegram calls the webhook; locally the bot asks Telegram for the updates (polling). The bot asks only for messages (`allowed_updates`).

```mermaid
flowchart TD
    start["👤 A person writes in the group"] --> mode{"Mode?"}
    mode -->|"polling, locally"| app["python-telegram-bot Application<br/>(bot.py)"]
    mode -->|"webhook, in production"| secret{"Right secret token?<br/>(webhook.py)"}
    secret -->|"no"| refused["Answer 403, update dropped"]
    secret -->|"yes"| seen{"update_id among the last 500?"}
    seen -->|"yes"| skipped["Answer 200, update ignored<br/>(Telegram sent it again)"]
    seen -->|"no"| app
    app --> sender["chat.py: learns the sender's username and name,<br/>picks the language of the chat (i18n.py)"]
    sender --> command{"Is it a command?"}
    command -->|"yes"| commands["commands.py: reads the database,<br/>computes with analysis.py and trophies.py"]
    command -->|"no"| poop{"Does it contain 💩 or 🚽?"}
    poop -->|"no"| location{"Is it a location?"}
    location -->|"no"| silent["No reply"]
    location -->|"yes"| window{"💩 of the sender in the<br/>last 15 minutes, window unused?"}
    window -->|"no"| first["'First the 💩, then the conquest'"]
    window -->|"yes"| conquer["messages.py: conquers the h3 tile,<br/>window used up, king from conquest.py,<br/>zoom map from maps.py (text only if the tiles fail)"]
    poop -->|"yes"| count["messages.py: +1 💩 on the day the message was sent<br/>(message.date, Italian time), opens the conquest window,<br/>reminds to send a location"]
    commands --> output["Text or chart in the chat language<br/>(formatting.py, charts.py)"]
    output --> send["RetryingRequest: send to Telegram,<br/>up to 6 attempts if the connection or the proxy fails"]
    count --> send
    first --> send
    conquer --> send
    send --> reply["👤 The person sees the reply"]
```

- When an update is done, `bot.py` (`LoggingApplication`) writes one line: `Update <id> done: command=<English command, or message, sticker, location> chat=<private|group> ms=<duration> attempts=<requests to Telegram, retries included> outcome=<ok|lost|error>`. `lost` means the network gave up after all the attempts, `error` any other exception. In webhook mode the line covers the whole request, also the start of the Application (its `getMe` after a reload, with the retries), and is written even when the start fails. No names, no text: the nightly summary is built on this line.
- An error inside a command or the counting goes to the error handler of `bot.py` (logged with the traceback and the command): the webhook still answers 200, so Telegram does not send the update again. A 💩 is counted before the reply is sent, so a lost reply never loses the count.
- An error outside the handlers (for example the bot cannot start) makes the webhook answer 500. Telegram sends the update again later. The `update_id` is remembered once the Application has started, so a 💩 is never counted twice, and an update refused because the start failed is processed when it comes again.
- `RetryingRequest` waits 1, 2, 4, 8 and 16 seconds between the attempts. It does not retry timeouts and read errors, because the message may have already arrived.
- The webhook starts and stops the Application at every request: each Flask request has its own event loop.

## Database

One SQLite file per chat, `db/<chat_id>_bot_data.db`:

```mermaid
erDiagram
    users ||--o{ user_count : "does"
    users ||--o{ conquests : "conquers"
    users ||--o| last_poop : "has open"
    users {
        INTEGER user_id PK "Telegram user ID"
        TEXT username "without @, may be missing"
        TEXT display_name "name shown in the messages"
    }
    user_count {
        INTEGER user_id PK "who"
        TEXT date PK "YYYY-MM-DD, Italian time"
        INTEGER count "💩 of that day"
    }
    user_count_legacy {
        TEXT username "history by username"
        TEXT date "YYYY-MM-DD"
        INTEGER count "💩 of that day"
    }
    conquests {
        INTEGER user_id "who"
        INTEGER ts "Unix time of the location message"
        TEXT cell "h3 cell, resolution 7"
        REAL lat "latitude"
        REAL lon "longitude"
    }
    last_poop {
        INTEGER user_id PK "who"
        INTEGER ts "Unix time of the last 💩, deleted when the window is used"
    }
    settings {
        TEXT key PK "language"
        TEXT value "it or en"
    }
```

- `conquests` keeps every conquest: the owner of a tile is its latest row (in the order the bot handled them); holdings and the king are replayed from the history (`conquest.holdings`). Latitude and longitude are kept so the resolution can change later.
- `settings` is created on the first choice made with `/language`: without the table the chat speaks Italian.
- `user_count_legacy` exists only in the chats migrated from the first version and empties as `/link_history` moves the history into `user_count`.
- The schema version is in `PRAGMA user_version` (4 today; 3 added `conquests` and `last_poop`, 4 recalculated every conquest at h3 resolution 7 from its latitude and longitude). The migration starts by itself when the database is opened, inside `BEGIN IMMEDIATE`, after a copy `db/<chat_id>_bot_data.db.v1.bak`.
- When a group becomes a supergroup, the database is renamed `db/<old>_bot_data.db` → `db/<new>_bot_data.db`. If the migration message arrives late and the new database already has counts, the two are merged (same user and same day are added up, conquests appended) and the old file stays as `<old>_bot_data.db.merged`. The migration also starts from the twin message in the old chat, so it gets two chances.

## Translations

`i18n.py` keeps the texts simple: the bot messages are written in Italian inside `tr("...")`, and each other language is a dictionary from the Italian sentence to its translation. The language of the chat is read once per update (`chat.register_sender`) and kept in a context variable, so every `tr()` of that update answers in it; the midnight announcement sets it for each chat. `tests/test_i18n.py` fails when a sentence has no translation.

A new language is one more dictionary in `i18n.py`, plus its name in `LANGUAGES` and its months in `MONTHS`.
