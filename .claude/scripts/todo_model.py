#!/usr/bin/env python3
"""Suggest the model a TODO should be implemented with: `sonnet` or `opus`.

/todo:run and /todo:iterate hand each TODO to a subagent; this picks its model from the
TODO itself, the same way every time, so the choice is cheap, testable and said aloud.

Rules, in order (the first that applies wins):
1. opus — the TODO touches the user's files or what protects them (a path of its
   `Files:` bullet matches RISKY_PATHS), names a risky subject in its text (RISKY_WORDS:
   cache, concurrency, a move, a deletion…), carries an `## Options` section or an open
   question, reports a past mistake, or lists more than MAX_SRC_FOR_SONNET source files;
2. sonnet — every listed file is text only (docs, translations, backlog, templates), or
   the TODO is Priority Low with at most MAX_SRC_FOR_SONNET source files;
3. opus — in doubt.

Usage: todo_model.py NNNN [todos-dir]
Output: one line, `<model>: <reason>`; exit 2 when the TODO is not found.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

MAX_SRC_FOR_SONNET = 3
NOT_FOUND = 2  # the exit code without a TODO
_WITH_ID = 2  # argv holds the script and the ID
# Paths whose change can lose or expose the user's photos, or break what protects them.
RISKY_PATHS = (
    "src/media_hygiene/actions/",
    "src/media_hygiene/index/",
    "src/media_hygiene/scan/",
    "src/media_hygiene/paths/",
    "src/media_hygiene/cli/templates/mh",
    "Dockerfile",
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


def listed_files(text: str) -> list[str]:
    """The paths of the `Files:` bullet.

    Args:
        text: The TODO.

    Returns:
        Each path written in backquotes there.
    """
    found = FILES.search(text)
    return PATH_IN_TEXT.findall(found.group(1)) if found else []


def _opus_reason(text: str, files: list[str]) -> str | None:
    """Why a TODO needs opus, if it does.

    Args:
        text: The TODO's whole file.
        files: The paths of its `Files:` bullet.

    Returns:
        The reason, or None when nothing calls for opus.
    """
    body = FILES.sub("", text)  # the words of the paths are not the subject
    sources = [path for path in files if path.startswith("src/")]
    risky = [path for path in files if path.startswith(RISKY_PATHS)]
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


def choose(text: str) -> tuple[str, str]:
    """Pick the model of a TODO.

    Args:
        text: The TODO's whole file.

    Returns:
        The model (`sonnet` or `opus`) and why, in a few words.
    """
    files = listed_files(text)
    if (why := _opus_reason(text, files)) is not None:
        return "opus", why
    if files and all(TEXT_ONLY.match(path) for path in files):
        return "sonnet", "text only (docs, translations, backlog)"
    priority = PRIORITY.search(text)
    if priority and priority.group(1).lower() == "low":
        sources = sum(path.startswith("src/") for path in files)
        return "sonnet", f"priority Low, {sources} source file(s)"
    return "opus", "in doubt"


def main(argv: list[str]) -> int:
    """Print the model suggested for a TODO.

    Args:
        argv: The command line.

    Returns:
        0, or 2 when the TODO is not found.
    """
    if len(argv) < _WITH_ID or not argv[1].isdigit():
        sys.stderr.write(__doc__.split("\n\n")[-2] + "\n")
        return NOT_FOUND
    todos = Path(argv[2]) if len(argv) > _WITH_ID else Path(".todos")
    path = find_todo(argv[1], todos)
    if path is None:
        sys.stderr.write(f"no open TODO {argv[1]} in {todos}\n")
        return NOT_FOUND
    model, why = choose(path.read_text(encoding="utf-8"))
    sys.stdout.write(f"{model}: {why}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
