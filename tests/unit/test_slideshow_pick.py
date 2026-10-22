"""What `slideshow` shows (0291): a folder and its subfolders, a search, the set aside.

Read from the index alone; photos and videos (0292), oldest first, the undated last;
exactly one of the three asked for.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.errors import MediaHygieneError
from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.index.schema import prepare
from media_hygiene.search.chosen import Selection
from media_hygiene.search.fts import SearchIndex
from media_hygiene.services.search_pages import chosen_desk
from media_hygiene.services.slideshow_pick import Pick, picked_slides
from media_hygiene.slideshow.slides import Film
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime

# Relative to the data folder; their row is their key (1 to 6).
_FILES: Final = (
    ("c/Photos/Holidays/late.jpg", "2026:07:20 10:00:00"),
    ("c/Photos/Holidays/day 2/early.jpg", "2026:07:02 10:00:00"),
    ("c/Photos/Holidays/undated.png", None),
    ("c/Photos/Holidays/film.mp4", "2026-07-03T10:00:00"),
    ("c/Photos/Holidays 2/other.jpg", "2026:07:01 10:00:00"),
    ("c/Photos/Home/cat.jpg", "2025:01:01 10:00:00"),
)


def _index(runtime: Runtime, tmp_path: Path) -> Path:
    index = tmp_path / "index.sqlite"
    data = runtime.locations.data_dir
    with closing(sqlite3.connect(index)) as connection:
        prepare(connection)
        for path, date in _FILES:
            connection.execute(
                "INSERT INTO files (path, size, mtime_ns, media_date)"
                " VALUES (?, 1, 7, ?)",
                (str(data / path), date),
            )
        connection.execute(
            "INSERT INTO tags (path, size, mtime_ns, source, value)"
            " VALUES (?, 1, 7, 'folder', 'chat')",
            (str(data / _FILES[5][0]),),
        )
        connection.commit()
    return index


@pytest.fixture
def runtime(tmp_path: Path) -> Runtime:
    """A runtime whose folders lie under the test's folder."""
    return make_runtime(make_locations(tmp_path))


def _keys(runtime: Runtime, tmp_path: Path, pick: Pick) -> tuple[int, ...]:
    with SearchIndex.open(_index(runtime, tmp_path)) as search:
        picked = picked_slides(runtime, search, pick)
    assert picked.found == len(picked.slides)
    return tuple(slide.key for slide in picked.slides)


def test_a_folder_and_its_subfolders_oldest_first(
    runtime: Runtime, tmp_path: Path
) -> None:
    """Its subfolder in, a folder whose name only starts the same out, the video in."""
    assert _keys(runtime, tmp_path, Pick(folder=r"C:\Photos\Holidays")) == (
        2,
        4,
        1,
        3,
    )


def test_a_search(runtime: Runtime, tmp_path: Path) -> None:
    """The words of `search`: the photo of the cat only."""
    assert _keys(runtime, tmp_path, Pick(words="chat")) == (6,)


def test_the_files_set_aside(runtime: Runtime, tmp_path: Path) -> None:
    """Read back from the decisions file of the reports folder."""
    data = runtime.locations.data_dir
    with SearchIndex.open(_index(runtime, tmp_path)) as search:
        desk = chosen_desk(runtime, search)
        desk.store.add(
            Selection(tuple(PhotoVersion(data / _FILES[at][0], 1, 7) for at in (0, 4)))
        )
        picked = picked_slides(runtime, search, Pick(chosen=True))
    assert tuple(slide.key for slide in picked.slides) == (5, 1)
    assert picked.slides[0].day == "2026-07-01"


@pytest.mark.parametrize("pick", [Pick(), Pick(folder="C:\\Photos", chosen=True)])
def test_exactly_one_choice(runtime: Runtime, tmp_path: Path, pick: Pick) -> None:
    """None, or two at once: said with the three forms."""
    with (
        SearchIndex.open(_index(runtime, tmp_path)) as search,
        pytest.raises(MediaHygieneError, match="--chosen"),
    ):
        picked_slides(runtime, search, pick)


@pytest.mark.parametrize(
    "case",
    [
        ('{"codec": "hevc", "duration": 12.5}', Film(".mp4", "hevc", 12.5)),
        ("not json", Film(".mp4")),
        (None, Film(".mp4")),
    ],
)
def test_a_video_carries_its_codec_and_length(
    runtime: Runtime, tmp_path: Path, case: tuple[str | None, Film]
) -> None:
    """Read from what the audit's ffprobe stored; unreadable: unknown, tried."""
    metadata, film = case
    index = _index(runtime, tmp_path)
    with closing(sqlite3.connect(index)) as connection:
        connection.execute("UPDATE files SET metadata = ? WHERE rowid = 4", (metadata,))
        connection.commit()
    with SearchIndex.open(index) as search:
        picked = picked_slides(runtime, search, Pick(folder=r"C:\Photos\Holidays"))
    films = [slide.film for slide in picked.slides]
    assert films == [None, film, None, None]
