"""`POST /person/api/rename`: `/person`'s naming line renames or merges (0827).

The same desk as the people page's (`people.rename_desk`): `config.toml` written,
read back, the settings naming the person following. Its faces in conflict are shown
by their photo's path (the page has no number for them); `/person` reads the names
from the disk at each request, so nothing is handed back to it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.people.rename_desk import FaceShown, RenameDesk
from media_hygiene.person.routes import PERSON_PREFIX
from media_hygiene.services.names_file import names_file

if TYPE_CHECKING:
    from media_hygiene.config.people_settings import PeopleSettings
    from media_hygiene.services.runtime import Runtime

RENAME_PATH: Final = f"{PERSON_PREFIX}/api/rename"


def person_rename(runtime: Runtime) -> RenameDesk:
    """The rename desk of `/person`.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        It.
    """
    shown = FaceShown(_no_number, runtime.mapper.to_host)
    return RenameDesk(names_file(runtime), shown, _read_again)


def _no_number(_key: str) -> int | None:
    """`/person` numbers the faces it shows only: a conflict is shown by its path.

    Args:
        _key: The face.

    Returns:
        None.
    """
    return None


def _read_again(_back: PeopleSettings) -> None:
    """`/person` reads the names from the disk at each request: nothing to do.

    Args:
        _back: The names read back.
    """
