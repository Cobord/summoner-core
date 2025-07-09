"""
Signal Tree Loader

This module builds a tree of named signals from a simple indented text file ("TRIGGERS"),
exposing each as a Signal instance on a dynamically-generated Trigger class.

TRIGGERS file format:
    Each line defines a signal; indentation (spaces or tabs) specifies hierarchy.
    Inline comments with "#" are allowed.

Example TRIGGERS file:
    OK
        acceptable
        all_good
    error
        minor
        major

Usage:
    from triggers import Move, Stay, Test, Action, load_triggers

    Trigger = load_triggers()
    print(Trigger.OK)           # <Signal 'OK' path=(0,)>
    print(Trigger.acceptable)   # <Signal 'acceptable' path=(0, 0)>
    print(Trigger.name_of(1, 1)) # major
    print(isinstance(Move(Trigger.OK), Action.Move))
"""


import re
import sys
from typing import Any, Optional
from pathlib import Path
import keyword


_VARNAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def is_valid_varname(name: str) -> bool:
    """Return True if name matches Python variable naming rules."""
    return bool(_VARNAME_RE.match(name))


def preprocess_line(raw: str, lineno: int, tabsize: int):
    """
    Process a raw line:
      1) strip trailing newline
      2) expand tabs -> spaces
      3) measure indent from leading spaces
      4) remove inline comments (anything after '#')
      5) skip blank or comment-only lines
    Returns (lineno, indent, name) or None to skip.
    """
    expanded = raw.rstrip("\n").expandtabs(tabsize)
    stripped = expanded.lstrip(" ")
    indent = len(expanded) - len(stripped)
    content = stripped.split("#", 1)[0].rstrip()
    if not content:
        return None
    name = content
    return lineno, indent, name


def update_hierarchy(indent: int, indent_levels: list[int]) -> int:
    """
    Given the indent of the current line and the existing indent_levels,
    determine the new depth and update indent_levels in place.
    Returns the computed depth.
    """
    prev = indent_levels[-1]
    if indent == prev:
        depth = len(indent_levels) - 1
    elif indent > prev:
        indent_levels.append(indent)
        depth = len(indent_levels) - 1
    else:
        if indent in indent_levels:
            depth = indent_levels.index(indent)
            del indent_levels[depth + 1 :]
        else:
            raise ValueError(f"Inconsistent indent {indent}; levels: {indent_levels}")
    return depth


def simplify_leaves(tree: dict[str, Any]) -> None:
    """
    Recursively convert empty dicts to None to mark leaves.
    (4) No return, operates in-place on 'tree'.
    """
    for key, subtree in list(tree.items()):
        if subtree == {}:
            tree[key] = None
        elif isinstance(subtree, dict):
            simplify_leaves(subtree)


def parse_signal_tree_lines(lines: list[str], tabsize: int = 8) -> dict[str, Any]:
    """
    Parse a list of lines (strings) into a nested dict tree.
    This is one entry point, taking raw lines (great for testing).
    """
    root: dict[str, Any] = {}
    nodes_by_depth: dict[int, dict[str, Any]] = {0: root}
    indent_levels: list[int] = [0]

    for lineno, raw in enumerate(lines, 1):
        entry = preprocess_line(raw, lineno, tabsize)
        if entry is None:
            continue
        lineno, indent, name = entry

        if not is_valid_varname(name):
            raise ValueError(f"Line {lineno}: invalid name {name!r}")

        depth = update_hierarchy(indent, indent_levels)

        parent = nodes_by_depth[depth]
        if name in parent:
            raise ValueError(f"Line {lineno}: duplicate signal name {name!r} at indent level {indent}")
        parent[name] = {}

        # 3) Trim nodes_by_depth so we don't keep stale deeper dicts
        for d in list(nodes_by_depth):
            if d > depth:
                del nodes_by_depth[d]
        nodes_by_depth[depth + 1] = parent[name]

    simplify_leaves(root)
    return root


def parse_signal_tree(filepath: str, tabsize: int = 8) -> dict[str, Any]:
    """
    Read a file and parse it into a nested dict tree.
    This is the second entry point, for file-based input.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return parse_signal_tree_lines(lines, tabsize)


class Signal:
    __slots__ = ("_path", "_name")
    def __init__(self, path: tuple[int, ...], name: str):
        self._path = path
        self._name = name

    @property
    def path(self) -> tuple[int, ...]:
        return self._path

    @property
    def name(self) -> str:
        return self._name

    def __gt__(self, other):
        if not isinstance(other, Signal):
            return NotImplemented
        a, b = self._path, other._path
        return len(a) < len(b) and b[:len(a)] == a
    
    def __lt__(self, other):
        return other > self

    def __ge__(self, other):
        if not isinstance(other, Signal):
            return NotImplemented
        return self._path == other._path or self > other
    
    def __le__(self, other):
        return other >= self

    def __eq__(self, other):
        if not isinstance(other, Signal):
            return NotImplemented
        return self._path == other._path

    def __hash__(self):
        return hash(self._path)

    def __repr__(self):
        return f"<Signal {self._name!r}>"


def build_triggers(tree: dict[str, Any]):
    name_to_path: dict[str, tuple[int, ...]] = {}
    path_to_name: dict[tuple[int, ...], str] = {}

    def recurse(subtree: dict[str, Any], prefix: tuple[int, ...] =()):
        for idx, (name, child) in enumerate(subtree.items()):
            path = prefix + (idx,)
            name_to_path[name] = path
            path_to_name[path] = name
            if isinstance(child, dict) and child:
                recurse(child, path)

    recurse(tree)

    attrs = {}
    reserved = set(dir(object)) | set(keyword.kwlist) | {
        "_path_to_name", "name_of"
    }

    for name, path in name_to_path.items():
        if name in reserved or name.startswith("_"):
            raise ValueError(
                f"Signal name '{name}' is reserved or invalid as a Python attribute. "
                "Please use a different name."
            )
        attrs[name] = Signal(path, name)

    attrs["_path_to_name"] = path_to_name

    def name_of(*args):
        """Get signal name from tuple (or *args)."""
        return path_to_name.get(tuple(args))
    
    attrs["name_of"] = staticmethod(name_of)

    return type("Trigger", (), attrs)


class Event:
    __slots__ = ("signal",)
    def __init__(self, signal: Signal) -> None:
        self.signal = signal
    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.signal!r})"


class Move(Event): pass
class Stay(Event): pass
class Test(Event):
    __test__ = False
    pass


class Action:
    MOVE = Move
    STAY = Stay
    TEST = Test


def extract_signal(trigger):
    if isinstance(trigger, Event):
        return trigger.signal
    elif isinstance(trigger, Signal):
        return trigger
    elif trigger is None:
        return None
    else:
        raise TypeError(f"Cannot extract signal from object of type {type(trigger).__name__!r}")
     

# the file TRIGGERS needs to be next to the code for the client, hence sys.argv[0]
WORKING_DIR = Path(sys.argv[0]).resolve().parent

def load_triggers(
        triggers_file: Optional[str] = "TRIGGERS",
        text: Optional[str] = None, 
        json_dict: Optional[dict[str, Any]] = None
        ):
    """
    Load and build the TRIG class from a TRIGGERS file, text, or nested dict.

    Priority:
        1. If `text` is provided, it is used.
        2. Else if `json_dict` is provided, it is used.
        3. Else, file path is used (`triggers_file` or TRIGGERS_FILE).

    `json_dict` must match the nested structure output by `parse_signal_tree_lines`.

    Raises FileNotFoundError with clear message if file is missing.
    """
    try:
        if text is not None:
            lines = text.splitlines()
            tree = parse_signal_tree_lines(lines)
        elif json_dict is not None:
            tree = dict(json_dict)  # shallow copy to avoid mutation
        else:
            path = WORKING_DIR / triggers_file
            tree = parse_signal_tree(path)
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Could not find triggers file at {path if 'path' in locals() else '<provided text or dict>'}"
        ) from e
    return build_triggers(tree)

