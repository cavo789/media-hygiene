"""0518: the files set aside are gone for the album, the share, the TV and the move."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.search import move_go
from media_hygiene.search.aside_filter import AsideFilter, Kept
from media_hygiene.share import album_pickers as pickers
from media_hygiene.share.album_api import AlbumAsked
from media_hygiene.share.album_pickers import SearchPicker

if TYPE_CHECKING:
    import pytest

    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.search.rule_desk import RuleDesk

MAPPER = HostPathMapper(Path("/data"))
PATHS = {1: Path("/data/c/a.jpg"), 2: Path("/data/c/b.jpg")}
ASIDE = frozenset({MAPPER.to_host(PATHS[2])})


def _index() -> SimpleNamespace:
    """An index naming two files, the second set aside; versions: every file."""
    return SimpleNamespace(
        source_of=lambda key: (
            SimpleNamespace(path=PATHS[key]) if key in PATHS else None
        ),
        versions=lambda _query: [SimpleNamespace(path=path) for path in PATHS.values()],
    )


def _picker() -> SearchPicker:
    """The search's picker, the second file set aside."""
    return SearchPicker(
        cast("SearchIndex", _index()), AsideFilter(lambda: ASIDE, MAPPER)
    )


def test_keep_drops_the_files_set_aside_and_counts_them() -> None:
    """Only the file not set aside is kept; the sentence says one was left out."""
    kept = AsideFilter(lambda: ASIDE, MAPPER).keep(PATHS.values())
    assert kept.files == (PATHS[1],)
    assert kept.said == "1 file set aside ignored."
    assert not Kept(()).said


def test_an_album_add_of_keys_leaves_the_file_set_aside_out() -> None:
    """Keys picked by Ctrl+A or Shift: the file set aside never enters the album."""
    asked = AlbumAsked(album="Trip", action="add", keys=("1", "2"))
    assert _picker().files(asked) == Kept((PATHS[1],), 1)


def test_the_tv_of_every_file_found_leaves_the_file_set_aside_out(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`all` (every file a search finds) on the TV: the same rule."""
    monkeypatch.setattr(pickers, "read_query", lambda _index, query: query)
    asked = AlbumAsked(album="Trip", action="tv", all=True)
    assert _picker().files(asked).files == (PATHS[1],)


def test_taking_out_of_an_album_still_reaches_a_file_set_aside() -> None:
    """*Take out* takes a file set aside out of an album: it is never added again."""
    asked = AlbumAsked(album="Trip", action="remove", keys=("2",))
    assert _picker().files(asked).files == (PATHS[2],)


def test_an_event_move_never_moves_a_file_set_aside() -> None:
    """*📂 Event…* with a file set aside picked: it stays, the answer says so."""
    index = SimpleNamespace(
        connection=SimpleNamespace(
            execute=lambda *_args: SimpleNamespace(fetchone=lambda: None)
        ),
        source_of=lambda key: SimpleNamespace(path=PATHS[key]),
    )
    desk = cast(
        "RuleDesk",
        SimpleNamespace(index=index, mover=None, mapper=MAPPER, aside=lambda: ASIDE),
    )
    picked, said = move_go._picked(desk, (1, 2))  # noqa: SLF001  # pylint: disable=protected-access
    assert dict(picked.paths) == {1: PATHS[1]}
    assert said == "1 file set aside ignored."
