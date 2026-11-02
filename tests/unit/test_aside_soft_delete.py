"""0518: a file set aside is a soft delete for the albums, the burst review, the events.

Set aside (`chosen`) or left out of a burst, it no longer shows in an album nor its
TV, never enters an album from the burst review, and is never sent elsewhere by a
choice of the Events view; *Take out* of an album still reaches it.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, cast

from media_hygiene.classify.plan_file import ClassifyPlan, PlanRow
from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.report.burst_decisions import BurstDecision
from media_hygiene.report.chosen_decisions import ChosenFile
from media_hygiene.report.decisions import DecisionsFile
from media_hygiene.review.place import DEFAULT_DECISIONS
from media_hygiene.search.aside_filter import AsideFilter, Kept
from media_hygiene.search.events_aside import rows_kept
from media_hygiene.services import album_pages
from media_hygiene.services.aside_paths import review_picker, set_aside
from media_hygiene.services.sort_event import not_aside
from media_hygiene.services.sort_inputs import SortInputs
from media_hygiene.share.album_api import AlbumAsked
from media_hygiene.share.album_pickers import KeyPicker
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from media_hygiene.classify.page_overlay import Overlaid
    from media_hygiene.review.session import ReviewSession
    from media_hygiene.review.sort_batch import SortBatchSession
    from media_hygiene.search.events_desk import EventsDesk
    from media_hygiene.services.album_reader import AlbumReader
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.share.album_shelf import Shown

MAPPER = HostPathMapper(Path("/data"))
PATHS = {"a": Path("/data/c/a.jpg"), "b": Path("/data/c/b.jpg")}
ASIDE = frozenset({MAPPER.to_host(PATHS["b"])})


def _runtime(tmp_path: Path, decisions: DecisionsFile) -> Runtime:
    runtime = make_runtime(make_locations(tmp_path))
    target = runtime.locations.reports_dir / DEFAULT_DECISIONS
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(decisions.model_dump_json(), encoding="utf-8")
    return runtime


def test_set_aside_reads_the_files_chosen_and_the_burst_shots_left_out(
    tmp_path: Path,
) -> None:
    """Both kinds of set aside count; no decisions file: nothing set aside."""
    assert set_aside(make_runtime(make_locations(tmp_path / "none"))) == frozenset()
    decisions = DecisionsFile(
        version=1,
        roots=("C:\\",),
        chosen=(ChosenFile(path=r"C:\a.jpg", size=1, mtime_ns=1),),
        bursts=(BurstDecision(kept=(r"C:\k.jpg",), discarded=(r"C:\d.jpg",)),),
    )
    assert set_aside(_runtime(tmp_path, decisions)) == {r"C:\a.jpg", r"C:\d.jpg"}


def test_the_burst_review_never_adds_a_shot_set_aside_to_an_album() -> None:
    """Its picker drops the shot, but *Take out* still reaches it."""
    picker = KeyPicker(PATHS.get, AsideFilter(lambda: ASIDE, MAPPER))
    add = AlbumAsked(album="Trip", action="add", keys=("a", "b"))
    assert picker.files(add) == Kept((PATHS["a"],), 1)
    remove = add.model_copy(update={"action": "remove"})
    assert picker.files(remove) == Kept((PATHS["a"], PATHS["b"]))


def test_the_burst_review_reads_its_own_choices_too(tmp_path: Path) -> None:
    """A shot left out in the review, not yet in the reports folder, is dropped."""
    runtime = make_runtime(make_locations(tmp_path))
    host = runtime.mapper.to_host(PATHS["b"])
    decisions = DecisionsFile(
        version=1,
        roots=("C:\\",),
        bursts=(BurstDecision(kept=("k",), discarded=(host,)),),
    )
    session = SimpleNamespace(preview_source=PATHS.get, decisions=lambda: decisions)
    picker = review_picker(runtime, cast("ReviewSession", session))
    asked = AlbumAsked(album="Trip", action="tv", keys=("a", "b"))
    assert picker(asked).files == (PATHS["a"],)


def test_the_albums_page_cannot_bring_back_a_file_set_aside_since() -> None:
    """A page shown before *Set aside*: its TV and its add leave the file out."""
    reader = SimpleNamespace(source=lambda key: PATHS["a" if key == 1 else "b"])
    shown = SimpleNamespace(picked=lambda _keys: (1, 2))
    sources = (
        cast("AlbumReader", reader),
        cast("Shown", shown),
        AsideFilter(lambda: ASIDE, MAPPER),
    )
    tv = AlbumAsked(album="Trip", action="tv", keys=("1", "2"))
    assert album_pages._picked(sources, tv) == Kept((PATHS["a"],), 1)  # noqa: SLF001  # pylint: disable=protected-access
    remove = tv.model_copy(update={"action": "remove"})
    assert len(album_pages._picked(sources, remove).files) == 2  # noqa: SLF001  # pylint: disable=protected-access


def test_an_events_choice_of_photos_leaves_the_file_set_aside_out() -> None:
    """`POST /api/sort/files`: the row of the file set aside is dropped server-side."""
    desk = SimpleNamespace(chosen=lambda: ASIDE, mapper=MAPPER)
    session = SimpleNamespace(preview_source=PATHS.get)
    body = json.dumps({"event": "e1", "rows": ["a", "b", "z"], "category": "Pets"})
    kept = rows_kept(
        cast("EventsDesk", desk), cast("SortBatchSession", session), body.encode()
    )
    assert json.loads(kept) == {"event": "e1", "rows": ["a", "z"], "category": "Pets"}
    assert rows_kept(cast("EventsDesk", desk), cast("SortBatchSession", session), b"x")


def test_sort_this_event_now_leaves_the_files_set_aside_in_place() -> None:
    """The plan cut to an event loses the rows of the files set aside."""
    # model_construct skips validation: only the fields not_aside reads are given.
    fields: tuple[dict[str, Any], ...] = (
        {"id": "1", "path": r"C:\a.jpg"},
        {"id": "2", "path": r"C:\b.jpg"},
    )
    rows = tuple(PlanRow.model_construct(**row) for row in fields)
    plan: dict[str, Any] = {"rows": rows}
    inputs = SortInputs(
        workbook=Path("/reports/w.xlsx"),
        plan=ClassifyPlan.model_construct(**plan),
        page=cast("Overlaid", None),
        saved_at=datetime.now(tz=UTC),
        open_elsewhere=False,
    )
    assert not_aside(inputs, frozenset()) is inputs
    cut = not_aside(inputs, frozenset({r"C:\b.jpg"}))
    assert [row.id for row in cut.plan.rows] == ["1"]
    assert cut.cut
