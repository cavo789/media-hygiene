"""The grouping preview works on the files a real `classify` run works on (0646)."""

from __future__ import annotations

from contextlib import closing
from typing import TYPE_CHECKING

from media_hygiene.index.read_only import connect_read_only
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.classify import ClassifyService
from media_hygiene.services.grouping_look import GroupingLook
from tests.support.sorting import audited_library

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations


def test_preview_and_classify_count_the_same(locations: Locations) -> None:
    """Same files, same events, same photos in an event."""
    runtime = audited_library(locations)
    assert runtime.index_file is not None
    service = ClassifyService(runtime, NullProgress())
    inputs = service.collect()
    with closing(connect_read_only(runtime.index_file)) as connection:
        look = GroupingLook(runtime, connection)
        assert {file.path for file in look.files()} == {
            file.path for file in inputs.files
        }
        kept = runtime.settings.classify
        values = {
            "merge_gap_hours": kept.merge_gap_hours,
            "min_event_size": kept.min_event_size,
            "trip_min_km": kept.trip_min_km,
        }
        answer = look(values, values)
    real = service.decide(inputs).classification.events
    assert real
    assert answer["before"] == answer["after"]
    assert answer["after"] == {
        "events": len(real),
        "files": sum(len(event.paths) for event in real),
    }
