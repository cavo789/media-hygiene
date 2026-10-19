"""The photos of the map given a place by hand: which they are, give, take back (0237).

They are found among the located files by content (`hand_placed`): size, then the
SHA-256, read once per file and kept for the session. Giving a cluster's photos reads
each of them (the folders are mounted read-only: nothing is written next to them).
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from media_hygiene.classify.hand_placed import Candidate, digest_of, hand_placed
from media_hygiene.config.place_photos import SHA256, HandPhoto, PlacePhotos
from media_hygiene.i18n import _
from media_hygiene.places.clusters import SHOWN
from media_hygiene.places.config_photos import give_photos, read_place_photos
from media_hygiene.places.drawer_rows import JPEG
from media_hygiene.review.views import PREVIEW_PREFIX, preview_key

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.places.clusters import Cluster
    from media_hygiene.places.folder_rows import FolderContext
    from media_hygiene.scan.models import MediaFile


class PhotosAction(StrEnum):
    """What the page asks of the photos given by hand."""

    GIVE = "give"  # a cluster's photos, but those left out, to a place
    REMOVE = "remove"  # one photo: its GPS decides again


class PhotosAct(BaseModel):
    """`POST /api/place-photos`."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    action: PhotosAction
    cluster: int = Field(default=-1, ge=-1)  # its rank in the state
    place: str = ""
    left_out: tuple[tuple[str, str], ...] = ()  # (host folder, name), unticked
    sha256: str = Field(default="", pattern=f"({SHA256})|^$")


class HandDesk:
    """The photos given a place, as `config.toml` holds them, found among the files."""

    def __init__(self, clusters: Sequence[Cluster], context: FolderContext) -> None:
        """Find the photos given a place among the files of the clusters.

        Args:
            clusters: Where the photos were taken.
            context: `config.toml` and the host paths.

        Raises:
            ValueError: An entry of the file is invalid.
        """
        self._context = context
        self._files = {file.path: file for found in clusters for file in found.files}
        self._digests: dict[Path, str] = {}
        self.sources: dict[str, Path] = {}  # the previews listed
        self.entries: tuple[PlacePhotos, ...] = ()
        self.given: dict[Path, str] = {}
        self.reload()

    def reload(self) -> None:
        """Read the file again, then find the photos it lists.

        Raises:
            ValueError: An entry of the file is invalid.
        """
        self.entries = read_place_photos(self._context.config_file)
        candidates = (Candidate(file.path, file.size) for file in self._files.values())
        self.given = hand_placed(candidates, self.entries, self._digest)

    def give(self, cluster: Cluster, act: PhotosAct, place: str) -> None:
        """Give a cluster's photos, but those left out, to a place, then read back.

        Args:
            cluster: The cluster.
            act: What the page asks: the photos left out.
            place: The place's name, as written.

        Raises:
            ValueError: No photo is left to give, or none can be read.
            OSError: The file cannot be written.
        """
        mapper = self._context.mapper
        left_out = set(act.left_out)
        photos: list[HandPhoto] = []
        for file in cluster.files:
            host = (mapper.to_host(file.path.parent), file.path.name)
            if file.path in self.given or host in left_out:
                continue
            sha = self._digest(Candidate(file.path, file.size))
            if sha is not None:
                size = file.path.stat().st_size
                path = mapper.to_host(file.path)
                photos.append(HandPhoto(sha256=sha, size=size, path=path))
        if not photos:
            raise ValueError(_("No photo to give: none ticked, or none reachable."))
        given = PlacePhotos(place=place, photos=tuple(photos))
        give_photos(self._context.config_file, given)
        self.reload()

    def listed(self, place: str) -> list[dict[str, object]]:
        """The photos given a place, for its editor.

        Args:
            place: The place's name.

        Returns:
            Each photo's digest, its host path when given, its host path now and its
            preview (absent when it is not found among the located files).
        """
        now = {self._digests[path]: path for path in self.given}
        rows: list[dict[str, object]] = []
        for entry in self.entries:
            if entry.place.casefold() != place.casefold():
                continue
            for photo in entry.photos:
                row: dict[str, object] = {"sha256": photo.sha256, "path": photo.path}
                found = now.get(photo.sha256)
                row["now"] = self._context.mapper.to_host(found) if found else ""
                if found is not None and self._files[found].kind in SHOWN:
                    row["preview"] = self._preview(self._files[found])
                rows.append(row)
        return rows

    def _preview(self, file: MediaFile) -> str:
        """Register a file's preview, to serve it.

        Args:
            file: The file.

        Returns:
            Its address.
        """
        key = preview_key(file)
        self.sources[key] = file.path
        return f"{PREVIEW_PREFIX}{key}{JPEG}"

    def _digest(self, candidate: Candidate) -> str | None:
        """A file's SHA-256, read once per session.

        Args:
            candidate: The file.

        Returns:
            The digest; None when it cannot be read.
        """
        known = self._digests.get(candidate.path)
        if known is None and (known := digest_of(candidate)) is not None:
            self._digests[candidate.path] = known
        return known
