"""A narrowed `classify` (`--year`, `--path`) keeps the other edits for a later run."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from media_hygiene.classify.carry_models import EditSheet, LostWhy
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.carry import CarryRequest, carry_source
from media_hygiene.services.classify import ClassifyService
from media_hygiene.services.classify_output import write_classify_output
from tests.support.carrying import (
    DCIM,
    WEDDING,
    build_day,
    edit,
    final,
    plan_of,
    rename,
    run_classify,
)
from tests.support.runtime import make_runtime
from tests.support.scenes import Shot, write_shot

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.locations import Locations
    from media_hygiene.services.classify_output import ClassifyOutput
    from media_hygiene.services.runtime import Runtime

YEAR_2017 = (2017, 2017)


def run_narrowed(
    runtime: Runtime,
    years: tuple[int, int] | None = None,
    within: tuple[Path, ...] = (),
) -> ClassifyOutput:
    """Run `classify --year` / `--path` as the command does."""
    source = carry_source(runtime, CarryRequest())
    service = ClassifyService(runtime, NullProgress())
    inputs = service.collect(years)
    inputs = replace(inputs, scope=replace(inputs.scope, within=within))
    result = replace(service.decide(inputs), narrowed=True)  # as the command does
    written = write_classify_output(runtime, result, source)
    assert written is not None
    return written


def folders(written: ClassifyOutput) -> dict[str, str | None]:
    """File name → the folder its row goes to."""
    return {row.name: row.folder for row in plan_of(written).rows}


def edited_full_run(locations: Locations) -> Runtime:
    """A full run, then edits of 2017 and 2018 files and of the 2018 category."""
    build_day(locations.data_dir)
    write_shot(locations.data_dir / DCIM / "D0.jpg", Shot(60))  # dated by the disk
    runtime = make_runtime(locations)
    first = run_classify(runtime)
    edit(
        first.folder / "classify.xlsx",
        final("A0.jpg", "2017/Early")
        | final("M0.jpg", "2018/Kept")
        | final("D0.jpg", "Scans")
        | rename("Mariage", "Wedding"),
    )
    return runtime


def test_a_year_run_keeps_the_other_years_for_later(locations: Locations) -> None:
    """2017 carried; 2018 and the disk-dated file kept, not lost; a full run: all."""
    runtime = edited_full_run(locations)
    narrowed = run_narrowed(runtime, YEAR_2017)
    record = narrowed.carried
    assert record is not None
    assert record.edits == 1
    assert not record.lost
    assert record.deferred == 3  # M0, D0 and the category Mariage
    assert folders(narrowed)["A0.jpg"] == "2017/Early"
    assert "M0.jpg" not in folders(narrowed)
    full = run_classify(runtime)
    assert full.carried is not None
    assert not full.carried.lost
    assert not full.carried.deferred
    rows = folders(full)
    assert rows["A0.jpg"] == "2017/Early"
    assert rows["M0.jpg"] == "2018/Kept"
    assert rows["D0.jpg"] == "Scans"
    assert rows["M2.jpg"] == "2018/2018-06/Wedding"
    assert plan_of(full).deferred is None


def test_a_path_run_keeps_the_other_folders_and_a_second_narrow_run_too(
    locations: Locations,
) -> None:
    """`--path`: the wedding edits are kept, again by the next narrowed run."""
    runtime = edited_full_run(locations)
    dcim = (locations.data_dir / DCIM,)
    first = run_narrowed(runtime, within=dcim)
    assert first.carried is not None
    assert first.carried.deferred == 2  # M0 and the category Mariage
    assert not first.carried.lost
    again = run_narrowed(runtime, within=dcim)
    assert again.carried is not None
    assert again.carried.deferred == 2
    rows = folders(run_classify(runtime))
    assert rows["M0.jpg"] == "2018/Kept"
    assert rows["M2.jpg"] == "2018/2018-06/Wedding"


def test_a_file_deleted_is_still_gone(locations: Locations) -> None:
    """Out of the year but deleted: listed as gone, not kept."""
    runtime = edited_full_run(locations)
    (locations.data_dir / WEDDING / "M0.jpg").unlink()
    narrowed = run_narrowed(runtime, YEAR_2017)
    assert narrowed.carried is not None
    assert [(lost.sheet, lost.why) for lost in narrowed.carried.lost] == [
        (EditSheet.FILES, LostWhy.GONE)
    ]
    assert narrowed.carried.deferred == 2  # D0 and the category Mariage
