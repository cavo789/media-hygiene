"""The steps after an import, shown and switched from the home page (0481, 0538).

`[imports] then` of `config.toml`: `GET /api/import-steps` reads it from the disk;
`POST /api/import-steps` writes the steps ticked with `toml_edit` (comments kept,
atomic), then reads them back: the page shows what the file holds, never what it
sent. `ImportSettings` puts them in the chain's order and adds the audit when
another step is on.
"""

from __future__ import annotations

import asyncio
import tomllib
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

import tomlkit
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.config.import_settings import ImportSettings, ImportStep
from media_hygiene.i18n import _
from media_hygiene.places.toml_edit import (
    document_of,
    loaded,
    table_of,
    write_document,
)
from media_hygiene.review.http import Response
from media_hygiene.review.serving import json_response, refused_write

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.review.http import Request

IMPORT_STEPS_PATH: Final = "/api/import-steps"
_TABLE: Final = "imports"
_THEN: Final = "then"


class StepsAsked(BaseModel):
    """`POST /api/import-steps`: the steps ticked (none: nothing after the copies)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    steps: tuple[ImportStep, ...] = Field(default=(), max_length=len(ImportStep))


def steps_of(config_file: Path) -> list[str]:
    """The steps the file runs after an import, read from the disk.

    Args:
        config_file: `config.toml`; missing or unreadable: the default steps.

    Returns:
        The steps, in the chain's order.
    """
    try:
        table = dict(loaded(config_file).get(_TABLE, {}))
    except OSError, tomllib.TOMLDecodeError:
        table = {}
    try:
        settings = ImportSettings.model_validate(table)
    except ValidationError:
        settings = ImportSettings()
    return [str(step) for step in settings.then]


def saved_steps(config_file: Path, asked: StepsAsked) -> list[str]:
    """Write the steps ticked, then read them back from the disk.

    Args:
        config_file: `config.toml`.
        asked: What the page sent.

    Returns:
        The steps the file now holds.
    """
    steps = ImportSettings(then=asked.steps).then
    document = document_of(config_file)
    array = tomlkit.array()
    array.extend(str(step) for step in steps)
    table_of(document, _TABLE)[_THEN] = array
    write_document(config_file, document)
    return steps_of(config_file)


async def import_steps_route(config_file: Path, request: Request) -> Response:
    """`/api/import-steps`: `GET` reads the steps, `POST` changes them.

    Args:
        config_file: `config.toml`.
        request: The request.

    Returns:
        The steps read back; 400 on a bad body, 405 for another method, 500 when
        the file cannot be written.
    """
    if request.method == "GET":
        steps = await asyncio.to_thread(steps_of, config_file)
        return json_response(HTTPStatus.OK, {"steps": steps})
    refused = refused_write(request)
    if refused is not None:
        return refused
    try:
        asked = StepsAsked.model_validate_json(request.body)
    except ValidationError:
        return Response(HTTPStatus.BAD_REQUEST)
    try:
        steps = await asyncio.to_thread(saved_steps, config_file, asked)
    except OSError:
        message = _("The settings could not be saved in config.toml.")
        return json_response(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": message})
    return json_response(HTTPStatus.OK, {"steps": steps})
