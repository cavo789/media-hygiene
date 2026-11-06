"""The chain after an import, followed and run again from the home page (0604).

`GET /api/import-chain` reads `import-chain.json` from the disk, what `mh.ps1` wrote;
`POST` (`from`: a step of that chain) hands `mh import --chain --from-step <step>` to
the `mh` beside the server, like any console step: its questions stay in its window.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.config.import_settings import ImportStep
from media_hygiene.i18n import _
from media_hygiene.review.http import Response
from media_hygiene.review.serving import json_response, refused_write
from media_hygiene.review.step_watch import keep_step
from media_hygiene.services.import_chain import (
    CHAIN_FLAG,
    FROM_FLAG,
    ChainState,
    ImportChain,
    read_chain,
)

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.review.http import Request

IMPORT_CHAIN_PATH: Final = "/api/import-chain"


@dataclass(frozen=True, slots=True)
class ChainDoor:
    """What the route needs."""

    file: Path  # `import-chain.json`
    reports_dir: Path
    runs: bool  # an `mh` keeps the server up and runs a console step beside it


class _Asked(BaseModel):
    """`POST /api/import-chain`: the step to start from."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    from_step: ImportStep = Field(alias="from")


def _words(step: str) -> tuple[str, str, str, str]:
    """The command running a chain from a step.

    Args:
        step: The step.

    Returns:
        Its words, without `mh`.
    """
    return ("import", CHAIN_FLAG, FROM_FLAG, step)


def _command(step: str) -> str:
    """The command as the page shows it.

    Args:
        step: The step.

    Returns:
        The line to type.
    """
    return "mh " + " ".join(_words(step))


def _said(door: ChainDoor, chain: ImportChain | None) -> dict[str, object]:
    """What the page reads.

    Args:
        door: Whether `mh` runs it.
        chain: The chain, if any.

    Returns:
        The chain, whether a button may run it, and the line to type.
    """
    return {
        "chain": None if chain is None else chain.model_dump(mode="json"),
        "runs": door.runs,
        "command": "" if chain is None else _command(chain.at.value),
    }


async def import_chain_route(door: ChainDoor, request: Request) -> Response:
    """`/api/import-chain`: `GET` where the chain is, `POST` run it from a step.

    Args:
        door: The files, and whether `mh` runs a step.
        request: The request.

    Returns:
        The chain read back, or the step handed over; 400 on a bad body, 405 for
        another method, 409 when it cannot run now.
    """
    chain = await asyncio.to_thread(read_chain, door.file)
    if request.method == "GET":
        return json_response(HTTPStatus.OK, _said(door, chain))
    refused = refused_write(request)
    if refused is not None:
        return refused
    try:
        step = _Asked.model_validate_json(request.body).from_step
    except ValidationError:
        return Response(HTTPStatus.BAD_REQUEST)
    if chain is None or step not in chain.steps or not door.runs:
        message = _("This chain cannot be run from here: type the command in mh.")
        return json_response(HTTPStatus.CONFLICT, {"error": message})
    if chain.state is ChainState.RUNNING:
        message = _("The steps of this import are running: wait for their end.")
        return json_response(HTTPStatus.CONFLICT, {"error": message})
    return await keep_step(door.reports_dir, _words(step.value), _command(step.value))
