"""*Make the folder in Explorer* from an album's page (0625): shown first, then made.

`POST /api/album-make` with an album: the dry run of `album` (links to make and to
remove, files not found), nothing touched. With `apply` and the counts it showed, the
same run as `album --apply`: journaled, its `undo` line said, what the folder holds
read back from the disk. Counts that changed since: shown again, nothing made.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.classify.album_rows import Criteria
from media_hygiene.config.loader import load_settings
from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import _, ngettext
from media_hygiene.review.http import Response
from media_hygiene.review.serving import json_response
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.album import AlbumRequest, AlbumService

if TYPE_CHECKING:
    from media_hygiene.services.album import AlbumPrepared, AlbumResult
    from media_hygiene.services.runtime import Runtime

ALBUM_MAKE_PATH: Final = "/api/album-make"
_MAX_TEXT: Final = 200


class MakeAsked(BaseModel):
    """`POST /api/album-make`: an album; `apply` with the counts the page showed."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    album: str = Field(min_length=1, max_length=_MAX_TEXT)
    apply: bool = False
    links: int = 0
    remove: int = 0


def _preview(prepared: AlbumPrepared, folder: str) -> dict[str, object]:
    """What the run would do, in a few lines and a button stating the count.

    Args:
        prepared: The album.
        folder: Its folder (host path).

    Returns:
        The answer's JSON.
    """
    plan = prepared.plan
    links, remove = len(plan.links), len(plan.leftovers.stale)
    lines = [
        _("Folder: {folder}").format(folder=folder),
        ngettext("{n} link to make.", "{n} links to make.", links).format(n=links),
    ]
    for count, one, many in (
        (remove, _("{n} link to remove."), _("{n} links to remove.")),
        (len(plan.present), _("{n} already there."), _("{n} already there.")),
        (len(plan.missing), _("{n} file not found."), _("{n} files not found.")),
        (
            len(plan.elsewhere),
            _("{n} file on another disk or mount: no link possible."),
            _("{n} files on another disk or mount: no link possible."),
        ),
    ):
        if count:
            lines.append((one if count == 1 else many).format(n=count))
    return {
        "said": lines,
        "links": links,
        "remove": remove,
        "button": ngettext(
            "📁 Make the folder: {n} change",
            "📁 Make the folder: {n} changes",
            links + remove,
        ).format(n=links + remove),
    }


@dataclass(frozen=True, slots=True)
class AlbumMakeDesk:
    """Shows, then makes, the folder of links of an album of `albums.json`."""

    runtime: Runtime

    def answer(self, body: bytes) -> Response:
        """`POST /api/album-make`: the dry run, or the run.

        Args:
            body: The JSON the page sent.

        Returns:
            What it would do or did; `ask_folder` when no folder holds the albums;
            400 for a bad body, 409 with the reason when it cannot be done.
        """
        try:
            asked = MakeAsked.model_validate_json(body)
        except ValidationError:
            return Response(HTTPStatus.BAD_REQUEST)
        runtime = self.runtime
        now = replace(
            runtime, loaded=load_settings(runtime.locations, runtime.cli_layer)
        )
        if not (now.settings.album.root or now.settings.classify.target):
            return json_response(HTTPStatus.OK, {"ask_folder": True})
        try:
            return json_response(HTTPStatus.OK, self._acted(now, asked))
        except MediaHygieneError as exc:
            said = " ".join(part for part in (exc.message, exc.tip) if part)
            return json_response(HTTPStatus.CONFLICT, {"error": said})
        except OSError as exc:
            return json_response(HTTPStatus.CONFLICT, {"error": str(exc)})

    def _acted(self, now: Runtime, asked: MakeAsked) -> dict[str, object]:
        """Prepare the album, and make it when asked with the counts still true.

        Args:
            now: The runtime, its settings read from the disk.
            asked: The request.

        Returns:
            The answer's JSON.
        """
        service = AlbumService(now, NullProgress())
        service.ensure_ready()  # no journal, read-only photos: said before anything
        request = AlbumRequest(asked.album, Criteria())
        prepared = service.prepare(request)
        folder = now.mapper.to_host(prepared.plan.folder)
        shown = _preview(prepared, folder)
        if not asked.apply:
            return shown
        if (asked.links, asked.remove) != (shown["links"], shown["remove"]):
            lines = [_("The album changed since: look again."), *shown["said"]]  # type: ignore[misc]
            return {**shown, "said": lines}
        result = service.execute(prepared, lambda: False)
        return _done(result, service.prepare(request), folder)


def _done(result: AlbumResult, after: AlbumPrepared, folder: str) -> dict[str, object]:
    """What the run did, the folder read back from the disk, and how to undo it.

    Args:
        result: The run.
        after: The album prepared again after it.
        folder: Its folder (host path).

    Returns:
        The answer's JSON.
    """
    held = len(after.plan.present)
    lines = [
        ngettext(
            "{n} photo or video in {folder}, read back from the disk: nothing "
            "copied, no extra space.",
            "{n} photos and videos in {folder}, read back from the disk: nothing "
            "copied, no extra space.",
            held,
        ).format(n=held, folder=folder)
    ]
    if result.ended.unsupported:
        lines.append(result.ended.unsupported)
    failed = len(result.outcome.failed)
    if failed:
        lines.append(
            ngettext("{n} link failed.", "{n} links failed.", failed).format(n=failed)
        )
    lines.append(_("To undo: {commands}").format(commands=f"mh undo {result.run_id}"))
    return {"said": lines, "done": True}
