"""The question of `tags` and its answer: prompt C, the schema, the words kept."""

from __future__ import annotations

import json
from pathlib import Path

from media_hygiene.classify.ai.models import Description
from media_hygiene.classify.models import MediaInput
from media_hygiene.config.tags_settings import TagSettings
from media_hygiene.constants import Locale
from media_hygiene.scan.models import VisualFacts
from media_hygiene.tags.models import Tag, TagSource
from media_hygiene.tags.normalize import WordRules
from media_hygiene.tags.selection import vision_plan
from media_hygiene.tags.vision import (
    MAX_TAGS,
    prompt_version,
    read_answer,
    tags_question,
    vision_tags,
)

RULES = WordRules.of(TagSettings(language="fr"), Locale.EN)
RELATIONS = ("mother", "sister", "grandmother")


def test_the_question_follows_the_language_and_forbids_relationships() -> None:
    """French by `[tags] language`; no relation words asked; one-line JSON."""
    body = tags_question(Locale.FR).request("vision", b"jpeg")
    content = body["messages"][0]["content"]  # type: ignore[index]
    assert "Réponds en français" in content
    assert "jamais une relation" in content
    assert "une seule ligne" in content
    english = tags_question(Locale.EN).request("vision", b"jpeg")
    sent = english["messages"][0]["content"]  # type: ignore[index]
    assert "never a relationship" in sent
    assert body["think"] is False
    tags = body["format"]["properties"]["tags"]  # type: ignore[index]
    assert tags["maxItems"] == MAX_TAGS
    assert prompt_version(Locale.FR) != prompt_version(Locale.EN)


def test_the_answer_is_kept_as_written_up_to_ten_tags() -> None:
    """The cache keeps the raw words; nonsense is no answer."""
    words = [f"mot{n}" for n in range(12)]
    content = json.dumps({"description": " Un gâteau. ", "tags": [*words, " "]})
    found = read_answer(content, 2.5)
    assert found == Description("Un gâteau.", tuple(words[:MAX_TAGS]), 2.5)
    assert read_answer("not json", 1) is None
    assert read_answer("[1]", 1) is None
    assert read_answer(json.dumps({"description": " "}), 1) is None
    assert read_answer(json.dumps({"description": "x", "tags": "a"}), 1) == (
        Description("x", (), 1)
    )


def test_the_tags_are_the_sentence_then_the_normalized_words() -> None:
    """The caption whole; the words normalized; the model named."""
    answer = Description("Des bougies sur un gâteau.", ("Bougies", "Gâteaux", "mur"))
    assert vision_tags(answer, RULES, "qwen") == (
        Tag(TagSource.CAPTION, "Des bougies sur un gâteau.", "qwen"),
        Tag(TagSource.VISION, "bougie", "qwen"),
        Tag(TagSource.VISION, "gâteau", "qwen"),
    )


def shot(name: str, seconds: int, size: tuple[int, int] = (4000, 3000)) -> MediaInput:
    """A Canon shot taken at `seconds` past ten, `digest` from its name."""
    visual = VisualFacts(
        1,
        0xFF00FF00FF00FF00,
        *size,
        100.0 + seconds,
        taken_at=f"2021:07:14 10:00:{seconds:02d}",
        camera="Canon",
    )
    return MediaInput(
        Path(f"/data/c/{name}"), Path("/data/c"), 1, 1, visual, None, name
    )


def test_one_photo_per_burst_and_per_set_of_copies() -> None:
    """A burst asks its sharpest shot; a copy takes its twin's answer."""
    burst = [shot("a.jpg", 0), shot("b.jpg", 2), shot("c.jpg", 4)]
    alone = shot("d.jpg", 59)
    twin = MediaInput(
        Path("/data/d/d.jpg"), Path("/data/d"), 1, 1, alone.visual, None, "d.jpg"
    )
    small = shot("e.jpg", 30, (300, 200))
    video = MediaInput(Path("/data/c/f.mp4"), Path("/data/c"), 1, 1, alone.visual)
    plan = vision_plan([*burst, alone, twin, small, video], 512)
    assert [file.path.name for file in plan.asked] == ["d.jpg", "c.jpg"]  # newest first
    assert plan.answered_by[Path("/data/c/a.jpg")] == Path("/data/c/c.jpg")
    assert plan.answered_by[Path("/data/d/d.jpg")] == Path("/data/c/d.jpg")
    assert Path("/data/c/e.jpg") not in plan.answered_by
    assert Path("/data/c/f.mp4") not in plan.answered_by
