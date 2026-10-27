"""The home network's door in HTTPS: the PC's authority, its certificates (0430).

The authority made once and kept, the server certificate issued for the address and
issued again only when it changes, a real TLS handshake trusting the authority alone,
the plain HTTP door (the steps, `ca.crt`, never `ca.key`, everything else on to HTTPS),
the access in HTTPS (origin, `Secure` cookie, the card's `ca` line), and `mh --lan`
mounting `/lan` for the home page only.
"""

from __future__ import annotations

import asyncio
import json
import re
import ssl
from dataclasses import replace
from http import HTTPStatus
from pathlib import Path
from typing import Final

import pytest

from media_hygiene.paths.docker_run import Shell
from media_hygiene.paths.mounts import MountTable
from media_hygiene.review.doors import LAN_CA_DOOR_PORT, LAN_CA_PORT
from media_hygiene.review.http import Request
from media_hygiene.review.lan import LAN_SECRET_VARIABLE, LanAccess, lan_access
from media_hygiene.review.lan_address import LAN_ADDRESS_VARIABLE
from media_hygiene.review.lan_ca_page import CA_DOWNLOAD, CaDoor
from media_hygiene.review.lan_card import CA_DOC, lan_response
from media_hygiene.review.lan_pairing import Pairing
from media_hygiene.review.lan_tls import (
    CA_CERT,
    CA_KEY,
    SERVER_CERT,
    certificates,
    lan_folder,
    secure_door,
    server_context,
)
from media_hygiene.services.launcher import (
    LauncherCommands,
    launcher_script,
    render_script,
)
from tests.support.runtime import make_locations, make_runtime

_ADDRESS: Final = "192.168.1.20"
_OTHER: Final = "192.168.1.42"
_PORT: Final = 8088
_SECURE: Final = f"https://{_ADDRESS}:{_PORT}"
_LAN_DIR: Final = "MEDIA_HYGIENE_LAN_DIR"


def _get(door: CaDoor, path: str, method: str = "GET") -> tuple[HTTPStatus, bytes, str]:
    request = Request(method, path, {"host": f"{_ADDRESS}:{LAN_CA_PORT}"}, b"")
    answer = asyncio.run(door.handle(request))
    location = next((h for h in answer.headers if h.startswith("Location:")), "")
    return answer.status, answer.body, location


def test_the_authority_is_made_once_and_the_server_names_the_address(
    tmp_path: Path,
) -> None:
    """The authority is kept; only the server certificate follows the address."""
    assert certificates(tmp_path, _ADDRESS)
    authority = (tmp_path / CA_CERT).read_bytes()
    first = (tmp_path / SERVER_CERT).read_bytes()
    assert (tmp_path / CA_KEY).stat().st_mode & 0o077 == 0
    assert certificates(tmp_path, _ADDRESS)
    assert (tmp_path / SERVER_CERT).read_bytes() == first  # same address: kept
    assert certificates(tmp_path, _OTHER)
    assert (tmp_path / CA_CERT).read_bytes() == authority  # phones keep trusting it
    assert (tmp_path / SERVER_CERT).read_bytes() != first


def test_a_folder_that_cannot_hold_them_keeps_plain_http(tmp_path: Path) -> None:
    """Without the folder, no certificate: the door stays plain HTTP."""
    assert not certificates(tmp_path / "missing", _ADDRESS)


def test_a_phone_trusting_the_authority_completes_the_handshake(
    tmp_path: Path,
) -> None:
    """A client trusting the authority alone opens the HTTPS door."""
    loopback = "127.0.0.1"
    assert certificates(tmp_path, loopback)
    client = ssl.create_default_context(cafile=tmp_path / CA_CERT)

    async def handshake() -> bytes:
        async def answer(
            _reader: asyncio.StreamReader, writer: asyncio.StreamWriter
        ) -> None:
            writer.write(b"ok")
            await writer.drain()
            writer.close()

        server = await asyncio.start_server(
            answer, loopback, 0, ssl=server_context(tmp_path)
        )
        async with server:
            port = server.sockets[0].getsockname()[1]
            reader, writer = await asyncio.open_connection(
                loopback, port, ssl=client, server_hostname=loopback
            )
            said = await reader.read()
            writer.close()
            return said

    assert asyncio.run(handshake()) == b"ok"


def test_the_folder_is_taken_only_when_mounted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`/lan` is used only when it is a folder to write to."""
    monkeypatch.setenv(_LAN_DIR, str(tmp_path / "missing"))
    assert lan_folder() is None
    assert secure_door(_ADDRESS) is None
    monkeypatch.setenv(_LAN_DIR, str(tmp_path))
    assert lan_folder() == tmp_path
    assert secure_door(_ADDRESS) is not None


def test_the_plain_door_hands_out_the_authority_only(tmp_path: Path) -> None:
    """The steps and `ca.crt`; never `ca.key`; the rest goes on to HTTPS."""
    assert certificates(tmp_path, _ADDRESS)
    door = CaDoor(tmp_path, _SECURE)
    status, body, _location = _get(door, CA_DOWNLOAD)
    assert status is HTTPStatus.OK
    assert body == (tmp_path / CA_CERT).read_bytes()
    status, body, _location = _get(door, "/")
    assert status is HTTPStatus.OK
    assert CA_DOWNLOAD.encode() in body
    assert f"{_SECURE}/".encode() in body
    key = (tmp_path / CA_KEY).read_bytes()
    for path in (f"/{CA_KEY}", "/pair/01234567", "/api/state"):
        status, body, location = _get(door, path)
        assert status is HTTPStatus.SEE_OTHER
        assert location == f"Location: {_SECURE}{path}"
        assert key not in body
    assert _get(door, "/", "POST")[0] is HTTPStatus.METHOD_NOT_ALLOWED


def test_the_access_is_https_with_the_certificates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The access is HTTPS with `/lan` mounted, plain HTTP without it."""
    monkeypatch.setenv(LAN_ADDRESS_VARIABLE, _ADDRESS)
    monkeypatch.setenv(LAN_SECRET_VARIABLE, "s" * 64)
    monkeypatch.setenv(_LAN_DIR, str(tmp_path / "missing"))
    plain = lan_access(_PORT)
    assert plain is not None
    assert not plain.secure
    assert plain.origin == f"http://{_ADDRESS}:{_PORT}"
    monkeypatch.setenv(_LAN_DIR, str(tmp_path))
    secure = lan_access(_PORT)
    assert secure is not None
    assert secure.secure
    assert secure.origin == _SECURE
    assert secure.pair_url.startswith(f"{_SECURE}/pair/")


@pytest.mark.parametrize("secure", [True, False])
def test_the_cookie_and_the_card_follow_https(*, secure: bool) -> None:
    """The cookie is `Secure` and the card names the certificate under HTTPS."""
    lan = LanAccess(_ADDRESS, _PORT, b"x" * 32, secure=secure)
    answer = Pairing().check(lan, lan.code)
    cookie = next(h for h in answer.headers if h.startswith("Set-Cookie:"))
    assert cookie.endswith("; Secure") is secure
    card = json.loads(lan_response(lan).body)
    assert card.get("ca") == (f"http://{_ADDRESS}:{LAN_CA_PORT}/" if secure else None)
    assert ("caHelp" in card) is secure


@pytest.mark.parametrize(
    ("language", "heading"),
    [
        ("en", "### Once per phone: install the certificate"),
        ("fr", "### Une fois par téléphone : installer le certificat"),
    ],
)
def test_the_card_links_the_steps_of_the_docs(language: str, heading: str) -> None:
    """The anchor of `CA_DOC` is the heading of each language (GitHub's slug)."""
    page = Path("documentation", language, "commands", "home.md").read_text("utf-8")
    assert heading in page
    title = heading.removeprefix("### ").lower()
    slug = "#" + re.sub(r"[^\w\- ]", "", title).replace(" ", "-")
    assert slug == (CA_DOC.en if language == "en" else CA_DOC.fr)


def test_mh_lan_mounts_the_certificates_for_the_home_page_only(
    tmp_path: Path,
) -> None:
    """`mh --lan` mounts `/lan` for the home page, never the slideshow."""
    runtime = replace(
        make_runtime(make_locations(tmp_path)), mounts=MountTable(frozenset())
    )
    commands = LauncherCommands(("audit", "home"), (), ("home",), (), _PORT)
    script = render_script(launcher_script(runtime, Shell.POWERSHELL, commands))
    mount = r'''-v', "$HOME\media-hygiene\lan:/lan"'''
    assert mount in script
    assert f":{LAN_CA_PORT}:{LAN_CA_DOOR_PORT}" in script
    guarded = script[script.index("if ($command -eq 'home') {") :]
    assert guarded.index(mount) < guarded.index("}")
