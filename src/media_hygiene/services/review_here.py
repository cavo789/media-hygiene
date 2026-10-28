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
from typing import TYPE_CHECKING

from media_hygiene.errors import DecisionsError, MountError
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.review.apply_api import ApplyDesk, ApplyingApp, ApplyOffer
from media_hygiene.review.apply_relay import home_relay
from media_hygiene.review.http import Request, Response
from media_hygiene.review.local_app import PAGE_PATH
from media_hygiene.review.place import DEFAULT_DECISIONS
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.data_checks import refuse_empty_data
from media_hygiene.services.review import decisions_path
from media_hygiene.services.review_file import review_page
from media_hygiene.services.writable import ensure_writable

if TYPE_CHECKING:
    from media_hygiene.review.ending import Handling
    from media_hygiene.services.fresh_runtime import FreshRuntime
    from media_hygiene.services.home_pages import HomeServer
    from media_hygiene.services.review_kinds import ReviewKind


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
                self._app = await asyncio.to_thread(self._build)
            except (MountError, DecisionsError) as exc:
                return Response(HTTPStatus.CONFLICT, str(exc).encode())
            if self._app is None:
                return Response(HTTPStatus.OK, self.kind.empty().encode())
        if self._app is None:
            return Response(HTTPStatus.NOT_FOUND)
        return await self._app.handle(dataclasses.replace(request, path=path))

    def _build(self) -> Handling | None:
        """Audit from the index, open the session, resume the decisions file.

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
        page = self.kind.opened(runtime, findings, target)
        if page is None:
            return None
        server = self._server
        body = review_page(page.template, page.place, page.api)
        app = page.app(body, server.executor, runtime.previews_dir)
        if page.apply is None:
            return app
        offer = ApplyOffer(server.apply, page.apply.pending)
        relay = home_relay(runtime.locations.reports_dir)
        return ApplyingApp(app, ApplyDesk(offer, server.ending, relay))
