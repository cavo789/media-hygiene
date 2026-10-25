"""`sort` and `undo` rewrite every file naming photos by path, read back (0382)."""

from __future__ import annotations

import datetime as dt
import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.config.people_settings import PeopleSettings, Person
from media_hygiene.people.config_file import read_people, save_people
from media_hygiene.plan.review import PairAction
from media_hygiene.report.burst_decisions import BurstDecision
from media_hygiene.report.chosen_decisions import ChosenFile
from media_hygiene.report.decisions import (
    DecisionsFile,
    PairDecision,
    read_decisions,
    write_decisions,
)
from media_hygiene.review.place import DEFAULT_DECISIONS
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.share.albums import (
    ALBUMS_FILE,
    Album,
    AlbumEntry,
    AlbumsFile,
    read_albums,
    write_albums,
)
from media_hygiene.shrink.drafts import drafts_root
from media_hygiene.shrink.try_choices import (
    CHOICES_FILE,
    TryChoice,
    TryChoices,
    read_choices,
    save_choices,
)
from tests.support.runtime import make_runtime
from tests.support.sorting import (
    MIXED,
    PARTY,
    build_library,
    classify,
    name_first_event,
    sort,
    undo,
)

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations
    from media_hygiene.services.runtime import Runtime

_ADDED = dt.datetime(2026, 10, 25, 10, tzinfo=dt.UTC)


def _ready(locations: Locations) -> Runtime:
    """A library audited and classified, its first event named.

    Args:
        locations: Mount points.

    Returns:
        The runtime.
    """
    build_library(locations.data_dir)
    runtime = make_runtime(locations)
    AuditService(runtime, NullProgress()).run()
    name_first_event(classify(runtime))
    return runtime


def _stores(runtime: Runtime, photos: tuple[Path, Path]) -> None:
    """Write each file that names photos by path, naming two of the party's.

    Args:
        runtime: The runtime.
        photos: Two photos the sort moves.
    """
    host = runtime.mapper.to_host
    first, second = photos
    locations = runtime.locations
    face = f"{first}#0"
    save_people(
        locations.config_file,
        PeopleSettings(
            person=(Person(name="Ann", faces=(face,)),), ignored=(f"{second}#1",)
        ),
    )
    digest = hashlib.sha256(first.read_bytes()).hexdigest()
    entry = AlbumEntry(
        path=host(first), sha256=digest, size=first.stat().st_size, added=_ADDED
    )
    locations.reports_dir.mkdir(parents=True, exist_ok=True)
    write_albums(
        locations.reports_dir / ALBUMS_FILE,
        AlbumsFile(albums=(Album(name="Summer", entries=(entry,)),)),
    )
    stat = second.stat()
    write_decisions(
        locations.reports_dir / DEFAULT_DECISIONS,
        DecisionsFile(
            version=1,
            roots=(host(locations.data_dir / MIXED),),
            pairs=(
                PairDecision(
                    kept_in=host(locations.data_dir / MIXED),
                    removed_from=host(locations.data_dir / PARTY),
                    action=PairAction.SWAP,
                ),
            ),
            bursts=(BurstDecision(kept=(host(first),), discarded=(host(second),)),),
            chosen=(
                ChosenFile(
                    path=host(second), size=stat.st_size, mtime_ns=stat.st_mtime_ns
                ),
            ),
        ),
    )
    drafts = drafts_root(locations.cache_dir)
    drafts.mkdir(parents=True, exist_ok=True)
    choice = TryChoice(path=str(first), size=first.stat().st_size, mtime_ns=0, draft=1)
    save_choices(drafts / CHOICES_FILE, TryChoices(run="r", chosen=(choice,)))


def _named(runtime: Runtime) -> set[str]:
    """Every path the user's files name, read from the disk alone.

    Args:
        runtime: The runtime.

    Returns:
        Container paths of faces and choices, host paths of albums and decisions.
    """
    locations = runtime.locations
    people = read_people(locations.config_file)
    faces = {
        key.rpartition("#")[0] for key in (*people.ignored, *people.person[0].faces)
    }
    albums = read_albums(locations.reports_dir / ALBUMS_FILE)
    decisions = read_decisions(locations.reports_dir / DEFAULT_DECISIONS)
    choices = read_choices(drafts_root(locations.cache_dir) / CHOICES_FILE)
    assert choices is not None
    return {
        *faces,
        *(entry.path for album in albums.albums for entry in album.entries),
        *(p for burst in decisions.bursts for p in (*burst.kept, *burst.discarded)),
        *(entry.path for entry in decisions.chosen),
        *(choice.path for choice in choices.chosen),
    }


def test_sort_then_undo_rewrite_every_file_naming_photos(locations: Locations) -> None:
    """After sort the files name the new paths, the cache lost; undo puts them back."""
    runtime = _ready(locations)
    party = locations.data_dir / PARTY
    photos = (party / "IMG_0000.jpg", party / "IMG_0001.jpg")
    _stores(runtime, photos)
    before = _named(runtime)
    result = sort(runtime)
    moved = {entry.path: entry.target for entry in result.moves.moved}
    assert all(str(photo) in moved for photo in photos)
    if runtime.index_file is not None:
        runtime.index_file.unlink()  # the cache volume lost: the files alone say it
    host = runtime.mapper.to_host
    named = _named(runtime)
    for photo in photos:
        target = moved[str(photo)]
        assert target is not None
        assert host(Path(target)) in named
        assert str(photo) not in named
        assert host(photo) not in named
    decisions = read_decisions(locations.reports_dir / DEFAULT_DECISIONS)
    assert not decisions.pairs  # the party's folder is gone: its pair dropped
    assert result.links.lines, result.links
    assert not result.links.problems, result.links
    undo(runtime, result.run_id)
    assert _named(runtime) == before


def test_a_file_that_cannot_be_rewritten_is_named_and_the_sort_completes(
    locations: Locations,
) -> None:
    """A broken albums file: the moves are done, one line says it was not updated."""
    runtime = _ready(locations)
    locations.reports_dir.mkdir(parents=True, exist_ok=True)
    (locations.reports_dir / ALBUMS_FILE).write_text("not json", encoding="utf-8")
    result = sort(runtime)
    assert result.manifest.intact
    assert any(ALBUMS_FILE in line for line in result.links.problems), result.links
