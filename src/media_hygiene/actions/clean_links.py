"""Replace a duplicate copy by a hard link to its kept file: both names stay (0213).

The copy is compared byte for byte with the kept file first, as before a deletion.
Then a link to the kept file is made under a draft name in the copy's folder, and
`os.replace` puts it over the copy: the name always holds the copy or the link, never
nothing, even when the run is killed in between. Journaled as every change of a
clean: `pending`, the change, `done`. Across two disks or mounts, it is refused.
"""

from __future__ import annotations

import errno
import os
from functools import partial
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.album_links import UNSUPPORTED
from media_hygiene.actions.kinds import ActionKind
from media_hygiene.actions.link_move import same_file
from media_hygiene.actions.outcome import Incident
from media_hygiene.actions.verify import checked_removal
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.actions.journaled import JournaledChanges
    from media_hygiene.actions.outcome import Tally
    from media_hygiene.plan.models import KeepDecision
    from media_hygiene.scan.models import MediaFile

_DRAFT_SUFFIX: Final = ".media-hygiene-link"


def draft_of(path: Path) -> Path:
    """The draft name a link is made under, next to the name it replaces.

    Hidden, without a media extension: an audit never lists it.

    Args:
        path: The copy's name.

    Returns:
        `.<name>.media-hygiene-link`, in the same folder.
    """
    return path.with_name(f".{path.name}{_DRAFT_SUFFIX}")


class CopyLinker:
    """Makes copies hard links to their kept files, journaled, one file at a time."""

    def __init__(self, changes: JournaledChanges, tally: Tally) -> None:
        """Prepare the links of a run.

        Args:
            changes: Journals and counts each change.
            tally: Counters of the run: what is skipped, and why.
        """
        self._changes = changes
        self._tally = tally

    def link(self, decision: KeepDecision, file: MediaFile) -> None:
        """Replace a copy by a link to the kept file, once proven identical.

        Args:
            decision: The group decision, holding the kept file.
            file: The copy, which keeps its name.
        """
        keeper = decision.keeper.path
        removal = checked_removal(keeper, file.path, decision.size)
        reason = removal.reason or _device_refusal(keeper, file.path)
        if reason is not None:
            self._tally.skipped.append(Incident(file.path, reason))
            return
        entry = self._changes.entry(file, ActionKind.LINK_DUPLICATE).model_copy(
            update={"sha256": removal.sha256, "keeper": str(keeper)},
        )
        self._changes.act(entry, partial(replace_by_link, keeper, file.path))


def replace_by_link(keeper: Path, path: Path) -> None:
    """Put a hard link to `keeper` in place of `path`, in one rename.

    Args:
        keeper: The kept file.
        path: The copy's name: it holds the copy until the rename, the link after.

    Raises:
        BaseException: The rename failed or was interrupted: raised again once the
            draft is removed (the copy is left as it was).
    """
    draft = draft_of(path)
    _clear(draft, keeper)
    _link(keeper, draft)
    try:
        draft.replace(path)
    except BaseException:
        draft.unlink(missing_ok=True)
        raise


def _clear(draft: Path, keeper: Path) -> None:
    """Remove the draft a run killed before its rename left, never a user's file.

    Args:
        draft: The draft name.
        keeper: The kept file: a draft left by a run is another name of it.

    Raises:
        OSError: Another file has that name (nothing changed).
    """
    if not draft.exists():
        return
    if not same_file(draft, keeper):
        message = _("a file named {name} is in the way").format(name=draft.name)
        raise OSError(message)
    draft.unlink()


def _link(keeper: Path, draft: Path) -> None:
    """Make the draft a second name of the kept file.

    Args:
        keeper: The kept file.
        draft: The draft name, free.

    Raises:
        OSError: The link could not be made, said in the user's words.
    """
    try:
        os.link(keeper, draft)
    except OSError as exc:
        if exc.errno == errno.EXDEV:
            raise OSError(_cross_device()) from exc
        if exc.errno in UNSUPPORTED:
            message = _("this disk does not support hard links (FAT, exFAT, a NAS?)")
            raise OSError(message) from exc
        raise


def _device_refusal(keeper: Path, path: Path) -> str | None:
    """Tell why a copy cannot become a link to its kept file: two disks.

    Args:
        keeper: The kept file.
        path: The copy.

    Returns:
        The translated reason, or None when both lie on one filesystem.
    """
    if keeper.stat().st_dev == path.stat().st_dev:
        return None
    return _cross_device()


def _cross_device() -> str:
    """Say that a hard link cannot cross two disks.

    Returns:
        The translated reason.
    """
    return _(
        "the copy and its kept file are on two disks or two mounts: a hard link "
        "cannot cross them, the copy is left as it is"
    )
