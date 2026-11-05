"""0597: an undated file takes the day of its sidecar in `classify` and in a move.

Sidecars are read at each run, never kept: a day written, undone or moved with its file
needs no invalidation. The tests below hold each event.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, Final, cast

from media_hygiene.classify.dating import DatingContext, dating_of
from media_hygiene.classify.dating_models import DateSource
from media_hygiene.classify.folders import FolderRules
from media_hygiene.classify.models import MediaInput
from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.scan.models import VisualFacts
from media_hygiene.search import move_go
from media_hygiene.services.classify_inputs import with_sidecar_days
from media_hygiene.services.selection_move import SelectionMover
from media_hygiene.tags.xmp_date import with_day

if TYPE_CHECKING:
    import pytest

    from media_hygiene.search.rule_desk import RuleDesk
    from media_hygiene.services.selection_models import Picked

_DAY: Final = "2019-07-14"
_NOON: Final = datetime(2019, 7, 14, 12)  # noqa: DTZ001 - naive local, like EXIF
_NO_MONTH: Final = "no month"


def _written(photo: Path, day: str = _DAY) -> Path:
    """A photo and its sidecar holding a day."""
    photo.parent.mkdir(parents=True, exist_ok=True)
    photo.write_bytes(b"photo")
    sidecar = photo.with_name(f"{photo.name}.xmp")
    content = with_day(None, day, "media-hygiene 9.9")
    assert content is not None
    sidecar.write_bytes(content)
    return sidecar


def _input(path: Path, taken: str | None = None) -> MediaInput:
    """An input, with an EXIF date or none."""
    visual = VisualFacts(0, 0, 1, 1, 0.0, taken) if taken else None
    return MediaInput(path, path.parent, 5, 0, visual=visual)


def _read(path: Path) -> datetime | None:
    """The day `classify` reads for one undated file."""
    return with_sidecar_days([_input(path)], UTC)[0].sidecar_day


def test_the_sidecar_s_day_is_read_for_an_undated_file(tmp_path: Path) -> None:
    """Written: at noon that day."""
    photo = tmp_path / "a.jpg"
    _written(photo)
    assert _read(photo) == _NOON


def test_a_date_of_its_own_wins_and_its_folder_is_not_listed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A dated file never reads its sidecar: most collections read no file here."""
    photo = tmp_path / "a.jpg"
    _written(photo)

    def forbidden(_paths: object) -> None:
        raise AssertionError

    monkeypatch.setattr("media_hygiene.services.classify_inputs.moments_of", forbidden)
    dated = _input(photo, "2001:02:03 10:00:00")
    assert with_sidecar_days([dated], UTC)[0].sidecar_day is None


def test_undone_the_day_is_gone_at_the_next_read(tmp_path: Path) -> None:
    """`undo` removes the sidecar: nothing kept says the day any more."""
    photo = tmp_path / "a.jpg"
    sidecar = _written(photo)
    assert _read(photo) == _NOON
    sidecar.unlink()
    assert _read(photo) is None


def test_edited_the_new_day_counts(tmp_path: Path) -> None:
    """A sidecar rewritten in place, its size and time the same or not: read again."""
    photo = tmp_path / "a.jpg"
    _written(photo)
    assert _read(photo) == _NOON
    _written(photo, "2020-01-02")
    assert _read(photo) == datetime(2020, 1, 2, 12)  # noqa: DTZ001


def test_moved_with_its_sidecar_the_day_follows(tmp_path: Path) -> None:
    """`sort`, or a folder renamed in Explorer: found by its name beside the file."""
    photo = tmp_path / "old" / "a.jpg"
    _written(photo)
    (tmp_path / "old").rename(tmp_path / "new")
    assert _read(tmp_path / "new" / "a.jpg") == _NOON


def test_moved_without_its_sidecar_the_day_stays_behind(tmp_path: Path) -> None:
    """The file alone in Explorer: undated again, never a day guessed from elsewhere."""
    photo = tmp_path / "old" / "a.jpg"
    _written(photo)
    target = tmp_path / "new"
    target.mkdir()
    moved = target / "a.jpg"
    photo.rename(moved)
    assert _read(moved) is None


def test_a_sidecar_alone_moved_gives_its_day_to_the_file_beside_it(
    tmp_path: Path,
) -> None:
    """The name decides, as for every sidecar reader: the file it now lies beside."""
    photo = tmp_path / "old" / "a.jpg"
    sidecar = _written(photo)
    target = tmp_path / "new"
    target.mkdir()
    other = target / "a.jpg"
    other.write_bytes(b"photo")
    sidecar.rename(target / sidecar.name)
    assert _read(other) == _NOON
    assert _read(photo) is None


def test_a_day_that_is_no_day_is_ignored(tmp_path: Path) -> None:
    """`2019-13-45` from another application: no date, no failure."""
    photo = tmp_path / "a.jpg"
    sidecar = _written(photo)
    sidecar.write_bytes(sidecar.read_bytes().replace(_DAY.encode(), b"2019-13-45"))
    assert _read(photo) is None


def test_the_chain_puts_the_sidecar_above_the_name_and_below_the_camera() -> None:
    """The user's day beats a name's or a folder's, never the file's own."""
    context = DatingContext(FolderRules.build((), ((), ())), (), UTC)
    path = Path("/data/c/2001/a.jpg")
    found = dating_of(
        MediaInput(path, Path("/data/c"), 5, 0, sidecar_day=_NOON), context
    )
    assert (found.when, found.source) == (_NOON, DateSource.SIDECAR)
    own = VisualFacts(0, 0, 1, 1, 0.0, "2019:01:01 10:00:00")
    kept = MediaInput(path, Path("/data/c"), 5, 0, visual=own, sidecar_day=_NOON)
    assert dating_of(kept, context).source is DateSource.EXIF


def _picked(photo: Path) -> Picked:
    """What *Move to an event…* reads of one file the index has no date for."""
    with closing(sqlite3.connect(":memory:")) as connection:
        connection.execute("CREATE TABLE files (media_date TEXT)")
        connection.execute("INSERT INTO files VALUES (NULL)")
        index = SimpleNamespace(
            connection=connection,
            source_of=lambda _key: SimpleNamespace(path=photo),
        )
        desk = SimpleNamespace(
            index=index,
            mover=None,
            mapper=HostPathMapper(photo.parent),
            aside=frozenset,
        )
        return move_go._picked(cast("RuleDesk", desk), (1,))[0]  # noqa: SLF001  # pylint: disable=protected-access


def _month(photo: Path, rows: dict[str, Any]) -> str:
    """The month the move files it in, or that there is none."""
    runtime = SimpleNamespace(mapper=SimpleNamespace(to_host=str))
    mover = SelectionMover(cast("Any", runtime))
    plan = cast("Any", SimpleNamespace(by_path=rows))
    try:
        return mover._month(plan, _picked(photo))  # noqa: SLF001  # pylint: disable=protected-access
    except ValueError:
        return _NO_MONTH


def test_dated_on_the_page_the_move_files_it_undone_no_month(tmp_path: Path) -> None:
    """The TODO's test: that month, then no month again."""
    photo = tmp_path / "a.jpg"
    sidecar = _written(photo)
    assert _month(photo, {}) == "2019/2019-07"
    sidecar.unlink()
    assert _month(photo, {}) == _NO_MONTH


def test_undone_a_plan_of_before_does_not_keep_the_month(tmp_path: Path) -> None:
    """A plan made while the day stood says `sidecar`: the disk decides."""
    photo = tmp_path / "a.jpg"
    sidecar = _written(photo)
    row = SimpleNamespace(date=_NOON.isoformat(), date_source=DateSource.SIDECAR)
    rows = {str(photo): row}
    assert _month(photo, rows) == "2019/2019-07"
    sidecar.unlink()
    assert _month(photo, rows) == _NO_MONTH
