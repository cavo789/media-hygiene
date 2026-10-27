"""The home page as an app on the phone: manifest, icons, worker, offline page (0432).

Under HTTPS (0430) a phone may install the home page: Chrome needs a manifest with
icons and a service worker; iOS reads the `apple-*` tags of the page. These answers
hold no photo and nothing of the user: the home network's door serves them before
pairing (the browser fetches a manifest without its cookie). The service worker keeps
only the offline page and its meerkat, never a photo nor an API answer (the phone stays
read-only); when Media Hygiene is not running, it shows that page instead of the
browser's error.
"""

from __future__ import annotations

import io
import json
from functools import cache
from http import HTTPStatus
from importlib import resources
from typing import Final

from PIL import Image

from media_hygiene.i18n import _
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.review.http import ContentType, Response

MANIFEST_PATH: Final = "/manifest.webmanifest"
WORKER_PATH: Final = "/sw.js"
OFFLINE_PATH: Final = "/offline"
OFFLINE_IMAGE: Final = "/offline-meerkat.webp"
ICON_PATH: Final = "/app-icon-{size}.png"
ICON_SIZES: Final = (192, 512)  # what Chrome asks of an installable app
SPLASH_IMAGE: Final = "meerkat-splash.webp"
ASLEEP_IMAGE: Final = "meerkat-asleep.webp"
BACKGROUND: Final = "#f3f6fa"  # the splash's background, as the page's light theme
RETRY_SECONDS: Final = 5
_ICONS: Final = {ICON_PATH.format(size=size): size for size in ICON_SIZES}
SHELL_PATHS: Final = frozenset(
    {MANIFEST_PATH, WORKER_PATH, OFFLINE_PATH, OFFLINE_IMAGE, *_ICONS}
)
_IMAGES: Final = "media_hygiene.assets.images"
_PACKAGE: Final = "media_hygiene.review"


def _image(name: str) -> bytes:
    """A picture of the package's assets.

    Args:
        name: Its file name.

    Returns:
        Its bytes.
    """
    return resources.files(_IMAGES).joinpath(name).read_bytes()


@cache
def icon(size: int) -> bytes:
    """The app's icon: the splash meerkat, square, as PNG.

    Args:
        size: Its side, in pixels.

    Returns:
        The PNG.
    """
    with Image.open(io.BytesIO(_image(SPLASH_IMAGE))) as picture:
        square = picture.convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    square.save(buffer, "PNG", optimize=True)
    return buffer.getvalue()


def manifest() -> bytes:
    """The web app manifest: the name, the meerkat, standalone, the home page.

    Returns:
        Its JSON.
    """
    icons = [
        {"src": path, "sizes": f"{size}x{size}", "type": ContentType.PNG.value}
        for path, size in _ICONS.items()
    ]
    name = _("Media Hygiene")
    content = {
        "name": name,
        "short_name": name,
        "description": _("Your photos and videos, sorted and without duplicates."),
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "background_color": BACKGROUND,
        "theme_color": BACKGROUND,
        "icons": icons,
    }
    return json.dumps(content, ensure_ascii=False).encode()


def _render(template: str) -> bytes:
    """Draw a template of the app's shell.

    Args:
        template: Its file name.

    Returns:
        The text, encoded.
    """
    environment = translated_environment(_PACKAGE, escaped=("html", "j2"))
    page = environment.get_template(template).render(
        offline=OFFLINE_PATH, image=OFFLINE_IMAGE, retry=RETRY_SECONDS * 1000
    )
    return page.encode()


def shell_response(path: str) -> Response | None:
    """Answer a path of the app's shell.

    Args:
        path: The request's path.

    Returns:
        The response; None for any other path.
    """
    if path == MANIFEST_PATH:
        return Response(HTTPStatus.OK, manifest(), ContentType.MANIFEST)
    if path == WORKER_PATH:
        return Response(
            HTTPStatus.OK, _render("app_worker.js.j2"), ContentType.JAVASCRIPT
        )
    if path == OFFLINE_PATH:
        return Response(HTTPStatus.OK, _render("app_offline.html.j2"), ContentType.HTML)
    if path == OFFLINE_IMAGE:
        return Response(HTTPStatus.OK, _image(ASLEEP_IMAGE), ContentType.WEBP)
    size = _ICONS.get(path)
    return (
        None if size is None else Response(HTTPStatus.OK, icon(size), ContentType.PNG)
    )
