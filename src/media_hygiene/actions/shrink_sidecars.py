"""After `shrink`: a sidecar named after the whole video follows its new name.

`clip.avi.xmp` describes `clip.avi`: once it is `clip.mp4`, the sidecar becomes
`clip.mp4.xmp` (journaled, `undo` moves it back), so that it stays paired. One named
after the stem (`clip.xmp`, `clip.thm`) keeps its pair: the stem does not change.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.kinds import ActionKind
from media_hygiene.actions.no_overwrite import move_no_replace
from media_hygiene.actions.outcome import Incident, why
from media_hygiene.actions.sort_moves import file_of

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.actions.journaled import JournaledChanges

_SIDECARS: Final = (".xmp", ".XMP")


def follow_sidecars(
    changes: JournaledChanges, skipped: list[Incident], names: tuple[Path, Path]
) -> None:
    """Rename the sidecars named after the whole video; one that cannot is said.

    Args:
        changes: The journaled changes of the run.
        skipped: Where a sidecar left where it was is counted.
        names: The video set aside, and the name of the lighter one.
    """
    original, final = names
    if final == original:
        return
    for suffix in _SIDECARS:
        sidecar = original.with_name(original.name + suffix)
        if not sidecar.is_file():
            continue
        moved = final.with_name(final.name + suffix)
        entry = changes.entry(file_of(sidecar), ActionKind.MOVE)
        entry = entry.model_copy(update={"target": str(moved)})
        try:
            changes.record(entry, partial(move_no_replace, sidecar, moved))
        except OSError as exc:
            skipped.append(Incident(sidecar, why(exc)))
