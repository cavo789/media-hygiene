"""What the PC's door of `mh --lan` answers besides the home page (0269, 0681).

The card (`GET /api/lan`: the code, its QR code, the wrong codes per address and the
devices paired this run, the connections the home network's doors refused, 0682),
*Open pairing again* (a new code, no restart) and *It was me*
(the report put away), the paired phones (0431), an album's link (0462). The loopback
only: a phone never asks them. Each `POST` answers the card read back from the server.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Final

from media_hygiene.review.http import Response, is_local
from media_hygiene.review.lan_card import lan_response
from media_hygiene.review.lan_gate import lan_gate
from media_hygiene.review.lan_paths import LAN_PATH
from media_hygiene.review.lan_phones_api import PHONE_PATHS, phones_answer
from media_hygiene.review.serving import refused_post
from media_hygiene.share.album_link_door import ALBUM_LINK_PATH

if TYPE_CHECKING:
    from media_hygiene.review.http import Request
    from media_hygiene.review.lan_app import LanApp

REOPEN_PATH: Final = f"{LAN_PATH}/reopen"  # *Open pairing again*: a new code
SEEN_PATH: Final = f"{LAN_PATH}/seen"  # *It was me*: the report put away
_POST: Final = "POST"


def card(app: LanApp) -> Response:
    """The PC's card, with what the pairing saw this run.

    Args:
        app: The home network's door.

    Returns:
        JSON: what `lan_response` says, plus `attempts`, `closed`, `paired`,
        `refused` (connections beyond the doors' caps, per address) and the
        paths `reopen` and `seen`.
    """
    pairing = app.pairing
    answer = lan_response(pairing.access(app.lan), phones=app.phones is not None)
    extra = {
        "attempts": pairing.attempts.reported(),
        "closed": pairing.closed,
        "paired": pairing.paired,
        "refused": lan_gate().reported(),
        "reopen": REOPEN_PATH,
        "seen": SEEN_PATH,
    }
    return lan_response_with(answer, extra)


def lan_response_with(answer: Response, extra: dict[str, object]) -> Response:
    """Add fields to the card's JSON.

    Args:
        answer: The card.
        extra: The fields to add.

    Returns:
        The card with them.
    """
    merged = json.loads(answer.body) | extra
    return Response(answer.status, json.dumps(merged).encode(), answer.content_type)


def _pairing_post(app: LanApp, request: Request) -> Response:
    """*Open pairing again* or *It was me*, then the card read back.

    Args:
        app: The home network's door.
        request: The `POST`, from the loopback.

    Returns:
        The card; 415/403 for a request not from the page itself.
    """
    refused = refused_post(request)
    if refused is not None:
        return refused
    if request.path == REOPEN_PATH:
        app.pairing.reopen()
    else:
        app.pairing.attempts.seen()
        lan_gate().seen()
    return card(app)


async def pc_answer(app: LanApp, request: Request) -> Response:
    """Answer the PC: the card, the pairing's buttons, its phones, or the home page.

    Args:
        app: The home network's door.
        request: A request of the PC's door.

    Returns:
        The response.
    """
    if not is_local(request):
        return await app.home.handle(request)
    if request.path == LAN_PATH:
        return card(app)
    if request.method == _POST and request.path in {REOPEN_PATH, SEEN_PATH}:
        return _pairing_post(app, request)
    if request.method == _POST and request.path == ALBUM_LINK_PATH and app.links:
        refused = refused_post(request)  # the PC's page alone makes a link
        return refused or await app.links.make(request, app.lan)
    if request.path in PHONE_PATHS and app.phones is not None:
        return phones_answer(app.phones, app.phones.activity, request)
    return await app.home.handle(request)
