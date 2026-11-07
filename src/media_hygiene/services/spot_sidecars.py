"""The landmarks the sidecars name, read back when a row is written (0649).

The sidecar is the truth, the `spots` row its cache: a row written again (a new
snapshot, an index rebuilt) takes the name of the sidecar (source `user`), and never
a name the user rejected there.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.index.spot_rows import SpotSource
from media_hygiene.services.xmp_sidecars import sidecar_of
from media_hygiene.tags.xmp_doc import XmpError, parse
from media_hygiene.tags.xmp_landmark import SidecarLandmark, landmark_in

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from media_hygiene.index.spot_rows import Known

_LANDMARK: Final = 4  # its column in a row of `spots`
_SOURCE: Final = 5


def sidecar_names(stale: Iterable[Known]) -> dict[str, SidecarLandmark]:
    """What the sidecars of some photos say, those naming or rejecting something.

    Args:
        stale: The photos whose rows are written again.

    Returns:
        Each one's landmark by path.
    """
    folders: dict[Path, list[str]] = {}
    found: dict[str, SidecarLandmark] = {}
    for known in stale:
        try:
            sidecar = sidecar_of(Path(known.path), folders)
            if not sidecar.is_file():
                continue
            said = landmark_in(parse(sidecar.read_bytes()))
        except OSError, XmpError:
            continue
        if said.name or said.rejected:
            found[known.path] = said
    return found


def as_named(known: Known, said: Mapping[str, SidecarLandmark]) -> Known:
    """The file, as if its row held the sidecar's name already.

    Args:
        known: The file and its row.
        said: The sidecars' landmarks.

    Returns:
        It, its landmark the user's when its sidecar names one.
    """
    landmark = said.get(known.path)
    if landmark is None or not landmark.name:
        return known
    return replace(
        known,
        stored_at=(known.latitude, known.longitude),
        landmark=landmark.name,
        source=SpotSource.USER.value,
    )


def unrejected(
    row: tuple[object, ...], said: Mapping[str, SidecarLandmark]
) -> tuple[object, ...]:
    """A row without a landmark its sidecar rejected.

    Args:
        row: The columns of `spots`, its path first.
        said: The sidecars' landmarks.

    Returns:
        The row; its landmark emptied (source `user`: no name, by choice) when rejected.
    """
    landmark = said.get(str(row[0]))
    name = str(row[_LANDMARK]).casefold()
    if landmark is None or not name:
        return row
    if name not in {each.casefold() for each in landmark.rejected}:
        return row
    return (*row[:_LANDMARK], "", SpotSource.USER.value, *row[_SOURCE + 1 :])
