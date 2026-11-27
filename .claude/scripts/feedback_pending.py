#!/usr/bin/env python3
"""List the feedback files of unattended runs that were never reviewed; close one.

The inventory of `/todo:review-feedback`. The location is the state: a pending
file sits at the top of the plans folder (`feedback-*.md`), a reviewed one was
moved to its `reviewed/` subfolder, so the listing reads no file it does not
report on, however many runs were ever made. Pending files come oldest first,
with how many questions and deviations each holds, so a review never stops at
the newest file alone.

Usage:
    feedback_pending.py [plans_dir]
        One tab-separated line per pending file: path, questions, deviations;
        then a total line. Default plans_dir: .claude/plans.
    feedback_pending.py done FILE [--note TEXT]
        Append `## Reviewed (<date>)` (and the note) to FILE, then move it to
        `reviewed/` next to it. Prints the new path.
"""

from __future__ import annotations

import datetime as dt
import re
import sys
from pathlib import Path

DEFAULT_DIR = ".claude/plans"
REVIEWED_DIR = "reviewed"
QUESTION = re.compile(r"\*\*Question\*\*", re.IGNORECASE)
DEVIATION = re.compile(r"\*\*Deviation\*\*", re.IGNORECASE)
_DONE_ARGS = 2  # `done FILE`
_NOTE_ARGS = 4  # `done FILE --note TEXT`


def pending(plans: Path) -> list[str]:
    """Give the lines of the pending feedback files, oldest first.

    Args:
        plans: The plans folder.

    Returns:
        One line per pending file, then the total line.
    """
    files = sorted(plans.glob("feedback-*.md"), key=lambda path: path.stat().st_mtime)
    lines: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        questions = len(QUESTION.findall(text))
        deviations = len(DEVIATION.findall(text))
        lines.append(f"{path}\t{questions}Q\t{deviations}D")
    lines.append(f"PENDING: {len(files)}")
    return lines


def done(path: Path, note: str = "") -> Path:
    """Mark a feedback file reviewed and move it to `reviewed/`.

    Args:
        path: The feedback file.
        note: The decisions, written under the heading (optional).

    Returns:
        Its new path.
    """
    today = dt.datetime.now(tz=dt.UTC).date().isoformat()
    text = path.read_text(encoding="utf-8").rstrip("\n")
    closing = f"\n\n## Reviewed ({today})\n" + (f"\n{note}\n" if note else "")
    path.write_text(text + closing, encoding="utf-8")
    target = path.parent / REVIEWED_DIR / path.name
    target.parent.mkdir(exist_ok=True)
    return path.rename(target)


def main(argv: list[str]) -> int:
    """List the pending files, or close one with `done`.

    Args:
        argv: The command line.

    Returns:
        0, or 2 on a wrong `done` call.
    """
    args = argv[1:]
    if args[:1] == ["done"]:
        valid = len(args) == _DONE_ARGS or (
            len(args) == _NOTE_ARGS and args[2] == "--note"
        )
        if not valid or not Path(args[1]).is_file():
            sys.stderr.write("usage: feedback_pending.py done FILE [--note TEXT]\n")
            return 2
        moved = done(Path(args[1]), args[3] if len(args) == _NOTE_ARGS else "")
        sys.stdout.write(f"{moved}\n")
        return 0
    plans = Path(args[0] if args else DEFAULT_DIR)
    sys.stdout.write("\n".join(pending(plans)) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
