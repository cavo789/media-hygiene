"""Give a word typed by hand to photos, take it back, keep their paths current (0555).

A word is one entry whatever its case (`Léa` and `léa` are the same word, the first
spelling kept). The tool's own moves rewrite the paths at once (`follow_hand_tags`,
from `services.sort_links_places`); a folder renamed in Explorer is caught at the end
of the next `audit` (`relocate_hand_tags`). Each save is read back.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.config.hand_tags import HandTag
from media_hygiene.config.photo_ref import follow_paths, relocate
from media_hygiene.config.photo_ref_files import rewritten
from media_hygiene.tags.hand_files import read_hand_tags, save_hand_tags

if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Mapping, Sequence
    from pathlib import Path

    from media_hygiene.config.photo_ref import PhotoRef

    type Rewrite = Callable[[list[PhotoRef]], list[PhotoRef]]


def give_word(config_file: Path, given: HandTag) -> None:
    """Add photos to a word, those it had already kept once (by id).

    Args:
        config_file: `config.toml`, created when missing.
        given: The word and its new photos.

    Raises:
        ValueError: A file is not TOML.
        OSError: A file cannot be written.
    """
    entries = list(read_hand_tags(config_file))
    word = given.word.strip()
    if not any(entry.word.casefold() == word.casefold() for entry in entries):
        entries.append(HandTag(word=word))
    save_hand_tags(
        config_file,
        tuple(
            entry.model_copy(update={"photos": _merged(entry.photos, given.photos)})
            if entry.word.casefold() == word.casefold()
            else entry
            for entry in entries
        ),
    )


def take_word(config_file: Path, word: str, ids: Collection[str]) -> None:
    """Take a word off photos; a word left without photos goes.

    Args:
        config_file: `config.toml`.
        word: The word, any case.
        ids: The photos' ids.

    Raises:
        ValueError: A file is not TOML.
        OSError: A file cannot be written.
    """
    save_hand_tags(
        config_file,
        tuple(
            entry.model_copy(
                update={"photos": tuple(p for p in entry.photos if p.id not in ids)}
            )
            if entry.word.casefold() == word.strip().casefold()
            else entry
            for entry in read_hand_tags(config_file)
        ),
    )


def _merged(
    before: Sequence[PhotoRef], added: Sequence[PhotoRef]
) -> tuple[PhotoRef, ...]:
    """The photos of a word, each id once: a new path replaces an older one.

    Args:
        before: Its photos.
        added: The new ones.

    Returns:
        Them, in order.
    """
    by_id = {photo.id: photo for photo in before}
    by_id.update({photo.id: photo for photo in added})
    return tuple(by_id.values())


def follow_hand_tags(config_file: Path, moves: Mapping[str, str]) -> int:
    """Rewrite the paths of the photos a run moved.

    Args:
        config_file: `config.toml`; missing: nothing to do.
        moves: New host path by old one.

    Returns:
        The photos whose path changed, counted on the files read back.
    """
    return _rewrite(config_file, lambda refs: follow_paths(refs, moves))


def relocate_hand_tags(config_file: Path, found: Mapping[str, Sequence[str]]) -> int:
    """Rewrite the paths of the photos renamed outside, found again by id.

    Args:
        config_file: `config.toml`; missing: nothing to do.
        found: The host paths holding each id.

    Returns:
        The photos whose path changed, counted on the files read back.
    """
    return _rewrite(config_file, lambda refs: relocate(refs, found))


def _rewrite(config_file: Path, rewrite: Rewrite) -> int:
    """Apply a rewrite to every photo, save when something changed, read back.

    Args:
        config_file: `config.toml`.
        rewrite: The new references, in order, from the old ones.

    Returns:
        The photos whose path changed, counted on the files read back.
    """
    if not config_file.is_file():
        return 0
    before = read_hand_tags(config_file)
    after = rewritten(before, rewrite)
    if after is None:
        return 0
    save_hand_tags(config_file, after)
    back = {
        (e.word, p.id): p.path for e in read_hand_tags(config_file) for p in e.photos
    }
    return sum(
        1
        for entry in before
        for photo in entry.photos
        if back.get((entry.word, photo.id), photo.path) != photo.path
    )


def hand_ids(config_file: Path) -> frozenset[str]:
    """The ids of every photo given a word by hand.

    Args:
        config_file: `config.toml`.

    Returns:
        Them.
    """
    if not config_file.is_file():
        return frozenset()
    return frozenset(p.id for e in read_hand_tags(config_file) for p in e.photos)
