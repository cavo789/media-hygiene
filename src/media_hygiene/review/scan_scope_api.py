"""What the audit analyses and ignores, shown and changed from the home page (0535).

`[scan] extensions` (the categories `photo`, `raw`, `video`, or extensions) and
`excluded_names` (folder names skipped wherever they are) of `config.toml`.
`GET /api/scan-scope` reads them from the disk; `POST /api/scan-scope` writes the
categories ticked and the names, with `toml_edit` (comments kept, atomic), then reads
them back: the page shows what the file holds, never what it sent. Extensions the
user wrote by hand (`.jpg`) are kept as they are. Every kind ticked writes no
extension at all: every media file, as by default. A change makes the last audit's
proposals stale: the answer says so, for the page to offer the audit again.
"""

from __future__ import annotations

import asyncio
import json
import tomllib
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, Literal

import tomlkit
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.config.scan_settings import ScanSettings
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

SCOPE_PATH: Final = "/api/scan-scope"
KINDS: Final = ("photo", "raw", "video")
_TABLE: Final = "scan"
_EXTENSIONS: Final = "extensions"
_NAMES: Final = "excluded_names"
_MOST_NAMES: Final = 200
_MAX_NAME: Final = 255
type Kind = Literal["photo", "raw", "video"]


class ScopeAsked(BaseModel):
    """`POST /api/scan-scope`: the kinds analysed and the folder names ignored."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    kinds: tuple[Kind, ...] = Field(min_length=1, max_length=len(KINDS))
    names: tuple[str, ...] = Field(default=(), max_length=_MOST_NAMES)


def scope_of(config_file: Path) -> dict[str, list[str]]:
    """What the file asks the audit to analyse and to ignore, read from the disk.

    Args:
        config_file: `config.toml`; missing: everything analysed, nothing ignored.

    Returns:
        `kinds` ticked, `others` (extensions written by hand) and `names` ignored.
    """
    try:
        table: dict[str, object] = dict(loaded(config_file).get(_TABLE, {}))
    except OSError, tomllib.TOMLDecodeError:
        table = {}
    asked = [str(value) for value in _listed(table.get(_EXTENSIONS))]
    names = [str(value) for value in _listed(table.get(_NAMES))]
    if not asked or "media" in asked:
        return {"kinds": list(map(str, KINDS)), "others": [], "names": names}
    kinds: list[str] = [kind for kind in KINDS if kind in asked]
    others = [value for value in asked if value not in KINDS]
    return {"kinds": kinds, "others": others, "names": names}


def _listed(value: object) -> list[object]:
    """A TOML value as a list: a string is one item, anything else none.

    Args:
        value: What the key holds.

    Returns:
        The items.
    """
    if isinstance(value, list):
        return value
    return [value] if isinstance(value, str) else []


def saved_scope(config_file: Path, asked: ScopeAsked) -> dict[str, list[str]]:
    """Write the kinds and the names, then read them back from the disk.

    Args:
        config_file: `config.toml`.
        asked: What the page sent.

    Returns:
        The scope the file now holds.

    Raises:
        ValueError: The names or extensions are not valid settings (file unchanged).
    """
    others = scope_of(config_file)["others"]
    every = set(asked.kinds) == set(KINDS)
    extensions = [] if every else [*dict.fromkeys(asked.kinds), *others]
    names = [name.strip() for name in asked.names if name.strip()]
    try:
        ScanSettings.model_validate({_EXTENSIONS: extensions, _NAMES: names})
    except ValidationError as exc:
        reason = "; ".join(str(error["msg"]) for error in exc.errors())
        raise ValueError(reason) from exc
    document = document_of(config_file)
    table = table_of(document, _TABLE)
    if extensions or _EXTENSIONS in table:
        table[_EXTENSIONS] = _array(extensions)
    if names or _NAMES in table:
        table[_NAMES] = _array(names)
    write_document(config_file, document)
    return scope_of(config_file)


def _array(values: list[str]) -> tomlkit.items.Array:
    """Values as a TOML array, each once.

    Args:
        values: The values, in their order.

    Returns:
        The array.
    """
    array = tomlkit.array()
    array.extend(dict.fromkeys(values))
    return array


async def scope_route(config_file: Path, request: Request) -> Response:
    """`/api/scan-scope`: `GET` reads the scope, `POST` changes it.

    Args:
        config_file: `config.toml`.
        request: The request.

    Returns:
        The response; 405 for another method.
    """
    if request.method not in {"GET", "POST"}:
        return Response(HTTPStatus.METHOD_NOT_ALLOWED)
    if request.method == "GET":
        body = {"scope": await asyncio.to_thread(scope_of, config_file)}
        return Response(HTTPStatus.OK, json.dumps(body).encode(), ContentType.JSON)
    return await scope_response(config_file, request)


async def scope_response(config_file: Path, request: Request) -> Response:
    """`POST /api/scan-scope`: save the scope and answer what the file holds.

    Args:
        config_file: `config.toml`.
        request: `{"kinds": [...], "names": [...]}`.

    Returns:
        The scope read back and the stale audit's line; 400 on a bad body, 409 (the
        file unchanged) on invalid names, 500 when the file cannot be written.
    """
    refused = refused_post(request)
    if refused is not None:
        return refused
    try:
        asked = ScopeAsked.model_validate_json(request.body)
    except ValidationError:
        message = _("Tick at least one kind of file to analyse.")
        return json_response(HTTPStatus.BAD_REQUEST, {"error": message})
    try:
        scope = await asyncio.to_thread(saved_scope, config_file, asked)
    except ValueError as exc:
        return json_response(HTTPStatus.CONFLICT, {"error": str(exc)})
    except OSError:
        message = _("The settings could not be saved in config.toml.")
        return json_response(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": message})
    stale = _(
        "The last audit was made with the former settings: run the audit again "
        "before cleaning."
    )
    return json_response(HTTPStatus.OK, {"scope": scope, "stale": stale})
