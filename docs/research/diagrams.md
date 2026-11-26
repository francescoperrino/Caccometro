# Documentation diagrams

Which views of the code the documentation of Caccometro (#204) should show, in which notation, how they look on GitHub and which ones are written by the code. Three kinds of readers look at them: people in a group, who see the infographics in the README; contributors, who need a map of the modules and of what happens when a message arrives; the maintainer, who runs the bot. A view that nobody reads is a view that goes stale.

## What the evidence says

**Structure and behaviour.** UML 2.5.1 splits its 14 diagram kinds into structure diagrams, "irrespective of time" (class, component, package, deployment and others), and behaviour diagrams (activity, use case, state machine, and the interactions: sequence, communication, interaction overview, timing) ([UML 2.5.1, Annex A](https://www.omg.org/spec/UML/2.5.1/PDF)). The behaviour of a use case "can be described by a set of Behaviors ... such as Interactions, Activities, and StateMachines" ([UML 2.5.1, 18.1.3](https://www.omg.org/spec/UML/2.5.1/PDF)): a sequence and a communication diagram per command are UML Interactions of a use case; "use case realization" is the older Rational Unified Process name. `alt` is a choice where at most one guarded branch runs, `opt` a branch that runs or not, `break` ends the enclosing fragment, `loop` repeats, `par` interleaves ([UML 2.5.1, 17.6.3](https://www.omg.org/spec/UML/2.5.1/PDF)).

**Draw the top, generate the bottom.** C4 has four levels (context, container, component, code) plus deployment and dynamic diagrams, and "the system context and container diagrams are sufficient for most software development teams" ([C4, diagrams](https://c4model.com/diagrams)). A container is something that runs or stores data: a server-side web app and a JavaScript app in a browser are two containers; modules inside an app are not ([C4, container](https://c4model.com/abstractions/container)). Component diagrams should be automated for long-lived documentation ([C4, component](https://c4model.com/diagrams/component)) and the code level "automatically generated using tooling", never drawn by hand ([C4, code](https://c4model.com/diagrams/code)). Dynamic diagrams, based on the UML communication diagram, are for the few interesting interactions ([C4, dynamic](https://c4model.com/diagrams/dynamic)). Every diagram needs a title, a legend, the type and technology of each box, and labelled one-way lines ([C4, notation](https://c4model.com/diagrams/notation)).

**Relevance over completeness.** arc42's context section is the C4 context diagram and its building block level 1 is the container diagram ([C4, FAQ](https://c4model.com/faq)). Level 1 is mandatory and may be a table of names and responsibilities; leave out the "normal, simple, boring" parts ([arc42, section 5](https://docs.arc42.org/section-5/)). "Document only a few runtime scenarios!": important use cases, external interfaces, start-up and errors ([arc42, section 6](https://docs.arc42.org/section-6/)). The deployment view maps the software onto the infrastructure ([arc42, section 7](https://docs.arc42.org/section-7/)).

**Small systems drop views.** Kruchten's 4+1: views "that are useless can be omitted", the physical view with one processor, the process view with one process, and logical and development views can merge; "the scenarios are useful in all circumstances" ([Kruchten 1995](https://arxiv.org/pdf/2006.04975)). The bot is that case: one uWSGI process, one hosting node.

**Standards add words, not diagrams.** ISO/IEC/IEEE 42010:2022 defines view, viewpoint, concern, stakeholder and correspondence (consistency, traceability between elements), and leaves the notation to each viewpoint ([42010:2022 preview](https://cdn.standards.iteh.ai/samples/74393/fc7b7f103d8446a4b87a3261e31370d3/ISO-IEC-IEEE-42010-2022.pdf)). Automotive SPICE 4.0 asks for static and dynamic aspects of the architecture (SWE.2) and of the detailed design (SWE.3), consistent and traceable, in natural language or UML, without naming diagram types; "traceability alone ... does not necessarily mean that the information is consistent" ([ASPICE PAM 4.0](https://vda-qmc.de/wp-content/uploads/2023/12/Automotive-SPICE-PAM-v40.pdf)).

**Only Mermaid renders on GitHub.** GitHub renders `mermaid`, `geojson`, `topojson` and `stl` blocks; a block with `info` shows the Mermaid version; nothing is said about themes, dark mode or limits ([GitHub Docs, diagrams](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams)). PlantUML ([plantuml.com](https://plantuml.com/)), Structurizr ([docs](https://docs.structurizr.com/)), LikeC4 ([CLI](https://likec4.dev/tooling/cli/)), D2 ([d2](https://github.com/terrastruct/d2)) and Graphviz would be committed images, built with Java, Node or Go. Structurizr and LikeC4 keep one model behind many views and can export Mermaid.

**Generators see structure, not behaviour.** pydeps draws imports through Graphviz ([pydeps](https://pypi.org/project/pydeps/)), pyreverse writes class and package diagrams, also as Mermaid ([pyreverse](https://pylint.readthedocs.io/en/latest/additional_tools/pyreverse/index.html)), code2flow call graphs, warning that a perfect call graph of a dynamic language is impossible ([code2flow](https://github.com/scottrogowski/code2flow)). None draws use-case sequences. import-linter turns import rules into tests ([import-linter](https://import-linter.readthedocs.io/en/stable/)); mermaid-cli renders every block of a Markdown file, which catches syntax errors, at the price of Node and Chromium ([mermaid-cli](https://github.com/mermaid-js/mermaid-cli)).

**Styling.** Only the `base` theme takes `themeVariables`, in hex only ([Mermaid theming](https://mermaid.js.org/config/theming.html)); they go in YAML frontmatter under `config:`, since `%%{init}%%` is deprecated from v10.5.0 ([Mermaid directives](https://mermaid.js.org/config/directives.html)). Flowcharts and state diagrams take `classDef`; sequence diagrams do not, and use the actor and signal variables and `rect rgb(...)` blocks ([sequence diagrams](https://mermaid.js.org/syntax/sequenceDiagram.html)). Colours are fixed at render time, so one diagram cannot follow both modes ([theming](https://mermaid.js.org/config/theming.html)); GitHub users report flowcharts unreadable in dark mode ([community #35733](https://github.com/orgs/community/discussions/35733)). `click` links are off under the strict security level ([flowchart](https://mermaid.js.org/syntax/flowchart.html)).

**Accessibility.** A complex image needs a short alternative and a long description in the page ([W3C WAI](https://www.w3.org/WAI/tutorials/images/complex/)). Mermaid's `accTitle` and `accDescr` become the SVG `<title>` and `<desc>` ([Mermaid accessibility](https://mermaid.js.org/config/accessibility.html)); whether GitHub keeps them is not documented. Alt text stays under 155 characters, and new information goes in the text, never only in a figure ([Google style, images](https://developers.google.com/style/images)).

**What well-known projects do.** GitLab: two component overviews and two sequence diagrams of `git fetch`, all Mermaid ([GitLab](https://docs.gitlab.com/development/architecture/)). python-telegram-bot: one Mermaid flowchart and a paragraph per part ([PTB wiki](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Architecture)). rust-analyzer: one image and a long codemap with "Architecture Invariant" notes ([rust-analyzer](https://github.com/rust-lang/rust-analyzer/blob/master/docs/book/src/contributing/architecture.md)); matklad says to keep it short, state invariants and not try to sync it with the code ([ARCHITECTURE.md](https://matklad.github.io/2021/02/06/ARCHITECTURE.md.html)). Immich ships an exported image ([Immich](https://docs.immich.app/developer/architecture)). None of those checked has a full C4 set or generates diagrams from code in CI.

## What we chose and why

Today the repository already goes past what C4 and arc42 ask at the bottom (modules, functions and use cases are written by the code and tested) and is missing the top (context and containers).

| View | Framework | Where | Exists | Generated, tested |
| --- | --- | --- | --- | --- |
| Views and readers | 42010 (view, concern, stakeholder) | `architecture.md`, top | No: add | Hand-written |
| System context | C4 level 1, arc42 §3 | `architecture.md` | No: add | Hand-written |
| Containers | C4 level 2, arc42 §5 level 1 | `architecture.md` | Partly, inside the production diagram of `deployment.md` | Hand-written |
| Module codemap | arc42 §5 black boxes, matklad | `architecture.md`, Modules | Yes | Hand-written |
| Module dependencies | C4 component, UML package, 4+1 development, SWE.2 static | `architecture.md` | Yes | `draw_dependencies.py`, test |
| Functions and classes | C4 code, SWE.3 static | `functions.md` | Yes | `write_functions.py`, test, pre-commit |
| Data model | UML class (ER), arc42 §8 | `architecture.md`, Database | Yes | Hand-written, not tested |
| Deployment | C4 deployment, arc42 §7, UML deployment | `deployment.md`, Production | Yes | Hand-written |
| Flows: message, Mini App, announcement, operations | UML activity, arc42 §6 | `architecture.md`, `deployment.md`, `operations.md`, `CONTRIBUTING.md` | Yes | Hand-written |
| A 💩 and its conquest | C4 dynamic, 4+1 scenario, UML sequence | `architecture.md` | Yes | Hand-written |
| Use cases: communication, sequence, call tree | UML interactions, C4 dynamic, SWE.3 dynamic | `use_cases.md` | Yes | `write_use_cases.py`, test, pre-commit |
| Conquest window | UML state machine | `architecture.md` | Yes | Hand-written |
| End-user infographics | Google style, Diátaxis how-to | `docs/images/`, README | Yes | `draw_infographics.py`, pre-commit; text not tested |

**Add.**

- A table of the views at the top of `architecture.md`: reader, question answered, notation, file. It is the whole 42010 paperwork this project needs.
- A system context diagram: people in a group and the maintainer; Caccometro; Telegram (Bot API, and the app that runs the Mini App); the hosting; OpenStreetMap tiles; the CDN of Leaflet and Chart.js; GitHub with its CI. One labelled arrow each, with the protocol.
- A container diagram: the webhook app (Flask, one uWSGI process, Python 3.10), polling mode for development (`python -m caccometro`), the announcement task (22:00 UTC), the Mini App page (HTML and JavaScript inside Telegram), one SQLite file per chat, `tile_cache/`, the log. The production diagram in `deployment.md` then shows only where they run.
- The invariants of the dependency paragraph ("rules and storage know nothing of Telegram") as a test on the graph `draw_dependencies.py` already builds, instead of import-linter, a dependency for one rule.
- A test that every table and column of the database diagram exists in the schema of `database.py`.

**Keep, do not add.** One sequence and one communication diagram per command stay in `use_cases.md`, since they cost nothing to keep; `architecture.md` keeps only the hand-picked scenarios, as arc42 asks. No class diagrams (`functions.md` covers the code level), no interaction overview or timing diagrams, no `par` (one process, no threads), no `click` links, no full arc42 template (decisions and risks live in the issues).

**Do not adopt** PlantUML, Structurizr, LikeC4, D2 or Graphviz: none renders on GitHub, all add a toolchain, and none reads Python. mermaid-cli in CI is the one add-on worth reconsidering if a broken block ever reaches `main`.

**One style for every Mermaid block.** Every block starts with the same frontmatter; flowcharts and state diagrams keep the seven `classDef` lines of `architecture.md`. The header lives in one constant that the three generators write and `tests/test_docs.py` checks in every block of the repository, together with `accTitle` and `accDescr`. The generators replace `%%{init}%%` with the same frontmatter, adding their `flowchart` spacing.

```yaml
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
```

- **Classes.** Brown `person` for people, denim `main` for the step that matters, cream `step` for a step or module, orange border `check` for a question, dashed `stop` for an end without reply, `alert` for a warning. One legend line under the first diagram of each page says so, as C4 asks.
- **Dark mode.** The ink `#3b2a1e` is 13:1 on cream but 1.4:1 on GitHub's dark page, so text always sits on a fill: nodes, edge labels on the `edgeLabelBackground` chip, subgraph titles on `clusterBkg`. `#7a6a5c` is the only colour of the palette readable on both pages (5.2:1 on white, 3.6:1 on dark) and is used for every line and arrow. `alert` writes `#3b2a1e` instead of cream: cream on orange is 2.5:1, ink on orange 5.3:1.
- **Sequence diagrams.** No `classDef`: they get the actor and signal variables, and their messages sit in one `rect rgb(255, 250, 243)` block, so the text has a cream ground in dark mode too. `autonumber` stays, as in the flowcharts' numbered cards.
- **Infographics** keep their own background and `<title>`, so they read in both modes. Their alt text stays under 155 characters (the README one is longer) and the steps are also in the README text.

**Checked on GitHub (November 2026).** A test page showed that GitHub runs Mermaid 12.3.0 and applies the frontmatter: the `base` theme, the palette, the `classDef` lines and the cream ground of the sequence diagrams, legible in light and dark mode. The one thing that disappeared in dark mode was the label under an `actor` stick figure, which has no fill: sequence diagrams use `participant` boxes only. The style lives in `tools/mermaid_style.py` and `tests/test_docs.py` checks every block.

**Hand-written or generated.**

- **Generate** what mirrors the code and changes on ordinary commits: imports, functions, calls, replies. The output is byte-stable, says "do not edit by hand", is checked by a test and redrawn by the pre-commit hook.
- **Hand-write** what explains intent across processes, updates or systems, or a decision: context, containers, deployment, scenarios, states, data model. At most one diagram per question; the paragraph above it names the code it reflects (file, function, table) and says the same in words; it changes in the same pull request as that code; a test checks its names where that is cheap.
- **Never both** for the same thing: when a hand-written diagram starts to repeat a generated one, link to the generated one instead.
