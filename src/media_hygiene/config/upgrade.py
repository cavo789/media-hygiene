"""Add to an existing `config.toml` the settings a newer version brought, with comments.

The commented template of this version is compared with the user's file, table by
table: a missing table is copied whole, a missing key with the comment block above it,
after the last setting before it that the file already has. Nothing the user wrote is
changed, moved or removed; arrays of tables (`[[classify.rules]]`, places, people) are
the user's own and left alone. A comment line says which version wrote the file.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

import tomlkit
from tomlkit.items import AoT, Table
from tomlkit.toml_document import TOMLDocument

if TYPE_CHECKING:
    from tomlkit.container import Container
    from tomlkit.items import Item, Key

    type Holder = TOMLDocument | Table
    type Block = list[tuple[Key | None, Item]]

# The comment line naming the version that wrote the file: not a setting.
VERSION_MARK: Final = "# media-hygiene-config:"
_VERSION_LINE: Final = re.compile(
    rf"^{re.escape(VERSION_MARK)}\s*(\S+)\s*$", re.MULTILINE
)


@dataclass(frozen=True, slots=True)
class Upgrade:
    """The file once completed, and what it gains."""

    text: str
    added: tuple[str, ...]  # `review.port`, or `tags` for a whole table
    written_by: str | None  # the version the file says wrote it; None: unknown


def written_by(text: str) -> str | None:
    """The version a `config.toml` says wrote it.

    Args:
        text: The file.

    Returns:
        The version, or None for a file older than the mark.
    """
    found = _VERSION_LINE.search(text)
    return found.group(1) if found else None


def plan_upgrade(text: str, template: str, version: str) -> Upgrade:
    """Complete a `config.toml` with what the template has and it lacks.

    Args:
        text: The user's file.
        template: The commented default file of this version, in the file's language.
        version: This version, written in the mark line.

    Returns:
        The completed text and the settings added; the text unchanged when nothing
        is missing (the mark included).
    """
    added: list[str] = []
    document = tomlkit.parse(text)
    merged = _merge(document, tomlkit.parse(template), ("", added))
    if not added:
        return Upgrade(text, (), written_by(text))
    return Upgrade(
        _stamped(tomlkit.dumps(merged), version), tuple(added), written_by(text)
    )


def _merge(user: Holder, model: Holder, where: tuple[str, list[str]]) -> Holder:
    """Add to a table what the template's table has and it lacks.

    Args:
        user: The user's table (or the whole file).
        model: The template's.
        where: The dotted name of the table, and the list of what was added.

    Returns:
        The user's table, rebuilt when something was added.
    """
    prefix, added = where
    inserts: dict[str | None, Block] = {}
    pending: Block = []
    anchor: str | None = None
    for key, item in _body(model):
        if key is None:
            pending.append((key, item))
            continue
        name = key.key
        if name in user:
            _complete(user, name, (item, f"{prefix}{name}.", added))
            anchor, pending = name, []
        elif isinstance(item, AoT):
            pending = []  # the user's own: never added
        else:
            inserts.setdefault(anchor, []).extend((*pending, (key, item)))
            added.append(f"{prefix}{name}")
            pending = []
    return _rebuilt(user, inserts) if inserts else user


def _complete(user: Holder, name: str, model: tuple[Item, str, list[str]]) -> None:
    """Complete one table the file already has, in place.

    Args:
        user: The user's table holding it.
        name: Its key.
        model: The template's item, the dotted name of the table, what was added.
    """
    item, prefix, added = model
    existing = user[name]
    if not isinstance(item, Table) or not isinstance(existing, Table):
        return
    completed = _merge(existing, item, (prefix, added))
    if completed is not existing:
        user[name] = completed


def _rebuilt(user: Holder, inserts: dict[str | None, Block]) -> Holder:
    """The same table, the blocks inserted after their anchors.

    Args:
        user: The user's table (or the whole file).
        inserts: The blocks, by the key they follow (None: first).

    Returns:
        A new table, in the user's order.
    """
    fresh: Holder = (
        tomlkit.document()
        if isinstance(user, TOMLDocument)
        else tomlkit.table(is_super_table=user.is_super_table())
    )
    for key, item in (*inserts.get(None, ()), *_with_inserts(user, inserts)):
        if key is None:
            fresh.add(item)  # a comment or a blank line
        else:
            fresh.add(key, item)
    return fresh


def _with_inserts(user: Holder, inserts: dict[str | None, Block]) -> Block:
    """The user's items, each block after the key it follows.

    Args:
        user: The user's table.
        inserts: The blocks, by the key they follow.

    Returns:
        The items, in order.
    """
    items: Block = []
    for key, item in _body(user):
        items.append((key, item))
        if key is not None:
            items.extend(inserts.get(key.key, ()))
    return items


def _body(container: Holder) -> Block:
    """The items of a table, comments and blank lines included.

    Args:
        container: A table or the whole file.

    Returns:
        Its items, in order.
    """
    inner: Container = (
        container if isinstance(container, TOMLDocument) else container.value
    )
    return list(inner.body)


def _stamped(text: str, version: str) -> str:
    """Write the version mark: replaced, else added on top.

    Args:
        text: The file.
        version: This version.

    Returns:
        The text with one mark line.
    """
    line = f"{VERSION_MARK} {version}"
    if _VERSION_LINE.search(text):
        return _VERSION_LINE.sub(line, text, count=1)
    return f"{line}\n{text}"
