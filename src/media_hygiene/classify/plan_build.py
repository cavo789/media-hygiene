"""Build `plan.json` from the proposals: host paths, stable ids, events in scope."""

from __future__ import annotations

import hashlib
import uuid
from collections import Counter
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.plan_file import ClassifyPlan, PlanEvent, PlanRow, RowValues

if TYPE_CHECKING:
    from media_hygiene.classify.engine import Classification
    from media_hygiene.classify.models import Event, Proposal
    from media_hygiene.config.classify_settings import ClassifySettings
    from media_hygiene.paths.host_paths import HostPathMapper

_ID_LENGTH: Final = 16


def build_plan(
    classification: Classification,
    settings: ClassifySettings,
    mapper: HostPathMapper,
) -> ClassifyPlan:
    """Turn the proposals into a plan, in host paths.

    Args:
        classification: The proposals and the events.
        settings: `[classify]`: the layouts.
        mapper: Container ↔ host paths.

    Returns:
        The plan, rows in path order.
    """
    proposals = sorted(classification.proposals, key=lambda p: str(p.file.path))
    ids = _row_ids(proposals)
    rows = tuple(_row(p, ids[str(p.file.path)], mapper) for p in proposals)
    known = {str(p.file.path) for p in proposals}
    events = tuple(
        _event(event, ids)
        for event in classification.events
        if any(str(path) in known for path in event.paths)
    )
    return ClassifyPlan(
        plan_id=uuid.uuid4().hex,
        layout=settings.layout,
        unsure_layout=settings.unsure_layout,
        rows=rows,
        events=events,
        unused_rules=classification.unused_rules,
    )


def _row_ids(proposals: list[Proposal]) -> dict[str, str]:
    """Stable ids: the content's, with a suffix for the second copy of a file.

    Args:
        proposals: The proposals, in path order.

    Returns:
        Container path → row id.
    """
    ids: dict[str, str] = {}
    seen: Counter[str] = Counter()
    for proposal in proposals:
        file = proposal.file
        identity = file.digest or f"{file.path}|{file.size}"
        base = hashlib.sha256(identity.encode()).hexdigest()[:_ID_LENGTH]
        seen[base] += 1
        suffix = f"-{seen[base]}" if seen[base] > 1 else ""
        ids[str(file.path)] = base + suffix
    return ids


def _row(proposal: Proposal, row_id: str, mapper: HostPathMapper) -> PlanRow:
    """One row of the plan.

    Args:
        proposal: A proposal.
        row_id: Its stable id.
        mapper: Container ↔ host paths.

    Returns:
        The row.
    """
    file, dating = proposal.file, proposal.dating
    folder = proposal.folder
    root = file.root
    if proposal.target is not None and folder is not None:
        root = proposal.target
        for _segment in folder.split("/"):
            root = root.parent
    return PlanRow(
        id=row_id,
        path=mapper.to_host(file.path),
        size=file.size,
        mtime_ns=file.mtime_ns,
        sha256=file.digest,
        date=dating.when.isoformat(timespec="seconds") if dating else None,
        date_source=dating.source if dating else None,
        event_id=proposal.event_id,
        values=RowValues.of(proposal.values) if proposal.values else None,
        band=proposal.band,
        reason=proposal.reason,
        score=proposal.verdict.score,
        rule=proposal.rule,
        root=mapper.to_host(root),
        folder=folder,
        name=file.path.name,
    )


def _event(event: Event, ids: dict[str, str]) -> PlanEvent:
    """One event of the plan.

    Args:
        event: An event of the engine.
        ids: Container path → row id.

    Returns:
        The event, with the ids of its rows in scope.
    """
    return PlanEvent(
        id=event.event_id,
        start=event.start.isoformat(timespec="seconds"),
        end=event.end.isoformat(timespec="seconds"),
        span=event.span,
        label=event.label,
        rows=tuple(ids[str(path)] for path in event.paths if str(path) in ids),
    )
