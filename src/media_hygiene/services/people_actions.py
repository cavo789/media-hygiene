"""The people page with its persons' actions (0827, 0836): rename, set aside, album.

Wraps the page's app in the doors of `people.person_actions` and the albums API of
`share.album_route`, keyed by the board's face numbers: each names that face's photo,
kept only when the index holds it (`keyed_albums`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.people.naming import id_of
from media_hygiene.people.person_actions import PersonAsideDoor, RenameDoor
from media_hygiene.people.person_aside import PersonAside
from media_hygiene.people.rename_desk import FaceShown, RenameDesk
from media_hygiene.services.keyed_albums import keyed_albums
from media_hygiene.share.album_route import WithAlbums

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.people.app import PeopleApp
    from media_hygiene.people.aside import AsideDesk
    from media_hygiene.review.ending import Handling
    from media_hygiene.services.runtime import Runtime

ALBUMS_PATH: Final = "/api/albums"


def with_actions(
    app: PeopleApp, runtime: Runtime, names: tuple[Path | None, AsideDesk]
) -> Handling:
    """The people page, answering its persons' actions first.

    Args:
        app: The people page.
        runtime: Settings, mount points and output.
        names: `config.toml` (None: not writable), the desk of the photos set aside.

    Returns:
        It, with rename, set aside and the albums.
    """
    config_file, aside = names
    board = app.roster.board
    numbers = {id_of(face): at for at, face in enumerate(board.faces)}
    shown = FaceShown(numbers.get, runtime.mapper.to_host)
    rename = RenameDesk(config_file, shown, app.roster.adopt)
    person = PersonAside(aside, config_file, app.roster.adopt)

    def photo(key: str) -> Path | None:
        """The photo of a face of the board.

        Args:
            key: Its number, from the page.

        Returns:
            Its photo; None for an unknown number.
        """
        face = board.face(key)
        return None if face is None else face.path

    door = RenameDoor(PersonAsideDoor(app, person), rename)
    return WithAlbums(door, keyed_albums(runtime, photo), ALBUMS_PATH)
