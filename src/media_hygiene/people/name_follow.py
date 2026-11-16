"""After a rename or a merge (0827), every setting naming the person follows.

The readers of a person's name, besides `[[people.person]]`: `[slideshow] avoid` (0834),
the `names` of `[[classify.rules]]` in `config.toml` and of `[[rules]]` in the events
remembered (`/config/events/<year>.toml`, 0576). Each is rewritten with tomlkit
(comments kept, atomic, the previous file in `.history/`), names compared without case
nor accents as their readers do; a name already there is not added twice. What does
not follow: the albums hold files, not names (an album named after the person keeps its
name), and the names written into XMP sidecars stay as written until `xmp` runs again.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.config.event_layer import FOLDER as EVENTS
from media_hygiene.people.folding import folded
from media_hygiene.places.toml_edit import document_of, write_document

if TYPE_CHECKING:
    from pathlib import Path

    from tomlkit.toml_document import TOMLDocument

_NAMES: Final = "names"
_RULES: Final = "rules"
_SUFFIX: Final = ".toml"
_LABELS: Final = {"slideshow": "[slideshow] avoid", "classify": "[[classify.rules]]"}


def follow_name(config_file: Path, old: str, new: str) -> tuple[str, ...]:
    """Rename a person in every setting that names them, and say where.

    Args:
        config_file: `config.toml`.
        old: The name before.
        new: The name now.

    Returns:
        The settings rewritten: `[slideshow] avoid`, `[[classify.rules]]`, events files.
    """
    pair = (folded(old), new)
    changed: list[str] = []
    document = document_of(config_file)
    found = [
        label
        for key, label in _LABELS.items()
        if _rename_in(_lists(document, key), pair)
    ]
    if found:
        write_document(config_file, document)
        changed.extend(found)
    folder = config_file.parent / EVENTS
    for file in sorted(folder.glob(f"*{_SUFFIX}")) if folder.is_dir() else ():
        events = document_of(file)
        if _rename_in(_lists(events, _RULES), pair):
            write_document(file, events)
            changed.append(f"{EVENTS}/{file.name}")
    return tuple(changed)


def _lists(document: TOMLDocument, key: str) -> list[list[object]]:
    """The lists of names a table of the document holds.

    Args:
        document: The file.
        key: `slideshow` (its `avoid`), `classify` (its rules), `rules` (events).

    Returns:
        The tomlkit arrays, edited in place.
    """
    found = document.get(key)
    if key == "slideshow":
        avoid = found.get("avoid") if isinstance(found, dict) else None
        return [avoid] if isinstance(avoid, list) else []
    rules = (
        found.get(_RULES) if key == "classify" and isinstance(found, dict) else found
    )
    if not isinstance(rules, list):
        return []
    return [
        names
        for rule in rules
        if isinstance(rule, dict) and isinstance(names := rule.get(_NAMES), list)
    ]


def _rename_in(lists: list[list[object]], pair: tuple[str, str]) -> bool:
    """Replace a name in lists of names, each name once.

    Args:
        lists: The arrays, edited in place.
        pair: The old name, folded, and the new one.

    Returns:
        True when one changed.
    """
    old, new = pair
    changed = False
    for names in lists:
        if not any(isinstance(n, str) and folded(n) == old for n in names):
            continue
        seen: set[str] = set()
        kept: list[str] = []
        for name in (new if folded(str(n)) == old else str(n) for n in names):
            if folded(name) not in seen:
                seen.add(folded(name))
                kept.append(name)
        names.clear()
        names.extend(kept)
        changed = True
    return changed
