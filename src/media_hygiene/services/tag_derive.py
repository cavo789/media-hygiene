"""The model's words of each photo, written as soon as it is described (0353).

`tags` used to write the `caption` and `vision` rows the search reads only once every
photo was described: hours without a model word in the search, and a run killed lost
them. Now each answer, stored at once, writes at once the words of the photo and of
every file it answers for (its identical copies, the burst series it leads, its near
group): a search a moment later finds them. One code path with the end of the run,
which still writes the files whose answer came from the cache.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Final, override

from media_hygiene.i18n import _
from media_hygiene.index.descriptions import DescriptionStore
from media_hygiene.index.tag_rows import TagStore
from media_hygiene.services.tag_work import version_of
from media_hygiene.tags.models import MODEL_SOURCES, FileTags, TagSource
from media_hygiene.tags.vision import vision_tags

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence
    from pathlib import Path

    from media_hygiene.classify.ai.models import Description
    from media_hygiene.classify.models import MediaInput
    from media_hygiene.index.descriptions import PhotoVersion
    from media_hygiene.services.tag_work import TagWork
    from media_hygiene.tags.normalize import WordRules


def model_rows(
    work: TagWork, store: DescriptionStore, sight: tuple[WordRules, str]
) -> list[FileTags]:
    """The model's tags of every photo whose answer is in the cache.

    A photo takes its own answer, else the one of the photo that answers for it.

    Args:
        work: The files and who answers for whom.
        store: The cached answers.
        sight: The words' rules, and the model.

    Returns:
        One row per photo with an answer.
    """
    asked = {file.path: version_of(file) for file in work.vision.asked}
    rows: list[FileTags] = []
    for file in work.files:
        leader = work.vision.answered_by.get(file.path)
        if leader is None:
            continue
        found = store.get(version_of(file)) or store.get(asked[leader])
        if found is not None:
            rows.append(FileTags(version_of(file), vision_tags(found, *sight)))
    return rows


# Of the last photo's words, those the progress line shows (0421).
_SHOWN_WORDS: Final = 6


def _ignored(_text: str) -> None:
    """Say nothing: no progress listens."""


class TaggingStore(DescriptionStore):
    """The cache of answers that also writes the words of each answer at once."""

    def __init__(
        self, base: DescriptionStore, work: TagWork, sight: tuple[WordRules, str]
    ) -> None:
        """Wrap the store of a run.

        Args:
            base: The store of the run (its connection, model and prompt).
            work: Who answers for whom.
            sight: The words' rules, and the model.
        """
        super().__init__(base.connection, base.asked)
        self._answered = answered_for(work.files, work.vision.answered_by)
        self._sight = sight
        self._tell: Callable[[str], None] = _ignored

    def telling(self, tell: Callable[[str], None]) -> None:
        """Say the words of each photo described, e.g. on the progress's line (0421).

        Args:
            tell: Receives `name: word, word, ...`, translated.
        """
        self._tell = tell

    @override
    def put(self, photo: PhotoVersion, description: Description) -> None:
        """Remember an answer, then write the words of the files it answers for.

        A file that has an answer of its own keeps it.

        Args:
            photo: The photo described.
            description: What the model saw.
        """
        super().put(photo, description)
        tags = vision_tags(description, *self._sight)
        rows = [
            FileTags(version_of(file), tags)
            for file in self._answered.get(photo.path, ())
            if file.path == photo.path or self.get(version_of(file)) is None
        ]
        TagStore(self.connection).replace(MODEL_SOURCES, rows)
        words = [tag.value for tag in tags if tag.source is TagSource.VISION]
        if words:
            self._tell(
                _("{name}: {words}").format(
                    name=photo.path.name, words=", ".join(words[:_SHOWN_WORDS])
                )
            )


def answered_for(
    files: Sequence[MediaInput], answered_by: Mapping[Path, Path]
) -> dict[Path, tuple[MediaInput, ...]]:
    """The files each photo asked about answers for, itself included.

    Args:
        files: The files of the run.
        answered_by: Each photo seen → the photo asked about.

    Returns:
        The photo asked about → its files.
    """
    found: dict[Path, list[MediaInput]] = defaultdict(list)
    for file in files:
        leader = answered_by.get(file.path)
        if leader is not None:
            found[leader].append(file)
    return {leader: tuple(group) for leader, group in found.items()}
