"""`[[tags.hand]]`: the words the user typed on photos, one file per word (0555).

A word typed on photos of the search page (*🏷 Tag…*) is a decision, like a person or a
place: it lives in `/config`, never in the index (`/cache`, recomputable), and no run
would find it again. `config.toml` keeps each word's entry short, `word` and `file =
"tags/<word>.toml"`; that file lists its photos as `{path, id}` (`config.photo_ref`,
0551): the path kept current by the tool's moves and by each `audit`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field

from media_hygiene.config.photo_ref import PhotoRef
from media_hygiene.config.place_files import linked_entries
from media_hygiene.errors import ConfigError
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.config.layers import Layer

SECTION: Final = "tags"
KEY: Final = "hand"
WORD: Final = "word"
FOLDER: Final = "tags"  # under the folder of config.toml
LONGEST: Final = 80  # characters of a word typed: a few words, never a text


class HandTag(BaseModel):
    """One word typed by hand, and the photos it was given to."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    word: str = Field(min_length=1, max_length=LONGEST)
    photos: tuple[PhotoRef, ...] = ()
    # The file holding the photos, relative to the folder of `config.toml`.
    file: str = ""


def linked_hand(layer: Layer, config_dir: Path) -> Layer:
    """The layer of `config.toml`, the photos of each hand word read from its file.

    Args:
        layer: The file's tables, as parsed.
        config_dir: The folder of `config.toml`.

    Returns:
        The layer, `[[tags.hand]]` filled in.

    Raises:
        ConfigError: A linked file is missing, outside the folder, or not TOML.
    """
    section = layer.get(SECTION)
    if section is None:
        return layer
    try:
        return {**layer, SECTION: linked_entries(section, config_dir, KEY)}
    except ValueError as exc:
        message = _("The words typed on photos cannot be read: {error}.")
        raise ConfigError(message.format(error=exc)) from exc
