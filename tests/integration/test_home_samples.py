"""The random photos of the home page (0485), from a real index."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from typing import TYPE_CHECKING, Final

from media_hygiene.cli.home_samples import SAMPLES, home_samples
from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.index.repository import FactsRepository
from media_hygiene.search.chosen import Selection
from media_hygiene.services.chosen_place import chosen_store
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.locations import Locations
    from media_hygiene.services.runtime import Runtime

_MORE: Final = SAMPLES + 5


def _rows(runtime: Runtime, paths: list[Path], broken: tuple[Path, ...] = ()) -> None:
    """Index rows for these files."""
    index = runtime.index_file
    assert index is not None
    with FactsRepository.open(index):
        pass
    with closing(sqlite3.connect(index)) as connection:
        for path in paths:
            connection.execute(
                "INSERT INTO files (path, size, mtime_ns, broken_reason)"
                " VALUES (?, 1, 1, ?)",
                (str(path), "x" if path in broken else None),
            )
        connection.commit()


def _photos(folder: Path, count: int) -> list[Path]:
    """Files on the disk."""
    folder.mkdir(parents=True, exist_ok=True)
    paths = [folder / f"p{number}.jpg" for number in range(count)]
    for path in paths:
        path.write_bytes(b"x")
    return paths


def test_no_index_no_photo(locations: Locations) -> None:
    """The block stays hidden."""
    runtime = make_runtime(locations)
    if runtime.index_file is not None:
        runtime.index_file.unlink(missing_ok=True)
    assert not home_samples(runtime)


def test_at_most_ten_each_leading_to_its_folder(locations: Locations) -> None:
    """More photos than shown: ten, a thumbnail and the Library's folder."""
    runtime = make_runtime(locations)
    folder = locations.data_dir / "c" / "many"
    _rows(runtime, _photos(folder, _MORE))
    drawn = home_samples(runtime)
    assert len(drawn) == SAMPLES
    assert all(sample.thumb.startswith("/thumb/") for sample in drawn)
    assert all(sample.url.startswith("/search?folder=") for sample in drawn)
    assert {sample.folder for sample in drawn} == {runtime.mapper.to_host(folder)}


def test_fewer_and_what_cannot_be_shown_is_skipped(locations: Locations) -> None:
    """Gone from the disk, broken, a video, set aside: never drawn."""
    runtime = make_runtime(locations)
    folder = locations.data_dir / "c" / "few"
    good, broken, aside = _photos(folder, 3)
    video = folder / "v.mp4"
    video.write_bytes(b"x")
    gone = folder / "gone.jpg"
    _rows(runtime, [good, broken, aside, video, gone], (broken,))
    stat = aside.stat()
    version = PhotoVersion(aside, stat.st_size, stat.st_mtime_ns)
    chosen_store(runtime).add(Selection((version,)))
    drawn = home_samples(runtime)
    assert len(drawn) == 1
