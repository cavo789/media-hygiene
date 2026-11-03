"""*Move the album folders*, offered once `[album] root` changed on the page (0582).

`POST /api/album-root/move` with the old folder: each album of `albums.json` still
in it is made again in the root `config.toml` names now (read from the disk), one
journaled album run per album, then the old folder is emptied of the links the tool
made (`services/album_relocate`). The answer says what moved and what stayed, read
back from the disk.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.config.loader import load_settings
from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import _, ngettext
from media_hygiene.review.serving import json_response
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.album_relocate import AlbumMove, albums_in, relocate

if TYPE_CHECKING:
    from media_hygiene.review.http import Response
    from media_hygiene.services.album_relocate import Relocated
    from media_hygiene.services.runtime import Runtime

ALBUM_MOVE_PATH: Final = "/api/album-root/move"
_MAX_PATH: Final = 4096


class MoveAsked(BaseModel):
    """`POST /api/album-root/move`: the folder the albums were in (host path)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    old: str = Field(min_length=1, max_length=_MAX_PATH)


@dataclass(frozen=True, slots=True)
class AlbumMoveDesk:
    """Counts the album folders of an old root, and moves them on demand."""

    runtime: Runtime

    def movable(self, old: str) -> int:
        """How many albums of `albums.json` still have a folder in an old root.

        Args:
            old: The old root (host path).

        Returns:
            Their count; 0 when the albums file cannot be read.
        """
        try:
            return len(albums_in(self.runtime, self.runtime.mapper.to_container(old)))
        except OSError, MediaHygieneError:
            return 0

    def answer(self, body: bytes) -> Response:
        """`POST /api/album-root/move`: move every album folder of the old root.

        Args:
            body: The JSON the page sent.

        Returns:
            What moved and what stayed; 400 for a bad body, 409 when nothing may
            be done (no journal, the new folder refused).
        """
        try:
            asked = MoveAsked.model_validate_json(body)
        except ValidationError as exc:
            reason = "; ".join(str(error["msg"]) for error in exc.errors())
            return json_response(HTTPStatus.BAD_REQUEST, {"error": reason})
        runtime = self.runtime
        now = replace(
            runtime, loaded=load_settings(runtime.locations, runtime.cli_layer)
        )
        move = AlbumMove(now, NullProgress(), lambda: False)
        try:
            done = relocate(move, runtime.mapper.to_container(asked.old))
        except (OSError, MediaHygieneError) as exc:
            return json_response(HTTPStatus.CONFLICT, {"error": str(exc)})
        return json_response(HTTPStatus.OK, {"said": self._said(done, asked.old)})

    def _said(self, done: tuple[Relocated, ...], old: str) -> str:
        """The sentence of the move, from what the runs did on the disk.

        Args:
            done: The albums moved.
            old: The old root (host path).

        Returns:
            It, with the undo line and the files that stayed.
        """
        said = ngettext(
            "{n} album made again in the new folder.",
            "{n} albums made again in the new folder.",
            len(done),
        ).format(n=len(done))
        kept = [p for each in done if each.vacated for p in each.vacated.kept]
        if kept:
            mapper = self.runtime.mapper
            said += " " + ngettext(
                "{n} file of {folder} was not made by media-hygiene: it stays "
                "({files}).",
                "{n} files of {folder} were not made by media-hygiene: they stay "
                "({files}).",
                len(kept),
            ).format(
                n=len(kept),
                folder=old,
                files=", ".join(mapper.to_host(p) for p in kept[:5]),
            )
        commands = "; ".join(f"mh undo {each.run_id}" for each in done)
        if commands:
            said += " " + _("To undo: {commands}").format(commands=commands)
        return said
