"""Remove the stale entries the user ticked from `config.toml`, keeping the rest.

`tomlkit` edits the document in place: the comments, the order and the other entries
stay as written. The new text must read back as the old one minus exactly the entries
removed, or nothing is written.
"""

from __future__ import annotations

import tomllib
from typing import TYPE_CHECKING, Any

import tomlkit
from tomlkit.items import AoT, Array, Table

from media_hygiene.errors import ConfigError
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from media_hygiene.config.tidy_rules import StaleEntry


def without_entries(text: str, entries: Sequence[StaleEntry]) -> str:
    """The text of `config.toml` once the entries are removed.

    Args:
        text: The file.
        entries: The entries to remove.

    Returns:
        The new text.

    Raises:
        ConfigError: The result would not be the file minus these entries.
    """
    document = tomlkit.parse(text)
    sections = sorted({entry.section for entry in entries})
    for section in sections:
        ranks = sorted(
            {entry.rank for entry in entries if entry.section == section}, reverse=True
        )
        _remove(document, section, ranks)
    result = tomlkit.dumps(document)
    check_removed(text, result, entries)
    return result


def check_removed(before: str, after: str, entries: Sequence[StaleEntry]) -> None:
    """Prove that `after` is `before` minus exactly the entries, nothing else.

    Args:
        before: The file before.
        after: The file after (read back from the disk, once written).
        entries: The entries removed.

    Raises:
        ConfigError: Another value changed, or an entry is still there.
    """
    expected = tomllib.loads(before)
    for section in {entry.section for entry in entries}:
        ranks = {entry.rank for entry in entries if entry.section == section}
        top, key = section.split(".")
        rows = expected[top][key]
        expected[top][key] = [row for rank, row in enumerate(rows) if rank not in ranks]
    if _pruned(expected) != _pruned(tomllib.loads(after)):
        raise ConfigError(
            _("Tidying config.toml would change other settings: nothing was written.")
        )


def _pruned(document: Mapping[str, Any]) -> dict[str, Any]:
    """The document without its empty arrays (an emptied array of tables goes away).

    Args:
        document: A parsed file.

    Returns:
        The same, empty arrays left out.
    """
    return {
        key: _pruned(value) if isinstance(value, dict) else value
        for key, value in document.items()
        if value != []
    }


def _remove(document: tomlkit.TOMLDocument, section: str, ranks: Sequence[int]) -> None:
    """Remove some rows of one array, from the last one; an emptied table array goes.

    Args:
        document: The parsed file.
        section: `classify.rules`, `folders.protected`…
        ranks: The ranks to remove, from the last one.

    Raises:
        ConfigError: The section is not an array.
    """
    top, key = section.split(".")
    holder = document.get(top)
    rows = holder.get(key) if isinstance(holder, Table) else None
    if not isinstance(rows, AoT | Array):
        raise ConfigError(_("{section} is not a list.").format(section=section))
    for rank in ranks:
        del rows[rank]
    if isinstance(rows, AoT) and not rows.body and isinstance(holder, Table):
        del holder[key]
