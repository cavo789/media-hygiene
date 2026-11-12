"""`purge`: the files set aside that exist nowhere else, shown before its one question.

0688 asked for them apart, after the first question; 0699 shows them first, then the
one question names them (seeing first, 0524): one informed decision.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.console.formatting import human_number, human_size
from media_hygiene.i18n import _, ngettext
from media_hygiene.services.only_copies import SHOWN, only_copies

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime


def show_only_copies(
    runtime: Runtime, quarantines: Sequence[Path], runs: Sequence[str]
) -> int:
    """List the only copies about to be erased, before any question.

    Args:
        runtime: Settings, mount points and output.
        quarantines: The default quarantine and the per-drive ones.
        runs: The runs about to be purged.

    Returns:
        How many there are (0: nothing shown).
    """
    found = only_copies(quarantines, runtime.locations.journal_dir, runs)
    count = len(found.files)
    if not count:
        return 0
    output = runtime.output
    output.warning(
        ngettext(
            "{count} file set aside exists nowhere else ({size}): a near duplicate, "
            "a burst shot, junk or unreadable, not an exact copy.",
            "{count} files set aside exist nowhere else ({size}): near duplicates, "
            "burst shots, junk or unreadable, not exact copies.",
            count,
        ).format(count=human_number(count), size=human_size(found.size))
    )
    for file in found.files[:SHOWN]:
        output.info(f"  {runtime.mapper.to_host(file)}")
    if count > SHOWN:
        output.info(
            _("  … and {count} more.").format(count=human_number(count - SHOWN))
        )
    return count


def with_only_copies(question: str, count: int) -> str:
    """Name the only copies in the purge's one question.

    Args:
        question: The purge's question.
        count: How many only copies it erases (0: the question as it is).

    Returns:
        The question, then what it erases with no other copy.
    """
    if not count:
        return question
    named = ngettext(
        "That includes the {count} file listed above, which exists nowhere else.",
        "That includes the {count} files listed above, which exist nowhere else.",
        count,
    )
    return f"{question} {named.format(count=human_number(count))}"


def ask_once(
    runtime: Runtime, question: str, scope: tuple[Sequence[Path], Sequence[str]]
) -> bool:
    """Show the only copies, then ask the purge's one question naming them.

    Args:
        runtime: Settings, mount points and output.
        question: The purge's question.
        scope: The quarantines, and the runs about to be purged.

    Returns:
        True when the user said yes.
    """
    only = show_only_copies(runtime, *scope)
    return runtime.output.confirm(with_only_copies(question, only))
