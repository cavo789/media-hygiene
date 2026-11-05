"""An album on the TV, served by the home server itself (0417).

The step *Show an album on the TV* used to end the home server so that `mh` ran
`slideshow --album <name> --lan`, then the TV and the phones waited for the new server.
An `mh` that keeps the home server up answers it with a page instead,
`/slideshow/album/<name>`: the show starts in the home server (`slideshow_here`), the
TV paired once stays paired while it runs.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Final
from urllib.parse import quote

from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.paths.locations import Locations
from media_hygiene.paths.mounts import MountTable
from media_hygiene.review.serving import json_response
from media_hygiene.review.step_watch import busy

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.review.http import Response

SLIDESHOW_PAGE: Final = "/slideshow/"  # `services/slideshow_here`
ALBUM_SHOW: Final = "album/"  # `/slideshow/album/<name>`: that album's show starts
TV_CHOICES: Final = f"{SLIDESHOW_PAGE}choices"  # a folder or a month (0455)
TV_CHOOSE: Final = f"{SLIDESHOW_PAGE}choose"  # `services/slideshow_choices`
ALBUM_STEP: Final = "slideshow-album"  # the step that shows an album on the TV
FOLDER_SHOW: Final = "folder/"  # `/slideshow/folder/<path>`: a folder mounted (0598)
FOLDER_STEP: Final = "slideshow"  # *Show your photos on the TV*: any folder


def shown_here(step: str, fields: Mapping[str, str]) -> str | None:
    """The page of a step with a form that the home server serves itself (0417).

    Args:
        step: The step's name.
        fields: Its values, checked.

    Returns:
        `/slideshow/album/<name>` for an album on the TV, `/slideshow/folder/<path>`
        for a folder already mounted (0598: no new mount, no restart); None for any
        other step, or a folder that needs its own mount.
    """
    if step == FOLDER_STEP and _mounted(folder := fields.get("path", "").strip()):
        return f"{SLIDESHOW_PAGE}{FOLDER_SHOW}{quote(folder, safe='')}"
    if step != ALBUM_STEP or not fields.get("album", "").strip():
        return None
    return f"{SLIDESHOW_PAGE}{ALBUM_SHOW}{quote(fields['album'].strip(), safe='')}"


def _mounted(folder: str) -> bool:
    """Tell whether a folder, as the Explorer shows it, is a folder this container sees.

    Args:
        folder: The folder typed; empty for none.

    Returns:
        True when it maps to a folder under a mount (the library, a backup).
    """
    if not folder:
        return False
    mapper = HostPathMapper(Locations().data_dir, MountTable.current().host_sources)
    return mapper.to_container(folder).is_dir()


def album_answer(step: str, fields: Mapping[str, str]) -> Response | None:
    """Answer the step of an album on the TV with its page in the home server.

    Args:
        step: The step's name.
        fields: Its values.

    Returns:
        `{"page": …}`; None for any other step.
    """
    page = shown_here(step, fields)
    return None if page is None else json_response(HTTPStatus.OK, {"page": page})


def kept_answer(reports: Path, step: str, fields: Mapping[str, str]) -> Response | None:
    """What an `mh` that keeps the server up answers before running a step.

    Args:
        reports: The reports folder, where `mh` says the step it runs.
        step: The step's name.
        fields: Its values.

    Returns:
        The album's page (0417); 409 while `mh` runs another step; None otherwise.
    """
    return album_answer(step, fields) or busy(reports)
