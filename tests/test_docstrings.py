"""The docstrings follow the Google style of the rules in issue #187: summary line, Args, Returns, Raises."""
import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
# Modules not converted yet: each commit of #187 removes some, the last one empties the list
PENDING = {
    "__main__",
    "announce",
    "arguments",
    "bot",
    "chat",
    "cmd_conquests",
    "cmd_counts",
    "cmd_leaderboards",
    "cmd_records",
    "cmd_settings",
    "messages",
    "miniapp",
    "webhook",
}
MODULES = sorted(path for path in (ROOT / "caccometro").glob("*.py") if path.stem not in PENDING | {"__init__"})


def parse(path):
    return ast.parse(path.read_text(encoding="utf-8"))


def own_nodes(function):
    """The nodes of a function without those of the functions, classes and lambdas inside it."""
    stack = list(function.body)
    while stack:
        node = stack.pop()
        yield node
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            stack.extend(ast.iter_child_nodes(node))


def definitions(tree):
    """[(qualified name, node, is nested in a function)] of every function and class."""
    found = []

    def visit(node, prefix, nested):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                found.append((prefix + child.name, child, nested))
                visit(child, f"{prefix}{child.name}.", nested or not isinstance(child, ast.ClassDef))
            else:
                visit(child, prefix, nested)

    visit(tree, "", False)
    return found


def sections(docstring):
    """{section name: its text} of a Google style docstring."""
    parts = re.split(r"^(Args|Returns|Yields|Raises|Attributes|Example):\s*$", docstring, flags=re.MULTILINE)
    return dict(zip(parts[1::2], parts[2::2]))


def needs_sections(node, nested):
    """Plain functions and methods need Args, Returns and Raises; closures, dunders and properties only a summary."""
    if nested or isinstance(node, ast.ClassDef) or node.name.startswith("__"):
        return False
    return not any(isinstance(d, ast.Name) and d.id == "property" for d in node.decorator_list)


@pytest.mark.parametrize("path", MODULES, ids=lambda path: path.stem)
def test_the_docstrings_follow_the_rules(path):
    tree = parse(path)
    problems = []
    if not ast.get_docstring(tree):
        problems.append("module: no docstring")
    for name, node, nested in definitions(tree):
        docstring = ast.get_docstring(node)
        if not docstring:
            problems.append(f"{name}: no docstring")
            continue
        if not docstring.split("\n")[0].endswith("."):
            problems.append(f"{name}: the first line must end with a full stop")
        found = sections(docstring)
        if isinstance(node, ast.ClassDef):
            fields = [item.target.id for item in node.body if isinstance(item, ast.AnnAssign)]
            if any(isinstance(base, ast.Name) and base.id == "NamedTuple" for base in node.bases):
                problems += [f"{name}: field {field} is not in Attributes" for field in fields
                             if not re.search(rf"^\s+{field}\b", found.get("Attributes", ""), re.MULTILINE)]
            continue
        if not needs_sections(node, nested):
            continue
        arguments = node.args
        params = [a.arg for a in arguments.posonlyargs + arguments.args + arguments.kwonlyargs
                  if a.arg not in ("self", "cls")] + [a.arg for a in (arguments.vararg, arguments.kwarg) if a]
        problems += [f"{name}: parameter {param} is not in Args" for param in params
                     if not re.search(rf"^\s+\*{{0,2}}{param}\b", found.get("Args", ""), re.MULTILINE)]
        nodes = list(own_nodes(node))
        if any(isinstance(n, (ast.Yield, ast.YieldFrom)) for n in nodes):
            if "Yields" not in found:
                problems.append(f"{name}: no Yields")
        elif any(isinstance(n, ast.Return) and n.value is not None
                 and not (isinstance(n.value, ast.Constant) and n.value.value is None) for n in nodes):
            if "Returns" not in found:
                problems.append(f"{name}: no Returns")
        if any(isinstance(n, ast.Raise) and n.exc is not None for n in nodes) and "Raises" not in found:
            problems.append(f"{name}: no Raises")
    assert not problems, f"{path.name}:\n  " + "\n  ".join(problems)
