r"""The role of a folder, set from the tree of the pages (0532).

`[folders]` of `config.toml` gives a folder one role: `protected` (never changed, it
holds the copy kept), `preferred` (its copy is kept first), `backups` (only compared)
or `excluded` (not read). `POST /api/folder-role` gives a folder a role, or none; the
file is edited with `toml_edit` (comments kept, atomic), then read back from the disk:
the roles the page shows are those of the file. A role clashing with another (a backup
inside a protected folder…) is refused with the reason, the file left as it was.
A folder renamed or deleted in Explorer keeps its role on a path that is gone: it is
listed as missing, for the page to offer *Remove*, and *Carry the role* to the folders
now holding its files (0580, `folder_role_carry`): `former` moves the role in one write.
"""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.config.folder_roles import check_protected_excluded, same_folder
from media_hygiene.config.settings import FolderSettings
from media_hygiene.i18n import _
from media_hygiene.places.toml_edit import (
    document_of,
    host_path,
    loaded,
    table_of,
    write_document,
)
from media_hygiene.review.serving import json_response
from media_hygiene.search.folder_role_carry import carried_to

if TYPE_CHECKING:
    import sqlite3
    from pathlib import Path

    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.review.http import Response

ROLE_PATH: Final = "/api/folder-role"
ROLES: Final = ("protected", "preferred", "backups", "excluded")
_TABLE: Final = "folders"
_MAX_PATH: Final = 4096
type Role = Literal["none", "protected", "preferred", "backups", "excluded"]
type Where = Literal["here", "missing", "elsewhere"]


def role_name(role: str) -> str:
    """A role as the pages say it.

    Args:
        role: A key of `[folders]`, or `none`.

    Returns:
        Its name, translated.
    """
    names = {
        "protected": _("protected"),
        "preferred": _("preferred"),
        "backups": _("a backup"),
        "excluded": _("excluded"),
    }
    return names.get(role, _("without a role"))


class RoleAsked(BaseModel):
    """`POST /api/folder-role`: a folder (host path) and its new role, or none."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    folder: str = Field(min_length=1, max_length=_MAX_PATH)
    role: Role
    former: str = Field(default="", max_length=_MAX_PATH)  # its role carried (0580)

    def names(self, path: str) -> bool:
        """Tell whether a folder of the file is the one asked, or the one it replaces.

        Args:
            path: A folder of `[folders]`.

        Returns:
            True for either.
        """
        return same_folder(path, self.folder) or bool(
            self.former and same_folder(path, self.former)
        )


@dataclass(frozen=True, slots=True)
class RoleDesk:
    """Reads and writes the roles of the folders, in `config.toml`."""

    config_file: Path
    mapper: HostPathMapper
    roots: tuple[Path, ...]  # the mounted folders, in the container
    index: sqlite3.Connection | None = None  # where a folder renamed went (0580)

    def listed(self) -> list[dict[str, object]]:
        """The roles of the file, as on the disk now.

        Returns:
            Each folder with a role: its host path, its role, where it is (`here`,
            `missing`: gone from a mounted folder, `elsewhere`: not mounted) and,
            when missing, the folders its files are in now (`carry`).
        """
        table = loaded(self.config_file).get(_TABLE, {})
        listed: list[dict[str, object]] = []
        for role in ROLES:
            for path in table.get(role, []):
                where = self.where(str(path))
                carry = self._carry(str(path)) if where == "missing" else []
                shown = {"path": str(path), "role": role, "where": where}
                listed.append({**shown, "carry": carry})
        return listed

    def _carry(self, folder: str) -> list[str]:
        """The folders now holding the files of a folder gone (0580).

        Args:
            folder: Its host path.

        Returns:
            Their host paths; none without an index.
        """
        if self.index is None:
            return []
        found = carried_to(self.index, self.mapper.to_container(folder))
        return [self.mapper.to_host(path) for path in found]

    def where(self, folder: str) -> Where:
        """Tell whether a folder with a role is here, gone, or not mounted.

        Args:
            folder: Its host path.

        Returns:
            `here`, `missing` or `elsewhere`.
        """
        inside = self.mapper.to_container(folder)
        if not any(inside.is_relative_to(root) for root in self.roots):
            return "elsewhere"
        return "here" if inside.is_dir() else "missing"

    def answer(self, body: bytes) -> Response:
        """`POST /api/folder-role`: give a folder a role, or take it away.

        Args:
            body: The JSON the page sent.

        Returns:
            The roles read back from the disk and what changed; 400 for a body that
            is not a role; 409, the file unchanged, for a role clashing with another.
        """
        try:
            asked = RoleAsked.model_validate_json(body)
        except ValidationError:
            return json_response(HTTPStatus.BAD_REQUEST, {"error": _("Unknown role.")})
        document = document_of(self.config_file)
        table = table_of(document, _TABLE)
        for role in ROLES:
            kept = [p for p in table.get(role, []) if not asked.names(p)]
            if role in table or role == asked.role:
                added = [asked.folder] if role == asked.role else []
                table[role] = [host_path(path) for path in (*kept, *added)]
        try:
            folders = FolderSettings.model_validate(document.unwrap().get(_TABLE, {}))
            check_protected_excluded(folders.protected, folders.excluded)
        except ValidationError as exc:
            reason = "; ".join(str(error["msg"]) for error in exc.errors())
            return json_response(HTTPStatus.CONFLICT, {"error": reason})
        except ValueError as exc:
            return json_response(HTTPStatus.CONFLICT, {"error": str(exc)})
        write_document(self.config_file, document)
        roles = self.listed()
        now = next(
            (
                str(r["role"])
                for r in roles
                if same_folder(str(r["path"]), asked.folder)
            ),
            "none",
        )
        said = _("Saved in {file}: {folder} is now {role}.").format(
            file=self.mapper.to_host(self.config_file),
            folder=asked.folder,
            role=role_name(now),
        )
        stale = _(
            "The last audit's proposals were made with the former roles: run the "
            "audit again before cleaning."
        )
        return json_response(
            HTTPStatus.OK, {"roles": roles, "said": said, "stale": stale}
        )
