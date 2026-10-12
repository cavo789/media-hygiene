"""What `tags` saw, read back as a description for the `subject` rule."""

from __future__ import annotations

from media_hygiene.classify.ai.models import Description
from media_hygiene.services.subject_store import described_by_tags
from media_hygiene.tags.models import Tag, TagSource

TAGS = (
    Tag(TagSource.FOLDER, "Durbuy"),
    Tag(TagSource.CAPTION, "A beach by the sea.", "vision"),
    Tag(TagSource.VISION, "beach", "vision"),
    Tag(TagSource.VISION, "sea", "vision"),
    Tag(TagSource.VISION, "castle", "older"),
)


def test_the_sentence_and_words_of_that_model() -> None:
    """Its caption and its vision words; the folder and another model's words left."""
    found = described_by_tags(TAGS, "vision")
    assert found == Description("A beach by the sea.", ("beach", "sea"))


def test_nothing_from_another_model_or_without_a_model() -> None:
    """No sentence of the model asked, or no model: not described."""
    assert described_by_tags(TAGS, "older") is None
    assert described_by_tags(TAGS, "") is None
    assert described_by_tags((), "vision") is None
