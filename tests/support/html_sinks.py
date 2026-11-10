"""Find the `${…}` of the pages' scripts that build HTML without escaping (0671).

The pages build their HTML in the browser from template literals (`innerHTML`,
`insertAdjacentHTML`): every name, EXIF field or tag shown must go through an escaping
helper. This reads the templates' scripts as text (no browser, no JavaScript parser) and
lists each interpolation of a literal holding markup whose value is not proven safe.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final

SOURCES: Final = Path(__file__).parents[2] / "src" / "media_hygiene"
# Helpers that return escaped text or the tool's own markup: `icon` names a sprite,
# `said` joins texts through `esc`, `opened` builds a link with `encodeURIComponent`.
SAFE_CALLS: Final = frozenset(
    {"esc", "icon", "number", "Number", "encodeURIComponent", "said", "opened"}
)
_JINJA_COMMENT: Final = re.compile(r"\{#.*?#\}", re.DOTALL)
_MARKUP: Final = re.compile(r"<[a-zA-Z/!]")
_CALL: Final = re.compile(r"^([A-Za-z_$][\w$.]*)\(")
_NUMERIC: Final = re.compile(r"^[\w$.]*\.(length|size|count|total|width|height)$")
_QUOTES: Final = "'\""
_REGEX_AFTER: Final = "(,=:[!&|?{};"


def _goes_on(text: str, index: int) -> bool:
    """Tell whether the expression ending a line goes on on the next one.

    Args:
        text: The script.
        index: The index of a `;` or a line break.

    Returns:
        True for a line break followed by an operator (`?`, `:`, `+`, `.`, `|`, `&`).
    """
    if text[index] != "\n":
        return False
    rest = text[index:].lstrip()
    return bool(rest) and rest[0] in "?:+.|&"


@dataclass(frozen=True, slots=True)
class Hole:
    """An interpolation that puts an unproven value into markup."""

    file: str
    line: int
    expression: str


def _skip_string(text: str, start: int) -> int:
    """The index after a quoted string.

    Args:
        text: The source.
        start: The index of the opening quote.

    Returns:
        The index after the closing quote.
    """
    quote, index = text[start], start + 1
    while index < len(text) and text[index] != quote:
        index += 2 if text[index] == "\\" else 1
    return index + 1


def _skip_regex(text: str, start: int) -> int:
    """The index after a regular expression literal.

    Args:
        text: The source.
        start: The index of the opening slash.

    Returns:
        The index after its closing slash.
    """
    index, in_class = start + 1, False
    while index < len(text) and text[index] != "\n":
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == "/" and not in_class:
            return index + 1
        in_class = (in_class or char == "[") and char != "]"
        index += 1
    return index


@dataclass(frozen=True, slots=True)
class _Literal:
    """A template literal: its static parts, its interpolations, where it ends."""

    static: str
    parts: tuple[tuple[int, str], ...]  # (index of `${`, expression)
    end: int


class _Scanner:
    """Reads a script, collecting every template literal met, nested ones included."""

    def __init__(self, text: str) -> None:
        """Keep the text.

        Args:
            text: The script.
        """
        self.text = text
        self.found: list[_Literal] = []

    def code_end(  # noqa: C901  # pylint: disable=too-complex
        self, start: int, closer: str
    ) -> int:
        """Scan code up to `closer` at depth 0, skipping strings, comments, literals.

        Args:
            start: Where the code starts.
            closer: `}` for an interpolation, "" for the whole script.

        Returns:
            The index of the closer (or the end of the text).
        """
        text, index, depth, last = self.text, start, 0, "("
        while index < len(text):
            char = text[index]
            if (
                closer == ";"
                and depth == 0
                and char in ";\n"
                and not _goes_on(text, index)
            ):
                return index
            if char in "{([":
                depth += 1
            elif char in "})]":
                if depth == 0 and char == closer:
                    return index
                depth -= 1
            elif char in _QUOTES:
                index, last = _skip_string(text, index), '"'
                continue
            elif char == "`":
                index, last = self.literal(index).end, '"'
                continue
            elif text.startswith("//", index):
                found = text.find("\n", index)
                index = len(text) if found < 0 else found
                continue
            elif text.startswith("/*", index):
                index = text.find("*/", index) + 2
                continue
            elif char == "/" and last in _REGEX_AFTER:
                index, last = _skip_regex(text, index), '"'
                continue
            if not char.isspace():
                last = char
            index += 1
        return index

    def literal(self, start: int) -> _Literal:
        """Read the template literal opening at `start`, and record it.

        Args:
            start: The index of its backtick.

        Returns:
            The literal.
        """
        text, index = self.text, start + 1
        static: list[str] = []
        parts: list[tuple[int, str]] = []
        while index < len(text) and text[index] != "`":
            if text[index] == "\\":
                index += 2
                continue
            if text.startswith("${", index):
                end = self.code_end(index + 2, "}")
                parts.append((index, text[index + 2 : end].strip()))
                index = end + 1
                continue
            static.append(text[index])
            index += 1
        found = _Literal("".join(static), tuple(parts), index + 1)
        self.found.append(found)
        return found


def _bare(expression: str) -> str:
    """The expression with its strings and nested template literals emptied.

    Args:
        expression: A JavaScript expression.

    Returns:
        It, each literal replaced by `""`.
    """
    out, index = [], 0
    scanner = _Scanner(expression)
    while index < len(expression):
        char = expression[index]
        if char in _QUOTES or char == "`":
            index = (
                _skip_string(expression, index)
                if char in _QUOTES
                else scanner.literal(index).end
            )
            out.append('""')
            continue
        out.append(char)
        index += 1
    return "".join(out)


def _split_top(expression: str, separator: str) -> list[str]:
    """Split at a separator found at depth 0.

    Args:
        expression: An expression whose literals are emptied.
        separator: `?`, `:`, `||`…

    Returns:
        The pieces.
    """
    pieces, depth, begin, index = [], 0, 0, 0
    while index < len(expression):
        char = expression[index]
        depth += (char in "([{") - (char in ")]}")
        if depth == 0 and expression.startswith(separator, index):
            if separator == "?" and expression.startswith(("??", "?."), index):
                index += 2
                continue
            pieces.append(expression[begin:index])
            index += len(separator)
            begin = index
            continue
        index += 1
    return [*pieces, expression[begin:]]


def _closes_at_end(bare: str, start: int) -> bool:
    """Tell whether the bracket opened before `start` closes at the very end.

    Args:
        bare: An expression whose literals are emptied.
        start: The index after the opening bracket.

    Returns:
        True when the closing one is the last character.
    """
    return _Scanner(bare).code_end(start, ")") == len(bare) - 1


_SCRIPT: Final = re.compile(r"<script\b[^>]*>(.*?)</script>", re.DOTALL)
_FUNCTION: Final = re.compile(
    r"^\s*(?:async\s+)?function\s+([\w$]+)\s*\(|^\s*(?:const|let)\s+([\w$]+)\s*=\s*"
    r"(?:async\s*)?(?:\([^)]*\)|[\w$]+)\s*=>",
    re.MULTILINE,
)
_TOP_STATEMENT: Final = re.compile(
    r"^(?:async\s+)?(?:function|const|let|var)\b", re.MULTILINE
)
_MAP_JOIN: Final = re.compile(
    r"^(.*)\.map\((.*)\)\.join\((?:\"\"|\"[^\"<]*\")?\)$", re.DOTALL
)
_ARROW: Final = re.compile(r"^(?:\([^)]*\)|[\w$]+)\s*=>\s*(.*)$", re.DOTALL)
_NAME: Final = re.compile(r"^[A-Za-z_$][\w$]*$")


def _scripts(path: Path) -> list[tuple[int, str]]:
    """The scripts of a template: the whole file for `.js.j2`, else its `<script>`s.

    Args:
        path: The template.

    Returns:
        (offset in the file, script text) pairs, Jinja comments blanked.
    """
    source = path.read_text(encoding="utf-8")
    text = _JINJA_COMMENT.sub(lambda found: " " * len(found.group()), source)
    if path.name.endswith(".js.j2"):
        return [(0, text)]
    return [(found.start(1), found.group(1)) for found in _SCRIPT.finditer(text)]


def _builders(scripts: list[str]) -> frozenset[str]:
    """The functions that build markup from a template literal of their own.

    Their literals are checked like any other: calling one is safe.

    Args:
        scripts: Every script of the package.

    Returns:
        Their names.
    """
    names: set[str] = set()
    for script in scripts:
        for found in _FUNCTION.finditer(script):
            following = _TOP_STATEMENT.search(script, found.end())
            body = script[found.end() : following.start() if following else len(script)]
            if "`" in body and _MARKUP.search(body):
                names.add(found.group(1) or found.group(2))
    return frozenset(names)


def _assigned(script: str, name: str) -> list[str]:
    """Every expression assigned to a variable in a script.

    Args:
        script: The script.
        name: The variable.

    Returns:
        The expressions (empty for a parameter: nothing proves it).
    """
    named = re.escape(name)
    found = re.finditer(
        rf"(?:\b(?:const|let|var)\s+|(?<![\w$.]))"
        rf"(?:\[[^\]]*\b{named}\b[^\]]*\]|{named})\s*\+?=(?![=>])\s*",
        script,
    )
    scanner = _Scanner(script)
    return [script[place.end() : scanner.code_end(place.end(), ";")] for place in found]


@dataclass(frozen=True, slots=True)
class Context:
    """What the check knows of a script: its builders and its assignments."""

    script: str
    builders: frozenset[str]


def is_safe(  # noqa: C901, PLR0911  # pylint: disable=too-complex,too-many-return-statements
    expression: str, context: Context, seen: frozenset[str] = frozenset()
) -> bool:
    """Tell whether an interpolated value is proven safe in markup.

    Safe: a literal (its own `${…}` are checked apart), a call of an escaping helper or
    of a markup builder, a translated text (`T.…`), a count, a choice between safe
    values, a `.map(builder).join("")`, a variable only ever assigned safe values.

    Args:
        expression: The JavaScript expression of a `${…}`.
        context: The script it is in.
        seen: Variables being resolved (a cycle proves nothing).

    Returns:
        True when it cannot carry markup from data.
    """
    bare = _bare(expression).strip()
    while bare.startswith("(") and bare.endswith(")") and _closes_at_end(bare, 1):
        bare = bare[1:-1].strip()
    if (
        bare == '""'
        or bare.lstrip("-").isdigit()
        or _NUMERIC.match(bare)
        or bare.startswith("T.")
    ):
        return "(" not in bare and "[" not in bare
    choice = _split_top(bare, "?")
    if len(choice) > 1:
        rest = _split_top("?".join(choice[1:]), ":")
        return all(is_safe(piece, context, seen) for piece in rest)
    for operator in ("||", "??", "&&", "+"):
        either = _split_top(bare, operator)
        if len(either) > 1:
            kept = either[1:] if operator == "&&" else either
            return all(is_safe(piece, context, seen) for piece in kept)
    mapped = _MAP_JOIN.match(bare)
    if mapped:
        mapper = mapped.group(2).strip()
        arrow = _ARROW.match(mapper)
        return (
            is_safe(arrow.group(1), context, seen)
            if arrow
            else mapper in context.builders
        )
    call = _CALL.match(bare)
    if call and _closes_at_end(bare, call.end()):
        named = call.group(1)
        return named in SAFE_CALLS or named.rpartition(".")[2] in context.builders
    if _NAME.match(bare) and bare not in seen:
        values = _assigned(context.script, bare)
        return bool(values) and all(
            is_safe(value, context, seen | {bare}) for value in values
        )
    return False


def holes_in(path: Path, builders: frozenset[str]) -> list[Hole]:
    """List the unproven interpolations of every markup literal of a template.

    Args:
        path: The template.
        builders: The markup builders of the package.

    Returns:
        The holes, in order.
    """
    source = path.read_text(encoding="utf-8")
    name = str(path.relative_to(SOURCES))
    holes: list[Hole] = []
    for offset, script in _scripts(path):
        scanner = _Scanner(script)
        scanner.code_end(0, "")
        context = Context(script, builders)
        for literal in scanner.found:
            if not _MARKUP.search(literal.static):
                continue
            holes.extend(
                Hole(name, source.count("\n", 0, offset + index) + 1, expression)
                for index, expression in literal.parts
                if not is_safe(expression, context)
            )
    return sorted(holes, key=lambda hole: hole.line)


def all_holes() -> list[Hole]:
    """Scan every template of the package.

    Returns:
        The holes of every `.j2` file.
    """
    paths = sorted(SOURCES.rglob("*.j2"))
    builders = _builders([script for path in paths for _o, script in _scripts(path)])
    return [hole for path in paths for hole in holes_in(path, builders)]
