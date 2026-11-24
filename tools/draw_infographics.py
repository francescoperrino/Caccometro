"""Draw the infographics of the documentation in docs/images/ (#194), all in the same vertical style.

Each picture: a title, a sentence, three highlights, then one card per step (icon, number,
title, up to three short lines) joined by arrows, and a closing line when the flow repeats.
The colours are those of the bot charts and, like them, the pictures carry the bot version. Run it after changing a flow below; it warns when a
line may not fit its card.

    python tools/draw_infographics.py
"""
import sys
from pathlib import Path
from xml.sax.saxutils import escape

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from caccometro import __version__  # noqa: E402

OUT = REPO / "docs" / "images"

INK, MUTED, PAGE, CARD, LINE = "#3b2a1e", "#7a6a5c", "#f3e4d0", "#fffaf3", "#eadccb"
ORANGE, DENIM, BROWN, SKY = "#e0902b", "#2f4f8f", "#5c4f42", "#2aa3e0"
FONT = "Nunito, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
WIDTH, LEFT, TEXT_X = 900, 40, 190

# White glyphs drawn around (0, 0), about 48 px wide, on a coloured circle.
W = f'fill="{CARD}"'
S = f'fill="none" stroke="{CARD}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"'
ICONS = {
    "person": f'<circle cx="0" cy="-9" r="10" {W}/><path d="M-19 21 a19 19 0 0 1 38 0 z" {W}/>',
    "people": f'<circle cx="-8" cy="-8" r="7" {W}/><circle cx="10" cy="-8" r="7" {W}/>'
              f'<path d="M-22 16 a14 13 0 0 1 28 0 z M-4 16 a14 13 0 0 1 28 0 z" {W}/>',
    "telegram": f'<path d="M-21 0 l40 -17 l-8 36 l-11 -10 l-7 8 l-1 -12 z" {W}/>',
    "server": f'<rect x="-18" y="-19" width="36" height="16" rx="4" {S}/><rect x="-18" y="3" width="36" height="16" rx="4" {S}/>'
              f'<circle cx="-9" cy="-11" r="2.5" {W}/><circle cx="-9" cy="11" r="2.5" {W}/>',
    "phone": f'<rect x="-13" y="-21" width="26" height="42" rx="5" {S}/><circle cx="0" cy="14" r="2.5" {W}/>',
    "moon": f'<path d="M6 -19 a19 19 0 1 0 13 30 a15 15 0 0 1 -13 -30 z" {W}/>',
    "lock": f'<rect x="-14" y="-3" width="28" height="22" rx="4" {S}/><path d="M-8 -3 v-7 a8 8 0 0 1 16 0 v7" {S}/>',
    "shield": f'<path d="M0 -21 l17 6 v9 c0 13 -8 21 -17 26 c-9 -5 -17 -13 -17 -26 v-9 z" {S}/><path d="M-7 1 l5 5 l9 -10" {S}/>',
    "pin": f'<path d="M0 -21 a13 13 0 0 1 13 13 c0 11 -13 26 -13 26 s-13 -15 -13 -26 a13 13 0 0 1 13 -13 z" {W}/>'
           f'<circle cx="0" cy="-8" r="5" fill="{DENIM}"/>',
    "chart": f'<path d="M-18 18 h36" {S}/><rect x="-15" y="-2" width="8" height="16" rx="2" {W}/>'
             f'<rect x="-4" y="-18" width="8" height="32" rx="2" {W}/><rect x="7" y="-9" width="8" height="23" rx="2" {W}/>',
    "calendar": f'<rect x="-18" y="-14" width="36" height="32" rx="4" {S}/><path d="M-18 -4 h36 M-9 -20 v8 M9 -20 v8" {S}/>',
    "globe": f'<circle cx="0" cy="0" r="19" {S}/><path d="M-19 0 h38 M0 -19 c-11 11 -11 27 0 38 c11 -11 11 -27 0 -38" {S}/>',
    "poop": '<text x="0" y="15" text-anchor="middle" font-size="40">💩</text>',
}


def icon(name, x, y, r, colour):
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="{colour}"/>'
            f'<g transform="translate({x},{y}) scale({r / 46:.3f})">{ICONS[name]}</g>')


def text(x, y, value, size, colour=INK, weight=400, anchor="start"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{colour}" '
            f'text-anchor="{anchor}">{escape(value)}</text>')


def fits(value, size, room, where, bold=False):
    """Warn when a line may overflow: about 0.58 em a character (DejaVu, the widest fallback)."""
    if len(value) * size * (0.62 if bold else 0.58) > room:
        print(f"  {where}: '{value}' may not fit in {room} px")


def draw(name, title, sentence, highlights, steps, closing=None):
    room = WIDTH - LEFT - TEXT_X - 20
    out, y = [text(LEFT, 70, title, 38, INK, 800)], 70
    fits(title, 38, WIDTH - 2 * LEFT, name, bold=True)
    for line in sentence:
        y += 30
        out.append(text(LEFT, y, line, 19, MUTED))
        fits(line, 19, WIDTH - 2 * LEFT, name)
    y += 26
    for glyph, head, body in highlights:
        y += 38
        out += [icon(glyph, LEFT + 18, y - 6, 16, DENIM), text(LEFT + 48, y, head, 17, INK, 800), text(370, y, body, 16, MUTED)]
        fits(head, 17, 370 - LEFT - 56, name, bold=True)
        fits(body, 16, WIDTH - 370 - LEFT, name)
    y += 40
    for i, step in enumerate(steps):
        height = max(110, 70 + 24 * len(step["lines"]))
        middle = y + height / 2
        out += [f'<rect x="{LEFT}" y="{y}" width="{WIDTH - 2 * LEFT}" height="{height}" rx="20" fill="{CARD}" stroke="{LINE}" stroke-width="1.5"/>',
                icon(step["icon"], LEFT + 76, middle, 40, step.get("colour", DENIM)),
                f'<circle cx="{LEFT + 110}" cy="{middle - 32}" r="16" fill="{ORANGE}" stroke="{CARD}" stroke-width="3"/>',
                text(LEFT + 110, middle - 26, str(i + 1), 16, CARD, 800, "middle"),
                text(TEXT_X, y + 44, step["title"], 23, INK, 800)]
        fits(step["title"], 23, room, name, bold=True)
        for j, line in enumerate(step["lines"]):
            out.append(text(TEXT_X, y + 76 + 24 * j, line, 18, MUTED))
            fits(line, 18, room, name)
        y += height
        if i < len(steps) - 1:
            out.append(f'<path d="M{LEFT + 76} {y + 4} v18" stroke="{INK}" stroke-width="3" marker-end="url(#arrow)"/>')
            y += 30
    if closing:
        y += 46
        out += [f'<g transform="translate({LEFT + 18},{y - 6})"><path d="M-7 -5 a9 9 0 1 1 -2 7" fill="none" stroke="{INK}" stroke-width="2.5" stroke-linecap="round"/>'
                f'<path d="M-11 -9 l4 4 l5 -3" fill="none" stroke="{INK}" stroke-width="2.5" stroke-linecap="round"/></g>',
                text(LEFT + 42, y, closing, 18, INK, 800)]
        fits(closing, 18, WIDTH - 2 * LEFT - 42, name, bold=True)
    height = y + 40
    # the version, as under the bot charts: the pre-commit hook redraws the pictures when it changes
    out.append(text(WIDTH - LEFT, height - 14, f"Caccometro v{__version__}", 13, MUTED, anchor="end"))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" width="{WIDTH}" height="{height}" font-family="{FONT}">'
           f'<title>{escape(title)}</title>'
           f'<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" orient="auto">'
           f'<path d="M0 0 L10 5 L0 10 z" fill="{INK}"/></marker></defs>'
           f'<rect width="{WIDTH}" height="{height}" rx="24" fill="{PAGE}"/>' + "".join(out) + "</svg>\n")
    (OUT / f"{name}.svg").write_text(svg, encoding="utf-8")
    print(f"docs/images/{name}.svg")


PICTURES = [
    ("how_the_bot_works", "How Caccometro works",
     ["Friends send 💩 in the group, the bot keeps the count and",
      "turns it into leaderboards, statistics, trophies and a map."],
     [("lock", "No message text stored", "Only who, which day and how many."),
      ("globe", "Italian and English", "An admin switches with /language."),
      ("calendar", "A new race every month", "And a season every three months.")],
     [{"title": "You", "icon": "person", "colour": BROWN, "lines": ["Send 💩 or 🚽 (a sticker too) when it is done."]},
      {"title": "The bot counts", "icon": "poop", "colour": ORANGE, "lines": ["+1 on today, with a funny reply that changes", "with the hour and with the count of the day."]},
      {"title": "Conquer", "icon": "pin", "lines": ["Send a location within 15 minutes:", "the hexagon on the map is yours."]},
      {"title": "Compare", "icon": "chart", "lines": ["Leaderboards, statistics, records, trophies", "and charts; /app opens them all in one place."]},
      {"title": "Midnight", "icon": "moon", "lines": ["On the 1st of the month the bot announces", "the 💩 of the month."]}],
     "A new month: the race starts again."),
    ("come_funziona_il_bot", "Come funziona il Caccometro",
     ["Gli amici mandano 💩 nel gruppo, il bot tiene il conto e lo",
      "trasforma in classifiche, statistiche, trofei e una mappa."],
     [("lock", "Nessun testo salvato", "Solo chi, che giorno e quante."),
      ("globe", "Italiano e inglese", "Un admin cambia lingua con /lingua."),
      ("calendar", "Ogni mese una gara nuova", "E una stagione ogni tre mesi.")],
     [{"title": "Tu", "icon": "person", "colour": BROWN, "lines": ["Mandi 💩 o 🚽 (anche come sticker) quando hai fatto."]},
      {"title": "Il bot conta", "icon": "poop", "colour": ORANGE, "lines": ["+1 su oggi, con una risposta buffa che cambia", "con l'ora e con il conto del giorno."]},
      {"title": "Conquista", "icon": "pin", "lines": ["Manda la posizione entro 15 minuti:", "l'esagono sulla mappa è tuo."]},
      {"title": "Confronta", "icon": "chart", "lines": ["Classifiche, statistiche, record, trofei e grafici;", "/app li apre tutti in un posto solo."]},
      {"title": "Mezzanotte", "icon": "moon", "lines": ["Il primo del mese il bot annuncia", "il 💩 del mese."]}],
     "Un mese nuovo: la gara riparte."),
    ("mini_app_flow", "How the Mini App works",
     ["A member opens it from Telegram. The server checks who they are",
      "and sends only the data of their chat. The phone draws everything."],
     [("lock", "Signed identity", "No Telegram signature, no data."),
      ("people", "Members only", "Who left the group gets nothing."),
      ("pin", "No locations", "Only hexagons leave the server.")],
     [{"title": "You", "icon": "person", "colour": BROWN, "lines": ["Tap the menu button of the private chat,", "or /app in a group."]},
      {"title": "Telegram", "icon": "telegram", "colour": SKY, "lines": ["Opens the page /app with a signed ticket:", "who you are and from which chat."]},
      {"title": "Checks", "icon": "shield", "lines": ["Signature younger than 24 hours (else 401),", "a chat with a database (else 404),", "still a member of the group (else 403)."]},
      {"title": "Data", "icon": "server", "lines": ["/api/chat: map, seasons, records, trophies.", "/api/period: leaderboard and statistics", "of a month or a year, as the commands."]},
      {"title": "Your screen", "icon": "phone", "lines": ["Map, podium, lists and charts", "drawn on the phone."]}],
     "Another month or year? Only /api/period is asked again."),
]

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for picture in PICTURES:
        draw(*picture)
