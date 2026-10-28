"""Phones paired once with the home page stay paired across runs (0431).

The paired-phones file (hashes only, atomic, read back, a bad file means pairing again),
the durable `Secure` cookie, a phone recognised after a restart (a new secret), a
forgotten one refused, and the PC's list with "Forget this phone" (loopback only).
"""

from __future__ import annotations

import asyncio
import json
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.review.doors import Door
from media_hygiene.review.http import Request, Response
from media_hygiene.review.lan import COOKIE_NAME, LanAccess
from media_hygiene.review.lan_app import LanApp
from media_hygiene.review.lan_paths import LAN_PATH
from media_hygiene.review.lan_phones import (
    DEFAULT_DEVICE,
    PHONES_FILE,
    PhoneBook,
    device_name,
    phone_book,
)
from media_hygiene.review.lan_phones_api import FORGET_PATH, PHONES_PATH

if TYPE_CHECKING:
    from pathlib import Path

_ADDRESS: Final = "192.168.1.20"
_PORT: Final = 8088
_HOST: Final = f"{_ADDRESS}:{_PORT}"
_LOCAL: Final = f"127.0.0.1:{_PORT}"
_ANDROID: Final = "Mozilla/5.0 (Linux; Android 14; Pixel 8) Chrome/130"
_JSON: Final = "application/json"


class _Home:
    """Stands for the home page: answers 200."""

    async def handle(self, _request: Request) -> Response:
        """Answer 200.

        Returns:
            An empty page.
        """
        return Response(HTTPStatus.OK, b"home")


def _app(tmp_path: Path, secret: bytes = b"a" * 32) -> LanApp:
    lan = LanAccess(_ADDRESS, _PORT, secret, secure=True)
    return LanApp(_Home(), lan, b"<p>phone</p>", phones=PhoneBook(tmp_path))


def _ask(app: LanApp, request: Request) -> Response:
    return asyncio.run(app.handle(request))


def _phone(path: str, cookie: str = "") -> Request:
    headers = {"host": _HOST, "user-agent": _ANDROID}
    if cookie:
        headers["cookie"] = f"{COOKIE_NAME}={cookie}"
    return Request("GET", path, headers, b"", Door.LAN)


def _pc(path: str, body: dict[str, str] | None = None) -> Request:
    if body is None:
        return Request("GET", path, {"host": _LOCAL}, b"", Door.PC)
    headers = {"host": _LOCAL, "content-type": _JSON, "origin": f"http://{_LOCAL}"}
    return Request("POST", path, headers, json.dumps(body).encode(), Door.PC)


def _pair(app: LanApp) -> tuple[str, str]:
    """Pair through the code; the cookie's token and the whole header."""
    answer = _ask(app, _phone(f"/pair/{app.lan.code}"))
    assert answer.status is HTTPStatus.SEE_OTHER
    header = next(h for h in answer.headers if h.startswith("Set-Cookie:"))
    token = header.split(f"{COOKIE_NAME}=", 1)[1].split(";", 1)[0]
    return token, header


def test_a_phone_is_kept_by_its_hash_only(tmp_path: Path) -> None:
    """The file names the phone and holds the token's hash, never the token."""
    book = PhoneBook(tmp_path)
    token = book.add("Android")
    assert token is not None
    text = (tmp_path / PHONES_FILE).read_text(encoding="utf-8")
    assert token not in text
    assert "Android" in text
    assert PhoneBook(tmp_path).knows(token)  # read again, as after a restart
    assert not book.knows("")
    assert not book.knows("0" * 64)


def test_a_bad_file_means_pairing_again(tmp_path: Path) -> None:
    """A missing or unreadable file lists nobody and never fails."""
    book = PhoneBook(tmp_path)
    assert book.listed() == ()
    (tmp_path / PHONES_FILE).write_text("{not json", encoding="utf-8")
    assert book.listed() == ()
    assert not book.knows("x")
    assert book.add("iPhone") is not None  # the file is written anew


def test_a_forgotten_phone_is_gone_on_disk(tmp_path: Path) -> None:
    """Forget removes one phone and keeps the others, read back."""
    book = PhoneBook(tmp_path)
    first, second = book.add("Android"), book.add("iPhone")
    assert first is not None
    assert second is not None
    gone = book.listed()[0].id
    assert book.forget(gone)
    assert not book.knows(first)
    assert book.knows(second)
    assert [phone.name for phone in PhoneBook(tmp_path).listed()] == ["iPhone"]


@pytest.mark.parametrize(
    ("agent", "name"),
    [
        (_ANDROID, "Android"),
        ("Mozilla/5.0 (iPhone; CPU iPhone OS 18_0)", "iPhone"),
        ("Mozilla/5.0 (iPad; CPU OS 18_0)", "iPad"),
        ("curl/8", DEFAULT_DEVICE),
    ],
)
def test_a_phone_is_named_after_its_browser(agent: str, name: str) -> None:
    """The PC's list says which phone it is."""
    assert device_name(agent) == name


def test_the_durable_cookie_survives_a_restart(tmp_path: Path) -> None:
    """Paired once, the phone opens the page of the next run without a code."""
    token, header = _pair(_app(tmp_path))
    for part in ("HttpOnly", "SameSite=Lax", "Secure", "Max-Age="):
        assert part in header
    later = _app(tmp_path, secret=b"b" * 32)  # a new run: a new secret
    assert _ask(later, _phone("/", token)).status is HTTPStatus.OK
    assert _ask(later, _phone("/")).status is HTTPStatus.UNAUTHORIZED


def test_a_forgotten_phone_gets_the_pairing_page(tmp_path: Path) -> None:
    """Forgotten from the PC's page, its cookie opens nothing any more."""
    app = _app(tmp_path)
    token, _header = _pair(app)
    listed = json.loads(_ask(app, _pc(PHONES_PATH)).body)["phones"]
    assert [phone["name"] for phone in listed] == ["Android"]
    answer = _ask(app, _pc(FORGET_PATH, {"id": listed[0]["id"]}))
    assert answer.status is HTTPStatus.OK
    assert json.loads(answer.body) == {"phones": []}
    assert _ask(app, _phone("/", token)).status is HTTPStatus.UNAUTHORIZED


def test_only_the_pc_lists_or_forgets_phones(tmp_path: Path) -> None:
    """A paired phone may neither list the phones nor forget one."""
    app = _app(tmp_path)
    token, _header = _pair(app)
    assert _ask(app, _phone(PHONES_PATH, token)).status is HTTPStatus.FORBIDDEN
    assert _ask(app, _pc(FORGET_PATH, {})).status is HTTPStatus.BAD_REQUEST
    card = json.loads(_ask(app, _pc(LAN_PATH)).body)
    assert (card["phones"], card["forget"]) == (PHONES_PATH, FORGET_PATH)


def test_plain_http_pairs_for_this_run_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without HTTPS no file: the cookie of the run, as before."""
    monkeypatch.setenv("MEDIA_HYGIENE_LAN_DIR", str(tmp_path))
    assert phone_book(secure=False) is None
    assert phone_book(secure=True) is not None
    lan = LanAccess(_ADDRESS, _PORT, b"a" * 32)
    app = LanApp(_Home(), lan, b"")
    _token, header = _pair(app)
    assert "Max-Age" not in header
    assert not (tmp_path / PHONES_FILE).exists()
