#!/usr/bin/env python3
"""List the feedback files of unattended runs that were never reviewed.

The inventory of `/todo:review-feedback`: a feedback file is reviewed once it
carries a `## Reviewed (<date>)` heading (written by the command when it closes
the file). Every other `feedback-*.md` is pending, whatever its age: oldest
first, with how many questions and deviations it holds, so a review never stops
at the newest file alone.

Usage: python3 .claude/scripts/feedback_pending.py [plans_dir]
(default: .claude/plans). One tab-separated line per pending file: path,
questions, deviations; then a total line.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

DEFAULT_DIR = ".claude/plans"
REVIEWED = re.compile(r"^## Reviewed\b", re.MULTILINE)
QUESTION = re.compile(r"\*\*Question\*\*", re.IGNORECASE)
DEVIATION = re.compile(r"\*\*Deviation\*\*", re.IGNORECASE)


def main() -> int:
    """Print the pending feedback files, oldest first.

    Returns:
        0 always (an empty list is not an error).
    """
    plans = Path(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DIR)
    files = sorted(plans.glob("feedback-*.md"), key=lambda path: path.stat().st_mtime)
    lines: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        if REVIEWED.search(text):
            continue
        questions = len(QUESTION.findall(text))
        deviations = len(DEVIATION.findall(text))
        lines.append(f"{path}\t{questions}Q\t{deviations}D")
    lines.append(f"PENDING: {len(lines)} of {len(files)}")
    sys.stdout.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
