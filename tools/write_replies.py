"""Write docs/replies.md: every sentence the bot sends, in Italian and English, one section per command.

Usage: python tools/write_replies.py  (the pre-commit hook runs it; tests/test_docs.py fails when the page is stale)
The sections are the comments of the i18n.EN dictionary: a comment starts a section, and the same comment twice
adds to the same section. Commands come first in menu order, then the shared sentences and the group messages.
"""
import ast
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from caccometro.i18n import EN  # noqa: E402
from caccometro.menus import MENU  # noqa: E402

SOURCE = REPO / "caccometro" / "i18n.py"
OUT = REPO / "docs" / "replies.md"
ITALIAN = {en: it for en, it, _, _ in MENU}
ORDER = [en for en, _, _, _ in MENU]
COMMAND = re.compile(r"/(\w+)")

INTRO = """# Replies of the bot

Every sentence the bot can send, in English and Italian, from `caccometro/i18n.py`. Written by `tools/write_replies.py`: do not edit by hand. `{name}`, `{count}` and the other words in braces are filled in when the bot answers; `*bold*` and `_italic_` are Telegram formatting. Where a section has several sentences for the same moment, the bot picks one at random.
"""


def sections():
    """The sentences of i18n.py grouped by the comment above them.

    Returns:
        list: [(comment, [Italian sentence, ...])] in the order of the file; a repeated comment joins its first section.
    """
    text = SOURCE.read_text(encoding="utf-8")
    lines = text.splitlines()
    comments = [(number, line.strip()[2:]) for number, line in enumerate(lines, 1)
                if line.startswith("    # ")]
    tree = ast.parse(text)
    dictionary = next(node.value for node in tree.body
                      if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", None) == "EN")
    found = {}
    for key in dictionary.keys:
        comment = [title for number, title in comments if number < key.lineno][-1]
        found.setdefault(comment, []).append(key.value)
    return list(found.items())


def title(comment):
    """A section title with each English command followed by its Italian name.

    Args:
        comment (str): the comment.

    Returns:
        str: the title.
    """
    def names(match):
        """The text for one command found in a comment: the English name and, if different, the Italian one.

        Args:
            match (re.Match): the match of COMMAND.

        Returns:
            str: the text.
        """
        english = match.group(1)
        if english not in ITALIAN:
            return match.group(0)
        italian = ITALIAN[english]
        return f"`/{english}`" + (f" (`/{italian}`)" if italian != english else "")
    return COMMAND.sub(names, comment)


def rank(item):
    """The order of a section: commands in menu order, then the other sections in the order of i18n.py.

    Args:
        item (tuple): (comment, sentences).

    Returns:
        int: the sort key.
    """
    commands = [name for name in COMMAND.findall(item[0]) if name in ITALIAN]
    return ORDER.index(commands[0]) if commands and item[0].startswith("/") else len(ORDER)


def cell(sentence):
    """A sentence that stays on one row of a Markdown table and shows its symbols as they are.

    Args:
        sentence (str): the sentence.

    Returns:
        str: the text with the characters of the table escaped.
    """
    return sentence.replace("|", "\\|").replace("<", "&lt;").replace("\n", "<br>").strip() or "(space)"


def render():
    """The Markdown of docs/replies.md.

    Returns:
        str: the page.
    """
    parts = [INTRO]
    for comment, sentences in sorted(sections(), key=rank):
        parts.append(f"\n## {title(comment)}\n\n| English | Italian |\n| --- | --- |\n")
        parts.extend(f"| {cell(EN[it])} | {cell(it)} |\n" for it in sentences)
    return "".join(parts)


if __name__ == "__main__":
    OUT.write_text(render(), encoding="utf-8", newline="\n")
    print(f"{OUT.relative_to(REPO)}: {sum(len(s) for _, s in sections())} sentences")
