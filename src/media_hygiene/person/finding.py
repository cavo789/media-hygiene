r"""The answers of `/person`: the faces of one photo, then the photos of one face.

A photo is named by its path as the user knows it (`C:\\Photos\\x.jpg`, pasted) or as
a page sends it: it must be a file below the photo folders, or the page says why in
one sentence. Its faces come from the index; the photos of a face from every face
of the index (`likeness`), the photo of the face first.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.people.remembered import aside_date
from media_hygiene.person.likeness import likeness
from media_hygiene.person.routes import FACE_PREFIX, JPEG, PREVIEW_PREFIX, THUMB_PREFIX
from media_hygiene.person.shelf import ShelfFace

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.index.face_rows import StoredFace
    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.people.aside import AsideDesk
    from media_hygiene.person.lookup import FaceIndex
    from media_hygiene.person.shelf import FaceShelf

_QUOTES: Final = "\"' "


@dataclass(frozen=True, slots=True)
class PhotoPlace:
    """The photo folders, as the container and the user name them."""

    mapper: HostPathMapper
    data_dir: Path

    def resolve(self, typed: str) -> Path | None:
        r"""The photo a typed path names, if it is a file below the photo folders.

        Args:
            typed: A host path (`C:\\...`), or a container path.

        Returns:
            Its path in the container; None for anything else (`..` included).
        """
        path = self.mapper.to_container(typed.strip(_QUOTES))
        try:
            real = path.resolve(strict=True)
        except OSError, RuntimeError:
            return None
        data = self.data_dir.resolve()
        if not real.is_relative_to(data) or not real.is_file():
            return None
        return self.data_dir / real.relative_to(data)


@dataclass(frozen=True, slots=True)
class PersonFinder:
    """Finds a photo's faces, and a face's photos, numbered on the shelf."""

    place: PhotoPlace
    faces: FaceIndex
    shelf: FaceShelf

    def photo(self, typed: str) -> dict[str, object]:
        """The faces of a photo, as the page reads them.

        Args:
            typed: Its path, typed or sent.

        Returns:
            Its host path, its faces, whether the audit looked for them; a sentence
            (`said`) for a path that is not a photo here.
        """
        path = self.place.resolve(typed)
        if path is None:
            message = _("{path} is not a photo of the folders this page shows.")
            return {"said": message.format(path=typed.strip(_QUOTES)), "faces": []}
        faces = [
            self.shelf.add(ShelfFace(face.path, face.embedding, face.box))
            for face in self.faces.of(path)
        ]
        return {
            "photo": self.place.mapper.to_host(path),
            "scanned": self.faces.scanned(path),
            "faces": [face_view(key) for key in faces],
        }

    def like(self, key: str, aside: AsideDesk | None) -> dict[str, object]:
        """The photos of the person a face shows, as the page's grid reads them.

        Args:
            key: The face's number.
            aside: Where the photos set aside are, and who was set aside before.

        Returns:
            The photos (the face's first), and the person set aside they are; none
            for an unknown number.
        """
        seed = self.shelf.face(key)
        if seed is None:
            return {"files": [], "known": None}
        memory = None if aside is None else aside.memory
        people = () if memory is None else memory.people()
        found = likeness(seed.embedding, self.faces.every, people)
        chosen = frozenset() if aside is None else aside.paths()
        others = (face for face in found.faces if face.path != seed.path)
        files = [self._card(int(key), seed.path, chosen)]
        files.extend(
            self._card(self._number(face), face.path, chosen) for face in others
        )
        known = found.known
        if known is None:
            return {"files": files, "known": None}
        date = aside_date(known.aside)
        said = {"aside": known.aside, "label": known.label, "date": date}
        return {"files": files, "known": said}

    def _number(self, face: StoredFace) -> int:
        """Put a face of the index on the shelf.

        Args:
            face: The face.

        Returns:
            Its number.
        """
        return self.shelf.add(ShelfFace(face.path, face.embedding, face.box))

    def _card(self, key: int, path: Path, chosen: frozenset[str]) -> dict[str, object]:
        """One photo of the grid, by the number of its face.

        Args:
            key: The face's number.
            path: Its photo.
            chosen: The host paths set aside.

        Returns:
            What `pick_grid.js.j2` reads of a file.
        """
        host = self.place.mapper.to_host(path)
        return {
            "key": key,
            "name": path.name,
            "thumb": f"{THUMB_PREFIX}{key}{JPEG}",
            "preview": f"{PREVIEW_PREFIX}{key}{JPEG}",
            "original": f"{PREVIEW_PREFIX}{key}{JPEG}",
            "where": host,
            "path": host,  # 👤: `/person` again, from this photo
            "chosen": host in chosen,
        }


def face_view(key: int) -> dict[str, object]:
    """A face to choose, as the page reads it.

    Args:
        key: Its number.

    Returns:
        Its number and its picture.
    """
    return {"key": key, "face": f"{FACE_PREFIX}{key}{JPEG}"}
