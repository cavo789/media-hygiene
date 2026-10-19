"""The cheap tags: the words of the folders and name, the date, the place. Seconds.

The vision model sees scenes and objects, never occasions nor places (measured, TODO
0072): `Pâques 2007`, `Durbuy` and `Noël` come from here. Each producer gives the
words of one source, kept once each (case ignored), in their first order.
"""

from __future__ import annotations

import re
from dataclasses import replace
from typing import TYPE_CHECKING, Final

from media_hygiene.date_names import MONTHS
from media_hygiene.plan.copy_names import without_copy_marks
from media_hygiene.tags.dates import date_words
from media_hygiene.tags.models import Tag, TagSource
from media_hygiene.tags.place_words import place_tags

if TYPE_CHECKING:
    from collections.abc import Iterable

    from media_hygiene.classify.models import MediaInput
    from media_hygiene.plan.name_rules import NameRules
    from media_hygiene.tags.context import TagContext

# A folder name is split on spaces, underscores, dots and punctuation, not on hyphens:
# `Saint-Nicolas` stays one word.
_SEPARATORS: Final = re.compile(r"[\s_.,;:()\[\]{}+&!?#]+")
_MONTH_WORDS: Final = frozenset(name for names in MONTHS for name in names)
# Appended to a word to see whether a device numbers its files after it: `IMG_1`.
_COUNTER: Final = "_1"
_SPACES: Final = re.compile(r"\s+")
# Words that link others in a folder name, never searched for on their own.
_LINKS: Final = frozenset(
    {"les", "des", "une", "aux", "chez", "avec", "pour", "sur", "dans", "par", "et"}
    | {"the", "and", "with", "for", "from", "at", "to", "of", "in", "on"}
    | {"het", "een", "met", "van", "voor"}
)


def cheap_tags(file: MediaInput, context: TagContext) -> tuple[Tag, ...]:
    """Every tag a file gets without a model.

    Args:
        file: The file, its root and what the index knows of it.
        context: Folder rules, calendar, places and towns.

    Returns:
        Its folder, name, former folder and name, Takeout description, date and
        place tags.
    """
    return (
        *_tags(TagSource.FOLDER, folder_words(file, context)),
        *_tags(TagSource.NAME, name_words(file, context)),
        *_tags(TagSource.FORMER, former_words(file, context)),
        *_tags(TagSource.TAKEOUT, takeout_words(file, context)),
        *_tags(TagSource.DATE, date_words(file, context)),
        *place_tags(file, context),
    )


def folder_words(file: MediaInput, context: TagContext) -> tuple[str, ...]:
    """The meaningful words of the folders between the root and the file.

    Args:
        file: The file and its root.
        context: The folder rules (generic and band folders) and stop words.

    Returns:
        `2019/Durbuy - ours` → `Durbuy`, `ours`; nothing for `DCIM/100CANON`.
    """
    labels = context.folders.meaning(file.path.parent, file.root)
    return _meaningful(labels, context)


def name_words(file: MediaInput, context: TagContext) -> tuple[str, ...]:
    """The meaningful words of the file name, split like those of the folders.

    Args:
        file: The file.
        context: The generated names (`[keep]`) and the stop words.

    Returns:
        `Anniversaire Léa (1).mp4` → `Anniversaire`, `Léa`;
        `2019-07-12 Plage.jpg` → `Plage` (the date has its own source); nothing for
        a name a camera or an app generated (`IMG_1234.jpg`, `VID-20190712-WA0001`),
        nor for its words (`IMG_1234 Léa.jpg` → `Léa`).
    """
    if context.names.has_generated_name(file.path):
        return ()
    words = _meaningful((without_copy_marks(file.path.stem),), context)
    return tuple(
        word
        for word in words
        if any(letter.isalpha() for letter in word)
        and not _device_word(word, context.names)
    )


def former_words(file: MediaInput, context: TagContext) -> tuple[str, ...]:
    """The words of the folders and names of the copies `clean` removed (0207).

    Args:
        file: The kept file, and where its removed copies lay.
        context: As for `folder_words` and `name_words`.

    Returns:
        Their words, but those the file's own folders and name already give.
    """
    copies = [replace(file, path=c.path, root=c.root, former=()) for c in file.former]
    mine = (*folder_words(file, context), *name_words(file, context))
    own = {word.casefold() for word in mine}
    return tuple(
        word
        for copy in copies
        for word in (*folder_words(copy, context), *name_words(copy, context))
        if word.casefold() not in own
    )


def takeout_words(file: MediaInput, context: TagContext) -> tuple[str, ...]:
    """The description typed in Google Photos: the sentence whole, then its words.

    Args:
        file: The file and what its Takeout `.json` said (0240).
        context: The stop words.

    Returns:
        `Fête de Léa à la plage` → that sentence, `Fête`, `Léa`, `plage`; nothing
        without a Takeout `.json` or with an empty description.
    """
    text = _SPACES.sub(" ", (file.takeout.description or "") if file.takeout else "")
    if not text.strip():
        return ()
    return (text.strip(), *_meaningful((text,), context))


def _device_word(word: str, names: NameRules) -> bool:
    """Tell whether a word of a name is a camera's or an app's, not someone's.

    Args:
        word: One word of a file name.
        names: The generated names.

    Returns:
        True for `IMG` (as in `IMG_1234`), `DSC`, `GOPR0042` or a long hexadecimal.
    """
    return names.is_generated(word) or names.is_generated(word + _COUNTER)


def _meaningful(labels: Iterable[str], context: TagContext) -> tuple[str, ...]:
    """Split labels into words; drop short ones, numbers, months and link words.

    Args:
        labels: Folder names, or the name of a file without its extension.
        context: The stop words.

    Returns:
        The words kept, in order.
    """
    words = (word.strip("-") for label in labels for word in _SEPARATORS.split(label))
    return tuple(
        word
        for word in words
        if context.words.keeps(word)
        and word.casefold() not in _MONTH_WORDS
        and word.casefold() not in _LINKS
    )


def _tags(source: TagSource, words: Iterable[str]) -> tuple[Tag, ...]:
    """Make tags of words, each once whatever its case.

    Args:
        source: Where they come from.
        words: The words, in order.

    Returns:
        The tags.
    """
    seen: dict[str, str] = {}
    for word in words:
        seen.setdefault(word.casefold(), word.strip())
    return tuple(Tag(source, word) for word in seen.values() if word)
