r"""Where the albums go, said and changed from the album bar (0534).

`GET /api/album-root` says `[album] root` as `config.toml` holds it now, and the folder
used when it is empty (`Albums` in the `[classify] target`). `POST /api/album-root`
sets it: the folder must be in a mounted folder, outside the protected ones, and
writable (the checks of `album_folder`); the file is edited with `toml_edit`
(comments kept, atomic), then read back from the disk before it is said.
"""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.config.album_settings import AlbumSettings
from media_hygiene.i18n import _, ngettext
from media_hygiene.paths.host_paths import is_within
from media_hygiene.paths.mounts import is_writable
from media_hygiene.places.toml_edit import (
    document_of,
    host_path,
    loaded,
    table_of,
    write_document,
)
from media_hygiene.review.serving import json_response
from media_hygiene.search.album_move_desk import AlbumMoveDesk
from media_hygiene.search.folder_role_desk import ALBUM_ROOT_PATH
from media_hygiene.search.folders import FOLDERS_PATH

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.review.http import Response
    from media_hygiene.search.folder_role_desk import RoleDesk
    from media_hygiene.search.folders import FolderDesk
    from media_hygiene.services.runtime import Runtime

_TABLE: Final = "album"
_MAX_PATH: Final = 4096


class RootAsked(BaseModel):
    """`POST /api/album-root`: the host folder of the albums; empty: the default."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    root: str = Field(max_length=_MAX_PATH)


@dataclass(frozen=True, slots=True)
class AlbumRootDesk:
    """Reads and writes `[album] root`, with the files and mounts of the roles."""

    roles: RoleDesk  # `config.toml`, the host paths, the mounted folders
    move: AlbumMoveDesk | None = None  # moves the folders made before (0582)

    def shown(self) -> dict[str, str]:
        """The folder of the albums, as the file on the disk says it now.

        Returns:
            `root` (as written, maybe empty) and `used`: the folder the albums go
            to, empty when neither `[album] root` nor `[classify] target` is set.
        """
        config = loaded(self.roles.config_file)
        root = str(config.get(_TABLE, {}).get("root", ""))
        target = str(config.get("classify", {}).get("target", ""))
        mapper = self.roles.mapper
        default = mapper.to_host(mapper.to_container(target) / _("Albums"))
        return {"root": root, "used": root or (default if target else "")}

    def state(self) -> Response:
        """`GET /api/album-root`.

        Returns:
            The folder of the albums, read from the disk.
        """
        shown: dict[str, object] = {**self.shown()}
        return json_response(HTTPStatus.OK, shown)

    def answer(self, body: bytes) -> Response:
        """`POST /api/album-root`: save the folder of the albums.

        Args:
            body: The JSON the page sent.

        Returns:
            The folder read back and the sentence; 400 for a body that is not a
            folder, 409, the file unchanged, for a folder where no album can go.
        """
        try:
            asked = RootAsked.model_validate_json(body)
            AlbumSettings(root=asked.root.strip())
        except ValidationError as exc:
            reason = "; ".join(str(error["msg"]) for error in exc.errors())
            return json_response(HTTPStatus.BAD_REQUEST, {"error": reason})
        root = asked.root.strip()
        refused = self._refused(root) if root else None
        if refused is not None:
            return json_response(HTTPStatus.CONFLICT, {"error": refused})
        before = self.shown()["used"]
        document = document_of(self.roles.config_file)
        table_of(document, _TABLE)["root"] = host_path(root)
        write_document(self.roles.config_file, document)
        now = self.shown()
        said = _("Saved in {file}: your albums now go to {folder}.").format(
            file=self.roles.mapper.to_host(self.roles.config_file),
            folder=now["used"] or "—",
        )
        movable = 0
        if before and before != now["used"] and self.move is not None:
            movable = self.move.movable(before)
        if movable:
            said += " " + ngettext(
                "{n} album folder was made in {folder}: move it to the new folder?",
                "{n} album folders were made in {folder}: move them to the new folder?",
                movable,
            ).format(n=movable, folder=before)
        return json_response(
            HTTPStatus.OK, {**now, "said": said, "movable": movable, "old": before}
        )

    def _refused(self, root: str) -> str | None:
        """Why no album may go to a folder: not mounted, protected, read-only.

        Args:
            root: Its host path.

        Returns:
            The reason; None when albums may go there.
        """
        inside = self.roles.mapper.to_container(root)
        if not any(is_within(inside, top) for top in self.roles.roots):
            return _(
                "{path} is not in a mounted folder: an album made there would vanish "
                "with the container."
            ).format(path=root)
        protected = (
            loaded(self.roles.config_file).get("folders", {}).get("protected", [])
        )
        mapper = self.roles.mapper
        if any(is_within(inside, mapper.to_container(str(p))) for p in protected):
            return _(
                "{path} is inside a protected folder: nothing is ever added there."
            ).format(path=root)
        existing = next(p for p in (inside, *inside.parents) if p.exists())
        if not is_writable(existing):
            return _("The container cannot write to {folders}.").format(folders=root)
        return None


def folder_gets(folders: FolderDesk) -> dict[str, Callable[[], Response]]:
    """The `GET` routes of the folder view: the tree, and the albums' folder.

    Args:
        folders: The folder view.

    Returns:
        Each path and what answers it.
    """
    gets: dict[str, Callable[[], Response]] = {FOLDERS_PATH: folders.tree}
    if folders.album_root is not None:
        gets[ALBUM_ROOT_PATH] = folders.album_root.state
    return gets


def album_root_desk(roles: RoleDesk, runtime: Runtime) -> AlbumRootDesk:
    """The desk of the albums' folder, able to move the folders made before.

    Args:
        roles: `config.toml`, the host paths, the mounted folders.
        runtime: Settings, mount points and output of the page.

    Returns:
        It.
    """
    return AlbumRootDesk(roles, AlbumMoveDesk(runtime))
