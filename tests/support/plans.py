"""Classify plans written by hand: a row of 2016 in any band, a plan of rows."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.classify.models import Band, DateSource, SortReason
from media_hygiene.classify.plan_file import ClassifyPlan, PlanRow, RowValues

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.classify.plan_file import PlanEvent


def row(name: str, band: Band, tags: tuple[str, str] = ("", "")) -> PlanRow:
    """A row of 2016, in the band given; tags: its category and its event."""
    category, event = tags
    folders = {
        Band.SURE: f"2016/{category}",
        Band.UNSURE: f"2016/To check/{category}",
        Band.MANUAL: "2016/To sort/2016-07-14",
        Band.STAY: None,
    }
    return PlanRow(
        id=name,
        path=f"C:\\Photos\\DCIM\\{name}.jpg",
        size=1,
        mtime_ns=0,
        sha256=None,
        date="2016-07-14T10:00:00",
        date_source=DateSource.EXIF,
        event_id=event,
        values=RowValues(
            year=2016,
            month=7,
            day=14,
            category=category,
            event="2016-07-14",
            event_start="2016-07-14",
        ),
        band=band,
        reason=SortReason.EXISTING_FOLDER,
        score=90,
        root="C:\\Photos",
        folder=folders[band],
        name=f"{name}.jpg",
    )


def plan_of(rows: Sequence[PlanRow], events: Sequence[PlanEvent] = ()) -> ClassifyPlan:
    """A plan of these rows and events, laid out `{year}/{category}`."""
    return ClassifyPlan(
        plan_id="p",
        layout="{year}/{category}",
        unsure_layout="{year}/To check/{category}",
        rows=tuple(rows),
        events=tuple(events),
    )
