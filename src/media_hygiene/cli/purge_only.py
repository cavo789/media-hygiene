"""`purge`: the files set aside that exist nowhere else, shown, asked apart (0688)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.console.formatting import human_number, human_size
from media_hygiene.i18n import _, ngettext
from media_hygiene.services.only_copies import only_copies

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime

_SHOWN: Final = 20  # the only copies listed by name; the rest counted


def confirm_only_copies(
    runtime: Runtime, quarantines: Sequence[Path], runs: Sequence[str]
) -> bool:
    """List the only copies about to be erased first, then ask for them apart.

    Args:
        runtime: Settings, mount points and output.
        quarantines: The default quarantine and the per-drive ones.
        runs: The runs about to be purged.

    Returns:
        True when there is none, or the user said yes for them too.
    """
    found = only_copies(quarantines, runtime.locations.journal_dir, runs)
    if not found.files:
        return True
    output = runtime.output
    count = len(found.files)
    output.warning(
        ngettext(
            "{count} file set aside exists nowhere else ({size}): a near duplicate, "
            "a burst shot, junk or unreadable, not an exact copy.",
            "{count} files set aside exist nowhere else ({size}): near duplicates, "
            "burst shots, junk or unreadable, not exact copies.",
            count,
        ).format(count=human_number(count), size=human_size(found.size))
    )
    for file in found.files[:_SHOWN]:
        output.info(f"  {runtime.mapper.to_host(file)}")
    if count > _SHOWN:
        output.info(
            _("  … and {count} more.").format(count=human_number(count - _SHOWN))
        )
    return output.confirm(
        ngettext(
            "Erase this only copy too?",
            "Erase these {count} only copies too?",
            count,
        ).format(count=human_number(count))
    )
