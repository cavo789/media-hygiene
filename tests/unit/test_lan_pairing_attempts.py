"""Wrong pairing codes throttled per device, reported on the PC, reopened (0681)."""

from __future__ import annotations

import asyncio
import json
import time
from http import HTTPStatus
from typing import Final, override

import pytest

from media_hygiene.review.doors import Door
from media_hygiene.review.http import Request, Response
from media_hygiene.review.lan import COOKIE_NAME, LanAccess
from media_hygiene.review.lan_app import LanApp
from media_hygiene.review.lan_attempts import (
    FIRST_WAIT,
    FREE_TRIES,
    LONGEST_WAIT,
    MAX_FAILURES,
    wait_after,
)
from media_hygiene.review.lan_pc import REOPEN_PATH, SEEN_PATH
from media_hygiene.review.local_app import LocalApp
from media_hygiene.review.serving import peer_of

_PORT: Final = 8765
_ADDRESS: Final = "192.168.1.20"
_HOST: Final = f"{_ADDRESS}:{_PORT}"
_LOOPBACK: Final = f"127.0.0.1:{_PORT}"
_STRANGER: Final = "192.168.1.37"
_FAMILY: Final = "192.168.1.12"
_ANDROID: Final = "Mozilla/5.0 (Linux; Android 14)"


class _Home(LocalApp):
    """Stands for the home page."""

    @override
    async def answer(self, request: Request) -> Response:
        """Answer 200."""
        return Response(HTTPStatus.OK, b"home")


def _app() -> LanApp:
    return LanApp(_Home(), LanAccess(_ADDRESS, _PORT, b"cd" * 32), b"<p>phone</p>")


def _pair(app: LanApp, code: str, peer: str) -> Response:
    headers = {"host": _HOST, "user-agent": _ANDROID}
    request = Request("GET", f"/pair/{code}", headers, door=Door.LAN, peer=peer)
    return asyncio.run(app.handle(request))


def _pc(app: LanApp, path: str, method: str = "GET") -> dict[str, object]:
    headers = {"host": _LOOPBACK}
    if method == "POST":
        headers |= {"content-type": "application/json", "origin": f"http://{_LOOPBACK}"}
    answer = asyncio.run(app.handle(Request(method, path, headers, b"{}")))
    assert answer.status == HTTPStatus.OK
    card: dict[str, object] = json.loads(answer.body)
    return card


def _code(app: LanApp) -> str:
    return str(_pc(app, "/api/lan")["code"]).replace(" ", "")


def test_the_wait_doubles_then_stops_growing() -> None:
    """Free tries, then `FIRST_WAIT` doubling, capped."""
    assert wait_after(FREE_TRIES - 1) == 0
    assert wait_after(FREE_TRIES) == FIRST_WAIT
    assert wait_after(FREE_TRIES + 1) == 2 * FIRST_WAIT
    assert wait_after(FREE_TRIES + 40) == LONGEST_WAIT


def test_one_device_wrong_codes_never_stop_another() -> None:
    """Five wrong codes from one address: it waits, another address pairs."""
    app = _app()
    replies = [_pair(app, "00000000", _STRANGER) for _ in range(5)]
    assert replies[0].status == HTTPStatus.FORBIDDEN
    assert replies[-1].status == HTTPStatus.TOO_MANY_REQUESTS
    right = _code(app)
    assert _pair(app, right, _STRANGER).status == HTTPStatus.TOO_MANY_REQUESTS
    assert _pair(app, right, _FAMILY).status == HTTPStatus.SEE_OTHER


def test_the_wait_ends(monkeypatch: pytest.MonkeyPatch) -> None:
    """Once its wait is over, the device types again."""
    app = _app()
    for _ in range(FREE_TRIES):
        _pair(app, "00000000", _STRANGER)
    later = time.monotonic() + LONGEST_WAIT + 1
    monkeypatch.setattr(time, "monotonic", lambda: later)
    assert _pair(app, _code(app), _STRANGER).status == HTTPStatus.SEE_OTHER


def test_the_card_reports_the_attempts_and_the_new_devices() -> None:
    """The address, its count and a time; the device paired, read from the server."""
    app = _app()
    for _ in range(FREE_TRIES):
        _pair(app, "11111111", _STRANGER)
    _pair(app, _code(app), _FAMILY)
    card = _pc(app, "/api/lan")
    attempts = card["attempts"]
    assert isinstance(attempts, list)
    assert [(a["address"], a["failures"]) for a in attempts] == [
        (_STRANGER, FREE_TRIES)
    ]
    paired = card["paired"]
    assert isinstance(paired, list)
    assert [p["name"] for p in paired] == ["Android"]
    assert card["closed"] is False
    assert _pc(app, SEEN_PATH, "POST")["attempts"] == []  # *It was me*


def test_open_pairing_again_gives_a_new_code_that_works() -> None:
    """After the run's ceiling, a new code; the old one opens nothing.

    The phones paired with the old code keep their cookie.
    """
    app = _app()
    old = _code(app)
    first = _pair(app, old, _FAMILY)
    cookie = next(h for h in first.headers if h.startswith("Set-Cookie"))
    token = cookie.split(f"{COOKIE_NAME}=")[1].split(";")[0]
    for n in range(MAX_FAILURES):
        _pair(app, "00000000", f"192.168.1.{100 + n}")
    assert _pc(app, "/api/lan")["closed"] is True
    assert _pair(app, old, "192.168.1.90").status == HTTPStatus.TOO_MANY_REQUESTS
    card = _pc(app, REOPEN_PATH, "POST")
    new = str(card["code"]).replace(" ", "")
    assert new != old
    assert card["closed"] is False
    assert card["attempts"] == []
    assert _pair(app, old, "192.168.1.91").status == HTTPStatus.FORBIDDEN
    assert _pair(app, new, "192.168.1.92").status == HTTPStatus.SEE_OTHER
    headers = {"host": _HOST, "cookie": f"{COOKIE_NAME}={token}"}
    page = Request("GET", "/", headers, door=Door.LAN, peer=_FAMILY)
    assert asyncio.run(app.handle(page)).status == HTTPStatus.OK


def test_a_phone_cannot_reopen_the_pairing() -> None:
    """The buttons are the PC's: the home network's door refuses them."""
    app = _app()
    headers = {"host": _HOST, "content-type": "application/json"}
    asked = Request("POST", REOPEN_PATH, headers, b"{}", door=Door.LAN, peer=_STRANGER)
    assert asyncio.run(app.handle(asked)).status == HTTPStatus.FORBIDDEN
    assert app.pairing.generation == 0


class _Writer:
    """Stands for a connection's writer."""

    def __init__(self, peer: object) -> None:
        self.peer = peer

    def get_extra_info(self, name: str) -> object:
        """The socket's peer."""
        return self.peer if name == "peername" else None


@pytest.mark.parametrize(
    ("peer", "address"), [((_STRANGER, 50000), _STRANGER), (None, ""), ((), "")]
)
def test_the_address_comes_from_the_socket(peer: object, address: str) -> None:
    """The peer's address from the socket; nothing when it does not say."""
    assert peer_of(_Writer(peer)) == address  # type: ignore[arg-type]
