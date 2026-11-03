r"""The role of a folder, set from the tree of the pages (0532).

`[folders]` of `config.toml` gives a folder one role: `protected` (never changed, it
holds the copy kept), `preferred` (its copy is kept first), `backups` (only compared)
or `excluded` (not read). `POST /api/folder-role` gives a folder a role, or none; the
file is edited with `toml_edit` (comments kept, atomic), then read back from the disk:
the roles the page shows are those of the file. A role clashing with another (a backup
inside a protected folder…) is refused with the reason, the file left as it was.
A folder renamed or deleted in Explorer keeps its role on a path that is gone: it is
listed as missing, for the page to offer *Remove*.
"""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.config.folder_roles import same_folder
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

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.review.http import Response

ROLE_PATH: Final = "/api/folder-role"
ALBUM_ROOT_PATH: Final = "/api/album-root"  # `album_root_desk` (0534)
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


@dataclass(frozen=True, slots=True)
class RoleDesk:
    """Reads and writes the roles of the folders, in `config.toml`."""

    config_file: Path
    mapper: HostPathMapper
    roots: tuple[Path, ...]  # the mounted folders, in the container

    def listed(self) -> list[dict[str, str]]:
        """The roles of the file, as on the disk now.

        Returns:
            Each folder with a role: its host path, its role and where it is
            (`here`, `missing`: gone from a mounted folder, `elsewhere`: not mounted).
        """
        table = loaded(self.config_file).get(_TABLE, {})
        return [
            {"path": str(path), "role": role, "where": self._where(str(path))}
            for role in ROLES
            for path in table.get(role, [])
        ]

    def _where(self, folder: str) -> Where:
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
            kept = [p for p in table.get(role, []) if not same_folder(p, asked.folder)]
            if role in table or role == asked.role:
                added = [asked.folder] if role == asked.role else []
                table[role] = [host_path(path) for path in (*kept, *added)]
        try:
            FolderSettings.model_validate(document.unwrap().get(_TABLE, {}))
        except ValidationError as exc:
            reason = "; ".join(str(error["msg"]) for error in exc.errors())
            return json_response(HTTPStatus.CONFLICT, {"error": reason})
        write_document(self.config_file, document)
        roles = self.listed()
        now = next(
            (r["role"] for r in roles if same_folder(r["path"], asked.folder)), "none"
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
