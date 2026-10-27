"""Anywhere but the PC, everything is read-only (0427, 0429).

The originals behind `[review] lan_phone_originals`; never the audit started from a
phone; no route that writes in the phone's list, whatever the setting; the phone's pages
hide what writes; the PC's door published on the loopback only.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import replace
from http import HTTPStatus
from importlib.resources import files
from typing import TYPE_CHECKING, Final, override

import pytest

from media_hygiene.config.review_settings import ReviewSettings
from media_hygiene.paths.docker_run import Shell
from media_hygiene.paths.mounts import MountTable
from media_hygiene.review.doors import Door
from media_hygiene.review.ending import Ending, EndingDoor
from media_hygiene.review.http import ContentType, Request, Response
from media_hygiene.review.lan import COOKIE_NAME, LanAccess
from media_hygiene.review.lan_app import LanApp
from media_hygiene.review.lan_paths import (
    PHONE_HIDDEN,
    POST_PATHS,
    READ_PATHS,
    READ_PREFIXES,
    phone_may,
)
from media_hygiene.review.local_app import LocalApp
from media_hygiene.review.write_routes import CHANGES
from media_hygiene.services import home
from media_hygiene.services.launcher import (
    LauncherCommands,
    launcher_script,
    render_script,
)
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path

_PORT: Final = 8765
_HOST: Final = f"192.168.1.20:{_PORT}"
_ACCESS: Final = LanAccess("192.168.1.20", _PORT, b"cd" * 32)
_PAGE: Final = b'<!doctype html>\n<html lang="en"><button id="setAside">'


class _Home(LocalApp):
    """Stands for the home page: answers every request with a page."""

    __slots__ = ("seen",)

    def __init__(self) -> None:
        """Start without any request."""
        self.seen: list[str] = []

    @override
    async def answer(self, request: Request) -> Response:
        """Keep the path, answer a page of photos."""
        self.seen.append(request.path)
        return Response(HTTPStatus.OK, _PAGE, ContentType.HTML)


def _ask(app: LanApp, path: str, how: tuple[str, bool] = ("GET", True)) -> Response:
    method, paired = how
    headers = {"host": _HOST}
    if paired:
        headers["cookie"] = f"{COOKIE_NAME}={_ACCESS.token}"
    if method != "GET":
        headers |= {"content-type": "application/json", "origin": _ACCESS.origin}
    request = Request(method, path, headers, b"{}", Door.LAN)
    return asyncio.run(EndingDoor(app, Ending()).handle(request))


def _app(*, originals: bool = False) -> tuple[LanApp, _Home]:
    fake = _Home()
    return LanApp(fake, _ACCESS, b"<p>phone</p>", originals=originals), fake


def test_the_originals_are_off_by_default() -> None:
    """0427: a phone of an unknown home network gets nothing more than before."""
    assert ReviewSettings().lan_phone_originals is False
    app, fake = _app()
    assert _ask(app, "/original/1.jpg").status == HTTPStatus.FORBIDDEN
    assert not fake.seen


@pytest.mark.parametrize("name", ["1.jpg", "2.mp4"])
def test_the_setting_on_serves_an_original_photo_and_video(name: str) -> None:
    """0427: on, `/original/` passes to the home page, a read."""
    app, fake = _app(originals=True)
    assert _ask(app, f"/original/{name}").status == HTTPStatus.OK
    assert fake.seen == [f"/original/{name}"]


@pytest.mark.parametrize("originals", [False, True])
def test_a_phone_never_starts_the_audit(*, originals: bool) -> None:
    """0427: the audit follows a change made on the PC; its progress is still read."""
    app, fake = _app(originals=originals)
    reply = _ask(app, "/api/audit", ("POST", True))
    assert reply.status == HTTPStatus.FORBIDDEN
    assert b"on the PC" in reply.body
    assert not fake.seen
    assert _ask(app, "/api/audit").status == HTTPStatus.OK


@pytest.mark.parametrize("originals", [False, True])
@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE", "PATCH"])
def test_no_route_that_writes_is_in_the_phones_list(
    method: str, *, originals: bool
) -> None:
    """0429: every declared write refused, whatever `[review]` says."""
    assert not CHANGES & POST_PATHS
    for path in sorted(CHANGES):
        request = Request(method, path, {}, b"", Door.LAN)
        assert not phone_may(request, originals=originals), path


def test_a_write_added_to_the_phones_list_is_caught() -> None:
    """0429: the guard is not empty: a write in the list would be seen."""
    assert "/api/chosen" in CHANGES
    assert "/api/stop" in CHANGES
    assert "/api/apply" in CHANGES
    assert CHANGES & (POST_PATHS | {"/api/chosen"})


@pytest.mark.parametrize("path", sorted(CHANGES))
@pytest.mark.parametrize("paired", [False, True])
def test_a_curl_from_the_home_network_gets_403_on_every_write(
    path: str, *, paired: bool
) -> None:
    """0429: a real `POST` through the LAN door, with or without the cookie: 403."""
    app, fake = _app(originals=True)
    assert _ask(app, path, ("POST", paired)).status == HTTPStatus.FORBIDDEN
    assert not fake.seen


def test_the_phones_pages_hide_what_writes() -> None:
    """0429: a page of photos sent to a phone is marked; its CSS hides the writes."""
    app, _ = _app()
    for path in ("/search", "/browse"):
        body = _ask(app, path).body
        assert body.startswith(b'<!doctype html>\n<html data-phone lang="en">'), path
    pick = _read_template("pick_grid.css.j2")
    for selector in PHONE_HIDDEN:
        assert f"html[data-phone] {selector}" in pick, selector
    phone = home.home_page(remote=True).decode()
    assert "running || REMOTE" in phone  # the audit's start never shown


def test_the_reads_stay_reads() -> None:
    """0429: nothing of the phone's `GET` list is a declared write by `GET`."""
    assert all(path.startswith("/") for path in READ_PATHS)
    assert all(prefix.endswith("/") for prefix in READ_PREFIXES)


def _read_template(name: str) -> str:
    return (files("media_hygiene.review") / "templates" / name).read_text("utf-8")


_COMMANDS: Final = LauncherCommands(("audit", "home"), (), ("home",), (), _PORT)
_PS_PUBLISH: Final = re.compile(r"'-p',\s*([\"'])(.*?)\1")
_SH_PUBLISH: Final = re.compile(r'page=\(-p "([^"]*)"')


@pytest.mark.parametrize("shell", [Shell.POWERSHELL, Shell.BASH])
def test_the_pcs_door_is_published_on_the_loopback_only(
    shell: Shell, tmp_path: Path
) -> None:
    """0429: the PC's door on `127.0.0.1` only; the LAN door alone goes further."""
    runtime = replace(
        make_runtime(make_locations(tmp_path)), mounts=MountTable(frozenset())
    )
    script = render_script(launcher_script(runtime, shell, _COMMANDS))
    if shell is Shell.POWERSHELL:
        published = [match[1] for match in _PS_PUBLISH.findall(script)]
    else:
        published = _SH_PUBLISH.findall(script)
    assert published
    for host in published:
        assert host.startswith(("127.0.0.1:", "$($lan.address)")), host
    assert "0.0.0.0" not in script  # noqa: S104  # never every interface


def test_a_phones_spaces_list_only_the_pages_it_opens() -> None:
    """A phone's *Find* lists search and browse, never Excel nor a PC step."""
    phone = home.home_page(remote=True).decode()
    assert "(!REMOTE || PHONE_PAGES[BY_ID[name].command])" in phone
    assert '"mh search"' in phone
