"""Intruder files: a hint per extension (0509), a home tile opening the page (0515)."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.cli.home_tiles import home_tiles
from media_hygiene.constants import IMAGE_EXTENSIONS, RunKind
from media_hygiene.report.intruder_views import intruder_section
from media_hygiene.report.summary import ReportSummary
from media_hygiene.review.home_parts import Pill
from media_hygiene.review.intruders_views import intruders_state
from media_hygiene.scan.intruders import HINT_CACHE, HINT_KEEP, Intruder, hint
from media_hygiene.services.status import read_status
from tests.support.home_states import report
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from media_hygiene.review.home_parts import HomeTile
    from media_hygiene.services.runtime import Runtime

_FIXTURE: Final = Path(__file__).parents[1] / "fixtures" / "0.2.0" / "summary.json"
_MB: Final = 1024 * 1024
_AUDIT: Final = (RunKind.AUDIT, (0, 0))


@pytest.mark.parametrize(
    ("extension", "expected"),
    [
        (".ithmb", HINT_CACHE),
        (".zip", HINT_KEEP),
        (".7z", HINT_KEEP),
        (".pdf", HINT_KEEP),
        (".mp3", HINT_KEEP),
        (".mta", ""),
        (".mepx", ""),
        ("(none)", ""),
    ],
)
def test_each_extension_gets_a_cautious_hint_or_none(
    extension: str, expected: str
) -> None:
    """Cache, keep, or nothing for an extension nobody checked."""
    assert hint(extension) == expected


def test_the_report_and_the_page_carry_the_hint_of_extensions_only(
    tmp_path: Path,
) -> None:
    """The hint follows an extension's row, never a folder's."""
    found = (
        Intruder(Path("/data/c/Photos/a.ithmb"), 10, 0),
        Intruder(Path("/data/c/Photos/b.mta"), 5, 0),
    )
    runtime = make_runtime(make_locations(tmp_path))
    section = intruder_section(found, runtime.mapper)
    assert section is not None
    assert {row.name: row.hint for row in section.extensions} == {
        ".ithmb": HINT_CACHE,
        ".mta": "",
    }
    assert all(not row.hint for row in section.folders)
    state = intruders_state(found, (), (runtime.mapper, "x"))
    assert {row.key: row.hint for row in state.extensions}[".ithmb"] == HINT_CACHE
    assert all(not row.hint for row in state.folders)


def test_an_mpo_picture_is_a_photo_not_an_intruder() -> None:
    """MPO (3D / multi-frame JPEG): Pillow decodes it, so it is a photo."""
    assert ".mpo" in IMAGE_EXTENSIONS


def test_an_old_summary_loads_with_no_intruder() -> None:
    """`summary.json` of media-dedup 0.2: the new fields read 0."""
    summary = ReportSummary.model_validate_json(_FIXTURE.read_text(encoding="utf-8"))
    assert (summary.intruder_files, summary.intruder_bytes) == (0, 0)
    again = summary.model_copy(update={"intruder_files": 3, "intruder_bytes": 9})
    back = ReportSummary.model_validate_json(again.model_dump_json())
    assert (back.intruder_files, back.intruder_bytes) == (3, 9)


def _tiles(runtime: Runtime, intruders: tuple[int, int] | None) -> dict[str, HomeTile]:
    """The tiles after an audit that found these intruders (files, bytes), or none."""
    if intruders is not None:
        report(runtime, *_AUDIT)
        (path,) = runtime.locations.reports_dir.glob("*/summary.json")
        data = json.loads(path.read_text("utf-8"))
        data["intruder_files"], data["intruder_bytes"] = intruders
        path.write_text(json.dumps(data), "utf-8")
    return {tile.id: tile for tile in home_tiles(read_status(runtime))}


def test_the_tile_shows_the_weight_and_opens_the_page(tmp_path: Path) -> None:
    """Some intruders: their weight, their count, a click opens `review --intruders`."""
    runtime = make_runtime(make_locations(tmp_path))
    tile = _tiles(runtime, (262, 784 * _MB))["intruders"]
    assert tile.value == "784.0 MB"
    assert tile.sub == "262 files at the last audit, to set aside?"
    assert tile.pill is Pill.TODO
    assert tile.step == "review-intruders"


def test_no_intruder_says_none_and_leads_to_the_clean_space(tmp_path: Path) -> None:
    """None: the Clean space, never an empty page."""
    runtime = make_runtime(make_locations(tmp_path))
    tile = _tiles(runtime, (0, 0))["intruders"]
    assert (tile.value, tile.pill, tile.step, tile.space) == (
        "None",
        Pill.NONE,
        "",
        "clean",
    )


def test_before_any_audit_the_tile_waits(tmp_path: Path) -> None:
    """No audit yet: a dash."""
    tile = _tiles(make_runtime(make_locations(tmp_path)), None)["intruders"]
    assert (tile.value, tile.step) == ("—", "")


def test_faces_and_words_open_their_page_once_there_is_something(
    tmp_path: Path,
) -> None:
    """Faces found → `people`; words given → the Library; none yet → their space."""
    runtime = make_runtime(make_locations(tmp_path))
    status = read_status(runtime)
    before = {tile.id: tile.step for tile in home_tiles(status)}
    assert (before["faces"], before["words"]) == ("", "")
    later = replace(status, faces=(100, 20_614), tagged=(50, 100))
    after = {tile.id: tile.step for tile in home_tiles(later)}
    assert (after["faces"], after["words"]) == ("people", "search")
