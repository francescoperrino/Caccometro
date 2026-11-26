# Operations

The service scripts in `tools/` that keep the production bot running: deploy, backups, logs, releases. They run on the development machine and talk to the hosting through its HTTP API. For the first setup of the server see [deployment.md](deployment.md).

**Settings.** The scripts read `HOSTING_USERNAME` from the `.env` and the API token from the `HOSTING_API_TOKEN` environment variable (never in the `.env`, never printed). Run them from the repository root, with the virtual environment active. Backups and logs always end up in the project `backups/` and `logs/` folders, whatever folder the scripts start from, and only the owner can read them: they hold database copies and usernames.

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
flowchart TD
    accTitle: Operations
    accDescr: The local repository, the checks on GitHub, the release and the deploy to the hosting with a backup
    repo("💻 <b>1. Local repository</b><br/>development machine: code, tests")
    ci("✅ <b>2. CI on GitHub</b><br/>pytest on Python 3.10,<br/>required for the merge")
    rel("🏷️ <b>3. Release on GitHub</b><br/>signed tag vX.Y.Z")
    deploy("🚀 <b>4. deploy.py</b><br/>by hand, from the development machine")
    local[("backups/ and logs/<br/>development machine")]
    files[("Hosting<br/>code, assets, db/, logs")]
    web("🌐 <b>5. Web app on the hosting</b><br/>reloaded, home page checked")
    nightly("🌙 <b>Nightly cron, 03:30</b><br/>backup_db.py, then log_summary.py")
    maintainer("👤 <b>Maintainer</b><br/>private Telegram chat")
    repo -->|"pull request"| ci
    ci -->|"merge to main"| rel
    rel --> deploy
    deploy -->|"a. copy of the old .py files and the dbs"| local
    deploy -->|"b. upload"| files
    deploy -->|"c. reload"| web
    files -->|"db/*.db and the logs, every night"| nightly
    nightly -->|"copies and summaries"| local
    nightly -.->|"only when something is wrong"| maintainer
    classDef step fill:#fffaf3,stroke:#eadccb,stroke-width:2px,color:#3b2a1e
    classDef main fill:#2f4f8f,stroke:#2f4f8f,color:#fffaf3
    classDef person fill:#5c4f42,stroke:#5c4f42,color:#fffaf3
    classDef check fill:#f7ecdc,stroke:#e0902b,stroke-width:2px,color:#3b2a1e
    classDef detail fill:#f7ecdc,stroke:#eadccb,color:#3b2a1e
    classDef alert fill:#e0902b,stroke:#e0902b,color:#3b2a1e
    classDef stop fill:#f3e4d0,stroke:#cbbca9,stroke-dasharray:4 3,color:#7a6a5c
    class repo,ci,rel,web,nightly,local,files step
    class deploy main
    class maintainer person
```

## Deploy

`tools/deploy.py` runs only after the merge, by hand. Nothing runs on the server.

```bash
python tools/deploy.py caccometro/*.py           # dry run: shows what would change
python tools/deploy.py caccometro/*.py --yes     # real deploy
python tools/deploy.py --rollback backups/<stamp> --yes
```

With `--yes` it saves the old files and the databases in `backups/<stamp>/`, uploads the new files (fonts and emoji first, the WSGI file given with `--wsgi` last), reloads the web app, checks that the home page shows the new version and writes a line in `backups/deploys.log`. The rollback restores the saved `.py` files; it does not delete the files the deploy created.

## Nightly backup and log summary

A cron job on the development machine runs every night at 03:30 the backup and then the log summary, in the same line, so the summary runs even if the backup fails. Both write to `backups/db_backup.log`. The job runs only while the machine is on, and a skipped night is not caught up.

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
flowchart TD
    accTitle: Nightly backup and log summary
    accDescr: At 03,30 the databases are downloaded and checked, old copies are dropped, the logs are summarised and problems are sent on Telegram
    cron("🌙 <b>1. cron, 03:30</b>")
    download("🗄️ <b>2. backup_db.py</b><br/>downloads db/*.db<br/>to a new folder in backups/db/")
    healthy{"integrity_check ok, and no chat<br/>total down by more than 20%?"}
    keep("📦 <b>Keep the last 14 copies</b><br/>the first copy of each month<br/>also goes to backups/db_monthly/")
    failed("FAILED on stderr, exit code 1,<br/>Telegram alert to the maintainer<br/>(the copy stays, never monthly)")
    summary("📊 <b>3. log_summary.py</b><br/>summary of the last 24 hours<br/>to logs/ with a copy of the logs,<br/>the last 30 of each kept")
    wrong{"A lost reply, a new or repeated error,<br/>a slow update, error log lines,<br/>or a log not downloaded?"}
    alert("✈️ <b>4. One Telegram alert</b><br/>with all the reasons")
    quiet["nothing sent"]
    cron --> download --> healthy
    healthy -->|"yes"| keep --> summary
    healthy -->|"no"| failed --> summary
    summary --> wrong
    wrong -->|"yes"| alert
    wrong -->|"no"| quiet
    classDef step fill:#fffaf3,stroke:#eadccb,stroke-width:2px,color:#3b2a1e
    classDef main fill:#2f4f8f,stroke:#2f4f8f,color:#fffaf3
    classDef person fill:#5c4f42,stroke:#5c4f42,color:#fffaf3
    classDef check fill:#f7ecdc,stroke:#e0902b,stroke-width:2px,color:#3b2a1e
    classDef detail fill:#f7ecdc,stroke:#eadccb,color:#3b2a1e
    classDef alert fill:#e0902b,stroke:#e0902b,color:#3b2a1e
    classDef stop fill:#f3e4d0,stroke:#cbbca9,stroke-dasharray:4 3,color:#7a6a5c
    class cron,download,summary step
    class keep main
    class healthy,wrong check
    class failed,alert alert
    class quiet stop
```

- **Backup** (`tools/backup_db.py [--keep N]`): the alerts are sent by the development bot (`BOT_TOKEN` of the local `.env`) to the `ALERT_CHAT_ID` chat; without that variable nothing is sent. When the backup works nothing arrives.
- **Log summary** (`tools/log_summary.py`): built mostly on the line the bot writes for every update ([architecture.md](architecture.md)). It shows the updates received (private and group), retries towards Telegram, lost replies, updates ended by an error, calls refused by the webhook (403), slowest webhook call, every command with how many times it was used and its median and worst time, errors grouped by kind, exceptions with their time, restarts of the app (server log), lines of the web server error log and the other requests to the server (the Mini App ones too, grouped by page without the query), without the uptime checks. The expected kinds of error are listed in `KNOWN` in the script; the kinds already reported are in `logs/seen_kinds.txt`. The downloaded logs are kept compressed in `logs/logs_<date>.tar.gz`, the last 30 nights, like the summaries.
- **Alerts of the summary**: one Telegram message lists every reason to look: a lost reply, a kind of error never seen, an error (not a warning) outside `KNOWN` seen at least twice, a message (💩, sticker, location) slower than 5 s or a command slower than 15 s (`SLOW_MS`), any line in the web server error log.
- **Logs** (`tools/fetch_logs.py`): downloads the bot log and the web server logs into `logs/`, to look for errors by hand. The logs contain usernames: never publish them.

## Restoring a database

1. Run `tools/backup_db.py` to save the current state.
2. Pick the copy in `backups/db/` or `backups/db_monthly/` and check it with `sqlite3 <file> "PRAGMA integrity_check"`.
3. In the hosting Files tab, `db/` folder, upload the file with the same name `<chat_id>_bot_data.db`, overwriting the current one (no reload or journal files needed).
4. Try `/records` in the chat. The 💩 counted after the copy must be added back with `/add_poop`.

Tested on a copy: the restored file is sound and the totals are those of the copy.

## Releases

The version is in `caccometro/__init__.py` (`__version__`, [Semantic Versioning](https://semver.org/)): `/start`, the home page and the charts show it. A release:

1. A bump issue raises `__version__`; its pull request is merged like any other.
2. Signed tag `vX.Y.Z` and GitHub release titled `vX.Y.Z <Short name>`.
3. Deploy with `tools/deploy.py`, including `caccometro/__init__.py`.
4. `tools/bot_version.py` writes "Versione X.Y.Z" / "Version X.Y.Z" at the end of the descriptions of the production and development bots, in Italian and English (the description of each language must already be there).
5. If the commands changed, register the menus again on both bots with `tools/register_menus.py dev` and `prod` ([deployment.md](deployment.md#command-menus)). The menus already set in single chats with `/language` keep the old list until the chat sends `/language` again.
6. If the Mini App changed, take its README screenshots again: map, leaderboard, statistics and trophies, light theme, in a headless browser 390 px wide with fake data, saved as JPEG 390 px wide in `assets/screenshots/miniapp_<tab>_<en|it>.jpg`. No hook does it: it needs a browser.

The charts in the README and the infographics in `docs/images/` carry the version too: the commit of the bump redraws them (`tools/sample_charts.py` and `tools/draw_infographics.py`, see [CONTRIBUTING.md](../CONTRIBUTING.md#git-hooks)).

## Web app expiry

The free plan web app and the scheduled task expire about every month and must be extended by hand ([deployment.md](deployment.md#web-app-expiry)). `tools/deploy.py` and `tools/fetch_logs.py` print the days left and warn below 14.
