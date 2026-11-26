"""The one style of every Mermaid diagram of the documentation (#204, docs/research/diagrams.md).

The generators in tools/ import it; tests/test_docs.py checks that every Mermaid block of the repository starts with
FRONTMATTER, has accTitle and accDescr, and uses only the CLASSDEFS. A hand-written diagram copies them from here.
Text always sits on a light fill and lines use #7a6a5c, so the diagrams read in GitHub's light and dark mode.
"""
FRONTMATTER = """---
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
"""

# person: people and outside systems; main: the step that matters; step: a step or a module; check: a question;
# detail: a side note; alert: a warning; stop: an end without a reply
CLASSDEFS = [
    "classDef step fill:#fffaf3,stroke:#eadccb,stroke-width:2px,color:#3b2a1e",
    "classDef main fill:#2f4f8f,stroke:#2f4f8f,color:#fffaf3",
    "classDef person fill:#5c4f42,stroke:#5c4f42,color:#fffaf3",
    "classDef check fill:#f7ecdc,stroke:#e0902b,stroke-width:2px,color:#3b2a1e",
    "classDef detail fill:#f7ecdc,stroke:#eadccb,color:#3b2a1e",
    "classDef alert fill:#e0902b,stroke:#e0902b,color:#3b2a1e",
    "classDef stop fill:#f3e4d0,stroke:#cbbca9,stroke-dasharray:4 3,color:#7a6a5c",
]
SEQUENCE_GROUND = "rect rgb(255, 250, 243)"   # the cream ground under the messages of a sequence diagram


def accessible(title, description):
    """The accTitle and accDescr lines that follow the diagram type, for screen readers."""
    clean = [" ".join(text.replace(":", ",").split()) for text in (title, description)]
    return [f"    accTitle: {clean[0]}", f"    accDescr: {clean[1]}"]
