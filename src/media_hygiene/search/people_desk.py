"""`POST /api/people/reject`: a name taken off a photo from the search page (TODO 0317).

The cross of a `person` chip under a photo says "this is not them": the faces of the
photo that gave the name go into the person's `rejected` list, a face the user had
confirmed leaves their `faces` too, through the same functions as the people page
(`people.changes`, `people.config_file`). The file is read back and the line said comes
from what it holds. *Put back* (`action: back`) undoes it, the same way; *Yes, it is
them* (`action: confirm`, one face, from *Why this name?*, TODO 0318) confirms a face.
Only this photo changes in this search; other photos named after a face rejected keep
theirs until the next run (`classify`, inventory and XMP compute names per run).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.i18n import _
from media_hygiene.people.changes import Naming, give_name, put_back, reject_faces
from media_hygiene.people.config_file import read_people, save_people
from media_hygiene.people.followed import follow_ids
from media_hygiene.people.proof import proof_line, rejected_line
from media_hygiene.people.roster import Change
from media_hygiene.review.config_saving import save_refused
from media_hygiene.review.http import Response
from media_hygiene.review.serving import json_response
from media_hygiene.search.people_seen import Seen
from media_hygiene.search.people_words import words_of

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.config.people_settings import PeopleSettings
    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.search.fts import SearchIndex

PEOPLE_REJECT_PATH: Final = "/api/people/reject"
_NAME_LENGTH: Final = 100


class RejectAsked(BaseModel):
    """What the page asks: take a name off a photo, or put it back."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    action: Literal["reject", "back", "confirm"] = "reject"
    key: int = Field(ge=0)  # the photo, as the search names it
    name: str = Field(min_length=1, max_length=_NAME_LENGTH)
    face: int | None = Field(default=None, ge=0)  # one face of it (`Seen.faces` rank)


@dataclass(frozen=True, slots=True)
class NamesPlace:
    """Where the names are saved (None: not writable), and `[people]` at the start."""

    config_file: Path | None
    settings: PeopleSettings
    mapper: HostPathMapper  # the paths said, as the user knows them


@dataclass(slots=True)
class PeopleDesk:
    """Takes names off photos, puts them back, confirms them, for one search page."""

    search: SearchIndex
    place: NamesPlace
    seen: Seen | None = None  # made at the first cross, then kept true
    # What each cross did, by photo and name: faces rejected, those confirmed before.
    undo: dict[tuple[int, str], tuple[tuple[str, ...], tuple[str, ...]]] = field(
        default_factory=dict
    )

    def answer(self, body: bytes) -> Response:
        """Save what the page asks, read it back, say it.

        Args:
            body: The JSON the page sent.

        Returns:
            The line read back and the names left on the photo; 400 for a body
            that is not a request, 404 for an unknown photo, 422/500 when nothing
            could be saved.
        """
        try:
            asked = RejectAsked.model_validate_json(body)
        except ValidationError:
            return Response(HTTPStatus.BAD_REQUEST)
        photo = self.search.source_of(asked.key)
        if photo is None:
            return Response(HTTPStatus.NOT_FOUND)
        try:
            line = self._change(photo.path, asked)
        except (ValueError, OSError) as exc:
            return save_refused(exc)
        names = words_of(self.faces().named, self.place.settings).get(photo.path, ())
        return json_response(HTTPStatus.OK, {"saved": line, "names": list(names)})

    def _change(self, path: Path, asked: RejectAsked) -> str:
        """Write the change into `config.toml`, read it back, update this search.

        Args:
            path: The photo, in the container.
            asked: What the page asks.

        Returns:
            The line read back from the file.

        Raises:
            ValueError: No `config.toml` to write, nothing to change, or an invalid
                file.
        """
        config = self.place.config_file
        if config is None:
            raise ValueError(
                _("names are kept in config.toml: mount a folder of yours on /config")
            )
        seen = self.faces()
        named = seen.named.setdefault(path, {})
        written = follow_ids(read_people(config), seen.moves, seen.present())
        if asked.action == "back":
            ids, confirmed = self.undo.pop((asked.key, asked.name), ((), ()))
            if not ids:
                raise ValueError(_("nothing to put back"))
            naming = Naming(asked.name, ids)
            save_people(config, put_back(written, naming, confirmed))
            named[asked.name] = tuple(dict.fromkeys((*named.get(asked.name, ()), *ids)))
        else:
            naming = Naming(asked.name, seen.ids(path, asked.name, asked.face))
            if asked.action == "confirm":
                save_people(config, give_name(written, naming))
            else:
                confirmed = tuple(
                    k for k in naming.faces if _confirmed(written, naming, k)
                )
                save_people(config, reject_faces(written, naming))
                self.undo[asked.key, asked.name] = (naming.faces, confirmed)
                left = tuple(k for k in named[asked.name] if k not in naming.faces)
                named[asked.name] = left
                if not left:
                    named.pop(asked.name)
        self.search.name_people(words_of(seen.named, self.place.settings))
        back = read_people(config)
        seen.renamed(back)
        if asked.action == "confirm":
            return proof_line(back, Change("name", naming))
        return rejected_line(back, naming, again=asked.action == "back")

    def faces(self) -> Seen:
        """The faces of the index and their names, made once.

        Returns:
            Them, kept up to date by each change.
        """
        if self.seen is None:
            self.seen = Seen.load(self.search.connection, self.place.settings)
        return self.seen


def _confirmed(section: PeopleSettings, naming: Naming, key: str) -> bool:
    """Tell whether the user had confirmed a face as this person's.

    Args:
        section: `[people]` as written.
        naming: The name.
        key: The face id.

    Returns:
        True when it is among their `faces`.
    """
    folded = naming.name.strip().casefold()
    return any(
        person.name.strip().casefold() == folded and key in person.faces
        for person in section.person
    )
