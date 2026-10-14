#!/usr/bin/env python3
"""Gather everything the backlog waits for from the maintainer, in one list.

The questions are spread over many files: the `Needs maintainer` bullet of open TODOs,
the `### Not done` items of PARTIAL and BLOCKED TODOs, the unticked boxes of a review
file, the feedback files of unattended runs not reviewed yet. /todo:inbox reads this
list, sorts the items into what can be answered in a chat and what needs the
maintainer's machine, and asks.

Usage: todo_inbox.py [todos-dir] [measure-script]
  todos-dir       default .todos
  measure-script  a script that runs the pending measurements in one go (default
                  tests/measure/mh-measure.ps1): items of the TODOs it names are marked
                  `measured-by`.

Output: one record per item, blank-line separated:
  ID / STATE (open, partial, blocked, feedback) / FILE / TITLE / ITEM (first line) /
  REASON (its **Reason:**, when given) / UNBLOCKS (open TODOs whose Depends names it) /
  MEASURED-BY (the measure script, when it covers the TODO)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

STATES = {"": "open", "PARTIAL": "partial", "BLOCKED": "blocked"}
ID_IN_NAME = re.compile(r"(\d{3,4})-")
TODO_ID = re.compile(r"\b0\d{3}\b")
NEEDS = re.compile(r"^- \*\*Needs maintainer\*\*:\s*(.+)$", re.MULTILINE)
DEPENDS = re.compile(r"^- \*\*Depends\*\*:\s*(.+)$", re.MULTILINE)
REASON = re.compile(r"\*\*Reason:\*\*\s*(.+)")
type Record = dict[str, str]


def todo_files(todos: Path) -> list[tuple[str, Path]]:
    """Give the open, PARTIAL and BLOCKED TODO files, with their state.

    Returns:
        (state, path) pairs, sorted by path.
    """
    return [
        (state, path)
        for folder, state in STATES.items()
        for path in sorted((todos / folder).glob("*.md"))
        if path.name != "plan.md" and ID_IN_NAME.search(path.name)
    ]


def not_done(text: str) -> list[tuple[str, str]]:
    """Give the items of the `### Not done` section, and unticked boxes, with reasons.

    Returns:
        (item, reason) pairs; an item is its first line, a reason its first line too.
    """
    items: list[tuple[str, str]] = []
    section = text.split("### Not done", 1)[1] if "### Not done" in text else ""
    section = re.split(r"^#{1,3} ", section, maxsplit=1, flags=re.MULTILINE)[0]
    for block in re.split(r"^- ", section, flags=re.MULTILINE)[1:]:
        reason = REASON.search(block)
        items.append((block.splitlines()[0].strip(), reason[1] if reason else ""))
    items.extend(
        (box.strip(), "")
        for box in re.findall(r"^\s*- \[ \] (.+)$", text, re.MULTILINE)
    )
    return items


def records(todos: Path, measured: set[str]) -> list[Record]:
    """Collect one record per item waiting for the maintainer.

    Returns:
        The records, open TODOs first.
    """
    files = todo_files(todos)
    texts = {path: path.read_text(encoding="utf-8") for _, path in files}
    blocking: dict[str, list[str]] = {}
    for state, path in files:
        depends = DEPENDS.search(texts[path])
        for needed in TODO_ID.findall(depends[1] if depends else ""):
            if state == "open":
                blocking.setdefault(needed, []).append(_id(path))
    found: list[Record] = []
    for state, path in files:
        text, todo = texts[path], _id(path)
        title = text.splitlines()[0].lstrip("# ").strip()
        needs = NEEDS.search(text)
        items = [(needs[1], "")] if state == "open" and needs else []
        items += not_done(text) if state != "open" else []
        for item, reason in items:
            found.append(
                {
                    "ID": todo,
                    "STATE": state,
                    "FILE": str(path),
                    "TITLE": title,
                    "ITEM": item,
                    "REASON": reason,
                    "UNBLOCKS": ", ".join(blocking.get(todo, [])),
                    "MEASURED-BY": "yes" if todo in measured else "",
                }
            )
    return found


def feedback(plans: Path) -> list[Record]:
    """Give the feedback files of unattended runs that were not reviewed yet.

    Returns:
        One record per such file.
    """
    return [
        {
            "ID": "-",
            "STATE": "feedback",
            "FILE": str(path),
            "TITLE": path.stem,
            "ITEM": "not reviewed yet: /review-feedback",
            "REASON": "",
            "UNBLOCKS": "",
            "MEASURED-BY": "",
        }
        for path in sorted(plans.glob("feedback-*.md"))
        if "## Reviewed" not in path.read_text(encoding="utf-8")
    ]


def _id(path: Path) -> str:
    """Give the TODO number of a file name.

    Returns:
        Its digits, e.g. `0148`.
    """
    match = ID_IN_NAME.search(path.name)
    return match[1] if match else path.stem


def main() -> int:
    """Print the records; exit 0."""
    todos = Path(sys.argv[1] if len(sys.argv) > 1 else ".todos")
    script = Path(sys.argv[2] if len(sys.argv) > 2 else "tests/measure/mh-measure.ps1")  # noqa: PLR2004
    measured = (
        set(TODO_ID.findall(script.read_text(encoding="utf-8")))
        if script.is_file()
        else set()
    )
    found = records(todos, measured) + feedback(Path(".claude/plans"))
    blocks = (
        "\n".join(f"{key}: {value}" for key, value in record.items())
        for record in found
    )
    sys.stdout.write("\n\n".join(blocks) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
