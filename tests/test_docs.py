"""The documentation must match the code: commands, modules, variables and file names (#106, #143).

Diagrams and prose cannot be tested; they are reviewed with the checklist of the commit workflow.
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DOCS = sorted([ROOT / "README.md", ROOT / "README.it.md", ROOT / "CONTRIBUTING.md", ROOT / "SECURITY.md", *(ROOT / "docs").glob("*.md")])
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


def code_block_containing(readme, marker):
    """The fenced block that contains the first occurrence of `marker`."""
    at = readme.index(marker)
    return readme[readme.rindex("```", 0, at) + 3:readme.index("```", at)]


def handled_commands(language):
    """The names of the commands in 'it' or 'en' (bot.COMMANDS: English name, Italian name, handler)."""
    from caccometro.bot import COMMANDS
    return {names[0 if language == "en" else 1] for names in COMMANDS}




def test_every_italian_command_is_in_the_italian_readme_table():
    italian = read("README.it.md")
    for name in handled_commands("it"):
        assert re.search(rf"^\| `/{name}[ `]", italian, re.MULTILINE), f"/{name} is not in the Italian commands table"


def test_every_command_is_in_the_readme_table(readme):
    # The Italian names are in the menu table of docs/deployment.md
    for english in handled_commands("en"):
        assert re.search(rf"^\| `/{english}[ `]", readme, re.MULTILINE), f"/{english} is not in the commands table"


def test_the_menu_table_in_the_docs_is_the_menu_of_the_code(deployment):
    from caccometro.menus import ADMIN_ONLY, MENU
    rows = re.findall(r"^\| `/.*\|$", deployment, re.MULTILINE)
    expected = []
    for en, it, en_text, it_text in MENU:
        mark = " (admins)" if en in ADMIN_ONLY else ""
        expected.append(f"| `/{en}`{mark} | {en_text} | `/{it}`{mark} | {it_text} |")
    assert [row.rstrip("\r") for row in rows] == expected


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


@pytest.mark.parametrize("name", ["README.md", "README.it.md"])
def test_the_readmes_show_every_sample_chart(name):
    for chart in (ROOT / "assets" / "screenshots").glob("*.png"):
        assert f"assets/screenshots/{chart.name}" in read(name), f"{chart.name} is not in {name}"
