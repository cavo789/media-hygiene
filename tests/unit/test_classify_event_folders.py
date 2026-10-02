"""A "to sort" folder named after the file's own event is not a meaning (TODO 0048)."""

# classify works on naive local dates, as EXIF writes them.
# ruff: noqa: DTZ001

from __future__ import annotations

from datetime import datetime
from typing import Final

from media_hygiene.classify.event_folders import without_event_folders
from media_hygiene.classify.folders import FolderRules
from media_hygiene.classify.models import Event, SortReason
from media_hygiene.classify.signals import NO_SIGNAL, Signal
from tests.unit.test_classify_engine import shot

_WHEN: Final = datetime(2019, 7, 3, 10)
_LABEL: Final = "Seaside holidays"
_RULES: Final = FolderRules.build((), ((), ()))


def test_only_the_event_label_below_a_band_folder_is_dropped() -> None:
    """Below "To sort" and equal to the label: no signal; anything else is kept."""
    rendered = shot(f"2019/To sort/{_LABEL}/a.jpg", _WHEN)
    other = shot("2019/To sort/Beach/b.jpg", _WHEN)
    chosen = shot(f"2019/{_LABEL}/c.jpg", _WHEN)
    loose = shot("2019/To sort/d.jpg", _WHEN)
    alone = shot(f"2019/À trier/{_LABEL}/e.jpg", _WHEN)
    signals = {
        rendered.path: Signal(SortReason.EXISTING_FOLDER, _LABEL),
        other.path: Signal(SortReason.EXISTING_FOLDER, "Beach"),
        chosen.path: Signal(SortReason.EXISTING_FOLDER, _LABEL),
        alone.path: Signal(SortReason.EXISTING_FOLDER, _LABEL),
    }
    paths = (rendered.path, other.path, chosen.path, loose.path)
    event = Event("e1", _WHEN, _WHEN, paths, _LABEL)
    files = (rendered, other, chosen, loose, alone)
    event_of = dict.fromkeys(paths, event)
    event_of[alone.path] = Event("e2", _WHEN, _WHEN, (alone.path,))
    found = without_event_folders(files, (signals, event_of), _RULES)
    assert found[rendered.path] is NO_SIGNAL
    assert found[other.path].category == "Beach"
    assert found[chosen.path].category == _LABEL  # not below a band folder
    assert loose.path not in found
    assert found[alone.path].category == _LABEL  # its event has no label
