<p align="center">
  <img src="assets/demo.gif" alt="Caccometro: the robot strains on the toilet, sends a 💩 from the phone, a podium slides in with a gold medal and it gives a thumbs up" width="400">
</p>

<h1 align="center">Caccometro</h1>

<p align="center"><b>Who poops the most? The Telegram bot that counts the 💩 of your group.</b></p>

<p align="center"><b>English</b> · <a href="README.it.md">Italiano</a></p>

<p align="center">
  <a href="https://github.com/francescoperrino/Caccometro/actions/workflows/tests.yml"><img src="https://github.com/francescoperrino/Caccometro/actions/workflows/tests.yml/badge.svg" alt="Tests"></a>
  <a href="https://github.com/francescoperrino/Caccometro/releases/latest"><img src="https://img.shields.io/github/v/release/francescoperrino/Caccometro" alt="Latest release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/francescoperrino/Caccometro" alt="License: MIT"></a>
</p>

<p align="center">
  <a href="https://t.me/caccometro_bot?startgroup=true"><img src="https://img.shields.io/badge/Add_to_your_group-26A5E4?style=for-the-badge&logo=telegram&logoColor=white" alt="Add Caccometro to your Telegram group"></a>
</p>

Done your duty? Send 💩 in the group. Caccometro keeps the count for everyone and turns it into a game among friends:

- 🏆 **Leaderboards** of the month and of the year, with a forecast for the end of the month
- 📊 **Statistics and charts**: averages, the typical day, who is the most regular
- 🏅 **Records and trophies**: streaks, the 💩 of the month and of the year
- 🚩 **Conquest game**: send a location after the 💩 and the hexagon on the map is yours, season after season
- 📱 **Mini App**: map, leaderboards, statistics and trophies in one place, opened from the chat; in the first week of a month, the recap of your month (in January, of your year) to share
- 🌍 Italian and English, open source

## 📱 Mini App

| Map | Leaderboard | Statistics | Trophies |
| :---: | :---: | :---: | :---: |
| <img src="assets/screenshots/miniapp_map_en.jpg" alt="Mini App map: the hexagons conquered around Milan in the colours of their owners" width="190"> | <img src="assets/screenshots/miniapp_leaderboard_en.jpg" alt="Mini App leaderboard of the month: who leads, a podium with medals and forecasts, the list of the others" width="190"> | <img src="assets/screenshots/miniapp_stats_en.jpg" alt="Mini App statistics: your numbers of the month and how regular you are" width="190"> | <img src="assets/screenshots/miniapp_trophies_en.jpg" alt="Mini App trophies: the trophies in progress and the board of the group" width="190"> |

---

- [How to use it](#-how-to-use-it)
- [Commands](#-commands)
- [Charts and maps](#-charts-and-maps)
- [Rules](#-rules)
- [Privacy](#-privacy)
- [Documentation](#-documentation)

## 💬 How to use it

<p align="center"><img src="docs/images/how_the_bot_works.svg" alt="How Caccometro works: you send 💩, the bot counts it, you conquer a hexagon with a location, you compare leaderboards and statistics, at midnight on the 1st the 💩 of the month is announced" width="600"></p>

1. Add the bot to the group and send `/start`.
2. When you have done your duty, send a message with 💩 or 🚽 (also as a sticker): the bot replies with a funny sentence (it changes with the time of day and with the count of the day), today's count and a reminder to send your location.
3. Within 15 minutes of the 💩, send a location (📎 → Location) to conquer its tile: see the [conquest rules](#-rules).
4. Use the commands below for leaderboards, statistics and records, or `/app` for the Mini App.
5. The bot speaks Italian; for English an admin sends `/language en` (in a private chat anybody can).

---

## 📚 Commands

| Command                                        | What it does |
| :--------------------------------------------- | :----------- |
| `/start`                                       | Version of the bot and the main commands. |
| `/leaderboard_month [MM-YYYY]`                 | Leaderboard of the month, with a chart and the forecast. |
| `/leaderboard_year [YYYY]`                     | Leaderboard of the year, with a chart and the forecast. |
| `/stats_month [MM-YYYY]`                       | Mean, median and variance of the 💩 per day in the month. |
| `/stats_year [YYYY]`                           | The same statistics over the year. |
| `/records [me \| @username]`                   | Records of the group or of one person. |
| `/trophies [me \| @username]`                  | Trophies of the group or of one person. |
| `/conquests [me \| @username]`                 | Tiles held, the king of the hill and the maps. |
| `/app`                                         | Opens the Mini App on this chat. |
| `/day_count [@username] [DD-MM-YYYY]`          | 💩 of a person on a day. |
| `/last_poop [@username]`                       | Days since the last 💩. |
| `/add_poop [@username] DD-MM-YYYY`             | Adds 1 💩 on a day. |
| `/remove_poop [@username] DD-MM-YYYY`          | Removes 1 💩 on a day. |
| `/link_history [auto \| historical username]`  | Admins only: links the old history to the people. |
| `/language [it \| en]`                         | Language of the chat. |

Every command also has an Italian name (`/classifica_mese`, `/aggiungi_cacca`, ...), valid in every chat whatever its language: see the [menu table](docs/deployment.md#command-menus). Everything the bot can answer, in English and Italian, is in [docs/replies.md](docs/replies.md).

<details>
<summary><b>Each command in detail</b></summary>

- **`/start`** prepares the database of the chat, shows the version of the bot and the main commands.
- **`/leaderboard_month [MM-YYYY]`**: the current month if the date is missing (also `march 2026`), with a chart of the day-by-day trend. For the current month, next to each count, the forecast for the end of the month. Under the list: who leads, where you stand and, with 🔥 next to the names, the streaks in progress.
- **`/leaderboard_year [YYYY]`**: the current year if missing (also `26`), with a chart and, for the current year, the forecast for the end of the year.
- **`/stats_month [MM-YYYY]`**: mean, median and variance of the 💩 per day of each person in the month, with a chart of the distributions. Under the list: who leads and how regular you are.
- **`/records [me | @username]`**: without arguments the **group records** (who holds each record and who leads right now). With `me` (or `io`) your own records, with `@username` (or replying to a message) those of another person, each with its **current state** and its place in the group ("#2 of 5").
- **`/trophies [me | @username]`**: without arguments the **trophy board** of the group; with `me`, `@username` or a reply, the trophies of one person, with how many days are left to the next streak trophy.
- **`/conquests [me | @username]`**: without arguments the **tiles held** by each person, the king of the hill 👑 first; with `me`, `@username` or a reply, the tiles held and visited by one person, and maps of that person only: Lombardy, Italy and the world, lighter where tiles were lost, and a fourth map with the real tiles around the latest conquest (lost ones dashed).
- **`/app`** sends a button that opens the **Mini App** on this chat. In the private chat with the bot, the menu button opens it on that chat; only members of a group see its data. From the 1st to the 7th of a month the leaderboard opens **Your month**: your month just ended in a few screens (total, best day, longest streak, place, compared with the month before), and Share sends you the picture in private to forward or save. From the 1st to the 14th of January there is **Your year** too, with the year just ended. The midnight announcement of a new month has a button that opens it.
- **`/day_count [@username] [DD-MM-YYYY]`**: today if the date is missing (also `yesterday`).
- **`/add_poop` and `/remove_poop [@username] DD-MM-YYYY`** add or remove 1 💩 (down to 0) on a past day or today (also `today`, `yesterday`). On someone else's count: admins only.
- **`/link_history`** without arguments shows what is left to link: see [Old history and supergroups](#-rules).
- **`/language [it | en]`** without arguments shows the language of the chat; with `it` or `en` it changes it (in groups admins only). It applies to the replies, the charts, the midnight announcement and the command menu of the chat.

In the commands with `[@username]` the person can also be chosen by **replying to one of their messages** (useful for people without a username). An `@username` works only for people who have already written at least one message in the group. In groups with topics, replying to the message that created the topic does not count as replying to a person.

</details>

<details>
<summary><b>Dates and months</b></summary>

Dates can be written in several ways: `-`, `/` and `.` are the same, leading zeros are optional and the year can have two digits (`26` = 2026, also for `/leaderboard_year` and `/stats_year`). So `5/3/26`, `05.03.2026` and `5-3-2026` are the same day (day first, then month), and `3/26`, `03.2026` and `03-2026` the same month. You can also use `today` and `yesterday` (or `oggi` and `ieri`), a day without a year (`5/3`, the current year) and the name of the month in English or Italian (`march 2026`, `marzo 26`, `march` for the current year), whatever the language of the chat. The replies always show `DD-MM-YYYY` and `MM-YYYY`. Only real dates between 1970 and today are valid (months and years up to 2100).

Dates follow Italian time (`Europe/Rome`). A 💩 counts on the day the message was **sent**, even if the bot handles it later.

</details>

---

## 📈 Charts and maps

The leaderboards and the statistics come with a chart, and every conquest with a map. These are drawn by the bot's own code from sample data, and are drawn again whenever the code changes (`tools/sample_charts.py`, `tools/sample_maps.py`).

| Leaderboard of the month, with the forecast | Statistics of the month |
| :---: | :---: |
| <img src="assets/screenshots/leaderboard_month_en.png" alt="Leaderboard chart: table of the daily counts with medals, and the running total of each person with a dotted forecast to the end of the month" width="400"> | <img src="assets/screenshots/stats_month_en.png" alt="Statistics chart: a bell curve per person and a box plot of the daily 💩" width="400"> |

The same charts in an Italian chat: [leaderboard](assets/screenshots/leaderboard_month_it.png), [statistics](assets/screenshots/stats_month_it.png).

| Conquest | `/conquests`: Lombardy |
| :---: | :---: |
| <img src="assets/screenshots/conquest_zoom_en.jpg" alt="Map of Milan with the hexagonal tiles in the colours of their owners and the tile just conquered outlined" width="400"> | <img src="assets/screenshots/conquest_region_en.jpg" alt="Map of Lombardy with the hexagons of the conquered areas" width="400"> |
| **`/conquests`: Italy** | **`/conquests`: world** |
| <img src="assets/screenshots/conquest_country_en.jpg" alt="Map of Italy with the larger hexagons of the conquered areas" width="400"> | <img src="assets/screenshots/conquest_world_en.jpg" alt="World map with the hexagons of the conquests on several continents" width="400"> |

---

## 📏 Rules

<details>
<summary><b>🏅 Records and trophies</b></summary>

- **Day / streak / breaks:** the day with the most 💩, the longest streak of consecutive days with at least one 💩, the streak with the most 💩 in total and the longest break between two days with 💩. On a tie, all the periods are listed.
- **Best month:** complete months only (the current month does not count yet).
- **Worst month:** complete months only, excluding the first month with data (you may have started halfway) and those after the last month with data (you may have left the group); the months in between without any 💩 count as 0. So at least a second month of data is needed.
- **Group records:** for each metric the best value among all the people (also those who left the group) and who holds it; on a tie, all of them are listed. The "Now" block only considers people who had a 💩 in the last 90 days.
- **Current state:** a streak is "in progress" if the last 💩 is from today or yesterday; the current break is the days since the last 💩. The 🔥 appears when you reach a record (from 2 up) or go past the record break.
- **Forecast:** for the current month or year, the total so far plus, for each day left, the mean 💩 per day of the last 30 days.
- **Trophies:** 🔥 one every 15 consecutive days with at least one 💩 (15, 30, 45, ...; a 47-day streak is worth 3 trophies), announced in the reply to the first 💩 of the day that completes them; 🏅 **💩 of the month** and 👑 **💩 of the year** to whoever did the most in a complete month or year (on a tie, to all of them). Trophies are computed from the counts, so `/add_poop` and `/remove_poop` update them. 🚩 **Season conqueror** (most conquests in a calendar quarter, stolen tiles included) and ⛰️ **season king** (most tiles held at the end of the quarter) come from the conquest history, with ties as above; the midnight announcement of the first day of a quarter names them, and `/conquests` shows the season in progress.
- **Midnight announcement:** on the first day of every month, at midnight, the bot writes the 💩 of the month just ended in every chat; on January 1st also the 💩 of the year, with happy new year wishes.

</details>

<details>
<summary><b>🚩 Conquest game</b></summary>

- The world is split into hexagonal tiles of about 5 km² ([H3](https://h3geo.org/) cells at resolution 7, about 2.6 km wide).
- Every 💩 sent as a message or sticker (not `/add_poop`) opens a **15 minute window**: the first location sent in it conquers the tile it falls in. One conquest per 💩. A location without an open window conquers nothing.
- 🚩 new tile, ⚔️ tile stolen from another person, 🏠 own tile defended. A tile belongs to whoever conquered it last.
- 👑 The **king of the hill** holds the most tiles; on a tie the current king keeps the crown.
- Every chat has its own map, never reset; removing a 💩 with `/remove_poop` does not remove a conquest.
- Every conquest comes with a **map** of the tiles around it; `/conquests` sends the tiles of the group around its latest conquest, then Lombardy, Italy and the whole world. On these last three a large hexagon stands for the tiles inside it and takes the colour of whoever holds most of them (on a tie, whoever conquered last). If the map cannot be drawn, the reply comes as text.

</details>

<details>
<summary><b>🔄 Old history and supergroups</b></summary>

The counts are tied to the **Telegram user ID**, not to the username: whoever changes username keeps their data, and people without a username are counted under their name.

- The databases of the first versions (counts by username) are **migrated automatically** on the first start. A copy is made first; the old data stays in an archive table until it is linked.
- The group **admins** link the old history to the people with `/link_history`:
  1. `/link_history` shows the history still to link;
  2. when everybody has written at least one message, `/link_history auto` links the identical usernames;
  3. for the others, reply to a message of the person with `/link_history <historical username>`.
- Old records without a username cannot be linked.
- When a group becomes a **supergroup**, Telegram gives it a new chat ID: the bot moves the history to the new chat by itself, and merges it if the supergroup already has counts.

</details>

---

## 🔒 Privacy

The bot reads the group messages to find the 💩: this is why its **Group Privacy** is disabled. The text of the messages is never stored or written to the log. The bot stores, for each chat, the Telegram user ID, username and name of whoever writes, and the 💩 per day. For the conquest game it stores the time of the last 💩 (until its window is used) and, for every conquest, the time, the tile and the latitude and longitude of the location; the log never records the coordinates. For every update the log writes only the command, the kind of chat (private or group), the time taken and the outcome, without names or text. The log records the changes made by hand: for every `/add_poop` and `/remove_poop`, who sent it, the person, the day and the count before and after; for `/link_history`, the old username, the person and the days moved.

---

## 📖 Documentation

| Document | For |
| :------- | :-- |
| [docs/replies.md](docs/replies.md) | Every reply of the bot, in English and Italian |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Running the bot locally, tests, conventions and the workflow of a change |
| [docs/architecture.md](docs/architecture.md) | Modules, path of a message, database, translations |
| [docs/deployment.md](docs/deployment.md) | Telegram setup (menus, descriptions), production on a WSGI hosting, webhook, midnight announcement |
| [docs/operations.md](docs/operations.md) | Deploy, backups and restore, logs, releases |
| [docs/research/](docs/research/README.md) | The studies behind the choices: Mini App design, regularity index, hosting, README |
| [SECURITY.md](SECURITY.md) | Reporting a vulnerability |

## License

Caccometro is released under the [MIT](LICENSE) license.

The maps use tiles and data from [OpenStreetMap](https://www.openstreetmap.org/copyright), © OpenStreetMap contributors, available under the Open Database License.
