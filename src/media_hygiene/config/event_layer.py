"""The events remembered by the tool, in `/config/events/<year>.toml` (0576).

*Move to an event…* (0556) and *Events found in your folders* (0557) remember each event
as a `date_range` rule. Written into `config.toml`, 196 events made it about 1 000 lines
longer (estimated: 5 lines each): they live under `events/` instead, one file per year
of their start, as `[[rules]]` tables. Every `events/*.toml` holding `[[rules]]` is
read, whatever its name (a file renamed by hand still counts); the refusal files and
`not-events.toml` hold other keys and are skipped. The events take the place the tool
gave them in `config.toml`: just above *Existing folders* (the first sure rule wins). A
name written in `config.toml` too wins over the event (a move cut short by a crash).
"""

from __future__ import annotations

import tomllib
from typing import TYPE_CHECKING, Final

from media_hygiene.config.classify_rules import DEFAULT_RULES
from media_hygiene.errors import ConfigError
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.config.layers import Layer

FOLDER: Final = "events"  # under the folder of config.toml
RULES: Final = "rules"  # an events file: its `[[rules]]`
_SECTION: Final = "classify"
_EXISTING_FOLDER: Final = "existing_folder"
_ENCODING: Final = "utf-8"

type Table = dict[str, object]


def event_files(config_dir: Path) -> tuple[Path, ...]:
    """The files of `events/` that hold events, by name.

    Args:
        config_dir: The folder of `config.toml`.

    Returns:
        Them; none without the folder.

    Raises:
        ConfigError: A file is not valid TOML.
    """
    folder = config_dir / FOLDER
    if not folder.is_dir():
        return ()
    return tuple(path for path in sorted(folder.glob("*.toml")) if read_file(path))


def read_file(path: Path) -> list[Table]:
    """The events of one file.

    Args:
        path: An `events/*.toml` file.

    Returns:
        Its `[[rules]]`, as written; none when it holds other keys.

    Raises:
        ConfigError: The file cannot be read or is not valid TOML.
    """
    try:
        written = tomllib.loads(path.read_text(_ENCODING)).get(RULES, [])
    except (OSError, ValueError) as exc:
        message = _("The events file {file} cannot be read: {error}.")
        raise ConfigError(message.format(file=path.name, error=exc)) from exc
    return [item for item in written if isinstance(item, dict)]


def event_tables(config_dir: Path) -> list[Table]:
    """Every event of `events/`, file by file.

    Args:
        config_dir: The folder of `config.toml`.

    Returns:
        The events, as written.
    """
    return [item for path in event_files(config_dir) for item in read_file(path)]


def merged_rules(written: Sequence[object], events: Sequence[Table]) -> list[object]:
    """The rules of `config.toml` with the events in the place the tool gives them.

    Args:
        written: The `[[classify.rules]]` of `config.toml`.
        events: The events of `events/`.

    Returns:
        The rules, the events just above *Existing folders* (first when there is none);
        an event named like a rule of `config.toml` left out.
    """
    names = {_name(item) for item in written}
    kept = [item for item in events if _name(item) not in names]
    at = next(
        (
            index
            for index, item in enumerate(written)
            if isinstance(item, dict) and item.get("match") == _EXISTING_FOLDER
        ),
        0,
    )
    return [*written[:at], *kept, *written[at:]]


def linked_events(layer: Layer, config_dir: Path) -> Layer:
    """The layer of `config.toml`, the events of `events/` added to its rules.

    Args:
        layer: The file's tables, as parsed.
        config_dir: The folder of `config.toml`.

    Returns:
        The layer; as it was without events. Without `[[classify.rules]]` in the file,
        the events join the default list.
    """
    events = event_tables(config_dir)
    if not events:
        return layer
    section = dict(layer.get(_SECTION, {}))
    written = section.get(RULES)
    if not isinstance(written, list):
        written = [
            rule.model_dump(mode="json", exclude_defaults=True)
            for rule in DEFAULT_RULES
        ]
    section[RULES] = merged_rules(written, events)
    return {**layer, _SECTION: section}


def _name(item: object) -> str:
    """A rule's name, case ignored.

    Args:
        item: A raw rule.

    Returns:
        The name, folded; empty when there is none.
    """
    return str(item.get("name", "")).casefold() if isinstance(item, dict) else ""
