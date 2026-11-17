"""The documentation must match the code: commands, modules, variables and file names (#106).

Diagrams and prose cannot be tested; they are reviewed with the checklist of the commit workflow.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
ADMIN_ONLY = {"collega"}  # in the admin command list only


def code_block_after(marker):
    """The fenced block that follows the first line containing `marker`."""
    start = README.index(marker)
    start = README.index("```", start) + 3
    return README[start:README.index("```", start)]


def code_block_containing(marker):
    """The fenced block that contains the first occurrence of `marker`."""
    at = README.index(marker)
    return README[README.rindex("```", 0, at) + 3:README.index("```", at)]


def handled_commands():
    bot_source = (ROOT / "caccometro" / "bot.py").read_text(encoding="utf-8")
    return set(re.findall(r"CommandHandler\('(\w+)'", bot_source))


def test_every_command_is_in_the_readme_table():
    for command in handled_commands():
        assert re.search(rf"^\| `/{command}[ `]", README, re.MULTILINE), f"/{command} is not in the commands table"


def test_the_commands_menu_lists_exactly_the_commands_of_everybody():
    menu = {line.split(" - ")[0] for line in code_block_after("/setcommands").strip().splitlines()}
    assert menu == handled_commands() - ADMIN_ONLY


def test_menu_descriptions_fit_the_telegram_limit():
    for line in code_block_after("/setcommands").strip().splitlines():
        assert 3 <= len(line.split(" - ", 1)[1]) <= 256, line


def test_every_module_is_in_the_architecture_tree():
    tree = code_block_containing("il bot, come pacchetto Python")
    for module in (ROOT / "caccometro").glob("*.py"):
        assert re.search(rf"^\s+{module.name}\s", tree, re.MULTILINE), f"{module.name} is not in the architecture tree"


def test_every_variable_the_bot_reads_is_in_env_example():
    example = (ROOT / ".env.example").read_text(encoding="utf-8")
    sources = [ROOT / "caccometro" / "config.py", *(ROOT / "scripts").glob("*.py")]
    for source in sources:
        for name in re.findall(r"environ\.get\('(\w+)'", source.read_text(encoding="utf-8")):
            assert re.search(rf"^{name}\s*=", example, re.MULTILINE), f"{name} ({source.name}) is not in .env.example"


def test_the_files_named_in_the_readme_exist():
    tree = code_block_containing("il bot, come pacchetto Python")
    named = {line.split()[0] for line in tree.splitlines() if line.startswith(("scripts/", "tools/", ".githooks/", ".gitattributes", "tests/", ".github/", "requirements", "wsgi", "assets/"))}
    named |= {f"caccometro/{line.split()[0]}" for line in tree.splitlines() if line.startswith("  ") and line.split()[0].endswith(".py")}
    assert named, "the architecture tree was not found"
    for path in sorted(named):
        assert (ROOT / path).exists(), f"{path} is named in the README but does not exist"


def test_the_readme_has_no_hardcoded_test_counts():
    assert not re.search(r"\b\d+ (test|passed|passati)", README)


def test_every_service_script_is_named_in_the_readme():
    for script in (ROOT / "tools").glob("*.py"):
        assert f"tools/{script.name}" in README, f"tools/{script.name} is not named in the README"
