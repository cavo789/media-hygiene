"""The nonce of each page's scripts: an injected `<script>` or `onerror=` never runs.

Templates write `nonce="{{ page_nonce }}"` on each `<script>`: a mark drawn at each run,
never sent as it is (0671). `write_response` replaces it, in the HTML body and in the
Content-Security-Policy alike, by a nonce drawn for that answer; so a page rendered
once and kept (the home page) still gets a fresh one each time. An answer the browser
may keep and revalidate (`cacheable`: a 304 keeps the body it holds) gets the run's own
nonce, the same as long as its ETag. A report written to the disk is served as it lies:
its scripts are allowed by their SHA-256 (`hashed_policy`), never by `'unsafe-inline'`.
"""

from __future__ import annotations

import base64
import hashlib
import re
import secrets
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from media_hygiene.review.http import Response

_SIZE: Final = 16  # bytes of randomness: 128 bits
NONCE_MARK: Final = f"mh-nonce-{secrets.token_hex(_SIZE)}"  # never leaves the process
_RUN_NONCE: Final = secrets.token_urlsafe(_SIZE)
NONCED: Final = f"'nonce-{NONCE_MARK}'"  # what a policy's `script-src` names
# Itself only (+ manifest, worker: the phone's app, 0432); `places` adds scripts, tiles.
# Styles stay inline: the console pages (Rich) and `style="…"` attributes need it.
REVIEW_POLICY: Final = (
    f"default-src 'none'; script-src {NONCED}; style-src 'unsafe-inline'; "
    "img-src 'self'; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; "
    "manifest-src 'self'; worker-src 'self'"
)
_HTML: Final = "text/html"
_SCRIPT: Final = re.compile(
    rb"<script\b(?P<attributes>[^>]*)>(?P<code>.*?)</script>", re.DOTALL
)
_SOURCED: Final = re.compile(rb"\ssrc\s*=")


def sealed(response: Response) -> tuple[bytes, str]:
    """The body and the policy of an answer, the mark replaced by its nonce.

    Args:
        response: The answer.

    Returns:
        Its body (only an HTML one is changed) and its Content-Security-Policy.
    """
    if NONCE_MARK not in response.policy:
        return response.body, response.policy
    nonce = _RUN_NONCE if response.cacheable else secrets.token_urlsafe(_SIZE)
    body = response.body
    if response.content_type.startswith(_HTML):
        body = body.replace(NONCE_MARK.encode(), nonce.encode())
    return body, response.policy.replace(NONCE_MARK, nonce)


def hashed_policy(policy: str, page: bytes) -> str:
    """A policy that also allows the inline scripts of a page, by their SHA-256.

    Args:
        policy: A policy whose `script-src` names `NONCED`.
        page: The page, as it will be sent.

    Returns:
        The policy, each inline script of the page added as `'sha256-…'`.
    """
    hashes = " ".join(
        f"'sha256-{_digest(found.group('code'))}'"
        for found in _SCRIPT.finditer(page)
        if not _SOURCED.search(found.group("attributes"))
    )
    return policy.replace(NONCED, f"{NONCED} {hashes}".rstrip()) if hashes else policy


def _digest(code: bytes) -> str:
    """The SHA-256 of a script, as a policy names it.

    Args:
        code: The script's text, as sent.

    Returns:
        Its digest in base 64.
    """
    return base64.b64encode(hashlib.sha256(code).digest()).decode()
