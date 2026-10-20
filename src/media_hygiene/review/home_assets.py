"""`GET /assets/<path>`: the home page's images and fonts, inside the image.

Only the files of `media_hygiene/assets/` are served, with the type of their
extension; a path leaving that folder (`../`), or an unknown extension, is 404. They
change only with the image: the browser keeps them a day without asking.
"""

from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
from types import MappingProxyType
from typing import Final
from urllib.parse import unquote

from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.report_files import read_found

ASSETS_PREFIX: Final = "/assets/"
ASSETS_DIR: Final = Path(__file__).resolve().parents[1] / "assets"
MAX_AGE_S: Final = 24 * 60 * 60
_SERVED: Final = MappingProxyType(
    {
        ".webp": ContentType.WEBP,
        ".png": ContentType.PNG,
        ".woff2": ContentType.WOFF2,
        ".txt": ContentType.TEXT,
    }
)


def asset_file(path: str, root: Path = ASSETS_DIR) -> Path | None:
    """Find the file an `/assets/…` path names, inside the assets folder only.

    Args:
        path: The path asked for.
        root: The assets folder (another one in tests).

    Returns:
        The file; None outside the folder, missing, or of a type not served.
    """
    base = root.resolve()
    target = (base / unquote(path.removeprefix(ASSETS_PREFIX))).resolve()
    if not target.is_relative_to(base) or not target.is_file():
        return None
    return target if target.suffix.lower() in _SERVED else None


async def asset_response(path: str) -> Response:
    """Serve an image or a font of the home page.

    Args:
        path: The path asked for.

    Returns:
        The file, kept a day by the browser; 404 otherwise.
    """
    target = asset_file(path)
    body = await read_found(target)
    if target is None or body is None:
        return Response(HTTPStatus.NOT_FOUND)
    kind = _SERVED[target.suffix.lower()]
    return Response(HTTPStatus.OK, body, kind, max_age=MAX_AGE_S)
