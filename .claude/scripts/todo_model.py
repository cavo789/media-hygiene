#!/usr/bin/env python3
"""Suggest the model a TODO should be implemented with: `sonnet` or `opus`.

/todo:run and /todo:iterate hand each TODO to a subagent; this picks its model from the
TODO itself, the same way every time, so the choice is cheap, testable and said aloud.

Rules, in order (the first that applies wins):
1. opus — the TODO touches the user's files or what protects them (a path of its
   `Files:` bullet matches DEFAULT_RISKY or a glob of the project's RISKY_FILE), names a
   risky subject (RISKY_WORDS: cache, concurrency, a move, a deletion…), carries an
   `## Options` section or an open question, reports a past mistake, or lists more than
   MAX_SRC_FOR_SONNET source files;
2. sonnet — every listed file is text only (docs, translations, backlog, templates), or
   the TODO is Priority Low with at most MAX_SRC_FOR_SONNET source files;
3. opus — in doubt.

Usage: todo_model.py NNNN [NNNN ...] [todos-dir]
Output: one line per ID, `<id> <model>: <reason>`; exit 2 when a TODO is not found.
RISKY_FILE is read next to the backlog folder (`<todos-dir>/../.config/`): one glob per
line, `#` comments, matched with fnmatch against each path and its file name.
"""

from __future__ import annotations

import fnmatch
import re
import sys
from pathlib import Path

MAX_SRC_FOR_SONNET = 3
NOT_FOUND = 2  # the exit code without a TODO
RISKY_FILE = ".config/todo_model_risky_paths.txt"
# Globs risky in any project: images, environments, secrets, database migrations.
DEFAULT_RISKY = (
    "Dockerfile*",
    "*compose*.y*ml",
    ".devcontainer/*",
    "install*.sh",
    ".env*",
    "*migrations/*",
    "*.sql",
)
RISKY_WORDS = re.compile(
    r"\b(cache|concurren\w*|race|lock|journal|undo|quarantin\w*|delet\w*|move[sd]?|"
    r"rename\w*|migrat\w*|schema)\b",
    re.IGNORECASE,
)
OPEN_QUESTION = re.compile(
    r"^## Options\b|\bopen question\b|\bto decide\b", re.MULTILINE
)
PAST_MISTAKE = re.compile(
    r"\b(regression|went red|past mistake|broke)\b", re.IGNORECASE
)
# Files that hold text only: docs, translations, the backlog, page and console texts.
TEXT_ONLY = re.compile(r"^(documentation/|\.todos/|README|.*\.po$|.*\.pot$|.*\.md$)")
FILES = re.compile(r"^- \*\*Files\*\*:\s*(.+)$", re.MULTILINE)
PRIORITY = re.compile(r"^- \*\*Priority\*\*:\s*(\w+)", re.MULTILINE)
PATH_IN_TEXT = re.compile(r"`([^`]+)`")


def find_todo(number: str, todos: Path) -> Path | None:
    """Find the open TODO file of a number.

    Args:
        number: Its ID, any width (`448` or `0448`).
        todos: The backlog folder.

    Returns:
        Its path, or None.
    """
    wanted = int(number)
    for path in sorted(todos.glob("*.md")):
        head = re.match(r"(\d+)-", path.name)
        if head and int(head.group(1)) == wanted:
            return path
    return None


def risky_globs(todos: Path) -> tuple[str, ...]:
    """The risky globs: the generic defaults, then the project's file.

    Args:
        todos: The backlog folder; the project's file is read next to it.

    Returns:
        Every glob, defaults first.
    """
    path = todos.parent / RISKY_FILE
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    own = (line.split("#", 1)[0].strip() for line in lines)
    return DEFAULT_RISKY + tuple(glob for glob in own if glob)


def is_risky(path: str, globs: tuple[str, ...]) -> bool:
    """Whether a path matches a risky glob, by its whole path or its file name.

    Args:
        path: A path of the `Files:` bullet.
        globs: The risky globs.

    Returns:
        True when one matches.
    """
    name = path.rsplit("/", 1)[-1]
    return any(
        fnmatch.fnmatch(path, glob) or fnmatch.fnmatch(name, glob) for glob in globs
    )


def listed_files(text: str) -> list[str]:
    """The paths of the `Files:` bullet.

    Args:
        text: The TODO.

    Returns:
        Each path written in backquotes there.
    """
    found = FILES.search(text)
    return PATH_IN_TEXT.findall(found.group(1)) if found else []


def _opus_reason(text: str, files: list[str], globs: tuple[str, ...]) -> str | None:
    """Why a TODO needs opus, if it does.

    Args:
        text: The TODO's whole file.
        files: The paths of its `Files:` bullet.
        globs: The risky path globs.

    Returns:
        The reason, or None when nothing calls for opus.
    """
    body = FILES.sub("", text)  # the words of the paths are not the subject
    sources = [path for path in files if path.startswith("src/")]
    risky = [path for path in files if is_risky(path, globs)]
    word = RISKY_WORDS.search(body)
    reasons = (
        (
            bool(risky),
            f"touches {risky[0] if risky else ''} (user files or what protects them)",
        ),
        (word is not None, f"risky subject: {word.group(0).lower() if word else ''}"),
        (OPEN_QUESTION.search(text) is not None, "has options or an open question"),
        (PAST_MISTAKE.search(text) is not None, "reports a past mistake"),
        (len(sources) > MAX_SRC_FOR_SONNET, f"{len(sources)} source files"),
    )
    return next((why for applies, why in reasons if applies), None)


def choose(text: str, globs: tuple[str, ...] = DEFAULT_RISKY) -> tuple[str, str]:
    """Pick the model of a TODO.

    Args:
        text: The TODO's whole file.
        globs: The risky path globs (`risky_globs`).

    Returns:
        The model (`sonnet` or `opus`) and why, in a few words.
    """
    files = listed_files(text)
    if (why := _opus_reason(text, files, globs)) is not None:
        return "opus", why
    if files and all(TEXT_ONLY.match(path) for path in files):
        return "sonnet", "text only (docs, translations, backlog)"
    priority = PRIORITY.search(text)
    if priority and priority.group(1).lower() == "low":
        sources = sum(path.startswith("src/") for path in files)
        return "sonnet", f"priority Low, {sources} source file(s)"
    return "opus", "in doubt"


def main(argv: list[str]) -> int:
    """Print the model suggested for each TODO given.

    Args:
        argv: The command line: IDs, then the backlog folder (optional).

    Returns:
        0, or 2 when no ID is given or a TODO is not found.
    """
    ids = [arg for arg in argv[1:] if arg.isdigit()]
    others = [arg for arg in argv[1:] if not arg.isdigit()]
    if not ids or len(others) > 1:
        sys.stderr.write(__doc__.split("\n\n")[-2] + "\n")
        return NOT_FOUND
    todos = Path(others[0]) if others else Path(".todos")
    globs = risky_globs(todos)
    status = 0
    for number in ids:
        path = find_todo(number, todos)
        if path is None:
            sys.stderr.write(f"no open TODO {number} in {todos}\n")
            status = NOT_FOUND
            continue
        model, why = choose(path.read_text(encoding="utf-8"), globs)
        sys.stdout.write(f"{number} {model}: {why}\n")
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv))
