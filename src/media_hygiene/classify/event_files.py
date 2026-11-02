"""What the user said no to about events, in files of their own under `/config/events/`.

An event's refused files (in its window, not picked: never proposed again) go to
`events/<start date>-<name>.toml`, linked from its rule as `file = "events/…"`, like
`/config/people/<name>.toml` (0300): `config.toml` must not keep growing. The folders
the user says are no event (0557) go to `events/not-events.toml`. Both list content ids
(the files' SHA-256), so that they follow a move. A file is created only when there is
something to keep; each write is atomic and read back.
"""

from __future__ import annotations

import tomllib
from typing import TYPE_CHECKING, Final

import tomlkit

from media_hygiene.classify.layout import safe_name
from media_hygiene.classify.rules.calendar import parse_one_off
from media_hygiene.classify.rules_edit import replace_rule
from media_hygiene.classify.rules_file import read_rules
from media_hygiene.config.people_files import linked_path
from media_hygiene.errors import ConfigError
from media_hygiene.i18n import _
from media_hygiene.places.toml_edit import ENCODING, write_document

if TYPE_CHECKING:
    from collections.abc import Collection
    from pathlib import Path

    from media_hygiene.config.classify_rules import ClassifyRule

FOLDER: Final = "events"  # under the folder of config.toml
REFUSED: Final = "refused"  # an event's file: the content ids it never takes
NOT_EVENTS: Final = f"{FOLDER}/not-events.toml"
FOLDERS: Final = "folders"  # not-events.toml: the content ids of their files


def event_file(rule: ClassifyRule) -> str:
    """The file an event's refusals go to, relative to `config.toml`.

    Args:
        rule: The event.

    Returns:
        Its link if written, else `events/<start>-<name>.toml`.
    """
    if rule.file:
        return rule.file
    start = parse_one_off(rule.dates).start.isoformat()
    return f"{FOLDER}/{start}-{safe_name(rule.category or rule.name)}.toml"


def read_refused(config_dir: Path, rule: ClassifyRule) -> frozenset[str]:
    """The content ids an event never takes.

    Args:
        config_dir: The folder of `config.toml`.
        rule: The event.

    Returns:
        Them; none without a linked file.

    Raises:
        ConfigError: The linked file is missing, outside the folder, or not TOML.
    """
    return _ids(config_dir, rule.file, REFUSED) if rule.file else frozenset()


def add_refused(
    config_file: Path, rule: ClassifyRule, ids: Collection[str]
) -> frozenset[str]:
    """Add refused files to an event, its file created and linked when first needed.

    Args:
        config_file: `config.toml`.
        rule: The event, as read from it.
        ids: The content ids refused.

    Returns:
        Every id refused, read back from the disk.

    Raises:
        ConfigError: The file cannot be written or read back.
    """
    config_dir = config_file.parent
    relative = event_file(rule)
    held = _ids(config_dir, rule.file, REFUSED) if rule.file else frozenset()
    if not ids or held.issuperset(ids):
        return held
    _write_ids(config_dir, relative, (REFUSED, held | set(ids)))
    if not rule.file:
        replace_rule(config_file, rule.name, rule.model_copy(update={"file": relative}))
    linked = next(item for item in read_rules(config_file) if item.name == rule.name)
    return read_refused(config_dir, linked)


def read_not_events(config_dir: Path) -> frozenset[str]:
    """The content ids of the files of folders the user says are no event (0557).

    Args:
        config_dir: The folder of `config.toml`.

    Returns:
        Them; none before the first answer.
    """
    if not (config_dir / NOT_EVENTS).is_file():
        return frozenset()
    return _ids(config_dir, NOT_EVENTS, FOLDERS)


def add_not_events(config_dir: Path, ids: Collection[str]) -> frozenset[str]:
    """Say a folder's files are of no event, by content id.

    Args:
        config_dir: The folder of `config.toml`.
        ids: The content ids of its files.

    Returns:
        Every id kept, read back from the disk.
    """
    held = read_not_events(config_dir)
    if ids and not held.issuperset(ids):
        _write_ids(config_dir, NOT_EVENTS, (FOLDERS, held | set(ids)))
    return read_not_events(config_dir)


def take_back_not_events(config_dir: Path, ids: Collection[str]) -> frozenset[str]:
    """Tick folders back: their files are no longer said to be of no event (0557).

    Args:
        config_dir: The folder of `config.toml`.
        ids: The content ids of their files.

    Returns:
        Every id still kept, read back from the disk.
    """
    held = read_not_events(config_dir)
    if held & set(ids):
        _write_ids(config_dir, NOT_EVENTS, (FOLDERS, set(held - set(ids))))
    return read_not_events(config_dir)


def _ids(config_dir: Path, relative: str, key: str) -> frozenset[str]:
    """The ids of a linked file.

    Args:
        config_dir: The folder of `config.toml`.
        relative: The link.
        key: The list read.

    Returns:
        The ids.

    Raises:
        ConfigError: The file is missing, outside the folder, or not TOML.
    """
    try:
        path = linked_path(config_dir, relative)
        written = tomllib.loads(path.read_text(ENCODING)).get(key, [])
    except (OSError, ValueError) as exc:
        message = _("The events file {file} cannot be read: {error}.")
        raise ConfigError(message.format(file=relative, error=exc)) from exc
    return frozenset(str(item) for item in written)


def _write_ids(
    config_dir: Path, relative: str, content: tuple[str, Collection[str]]
) -> None:
    """Write one list of ids, sorted, atomically.

    Args:
        config_dir: The folder of `config.toml`.
        relative: The link.
        content: The list's key and its ids.
    """
    path = linked_path(config_dir, relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    key, ids = content
    document = tomlkit.document()
    listed = tomlkit.array()
    listed.extend(sorted(ids))
    document[key] = listed.multiline(multiline=True)
    write_document(path, document)
