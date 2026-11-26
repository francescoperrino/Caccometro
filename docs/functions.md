# Functions and classes

Every public function and class of the `caccometro` package, one table per module: the static view of the code below the modules. Written by `tools/write_functions.py` from the code: do not edit by hand. "What it does" is the first paragraph of the docstring; "Used by" names the other modules of the package that import it or call it as `module.name`, or the decorator through which a framework calls it. For the modules and how they depend on each other, see [architecture.md](architecture.md#dependencies-between-modules).

## analysis.py

Records and current status of the users' 💩 counts.

| Function or class | What it does | Used by |
| --- | --- | --- |
| `class Period` | A range of days, both ends included. | `formatting`, `trophies` |
| `class Record` | The best value of a metric and everything that reached it (ties are all kept). | only its own module |
| `class Status` | Where the user stands right now, metric by metric. | only its own module |
| `class UserRecords` | Personal records of one user, plus the current status they are compared with. | `formatting` |
| `class Run` | A run of consecutive days with 💩. | only its own module |
| `parse_counts(rows)` | Turn the stored rows into a dictionary by date, ignoring the days without 💩. | `trophies` |
| `consecutive_runs(days_sorted, counts)` | Group the days with 💩 into runs of consecutive days. | `trophies` |
| `analyze_user(rows, today)` | Records and current status of one user. | `cmd_records` |
| `class Holder` | Someone who holds (or shares) a group record. | only its own module |
| `class Leaders` | The best value of a metric in the group and everyone who reached it. | `formatting` |
| `class GroupBoard` | Records of the whole group: who holds each record of all times and who leads right now. | `formatting` |
| `analyze_users(users_rows, today)` | The records of every user with at least one 💩. | `cmd_leaderboards`, `cmd_records`, `miniapp` |
| `analyze_group(users_rows, today)` | Who holds each record of the group, and who leads right now. | `cmd_records`, `miniapp` |
| `forecast_totals(totals, recent_counts, today, end_period)` | Expected 💩 of every user at the end of the period. | `cmd_leaderboards`, `miniapp` |
| `period_statistics(daily_counts, users, start_period, end_period, today)` | Mean, median and variance of the daily 💩 of every user in a period. | `cmd_leaderboards`, `miniapp` |
| `period_regularity(daily, first_days, user_id, start, end, today)` | The regularity of one person in a period, on whole days only: from their first 💩 (not before they joined) to yesterday. | `cmd_leaderboards`, `miniapp` |
| `record_places(user_id, people)` | The place of each record of one person among the records of everybody. | `cmd_records` |
| `class Recap` | One person's month or year in a few facts, for the recap of the Mini App. | only its own module |
| `recap(daily, user_id, year, month, first_days)` | The recap of a person for a month, or for a whole year. | `miniapp` |

## announce.py

Midnight announcement of the 💩 of the month (on January 1st also of the year, on a quarter's first day the season) in every chat.

| Function or class | What it does | Used by |
| --- | --- | --- |
| `main(argv)` | Entry point of the scheduled task. | only its own module |

## arguments.py

Arguments of the commands: periods, dates, the person a command refers to.

| Function or class | What it does | Used by |
| --- | --- | --- |
| `invalid_format(usage)` | The reply to arguments that do not fit the command. | `cmd_settings` |
| `replied_person(update)` | The Telegram user of the message being replied to, or None when the reply is not to a person. | `cmd_settings` |
| `resolve_optional_target(update, context, sender, usage)` | Target of /records and /trophies: io, @username or a reply. Returns (target, error); no target and no error means the group. | `cmd_conquests`, `cmd_records` |
| `async target_from_args(update, args, sender, usage, counts)` | The person of a command (see _resolve_target) and the arguments after it, whose number must be in `counts`. | `cmd_counts` |
| `async date_from_arg(update, arg)` | _parse_date_arg, or None after telling the user why the date is not valid. | `cmd_counts` |
| `async period_from_args(update, args, time_period)` | The period asked for ('MM-YYYY' or 'YYYY'), the current one without arguments. | `cmd_leaderboards` |

## bot.py

The Telegram application: logging, requests with retries, error handler and handler registration.

| Function or class | What it does | Used by |
| --- | --- | --- |
| `outcome_of(error)` | 'lost' when the network gave up (the reply did not arrive), 'error' for any other exception. | `webhook` |
| `update_log()` | Time what runs inside and count its requests to Telegram; then log the line of info['update'], when set. | `webhook` |
| `main()` | Run the bot in polling mode (local development); in webhook mode the web server imports `app` (see wsgi.py). | `__main__` |

## charts.py

Charts of /leaderboard_* and /stats_*: one shared style, PNG bytes in memory.

| Function or class | What it does | Used by |
| --- | --- | --- |
| `png_bytes(fig, credit)` | Render a figure to PNG in memory and close it. | `maps` |
| `chart_label(name)` | Make a user name safe for matplotlib text ('$' would start a math expression). | `maps` |
| `short_name(name)` | The name cut to NAME_MAX characters, with an ellipsis when cut. | `maps` |
| `add_cards(fig, axes)` | Put a rounded card behind every axes, its labels and its title included. | `maps` |
| `sorted_by_name(names)` | Sort users by name, ignoring the case. | `maps` |
| `generate_rank_chart(rank, daily_counts, time_period, date, forecast)` | Ranking chart: a table of the counts, the medals and the cumulative counts of every user below it. | `cmd_leaderboards` |
| `generate_statistics_chart(statistics, daily_counts, time_period, date)` | Statistics chart: a normal curve per user and a box plot of the daily counts below it. | `cmd_leaderboards` |
| `generate_recap_image(recap, name)` | The picture of the recap to share: 1080x1350 (4:5, what Telegram shows whole). | `miniapp` |

## chat.py

Helpers shared by the commands and the message handler: users, replies, permissions.

| Function or class | What it does | Used by |
| --- | --- | --- |
| `register_user(chat_id, tg_user)` | Store the current username/name of a Telegram user and return it as a model.User. | `arguments`, `cmd_settings` |
| `register_sender(update)` | Record the sender of the message in the users table and return it; the replies follow the language of the chat. | `cmd_conquests`, `cmd_counts`, `cmd_leaderboards`, `cmd_records`, `cmd_settings`, `messages` |
| `where(update)` | 'PVT - &lt;chat name>' or 'GROUP - &lt;chat name>', for the log lines. | `cmd_counts`, `cmd_settings` |
| `escape_md(name)` | Escape a name for Telegram (legacy) Markdown. | `announce`, `cmd_conquests`, `cmd_leaderboards`, `cmd_records`, `messages` |
| `async reply_chart(update, chart, message)` | Send a chart with the message as its caption: one request instead of two, when it fits. | `cmd_leaderboards` |
| `async reply_charts(update, charts, message)` | Send the charts that could be drawn (None ones are skipped) with the message: an album when there are several, the text alone when there are none. | `cmd_conquests`, `messages` |
| `async is_chat_admin(update, context)` | True if the sender is an administrator (or the owner) of the chat; always True in private chats. | `cmd_counts`, `cmd_settings` |
| `legacy_hint(chat_id)` | Suffix for 'no data' replies when old username-based history is still waiting to be linked. | `cmd_leaderboards`, `cmd_records` |

## cmd_conquests.py

/conquests: the tiles held by each member, or by one person, with the maps.

| Function or class | What it does | Used by |
| --- | --- | --- |
| `async conquests_command(update, context)` | Handler for the /conquests command: tiles held by each member, king first; or one person (io, @username or a reply). | `bot` |

## cmd_counts.py

/add_poop, /remove_poop, /day_count and /last_poop: the counts of one person.

| Function or class | What it does | Used by |
| --- | --- | --- |
| `async add_poop_command(update, context)` | Handler for the /add_poop command. | `bot` |
| `async remove_poop_command(update, context)` | Handler for the /remove_poop command. | `bot` |
| `async day_count_command(update, context)` | Handler for the /day_count command. | `bot` |
| `async last_poop_command(update, context)` | Handler for the /last_poop command. | `bot` |

## cmd_leaderboards.py

/leaderboard_month, /leaderboard_year, /stats_month and /stats_year: totals and statistics of a period, with a chart.

| Function or class | What it does | Used by |
| --- | --- | --- |
| `async leaderboard_month_command(update, context)` | Handler for the /leaderboard_month command. | `bot` |
| `async leaderboard_year_command(update, context)` | Handler for the /leaderboard_year command. | `bot` |
| `async stats_month_command(update, context)` | Handler for the /stats_month command. | `bot` |
| `async stats_year_command(update, context)` | Handler for the /stats_year command. | `bot` |

## cmd_records.py

/records and /trophies: of the group, or of one person (io, @username or a reply).

| Function or class | What it does | Used by |
| --- | --- | --- |
| `async records_command(update, context)` | Handler for the /records command. | `bot` |
| `async trophies_command(update, context)` | Handler for the /trophies command: the trophies of the group, or of one person (io, @username or a reply). | `bot` |

## cmd_settings.py

/start, /app, /language and /link_history: the bot, its Mini App and the settings of the chat.

| Function or class | What it does | Used by |
| --- | --- | --- |
| `async start_command(update, context)` | Handler for the /start command. | `bot` |
| `async app_command(update, context)` | Handler for the /app command: a button that opens the Mini App on this chat. | `bot` |
| `async language_command(update, context)` | Handler for the /language command: show the language of the chat or, for the admins, change it (/language en). | `bot` |
| `async link_history_command(update, context)` | Handler for the /link_history command: link the old username-based history to Telegram users. | `bot` |

## config.py

Configuration: environment variables, date formats and the Rome time zone.

| Function or class | What it does | Used by |
| --- | --- | --- |
| `now_rome()` | Current date and time in Rome, without tzinfo (comparable with the naive datetimes used in the code). | `announce`, `arguments`, `charts`, `cmd_conquests`, `cmd_counts`, `cmd_leaderboards`, `cmd_records`, `database`, `messages`, `miniapp`, `webhook` |
| `period_bounds(time_period, date)` | Start and end date of a month or a year. | `cmd_leaderboards`, `database`, `miniapp` |

## conquest.py

Conquest game: after a 💩 a location conquers the h3 hexagon it falls in; most tiles held = king of the hill.

| Function or class | What it does | Used by |
| --- | --- | --- |
| `cell_of(lat, lon)` | The tile of a point. | `messages` |
| `holdings(history)` | Replay the conquests in order and tell who holds what. | `cmd_conquests`, `maps`, `messages`, `miniapp`, `trophies` |
| `visited(history, user_id)` | Count the different tiles a user has ever conquered. | `cmd_conquests` |
| `mention_of(users, user_id)` | Name for messages of a user of the chat. | `cmd_conquests`, `maps`, `messages`, `miniapp` |

## database.py

SQLite storage, one database file per chat: schema, migration from the legacy schema, counts, users and conquests.

| Function or class | What it does | Used by |
| --- | --- | --- |
| `migrate_chat(old_chat_id, new_chat_id)` | Move the database of a group that became a supergroup to its new chat ID. | `messages` |
| `init_database(chat_id)` | Initialize (or migrate) the SQLite database of a chat if needed. | `cmd_settings` |
| `get_language(chat_id)` | Language chosen for the chat with /language. | `announce`, `chat`, `messages`, `webhook` |
| `set_language(chat_id, language)` | Store the language of the chat (the settings table is created by the first choice). | `cmd_settings` |
| `get_users(chat_id)` | Every user known to the chat. | `cmd_conquests`, `cmd_leaderboards`, `messages`, `miniapp` |
| `upsert_user(chat_id, user_id, username, display_name)` | Record the current username and display name of a user (writes only when something changed). | `chat` |
| `find_user_by_username(chat_id, username)` | Find a known user by username, ignoring the case. | `arguments`, `cmd_settings` |
| `get_count(user_id, date, chat_id)` | Count of 💩 of a user on a day. | `cmd_counts` |
| `add_count(user_id, date, delta, chat_id)` | Add a change to the count of a user on a day, in a single transaction. | `cmd_counts`, `messages` |
| `get_daily_counts(chat_id, time_period, date)` | Counts of every user for every day of a month or a year. | `cmd_leaderboards` |
| `get_daily_counts_between(chat_id, start_period, end_period)` | Like get_daily_counts, for any range of days. | `cmd_leaderboards`, `miniapp` |
| `get_rank(chat_id, time_period, date)` | Total 💩 of every user in a month or a year, best first. | `cmd_leaderboards`, `miniapp` |
| `get_record(user_id, chat_id)` | The counts of one user. | `cmd_records`, `messages` |
| `get_all_user_rows(chat_id)` | The counts of every user of the chat, read with a single query. | `announce`, `cmd_leaderboards`, `cmd_records`, `webhook` |
| `get_days_since_last_poop(user_id, chat_id)` | Days since the last 💩 of a user. | `cmd_counts` |
| `open_conquest_window(user_id, ts, chat_id)` | Remember the time of a 💩 of the user: it opens the conquest window. | `messages` |
| `conquer(chat_id, user_id, ts, lat, lon, cell, window)` | Conquer a tile if the user sent a 💩 shortly before; the window is then used up. | `messages` |
| `get_timed_conquests(chat_id)` | Every conquest of the chat, with its time, for the seasons. | `announce`, `cmd_conquests`, `cmd_records`, `webhook` |
| `list_legacy_users(chat_id)` | The legacy usernames not yet linked to a user. | `chat`, `cmd_settings` |
| `count_legacy_orphans(chat_id)` | Count the legacy rows without a username: they cannot be linked to anybody by name. | `cmd_settings` |
| `link_legacy_username(chat_id, legacy_username, user_id)` | Move the legacy history of a username to a user ID, ignoring the case. | `cmd_settings` |
| `link_legacy_by_username(chat_id)` | Link every legacy username that matches the username of a known user. | `cmd_settings` |
| `get_first_days(chat_id)` | The first day with 💩 of every user of the chat. | `cmd_leaderboards`, `miniapp` |

## formatting.py

Text of the bot messages built from the results of analysis.py.

| Function or class | What it does | Used by |
| --- | --- | --- |
| `tie_positions(values)` | The place of each value of a list sorted best first: equal values share the place (1, 2, 2, 4). | `cmd_conquests`, `cmd_leaderboards` |
| `flame(status)` | The streak in progress, to write after a name, from 3 days on. | `cmd_leaderboards` |
| `standing_lines(rows, names, sender_id, unit, forecast)` | Who leads and where the sender is, as sentences for the whole chat (the Mini App's "answer", in the third person). | `cmd_leaderboards` |
| `format_user_record(name, records, places)` | The /records message of one user: every record followed by where the user stands right now. | `cmd_records` |
| `format_group_record(board, names)` | The /records message of the whole group: who holds each record, and who leads right now. | `cmd_records` |
| `format_season_line(season, result, names)` | One line of /conquests: who leads the current season so far. | `cmd_conquests` |
| `format_streak_trophy(days)` | The line added to the reply to the 💩 that completes a multiple of STREAK_STEP consecutive days. | `messages` |
| `format_group_trophies(trophies, names)` | The /trophies message of the whole group: how many trophies of each kind every winner has. | `cmd_records` |
| `format_user_trophies(name, trophies, current_streak)` | The /trophies message of one user: every trophy, then how far the next streak trophy is. | `cmd_records` |
| `format_new_period(today, month_winners, year_winners, names, season)` | The midnight message on the first day of a month: the 💩 of the month just ended and, on January 1st, of the year. | `announce` |
| `poop_sentence(name, hour, count)` | A random sentence for a 💩. | `messages` |
| `last_poop_sentence(name, days)` | A random sentence for /last_poop. | `cmd_counts` |
| `day_count_sentence(name, day, count)` | A random sentence for /day_count. | `cmd_counts` |
| `change_count_sentence(name, date, count, delta)` | A random sentence for /add_poop and /remove_poop. | `cmd_counts` |
| `ranked_line(position, name, value)` | One line of a ranking: a medal and the name in bold for the first three. | `cmd_conquests`, `cmd_leaderboards` |

## i18n.py

Translations of the bot messages: the Italian sentences are the keys, one dictionary per other language.

| Function or class | What it does | Used by |
| --- | --- | --- |
| `use(language)` | Answer in a language from now on, in the current update (or in the current chat of the announcement). | `announce`, `chat`, `cmd_settings`, `webhook` |
| `current()` | The language in use. | `charts`, `cmd_settings` |
| `tr(text)` | Translate an Italian sentence into the language in use. | `announce`, `arguments`, `charts`, `chat`, `cmd_conquests`, `cmd_counts`, `cmd_leaderboards`, `cmd_records`, `cmd_settings`, `formatting`, `maps`, `messages` |
| `month_name(number)` | Name of a month in the language in use. | `charts`, `formatting` |

## maps.py

Conquest maps: the tiles of a chat drawn over OpenStreetMap raster tiles, JPEG bytes in memory.

| Function or class | What it does | Used by |
| --- | --- | --- |
| `owners(history)` | The owner of every tile: a tile belongs to its last conqueror. | `miniapp` |
| `grouped(tiles, res)` | Give each larger hexagon to the member who holds most tiles inside it, on a tie the latest. | `miniapp` |
| `zoom_map(history, users, title)` | Reply to a conquest: the real tiles around the tile just conquered, the last of the history. | `messages` |
| `group_zoom_map(history, users, user_id)` | /conquests: the real tiles of every member around the latest conquest of the group. | `cmd_conquests` |
| `world_map(history, users, user_id)` | /conquests: the whole world. | `cmd_conquests` |
| `region_map(history, users, user_id)` | /conquests: Lombardy. | `cmd_conquests` |
| `country_map(history, users, user_id)` | /conquests: Italy. | `cmd_conquests` |
| `person_zoom_map(history, users, user_id)` | /conquests of one person: the real tiles around the member's latest conquest, held ones full, lost ones dashed. | `cmd_conquests` |
| `render(builder, *args)` | Draw a map, or tell that it cannot be drawn. | `cmd_conquests`, `messages` |

## menus.py

Command names and menu descriptions in Italian and English; the menu of a chat follows its language.

| Function or class | What it does | Used by |
| --- | --- | --- |
| `menu(language, admins)` | The menu of the commands in a language. | only its own module |
| `async set_chat_menu(bot, chat_id, language, group)` | Show the menu of one chat in a language, whatever the app language of who opens it. | `cmd_settings`, `messages` |

## messages.py

Handler of plain messages: counts the 💩 and 🚽 sent as text or sticker.

| Function or class | What it does | Used by |
| --- | --- | --- |
| `async handle_migration(update, context)` | A basic group became a supergroup: Telegram gave it a new chat ID, so the database follows it. | `bot` |
| `async handle_message(update, context)` | Handler for processing messages. | `bot` |

## miniapp.py

Mini App (#79): who opened it (signed initData), which chats they may see, and the direct link from the groups.

| Function or class | What it does | Used by |
| --- | --- | --- |
| `direct_link(bot_username, chat_id, view)` | Link that opens the Mini App already on a chat, and with `view` ('recap' or 'year', #195) on the recap of the month or of the year; plain URL buttons can carry it, in groups too (web_app buttons only work in private chats). | `announce`, `cmd_settings` |
| `user_of(init_data, token, now)` | The Telegram user (dict) who opened the Mini App, or None when initData is not signed by Telegram or too old. | `webhook` |
| `known_chats()` | IDs of every chat that has a database: the API never opens (and so never creates) the database of another one. | `webhook` |
| `async is_member(bot, chat_id, user_id)` | Whether the user is still in the chat; the private chat with the bot is always theirs. | `webhook` |
| `conquest_data(timed, users)` | The conquest map of a chat for the page (#189). timed: [(user_id, ts, cell)] in order; users: {user_id: User}. | `webhook` |
| `records_data(rows_by_user, today, timed)` | Records of the group and of each person, and everyone's trophies (#190): what /records and /trophies show. | `webhook` |
| `period_data(chat_id, time_period, period, today)` | Leaderboard with the forecast and statistics of a month ('MM-YYYY') or year ('YYYY'), like the commands (#190). | `webhook` |
| `recap_data(chat_id, user_id, today, yearly)` | The recap (#195) of one person: of the month just ended from the 1st to the RECAP_DAYS-th of a month, or with `yearly` of the year just ended from the 1st to the YEAR_RECAP_DAYS-th of January; None on other days or without 💩. | `webhook` |
| `recaps(chat_id, user_id, today)` | The recaps to show today, the year first: none, one, or in early January the year and December. | `webhook` |
| `recap_link(chat_id, user_id, yearly, token, now)` | The name of a short-lived link to a recap picture (#217), for the download of Telegram, which sends no initData: "chat.user.yearly.expiry.signature", signed with a key drawn from the bot token, so nobody can forge one. | `webhook` |
| `recap_of_link(name, token, now)` | (chat_id, user_id, yearly) of a link made by recap_link, or None when it is forged or expired. | `webhook` |
| `recap_image(chat_id, user_id, recap)` | The recap as the PNG to share, with the names the chat knows. | `webhook` |

## model.py

Data types shared by every layer: the storage returns them, the rules and the replies read them.

| Function or class | What it does | Used by |
| --- | --- | --- |
| `class User` | A Telegram user known to a chat. | `analysis`, `chat`, `database` |
| `User.name` | Plain name for charts and tables: the username if any, otherwise the display name. |  |
| `User.mention` | Name for messages: '@username' if any, otherwise the display name. |  |

## trophies.py

Trophies: one every STREAK_STEP consecutive days with 💩, the 💩 of the month and of the year, the seasons of the conquest game.

| Function or class | What it does | Used by |
| --- | --- | --- |
| `class Winners` | Who made the most 💩 in a month or a year (ties: all of them) and how many. | only its own module |
| `class UserTrophies` | The trophies of one user, in chronological order. | only its own module |
| `UserTrophies.streak_trophies` | One trophy for every STREAK_STEP days of each run: a run of 47 days is worth 3. |  |
| `new_streak_trophy(rows, today)` | The length of the run that earns a trophy today, if any. | `messages` |
| `monthly_winners(users_rows, today)` | Who won every completed month. | `announce` |
| `yearly_winners(users_rows, today)` | Who won every completed year. | `announce` |
| `class SeasonResult` | Titles of a season (a calendar quarter in Italian time) of the conquest game. | only its own module |
| `season_of(day)` | The season of a day. | `announce`, `cmd_conquests`, `miniapp` |
| `season_results(history)` | The titles of every season with a conquest. | `announce`, `cmd_conquests`, `miniapp` |
| `trophies_by_user(users_rows, today, history)` | The trophies of every user who has at least one. | `cmd_records`, `miniapp` |

## webhook.py

Webhook: the Flask app the web server runs; Telegram posts every update to /webhook.

| Function or class | What it does | Used by |
| --- | --- | --- |
| `async webhook()` | This function receives the update from Telegram and passes it to the library. | `@app.route('/webhook', methods=['POST'])` |
| `mini_app()` | The Mini App page (#79): static, it asks /api for the data with the initData Telegram gives it. | `@app.route('/app')` |
| `story_background(name)` | The drawn background of a month or of the year, behind the screens of the recap in the Mini App (#195). | `@app.route('/app/recap/<name>.jpg')` |
| `async api_chat()` | Data of one chat, only for its members (left or kicked users get 403). | `@app.route('/api/chat')` |
| `async api_period()` | Leaderboard and statistics of ?year= (and ?month=) in one chat, only for its members. | `@app.route('/api/period')` |
| `async api_recap()` | The picture of the recap (#195) of the signed user: GET gives it to the Mini App, which shows it on its last screen; POST sends the same picture in the chat (the group, or the private chat with the bot), and POST with to=link gives a short-lived link to it for the download of Telegram (#217). | `@app.route('/api/recap', methods=['GET', 'POST'])` |
| `recap_download(name)` | The recap picture behind a link of recap_link (#217): Telegram downloads it to the phone, without initData. | `@app.route('/api/recap/<name>.png')` |
| `index()` | Welcome page, useful for testing if the web app works; the deploy reads the version here. | `@app.route('/')` |
