"""Make the words of a vision model stable: one spelling per tag.

Measured on a real collection (TODO 0072): `bougie` / `bougies`, `Fleurs`, `à` split
from `salle à manger`, `sol` and `mur` on every photo. After this step a tag is lower
case, trimmed, singular for simple plurals, longer than two letters, not a stop word,
and listed once.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.tags.plurals import singular

if TYPE_CHECKING:
    from collections.abc import Iterable

    from media_hygiene.config.tags_settings import TagSettings
    from media_hygiene.constants import Locale

_MIN_LENGTH: Final = 3  # one or two letters: `à`, `de`, `un`
_SPACES: Final = re.compile(r"\s+")
_EDGES: Final = " \t.,;:!?\"'()[]{}«»“”‘’*-_/"  # noqa: RUF001 - French quotes
_WORD: Final = re.compile(r"[\w'’-]+")  # noqa: RUF001 - the French apostrophe


@dataclass(frozen=True, slots=True)
class WordRules:
    """The language of the tags, and the words left out (folded)."""

    language: Locale
    stop_words: frozenset[str]

    @classmethod
    def of(cls, settings: TagSettings, interface: Locale) -> WordRules:
        """Read `[tags]`.

        Args:
            settings: `[tags]`.
            interface: The language of the interface.

        Returns:
            The rules.
        """
        return cls(
            settings.language_of(interface),
            frozenset(word.casefold() for word in settings.stop_words),
        )

    def keeps(self, word: str) -> bool:
        """Tell whether a word says something.

        Args:
            word: A tag or a word of a folder name.

        Returns:
            False for one or two letters, a number, or a stop word.
        """
        if len(word) < _MIN_LENGTH or word.isdigit():
            return False
        return word.casefold() not in self.stop_words


def normalize(words: Iterable[str], rules: WordRules) -> tuple[str, ...]:
    """Normalize the tags of a model.

    Args:
        words: The tags, as the model wrote them.
        rules: Language and stop words.

    Returns:
        The tags kept, in their first order, each once.
    """
    found: dict[str, None] = {}
    for word in words:
        tag = clean(word, rules)
        if rules.keeps(tag):
            found.setdefault(tag)
    return tuple(found)


def clean(word: str, rules: WordRules) -> str:
    """Lower case, trimmed, spaces collapsed, each word singular.

    Args:
        word: One tag; several words stay one tag (`salle à manger`).
        rules: The language.

    Returns:
        The tag.
    """
    text = _SPACES.sub(" ", word.lower()).strip(_EDGES)
    return _WORD.sub(lambda found: singular(found[0], rules.language), text)
