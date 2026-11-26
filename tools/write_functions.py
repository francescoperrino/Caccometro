"""Write docs/functions.md: every public function and class of caccometro/, what it does and who uses it (#204).

Usage: python tools/write_functions.py  (the pre-commit hook runs it; tests/test_docs.py fails when the page is stale)
Listed: the public functions, classes and methods (no leading underscore). "What it does" is the first paragraph of
its docstring; "Used by" lists the other modules that import it by name or call it as module.unit.
"""
import ast
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PACKAGE = REPO / "caccometro"
OUT = REPO / "docs" / "functions.md"

INTRO = """# Functions and classes

Every public function and class of the `caccometro` package, one table per module: the static view of the code below the modules. Written by `tools/write_functions.py` from the code: do not edit by hand. "What it does" is the first paragraph of the docstring; "Used by" names the other modules of the package that import it or call it as `module.name`, or the decorator through which a framework calls it. For the modules and how they depend on each other, see [architecture.md](architecture.md#dependencies-between-modules).
"""


def signature(node, prefix=""):
    """The signature of a function or class as shown in the page.

    Shown as `name(arg, ...)` for a function, `name` for a property, `class Name` for a class; `self` and `cls` are left out.

    Args:
        node (ast.AST): the definition.
        prefix (str): text written before the name of a property, the name of its class.

    Returns:
        str: the text.
    """
    if isinstance(node, ast.ClassDef):
        return f"class {node.name}"
    if any(isinstance(item, ast.Name) and item.id == "property" for item in node.decorator_list):
        return f"{prefix}{node.name}"   # read like an attribute
    args = node.args
    names = [a.arg for a in args.posonlyargs + args.args if a.arg not in ("self", "cls")]
    if args.vararg:
        names.append(f"*{args.vararg.arg}")
    elif args.kwonlyargs:
        names.append("*")
    names += [a.arg for a in args.kwonlyargs]
    if args.kwarg:
        names.append(f"**{args.kwarg.arg}")
    asynchronous = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
    return f"{asynchronous}{prefix}{node.name}({', '.join(names)})"


def summary(node):
    """The first paragraph of the docstring of a node, on one line.

    Args:
        node (ast.AST): the definition.

    Returns:
        str: the text; '(no docstring)' when there is none.
    """
    docstring = ast.get_docstring(node)
    return " ".join(docstring.strip().split("\n\n")[0].split()) if docstring else "(no docstring)"


def decorators(node):
    """The decorators of a function, as written (`@app.route('/app')`).

    Args:
        node (ast.AST): the definition.

    Returns:
        list: the decorators as Markdown code.
    """
    return [f"`@{ast.unparse(item)}`" for item in getattr(node, "decorator_list", [])]


def units(tree):
    """The public functions, classes and methods of a module, in source order.

    A method has no name of its own: other modules reach it through its class.

    Args:
        tree (ast.Module): the module.

    Returns:
        list: [(name, signature, summary, decorators)].
    """
    found = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not node.name.startswith("_"):
            found.append((node.name, signature(node), summary(node), decorators(node)))
            if isinstance(node, ast.ClassDef):
                found += [(None, signature(item, f"{node.name}."), summary(item), []) for item in node.body
                          if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                          and not item.name.startswith("_")]
    return found


def users(trees):
    """Which modules use each unit of the package.

    Args:
        trees (dict): {module: ast.Module}.

    Returns:
        dict: {(module, name): set of the other modules that import `name` from `module` or use `module.name`}.
    """
    used = {}
    for user, tree in trees.items():
        aliases = {}   # local name -> module of the package
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "caccometro":
                aliases.update({alias.asname or alias.name: alias.name for alias in node.names})
            elif isinstance(node, ast.ImportFrom) and (node.module or "").startswith("caccometro."):
                module = node.module.split(".")[1]
                for alias in node.names:
                    used.setdefault((module, alias.name), set()).add(user)
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in aliases:
                used.setdefault((aliases[node.value.id], node.attr), set()).add(user)
    return used


def cell(text):
    """A text that stays in one cell of a Markdown table.

    Args:
        text (str): the text.

    Returns:
        str: the text with the characters of the table escaped.
    """
    return text.replace("|", "\\|").replace("<", "&lt;")


def render():
    """The Markdown of docs/functions.md.

    Returns:
        str: the page.
    """
    trees = {path.stem: ast.parse(path.read_text(encoding="utf-8")) for path in sorted(PACKAGE.glob("*.py"))}
    used = users(trees)
    # names each module reads besides defining them: a unit used only where it is defined
    local = {module: {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)} for module, tree in trees.items()}
    parts = [INTRO]
    for module, tree in trees.items():
        found = units(tree)
        if not found:
            continue
        doc = ast.get_docstring(tree)
        parts.append(f"\n## {module}.py\n\n")
        if doc:
            parts.append(cell(doc.strip().splitlines()[0]) + "\n\n")
        parts.append("| Function or class | What it does | Used by |\n| --- | --- | --- |\n")
        for name, sig, text, through in found:
            by = ", ".join(f"`{m}`" for m in sorted(used.get((module, name), set()) - {module}))
            if name and not by and through:
                by = ", ".join(through)
            elif name and not by:
                by = "only its own module" if name in local[module] else "none in the package"
            parts.append(f"| `{sig}` | {cell(text)} | {by} |\n")
    return "".join(parts)


if __name__ == "__main__":
    OUT.write_text(render(), encoding="utf-8", newline="\n")
    print(f"{OUT.relative_to(REPO)}: written")
