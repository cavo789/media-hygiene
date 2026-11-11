"""The paired phones on the PC's page: the list, and "Forget this phone" (0431).

Since 0683 each with its last seen date, address and days of activity, renamed by
the user, and all forgotten at once (*Forget every device*).

Asked by the PC's loopback only (`lan_app`): a phone never lists nor forgets one. The
list answered after a forget is read back from `phones.json`, never from memory.
"""

from __future__ import annotations

import json
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.review.http import Response
from media_hygiene.review.lan import COOKIE_NAME
from media_hygiene.review.lan_phone_care import forget_all, rename
from media_hygiene.review.lan_phone_model import GUEST, device_name
from media_hygiene.review.local_app import PAGE_PATH
from media_hygiene.review.serving import json_response, refused_post

if TYPE_CHECKING:
    from media_hygiene.review.http import Request
    from media_hygiene.review.lan_activity import Activity
    from media_hygiene.review.lan_phone_model import Phone
    from media_hygiene.review.lan_phones import PhoneBook

PHONES_PATH: Final = "/api/lan/phones"
FORGET_PATH: Final = "/api/lan/forget"
RENAME_PATH: Final = "/api/lan/rename"  # a name typed on the PC's card (0683)
FORGET_ALL_PATH: Final = "/api/lan/forget-all"  # *Forget every device* (0683)
PHONE_PATHS: Final = frozenset({PHONES_PATH, FORGET_PATH, RENAME_PATH, FORGET_ALL_PATH})
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


def _device(phone: Phone, activity: Activity | None, *, tv: bool) -> dict[str, object]:
    """One device as the PC's card shows it (0683).

    Args:
        phone: As on disk.
        activity: The counts per day; None without.
        tv: It is a TV of the slideshow.

    Returns:
        `id`, `name`, `paired`, `seen` (ISO instant or empty), `address`, `tv`, `days`.
    """
    seen = "" if phone.last_seen is None else phone.last_seen.isoformat()
    days = [] if activity is None else activity.of(phone.id)
    return {
        "id": phone.id,
        "name": phone.name,
        "paired": phone.paired.date().isoformat(),
        "seen": seen,
        "address": phone.address,
        "tv": tv,
        "guest": phone.role == GUEST,  # 0684
        "days": days,
    }


def phones_list(phones: PhoneBook, activity: Activity | None = None) -> Response:
    """The paired phones and TVs, as on disk.

    Args:
        phones: The paired-phones file (the TVs' beside it, 0456).
        activity: What each one did per day (0683); None without.

    Returns:
        JSON: `phones` (see `_device`) and `expired`: the names forgotten at this
        start, unseen for long.
    """
    listed = [_device(p, activity, tv=False) for p in phones.listed()]
    listed += [_device(p, activity, tv=True) for p in phones.tvs().listed()]
    body = {"phones": listed, "expired": list(phones.expired)}
    return json_response(HTTPStatus.OK, body)


def _changed(phones: PhoneBook, request: Request) -> bool | None:
    """Apply a forget, a rename or *Forget every device*.

    Args:
        phones: The paired-phones file.
        request: The `POST`.

    Returns:
        True when read back as asked, False when the file kept it, None for a bad body.
    """
    if request.path == FORGET_ALL_PATH:
        return forget_all(phones)
    try:
        asked = json.loads(request.body)
        phone_id = str(asked["id"])
        name = str(asked["name"]) if request.path == RENAME_PATH else ""
    except ValueError, KeyError, TypeError:
        return None
    if request.path == RENAME_PATH:
        return rename(phones, phone_id, name) or rename(phones.tvs(), phone_id, name)
    return phones.forget(phone_id) and phones.tvs().forget(phone_id)


def phones_answer(
    phones: PhoneBook, activity: Activity | None, request: Request
) -> Response:
    """Answer the PC's page: `GET` the list, `POST` change it then the list again.

    Args:
        phones: The paired-phones file.
        activity: What each one did per day; None without.
        request: The request, from the loopback.

    Returns:
        The list read back; 400 for a bad body, 500 when the file kept it.
    """
    if request.method == "GET" and request.path == PHONES_PATH:
        return phones_list(phones, activity)
    if request.method != "POST" or request.path == PHONES_PATH:
        return Response(HTTPStatus.METHOD_NOT_ALLOWED)
    refused = refused_post(request)
    if refused is not None:
        return refused
    done = _changed(phones, request)
    if done is None:
        return Response(HTTPStatus.BAD_REQUEST)
    if not done:
        return json_response(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": request.path})
    return phones_list(phones, activity)
