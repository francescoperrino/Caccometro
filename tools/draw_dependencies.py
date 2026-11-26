"""Draw the imports between the modules of caccometro/ as a Mermaid diagram in docs/architecture.md (#204).

Usage: python tools/draw_dependencies.py  (tests/test_docs.py fails when the diagram no longer matches the imports)
The diagram goes between the two MARKERS lines of docs/architecture.md. Every module needs a layer in LAYERS.
"""
import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

from mermaid_style import CLASSDEFS, FRONTMATTER, accessible  # noqa: E402

PACKAGE = REPO / "caccometro"
DOC = REPO / "docs" / "architecture.md"
MARKERS = ("<!-- drawn by tools/draw_dependencies.py: start -->", "<!-- drawn by tools/draw_dependencies.py: end -->")

# Layers from top to bottom. EVERYWHERE is imported by almost every module: its arrows would hide the others.
LAYERS = [
    ("start", "🚪 Entry points", ["__main__", "webhook", "announce"]),
    ("telegram", "✈️ Telegram: updates, commands, Mini App", ["bot", "cmd_leaderboards", "cmd_records", "cmd_counts", "cmd_conquests", "cmd_settings",
                                                         "arguments", "messages", "chat", "menus", "miniapp"]),
    ("replies", "💬 Replies: texts, charts, maps", ["formatting", "charts", "maps"]),
    ("rules", "🧮 Rules: pure functions", ["analysis", "trophies", "conquest"]),
    ("storage", "🗄️ Storage", ["database"]),
    ("types", "🧱 Shared types", ["model"]),
]
EVERYWHERE = ["config", "i18n"]
SKIPPED = ["__init__"]   # only the version


def imports():
    """The modules of the package that each module imports.

    Returns:
        dict: {module: set of the modules it imports}.
    """
    names = {path.stem for path in PACKAGE.glob("*.py")}
    found = {}
    for name in sorted(names):
        deps = set()
        for node in ast.walk(ast.parse((PACKAGE / f"{name}.py").read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom) and node.module == "caccometro":
                deps |= {alias.name for alias in node.names if alias.name in names}
            elif isinstance(node, ast.ImportFrom) and (node.module or "").startswith("caccometro."):
                deps.add(node.module.split(".")[1])
            elif isinstance(node, ast.Import):
                deps |= {alias.name.split(".")[1] for alias in node.names if alias.name.startswith("caccometro.")}
        found[name] = deps - {name}
    return found


def used_units():
    """The names of a module that another one uses: functions, classes and constants.

    A unit is used when it is imported by name (from caccometro.x import f) or called as x.f.

    Returns:
        dict: {(module, imported module): set of the names of the second that the first uses}.
    """
    trees = {path.stem: ast.parse(path.read_text(encoding="utf-8")) for path in PACKAGE.glob("*.py")}
    defined = {module: {node.name for node in tree.body
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
               | {target.id for node in tree.body if isinstance(node, (ast.Assign, ast.AnnAssign))
                  for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
                  for target in (target.elts if isinstance(target, ast.Tuple) else [target])   # A, B = 1, 2
                  if isinstance(target, ast.Name)}
               for module, tree in trees.items()}
    found = {}
    for user, tree in trees.items():
        aliases = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "caccometro":
                aliases.update({alias.asname or alias.name: alias.name for alias in node.names})
            elif isinstance(node, ast.ImportFrom) and (node.module or "").startswith("caccometro."):
                module = node.module.split(".")[1]
                found.setdefault((user, module), set()).update(
                    alias.name for alias in node.names if alias.name in defined.get(module, ()))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in aliases:
                module = aliases[node.value.id]
                if node.attr in defined.get(module, ()):
                    found.setdefault((user, module), set()).add(node.attr)
    return found


def cycles(graph):
    """Find the import cycles.

    Args:
        graph (dict): {module: set of the modules it imports}.

    Returns:
        list: each cycle once, as a list of modules, found by a depth-first search.
    """
    found, path = [], []

    def visit(node):
        """Follow the imports of a module, remembering the path; record a cycle when the path meets itself."""
        if node in path:
            cycle = path[path.index(node):]
            start = cycle.index(min(cycle))
            cycle = cycle[start:] + cycle[:start]
            if cycle not in found:
                found.append(cycle)
            return
        path.append(node)
        for dep in sorted(graph.get(node, ())):
            visit(dep)
        path.pop()

    for node in sorted(graph):
        visit(node)
    return found


def render():
    """Draw the dependency diagram, with a sentence that explains it and the list of import cycles.

    Returns:
        str: the Markdown for docs/architecture.md.
    """
    graph = imports()
    placed = [name for _, _, names in LAYERS for name in names] + EVERYWHERE + SKIPPED
    missing = sorted(set(graph) - set(placed))
    assert not missing, f"put {missing} in a layer of tools/draw_dependencies.py"
    lines = ["```mermaid", *FRONTMATTER.splitlines(), "flowchart TD",
             *accessible("Dependencies between modules", "Which module of caccometro imports which, in layers from "
                         "the entry points down to the storage, with the number of names used")]
    for key, title, names in LAYERS:
        lines.append(f'    subgraph {key}["{title}"]')
        lines.extend(f'        {name}("<b>{name}.py</b>")' for name in names)
        lines.append("    end")
    units = used_units()
    for name in sorted(graph):
        for dep in sorted(graph[name] - set(EVERYWHERE)):
            if name not in SKIPPED:
                lines.append(f'    {name} -->|"{len(units.get((name, dep), ()))}"| {dep}')
    lines += [
        *(f"    {line}" for line in CLASSDEFS if line.split()[1] in ("step", "main", "person")),
        f"    class {','.join(LAYERS[0][2])} person",
        f"    class {','.join(name for _, _, names in LAYERS[1:] for name in names)} step",
        f"    class {','.join(LAYERS[3][2])} main",
        "```",
        "",
        f"An arrow goes from a module to the modules it imports; its number is how many names of the imported "
        f"module it uses: functions, classes and constants (the functions and classes: [functions.md](functions.md), "
        f"column Used by). Not drawn: `{'.py`, `'.join(EVERYWHERE)}.py`, imported by "
        f"almost every module, and `__init__.py`, which holds only the version.",
    ]
    found = cycles(graph)
    lines.append("")
    lines.append("Import cycles: " + ("; ".join(" → ".join(c + [c[0]]) for c in found) if found else "none."))
    return "\n".join(lines)


def updated(text):
    """Put the diagram in the text of docs/architecture.md.

    Args:
        text (str): the text of the page.

    Returns:
        str: the text with the diagram between the markers replaced.
    """
    start = text.index(MARKERS[0]) + len(MARKERS[0])
    end = text.index(MARKERS[1])
    newline = "\r\n" if "\r\n" in text else "\n"
    return text[:start] + newline + render().replace("\n", newline) + newline + text[end:]


if __name__ == "__main__":
    DOC.write_bytes(updated(DOC.read_bytes().decode("utf-8")).encode("utf-8"))
    print(f"{DOC.relative_to(REPO)}: dependencies drawn")
