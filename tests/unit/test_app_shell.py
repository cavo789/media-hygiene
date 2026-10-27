"""The home page as an app on the phone: manifest, icons, worker, offline page (0432).

What Chrome and iOS need to install it, served before pairing and holding nothing
private; a worker that keeps the offline page and its meerkat only; the same splash on
the PC's page and the phone's.
"""

from __future__ import annotations

import asyncio
import io
import json
import re
from http import HTTPStatus
from typing import Final

import pytest
from PIL import Image

from media_hygiene.review.app_shell import (
    ICON_PATH,
    ICON_SIZES,
    MANIFEST_PATH,
    OFFLINE_IMAGE,
    OFFLINE_PATH,
    SHELL_PATHS,
    WORKER_PATH,
    shell_response,
)
from media_hygiene.review.doors import Door
from media_hygiene.review.http import REVIEW_POLICY, ContentType, Request, Response
from media_hygiene.review.lan import LanAccess
from media_hygiene.review.lan_app import LanApp
from media_hygiene.services.home import home_page

_ADDRESS: Final = "192.168.1.20"
_PORT: Final = 8088


class _Home:
    """Stands for the home page."""

    async def handle(self, _request: Request) -> Response:
        """Answer 200.

        Returns:
            An empty page.
        """
        return Response(HTTPStatus.OK, b"home")


def _served(path: str) -> Response:
    answer = shell_response(path)
    assert answer is not None
    assert answer.status is HTTPStatus.OK
    return answer


def test_the_manifest_names_the_product_and_opens_the_home_page() -> None:
    """Name, standalone, start at `/`, and the icons it lists are served."""
    answer = _served(MANIFEST_PATH)
    assert answer.content_type is ContentType.MANIFEST
    content = json.loads(answer.body)
    assert content["name"] == "Media Hygiene"
    assert (content["display"], content["start_url"]) == ("standalone", "/")
    assert content["background_color"]
    for listed in content["icons"]:
        assert _served(listed["src"]).content_type is ContentType.PNG


@pytest.mark.parametrize("size", ICON_SIZES)
def test_each_icon_is_a_square_png_of_its_size(size: int) -> None:
    """The meerkat at the sizes Chrome asks for."""
    body = _served(ICON_PATH.format(size=size)).body
    with Image.open(io.BytesIO(body)) as picture:
        assert (picture.format, picture.size) == ("PNG", (size, size))


def test_the_worker_keeps_the_offline_page_and_its_meerkat_only() -> None:
    """Never a photo nor an API answer: one `addAll` of those two."""
    answer = _served(WORKER_PATH)
    assert answer.content_type is ContentType.JAVASCRIPT
    script = answer.body.decode()
    assert re.findall(r"addAll\(\[(.*?)\]\)", script) == ["OFFLINE, IMAGE"]
    assert json.dumps(OFFLINE_PATH) in script
    assert json.dumps(OFFLINE_IMAGE) in script
    assert script.count("cache.put") == 0


def test_the_offline_page_shows_the_asleep_meerkat_and_retries() -> None:
    """The product's name, the meerkat, Retry."""
    page = _served(OFFLINE_PATH).body.decode()
    assert "Media Hygiene is asleep" in page
    assert f'src="{OFFLINE_IMAGE}"' in page
    assert 'id="retry"' in page
    assert _served(OFFLINE_IMAGE).content_type is ContentType.WEBP


def test_the_shell_is_served_before_pairing_and_the_page_is_not() -> None:
    """The browser fetches the manifest without its cookie; the page stays closed."""
    app = LanApp(_Home(), LanAccess(_ADDRESS, _PORT, b"a" * 32, secure=True), b"")
    host = {"host": f"{_ADDRESS}:{_PORT}"}
    for path in SHELL_PATHS:
        answer = asyncio.run(app.handle(Request("GET", path, host, b"", Door.LAN)))
        assert answer.status is HTTPStatus.OK, path
    home = asyncio.run(app.handle(Request("GET", "/", host, b"", Door.LAN)))
    assert home.status is HTTPStatus.UNAUTHORIZED
    assert shell_response("/api/state") is None


def test_the_policy_lets_the_manifest_and_the_worker_load() -> None:
    """`default-src 'none'` would block both."""
    assert "manifest-src 'self'" in REVIEW_POLICY
    assert "worker-src 'self'" in REVIEW_POLICY


def test_the_phone_page_links_the_app_and_both_share_the_splash() -> None:
    """The tags name the shell's paths; the startup screen is the same file."""
    phone = home_page(remote=True).decode()
    pc = home_page().decode()
    assert f'rel="manifest" href="{MANIFEST_PATH}"' in phone
    assert f'href="{ICON_PATH.format(size=ICON_SIZES[0])}"' in phone
    assert f'register("{WORKER_PATH}")' in phone
    assert 'rel="manifest"' not in pc

    def splash(page: str) -> str:
        return page[page.index('<div class="loading"') : page.index('<a class="skip"')]

    assert splash(phone) == splash(pc)
    assert "meerkat-splash.webp" in splash(pc)
