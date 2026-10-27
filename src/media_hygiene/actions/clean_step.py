"""The progress step of a clean run, worded after what happens to the copies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.constants import BrokenReason
from media_hygiene.i18n import _
from media_hygiene.scan.progress import Step

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.scan.models import BrokenFile, MediaFile

# One action of a run: the file, what the screen says of it, the change itself.
type Planned = tuple[MediaFile, str, Callable[[], object]]


@dataclass(frozen=True, slots=True)
class CleanLabels:  # pylint: disable=too-many-instance-attributes
    """What the line under the bar says about the file being handled (`{path}`)."""

    copy: str
    linked: str
    near: str
    burst: str
    chosen: str
    unwanted: str
    returned: str
    unreadable: str
    empty: str
    orphan: str

    def of_broken(self, item: BrokenFile) -> str:
        """The label of a broken file: an empty one is deleted, others set aside.

        Args:
            item: The broken file.

        Returns:
            Its label.
        """
        return self.empty if item.reason is BrokenReason.EMPTY else self.unreadable


def clean_labels(*, delete_copies: bool) -> CleanLabels:
    """The translated labels of a run.

    Args:
        delete_copies: `clean --delete`: copies of media are deleted for good.

    Returns:
        The labels.
    """
    kept_aside = _("Moving a duplicate copy to the quarantine: {path}")
    return CleanLabels(
        copy=_("Deleting a duplicate copy: {path}") if delete_copies else kept_aside,
        linked=_("Replacing a duplicate copy by a link to the kept file: {path}"),
        near=_("Moving a near duplicate to the quarantine: {path}"),
        burst=_("Moving a burst shot set aside to the quarantine: {path}"),
        chosen=_("Moving a file you set aside to the quarantine: {path}"),
        unwanted=_("Moving an unwanted photo you set aside to the quarantine: {path}"),
        returned=_("Moving a file you had set aside, back, to the quarantine: {path}"),
        unreadable=_("Moving an unreadable file to the quarantine: {path}"),
        empty=_("Deleting an empty file (0 bytes): {path}"),
        orphan=_("Moving an orphan sidecar to the quarantine: {path}"),
    )


def clean_step(actions: Sequence[Planned], *, delete_copies: bool) -> Step:
    """The title of the clean step, and what it really does to the copies.

    Args:
        actions: Every action of the run: the estimate follows the bytes they handle.
        delete_copies: `clean --delete`: copies of media are deleted for good.

    Returns:
        The translated step.
    """
    if delete_copies:
        hint = _(
            "Each copy is compared again with the kept one before deletion; "
            "unreadable files go to the quarantine."
        )
    else:
        hint = _(
            "Each copy is compared again with the kept one before going to the "
            "quarantine; unreadable files go there too."
        )
    weight = sum(file.size for file, _label, _change in actions)
    return Step(_("Cleaning"), hint, total_weight=weight)


def said(planned: Planned, mapper: HostPathMapper) -> str:
    """The line under the bar for one action: its label, with the Windows path.

    Args:
        planned: The file, its label and its action.
        mapper: Host/container path translator.

    Returns:
        The line to show.
    """
    file, label, _change = planned
    return label.format(path=mapper.to_host(file.path))
