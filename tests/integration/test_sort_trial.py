"""0526: `sort --trial`: a sample (a month, a folder) first, then the rest."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from media_hygiene.errors import WorkbookError
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.sort import SortService
from media_hygiene.services.sort_inputs import find_workbook, load_inputs
from media_hygiene.services.sort_trial import LATEST, only_trial
from tests.integration.test_sort_event import SPRING, SPRING_SHOTS, two_events
from tests.support.sorting import PARTY, undo

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.locations import Locations
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.sort_models import SortResult


def run(runtime: Runtime, workbook: Path, sample: str | None) -> SortResult:
    """Sort the sample, or the whole workbook when None.

    Returns:
        The run.
    """
    service = SortService(runtime, NullProgress())
    inputs = load_inputs(runtime, find_workbook(runtime, str(workbook)))
    if sample is not None:
        inputs = only_trial(inputs, sample, runtime.mapper)
    return service.execute(service.prepare(inputs), lambda: False)


def test_one_month_first_then_the_rest(locations: Locations) -> None:
    """The trial moves only May 2017; the same plan then moves the rest only."""
    runtime, workbook, sizes = two_events(locations)
    data = locations.data_dir
    trial = run(runtime, workbook, "2017-05")
    assert trial.manifest.intact
    assert trial.manifest.moved == SPRING_SHOTS
    assert not list((data / SPRING).glob("*.jpg"))
    assert list((data / PARTY).glob("*.jpg"))
    rest = run(runtime, workbook, None)
    assert rest.manifest.moved >= sizes[max(sizes, key=lambda key: sizes[key])]
    trial_files = {entry.target for entry in trial.moves.moved}
    assert not trial_files & {entry.path for entry in rest.moves.moved}
    undo(runtime, rest.run_id)
    undo(runtime, trial.run_id)  # the trial is one undoable run
    assert len(list((data / SPRING).glob("*.jpg"))) == SPRING_SHOTS


def test_a_folder_or_a_month_by_name(locations: Locations) -> None:
    """A folder (host path) or `YYYY-MM` names the sample; an empty one is refused."""
    runtime, workbook, _sizes = two_events(locations)
    inputs = load_inputs(runtime, find_workbook(runtime, str(workbook)))
    folder = runtime.mapper.to_host(locations.data_dir / SPRING)
    by_folder = only_trial(inputs, folder, runtime.mapper)
    assert len(by_folder.plan.rows) == SPRING_SHOTS
    assert by_folder.cut
    assert len(only_trial(inputs, "2017-05", runtime.mapper).plan.rows) == SPRING_SHOTS
    latest = only_trial(inputs, LATEST, runtime.mapper).plan.rows
    dates = [row.date for row in inputs.plan.rows if row.date]
    assert latest
    assert all(row.date and row.date[:7] == max(dates)[:7] for row in latest)
    with pytest.raises(WorkbookError):
        only_trial(inputs, "1999-01", runtime.mapper)
