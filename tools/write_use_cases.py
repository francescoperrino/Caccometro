"""Write docs/use_cases.md: for every use case, its communication diagram, sequence diagram and call tree (#204).

Usage: python tools/write_use_cases.py  (the pre-commit hook runs it; tests/test_docs.py fails when the page is stale)
Everything is read from the code with ast, not from a run, so both sides of an `if` appear. The sequence diagram
follows the statements of the entry point and of the functions it calls in other modules (if, for, try become
alt, opt, loop); the communication diagram regroups its arrows by pair of modules; the call tree lists every
public function the entry point may reach. Calls to config.py and i18n.py, to classes and to other libraries are
left out, except the Telegram methods that send something.
"""
import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from caccometro.menus import MENU  # noqa: E402
from mermaid_style import CLASSDEFS, FRONTMATTER, SEQUENCE_GROUND, accessible  # noqa: E402

PACKAGE = REPO / "caccometro"
OUT = REPO / "docs" / "use_cases.md"
SKIPPED = {"config", "i18n"}   # used by almost everything: they would hide the rest

# Use cases that are not commands: (title, who starts it, module, function)
OTHERS = [
    ("A message in the chat: 💩 or 🚽 (text or sticker), a location, a mention of the bot, \"run\"", "telegram", "messages", "handle_message"),
    ("A group becomes a supergroup", "telegram", "messages", "handle_migration"),
    ("Open the Mini App: the page", "miniapp_page", "webhook", "mini_app"),
    ("Mini App: data of the chat (map, seasons, records, trophies)", "miniapp_page", "webhook", "api_chat"),
    ("Mini App: a month or a year (leaderboard, statistics)", "miniapp_page", "webhook", "api_period"),
    ("Midnight announcement (scheduled task)", "task", "announce", "main"),
]

INTRO = """# Use cases

What the code does in each use case, read from the code by `tools/write_use_cases.py`: do not edit by hand. Each use case has three views, in UML notation drawn with Mermaid:

1. **Communication diagram**: the modules involved, one arrow for the calls from a module to another (the functions it uses, numbered) and a dashed arrow back with what they return.
2. **Sequence diagram**: the same steps in time order, with the arguments of every call and the variable that receives the result. `alt`, `opt` and `loop` boxes are the `if`, `else` and `for` of the code; a note marks a branch that ends the function, or a function of the same module already drawn above.
3. **Call tree**, folded: every function of the package the entry point may call, private functions replaced by the public ones they call.

The views come from the code, not from a run: every branch appears, whether or not it is taken. Calls inside one module have no arrow; calls to `config.py`, `i18n.py`, classes and other libraries are left out, except the Telegram methods that send something. Arguments and conditions are cut at 40 characters. What each function does is in [functions.md](functions.md); the path of a message through Telegram and the webhook is in [architecture.md](architecture.md#path-of-a-message).
"""


def parse():
    """{module: (functions {name: node}, names {local name: (module, name)}, modules {alias: module})}."""
    found = {}
    for path in sorted(PACKAGE.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        functions = {node.name: node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        names, modules = {}, {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "caccometro":
                modules.update({alias.asname or alias.name: alias.name for alias in node.names})
            elif isinstance(node, ast.ImportFrom) and (node.module or "").startswith("caccometro."):
                names.update({alias.asname or alias.name: (node.module.split(".")[1], alias.name) for alias in node.names})
        found[path.stem] = (functions, names, modules)
    return found


def calls(code, module, function):
    """The functions of the package that `module.function` calls, in the order they are written, each once.

    A function passed to a call (maps.render(maps.zoom_map, ...)) counts as called too.
    """
    functions, names, modules = code[module]
    seen = []
    called = [node for call in ast.walk(functions[function]) if isinstance(call, ast.Call)
              for node in [call.func, *call.args]]
    for node in sorted(called, key=lambda node: (node.lineno, node.col_offset)):
        target = None
        if isinstance(node, ast.Name):
            name = node.id
            target = (module, name) if name in functions else names.get(name)
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            alias = node.value.id
            if alias in modules:
                target = (modules[alias], node.attr)
        if (target and target[0] not in SKIPPED and target[0] in code and target[1] in code[target[0]][0]
                and target != (module, function) and target not in seen):
            seen.append(target)
    return seen


def public_calls(code, module, function, through=None):
    """calls() with the private functions (leading underscore) replaced by the public functions they call."""
    through = set() if through is None else through
    found = []
    for target in calls(code, module, function):
        if not target[1].startswith("_"):
            found.append(target)
        elif target not in through:
            through.add(target)
            found += public_calls(code, *target, through)
    return list(dict.fromkeys(found))


def tree(code, module, function, depth=0, expanded=None):
    """Markdown list lines of the calls of `module.function`, indented by depth."""
    expanded = set() if expanded is None else expanded
    expanded.add((module, function))
    lines = []
    for target in public_calls(code, module, function):
        label = f"`{target[0]}.{target[1]}`"
        if target in expanded:
            lines.append(f"{'  ' * depth}- {label} (see above)")
            continue
        lines.append(f"{'  ' * depth}- {label}")
        lines += tree(code, *target, depth + 1, expanded)
    return lines


# wider gaps than the default, so the labels of the arrows of a communication diagram do not cover each other
SPACED = FRONTMATTER.replace("\n---\n", "\n  flowchart:\n    nodeSpacing: 50\n    rankSpacing: 160\n---\n")
assert SPACED != FRONTMATTER

TELEGRAM_CALLS = {"reply_text", "reply_photo", "reply_media_group", "send_message", "get_chat_member",
                  "set_my_commands"}   # the Bot API methods the package calls, drawn as arrows to Telegram
LABEL = 40   # longest label of an argument list or a condition


def source(node):
    """ast.unparse of `node`, the same on every Python version: 3.10 writes `for (a, b) in`, 3.11 `for a, b in`."""
    text = ast.unparse(node)
    start = text.find("for (")
    while start != -1:
        depth, end = 0, start + 4
        for end in range(start + 4, len(text)):   # the parenthesis that closes the one after "for "
            depth += {"(": 1, ")": -1}.get(text[end], 0)
            if depth == 0:
                break
        if text.startswith(" in ", end + 1):
            text = text[:start + 4] + text[start + 5:end] + text[end + 1:]
        start = text.find("for (", start + 4)
    return text


assert source(ast.parse("[t for (a, (b, c)) in x]")) == source(ast.parse("[t for a, (b, c) in x]")) == "[t for a, (b, c) in x]"


def short(text):
    """`text` on one line, at most LABEL characters, without the characters Mermaid reads as syntax."""
    text = " ".join(text.split()).replace(";", ",").replace("#", "#35;")
    return text if len(text) <= LABEL else text[:LABEL - 3] + "..."


class Sequence:
    """Mermaid sequenceDiagram lines of one use case, read from the code (UML combined fragments for if/for)."""

    def __init__(self, code):
        self.code = code
        self.expanded = set()
        self.drawn = {}   # same-module function -> it drew arrows when it was expanded
        self.participants = []

    def meet(self, name):
        if name not in self.participants:
            self.participants.append(name)

    def resolve(self, module, func):
        """(module, name) of a function of the package called as `func` from `module`, or None."""
        functions, names, modules = self.code[module]
        target = None
        if isinstance(func, ast.Name):
            target = (module, func.id) if func.id in functions else names.get(func.id)
        elif isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id in modules:
            target = (modules[func.value.id], func.attr)
        if target and target[0] not in SKIPPED and target[0] in self.code and target[1] in self.code[target[0]][0]:
            return target
        return None

    def function(self, module, name, depth):
        self.expanded.add((module, name))
        return self.block(self.code[module][0][name].body, module, depth)

    def block(self, statements, module, depth, branch=False):
        lines = []
        for statement in statements:
            lines += self.statement(statement, module, depth)
        if lines and branch and isinstance(statements[-1], ast.Return):
            lines.append(f"{'    ' * depth}Note over {module}: returns")   # the branch ends the function
        return lines

    def statement(self, node, module, depth):
        pad = "    " * depth
        if isinstance(node, ast.If):
            lines = self.expression(node.test, module, depth)
            body = self.block(node.body, module, depth + 1, branch=True)
            other = self.block(node.orelse, module, depth + 1, branch=True)
            condition = short(source(node.test))
            if body and other:
                return lines + [f"{pad}alt {condition}", *body, f"{pad}else", *other, f"{pad}end"]
            if body or other:
                return lines + [f"{pad}opt {condition if body else short('not (' + source(node.test) + ')')}", *(body or other), f"{pad}end"]
            return lines
        if isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
            head = (f"for {source(node.target)} in {source(node.iter)}" if not isinstance(node, ast.While)
                    else f"while {source(node.test)}")
            lines = self.expression(node.iter if not isinstance(node, ast.While) else node.test, module, depth)
            body = self.block(node.body, module, depth + 1)
            return lines + ([f"{pad}loop {short(head)}", *body, f"{pad}end"] if body else [])
        if isinstance(node, (ast.With, ast.AsyncWith)):
            lines = [line for item in node.items for line in self.expression(item.context_expr, module, depth)]
            return lines + self.block(node.body, module, depth)
        if isinstance(node, ast.Try):
            lines = self.block(node.body, module, depth)
            for handler in node.handlers:
                body = self.block(handler.body, module, depth + 1)
                kind = source(handler.type) if handler.type else "any error"
                lines += [f"{pad}opt on {short(kind)}", *body, f"{pad}end"] if body else []
            return lines + self.block(node.orelse + node.finalbody, module, depth)
        if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)) and node.value is not None:
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            return self.expression(node.value, module, depth, ", ".join(source(t) for t in targets))
        if isinstance(node, (ast.Expr, ast.Return)) and node.value is not None:
            return self.expression(node.value, module, depth)
        return []

    def expression(self, node, module, depth, result=None):
        """Arrows of the calls in an expression, inner calls first; `result` names what the outer call returns into."""
        top = node.value if isinstance(node, ast.Await) else node
        lines = []

        def visit(item):
            if isinstance(item, (ast.Lambda, ast.FunctionDef, ast.AsyncFunctionDef)):
                return
            if isinstance(item, ast.Call):
                for child in [item.func.value] if isinstance(item.func, ast.Attribute) else []:
                    visit(child)
                for child in item.args + [keyword.value for keyword in item.keywords]:
                    visit(child)
                lines.extend(self.call(item, module, depth, result if item is top else None))
                return
            for child in ast.iter_child_nodes(item):
                visit(child)

        visit(node)
        return lines

    def call(self, node, module, depth, result):
        pad = "    " * depth
        arguments = short(", ".join(source(a) for a in node.args + node.keywords))
        target = self.resolve(module, node.func)
        if target is None:
            if isinstance(node.func, ast.Attribute) and node.func.attr in TELEGRAM_CALLS:
                self.meet("telegram")
                return [f"{pad}{module}->>telegram: {node.func.attr}({arguments})"]
            return []
        callee, name = target
        if callee == module:   # inside one module: no arrow, its calls to other modules still show
            if target not in self.expanded:
                lines = self.function(callee, name, depth)
                self.drawn[target] = bool(lines)
                return lines
            return [f"{pad}Note over {module}: {name}() as above"] if self.drawn.get(target) else []
        self.meet(callee)
        lines = [f"{pad}{module}->>{callee}: {name}({arguments})"]
        if target not in self.expanded and not name.startswith("__"):
            lines += self.function(callee, name, depth)
        if result:
            lines.append(f"{pad}{callee}-->>{module}: {short(result)}")
        return lines


def sequence(code, actor, module, function, title):
    """Mermaid source of the sequence diagram of a use case that starts with `actor` calling `module.function`."""
    diagram = Sequence(code)
    node = code[module][0][function]
    arguments = ", ".join(a.arg for a in node.args.args)
    diagram.meet(module)
    body = diagram.function(module, function, 1)
    actors = {"telegram": "participant telegram as ✈️ Telegram", "miniapp_page": "participant miniapp_page as 📱 Mini App page",
              "task": "participant task as 🕛 Scheduled task"}
    header = ["sequenceDiagram", *accessible(f"Sequence diagram, {title}", f"The calls between the modules in time "
                                                f"order, starting from {module}.{function}"),
              "    autonumber", f"    {actors[actor]}"]
    header += [f"    {actors['telegram']}" for name in diagram.participants if name == "telegram" and actor != "telegram"]
    header += [f"    participant {name} as {name}.py" for name in diagram.participants if name != "telegram"]
    answer = [f"    {module}-->>{actor}: HTTP response"] if actor == "miniapp_page" else []   # a return, not a call
    steps = [f"    {actor}->>{module}: {function}({arguments})"] + body + answer
    return "\n".join(header + [f"    {SEQUENCE_GROUND}"] + ["    " + step for step in steps] + ["    end"])


def communication(source, title):
    """Mermaid flowchart of a sequence diagram (UML communication diagram): the same participants, one arrow per
    pair of them with its calls, one dashed arrow back with what they return, each with its number in the sequence."""
    names, edges, step = {}, {}, 0
    for line in source.splitlines():
        line = line.strip()
        if line.startswith("participant "):
            _, key, _, label = line.split(" ", 3)
            names[key] = label
        elif "->>" in line:
            step += 1
            back = "-->>" in line
            source_key, rest = line.split("-->>" if back else "->>", 1)
            target, message = rest.split(":", 1)
            message = message.strip() if back else message.strip().split("(", 1)[0]
            calls = edges.setdefault((source_key, target, back), {})   # call or returned value -> its steps
            calls.setdefault(message, []).append(str(step))
    lines = ["flowchart LR", *accessible(f"Communication diagram, {title}", "The modules involved, the functions "
                                         "each one calls in another and what comes back, numbered as in the sequence")]
    lines += [f'    {key}("<b>{label}</b>")' for key, label in names.items()]
    lines += [f'    {a} {"-.->" if back else "-->"}|"{"<br/>".join(", ".join(steps) + ".#nbsp;" + name for name, steps in calls.items())}"| {b}'
              for (a, b, back), calls in edges.items()]   # #nbsp; keeps a number on the line of its function
    actors = [key for key in names if key in ("telegram", "miniapp_page", "task")]
    lines += [f"    {line}" for line in CLASSDEFS if line.split()[1] in ("step", "person")]
    lines += [f"    class {','.join(key for key in names if key not in actors)} step",
              f"    class {','.join(actors)} person"]
    return "\n".join(lines)


def handlers():
    """[(title, who starts it, module, function)] of the commands, in menu order."""
    from caccometro.bot import HANDLERS
    cases = []
    for english, italian, _, _ in MENU:
        handler = HANDLERS[english]
        title = f"`/{english}`" + (f" (`/{italian}`)" if italian != english else "")
        cases.append((title, "telegram", handler.__module__.split(".")[1], handler.__name__))
    return cases


def render():
    code = parse()
    parts = [INTRO]
    for title, actor, module, function in handlers() + OTHERS:
        plain = title.replace("`", "")
        source = sequence(code, actor, module, function, plain)
        lines = tree(code, module, function)
        parts.append(f"\n## {title}\n\nEntry point: `{module}.{function}`\n\n"
                     f"```mermaid\n{SPACED}{communication(source, plain)}\n```\n\n```mermaid\n{FRONTMATTER}{source}\n```\n\n"
                     "<details>\n<summary>Call tree</summary>\n\n"
                     + ("\n".join(lines) if lines else "No other function of the package.") + "\n\n</details>\n")
    return "".join(parts)


if __name__ == "__main__":
    OUT.write_text(render(), encoding="utf-8", newline="\n")
    print(f"{OUT.relative_to(REPO)}: written")
