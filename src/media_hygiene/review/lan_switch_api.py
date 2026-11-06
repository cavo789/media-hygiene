"""`[review] lan` and `lan_phone_originals` as switches on the home page (0605).

`GET /api/lan-switch` reads both from `config.toml` on the disk; `POST` writes them with
`toml_edit` (comments kept, atomic), then reads them back: the page shows what the file
holds, never what it sent. A change applies at the next start of `mh`, which the answer
says (the running server keeps the door it opened).
"""

from __future__ import annotations

import asyncio
import json
import tomllib
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, ValidationError

from media_hygiene.config.review_settings import ReviewSettings
from media_hygiene.i18n import _
from media_hygiene.places.toml_edit import (
    document_of,
    loaded,
    table_of,
    write_document,
)
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.serving import json_response, refused_post

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.review.http import Request

LAN_SWITCH_PATH: Final = "/api/lan-switch"
_TABLE: Final = "review"
_LAN: Final = "lan"
_ORIGINALS: Final = "lan_phone_originals"
_DEFAULTS: Final = ReviewSettings()


class LanSwitchAsked(BaseModel):
    """`POST /api/lan-switch`: the two switches."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    lan: bool
    originals: bool


def switch_of(config_file: Path) -> dict[str, bool]:
    """Both switches as the file holds them, read from the disk.

    Args:
        config_file: `config.toml`; missing, unreadable or odd values: the defaults.

    Returns:
        `lan` and `originals`.
    """
    try:
        table: dict[str, object] = dict(loaded(config_file).get(_TABLE, {}))
    except OSError, tomllib.TOMLDecodeError, TypeError, ValueError:
        table = {}
    lan, originals = table.get(_LAN), table.get(_ORIGINALS)
    return {
        "lan": lan if isinstance(lan, bool) else _DEFAULTS.lan,
        "originals": (
            originals if isinstance(originals, bool) else _DEFAULTS.lan_phone_originals
        ),
    }


def saved_switch(config_file: Path, asked: LanSwitchAsked) -> dict[str, bool]:
    """Write both switches, then read them back.

    Args:
        config_file: `config.toml`.
        asked: What the page sent.

    Returns:
        The switches the file now holds.
    """
    document = document_of(config_file)
    table = table_of(document, _TABLE)
    table[_LAN] = asked.lan
    table[_ORIGINALS] = asked.originals
    write_document(config_file, document)
    return switch_of(config_file)


async def lan_switch_route(config_file: Path, request: Request) -> Response:
    """`/api/lan-switch`: `GET` reads the switches, `POST` changes them.

    Args:
        config_file: `config.toml`.
        request: The request.

    Returns:
        The switches read back and the line saying when they apply; 400 on a bad
        body, 405 for another method, 500 when the file cannot be written.
    """
    if request.method == "GET":
        body = {"lan": await asyncio.to_thread(switch_of, config_file)}
        return Response(HTTPStatus.OK, json.dumps(body).encode(), ContentType.JSON)
    if request.method != "POST":
        return Response(HTTPStatus.METHOD_NOT_ALLOWED)
    if (refused := refused_post(request)) is not None:
        return refused
    try:
        asked = LanSwitchAsked.model_validate_json(request.body)
    except ValidationError:
        return json_response(HTTPStatus.BAD_REQUEST, {"error": _("Bad request.")})
    try:
        held = await asyncio.to_thread(saved_switch, config_file, asked)
    except OSError, ValueError:
        message = _("The settings could not be saved in config.toml.")
        return json_response(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": message})
    later = _("Applies the next time mh starts: the open page keeps its door.")
    return json_response(HTTPStatus.OK, {"lan": held, "later": later})
