# Use cases

What the code does in each use case, read from the code by `tools/write_use_cases.py`: do not edit by hand. Each use case has three views, in UML notation drawn with Mermaid:

1. **Communication diagram**: the modules involved, one arrow for the calls from a module to another (the functions it uses, numbered) and a dashed arrow back with what they return.
2. **Sequence diagram**: the same steps in time order, with the arguments of every call and the variable that receives the result. `alt`, `opt` and `loop` boxes are the `if`, `else` and `for` of the code; a note marks a branch that ends the function, or a function of the same module already drawn above.
3. **Call tree**, folded: every function of the package the entry point may call, private functions replaced by the public ones they call.

The views come from the code, not from a run: every branch appears, whether or not it is taken. Calls inside one module have no arrow; calls to `config.py`, `i18n.py`, classes and other libraries are left out, except the Telegram methods that send something. Arguments and conditions are cut at 40 characters. What each function does is in [functions.md](functions.md); the path of a message through Telegram and the webhook is in [architecture.md](architecture.md#path-of-a-message).

## `/start`

Entry point: `cmd_settings.start_command`

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
  flowchart:
    nodeSpacing: 50
    rankSpacing: 160
---
flowchart LR
    accTitle: Communication diagram, /start
    accDescr: The modules involved, the functions each one calls in another and what comes back, numbered as in the sequence
    telegram("<b>✈️ Telegram</b>")
    cmd_settings("<b>cmd_settings.py</b>")
    chat("<b>chat.py</b>")
    database("<b>database.py</b>")
    telegram -->|"1.#nbsp;start_command"| cmd_settings
    cmd_settings -->|"2.#nbsp;register_sender"| chat
    chat -->|"3.#nbsp;get_language<br/>4.#nbsp;upsert_user"| database
    chat -.->|"5.#nbsp;sender"| cmd_settings
    cmd_settings -->|"6.#nbsp;init_database"| database
    cmd_settings -->|"7.#nbsp;reply_text"| telegram
    classDef step fill:#fffaf3,stroke:#eadccb,stroke-width:2px,color:#3b2a1e
    classDef person fill:#5c4f42,stroke:#5c4f42,color:#fffaf3
    class cmd_settings,chat,database step
    class telegram person
```

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
---
sequenceDiagram
    accTitle: Sequence diagram, /start
    accDescr: The calls between the modules in time order, starting from cmd_settings.start_command
    autonumber
    participant telegram as ✈️ Telegram
    participant cmd_settings as cmd_settings.py
    participant chat as chat.py
    participant database as database.py
    rect rgb(255, 250, 243)
        telegram->>cmd_settings: start_command(update, context)
        cmd_settings->>chat: register_sender(update)
        chat->>database: get_language(update.message.chat_id)
        chat->>database: upsert_user(chat_id, user.user_id, user.username,...)
        chat-->>cmd_settings: sender
        cmd_settings->>database: init_database(update.message.chat_id)
        cmd_settings->>telegram: reply_text(tr('Ciao, sono 🤖 *Caccometro* 🤖.\nMan...)
    end
```

<details>
<summary>Call tree</summary>

- `chat.register_sender`
  - `database.get_language`
  - `chat.register_user`
    - `chat.display_name_of`
    - `database.upsert_user`
- `database.init_database`

</details>

## `/leaderboard_month` (`/classifica_mese`)

Entry point: `cmd_leaderboards.leaderboard_month_command`

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
  flowchart:
    nodeSpacing: 50
    rankSpacing: 160
---
flowchart LR
    accTitle: Communication diagram, /leaderboard_month (/classifica_mese)
    accDescr: The modules involved, the functions each one calls in another and what comes back, numbered as in the sequence
    telegram("<b>✈️ Telegram</b>")
    cmd_leaderboards("<b>cmd_leaderboards.py</b>")
    chat("<b>chat.py</b>")
    database("<b>database.py</b>")
    analysis("<b>analysis.py</b>")
    formatting("<b>formatting.py</b>")
    charts("<b>charts.py</b>")
    telegram -->|"1.#nbsp;leaderboard_month_command"| cmd_leaderboards
    cmd_leaderboards -->|"2.#nbsp;register_sender<br/>9.#nbsp;legacy_hint<br/>20.#nbsp;escape_md<br/>28.#nbsp;reply_chart"| chat
    chat -->|"3.#nbsp;get_language<br/>4.#nbsp;upsert_user<br/>10.#nbsp;list_legacy_users"| database
    chat -.->|"5.#nbsp;sender"| cmd_leaderboards
    cmd_leaderboards -->|"6, 11.#nbsp;reply_text"| telegram
    cmd_leaderboards -->|"7.#nbsp;get_rank<br/>12.#nbsp;get_all_user_rows<br/>16.#nbsp;get_daily_counts_between<br/>25.#nbsp;get_daily_counts"| database
    database -.->|"8.#nbsp;rank<br/>13.#nbsp;(rows_by_user, _)<br/>17.#nbsp;recent<br/>26.#nbsp;daily_counts"| cmd_leaderboards
    cmd_leaderboards -->|"14.#nbsp;analyze_user<br/>18.#nbsp;forecast_totals"| analysis
    cmd_leaderboards -->|"15.#nbsp;flame<br/>21.#nbsp;ranked_line<br/>22.#nbsp;tie_positions<br/>23.#nbsp;standing_lines"| formatting
    analysis -.->|"19.#nbsp;forecast"| cmd_leaderboards
    formatting -.->|"24.#nbsp;standing"| cmd_leaderboards
    cmd_leaderboards -->|"27.#nbsp;generate_rank_chart"| charts
    chat -->|"29, 30.#nbsp;reply_photo<br/>31.#nbsp;reply_text"| telegram
    classDef step fill:#fffaf3,stroke:#eadccb,stroke-width:2px,color:#3b2a1e
    classDef person fill:#5c4f42,stroke:#5c4f42,color:#fffaf3
    class cmd_leaderboards,chat,database,analysis,formatting,charts step
    class telegram person
```

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
---
sequenceDiagram
    accTitle: Sequence diagram, /leaderboard_month (/classifica_mese)
    accDescr: The calls between the modules in time order, starting from cmd_leaderboards.leaderboard_month_command
    autonumber
    participant telegram as ✈️ Telegram
    participant cmd_leaderboards as cmd_leaderboards.py
    participant chat as chat.py
    participant database as database.py
    participant analysis as analysis.py
    participant formatting as formatting.py
    participant charts as charts.py
    rect rgb(255, 250, 243)
        telegram->>cmd_leaderboards: leaderboard_month_command(update, context)
        cmd_leaderboards->>chat: register_sender(update)
        chat->>database: get_language(update.message.chat_id)
        chat->>database: upsert_user(chat_id, user.user_id, user.username,...)
        chat-->>cmd_leaderboards: sender
        opt date is None
            cmd_leaderboards->>telegram: reply_text(tr('⚠️ Formato data non valido. Usa M...)
        end
        cmd_leaderboards->>database: get_rank(update.message.chat_id, time_period, ...)
        database-->>cmd_leaderboards: rank
        opt not rank
            cmd_leaderboards->>chat: legacy_hint(update.message.chat_id)
            chat->>database: list_legacy_users(chat_id)
            cmd_leaderboards->>telegram: reply_text(empty.format(date=date) + legacy_hint...)
            Note over cmd_leaderboards: returns
        end
        opt start_period <= today.isoformat() <= ...
            cmd_leaderboards->>database: get_all_user_rows(update.message.chat_id)
            database-->>cmd_leaderboards: (rows_by_user, _)
            cmd_leaderboards->>analysis: analyze_user(rows, today)
            cmd_leaderboards->>formatting: flame(analyze_user(rows, today).status)
            cmd_leaderboards->>database: get_daily_counts_between(update.message.chat_id, (today - time...)
            database-->>cmd_leaderboards: recent
            cmd_leaderboards->>analysis: forecast_totals({user.user_id: total for user, total ...)
            analysis-->>cmd_leaderboards: forecast
        end
        cmd_leaderboards->>chat: escape_md(user.mention)
        cmd_leaderboards->>formatting: ranked_line(position, names[user.user_id] + flame...)
        cmd_leaderboards->>formatting: tie_positions([t for _, t in rank])
        cmd_leaderboards->>formatting: standing_lines([(user.user_id, total) for user, tota...)
        formatting-->>cmd_leaderboards: standing
        cmd_leaderboards->>database: get_daily_counts(update.message.chat_id, time_period, ...)
        database-->>cmd_leaderboards: daily_counts
        cmd_leaderboards->>charts: generate_rank_chart(rank, daily_counts, time_period, date...)
        cmd_leaderboards->>chat: reply_chart(update, generate_rank_chart(rank, dai...)
        opt fits_caption(message)
            chat->>telegram: reply_photo(chart, caption=message, parse_mode='M...)
            Note over chat: returns
        end
        chat->>telegram: reply_photo(chart, read_timeout=PHOTO_READ_TIMEOUT)
        chat->>telegram: reply_text(message, parse_mode='Markdown')
    end
```

<details>
<summary>Call tree</summary>

- `cmd_leaderboards.leaderboard_command`
  - `chat.register_sender`
    - `database.get_language`
    - `chat.register_user`
      - `chat.display_name_of`
      - `database.upsert_user`
  - `cmd_leaderboards.period_from_args`
  - `database.get_rank`
  - `chat.legacy_hint`
    - `database.list_legacy_users`
  - `database.get_all_user_rows`
  - `formatting.flame`
  - `analysis.analyze_user`
    - `analysis.parse_counts`
    - `analysis.consecutive_runs`
  - `database.get_daily_counts_between`
  - `analysis.forecast_totals`
  - `chat.escape_md`
  - `formatting.ranked_line`
    - `formatting.bold`
  - `formatting.tie_positions`
  - `formatting.standing_lines`
  - `database.get_daily_counts`
    - `database.get_daily_counts_between` (see above)
  - `chat.reply_chart`
    - `chat.fits_caption`
  - `charts.generate_rank_chart`
    - `charts.period_info`
    - `charts.last_day_shown`
    - `charts.chart_label`
    - `charts.sorted_by_name`
    - `charts.short_name`
    - `charts.user_style`
    - `charts.positions`
    - `charts.emoji`
    - `charts.fine_vlines`
    - `charts.layered_grid`
    - `charts.add_cards`
    - `charts.png_bytes`
      - `charts.add_watermark`

</details>

## `/leaderboard_year` (`/classifica_anno`)

Entry point: `cmd_leaderboards.leaderboard_year_command`

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
  flowchart:
    nodeSpacing: 50
    rankSpacing: 160
---
flowchart LR
    accTitle: Communication diagram, /leaderboard_year (/classifica_anno)
    accDescr: The modules involved, the functions each one calls in another and what comes back, numbered as in the sequence
    telegram("<b>✈️ Telegram</b>")
    cmd_leaderboards("<b>cmd_leaderboards.py</b>")
    chat("<b>chat.py</b>")
    database("<b>database.py</b>")
    analysis("<b>analysis.py</b>")
    formatting("<b>formatting.py</b>")
    charts("<b>charts.py</b>")
    telegram -->|"1.#nbsp;leaderboard_year_command"| cmd_leaderboards
    cmd_leaderboards -->|"2.#nbsp;register_sender<br/>9.#nbsp;legacy_hint<br/>20.#nbsp;escape_md<br/>28.#nbsp;reply_chart"| chat
    chat -->|"3.#nbsp;get_language<br/>4.#nbsp;upsert_user<br/>10.#nbsp;list_legacy_users"| database
    chat -.->|"5.#nbsp;sender"| cmd_leaderboards
    cmd_leaderboards -->|"6, 11.#nbsp;reply_text"| telegram
    cmd_leaderboards -->|"7.#nbsp;get_rank<br/>12.#nbsp;get_all_user_rows<br/>16.#nbsp;get_daily_counts_between<br/>25.#nbsp;get_daily_counts"| database
    database -.->|"8.#nbsp;rank<br/>13.#nbsp;(rows_by_user, _)<br/>17.#nbsp;recent<br/>26.#nbsp;daily_counts"| cmd_leaderboards
    cmd_leaderboards -->|"14.#nbsp;analyze_user<br/>18.#nbsp;forecast_totals"| analysis
    cmd_leaderboards -->|"15.#nbsp;flame<br/>21.#nbsp;ranked_line<br/>22.#nbsp;tie_positions<br/>23.#nbsp;standing_lines"| formatting
    analysis -.->|"19.#nbsp;forecast"| cmd_leaderboards
    formatting -.->|"24.#nbsp;standing"| cmd_leaderboards
    cmd_leaderboards -->|"27.#nbsp;generate_rank_chart"| charts
    chat -->|"29, 30.#nbsp;reply_photo<br/>31.#nbsp;reply_text"| telegram
    classDef step fill:#fffaf3,stroke:#eadccb,stroke-width:2px,color:#3b2a1e
    classDef person fill:#5c4f42,stroke:#5c4f42,color:#fffaf3
    class cmd_leaderboards,chat,database,analysis,formatting,charts step
    class telegram person
```

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
---
sequenceDiagram
    accTitle: Sequence diagram, /leaderboard_year (/classifica_anno)
    accDescr: The calls between the modules in time order, starting from cmd_leaderboards.leaderboard_year_command
    autonumber
    participant telegram as ✈️ Telegram
    participant cmd_leaderboards as cmd_leaderboards.py
    participant chat as chat.py
    participant database as database.py
    participant analysis as analysis.py
    participant formatting as formatting.py
    participant charts as charts.py
    rect rgb(255, 250, 243)
        telegram->>cmd_leaderboards: leaderboard_year_command(update, context)
        cmd_leaderboards->>chat: register_sender(update)
        chat->>database: get_language(update.message.chat_id)
        chat->>database: upsert_user(chat_id, user.user_id, user.username,...)
        chat-->>cmd_leaderboards: sender
        opt date is None
            cmd_leaderboards->>telegram: reply_text(tr('⚠️ Formato data non valido. Usa M...)
        end
        cmd_leaderboards->>database: get_rank(update.message.chat_id, time_period, ...)
        database-->>cmd_leaderboards: rank
        opt not rank
            cmd_leaderboards->>chat: legacy_hint(update.message.chat_id)
            chat->>database: list_legacy_users(chat_id)
            cmd_leaderboards->>telegram: reply_text(empty.format(date=date) + legacy_hint...)
            Note over cmd_leaderboards: returns
        end
        opt start_period <= today.isoformat() <= ...
            cmd_leaderboards->>database: get_all_user_rows(update.message.chat_id)
            database-->>cmd_leaderboards: (rows_by_user, _)
            cmd_leaderboards->>analysis: analyze_user(rows, today)
            cmd_leaderboards->>formatting: flame(analyze_user(rows, today).status)
            cmd_leaderboards->>database: get_daily_counts_between(update.message.chat_id, (today - time...)
            database-->>cmd_leaderboards: recent
            cmd_leaderboards->>analysis: forecast_totals({user.user_id: total for user, total ...)
            analysis-->>cmd_leaderboards: forecast
        end
        cmd_leaderboards->>chat: escape_md(user.mention)
        cmd_leaderboards->>formatting: ranked_line(position, names[user.user_id] + flame...)
        cmd_leaderboards->>formatting: tie_positions([t for _, t in rank])
        cmd_leaderboards->>formatting: standing_lines([(user.user_id, total) for user, tota...)
        formatting-->>cmd_leaderboards: standing
        cmd_leaderboards->>database: get_daily_counts(update.message.chat_id, time_period, ...)
        database-->>cmd_leaderboards: daily_counts
        cmd_leaderboards->>charts: generate_rank_chart(rank, daily_counts, time_period, date...)
        cmd_leaderboards->>chat: reply_chart(update, generate_rank_chart(rank, dai...)
        opt fits_caption(message)
            chat->>telegram: reply_photo(chart, caption=message, parse_mode='M...)
            Note over chat: returns
        end
        chat->>telegram: reply_photo(chart, read_timeout=PHOTO_READ_TIMEOUT)
        chat->>telegram: reply_text(message, parse_mode='Markdown')
    end
```

<details>
<summary>Call tree</summary>

- `cmd_leaderboards.leaderboard_command`
  - `chat.register_sender`
    - `database.get_language`
    - `chat.register_user`
      - `chat.display_name_of`
      - `database.upsert_user`
  - `cmd_leaderboards.period_from_args`
  - `database.get_rank`
  - `chat.legacy_hint`
    - `database.list_legacy_users`
  - `database.get_all_user_rows`
  - `formatting.flame`
  - `analysis.analyze_user`
    - `analysis.parse_counts`
    - `analysis.consecutive_runs`
  - `database.get_daily_counts_between`
  - `analysis.forecast_totals`
  - `chat.escape_md`
  - `formatting.ranked_line`
    - `formatting.bold`
  - `formatting.tie_positions`
  - `formatting.standing_lines`
  - `database.get_daily_counts`
    - `database.get_daily_counts_between` (see above)
  - `chat.reply_chart`
    - `chat.fits_caption`
  - `charts.generate_rank_chart`
    - `charts.period_info`
    - `charts.last_day_shown`
    - `charts.chart_label`
    - `charts.sorted_by_name`
    - `charts.short_name`
    - `charts.user_style`
    - `charts.positions`
    - `charts.emoji`
    - `charts.fine_vlines`
    - `charts.layered_grid`
    - `charts.add_cards`
    - `charts.png_bytes`
      - `charts.add_watermark`

</details>

## `/stats_month` (`/statistiche_mese`)

Entry point: `cmd_leaderboards.stats_month_command`

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
  flowchart:
    nodeSpacing: 50
    rankSpacing: 160
---
flowchart LR
    accTitle: Communication diagram, /stats_month (/statistiche_mese)
    accDescr: The modules involved, the functions each one calls in another and what comes back, numbered as in the sequence
    telegram("<b>✈️ Telegram</b>")
    cmd_leaderboards("<b>cmd_leaderboards.py</b>")
    chat("<b>chat.py</b>")
    database("<b>database.py</b>")
    analysis("<b>analysis.py</b>")
    formatting("<b>formatting.py</b>")
    charts("<b>charts.py</b>")
    telegram -->|"1.#nbsp;stats_month_command"| cmd_leaderboards
    cmd_leaderboards -->|"2.#nbsp;register_sender<br/>12.#nbsp;legacy_hint<br/>15.#nbsp;escape_md<br/>24.#nbsp;reply_chart"| chat
    chat -->|"3.#nbsp;get_language<br/>4.#nbsp;upsert_user<br/>13.#nbsp;list_legacy_users"| database
    chat -.->|"5.#nbsp;sender"| cmd_leaderboards
    cmd_leaderboards -->|"6, 14.#nbsp;reply_text"| telegram
    cmd_leaderboards -->|"7.#nbsp;get_daily_counts<br/>9.#nbsp;get_users<br/>20.#nbsp;get_first_days"| database
    database -.->|"8.#nbsp;daily_counts"| cmd_leaderboards
    cmd_leaderboards -->|"10.#nbsp;period_statistics<br/>21.#nbsp;period_regularity"| analysis
    analysis -.->|"11.#nbsp;statistics<br/>22.#nbsp;label"| cmd_leaderboards
    cmd_leaderboards -->|"16.#nbsp;ranked_line<br/>17.#nbsp;tie_positions<br/>18.#nbsp;standing_lines"| formatting
    formatting -.->|"19.#nbsp;standing"| cmd_leaderboards
    cmd_leaderboards -->|"23.#nbsp;generate_statistics_chart"| charts
    chat -->|"25, 26.#nbsp;reply_photo<br/>27.#nbsp;reply_text"| telegram
    classDef step fill:#fffaf3,stroke:#eadccb,stroke-width:2px,color:#3b2a1e
    classDef person fill:#5c4f42,stroke:#5c4f42,color:#fffaf3
    class cmd_leaderboards,chat,database,analysis,formatting,charts step
    class telegram person
```

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
---
sequenceDiagram
    accTitle: Sequence diagram, /stats_month (/statistiche_mese)
    accDescr: The calls between the modules in time order, starting from cmd_leaderboards.stats_month_command
    autonumber
    participant telegram as ✈️ Telegram
    participant cmd_leaderboards as cmd_leaderboards.py
    participant chat as chat.py
    participant database as database.py
    participant analysis as analysis.py
    participant formatting as formatting.py
    participant charts as charts.py
    rect rgb(255, 250, 243)
        telegram->>cmd_leaderboards: stats_month_command(update, context)
        cmd_leaderboards->>chat: register_sender(update)
        chat->>database: get_language(update.message.chat_id)
        chat->>database: upsert_user(chat_id, user.user_id, user.username,...)
        chat-->>cmd_leaderboards: sender
        opt date is None
            cmd_leaderboards->>telegram: reply_text(tr('⚠️ Formato data non valido. Usa M...)
        end
        cmd_leaderboards->>database: get_daily_counts(chat_id, time_period, date)
        database-->>cmd_leaderboards: daily_counts
        cmd_leaderboards->>database: get_users(chat_id)
        cmd_leaderboards->>analysis: period_statistics(daily_counts, get_users(chat_id), *pe...)
        analysis-->>cmd_leaderboards: statistics
        opt not statistics
            cmd_leaderboards->>chat: legacy_hint(update.message.chat_id)
            chat->>database: list_legacy_users(chat_id)
            cmd_leaderboards->>telegram: reply_text(empty.format(date=date) + legacy_hint...)
            Note over cmd_leaderboards: returns
        end
        cmd_leaderboards->>chat: escape_md(s['user'].mention)
        cmd_leaderboards->>formatting: ranked_line(position, names[s['user'].user_id], f...)
        cmd_leaderboards->>formatting: tie_positions([round(s['mean'], 2) for s in statist...)
        cmd_leaderboards->>formatting: standing_lines([(s['user'].user_id, round(s['mean'],...)
        formatting-->>cmd_leaderboards: standing
        opt sender.user_id in names
            cmd_leaderboards->>database: get_first_days(chat_id)
            cmd_leaderboards->>analysis: period_regularity(daily_counts, get_first_days(chat_id)...)
            analysis-->>cmd_leaderboards: label
        end
        cmd_leaderboards->>charts: generate_statistics_chart(statistics, daily_counts, time_period...)
        cmd_leaderboards->>chat: reply_chart(update, generate_statistics_chart(sta...)
        opt fits_caption(message)
            chat->>telegram: reply_photo(chart, caption=message, parse_mode='M...)
            Note over chat: returns
        end
        chat->>telegram: reply_photo(chart, read_timeout=PHOTO_READ_TIMEOUT)
        chat->>telegram: reply_text(message, parse_mode='Markdown')
    end
```

<details>
<summary>Call tree</summary>

- `cmd_leaderboards.stats_command`
  - `chat.register_sender`
    - `database.get_language`
    - `chat.register_user`
      - `chat.display_name_of`
      - `database.upsert_user`
  - `cmd_leaderboards.period_from_args`
  - `database.get_daily_counts`
    - `database.get_daily_counts_between`
  - `analysis.period_statistics`
  - `database.get_users`
  - `chat.legacy_hint`
    - `database.list_legacy_users`
  - `chat.escape_md`
  - `formatting.ranked_line`
    - `formatting.bold`
  - `formatting.tie_positions`
  - `formatting.standing_lines`
  - `analysis.period_regularity`
    - `analysis.regularity`
  - `database.get_first_days`
  - `chat.reply_chart`
    - `chat.fits_caption`
  - `charts.generate_statistics_chart`
    - `charts.period_info`
    - `charts.chart_label`
    - `charts.sorted_by_name`
    - `charts.last_day_shown`
    - `charts.user_style`
    - `charts.normal_pdf`
    - `charts.short_name`
    - `charts.decimal`
    - `charts.fine_vlines`
    - `charts.layered_grid`
    - `charts.add_cards`
    - `charts.png_bytes`
      - `charts.add_watermark`

</details>

## `/stats_year` (`/statistiche_anno`)

Entry point: `cmd_leaderboards.stats_year_command`

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
  flowchart:
    nodeSpacing: 50
    rankSpacing: 160
---
flowchart LR
    accTitle: Communication diagram, /stats_year (/statistiche_anno)
    accDescr: The modules involved, the functions each one calls in another and what comes back, numbered as in the sequence
    telegram("<b>✈️ Telegram</b>")
    cmd_leaderboards("<b>cmd_leaderboards.py</b>")
    chat("<b>chat.py</b>")
    database("<b>database.py</b>")
    analysis("<b>analysis.py</b>")
    formatting("<b>formatting.py</b>")
    charts("<b>charts.py</b>")
    telegram -->|"1.#nbsp;stats_year_command"| cmd_leaderboards
    cmd_leaderboards -->|"2.#nbsp;register_sender<br/>12.#nbsp;legacy_hint<br/>15.#nbsp;escape_md<br/>24.#nbsp;reply_chart"| chat
    chat -->|"3.#nbsp;get_language<br/>4.#nbsp;upsert_user<br/>13.#nbsp;list_legacy_users"| database
    chat -.->|"5.#nbsp;sender"| cmd_leaderboards
    cmd_leaderboards -->|"6, 14.#nbsp;reply_text"| telegram
    cmd_leaderboards -->|"7.#nbsp;get_daily_counts<br/>9.#nbsp;get_users<br/>20.#nbsp;get_first_days"| database
    database -.->|"8.#nbsp;daily_counts"| cmd_leaderboards
    cmd_leaderboards -->|"10.#nbsp;period_statistics<br/>21.#nbsp;period_regularity"| analysis
    analysis -.->|"11.#nbsp;statistics<br/>22.#nbsp;label"| cmd_leaderboards
    cmd_leaderboards -->|"16.#nbsp;ranked_line<br/>17.#nbsp;tie_positions<br/>18.#nbsp;standing_lines"| formatting
    formatting -.->|"19.#nbsp;standing"| cmd_leaderboards
    cmd_leaderboards -->|"23.#nbsp;generate_statistics_chart"| charts
    chat -->|"25, 26.#nbsp;reply_photo<br/>27.#nbsp;reply_text"| telegram
    classDef step fill:#fffaf3,stroke:#eadccb,stroke-width:2px,color:#3b2a1e
    classDef person fill:#5c4f42,stroke:#5c4f42,color:#fffaf3
    class cmd_leaderboards,chat,database,analysis,formatting,charts step
    class telegram person
```

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
---
sequenceDiagram
    accTitle: Sequence diagram, /stats_year (/statistiche_anno)
    accDescr: The calls between the modules in time order, starting from cmd_leaderboards.stats_year_command
    autonumber
    participant telegram as ✈️ Telegram
    participant cmd_leaderboards as cmd_leaderboards.py
    participant chat as chat.py
    participant database as database.py
    participant analysis as analysis.py
    participant formatting as formatting.py
    participant charts as charts.py
    rect rgb(255, 250, 243)
        telegram->>cmd_leaderboards: stats_year_command(update, context)
        cmd_leaderboards->>chat: register_sender(update)
        chat->>database: get_language(update.message.chat_id)
        chat->>database: upsert_user(chat_id, user.user_id, user.username,...)
        chat-->>cmd_leaderboards: sender
        opt date is None
            cmd_leaderboards->>telegram: reply_text(tr('⚠️ Formato data non valido. Usa M...)
        end
        cmd_leaderboards->>database: get_daily_counts(chat_id, time_period, date)
        database-->>cmd_leaderboards: daily_counts
        cmd_leaderboards->>database: get_users(chat_id)
        cmd_leaderboards->>analysis: period_statistics(daily_counts, get_users(chat_id), *pe...)
        analysis-->>cmd_leaderboards: statistics
        opt not statistics
            cmd_leaderboards->>chat: legacy_hint(update.message.chat_id)
            chat->>database: list_legacy_users(chat_id)
            cmd_leaderboards->>telegram: reply_text(empty.format(date=date) + legacy_hint...)
            Note over cmd_leaderboards: returns
        end
        cmd_leaderboards->>chat: escape_md(s['user'].mention)
        cmd_leaderboards->>formatting: ranked_line(position, names[s['user'].user_id], f...)
        cmd_leaderboards->>formatting: tie_positions([round(s['mean'], 2) for s in statist...)
        cmd_leaderboards->>formatting: standing_lines([(s['user'].user_id, round(s['mean'],...)
        formatting-->>cmd_leaderboards: standing
        opt sender.user_id in names
            cmd_leaderboards->>database: get_first_days(chat_id)
            cmd_leaderboards->>analysis: period_regularity(daily_counts, get_first_days(chat_id)...)
            analysis-->>cmd_leaderboards: label
        end
        cmd_leaderboards->>charts: generate_statistics_chart(statistics, daily_counts, time_period...)
        cmd_leaderboards->>chat: reply_chart(update, generate_statistics_chart(sta...)
        opt fits_caption(message)
            chat->>telegram: reply_photo(chart, caption=message, parse_mode='M...)
            Note over chat: returns
        end
        chat->>telegram: reply_photo(chart, read_timeout=PHOTO_READ_TIMEOUT)
        chat->>telegram: reply_text(message, parse_mode='Markdown')
    end
```

<details>
<summary>Call tree</summary>

- `cmd_leaderboards.stats_command`
  - `chat.register_sender`
    - `database.get_language`
    - `chat.register_user`
      - `chat.display_name_of`
      - `database.upsert_user`
  - `cmd_leaderboards.period_from_args`
  - `database.get_daily_counts`
    - `database.get_daily_counts_between`
  - `analysis.period_statistics`
  - `database.get_users`
  - `chat.legacy_hint`
    - `database.list_legacy_users`
  - `chat.escape_md`
  - `formatting.ranked_line`
    - `formatting.bold`
  - `formatting.tie_positions`
  - `formatting.standing_lines`
  - `analysis.period_regularity`
    - `analysis.regularity`
  - `database.get_first_days`
  - `chat.reply_chart`
    - `chat.fits_caption`
  - `charts.generate_statistics_chart`
    - `charts.period_info`
    - `charts.chart_label`
    - `charts.sorted_by_name`
    - `charts.last_day_shown`
    - `charts.user_style`
    - `charts.normal_pdf`
    - `charts.short_name`
    - `charts.decimal`
    - `charts.fine_vlines`
    - `charts.layered_grid`
    - `charts.add_cards`
    - `charts.png_bytes`
      - `charts.add_watermark`

</details>

## `/records` (`/record`)

Entry point: `cmd_records.records_command`

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
  flowchart:
    nodeSpacing: 50
    rankSpacing: 160
---
flowchart LR
    accTitle: Communication diagram, /records (/record)
    accDescr: The modules involved, the functions each one calls in another and what comes back, numbered as in the sequence
    telegram("<b>✈️ Telegram</b>")
    cmd_records("<b>cmd_records.py</b>")
    chat("<b>chat.py</b>")
    database("<b>database.py</b>")
    arguments("<b>arguments.py</b>")
    analysis("<b>analysis.py</b>")
    formatting("<b>formatting.py</b>")
    telegram -->|"1.#nbsp;records_command"| cmd_records
    cmd_records -->|"2.#nbsp;register_sender<br/>14, 24.#nbsp;legacy_hint<br/>19, 28.#nbsp;escape_md"| chat
    chat -->|"3.#nbsp;get_language<br/>4.#nbsp;upsert_user<br/>15.#nbsp;list_legacy_users"| database
    chat -.->|"5.#nbsp;sender"| cmd_records
    cmd_records -->|"6.#nbsp;resolve_optional_target"| arguments
    arguments -->|"7.#nbsp;find_user_by_username"| database
    database -.->|"8.#nbsp;target"| arguments
    arguments -->|"9.#nbsp;register_user"| chat
    arguments -.->|"10.#nbsp;(target, error)"| cmd_records
    cmd_records -->|"11, 16, 21, 25, 33.#nbsp;reply_text"| telegram
    cmd_records -->|"12, 27.#nbsp;get_all_user_rows<br/>22.#nbsp;get_record"| database
    database -.->|"13.#nbsp;(rows_by_user, users)<br/>23.#nbsp;rows"| cmd_records
    cmd_records -->|"17.#nbsp;analyze_group<br/>26, 29.#nbsp;analyze_user<br/>30.#nbsp;record_places"| analysis
    analysis -.->|"18.#nbsp;board"| cmd_records
    cmd_records -->|"20.#nbsp;format_group_record<br/>31.#nbsp;format_user_record"| formatting
    formatting -.->|"32.#nbsp;message"| cmd_records
    classDef step fill:#fffaf3,stroke:#eadccb,stroke-width:2px,color:#3b2a1e
    classDef person fill:#5c4f42,stroke:#5c4f42,color:#fffaf3
    class cmd_records,chat,database,arguments,analysis,formatting step
    class telegram person
```

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
---
sequenceDiagram
    accTitle: Sequence diagram, /records (/record)
    accDescr: The calls between the modules in time order, starting from cmd_records.records_command
    autonumber
    participant telegram as ✈️ Telegram
    participant cmd_records as cmd_records.py
    participant chat as chat.py
    participant database as database.py
    participant arguments as arguments.py
    participant analysis as analysis.py
    participant formatting as formatting.py
    rect rgb(255, 250, 243)
        telegram->>cmd_records: records_command(update, context)
        cmd_records->>chat: register_sender(update)
        chat->>database: get_language(update.message.chat_id)
        chat->>database: upsert_user(chat_id, user.user_id, user.username,...)
        chat-->>cmd_records: sender
        cmd_records->>arguments: resolve_optional_target(update, context, sender, usage)
        opt args and args[0].startswith('@')
            arguments->>database: find_user_by_username(chat_id, username)
            database-->>arguments: target
            Note over arguments: returns
        end
        opt replied is not None
            arguments->>chat: register_user(chat_id, replied)
            Note over arguments: returns
        end
        arguments-->>cmd_records: (target, error)
        opt error
            cmd_records->>telegram: reply_text(error)
            Note over cmd_records: returns
        end
        opt target is None
            cmd_records->>database: get_all_user_rows(chat_id)
            database-->>cmd_records: (rows_by_user, users)
            opt not rows_by_user
                cmd_records->>chat: legacy_hint(chat_id)
                chat->>database: list_legacy_users(chat_id)
                cmd_records->>telegram: reply_text(tr('🤷 Nessun dato disponibile.') + le...)
                Note over cmd_records: returns
            end
            cmd_records->>analysis: analyze_group(rows_by_user, now_rome().date())
            analysis-->>cmd_records: board
            cmd_records->>chat: escape_md(user.mention)
            cmd_records->>formatting: format_group_record(board, names)
            cmd_records->>telegram: reply_text(format_group_record(board, names), pa...)
            Note over cmd_records: returns
        end
        cmd_records->>database: get_record(target.user_id, chat_id)
        database-->>cmd_records: rows
        opt not rows
            cmd_records->>chat: legacy_hint(update.message.chat_id)
            cmd_records->>telegram: reply_text(tr('🤷 Nessun dato disponibile per {na...)
            Note over cmd_records: returns
        end
        cmd_records->>analysis: analyze_user(user_rows, today)
        cmd_records->>database: get_all_user_rows(chat_id)
        cmd_records->>chat: escape_md(target.mention)
        cmd_records->>analysis: analyze_user(rows, today)
        cmd_records->>analysis: record_places(target.user_id, people)
        cmd_records->>formatting: format_user_record(escape_md(target.mention), analyze_us...)
        formatting-->>cmd_records: message
        cmd_records->>telegram: reply_text(message, parse_mode='Markdown')
    end
```

<details>
<summary>Call tree</summary>

- `chat.register_sender`
  - `database.get_language`
  - `chat.register_user`
    - `chat.display_name_of`
    - `database.upsert_user`
- `arguments.resolve_optional_target`
  - `arguments.replied_person`
  - `arguments.resolve_target`
    - `arguments.parse_username_arg`
    - `arguments.invalid_format`
    - `database.find_user_by_username`
    - `arguments.replied_person` (see above)
    - `chat.register_user` (see above)
  - `arguments.invalid_format` (see above)
- `database.get_all_user_rows`
- `chat.legacy_hint`
  - `database.list_legacy_users`
- `analysis.analyze_group`
  - `analysis.analyze_user`
    - `analysis.parse_counts`
    - `analysis.consecutive_runs`
- `chat.escape_md`
- `formatting.format_group_record`
  - `formatting.bold`
- `database.get_record`
- `analysis.analyze_user` (see above)
- `formatting.format_user_record`
  - `formatting.bold` (see above)
- `analysis.record_places`

</details>

## `/trophies` (`/trofei`)

Entry point: `cmd_records.trophies_command`

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
  flowchart:
    nodeSpacing: 50
    rankSpacing: 160
---
flowchart LR
    accTitle: Communication diagram, /trophies (/trofei)
    accDescr: The modules involved, the functions each one calls in another and what comes back, numbered as in the sequence
    telegram("<b>✈️ Telegram</b>")
    cmd_records("<b>cmd_records.py</b>")
    chat("<b>chat.py</b>")
    database("<b>database.py</b>")
    arguments("<b>arguments.py</b>")
    trophies("<b>trophies.py</b>")
    analysis("<b>analysis.py</b>")
    conquest("<b>conquest.py</b>")
    formatting("<b>formatting.py</b>")
    telegram -->|"1.#nbsp;trophies_command"| cmd_records
    cmd_records -->|"2.#nbsp;register_sender<br/>22, 26.#nbsp;escape_md"| chat
    chat -->|"3.#nbsp;get_language<br/>4.#nbsp;upsert_user"| database
    chat -.->|"5.#nbsp;sender"| cmd_records
    cmd_records -->|"6.#nbsp;resolve_optional_target"| arguments
    arguments -->|"7.#nbsp;find_user_by_username"| database
    database -.->|"8.#nbsp;target"| arguments
    arguments -->|"9.#nbsp;register_user"| chat
    arguments -.->|"10.#nbsp;(target, error)"| cmd_records
    cmd_records -->|"11, 29.#nbsp;reply_text"| telegram
    cmd_records -->|"12.#nbsp;get_all_user_rows<br/>14.#nbsp;get_timed_conquests"| database
    database -.->|"13.#nbsp;(rows_by_user, users)"| cmd_records
    cmd_records -->|"15.#nbsp;trophies_by_user"| trophies
    trophies -->|"16, 18.#nbsp;parse_counts<br/>20.#nbsp;consecutive_runs"| analysis
    trophies -->|"17.#nbsp;holdings"| conquest
    analysis -.->|"19.#nbsp;counts"| trophies
    trophies -.->|"21.#nbsp;trophies"| cmd_records
    cmd_records -->|"23.#nbsp;format_group_trophies<br/>27.#nbsp;format_user_trophies"| formatting
    formatting -.->|"24, 28.#nbsp;message"| cmd_records
    cmd_records -->|"25.#nbsp;analyze_user"| analysis
    classDef step fill:#fffaf3,stroke:#eadccb,stroke-width:2px,color:#3b2a1e
    classDef person fill:#5c4f42,stroke:#5c4f42,color:#fffaf3
    class cmd_records,chat,database,arguments,trophies,analysis,conquest,formatting step
    class telegram person
```

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
---
sequenceDiagram
    accTitle: Sequence diagram, /trophies (/trofei)
    accDescr: The calls between the modules in time order, starting from cmd_records.trophies_command
    autonumber
    participant telegram as ✈️ Telegram
    participant cmd_records as cmd_records.py
    participant chat as chat.py
    participant database as database.py
    participant arguments as arguments.py
    participant trophies as trophies.py
    participant analysis as analysis.py
    participant conquest as conquest.py
    participant formatting as formatting.py
    rect rgb(255, 250, 243)
        telegram->>cmd_records: trophies_command(update, context)
        cmd_records->>chat: register_sender(update)
        chat->>database: get_language(update.message.chat_id)
        chat->>database: upsert_user(chat_id, user.user_id, user.username,...)
        chat-->>cmd_records: sender
        cmd_records->>arguments: resolve_optional_target(update, context, sender, usage)
        opt args and args[0].startswith('@')
            arguments->>database: find_user_by_username(chat_id, username)
            database-->>arguments: target
            Note over arguments: returns
        end
        opt replied is not None
            arguments->>chat: register_user(chat_id, replied)
            Note over arguments: returns
        end
        arguments-->>cmd_records: (target, error)
        opt error
            cmd_records->>telegram: reply_text(error)
            Note over cmd_records: returns
        end
        cmd_records->>database: get_all_user_rows(chat_id)
        database-->>cmd_records: (rows_by_user, users)
        cmd_records->>database: get_timed_conquests(chat_id)
        cmd_records->>trophies: trophies_by_user(rows_by_user, today, get_timed_conque...)
        loop for (user_id, rows) in users_rows.ite...
            trophies->>analysis: parse_counts(rows)
        end
        Note over trophies: _winners() as above
        loop for (season, counts) in per_season.it...
            trophies->>conquest: holdings([(user_id, cell) for user_id, _, cell...)
        end
        loop for user_id in set(users_rows) | set(...
            trophies->>analysis: parse_counts(rows)
            analysis-->>trophies: counts
            trophies->>analysis: consecutive_runs(sorted(counts), counts)
        end
        trophies-->>cmd_records: trophies
        alt target is None
            cmd_records->>chat: escape_md(user.mention)
            cmd_records->>formatting: format_group_trophies(trophies, names)
            formatting-->>cmd_records: message
        else
            cmd_records->>analysis: analyze_user(rows, today)
            cmd_records->>chat: escape_md(target.mention)
            cmd_records->>formatting: format_user_trophies(escape_md(target.mention), trophies.g...)
            formatting-->>cmd_records: message
        end
        cmd_records->>telegram: reply_text(message, parse_mode='Markdown')
    end
```

<details>
<summary>Call tree</summary>

- `chat.register_sender`
  - `database.get_language`
  - `chat.register_user`
    - `chat.display_name_of`
    - `database.upsert_user`
- `arguments.resolve_optional_target`
  - `arguments.replied_person`
  - `arguments.resolve_target`
    - `arguments.parse_username_arg`
    - `arguments.invalid_format`
    - `database.find_user_by_username`
    - `arguments.replied_person` (see above)
    - `chat.register_user` (see above)
  - `arguments.invalid_format` (see above)
- `database.get_all_user_rows`
- `trophies.trophies_by_user`
  - `trophies.monthly_winners`
    - `analysis.parse_counts`
  - `trophies.yearly_winners`
    - `analysis.parse_counts` (see above)
  - `trophies.season_results`
    - `trophies.season_of`
    - `conquest.holdings`
  - `trophies.season_of` (see above)
  - `trophies.streak_runs`
    - `analysis.parse_counts` (see above)
    - `analysis.consecutive_runs`
- `database.get_timed_conquests`
- `chat.escape_md`
- `formatting.format_group_trophies`
  - `formatting.bold`
- `analysis.analyze_user`
  - `analysis.parse_counts` (see above)
  - `analysis.consecutive_runs` (see above)
- `formatting.format_user_trophies`
  - `formatting.bold` (see above)

</details>

## `/conquests` (`/conquiste`)

Entry point: `cmd_conquests.conquests_command`

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
  flowchart:
    nodeSpacing: 50
    rankSpacing: 160
---
flowchart LR
    accTitle: Communication diagram, /conquests (/conquiste)
    accDescr: The modules involved, the functions each one calls in another and what comes back, numbered as in the sequence
    telegram("<b>✈️ Telegram</b>")
    cmd_conquests("<b>cmd_conquests.py</b>")
    chat("<b>chat.py</b>")
    database("<b>database.py</b>")
    arguments("<b>arguments.py</b>")
    conquest("<b>conquest.py</b>")
    formatting("<b>formatting.py</b>")
    trophies("<b>trophies.py</b>")
    maps("<b>maps.py</b>")
    telegram -->|"1.#nbsp;conquests_command"| cmd_conquests
    cmd_conquests -->|"2.#nbsp;register_sender<br/>18, 21, 29.#nbsp;escape_md<br/>33.#nbsp;reply_charts"| chat
    chat -->|"3.#nbsp;get_language<br/>4.#nbsp;upsert_user"| database
    chat -.->|"5.#nbsp;sender"| cmd_conquests
    cmd_conquests -->|"6.#nbsp;resolve_optional_target"| arguments
    arguments -->|"7.#nbsp;find_user_by_username"| database
    database -.->|"8.#nbsp;target"| arguments
    arguments -->|"9.#nbsp;register_user"| chat
    arguments -.->|"10.#nbsp;(target, error)"| cmd_conquests
    cmd_conquests -->|"11.#nbsp;reply_text"| telegram
    cmd_conquests -->|"12.#nbsp;get_timed_conquests<br/>16.#nbsp;get_users"| database
    database -.->|"13.#nbsp;timed<br/>17.#nbsp;users"| cmd_conquests
    cmd_conquests -->|"14.#nbsp;holdings<br/>19, 31.#nbsp;visited<br/>20, 28.#nbsp;mention_of"| conquest
    conquest -.->|"15.#nbsp;(counts, king)"| cmd_conquests
    cmd_conquests -->|"22.#nbsp;ranked_line<br/>23.#nbsp;tie_positions<br/>30.#nbsp;format_season_line"| formatting
    cmd_conquests -->|"24.#nbsp;season_of<br/>26.#nbsp;season_results"| trophies
    trophies -.->|"25.#nbsp;season"| cmd_conquests
    trophies -->|"27.#nbsp;holdings"| conquest
    cmd_conquests -->|"32.#nbsp;render"| maps
    chat -->|"34, 37, 38.#nbsp;reply_text<br/>35, 36.#nbsp;reply_photo<br/>39.#nbsp;reply_media_group"| telegram
    classDef step fill:#fffaf3,stroke:#eadccb,stroke-width:2px,color:#3b2a1e
    classDef person fill:#5c4f42,stroke:#5c4f42,color:#fffaf3
    class cmd_conquests,chat,database,arguments,conquest,formatting,trophies,maps step
    class telegram person
```

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
---
sequenceDiagram
    accTitle: Sequence diagram, /conquests (/conquiste)
    accDescr: The calls between the modules in time order, starting from cmd_conquests.conquests_command
    autonumber
    participant telegram as ✈️ Telegram
    participant cmd_conquests as cmd_conquests.py
    participant chat as chat.py
    participant database as database.py
    participant arguments as arguments.py
    participant conquest as conquest.py
    participant formatting as formatting.py
    participant trophies as trophies.py
    participant maps as maps.py
    rect rgb(255, 250, 243)
        telegram->>cmd_conquests: conquests_command(update, context)
        cmd_conquests->>chat: register_sender(update)
        chat->>database: get_language(update.message.chat_id)
        chat->>database: upsert_user(chat_id, user.user_id, user.username,...)
        chat-->>cmd_conquests: sender
        cmd_conquests->>arguments: resolve_optional_target(update, context, sender, tr('/conquis...)
        opt args and args[0].startswith('@')
            arguments->>database: find_user_by_username(chat_id, username)
            database-->>arguments: target
            Note over arguments: returns
        end
        opt replied is not None
            arguments->>chat: register_user(chat_id, replied)
            Note over arguments: returns
        end
        arguments-->>cmd_conquests: (target, error)
        opt error
            cmd_conquests->>telegram: reply_text(error)
            Note over cmd_conquests: returns
        end
        cmd_conquests->>database: get_timed_conquests(chat_id)
        database-->>cmd_conquests: timed
        cmd_conquests->>conquest: holdings(history)
        conquest-->>cmd_conquests: (counts, king)
        cmd_conquests->>database: get_users(chat_id)
        database-->>cmd_conquests: users
        alt target is not None
            cmd_conquests->>chat: escape_md(target.mention)
            cmd_conquests->>conquest: visited(history, target.user_id)
        else
            opt not (not counts)
                cmd_conquests->>conquest: mention_of(users, user_id)
                cmd_conquests->>chat: escape_md(mention_of(users, user_id))
                cmd_conquests->>formatting: ranked_line(position, escape_md(mention_of(users,...)
                cmd_conquests->>formatting: tie_positions([held for _, held in ranking])
                cmd_conquests->>trophies: season_of(now_rome().date())
                trophies-->>cmd_conquests: season
                cmd_conquests->>trophies: season_results(timed)
                loop for (season, counts) in per_season.it...
                    trophies->>conquest: holdings([(user_id, cell) for user_id, _, cell...)
                end
                opt season in (results := season_results(...
                    cmd_conquests->>conquest: mention_of(users, u)
                    cmd_conquests->>chat: escape_md(mention_of(users, u))
                    cmd_conquests->>formatting: format_season_line(season, results[season], {u: escape_m...)
                end
            end
        end
        cmd_conquests->>conquest: visited(history, target.user_id)
        cmd_conquests->>maps: render(view, history, users, shown)
        cmd_conquests->>chat: reply_charts(update, maps_drawn, message)
        alt not charts
            chat->>telegram: reply_text(message, parse_mode='Markdown')
        else
            alt len(charts) == 1
                opt fits_caption(message)
                    chat->>telegram: reply_photo(chart, caption=message, parse_mode='M...)
                    Note over chat: returns
                end
                chat->>telegram: reply_photo(chart, read_timeout=PHOTO_READ_TIMEOUT)
                chat->>telegram: reply_text(message, parse_mode='Markdown')
            else
                opt not caption
                    chat->>telegram: reply_text(message, parse_mode='Markdown')
                end
                chat->>telegram: reply_media_group([InputMediaPhoto(chart, caption=messa...)
            end
        end
    end
```

<details>
<summary>Call tree</summary>

- `chat.register_sender`
  - `database.get_language`
  - `chat.register_user`
    - `chat.display_name_of`
    - `database.upsert_user`
- `arguments.resolve_optional_target`
  - `arguments.replied_person`
  - `arguments.resolve_target`
    - `arguments.parse_username_arg`
    - `arguments.invalid_format`
    - `database.find_user_by_username`
    - `arguments.replied_person` (see above)
    - `chat.register_user` (see above)
  - `arguments.invalid_format` (see above)
- `database.get_timed_conquests`
- `conquest.holdings`
- `database.get_users`
- `chat.escape_md`
- `conquest.visited`
- `formatting.ranked_line`
  - `formatting.bold`
- `conquest.mention_of`
- `formatting.tie_positions`
- `trophies.season_of`
- `trophies.season_results`
  - `trophies.season_of` (see above)
  - `conquest.holdings` (see above)
- `formatting.format_season_line`
  - `formatting.bold` (see above)
- `maps.render`
- `chat.reply_charts`
  - `chat.reply_chart`
    - `chat.fits_caption`
  - `chat.fits_caption` (see above)

</details>

## `/app`

Entry point: `cmd_settings.app_command`

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
  flowchart:
    nodeSpacing: 50
    rankSpacing: 160
---
flowchart LR
    accTitle: Communication diagram, /app
    accDescr: The modules involved, the functions each one calls in another and what comes back, numbered as in the sequence
    telegram("<b>✈️ Telegram</b>")
    cmd_settings("<b>cmd_settings.py</b>")
    chat("<b>chat.py</b>")
    database("<b>database.py</b>")
    miniapp("<b>miniapp.py</b>")
    telegram -->|"1.#nbsp;app_command"| cmd_settings
    cmd_settings -->|"2.#nbsp;register_sender"| chat
    chat -->|"3.#nbsp;get_language<br/>4.#nbsp;upsert_user"| database
    chat -.->|"5.#nbsp;sender"| cmd_settings
    cmd_settings -->|"6.#nbsp;direct_link"| miniapp
    miniapp -.->|"7.#nbsp;link"| cmd_settings
    cmd_settings -->|"8.#nbsp;reply_text"| telegram
    classDef step fill:#fffaf3,stroke:#eadccb,stroke-width:2px,color:#3b2a1e
    classDef person fill:#5c4f42,stroke:#5c4f42,color:#fffaf3
    class cmd_settings,chat,database,miniapp step
    class telegram person
```

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
---
sequenceDiagram
    accTitle: Sequence diagram, /app
    accDescr: The calls between the modules in time order, starting from cmd_settings.app_command
    autonumber
    participant telegram as ✈️ Telegram
    participant cmd_settings as cmd_settings.py
    participant chat as chat.py
    participant database as database.py
    participant miniapp as miniapp.py
    rect rgb(255, 250, 243)
        telegram->>cmd_settings: app_command(update, context)
        cmd_settings->>chat: register_sender(update)
        chat->>database: get_language(update.message.chat_id)
        chat->>database: upsert_user(chat_id, user.user_id, user.username,...)
        chat-->>cmd_settings: sender
        cmd_settings->>miniapp: direct_link(context.bot.username, update.message....)
        miniapp-->>cmd_settings: link
        cmd_settings->>telegram: reply_text(tr('📱 Classifiche, statistiche e mapp...)
    end
```

<details>
<summary>Call tree</summary>

- `chat.register_sender`
  - `database.get_language`
  - `chat.register_user`
    - `chat.display_name_of`
    - `database.upsert_user`
- `miniapp.direct_link`

</details>

## `/day_count` (`/conto_giorno`)

Entry point: `cmd_counts.day_count_command`

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
  flowchart:
    nodeSpacing: 50
    rankSpacing: 160
---
flowchart LR
    accTitle: Communication diagram, /day_count (/conto_giorno)
    accDescr: The modules involved, the functions each one calls in another and what comes back, numbered as in the sequence
    telegram("<b>✈️ Telegram</b>")
    cmd_counts("<b>cmd_counts.py</b>")
    chat("<b>chat.py</b>")
    database("<b>database.py</b>")
    arguments("<b>arguments.py</b>")
    formatting("<b>formatting.py</b>")
    telegram -->|"1.#nbsp;day_count_command"| cmd_counts
    cmd_counts -->|"2.#nbsp;register_sender"| chat
    chat -->|"3.#nbsp;get_language<br/>4.#nbsp;upsert_user"| database
    chat -.->|"5.#nbsp;sender"| cmd_counts
    cmd_counts -->|"6.#nbsp;resolve_target<br/>11.#nbsp;invalid_format<br/>14.#nbsp;parse_date_arg"| arguments
    arguments -->|"7.#nbsp;find_user_by_username"| database
    database -.->|"8.#nbsp;target"| arguments
    arguments -->|"9.#nbsp;register_user"| chat
    arguments -.->|"10.#nbsp;(target, args, error)<br/>12.#nbsp;error<br/>15.#nbsp;(date, selected_date)"| cmd_counts
    cmd_counts -->|"13, 16, 20.#nbsp;reply_text"| telegram
    cmd_counts -->|"17.#nbsp;get_count"| database
    database -.->|"18.#nbsp;count"| cmd_counts
    cmd_counts -->|"19.#nbsp;day_count_sentence"| formatting
    classDef step fill:#fffaf3,stroke:#eadccb,stroke-width:2px,color:#3b2a1e
    classDef person fill:#5c4f42,stroke:#5c4f42,color:#fffaf3
    class cmd_counts,chat,database,arguments,formatting step
    class telegram person
```

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
---
sequenceDiagram
    accTitle: Sequence diagram, /day_count (/conto_giorno)
    accDescr: The calls between the modules in time order, starting from cmd_counts.day_count_command
    autonumber
    participant telegram as ✈️ Telegram
    participant cmd_counts as cmd_counts.py
    participant chat as chat.py
    participant database as database.py
    participant arguments as arguments.py
    participant formatting as formatting.py
    rect rgb(255, 250, 243)
        telegram->>cmd_counts: day_count_command(update, context)
        cmd_counts->>chat: register_sender(update)
        chat->>database: get_language(update.message.chat_id)
        chat->>database: upsert_user(chat_id, user.user_id, user.username,...)
        chat-->>cmd_counts: sender
        cmd_counts->>arguments: resolve_target(update, context.args, sender, usage)
        opt args and args[0].startswith('@')
            arguments->>database: find_user_by_username(chat_id, username)
            database-->>arguments: target
            Note over arguments: returns
        end
        opt replied is not None
            arguments->>chat: register_user(chat_id, replied)
            Note over arguments: returns
        end
        arguments-->>cmd_counts: (target, args, error)
        opt error is None and len(args) > 1
            cmd_counts->>arguments: invalid_format(usage)
            arguments-->>cmd_counts: error
        end
        opt error
            cmd_counts->>telegram: reply_text(error)
            Note over cmd_counts: returns
        end
        opt args
            cmd_counts->>arguments: parse_date_arg(args[0])
            arguments-->>cmd_counts: (date, selected_date)
            opt on ValueError
                cmd_counts->>telegram: reply_text(tr('⚠️ Errore: {error}').format(error=e))
            end
        end
        cmd_counts->>database: get_count(target.user_id, selected_date, update...)
        database-->>cmd_counts: count
        cmd_counts->>formatting: day_count_sentence(target.mention, day, count)
        cmd_counts->>telegram: reply_text(day_count_sentence(target.mention, da...)
    end
```

<details>
<summary>Call tree</summary>

- `chat.register_sender`
  - `database.get_language`
  - `chat.register_user`
    - `chat.display_name_of`
    - `database.upsert_user`
- `arguments.resolve_target`
  - `arguments.parse_username_arg`
  - `arguments.invalid_format`
  - `database.find_user_by_username`
  - `arguments.replied_person`
  - `chat.register_user` (see above)
- `arguments.invalid_format` (see above)
- `arguments.parse_date_arg`
- `database.get_count`
- `formatting.day_count_sentence`

</details>

## `/last_poop` (`/ultima_cacca`)

Entry point: `cmd_counts.last_poop_command`

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
  flowchart:
    nodeSpacing: 50
    rankSpacing: 160
---
flowchart LR
    accTitle: Communication diagram, /last_poop (/ultima_cacca)
    accDescr: The modules involved, the functions each one calls in another and what comes back, numbered as in the sequence
    telegram("<b>✈️ Telegram</b>")
    cmd_counts("<b>cmd_counts.py</b>")
    chat("<b>chat.py</b>")
    database("<b>database.py</b>")
    arguments("<b>arguments.py</b>")
    formatting("<b>formatting.py</b>")
    telegram -->|"1.#nbsp;last_poop_command"| cmd_counts
    cmd_counts -->|"2.#nbsp;register_sender"| chat
    chat -->|"3.#nbsp;get_language<br/>4.#nbsp;upsert_user"| database
    chat -.->|"5.#nbsp;sender"| cmd_counts
    cmd_counts -->|"6.#nbsp;resolve_target<br/>11.#nbsp;invalid_format"| arguments
    arguments -->|"7.#nbsp;find_user_by_username"| database
    database -.->|"8.#nbsp;target"| arguments
    arguments -->|"9.#nbsp;register_user"| chat
    arguments -.->|"10.#nbsp;(target, args, error)<br/>12.#nbsp;error"| cmd_counts
    cmd_counts -->|"13, 17.#nbsp;reply_text"| telegram
    cmd_counts -->|"14.#nbsp;get_days_since_last_poop"| database
    database -.->|"15.#nbsp;days"| cmd_counts
    cmd_counts -->|"16.#nbsp;last_poop_sentence"| formatting
    classDef step fill:#fffaf3,stroke:#eadccb,stroke-width:2px,color:#3b2a1e
    classDef person fill:#5c4f42,stroke:#5c4f42,color:#fffaf3
    class cmd_counts,chat,database,arguments,formatting step
    class telegram person
```

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
---
sequenceDiagram
    accTitle: Sequence diagram, /last_poop (/ultima_cacca)
    accDescr: The calls between the modules in time order, starting from cmd_counts.last_poop_command
    autonumber
    participant telegram as ✈️ Telegram
    participant cmd_counts as cmd_counts.py
    participant chat as chat.py
    participant database as database.py
    participant arguments as arguments.py
    participant formatting as formatting.py
    rect rgb(255, 250, 243)
        telegram->>cmd_counts: last_poop_command(update, context)
        cmd_counts->>chat: register_sender(update)
        chat->>database: get_language(update.message.chat_id)
        chat->>database: upsert_user(chat_id, user.user_id, user.username,...)
        chat-->>cmd_counts: sender
        cmd_counts->>arguments: resolve_target(update, context.args, sender, usage)
        opt args and args[0].startswith('@')
            arguments->>database: find_user_by_username(chat_id, username)
            database-->>arguments: target
            Note over arguments: returns
        end
        opt replied is not None
            arguments->>chat: register_user(chat_id, replied)
            Note over arguments: returns
        end
        arguments-->>cmd_counts: (target, args, error)
        opt error is None and args
            cmd_counts->>arguments: invalid_format(usage)
            arguments-->>cmd_counts: error
        end
        opt error
            cmd_counts->>telegram: reply_text(error)
            Note over cmd_counts: returns
        end
        cmd_counts->>database: get_days_since_last_poop(target.user_id, update.message.chat_id)
        database-->>cmd_counts: days
        cmd_counts->>formatting: last_poop_sentence(target.mention, days)
        cmd_counts->>telegram: reply_text(last_poop_sentence(target.mention, days))
    end
```

<details>
<summary>Call tree</summary>

- `chat.register_sender`
  - `database.get_language`
  - `chat.register_user`
    - `chat.display_name_of`
    - `database.upsert_user`
- `arguments.resolve_target`
  - `arguments.parse_username_arg`
  - `arguments.invalid_format`
  - `database.find_user_by_username`
  - `arguments.replied_person`
  - `chat.register_user` (see above)
- `arguments.invalid_format` (see above)
- `database.get_days_since_last_poop`
- `formatting.last_poop_sentence`

</details>

## `/add_poop` (`/aggiungi_cacca`)

Entry point: `cmd_counts.add_poop_command`

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
  flowchart:
    nodeSpacing: 50
    rankSpacing: 160
---
flowchart LR
    accTitle: Communication diagram, /add_poop (/aggiungi_cacca)
    accDescr: The modules involved, the functions each one calls in another and what comes back, numbered as in the sequence
    telegram("<b>✈️ Telegram</b>")
    cmd_counts("<b>cmd_counts.py</b>")
    chat("<b>chat.py</b>")
    database("<b>database.py</b>")
    arguments("<b>arguments.py</b>")
    formatting("<b>formatting.py</b>")
    telegram -->|"1.#nbsp;add_poop_command"| cmd_counts
    cmd_counts -->|"2.#nbsp;register_sender<br/>14.#nbsp;is_chat_admin<br/>22.#nbsp;where"| chat
    chat -->|"3.#nbsp;get_language<br/>4.#nbsp;upsert_user"| database
    chat -.->|"5.#nbsp;sender"| cmd_counts
    cmd_counts -->|"6.#nbsp;resolve_target<br/>11.#nbsp;invalid_format<br/>17.#nbsp;parse_date_arg"| arguments
    arguments -->|"7.#nbsp;find_user_by_username"| database
    database -.->|"8.#nbsp;target"| arguments
    arguments -->|"9.#nbsp;register_user"| chat
    arguments -.->|"10.#nbsp;(target, args, error)<br/>12.#nbsp;error<br/>18.#nbsp;(date, selected_date)"| cmd_counts
    cmd_counts -->|"13, 16, 19, 23, 25.#nbsp;reply_text"| telegram
    chat -->|"15.#nbsp;get_chat_member"| telegram
    cmd_counts -->|"20.#nbsp;add_count"| database
    database -.->|"21.#nbsp;(old_count, new_count)"| cmd_counts
    cmd_counts -->|"24.#nbsp;change_count_sentence"| formatting
    classDef step fill:#fffaf3,stroke:#eadccb,stroke-width:2px,color:#3b2a1e
    classDef person fill:#5c4f42,stroke:#5c4f42,color:#fffaf3
    class cmd_counts,chat,database,arguments,formatting step
    class telegram person
```

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
---
sequenceDiagram
    accTitle: Sequence diagram, /add_poop (/aggiungi_cacca)
    accDescr: The calls between the modules in time order, starting from cmd_counts.add_poop_command
    autonumber
    participant telegram as ✈️ Telegram
    participant cmd_counts as cmd_counts.py
    participant chat as chat.py
    participant database as database.py
    participant arguments as arguments.py
    participant formatting as formatting.py
    rect rgb(255, 250, 243)
        telegram->>cmd_counts: add_poop_command(update, context)
        cmd_counts->>chat: register_sender(update)
        chat->>database: get_language(update.message.chat_id)
        chat->>database: upsert_user(chat_id, user.user_id, user.username,...)
        chat-->>cmd_counts: sender
        cmd_counts->>arguments: resolve_target(update, context.args, sender, usage)
        opt args and args[0].startswith('@')
            arguments->>database: find_user_by_username(chat_id, username)
            database-->>arguments: target
            Note over arguments: returns
        end
        opt replied is not None
            arguments->>chat: register_user(chat_id, replied)
            Note over arguments: returns
        end
        arguments-->>cmd_counts: (target, args, error)
        opt error is None and len(args) != 1
            cmd_counts->>arguments: invalid_format(usage)
            arguments-->>cmd_counts: error
        end
        opt error
            cmd_counts->>telegram: reply_text(error)
            Note over cmd_counts: returns
        end
        cmd_counts->>chat: is_chat_admin(update, context)
        chat->>telegram: get_chat_member(update.message.chat_id, update.messag...)
        cmd_counts->>telegram: reply_text(tr('🔒 Solo gli admin del gruppo posso...)
        cmd_counts->>arguments: parse_date_arg(args[0])
        arguments-->>cmd_counts: (date, selected_date)
        opt on ValueError
            cmd_counts->>telegram: reply_text(tr('⚠️ Errore: {error}').format(error=e))
        end
        cmd_counts->>database: add_count(target.user_id, selected_date, delta,...)
        database-->>cmd_counts: (old_count, new_count)
        cmd_counts->>chat: where(update)
        alt delta < 0 and old_count == 0
            cmd_counts->>telegram: reply_text(tr('⚠️ Il conteggio di {name} nel gio...)
        else
            cmd_counts->>formatting: change_count_sentence(target.mention, date, new_count, delta)
            cmd_counts->>telegram: reply_text(change_count_sentence(target.mention,...)
        end
    end
```

<details>
<summary>Call tree</summary>

- `cmd_counts.change_count_command`
  - `chat.register_sender`
    - `database.get_language`
    - `chat.register_user`
      - `chat.display_name_of`
      - `database.upsert_user`
  - `arguments.resolve_target`
    - `arguments.parse_username_arg`
    - `arguments.invalid_format`
    - `database.find_user_by_username`
    - `arguments.replied_person`
    - `chat.register_user` (see above)
  - `arguments.invalid_format` (see above)
  - `cmd_counts.may_change_counts_of`
    - `chat.is_chat_admin`
  - `arguments.parse_date_arg`
  - `database.add_count`
  - `chat.where`
  - `formatting.change_count_sentence`

</details>

## `/remove_poop` (`/togli_cacca`)

Entry point: `cmd_counts.remove_poop_command`

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
  flowchart:
    nodeSpacing: 50
    rankSpacing: 160
---
flowchart LR
    accTitle: Communication diagram, /remove_poop (/togli_cacca)
    accDescr: The modules involved, the functions each one calls in another and what comes back, numbered as in the sequence
    telegram("<b>✈️ Telegram</b>")
    cmd_counts("<b>cmd_counts.py</b>")
    chat("<b>chat.py</b>")
    database("<b>database.py</b>")
    arguments("<b>arguments.py</b>")
    formatting("<b>formatting.py</b>")
    telegram -->|"1.#nbsp;remove_poop_command"| cmd_counts
    cmd_counts -->|"2.#nbsp;register_sender<br/>14.#nbsp;is_chat_admin<br/>22.#nbsp;where"| chat
    chat -->|"3.#nbsp;get_language<br/>4.#nbsp;upsert_user"| database
    chat -.->|"5.#nbsp;sender"| cmd_counts
    cmd_counts -->|"6.#nbsp;resolve_target<br/>11.#nbsp;invalid_format<br/>17.#nbsp;parse_date_arg"| arguments
    arguments -->|"7.#nbsp;find_user_by_username"| database
    database -.->|"8.#nbsp;target"| arguments
    arguments -->|"9.#nbsp;register_user"| chat
    arguments -.->|"10.#nbsp;(target, args, error)<br/>12.#nbsp;error<br/>18.#nbsp;(date, selected_date)"| cmd_counts
    cmd_counts -->|"13, 16, 19, 23, 25.#nbsp;reply_text"| telegram
    chat -->|"15.#nbsp;get_chat_member"| telegram
    cmd_counts -->|"20.#nbsp;add_count"| database
    database -.->|"21.#nbsp;(old_count, new_count)"| cmd_counts
    cmd_counts -->|"24.#nbsp;change_count_sentence"| formatting
    classDef step fill:#fffaf3,stroke:#eadccb,stroke-width:2px,color:#3b2a1e
    classDef person fill:#5c4f42,stroke:#5c4f42,color:#fffaf3
    class cmd_counts,chat,database,arguments,formatting step
    class telegram person
```

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
---
sequenceDiagram
    accTitle: Sequence diagram, /remove_poop (/togli_cacca)
    accDescr: The calls between the modules in time order, starting from cmd_counts.remove_poop_command
    autonumber
    participant telegram as ✈️ Telegram
    participant cmd_counts as cmd_counts.py
    participant chat as chat.py
    participant database as database.py
    participant arguments as arguments.py
    participant formatting as formatting.py
    rect rgb(255, 250, 243)
        telegram->>cmd_counts: remove_poop_command(update, context)
        cmd_counts->>chat: register_sender(update)
        chat->>database: get_language(update.message.chat_id)
        chat->>database: upsert_user(chat_id, user.user_id, user.username,...)
        chat-->>cmd_counts: sender
        cmd_counts->>arguments: resolve_target(update, context.args, sender, usage)
        opt args and args[0].startswith('@')
            arguments->>database: find_user_by_username(chat_id, username)
            database-->>arguments: target
            Note over arguments: returns
        end
        opt replied is not None
            arguments->>chat: register_user(chat_id, replied)
            Note over arguments: returns
        end
        arguments-->>cmd_counts: (target, args, error)
        opt error is None and len(args) != 1
            cmd_counts->>arguments: invalid_format(usage)
            arguments-->>cmd_counts: error
        end
        opt error
            cmd_counts->>telegram: reply_text(error)
            Note over cmd_counts: returns
        end
        cmd_counts->>chat: is_chat_admin(update, context)
        chat->>telegram: get_chat_member(update.message.chat_id, update.messag...)
        cmd_counts->>telegram: reply_text(tr('🔒 Solo gli admin del gruppo posso...)
        cmd_counts->>arguments: parse_date_arg(args[0])
        arguments-->>cmd_counts: (date, selected_date)
        opt on ValueError
            cmd_counts->>telegram: reply_text(tr('⚠️ Errore: {error}').format(error=e))
        end
        cmd_counts->>database: add_count(target.user_id, selected_date, delta,...)
        database-->>cmd_counts: (old_count, new_count)
        cmd_counts->>chat: where(update)
        alt delta < 0 and old_count == 0
            cmd_counts->>telegram: reply_text(tr('⚠️ Il conteggio di {name} nel gio...)
        else
            cmd_counts->>formatting: change_count_sentence(target.mention, date, new_count, delta)
            cmd_counts->>telegram: reply_text(change_count_sentence(target.mention,...)
        end
    end
```

<details>
<summary>Call tree</summary>

- `cmd_counts.change_count_command`
  - `chat.register_sender`
    - `database.get_language`
    - `chat.register_user`
      - `chat.display_name_of`
      - `database.upsert_user`
  - `arguments.resolve_target`
    - `arguments.parse_username_arg`
    - `arguments.invalid_format`
    - `database.find_user_by_username`
    - `arguments.replied_person`
    - `chat.register_user` (see above)
  - `arguments.invalid_format` (see above)
  - `cmd_counts.may_change_counts_of`
    - `chat.is_chat_admin`
  - `arguments.parse_date_arg`
  - `database.add_count`
  - `chat.where`
  - `formatting.change_count_sentence`

</details>

## `/language` (`/lingua`)

Entry point: `cmd_settings.language_command`

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
  flowchart:
    nodeSpacing: 50
    rankSpacing: 160
---
flowchart LR
    accTitle: Communication diagram, /language (/lingua)
    accDescr: The modules involved, the functions each one calls in another and what comes back, numbered as in the sequence
    telegram("<b>✈️ Telegram</b>")
    cmd_settings("<b>cmd_settings.py</b>")
    chat("<b>chat.py</b>")
    database("<b>database.py</b>")
    menus("<b>menus.py</b>")
    telegram -->|"1.#nbsp;language_command"| cmd_settings
    cmd_settings -->|"2.#nbsp;register_sender<br/>7.#nbsp;is_chat_admin<br/>11.#nbsp;where"| chat
    chat -->|"3.#nbsp;get_language<br/>4.#nbsp;upsert_user"| database
    chat -.->|"5.#nbsp;sender"| cmd_settings
    cmd_settings -->|"6, 9, 12.#nbsp;reply_text"| telegram
    chat -->|"8.#nbsp;get_chat_member"| telegram
    cmd_settings -->|"10.#nbsp;set_language"| database
    cmd_settings -->|"13.#nbsp;set_chat_menu"| menus
    menus -->|"14, 15.#nbsp;set_my_commands"| telegram
    classDef step fill:#fffaf3,stroke:#eadccb,stroke-width:2px,color:#3b2a1e
    classDef person fill:#5c4f42,stroke:#5c4f42,color:#fffaf3
    class cmd_settings,chat,database,menus step
    class telegram person
```

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
---
sequenceDiagram
    accTitle: Sequence diagram, /language (/lingua)
    accDescr: The calls between the modules in time order, starting from cmd_settings.language_command
    autonumber
    participant telegram as ✈️ Telegram
    participant cmd_settings as cmd_settings.py
    participant chat as chat.py
    participant database as database.py
    participant menus as menus.py
    rect rgb(255, 250, 243)
        telegram->>cmd_settings: language_command(update, context)
        cmd_settings->>chat: register_sender(update)
        chat->>database: get_language(update.message.chat_id)
        chat->>database: upsert_user(chat_id, user.user_id, user.username,...)
        chat-->>cmd_settings: sender
        opt language not in i18n.LANGUAGES
            cmd_settings->>telegram: reply_text(tr('🌐 La lingua di questa chat è {nam...)
            Note over cmd_settings: returns
        end
        cmd_settings->>chat: is_chat_admin(update, context)
        chat->>telegram: get_chat_member(update.message.chat_id, update.messag...)
        opt not await is_chat_admin(update, context)
            cmd_settings->>telegram: reply_text(tr('🔒 Solo gli admin del gruppo posso...)
            Note over cmd_settings: returns
        end
        cmd_settings->>database: set_language(update.message.chat_id, language)
        cmd_settings->>chat: where(update)
        cmd_settings->>telegram: reply_text(tr('Da ora parlo italiano 🇮🇹'))
        cmd_settings->>menus: set_chat_menu(context.bot, update.message.chat_id, ...)
        menus->>telegram: set_my_commands(menu(language), scope=BotCommandScope...)
        opt group
            menus->>telegram: set_my_commands(menu(language, admins=True), scope=Bo...)
        end
    end
```

<details>
<summary>Call tree</summary>

- `chat.register_sender`
  - `database.get_language`
  - `chat.register_user`
    - `chat.display_name_of`
    - `database.upsert_user`
- `chat.is_chat_admin`
- `database.set_language`
- `chat.where`
- `menus.set_chat_menu`
  - `menus.menu`

</details>

## `/link_history` (`/collega_storico`)

Entry point: `cmd_settings.link_history_command`

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
  flowchart:
    nodeSpacing: 50
    rankSpacing: 160
---
flowchart LR
    accTitle: Communication diagram, /link_history (/collega_storico)
    accDescr: The modules involved, the functions each one calls in another and what comes back, numbered as in the sequence
    telegram("<b>✈️ Telegram</b>")
    cmd_settings("<b>cmd_settings.py</b>")
    chat("<b>chat.py</b>")
    database("<b>database.py</b>")
    arguments("<b>arguments.py</b>")
    telegram -->|"1.#nbsp;link_history_command"| cmd_settings
    cmd_settings -->|"2.#nbsp;register_sender<br/>14.#nbsp;is_chat_admin<br/>19, 32.#nbsp;where<br/>28.#nbsp;register_user"| chat
    chat -->|"3.#nbsp;get_language<br/>4.#nbsp;upsert_user"| database
    chat -.->|"5.#nbsp;sender<br/>29.#nbsp;target"| cmd_settings
    cmd_settings -->|"6, 20.#nbsp;list_legacy_users<br/>9.#nbsp;find_user_by_username<br/>11.#nbsp;count_legacy_orphans<br/>17.#nbsp;link_legacy_by_username<br/>30.#nbsp;link_legacy_username"| database
    database -.->|"7.#nbsp;legacy<br/>10.#nbsp;match<br/>12.#nbsp;orphans<br/>18.#nbsp;linked<br/>21.#nbsp;remaining<br/>31.#nbsp;days"| cmd_settings
    cmd_settings -->|"8, 13, 16, 22, 24, 27, 33, 34.#nbsp;reply_text"| telegram
    chat -->|"15.#nbsp;get_chat_member"| telegram
    cmd_settings -->|"23.#nbsp;invalid_format<br/>25.#nbsp;replied_person"| arguments
    arguments -.->|"26.#nbsp;replied"| cmd_settings
    classDef step fill:#fffaf3,stroke:#eadccb,stroke-width:2px,color:#3b2a1e
    classDef person fill:#5c4f42,stroke:#5c4f42,color:#fffaf3
    class cmd_settings,chat,database,arguments step
    class telegram person
```

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
---
sequenceDiagram
    accTitle: Sequence diagram, /link_history (/collega_storico)
    accDescr: The calls between the modules in time order, starting from cmd_settings.link_history_command
    autonumber
    participant telegram as ✈️ Telegram
    participant cmd_settings as cmd_settings.py
    participant chat as chat.py
    participant database as database.py
    participant arguments as arguments.py
    rect rgb(255, 250, 243)
        telegram->>cmd_settings: link_history_command(update, context)
        cmd_settings->>chat: register_sender(update)
        chat->>database: get_language(update.message.chat_id)
        chat->>database: upsert_user(chat_id, user.user_id, user.username,...)
        chat-->>cmd_settings: sender
        opt not args
            cmd_settings->>database: list_legacy_users(chat_id)
            database-->>cmd_settings: legacy
            opt not legacy
                cmd_settings->>telegram: reply_text(tr('🤷 Non ci sono dati storici da col...)
                Note over cmd_settings: returns
            end
            loop for (legacy_username, total) in legacy
                cmd_settings->>database: find_user_by_username(chat_id, legacy_username)
                database-->>cmd_settings: match
            end
            cmd_settings->>database: count_legacy_orphans(chat_id)
            database-->>cmd_settings: orphans
            cmd_settings->>telegram: reply_text('\n'.join(lines))
            Note over cmd_settings: returns
        end
        cmd_settings->>chat: is_chat_admin(update, context)
        chat->>telegram: get_chat_member(update.message.chat_id, update.messag...)
        opt not await is_chat_admin(update, context)
            cmd_settings->>telegram: reply_text(tr('🔒 Solo gli admin del gruppo posso...)
            Note over cmd_settings: returns
        end
        opt len(args) == 1 and args[0] == 'auto'
            cmd_settings->>database: link_legacy_by_username(chat_id)
            database-->>cmd_settings: linked
            loop for (legacy_username, user, days) in ...
                cmd_settings->>chat: where(update)
            end
            cmd_settings->>database: list_legacy_users(chat_id)
            database-->>cmd_settings: remaining
            cmd_settings->>telegram: reply_text('\n'.join(lines))
            Note over cmd_settings: returns
        end
        opt len(args) != 1
            cmd_settings->>arguments: invalid_format(usage)
            cmd_settings->>telegram: reply_text(invalid_format(usage))
            Note over cmd_settings: returns
        end
        cmd_settings->>arguments: replied_person(update)
        arguments-->>cmd_settings: replied
        opt replied is None
            cmd_settings->>telegram: reply_text(tr('⚠️ Rispondi a un messaggio della ...)
            Note over cmd_settings: returns
        end
        cmd_settings->>chat: register_user(chat_id, replied)
        chat-->>cmd_settings: target
        cmd_settings->>database: link_legacy_username(chat_id, legacy_username, target.user_id)
        database-->>cmd_settings: days
        cmd_settings->>chat: where(update)
        alt days == 0
            cmd_settings->>telegram: reply_text(tr('🤷 Nessun dato storico trovato per...)
        else
            cmd_settings->>telegram: reply_text(tr('🔗 Collegati {days} giorni di dati...)
        end
    end
```

<details>
<summary>Call tree</summary>

- `chat.register_sender`
  - `database.get_language`
  - `chat.register_user`
    - `chat.display_name_of`
    - `database.upsert_user`
- `database.list_legacy_users`
- `database.find_user_by_username`
- `database.count_legacy_orphans`
- `chat.is_chat_admin`
- `database.link_legacy_by_username`
  - `database.list_legacy_users` (see above)
  - `database.find_user_by_username` (see above)
  - `database.link_legacy_username`
- `chat.where`
- `arguments.invalid_format`
- `arguments.replied_person`
- `chat.register_user` (see above)
- `database.link_legacy_username` (see above)

</details>

## A message in the chat: 💩 or 🚽 (text or sticker), a location, a mention of the bot, "run"

Entry point: `messages.handle_message`

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
  flowchart:
    nodeSpacing: 50
    rankSpacing: 160
---
flowchart LR
    accTitle: Communication diagram, A message in the chat, 💩 or 🚽 (text or sticker), a location, a mention of the bot, "run"
    accDescr: The modules involved, the functions each one calls in another and what comes back, numbered as in the sequence
    telegram("<b>✈️ Telegram</b>")
    messages("<b>messages.py</b>")
    chat("<b>chat.py</b>")
    database("<b>database.py</b>")
    formatting("<b>formatting.py</b>")
    trophies("<b>trophies.py</b>")
    analysis("<b>analysis.py</b>")
    conquest("<b>conquest.py</b>")
    maps("<b>maps.py</b>")
    telegram -->|"1.#nbsp;handle_message"| messages
    messages -->|"2.#nbsp;register_sender<br/>9, 18, 29, 31, 33.#nbsp;escape_md<br/>35.#nbsp;reply_charts"| chat
    chat -->|"3.#nbsp;get_language<br/>4.#nbsp;upsert_user"| database
    chat -.->|"5.#nbsp;sender"| messages
    messages -->|"6.#nbsp;add_count<br/>8.#nbsp;open_conquest_window<br/>11.#nbsp;get_record<br/>22.#nbsp;conquer<br/>27.#nbsp;get_users"| database
    database -.->|"7.#nbsp;(_, count)<br/>23.#nbsp;result<br/>28.#nbsp;users"| messages
    messages -->|"10.#nbsp;poop_sentence<br/>17.#nbsp;format_streak_trophy"| formatting
    messages -->|"12.#nbsp;new_streak_trophy"| trophies
    trophies -->|"13.#nbsp;parse_counts<br/>15.#nbsp;consecutive_runs"| analysis
    analysis -.->|"14.#nbsp;counts"| trophies
    trophies -.->|"16.#nbsp;streak"| messages
    messages -->|"19, 20.#nbsp;reply_text"| telegram
    messages -->|"21.#nbsp;cell_of<br/>24, 25.#nbsp;holdings<br/>30, 32.#nbsp;mention_of"| conquest
    conquest -.->|"26.#nbsp;(counts, king)"| messages
    messages -->|"34.#nbsp;render"| maps
    chat -->|"36, 39, 40.#nbsp;reply_text<br/>37, 38.#nbsp;reply_photo<br/>41.#nbsp;reply_media_group"| telegram
    classDef step fill:#fffaf3,stroke:#eadccb,stroke-width:2px,color:#3b2a1e
    classDef person fill:#5c4f42,stroke:#5c4f42,color:#fffaf3
    class messages,chat,database,formatting,trophies,analysis,conquest,maps step
    class telegram person
```

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
---
sequenceDiagram
    accTitle: Sequence diagram, A message in the chat, 💩 or 🚽 (text or sticker), a location, a mention of the bot, "run"
    accDescr: The calls between the modules in time order, starting from messages.handle_message
    autonumber
    participant telegram as ✈️ Telegram
    participant messages as messages.py
    participant chat as chat.py
    participant database as database.py
    participant formatting as formatting.py
    participant trophies as trophies.py
    participant analysis as analysis.py
    participant conquest as conquest.py
    participant maps as maps.py
    rect rgb(255, 250, 243)
        telegram->>messages: handle_message(update, context)
        messages->>chat: register_sender(update)
        chat->>database: get_language(update.message.chat_id)
        chat->>database: upsert_user(chat_id, user.user_id, user.username,...)
        chat-->>messages: sender
        alt update.message.text
            opt not (config.BOT_USERNAME and config.B...
                alt '💩' in text or '🚽' in text
                    messages->>database: add_count(sender.user_id, today.strftime(STORIN...)
                    database-->>messages: (_, count)
                    messages->>database: open_conquest_window(sender.user_id, int(time.time() if se...)
                    messages->>chat: escape_md(sender.mention)
                    messages->>formatting: poop_sentence(escape_md(sender.mention), sent.hour,...)
                    opt count == 1
                        messages->>database: get_record(sender.user_id, chat_id)
                        messages->>trophies: new_streak_trophy(get_record(sender.user_id, chat_id), ...)
                        trophies->>analysis: parse_counts(rows)
                        analysis-->>trophies: counts
                        trophies->>analysis: consecutive_runs(sorted((day for day in counts if day ...)
                        trophies-->>messages: streak
                        opt streak is not None
                            messages->>formatting: format_streak_trophy(streak)
                        end
                    end
                else
                    opt re.search('\\brun\\b', text)
                        messages->>chat: escape_md(sender.mention)
                    end
                end
            end
            opt response
                messages->>telegram: reply_text(response, parse_mode='Markdown')
            end
        else
            alt update.message.sticker
                opt emoji == '💩' or emoji == '🚽'
                    Note over messages: record_poop() as above
                    messages->>telegram: reply_text(response, parse_mode='Markdown')
                end
            else
                opt update.message.location
                    messages->>conquest: cell_of(location.latitude, location.longitude)
                    messages->>database: conquer(chat_id, sender.user_id, int(sent_at....)
                    database-->>messages: result
                    messages->>conquest: holdings(history[:-1])
                    messages->>conquest: holdings(history)
                    conquest-->>messages: (counts, king)
                    messages->>database: get_users(chat_id)
                    database-->>messages: users
                    messages->>chat: escape_md(sender.mention)
                    opt not (previous is None)
                        opt not (previous == sender.user_id)
                            messages->>conquest: mention_of(users, previous)
                            messages->>chat: escape_md(mention_of(users, previous))
                        end
                    end
                    opt king != king_before
                        messages->>conquest: mention_of(users, king)
                        messages->>chat: escape_md(mention_of(users, king))
                    end
                    messages->>maps: render(maps.zoom_map, history, users)
                    messages->>chat: reply_charts(update, [history and maps.render(maps...)
                    alt not charts
                        chat->>telegram: reply_text(message, parse_mode='Markdown')
                    else
                        alt len(charts) == 1
                            opt fits_caption(message)
                                chat->>telegram: reply_photo(chart, caption=message, parse_mode='M...)
                                Note over chat: returns
                            end
                            chat->>telegram: reply_photo(chart, read_timeout=PHOTO_READ_TIMEOUT)
                            chat->>telegram: reply_text(message, parse_mode='Markdown')
                        else
                            opt not caption
                                chat->>telegram: reply_text(message, parse_mode='Markdown')
                            end
                            chat->>telegram: reply_media_group([InputMediaPhoto(chart, caption=messa...)
                        end
                    end
                end
            end
        end
    end
```

<details>
<summary>Call tree</summary>

- `chat.register_sender`
  - `database.get_language`
  - `chat.register_user`
    - `chat.display_name_of`
    - `database.upsert_user`
- `messages.record_poop`
  - `database.add_count`
  - `database.open_conquest_window`
  - `formatting.poop_sentence`
    - `formatting.poop_pool`
  - `chat.escape_md`
  - `trophies.new_streak_trophy`
    - `analysis.parse_counts`
    - `analysis.consecutive_runs`
  - `database.get_record`
  - `formatting.format_streak_trophy`
- `chat.escape_md` (see above)
- `messages.record_conquest`
  - `database.conquer`
  - `conquest.cell_of`
  - `conquest.holdings`
  - `database.get_users`
  - `chat.escape_md` (see above)
  - `conquest.mention_of`
- `chat.reply_charts`
  - `chat.reply_chart`
    - `chat.fits_caption`
  - `chat.fits_caption` (see above)
- `maps.render`
- `maps.zoom_map`
  - `maps.owners`
  - `maps.tile_xy`
  - `maps.legend_and_colors`
    - `conquest.holdings` (see above)
    - `charts.chart_label`
    - `charts.short_name`
    - `conquest.mention_of` (see above)
    - `charts.sorted_by_name`
  - `maps.draw`
    - `maps.basemap`
      - `maps.cached_tile`
      - `maps.trim_cache`
    - `maps.outline`
      - `maps.tile_xy` (see above)
    - `charts.add_cards`
    - `maps.jpeg`
    - `charts.png_bytes`
      - `charts.add_watermark`

</details>

## A group becomes a supergroup

Entry point: `messages.handle_migration`

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
  flowchart:
    nodeSpacing: 50
    rankSpacing: 160
---
flowchart LR
    accTitle: Communication diagram, A group becomes a supergroup
    accDescr: The modules involved, the functions each one calls in another and what comes back, numbered as in the sequence
    telegram("<b>✈️ Telegram</b>")
    messages("<b>messages.py</b>")
    database("<b>database.py</b>")
    menus("<b>menus.py</b>")
    telegram -->|"1.#nbsp;handle_migration"| messages
    messages -->|"2.#nbsp;migrate_chat<br/>4.#nbsp;get_language"| database
    database -.->|"3.#nbsp;result<br/>5.#nbsp;language"| messages
    messages -->|"6.#nbsp;set_chat_menu"| menus
    menus -->|"7, 8.#nbsp;set_my_commands"| telegram
    classDef step fill:#fffaf3,stroke:#eadccb,stroke-width:2px,color:#3b2a1e
    classDef person fill:#5c4f42,stroke:#5c4f42,color:#fffaf3
    class messages,database,menus step
    class telegram person
```

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
---
sequenceDiagram
    accTitle: Sequence diagram, A group becomes a supergroup
    accDescr: The calls between the modules in time order, starting from messages.handle_migration
    autonumber
    participant telegram as ✈️ Telegram
    participant messages as messages.py
    participant database as database.py
    participant menus as menus.py
    rect rgb(255, 250, 243)
        telegram->>messages: handle_migration(update, context)
        messages->>database: migrate_chat(old_chat_id, new_chat_id)
        database-->>messages: result
        messages->>database: get_language(new_chat_id)
        database-->>messages: language
        opt language
            messages->>menus: set_chat_menu(context.bot, new_chat_id, language, g...)
            menus->>telegram: set_my_commands(menu(language), scope=BotCommandScope...)
            opt group
                menus->>telegram: set_my_commands(menu(language, admins=True), scope=Bo...)
            end
        end
    end
```

<details>
<summary>Call tree</summary>

- `database.migrate_chat`
- `database.get_language`
- `menus.set_chat_menu`
  - `menus.menu`

</details>

## Open the Mini App: the page

Entry point: `webhook.mini_app`

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
  flowchart:
    nodeSpacing: 50
    rankSpacing: 160
---
flowchart LR
    accTitle: Communication diagram, Open the Mini App, the page
    accDescr: The modules involved, the functions each one calls in another and what comes back, numbered as in the sequence
    miniapp_page("<b>📱 Mini App page</b>")
    webhook("<b>webhook.py</b>")
    miniapp_page -->|"1.#nbsp;mini_app"| webhook
    webhook -.->|"2.#nbsp;HTTP response"| miniapp_page
    classDef step fill:#fffaf3,stroke:#eadccb,stroke-width:2px,color:#3b2a1e
    classDef person fill:#5c4f42,stroke:#5c4f42,color:#fffaf3
    class webhook step
    class miniapp_page person
```

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
---
sequenceDiagram
    accTitle: Sequence diagram, Open the Mini App, the page
    accDescr: The calls between the modules in time order, starting from webhook.mini_app
    autonumber
    participant miniapp_page as 📱 Mini App page
    participant webhook as webhook.py
    rect rgb(255, 250, 243)
        miniapp_page->>webhook: mini_app()
        webhook-->>miniapp_page: HTTP response
    end
```

<details>
<summary>Call tree</summary>

No other function of the package.

</details>

## Mini App: data of the chat (map, seasons, records, trophies)

Entry point: `webhook.api_chat`

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
  flowchart:
    nodeSpacing: 50
    rankSpacing: 160
---
flowchart LR
    accTitle: Communication diagram, Mini App, data of the chat (map, seasons, records, trophies)
    accDescr: The modules involved, the functions each one calls in another and what comes back, numbered as in the sequence
    miniapp_page("<b>📱 Mini App page</b>")
    telegram("<b>✈️ Telegram</b>")
    webhook("<b>webhook.py</b>")
    miniapp("<b>miniapp.py</b>")
    database("<b>database.py</b>")
    conquest("<b>conquest.py</b>")
    maps("<b>maps.py</b>")
    trophies("<b>trophies.py</b>")
    analysis("<b>analysis.py</b>")
    miniapp_page -->|"1.#nbsp;api_chat"| webhook
    webhook -->|"2.#nbsp;user_of<br/>3.#nbsp;known_chats<br/>4.#nbsp;is_member<br/>12.#nbsp;conquest_data<br/>28.#nbsp;records_data<br/>36.#nbsp;recaps"| miniapp
    miniapp -->|"5.#nbsp;get_chat_member"| telegram
    miniapp -.->|"6.#nbsp;member"| webhook
    webhook -->|"7.#nbsp;get_all_user_rows<br/>9.#nbsp;get_timed_conquests<br/>11.#nbsp;get_language"| database
    database -.->|"8.#nbsp;(rows_by_user, users)<br/>10.#nbsp;timed"| webhook
    miniapp -->|"13, 26.#nbsp;holdings<br/>19.#nbsp;mention_of"| conquest
    conquest -.->|"14.#nbsp;(counts, king)<br/>27.#nbsp;(held, king)"| miniapp
    miniapp -->|"15.#nbsp;owners<br/>17.#nbsp;grouped"| maps
    maps -.->|"16.#nbsp;tiles<br/>18.#nbsp;owner_of"| miniapp
    miniapp -->|"20, 24.#nbsp;season_of<br/>22.#nbsp;season_results<br/>31.#nbsp;trophies_by_user"| trophies
    trophies -.->|"21, 25.#nbsp;season"| miniapp
    trophies -->|"23.#nbsp;holdings"| conquest
    miniapp -->|"29.#nbsp;analyze_user<br/>30.#nbsp;analyze_group<br/>40.#nbsp;recap"| analysis
    trophies -->|"32, 33.#nbsp;parse_counts<br/>35.#nbsp;consecutive_runs"| analysis
    analysis -.->|"34.#nbsp;counts"| trophies
    miniapp -->|"37.#nbsp;get_daily_counts_between<br/>39.#nbsp;get_first_days"| database
    database -.->|"38.#nbsp;daily"| miniapp
    webhook -.->|"41.#nbsp;HTTP response"| miniapp_page
    classDef step fill:#fffaf3,stroke:#eadccb,stroke-width:2px,color:#3b2a1e
    classDef person fill:#5c4f42,stroke:#5c4f42,color:#fffaf3
    class webhook,miniapp,database,conquest,maps,trophies,analysis step
    class miniapp_page,telegram person
```

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
---
sequenceDiagram
    accTitle: Sequence diagram, Mini App, data of the chat (map, seasons, records, trophies)
    accDescr: The calls between the modules in time order, starting from webhook.api_chat
    autonumber
    participant miniapp_page as 📱 Mini App page
    participant telegram as ✈️ Telegram
    participant webhook as webhook.py
    participant miniapp as miniapp.py
    participant database as database.py
    participant conquest as conquest.py
    participant maps as maps.py
    participant trophies as trophies.py
    participant analysis as analysis.py
    rect rgb(255, 250, 243)
        miniapp_page->>webhook: api_chat()
        webhook->>miniapp: user_of(request.headers.get('Authorization', ...)
        webhook->>miniapp: known_chats()
        webhook->>miniapp: is_member(application.bot, chat_id, user['id'])
        miniapp->>telegram: get_chat_member(chat_id, user_id)
        miniapp-->>webhook: member
        webhook->>database: get_all_user_rows(chat_id)
        database-->>webhook: (rows_by_user, users)
        webhook->>database: get_timed_conquests(chat_id)
        database-->>webhook: timed
        webhook->>database: get_language(chat_id)
        webhook->>miniapp: conquest_data(timed, users)
        miniapp->>conquest: holdings(history)
        conquest-->>miniapp: (counts, king)
        miniapp->>maps: owners(history)
        maps-->>miniapp: tiles
        loop for res in LEVELS
            miniapp->>maps: grouped(tiles, res)
            maps-->>miniapp: owner_of
        end
        miniapp->>conquest: mention_of(users, user_id)
        miniapp->>trophies: season_of(now_rome().date())
        trophies-->>miniapp: season
        miniapp->>trophies: season_results(timed)
        loop for (season, counts) in per_season.it...
            trophies->>conquest: holdings([(user_id, cell) for user_id, _, cell...)
        end
        loop for (i, (user_id, ts, cell)) in enume...
            miniapp->>trophies: season_of(datetime.fromtimestamp(ts, ROME_TZ).d...)
            trophies-->>miniapp: season
        end
        loop for season in sorted(last)
            miniapp->>conquest: holdings([(user_id, cell) for user_id, _, cell...)
            conquest-->>miniapp: (held, king)
        end
        webhook->>miniapp: records_data(rows_by_user, today, timed)
        miniapp->>analysis: analyze_user(rows, today)
        miniapp->>analysis: analyze_group(rows_by_user, today)
        miniapp->>trophies: trophies_by_user(rows_by_user, today, timed)
        loop for (user_id, rows) in users_rows.ite...
            trophies->>analysis: parse_counts(rows)
        end
        Note over trophies: _winners() as above
        loop for user_id in set(users_rows) | set(...
            trophies->>analysis: parse_counts(rows)
            analysis-->>trophies: counts
            trophies->>analysis: consecutive_runs(sorted(counts), counts)
        end
        webhook->>miniapp: recaps(chat_id, user_id, today)
        miniapp->>database: get_daily_counts_between(chat_id, start.isoformat(), end.isofo...)
        database-->>miniapp: daily
        miniapp->>database: get_first_days(chat_id)
        miniapp->>analysis: recap(daily, user_id, year, month, database...)
        Note over miniapp: recap_data() as above
        webhook-->>miniapp_page: HTTP response
    end
```

<details>
<summary>Call tree</summary>

- `webhook.member_chat`
  - `webhook.mini_app_user`
    - `miniapp.user_of`
  - `miniapp.known_chats`
  - `miniapp.is_member`
- `database.get_all_user_rows`
- `database.get_timed_conquests`
- `database.get_language`
- `miniapp.conquest_data`
  - `conquest.holdings`
  - `maps.owners`
  - `maps.grouped`
  - `conquest.mention_of`
  - `trophies.season_of`
  - `trophies.season_results`
    - `trophies.season_of` (see above)
    - `conquest.holdings` (see above)
  - `miniapp.season_boards`
    - `trophies.season_of` (see above)
    - `conquest.holdings` (see above)
- `miniapp.records_data`
  - `analysis.analyze_user`
    - `analysis.parse_counts`
    - `analysis.consecutive_runs`
  - `miniapp.plain`
  - `analysis.analyze_group`
    - `analysis.analyze_user` (see above)
  - `trophies.trophies_by_user`
    - `trophies.monthly_winners`
      - `analysis.parse_counts` (see above)
    - `trophies.yearly_winners`
      - `analysis.parse_counts` (see above)
    - `trophies.season_results` (see above)
    - `trophies.season_of` (see above)
    - `trophies.streak_runs`
      - `analysis.parse_counts` (see above)
      - `analysis.consecutive_runs` (see above)
- `miniapp.recaps`
  - `miniapp.plain` (see above)
  - `miniapp.recap_data`
    - `database.get_daily_counts_between`
    - `analysis.recap`
      - `analysis.consecutive_runs` (see above)
      - `analysis.period_regularity`
        - `analysis.regularity`
    - `database.get_first_days`

</details>

## Mini App: a month or a year (leaderboard, statistics)

Entry point: `webhook.api_period`

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
  flowchart:
    nodeSpacing: 50
    rankSpacing: 160
---
flowchart LR
    accTitle: Communication diagram, Mini App, a month or a year (leaderboard, statistics)
    accDescr: The modules involved, the functions each one calls in another and what comes back, numbered as in the sequence
    miniapp_page("<b>📱 Mini App page</b>")
    telegram("<b>✈️ Telegram</b>")
    webhook("<b>webhook.py</b>")
    miniapp("<b>miniapp.py</b>")
    database("<b>database.py</b>")
    analysis("<b>analysis.py</b>")
    miniapp_page -->|"1.#nbsp;api_period"| webhook
    webhook -->|"2.#nbsp;user_of<br/>3.#nbsp;known_chats<br/>4.#nbsp;is_member<br/>7.#nbsp;period_data"| miniapp
    miniapp -->|"5.#nbsp;get_chat_member"| telegram
    miniapp -.->|"6.#nbsp;member"| webhook
    miniapp -->|"8.#nbsp;get_rank<br/>10, 12.#nbsp;get_daily_counts_between<br/>16.#nbsp;get_users<br/>19.#nbsp;get_first_days"| database
    database -.->|"9.#nbsp;rank<br/>11.#nbsp;daily<br/>13.#nbsp;recent<br/>20.#nbsp;first_days"| miniapp
    miniapp -->|"14.#nbsp;forecast_totals<br/>17.#nbsp;period_statistics<br/>21.#nbsp;period_regularity"| analysis
    analysis -.->|"15.#nbsp;forecast<br/>18.#nbsp;statistics"| miniapp
    webhook -.->|"22.#nbsp;HTTP response"| miniapp_page
    classDef step fill:#fffaf3,stroke:#eadccb,stroke-width:2px,color:#3b2a1e
    classDef person fill:#5c4f42,stroke:#5c4f42,color:#fffaf3
    class webhook,miniapp,database,analysis step
    class miniapp_page,telegram person
```

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
---
sequenceDiagram
    accTitle: Sequence diagram, Mini App, a month or a year (leaderboard, statistics)
    accDescr: The calls between the modules in time order, starting from webhook.api_period
    autonumber
    participant miniapp_page as 📱 Mini App page
    participant telegram as ✈️ Telegram
    participant webhook as webhook.py
    participant miniapp as miniapp.py
    participant database as database.py
    participant analysis as analysis.py
    rect rgb(255, 250, 243)
        miniapp_page->>webhook: api_period()
        webhook->>miniapp: user_of(request.headers.get('Authorization', ...)
        webhook->>miniapp: known_chats()
        webhook->>miniapp: is_member(application.bot, chat_id, user['id'])
        miniapp->>telegram: get_chat_member(chat_id, user_id)
        miniapp-->>webhook: member
        webhook->>miniapp: period_data(chat_id, time_period, period, now_rom...)
        miniapp->>database: get_rank(chat_id, time_period, period)
        database-->>miniapp: rank
        miniapp->>database: get_daily_counts_between(chat_id, start, end)
        database-->>miniapp: daily
        opt rank and start <= today.isoformat() <...
            miniapp->>database: get_daily_counts_between(chat_id, (today - timedelta(days=FORE...)
            database-->>miniapp: recent
            miniapp->>analysis: forecast_totals({user.user_id: total for user, total ...)
            analysis-->>miniapp: forecast
        end
        miniapp->>database: get_users(chat_id)
        miniapp->>analysis: period_statistics(daily, database.get_users(chat_id), s...)
        analysis-->>miniapp: statistics
        miniapp->>database: get_first_days(chat_id)
        database-->>miniapp: first_days
        miniapp->>analysis: period_regularity(daily, first_days, s['user'].user_id,...)
        webhook-->>miniapp_page: HTTP response
    end
```

<details>
<summary>Call tree</summary>

- `webhook.member_chat`
  - `webhook.mini_app_user`
    - `miniapp.user_of`
  - `miniapp.known_chats`
  - `miniapp.is_member`
- `miniapp.period_data`
  - `database.get_rank`
  - `database.get_daily_counts_between`
  - `analysis.forecast_totals`
  - `analysis.period_statistics`
  - `database.get_users`
  - `database.get_first_days`
  - `analysis.period_regularity`
    - `analysis.regularity`

</details>

## Midnight announcement (scheduled task)

Entry point: `announce.main`

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
  flowchart:
    nodeSpacing: 50
    rankSpacing: 160
---
flowchart LR
    accTitle: Communication diagram, Midnight announcement (scheduled task)
    accDescr: The modules involved, the functions each one calls in another and what comes back, numbered as in the sequence
    task("<b>🕛 Scheduled task</b>")
    telegram("<b>✈️ Telegram</b>")
    announce("<b>announce.py</b>")
    database("<b>database.py</b>")
    trophies("<b>trophies.py</b>")
    analysis("<b>analysis.py</b>")
    chat("<b>chat.py</b>")
    conquest("<b>conquest.py</b>")
    formatting("<b>formatting.py</b>")
    miniapp("<b>miniapp.py</b>")
    task -->|"1.#nbsp;main"| announce
    announce -->|"2.#nbsp;get_language<br/>3.#nbsp;get_all_user_rows<br/>11.#nbsp;get_timed_conquests"| database
    database -.->|"4.#nbsp;(rows_by_user, users)"| announce
    announce -->|"5.#nbsp;monthly_winners<br/>7.#nbsp;yearly_winners<br/>9.#nbsp;season_of<br/>12.#nbsp;season_results"| trophies
    trophies -->|"6.#nbsp;parse_counts"| analysis
    announce -->|"8.#nbsp;escape_md"| chat
    trophies -.->|"10.#nbsp;key"| announce
    trophies -->|"13.#nbsp;holdings"| conquest
    announce -->|"14.#nbsp;format_new_period"| formatting
    announce -->|"15, 16.#nbsp;direct_link"| miniapp
    announce -->|"17.#nbsp;send_message"| telegram
    classDef step fill:#fffaf3,stroke:#eadccb,stroke-width:2px,color:#3b2a1e
    classDef person fill:#5c4f42,stroke:#5c4f42,color:#fffaf3
    class announce,database,trophies,analysis,chat,conquest,formatting,miniapp step
    class task,telegram person
```

```mermaid
---
config:
  theme: base
  themeVariables:
    fontFamily: "Nunito, Segoe UI, Roboto, sans-serif"
    primaryColor: "#fffaf3"
    primaryTextColor: "#3b2a1e"
    primaryBorderColor: "#eadccb"
    secondaryColor: "#f7ecdc"
    tertiaryColor: "#f3e4d0"
    lineColor: "#7a6a5c"
    textColor: "#3b2a1e"
    edgeLabelBackground: "#fffaf3"
    clusterBkg: "#f3e4d0"
    clusterBorder: "#cbbca9"
    titleColor: "#5c4f42"
    noteBkgColor: "#f7ecdc"
    noteTextColor: "#3b2a1e"
    actorBkg: "#fffaf3"
    actorBorder: "#5c4f42"
    actorTextColor: "#3b2a1e"
    signalColor: "#7a6a5c"
    signalTextColor: "#3b2a1e"
    labelBoxBkgColor: "#f3e4d0"
    loopTextColor: "#3b2a1e"
    sequenceNumberColor: "#fffaf3"
    xyChart:
      plotColorPalette: "#2f4f8f"
---
sequenceDiagram
    accTitle: Sequence diagram, Midnight announcement (scheduled task)
    accDescr: The calls between the modules in time order, starting from announce.main
    autonumber
    participant task as 🕛 Scheduled task
    participant telegram as ✈️ Telegram
    participant announce as announce.py
    participant database as database.py
    participant trophies as trophies.py
    participant analysis as analysis.py
    participant chat as chat.py
    participant conquest as conquest.py
    participant formatting as formatting.py
    participant miniapp as miniapp.py
    rect rgb(255, 250, 243)
        task->>announce: main(argv)
        loop for chat_id in chat_ids()
            announce->>database: get_language(chat_id)
            announce->>database: get_all_user_rows(chat_id)
            database-->>announce: (rows_by_user, users)
            announce->>trophies: monthly_winners(rows_by_user, today)
            loop for (user_id, rows) in users_rows.ite...
                trophies->>analysis: parse_counts(rows)
            end
            announce->>trophies: yearly_winners(rows_by_user, today)
            Note over trophies: _winners() as above
            announce->>chat: escape_md(user.mention)
            opt today.month % 3 == 1
                announce->>trophies: season_of(ended)
                trophies-->>announce: key
                announce->>database: get_timed_conquests(chat_id)
                announce->>trophies: season_results(database.get_timed_conquests(chat_id))
                loop for (season, counts) in per_season.it...
                    trophies->>conquest: holdings([(user_id, cell) for user_id, _, cell...)
                end
            end
            announce->>formatting: format_new_period(today, month, year, names, season)
            opt text is not None
                announce->>miniapp: direct_link(BOT_USERNAME, chat_id, 'recap')
                opt today.month == 1
                    announce->>miniapp: direct_link(BOT_USERNAME, chat_id, 'year')
                end
            end
        end
        loop for (chat_id, text, button) in messages
            announce->>telegram: send_message(chat_id, text, parse_mode='Markdown',...)
        end
    end
```

<details>
<summary>Call tree</summary>

- `announce.wait_for_midnight`
- `announce.announce`
  - `announce.chat_ids`
  - `announce.announcement`
    - `database.get_language`
    - `database.get_all_user_rows`
    - `trophies.monthly_winners`
      - `analysis.parse_counts`
    - `trophies.yearly_winners`
      - `analysis.parse_counts` (see above)
    - `chat.escape_md`
    - `trophies.season_of`
    - `trophies.season_results`
      - `trophies.season_of` (see above)
      - `conquest.holdings`
    - `database.get_timed_conquests`
    - `formatting.format_new_period`
      - `formatting.bold`
  - `announce.recap_button`
    - `miniapp.direct_link`

</details>
