"""`classify` reads what `tags` already saw: a photo is sent to the model once.

`tags` keeps, for every photo it described (and for the copies and burst shots that
take that answer), the model's sentence (`caption`) and its words (`vision`). When
the model of `[classify.ai]` wrote them, the `subject` rule maps them to its
categories like one of its own descriptions: only the photos `tags` never saw are
described again, with the question of `classify`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from media_hygiene.classify.ai.models import Description
from media_hygiene.index.descriptions import DescriptionStore
from media_hygiene.index.tag_rows import TagStore
from media_hygiene.tags.models import TagSource

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Sequence

    from media_hygiene.index.descriptions import PhotoVersion
    from media_hygiene.tags.models import Tag


class ReusingStore(DescriptionStore):
    """The descriptions of `classify`, else the answer `tags` had from that model."""

    def __init__(self, connection: sqlite3.Connection, asked: tuple[str, str]) -> None:
        """Bind the store to a model and a prompt version.

        Args:
            connection: The index connection, tables prepared.
            asked: The vision model, and the version of the describe prompt.
        """
        super().__init__(connection, asked)
        self._tags = TagStore(connection)
        self._vision_model = asked[0]

    @override
    def get(self, photo: PhotoVersion) -> Description | None:
        """The description of this version of a photo, its own or that of `tags`.

        Args:
            photo: The photo.

        Returns:
            It, or None when neither `classify` nor `tags` had it described.
        """
        own = super().get(photo)
        if own is not None:
            return own
        return described_by_tags(self._tags.of(photo), self._vision_model)


def described_by_tags(tags: Sequence[Tag], model: str) -> Description | None:
    """What a model saw, rebuilt from the tags it gave a photo.

    Args:
        tags: The tags of the photo.
        model: The vision model asked: the tags of another one are not its answer.

    Returns:
        Its sentence and words, or None without a sentence of that model.
    """
    if not model:
        return None
    caption = next(
        (
            tag.value
            for tag in tags
            if tag.source is TagSource.CAPTION and tag.model == model
        ),
        None,
    )
    if caption is None:
        return None
    words = tuple(
        tag.value
        for tag in tags
        if tag.source is TagSource.VISION and tag.model == model
    )
    return Description(caption, words)
