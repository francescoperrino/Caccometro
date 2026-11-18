"""The documentation must match the code: commands, modules, variables and file names (#106, #143).

Diagrams and prose cannot be tested; they are reviewed with the checklist of the commit workflow.
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DOCS = sorted([ROOT / "README.md", ROOT / "CONTRIBUTING.md", ROOT / "SECURITY.md", *(ROOT / "docs").glob("*.md")])
ADMIN_ONLY = {"collega_storico", "link_history"}  # in the admin command list only
TREE = "  __main__.py"  # a line found only in the architecture tree




def read(name):
    return (ROOT / name).read_text(encoding="utf-8")


@pytest.fixture
def readme():
    return read("README.md")


@pytest.fixture
def deployment():
    return read("docs/deployment.md")


@pytest.fixture
def architecture():
    return read("docs/architecture.md")


def code_block_after(readme, marker):
    """The fenced block that follows the first line containing `marker`."""
    start = readme.index(marker)
    start = readme.index("```", start) + 3
    return readme[start:readme.index("```", start)]


def code_block_containing(readme, marker):
    """The fenced block that contains the first occurrence of `marker`."""
    at = readme.index(marker)
    return readme[readme.rindex("```", 0, at) + 3:readme.index("```", at)]


def handled_commands(language):
    """The names of the commands in 'it' or 'en' (bot.COMMANDS: English name, Italian name, handler)."""
    from caccometro.bot import COMMANDS
    return {names[0 if language == "en" else 1] for names in COMMANDS}


MENUS = {"it": "Italian menu", "en": "English menu"}   # the line before the menu block of each language


def test_every_command_is_in_the_readme_table(readme):
    # The Italian names are in the Italian menu of docs/deployment.md (/collega_storico in the sentence under it)
    for english in handled_commands("en"):
        assert re.search(rf"^\| `/{english}[ `]", readme, re.MULTILINE), f"/{english} is not in the commands table"


@pytest.mark.parametrize("language", MENUS)
def test_the_commands_menu_lists_exactly_the_commands_of_everybody(deployment, language):
    menu = {line.split(" - ")[0] for line in code_block_after(deployment, MENUS[language]).strip().splitlines()}
    assert menu == handled_commands(language) - ADMIN_ONLY


@pytest.mark.parametrize("language", MENUS)
def test_menu_descriptions_fit_the_telegram_limit(deployment, language):
    for line in code_block_after(deployment, MENUS[language]).strip().splitlines():
        assert 3 <= len(line.split(" - ", 1)[1]) <= 256, line


def test_every_module_is_in_the_architecture_tree(architecture):
    tree = code_block_containing(architecture, TREE)
    for module in (ROOT / "caccometro").glob("*.py"):
        assert re.search(rf"^\s+{module.name}\s", tree, re.MULTILINE), f"{module.name} is not in the architecture tree"


def test_every_variable_the_bot_reads_is_in_env_example():
    example = (ROOT / ".env.example").read_text(encoding="utf-8")
    sources = [ROOT / "caccometro" / "config.py", *(ROOT / "scripts").glob("*.py")]
    for source in sources:
        for name in re.findall(r"environ\.get\('(\w+)'", source.read_text(encoding="utf-8")):
            assert re.search(rf"^{name}\s*=", example, re.MULTILINE), f"{name} ({source.name}) is not in .env.example"


def test_the_files_named_in_the_architecture_tree_exist(architecture):
    tree = code_block_containing(architecture, TREE)
    named = {line.split()[0] for line in tree.splitlines() if line.startswith(("scripts/", "tools/", ".githooks/", ".gitattributes", "tests/", ".github/", "requirements", "wsgi", "assets/"))}
    named |= {f"caccometro/{line.split()[0]}" for line in tree.splitlines() if line.startswith("  ") and line.split()[0].endswith(".py")}
    assert named, "the architecture tree was not found"
    for path in sorted(named):
        assert (ROOT / path).exists(), f"{path} is named in the README but does not exist"


@pytest.mark.parametrize("doc", DOCS, ids=lambda path: path.name)
def test_the_documentation_has_no_hardcoded_test_counts(doc):
    assert not re.search(r"\b\d+ (tests?|passed|passati)", doc.read_text(encoding="utf-8"))


def test_every_service_script_is_named_in_the_documentation():
    docs = "".join(doc.read_text(encoding="utf-8") for doc in DOCS)
    for script in (ROOT / "tools").glob("*.py"):
        assert f"tools/{script.name}" in docs, f"tools/{script.name} is not named in the documentation"


@pytest.mark.parametrize("doc", DOCS, ids=lambda path: path.name)
def test_the_relative_links_point_to_existing_files(doc):
    for target in re.findall(r"\]\((?!https?:|#)([^)#\s]+)", doc.read_text(encoding="utf-8")):
        assert (doc.parent / target).exists(), f"{doc.name} links to {target}, which does not exist"


def test_the_readme_shows_every_sample_chart(readme):
    for chart in (ROOT / "assets" / "screenshots").glob("*.png"):
        assert f"assets/screenshots/{chart.name}" in readme, f"{chart.name} is not in the README"
