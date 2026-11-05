"""`POST /api/favourites`: the home page's starred actions, saved then read back (0484).

JSON only, from the page itself (`refused_post`); the loopback `Host` is checked by the
server, and a paired phone never reaches it (`lan_paths`: not in its list). The answer
is the list `config.toml` holds once written.
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from functools import partial
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.cli.home_favourites import MOST, save_favourites
from media_hygiene.i18n import _
from media_hygiene.review.http import Response
from media_hygiene.review.serving import json_response, refused_post

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pathlib import Path

    from media_hygiene.review.http import Request

_LOGGER: Final = logging.getLogger(__name__)
_NAME: Final = re.compile(r"[a-z0-9-]{1,40}")  # an action's name in the catalog


class _Starred(BaseModel):
    """The whole list, in its order."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    names: tuple[str, ...] = Field(max_length=MOST)


@dataclass(frozen=True, slots=True)
class SavedList:
    """A list of `[home]` the page sends whole: how to save it, what to say if not."""

    save: Callable[[Sequence[str]], tuple[str, ...]]
    answer_key: str
    unwritable: Callable[[], str]
    unreadable: Callable[[], str]


async def favourites_response(config_file: Path, request: Request) -> Response:
    """Save the starred actions and answer what the file now holds.

    Args:
        config_file: `config.toml`.
        request: `POST /api/favourites`, `{"names": [...]}`.

    Returns:
        `{"favourites": [...]}`, as `saved_list_response`.
    """
    kind = SavedList(
        partial(save_favourites, config_file),
        "favourites",
        lambda: _("config.toml cannot be written: the favourites were not saved."),
        lambda: _(
            "config.toml cannot be read (a mistake in the file?):"
            " the favourites were not saved."
        ),
    )
    return await saved_list_response(kind, request)


async def saved_list_response(kind: SavedList, request: Request) -> Response:
    """Save a list of words and answer what the file now holds.

    Args:
        kind: The list.
        request: The `POST`, `{"names": [...]}`.

    Returns:
        The list read back from the disk; 400 on a bad body, 500 (which case, never a
        trace; the exception goes to the log) when the save fails.
    """
    refused = refused_post(request)
    if refused is not None:
        return refused
    try:
        asked = _Starred.model_validate_json(request.body)
    except ValidationError:
        return Response(HTTPStatus.BAD_REQUEST)
    names = tuple(name for name in asked.names if _valid(name))
    try:
        saved = await asyncio.to_thread(kind.save, names)
    except OSError:
        _LOGGER.exception("%s: not saved", kind.answer_key)
        return json_response(
            HTTPStatus.INTERNAL_SERVER_ERROR, {"error": kind.unwritable()}
        )
    except ValueError:  # its TOML, its encoding, a `home` that is not a table
        _LOGGER.exception("%s: not saved", kind.answer_key)
        return json_response(
            HTTPStatus.INTERNAL_SERVER_ERROR, {"error": kind.unreadable()}
        )
    return json_response(HTTPStatus.OK, {kind.answer_key: list(saved)})


def _valid(name: str) -> bool:
    """Whether a name can be an action's.

    Args:
        name: The name sent.

    Returns:
        True for lowercase words and dashes.
    """
    return _NAME.fullmatch(name) is not None
