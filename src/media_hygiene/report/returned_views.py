"""The report's section of the files set aside before that came back (0216)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.kinds import ActionKind
from media_hygiene.i18n import _
from media_hygiene.plan.returned import returned_moves
from media_hygiene.report.thumbnails import thumbnail_name

if TYPE_CHECKING:
    from datetime import datetime

    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.plan.models import CleanPlan
    from media_hygiene.plan.returned import ReturnedFile

# The files back shown in the report; the terminal and the plan count them all.
MAX_RETURNED_IN_REPORT: Final = 500


@dataclass(frozen=True, slots=True)
class ReturnedView:
    """One file back: where it is, when and why it was set aside, where it lay."""

    path: str
    size: int
    set_aside: datetime
    why: str
    run_id: str
    former: str
    thumbnail: str | None = None


@dataclass(frozen=True, slots=True)
class ReturnedSection:
    """The files back that `clean` sets aside again, and how many are not shown."""

    items: tuple[ReturnedView, ...] = ()
    hidden: int = 0


def why_set_aside(action: ActionKind) -> str:
    """Say why a content was set aside, in the user's words.

    Args:
        action: The action journaled when it was set aside.

    Returns:
        The translated reason.
    """
    reasons = {
        ActionKind.QUARANTINE_BURST: _("a burst shot you set aside"),
        ActionKind.QUARANTINE_NEAR: _("a near duplicate set aside"),
        ActionKind.QUARANTINE_CHOSEN: _("set aside in 'search' or 'browse'"),
        ActionKind.QUARANTINE_UNWANTED: _("an unwanted photo set aside"),
        ActionKind.MARK_GONE: _("deleted in the Explorer, on purpose"),
    }
    return reasons.get(action, _("set aside again after it came back"))


def returned_section(
    plan: CleanPlan, mapper: HostPathMapper, previews: frozenset[str]
) -> ReturnedSection:
    """Describe the files back, each with its preview when one was written.

    Args:
        plan: The plan.
        mapper: Translates container paths to host paths.
        previews: The names of the previews written.

    Returns:
        The section.
    """
    moves = returned_moves(plan)
    return ReturnedSection(
        items=tuple(
            _view(item, mapper, previews) for item in moves[:MAX_RETURNED_IN_REPORT]
        ),
        hidden=max(0, len(moves) - MAX_RETURNED_IN_REPORT),
    )


def _view(
    item: ReturnedFile, mapper: HostPathMapper, previews: frozenset[str]
) -> ReturnedView:
    """Describe one file back.

    Args:
        item: The file and what was remembered of it.
        mapper: Translates container paths to host paths.
        previews: The names of the previews written.

    Returns:
        Its view.
    """
    said = item.remembered
    name = thumbnail_name(item.file)
    return ReturnedView(
        path=mapper.to_host(item.file.path),
        size=item.file.size,
        set_aside=said.at,
        why=why_set_aside(said.action),
        run_id=said.run_id,
        former=said.host_path,
        thumbnail=name if name in previews else None,
    )
