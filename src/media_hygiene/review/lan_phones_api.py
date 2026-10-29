"""The paired phones on the PC's page: the list, and "Forget this phone" (0431).

Asked by the PC's loopback only (`lan_app`): a phone never lists nor forgets one. The
list answered after a forget is read back from `phones.json`, never from memory.
"""

from __future__ import annotations

import json
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.review.http import Response
from media_hygiene.review.lan import COOKIE_NAME
from media_hygiene.review.lan_phones import device_name
from media_hygiene.review.local_app import PAGE_PATH
from media_hygiene.review.serving import json_response, refused_post

if TYPE_CHECKING:
    from media_hygiene.review.http import Request
    from media_hygiene.review.lan_phones import PhoneBook

PHONES_PATH: Final = "/api/lan/phones"
FORGET_PATH: Final = "/api/lan/forget"
PHONE_PATHS: Final = frozenset({PHONES_PATH, FORGET_PATH})
# Chrome keeps a cookie 400 days at most; each pairing starts the count again.
COOKIE_SECONDS: Final = 400 * 24 * 3600


def durable_cookie(token: str) -> str:
    """The header giving a phone its own token, for the next runs too.

    Args:
        token: The token drawn for it.

    Returns:
        The `Set-Cookie` header line: HTTPS only, never read by the page's scripts.
        `Lax`, not `Strict`: the installed app opened from its icon arrives as from
        another app, and asked for the code again (maintainer's Android, 2026-10-27);
        every `POST` still checks its `Origin`, and a phone only reads.
    """
    return (
        f"Set-Cookie: {COOKIE_NAME}={token}; Path=/; Max-Age={COOKIE_SECONDS}; "
        "HttpOnly; SameSite=Lax; Secure"
    )


def for_good(answer: Response, phones: PhoneBook | None, request: Request) -> Response:
    """Pair for good a phone whose code was right, on any page under HTTPS (0431).

    Args:
        answer: The pairing's answer: 303 when the code was right.
        phones: The paired-phones file; None without HTTPS.
        request: `GET /pair/<code>`, for the phone's name.

    Returns:
        303 to the page with the phone's own cookie; the answer as it was otherwise
        (a wrong code, no HTTPS, or a file that cannot be written: this run only).
    """
    if answer.status is not HTTPStatus.SEE_OTHER or phones is None:
        return answer
    token = phones.add(device_name(request.headers.get("user-agent", "")))
    if token is None:
        return answer
    headers = (f"Location: {PAGE_PATH}", durable_cookie(token))
    return Response(HTTPStatus.SEE_OTHER, headers=headers)


def phones_list(phones: PhoneBook) -> Response:
    """The paired phones, as on disk.

    Args:
        phones: The paired-phones file (the TVs' beside it, 0456).

    Returns:
        JSON: `phones`, each with `id`, `name` and `paired` (ISO date).
    """
    listed = [
        {"id": p.id, "name": p.name, "paired": p.paired.date().isoformat()}
        for p in (*phones.listed(), *phones.tvs().listed())
    ]
    return json_response(HTTPStatus.OK, {"phones": listed})


def phones_answer(phones: PhoneBook, request: Request) -> Response:
    """Answer the PC's page: `GET` the list, `POST` forget one then the list again.

    Args:
        phones: The paired-phones file.
        request: The request, from the loopback.

    Returns:
        The list read back; 400 without an `id`, 500 when the file kept it.
    """
    if request.method == "GET" and request.path == PHONES_PATH:
        return phones_list(phones)
    if request.method != "POST" or request.path != FORGET_PATH:
        return Response(HTTPStatus.METHOD_NOT_ALLOWED)
    refused = refused_post(request)
    if refused is not None:
        return refused
    try:
        phone_id = str(json.loads(request.body)["id"])
    except ValueError, KeyError, TypeError:
        return Response(HTTPStatus.BAD_REQUEST)
    if not (phones.forget(phone_id) and phones.tvs().forget(phone_id)):
        return json_response(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": phone_id})
    return phones_list(phones)
