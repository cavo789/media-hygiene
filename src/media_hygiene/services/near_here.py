"""`review --near` served by the home server itself, under `/review/near/` (0357).

A click on it from the home page used to stop the home server, start a container for
the review and wait for it (about 5.5 s, *estimated* after 0354). Now the home server
answers it: each time the page itself is asked for, the audit runs again on the
server's settings (from the index: only what changed is read), the session is built on
its findings and the decisions file resumed, as `review --near` typed alone does; the
page's paths are relative to it, so its app answers under the prefix unchanged.
"""

from __future__ import annotations

import asyncio
import dataclasses
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.errors import DecisionsError, MountError
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.review.apply_api import ApplyDesk, ApplyingApp, ApplyOffer
from media_hygiene.review.http import Request, Response
from media_hygiene.review.local_app import PAGE_PATH
from media_hygiene.review.near_app import NEAR_DECIDE_PATH, NEAR_FILE_PATH, NearApp
from media_hygiene.review.place import DEFAULT_DECISIONS
from media_hygiene.review.step_watch import NEAR_REVIEW_PAGE
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.data_checks import refuse_empty_data
from media_hygiene.services.near_reviewing import open_near_review
from media_hygiene.services.review import decisions_path
from media_hygiene.services.review_file import review_page
from media_hygiene.services.writable import ensure_writable

if TYPE_CHECKING:
    from media_hygiene.review.apply_relay import ApplyRelay
    from media_hygiene.review.ending import Handling
    from media_hygiene.services.fresh_runtime import FreshRuntime
    from media_hygiene.services.home_pages import HomeServer

NEAR_PAGE: Final = NEAR_REVIEW_PAGE
NEAR_PREFIX: Final = NEAR_PAGE.removesuffix("/")
_TEMPLATE: Final = "near_review.html.j2"


class NearHere:
    """The near duplicates' review: built again each time its page is opened."""

    def __init__(
        self, fresh: FreshRuntime, server: HomeServer, relay: ApplyRelay
    ) -> None:
        """Remember how to build it.

        Args:
            fresh: The server's settings, read again when their files change.
            server: The home server's *Apply now*, end and pool.
            relay: Where *Apply now* hands its step.
        """
        self._fresh = fresh
        self._server = server
        self._relay = relay
        self._app: Handling | None = None

    async def handle(self, request: Request) -> Response:
        """Answer a path under `/review/near`, the prefix taken off.

        Args:
            request: The request, its path under the prefix.

        Returns:
            The response; the page itself rebuilt first.
        """
        path = request.path.removeprefix(NEAR_PREFIX)
        if not path:  # its paths are relative to `/review/near/`
            return Response(HTTPStatus.SEE_OTHER, headers=(f"Location: {NEAR_PAGE}",))
        if path == PAGE_PATH and request.method == "GET":
            try:
                self._app = await asyncio.to_thread(self._build)
            except (MountError, DecisionsError) as exc:
                return Response(HTTPStatus.CONFLICT, str(exc).encode())
            if self._app is None:
                message = _("No near duplicates: nothing to review.")
                return Response(HTTPStatus.OK, message.encode())
        if self._app is None:
            return Response(HTTPStatus.NOT_FOUND)
        return await self._app.handle(dataclasses.replace(request, path=path))

    def _build(self) -> Handling | None:
        """Audit from the index, open the session, resume the decisions file.

        Returns:
            The review's app; None when there is no near duplicate.
        """
        runtime = self._fresh.runtime()
        refuse_empty_data(runtime, "review")
        ensure_writable(runtime, MountKind.CACHE, MountKind.REPORTS)
        service = AuditService(runtime, NullProgress())
        findings = service.run()
        service.guide.close()
        if not findings.similar.groups:
            return None
        target = decisions_path(runtime, Path(DEFAULT_DECISIONS))
        session = open_near_review(runtime, findings, target)
        page = review_page(_TEMPLATE, session.place, (NEAR_DECIDE_PATH, NEAR_FILE_PATH))
        server = self._server
        app = NearApp(session, page, server.executor, runtime.previews_dir)
        offer = ApplyOffer(server.apply, lambda: session.decided[0] > 0)
        return ApplyingApp(app, ApplyDesk(offer, server.ending, self._relay))
