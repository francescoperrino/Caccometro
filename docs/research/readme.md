# README structure

How the README of Caccometro (#204) should be built: what sits at the top, in which order the sections come, and what moves to other files. Most visitors land on the repository page from a link and decide in a few seconds whether the bot is for their group; a few want to contribute, and one person runs it. The README serves the first group and points the other two elsewhere.

## What the evidence says

**What a README is for.** GitHub says a README tells people "why your project is useful, what they can do with your project, and how they can use it", and keeps only what is needed to start using and contributing; longer documentation belongs elsewhere ([GitHub Docs, about READMEs](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes)). The Open Source Guides reduce it to four questions: what does it do, why is it useful, how do I get started, where do I get help ([Open Source Guides, starting a project](https://opensource.guide/starting-a-project/)). The same guide sends contributors to a separate CONTRIBUTING file linked from the README.

**A standard order.** The standard-readme spec fixes the order: title, banner, badges, short description, long description, table of contents, then background, install, usage, extra sections, API, maintainers, thanks, contributing, license ([standard-readme spec](https://github.com/RichardLitt/standard-readme/blob/main/spec.md)). The short description must be under 120 characters, on its own line, and match the GitHub description; the banner sits right after the title and must be a local image; badges have no heading, and static badges should be local files to avoid tracking requests; a table of contents is required past 100 lines. Make a README proposes nearly the same list (name, description, badges, visuals, installation, usage, support, roadmap, contributing, authors, license, project status) and says GIFs are more common than real videos ([makeareadme.com](https://www.makeareadme.com/)).

**What well-known projects put first.** Read in November 2026:

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot): logo, 14 badges, a one-line joke, links to its Telegram group and channel; then Introduction, Installing, Working with PTB, Contributing, License. Everything else lives in the docs and wiki.
- [grammY](https://github.com/grammyjs/grammY): logo, tagline, 3 badges (Bot API version, npm, contributors), a row of links (docs, reference, chat, news), then a quickstart with code, resources, contribution guide, contributors.
- [Excalidraw](https://github.com/excalidraw/excalidraw): a cover image with a light and a dark version via `<picture>`, a row of links, a two-line pitch, 6 badges, a product screenshot; then Features, the hosted app, Quick start, Contributing, Integrations, Sponsors.
- [Hoppscotch](https://github.com/hoppscotch/hoppscotch): logo, name, tagline, 4 badges, a light and dark banner via `<picture>`, a link to the docs; then a long Features list where each feature folds its details into `<details>`, then Demo, Usage, Developing, Contributing, License.
- [Immich](https://github.com/immich-app/immich): 2 badges, logo, one-line pitch, one wide screenshot of the app, then a row of 21 language links; then Links, Demo, Features, Translations, Contributors.
- [Home Assistant](https://github.com/home-assistant/core): name with one badge, a three-line pitch, a link to the website for demo, install and docs, then two screenshots. The README is about 30 lines; all the rest is on the website.
- [Bun](https://github.com/oven-sh/bun): logo, name, 3 badges, a row of links (docs, chat, issues, roadmap), then What is Bun, Install, Quick links, Guides, Contributing, License.
- [Deno](https://github.com/denoland/deno): name, 5 badges, logo floated right, a short pitch with a docs link, then Installation, first program, resources, Contributing.
- [ripgrep](https://github.com/BurntSushi/ripgrep): a paragraph that says what it does, 3 badges, license, quick links to the guide and FAQ in other files, a screenshot, then why and why not use it, installation, building, tests.
- [bat](https://github.com/sharkdp/bat): a logo, 3 badges, a short pitch, then one screenshot per feature before How to use and Installation.

The pattern is steady: name, a pitch of one or two lines and one picture of the product come before any heading; install or "how to start" comes next; contributors get a link, not a chapter. Apps (Excalidraw, Immich, Home Assistant) lead with a screenshot; libraries (grammY, Bun) lead with code.

**Badges.** Counts go from 1 (Home Assistant) to 14 (python-telegram-bot); most projects show 2 to 6. The common ones are build status, version or package, license and a chat link. A bot that is not a package has no version or download badge to show.

**Images.** GitHub supports `<picture>` and documents the light and dark pattern with `prefers-color-scheme`, a fallback `<img>` and alt text ([GitHub Docs, quickstart for writing](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/quickstart-for-writing-on-github); [basic formatting](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax)). Images in the repository should use relative paths, which follow the branch and work in clones (same pages). Excalidraw and Hoppscotch use `<picture>` for their banner only, not for every screenshot.

**Videos.** GitHub accepts `.mp4`, `.mov` and `.webm` uploads in issues, pull requests and comments, 10 MB on a free plan, H.264 recommended ([GitHub Docs, attaching files](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/attaching-files)). No GitHub page we found says that a video file stored in the repository plays inside a README, and none of the ten READMEs above embeds a video. Treat README video as undocumented; a GIF works everywhere, images and GIFs up to 10 MB as uploads.

**Collapsed sections.** `<details>` with a `<summary>` hides any Markdown until clicked; `open` shows it expanded ([GitHub Docs, collapsed sections](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/organizing-information-with-collapsed-sections)). Hoppscotch uses it to keep a long feature list scannable.

**Navigation and length.** GitHub builds an outline from the headings of every rendered Markdown file, and every heading gets an anchor; changing a heading breaks links to it ([basic formatting](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax)). A README is cut past 500 KiB ([about READMEs](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes)).

**Translations.** standard-readme names translated files `README.<lang>.md` and keeps `README.md` for English ([spec](https://github.com/RichardLitt/standard-readme/blob/main/spec.md)). Immich puts a row of language links right under its hero screenshot; ripgrep lists translations in a section at the end.

## What we chose and why

Three readers: people who use the bot (the README), contributors ([CONTRIBUTING.md](../../CONTRIBUTING.md) and [architecture](../architecture.md)) and the maintainer ([deployment](../deployment.md) and [operations](../operations.md)). Both READMEs follow this order:

| # | Part | Why |
| --- | --- | --- |
| 1 | Demo GIF, name, one-line pitch, language switcher | Apps lead with a picture of the product. The GIF is the avatar in motion, so a still avatar above it would repeat it. |
| 2 | Three badges: tests, latest release, license | Enough to show the project is alive. The release badge stands in for the package badge a bot does not have. |
| 3 | An "Add to your group" button (`t.me/<bot>?startgroup`) | Adding the bot is the one thing a visitor wants to do; a plain Telegram badge would only open the chat. |
| 4 | Feature list | Answers "what does it do" in one screen. |
| 5 | Mini App screenshots, four in a row | The part people cannot imagine from the commands. Light theme, JPEG, 390 px. |
| 6 | Table of contents | The README stays over 100 lines, and the GitHub outline is easy to miss. |
| 7 | How to use it | "How do I get started", the second question of every guide. |
| 8 | Commands: one short row each, details and date formats in `<details>` | The table is the reference users come back for; `tests/test_docs.py` still finds every command at the start of a row. |
| 9 | Charts and conquest maps | What the replies look like. |
| 10 | Rules of records, trophies, conquests and old history, in `<details>` | Detail on demand, never steps a new user needs. |
| 11 | Privacy | A group must know what is stored before adding the bot. |
| 12 | Documentation table, license, OpenStreetMap credit | Where contributors and the maintainer go next. [replies.md](../replies.md) comes first: it is the one document users read too. |

Other choices:

- **Pitch.** "Who poops the most? ..." stays under 120 characters. The GitHub description is longer and lists the features; standard-readme asks for the two to match, which is left for the next release.
- **Video.** A GIF of about 400 px and 2 MB, since GitHub does not document video stored in the repository.
- **Dark screenshots.** None: the projects above use `<picture>` only for a banner, and a second set doubles the work at every Mini App change.
- **Menus and replies.** The full English and Italian menu table is in [deployment](../deployment.md#command-menus); every reply of the bot is in [replies.md](../replies.md), written from the code.
- **Language switcher.** `README.md` in English and `README.it.md` in Italian, with the switcher under the pitch. Both files keep the same order, so a change is easy to copy across.
