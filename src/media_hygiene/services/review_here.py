"""The reviews served by the home server itself, each under its prefix (0357, 0417).

A click on a review from the home page used to stop the home server, start a
container for the review and wait for it (about 5.5 s, *estimated* after 0354). Now
the home server answers it: each time the page itself is asked for, the audit runs
again on the server's settings (from the index: only what changed is read), the
session is built on its findings and the decisions file resumed, as `review` typed
with its option does; the page's paths are relative to it, so its app answers under
the prefix unchanged. `review --near` first (0357), then the burst series,
`--pairs`, `--junk`, `--gone` (0417, `review_kinds`).
"""

from __future__ import annotations

import asyncio
import dataclasses
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.errors import DecisionsError, MountError
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.review.app import ReviewApp
from media_hygiene.review.apply_api import ApplyDesk, ApplyingApp, ApplyOffer
from media_hygiene.review.apply_relay import home_relay
from media_hygiene.review.http import ContentType, Request, Response
from media_hygiene.review.local_app import PAGE_PATH
from media_hygiene.review.page_header import headed_page
from media_hygiene.review.place import DEFAULT_DECISIONS
from media_hygiene.review.step_watch import BURSTS_PAGE, NEAR_REVIEW_PAGE
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.data_checks import refuse_empty_data
from media_hygiene.services.import_note import IMPORTED, imported_note
from media_hygiene.services.page_undo import PageUndo
from media_hygiene.services.review import decisions_path
from media_hygiene.services.review_file import review_page
from media_hygiene.services.review_kinds_more import imported_bursts
from media_hygiene.services.writable import ensure_writable

if TYPE_CHECKING:
    from media_hygiene.review.ending import Handling
    from media_hygiene.review.local_app import LocalApp
    from media_hygiene.services.fresh_runtime import FreshRuntime
    from media_hygiene.services.home_pages import HomeServer
    from media_hygiene.services.review_kinds import ReviewKind
    from media_hygiene.services.slideshow_selection import TvSlot


_TEMPLATES: Final = "media_hygiene.review"
_TIDY_NEXT: Final = {BURSTS_PAGE: NEAR_REVIEW_PAGE}  # the order of a tidying session


class ReviewHere:
    """A review: built again each time its page is opened."""

    def __init__(
        self, kind: ReviewKind, fresh: FreshRuntime, server: HomeServer
    ) -> None:
        """Remember how to build it.

        Args:
            kind: Which review, where it is served.
            fresh: The server's settings, read again when their files change.
            server: The home server's *Apply now*, end and pool.
        """
        self.kind = kind
        self.prefix = kind.page.removesuffix("/")
        self._fresh = fresh
        self._server = server
        self._app: Handling | None = None

    def serves(self, path: str) -> bool:
        """Tell whether a path is this review's.

        Args:
            path: The request's path.

        Returns:
            True for the prefix and every path under it.
        """
        return path == self.prefix or path.startswith(f"{self.prefix}/")

    async def handle(self, request: Request) -> Response:
        """Answer a path under the review's prefix, the prefix taken off.

        Args:
            request: The request, its path under the prefix.

        Returns:
            The response; the page itself rebuilt first.
        """
        path = request.path.removeprefix(self.prefix)
        if not path:  # its paths are relative to the page
            location = f"Location: {self.kind.page}"
            return Response(HTTPStatus.SEE_OTHER, headers=(location,))
        if path == PAGE_PATH and request.method == "GET":
            try:
                only_new = self.kind.page == BURSTS_PAGE and request.query == IMPORTED
                self._app = await asyncio.to_thread(self._build, only_new)
            except (MountError, DecisionsError) as exc:
                return Response(HTTPStatus.CONFLICT, str(exc).encode())
            if self._app is None:
                page = self._nothing(only_new)
                return Response(HTTPStatus.OK, page, ContentType.HTML)
        if self._app is None:
            return Response(HTTPStatus.NOT_FOUND)
        return await self._app.handle(dataclasses.replace(request, path=path))

    def _nothing(self, only_new: bool) -> bytes:  # noqa: FBT001
        """The page of a review with nothing to review; a tidying session goes on.

        Args:
            only_new: The last import's series were asked: *See every series* (0630).

        Returns:
            It, in the language in use.
        """
        environment = translated_environment(_TEMPLATES, escaped=("html", "j2"))
        following = _TIDY_NEXT.get(self.kind.page, "")
        values = {
            "said": self.kind.empty(),
            "tidy_next": following,
            "every_series": only_new,
        }
        return headed_page(environment, "tidy_empty.html.j2", values)

    def _build(self, only_new: bool) -> Handling | None:  # noqa: FBT001
        """Audit from the index, open the session, resume the decisions file.

        Args:
            only_new: The burst series of the last import's new files only (0630).

        Returns:
            The review's app; None when there is nothing to review.
        """
        runtime = self._fresh.runtime()
        refuse_empty_data(runtime, "review")
        ensure_writable(runtime, MountKind.CACHE, MountKind.REPORTS)
        service = AuditService(runtime, NullProgress())
        findings = service.run()
        service.guide.close()
        target = decisions_path(runtime, Path(DEFAULT_DECISIONS))
        opened = imported_bursts if only_new else self.kind.opened
        page = opened(runtime, findings, target)
        if page is None:
            return None
        server = self._server
        body = review_page(page.template, page.place, page.api)
        if only_new:
            body = imported_note(body)
        app = on_tv(page.app(body, server.executor, runtime.previews_dir), server.tv)
        if page.apply is None:
            return app
        offer = ApplyOffer(server.apply, page.apply.pending, PageUndo(runtime))
        relay = home_relay(runtime.locations.reports_dir)
        return ApplyingApp(app, ApplyDesk(offer, server.ending, relay))


def on_tv(app: LocalApp, tv: TvSlot) -> LocalApp:
    """The review's app, its albums API showing files on the home server's TV (0655).

    Args:
        app: The review's app.
        tv: The home server's slideshow slot.

    Returns:
        The same app; a burst review's albums answer `action: "tv"`.
    """
    if not isinstance(app, ReviewApp) or app.albums is None:
        return app
    return dataclasses.replace(app, albums=dataclasses.replace(app.albums, tv=tv))
