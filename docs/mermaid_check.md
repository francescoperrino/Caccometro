# Mermaid check (temporary)

Test page for the style proposed in [research/diagrams.md](research/diagrams.md): look at it on GitHub in light and dark mode. Deleted before the merge of #204.

## Mermaid version

```mermaid
info
```

## Flowchart with the style

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
---
flowchart TD
    accTitle: Path of a message
    accDescr: From Telegram to the reply: secret token, duplicate check, then a count, a command or a location.
    you("👤 <b>1. You</b><br/>write 💩, a command or a location")
    tg("✈️ <b>2. Telegram</b><br/>delivers the message")
    secret{"Right secret token?"}
    seen{"update_id new?<br/>(the last 500 are kept)"}
    kind{"What is it?"}
    poop("💩 <b>3. Count</b><br/>+1 on the day it was sent,<br/>Italian time; opens the<br/>15-minute window")
    cmd("📊 <b>3. Command</b><br/>commands.py reads the database,<br/>computes with analysis.py<br/>and trophies.py")
    loc("📍 <b>3. Location</b><br/>messages.py conquers the tile<br/>if a 💩 came in the last 15 min,<br/>zoom map from maps.py")
    reply("💬 <b>4. Reply</b><br/>text or chart in the chat language;<br/>RetryingRequest: up to 6 attempts")
    r403["403, dropped"]
    r200["200, ignored<br/>(Telegram sent it again)"]
    silent["no reply"]
    you --> tg
    tg -->|"production: webhook"| secret
    tg -->|"locally: polling"| kind
    secret -->|"no"| r403
    secret -->|"yes"| seen
    seen -->|"no"| r200
    seen -->|"yes"| kind
    kind -->|"💩 or 🚽"| poop
    kind -->|"command"| cmd
    kind -->|"location"| loc
    kind -->|"anything else"| silent
    poop --> reply
    cmd --> reply
    loc --> reply
    classDef step fill:#fffaf3,stroke:#eadccb,stroke-width:2px,color:#3b2a1e
    classDef main fill:#2f4f8f,stroke:#2f4f8f,color:#fffaf3
    classDef person fill:#5c4f42,stroke:#5c4f42,color:#fffaf3
    classDef check fill:#f7ecdc,stroke:#e0902b,stroke-width:2px,color:#3b2a1e
    classDef detail fill:#f7ecdc,stroke:#eadccb,color:#3b2a1e
    classDef alert fill:#e0902b,stroke:#e0902b,color:#3b2a1e
    classDef stop fill:#f3e4d0,stroke:#cbbca9,stroke-dasharray:4 3,color:#7a6a5c
    class you person
    class tg,cmd,loc,reply step
    class poop main
    class secret,seen,kind check
    class r403,r200,silent stop
```

## Sequence diagram with the style

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
---
sequenceDiagram
    accTitle: A poop and its conquest
    accDescr: A poop counted and the window opened, then a location within 15 minutes conquers a tile.
    autonumber
    actor you as 👤 You
    participant tg as ✈️ Telegram
    participant hook as webhook.py
    participant bot as bot.py
    participant msg as messages.py
    participant db as database.py
    participant maps as maps.py
    rect rgb(255, 250, 243)
        you->>tg: 💩
        tg->>hook: POST /webhook with the secret token
        hook->>bot: process_update
        bot->>msg: handle_message
        msg->>db: add_count: +1 on the day it was sent
        msg->>db: open_conquest_window: time of this 💩
        msg->>tg: reply: funny sentence, 💩 today, send your location
        hook-->>tg: 200
        you->>tg: 📍 location, within 15 minutes
        tg->>hook: POST /webhook
        hook->>bot: process_update
        bot->>msg: handle_message
        msg->>db: conquer: one transaction checks and uses up the window, saves the conquest
        db-->>msg: previous owner and all the conquests of the chat
        msg->>maps: zoom_map: tiles around the conquest
        maps-->>msg: JPEG, or None without the map tiles
        msg->>tg: photo with 🚩, 🏠 or ⚔️, and 👑 if the king changed
        hook-->>tg: 200
    end
```
