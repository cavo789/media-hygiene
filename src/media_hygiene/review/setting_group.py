"""A few `config.toml` values saved from the page where they act (0606-0609).

`GET` reads the group from the disk; `POST` validates, writes it with `toml_edit`
(comments kept, atomic), then reads it back: the page shows what the file holds, never
what it sent. A change applies at the next start of `mh`, but a group that applies
itself (`applied`: the language, 0644).
"""

from __future__ import annotations

import asyncio
import json
import tomllib
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING

from media_hygiene.i18n import _
from media_hygiene.places.toml_edit import (
    document_of,
    loaded,
    table_of,
    write_document,
)
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.serving import json_response, refused_write

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.review.http import Request

type Held = dict[str, object]


@dataclass(frozen=True, slots=True)
class Field:
    """One value: its key, kind, bounds (numbers) or choices (text), default.

    A boolean default makes a switch: only `true` or `false` then (0747).
    """

    key: str
    default: object
    low: float = 0
    high: float = 0
    choices: tuple[str, ...] = ()
    longest: int = 200  # a text without choices

    def accepts(self, value: object) -> bool:
        """Is `value` one the settings would load?

        Args:
            value: What the file or the page holds.

        Returns:
            True when it has the kind and the bounds of the field.
        """
        if isinstance(self.default, bool) or isinstance(value, bool):
            return isinstance(self.default, bool) and isinstance(value, bool)
        if isinstance(self.default, str):
            ok = isinstance(value, str) and len(value) <= self.longest
            return ok and (not self.choices or value in self.choices)
        wanted = int if isinstance(self.default, int) else (int, float)
        return isinstance(value, wanted) and self.low <= value <= self.high


@dataclass(frozen=True, slots=True)
class SettingGroup:
    """The values of one table of `config.toml` a page changes, and the route."""

    path: str
    tables: tuple[str, ...]
    fields: tuple[Field, ...]
    # Applies the values read back at once and says so (the language, 0644); None:
    # at the next start of `mh`.
    applied: Callable[[Held], str] | None = None


def _values(config_file: Path, group: SettingGroup) -> dict[str, object]:
    """The group's table as the file holds it; empty when missing or unreadable."""
    try:
        node: object = loaded(config_file)
    except OSError, tomllib.TOMLDecodeError, ValueError:
        return {}
    for name in group.tables:
        node = node.get(name, {}) if isinstance(node, dict) else {}
    return dict(node) if isinstance(node, dict) else {}


def held(config_file: Path, group: SettingGroup) -> Held:
    """The group as the file holds it, read from the disk.

    Args:
        config_file: `config.toml`; missing, unreadable or odd values: the defaults.
        group: The values.

    Returns:
        Each key with its value.
    """
    table = _values(config_file, group)
    return {
        one.key: table[one.key] if one.accepts(table.get(one.key)) else one.default
        for one in group.fields
    }


def saved(config_file: Path, group: SettingGroup, asked: Held) -> Held:
    """Write the group, then read it back.

    Args:
        config_file: `config.toml`.
        group: The values.
        asked: What the page sent: every key of the group, nothing else.

    Returns:
        The values the file now holds.

    Raises:
        ValueError: A key missing or unknown, or a value out of its bounds.
    """
    if set(asked) != {one.key for one in group.fields}:
        raise ValueError(sorted(asked))
    for one in group.fields:
        if not one.accepts(asked[one.key]):
            raise ValueError(one.key)
    document = document_of(config_file)
    table = table_of(document, group.tables[0])
    for name in group.tables[1:]:
        table = table_of(table, name)
    for key, value in asked.items():
        table[key] = value
    write_document(config_file, document)
    return held(config_file, group)


async def setting_route(
    group: SettingGroup, config_file: Path, request: Request
) -> Response:
    """`GET` reads the group, `POST` changes it.

    Args:
        group: The values.
        config_file: `config.toml`.
        request: The request.

    Returns:
        The values read back and the line saying when they apply; 400 on a bad body,
        405 for another method, 500 when the file cannot be written.
    """
    if request.method == "GET":
        body = {"values": await asyncio.to_thread(held, config_file, group)}
        return Response(HTTPStatus.OK, json.dumps(body).encode(), ContentType.JSON)
    if (refused := refused_write(request)) is not None:
        return refused
    try:
        asked = json.loads(request.body)
        if not isinstance(asked, dict):
            raise ValueError  # noqa: TRY004, TRY301
        values = await asyncio.to_thread(saved, config_file, group, asked)
    except OSError:
        message = _("The settings could not be saved in config.toml.")
        return json_response(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": message})
    except ValueError:
        return json_response(HTTPStatus.BAD_REQUEST, {"error": _("Bad request.")})
    if group.applied is not None:
        later = group.applied(values)
        return json_response(
            HTTPStatus.OK, {"values": values, "later": later, "reload": True}
        )
    later = _("Applies the next time mh starts: the open page keeps its settings.")
    return json_response(HTTPStatus.OK, {"values": values, "later": later})
