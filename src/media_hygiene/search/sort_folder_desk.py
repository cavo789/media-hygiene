"""`leave` and `person_folders` set from a folder's menu in the tree (0533).

`GET /api/sort-setup/folder` lists them as `config.toml` holds them now; `POST` changes
one, with `toml_edit`, read back from the disk. A folder of `leave` renamed in Explorer
points nowhere: it is listed as `missing`, for the page to offer *Remove* (nothing in
the tool moves such a folder: it is never sorted). `person_folders` holds names, not
paths: a rename only matters when the new name no longer holds the person's.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from http import HTTPStatus
from pathlib import PureWindowsPath
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.config.folder_roles import same_folder
from media_hygiene.i18n import _
from media_hygiene.people import folding
from media_hygiene.places.toml_edit import (
    document_of,
    host_path,
    loaded,
    table_of,
    write_document,
)
from media_hygiene.review.serving import json_response
from media_hygiene.search.sort_setup_desk import SETUP_PATH, TABLE, SortSetupDesk

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.review.http import Response
    from media_hygiene.search.folder_role_desk import RoleDesk

SORT_FOLDER_PATH: Final = "/api/sort-setup/folder"
_MAX: Final = 4096


class FolderSortAsked(BaseModel):
    """One change: a folder in or out of `leave`, a person's name added or forgotten."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    folder: str = Field(default="", max_length=_MAX)
    leave: bool | None = None
    person: str = Field(default="", max_length=_MAX)
    forget: str = Field(default="", max_length=_MAX)


def _names_person(folder: str, name: str) -> bool:
    """Tell whether a folder's name holds a person's, as `FolderRules.of_person` reads.

    Args:
        folder: The folder's host path.
        name: The person's name.

    Returns:
        True when it holds it as a word, case and accents ignored.
    """
    word = re.escape(folding.folded(name))
    own = folding.folded(PureWindowsPath(folder).name)
    return re.search(rf"(?<!\w){word}(?!\w)", own) is not None


@dataclass(frozen=True, slots=True)
class SortFolderDesk:
    """Reads and writes `[classify] leave` and `person_folders`."""

    roles: RoleDesk

    def state(self) -> Response:
        """`GET /api/sort-setup/folder`.

        Returns:
            The two lists, as on the disk.
        """
        return json_response(HTTPStatus.OK, self.shown())

    def shown(self) -> dict[str, object]:
        """The two lists, read from the disk.

        Returns:
            `leave`, each with where it is; `people`, the names.
        """
        table = loaded(self.roles.config_file).get(TABLE, {})
        leave = [
            {"path": str(path), "where": self.roles.where(str(path))}
            for path in table.get("leave", [])
        ]
        people = [str(name) for name in table.get("person_folders", [])]
        return {"leave": leave, "people": people}

    def answer(self, body: bytes) -> Response:
        """`POST /api/sort-setup/folder`: apply one change.

        Args:
            body: The JSON the page sent.

        Returns:
            The lists read back and the sentence; 400 for another body; 409, the file
            unchanged, for a name the folder's does not hold.
        """
        try:
            asked = FolderSortAsked.model_validate_json(body)
        except ValidationError:
            return json_response(
                HTTPStatus.BAD_REQUEST, {"error": _("Not a choice of the page.")}
            )
        person = asked.person.strip()
        if person and not _names_person(asked.folder, person):
            refused = _(
                "The name of this folder does not hold '{name}': the sort would not "
                "see it as theirs."
            ).format(name=person)
            return json_response(HTTPStatus.CONFLICT, {"error": refused})
        document = document_of(self.roles.config_file)
        table = table_of(document, TABLE)
        if asked.leave is not None and asked.folder:
            held = table.get("leave", [])
            others = [path for path in held if not same_folder(path, asked.folder)]
            added = [asked.folder] if asked.leave else []
            table["leave"] = [host_path(path) for path in (*others, *added)]
        if person or asked.forget:
            gone = {folding.folded(name) for name in (person, asked.forget) if name}
            names = table.get("person_folders", [])
            kept = [str(n) for n in names if folding.folded(n) not in gone]
            table["person_folders"] = [*kept, *([person] if person else [])]
        write_document(self.roles.config_file, document)
        said = _(
            "Saved in {file}. Nothing moved: the next classify takes it into account."
        ).format(file=self.roles.mapper.to_host(self.roles.config_file))
        return json_response(HTTPStatus.OK, {**self.shown(), "said": said})


@dataclass(frozen=True, slots=True)
class SortSetup:
    """The two desks of the sort setup, and their routes."""

    setup: SortSetupDesk
    folder: SortFolderDesk

    def gets(self) -> dict[str, Callable[[], Response]]:
        """The `GET` routes.

        Returns:
            Each path and what answers it.
        """
        return {SETUP_PATH: self.setup.state, SORT_FOLDER_PATH: self.folder.state}

    def posts(self) -> dict[str, Callable[[bytes], Response]]:
        """The `POST` routes.

        Returns:
            Each path and what answers it.
        """
        return {SETUP_PATH: self.setup.answer, SORT_FOLDER_PATH: self.folder.answer}
