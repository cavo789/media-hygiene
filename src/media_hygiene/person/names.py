"""Name the faces of `/person` (TODO 0714): "this is Aunt Juliette", then her photos.

The page sends faces by their shelf number; they become face ids (`<path>#<n>`) of the
index and the change goes into `config.toml` as on the people page (`changes`,
`moving`), then is read back from the disk: what the page shows is what the file
holds. A face found by a second look (no number in the index) cannot be named.
Each face and photo of the page is told its name: confirmed, attributed by the
tool (the nearest confirmed face), or none; and the names it was said not to be.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final, Literal

from pydantic import BaseModel, ConfigDict, Field

from media_hygiene.i18n import _
from media_hygiene.people.changes import Naming, give_name, reject_faces
from media_hygiene.people.config_file import read_people, save_people
from media_hygiene.people.followed import follow_ids
from media_hygiene.people.known import Known
from media_hygiene.people.moving import move_faces
from media_hygiene.people.naming import How, face_id, id_of, name_all
from media_hygiene.people.people_memo import PeopleMemo
from media_hygiene.people.proof import proof_line, rejected_line
from media_hygiene.people.roster import Change

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.config.people_settings import PeopleSettings
    from media_hygiene.index.face_rows import StoredFace
    from media_hygiene.person.lookup import FaceIndex
    from media_hygiene.person.shelf import FaceShelf

_NAME_LENGTH: Final = 100
_NAMED: Final = frozenset({How.CONFIRMED, How.ASSIGNED})


class NameAsked(BaseModel):
    """`POST /person/api/names`: these faces are someone, or are not someone."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    action: Literal["name", "move", "reject"]
    name: str = Field(min_length=1, max_length=_NAME_LENGTH)
    faces: tuple[int, ...] = Field(min_length=1)
    source: str = Field(default="", max_length=_NAME_LENGTH)  # "move": shown under


@dataclass(frozen=True, slots=True)
class FaceNames:
    """`config.toml` (None: not writable), the settings, the index, the shelf."""

    config_file: Path | None
    base: PeopleSettings
    faces: FaceIndex
    shelf: FaceShelf
    memo: PeopleMemo = field(default_factory=PeopleMemo)  # read again after a change

    def settings(self) -> PeopleSettings:
        """`[people]` as the file holds it now, the thresholds of the run.

        Returns:
            The settings.
        """
        if self.config_file is None:
            return self.base
        back = self.memo.read(self.config_file)
        return self.base.model_copy(
            update={"person": back.person, "ignored": back.ignored}
        )

    def answer(self, body: bytes) -> dict[str, object]:
        """Save a naming, read it back.

        Args:
            body: A `NameAsked`, as JSON.

        Returns:
            The line read back from the file (`saved`), the names known; or `error`.

        Raises:
            ValidationError: The body is not a naming.
        """
        asked = NameAsked.model_validate_json(body)
        ids = tuple(self._ids(asked.faces))
        if self.config_file is None:
            said = _(
                "names are kept in config.toml: mount a folder of yours on /config"
            )
            return {"error": said}
        if not ids:
            return {
                "error": _("This face was found by a second look: it cannot be named.")
            }
        naming = Naming(asked.name.strip(), ids)
        try:
            original = read_people(self.config_file)
            present = {str(face.path) for face in self.faces.every}
            written = follow_ids(original, {}, present)
            if asked.action == "reject":
                wanted = reject_faces(written, naming)
            elif asked.action == "move":
                wanted = move_faces(written, naming, asked.source)
            else:
                wanted = give_name(written, naming)
            save_people(self.config_file, wanted)
            back = read_people(self.config_file)
        except (ValueError, OSError) as error:
            return {"error": str(error)}
        if asked.action == "reject":
            line = rejected_line(back, naming, again=False)
        else:
            line = proof_line(back, Change(asked.action, naming, asked.source))
        return {"saved": line, "people": [person.name for person in back.person]}

    def tags(self, keys: list[int]) -> dict[int, dict[str, object]]:
        """The name of each face, as the file and the index say now.

        Args:
            keys: Shelf numbers.

        Returns:
            By number: `name`, `how` (confirmed or assigned), `not` (names ruled out).
        """
        stored = {key: face for key in keys if (face := self._stored(key)) is not None}
        settings = self.settings()
        known = Known.of(self.faces.every, settings)
        names = name_all(tuple(stored.values()), known)
        tags: dict[int, dict[str, object]] = {}
        for (key, face), named in zip(stored.items(), names, strict=True):
            ruled_out = sorted(known.rejected.get(id_of(face), frozenset()))
            if named.how in _NAMED or ruled_out:
                name = named.name if named.how in _NAMED else ""
                tags[key] = {"name": name, "how": str(named.how), "not": ruled_out}
        return tags

    def _stored(self, key: int) -> StoredFace | None:
        """The face of the index a shelf number names.

        Args:
            key: Its number.

        Returns:
            It; None for a face of a second look or an unknown number.
        """
        face = self.shelf.face(str(key))
        if face is None or face.number is None:
            return None
        wanted = face_id(face.path, face.number)
        return next(
            (one for one in self.faces.of(face.path) if id_of(one) == wanted), None
        )

    def _ids(self, keys: tuple[int, ...]) -> list[str]:
        """The face ids of shelf numbers, those that have one.

        Args:
            keys: Shelf numbers.

        Returns:
            The ids, in order.
        """
        return [id_of(face) for key in keys if (face := self._stored(key)) is not None]


def tagged(names: FaceNames | None, answer: dict[str, object]) -> dict[str, object]:
    """An answer of the page, each face and photo told its name.

    A photo whose face was said not to be the name of the first (the face chosen) is
    left out: "not him" removes it from the search.

    Args:
        names: The desk; None: the answer as it is.
        answer: `faces` (a photo's) or `files` (a face's photos), each with `key`.

    Returns:
        The same answer, with `named` on each item named, `people`, `writable`.
    """
    if names is None:
        return answer
    for listed in ("faces", "files"):
        items = answer.get(listed)
        if not isinstance(items, list):
            continue
        tags = names.tags([int(item["key"]) for item in items])
        for item in items:
            item["named"] = tags.get(int(item["key"]))
        if listed == "files" and items and items[0]["named"]:
            seed = items[0]["named"]["name"]
            answer[listed] = [items[0]] + [
                item
                for item in items[1:]
                if not (item["named"] and seed and seed in item["named"]["not"])
            ]
    people = [person.name for person in names.settings().person]
    return {**answer, "people": people, "writable": names.config_file is not None}
