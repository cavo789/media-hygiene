"""The questions asked to the model, and how its answers are read."""

from __future__ import annotations

import base64
import json

from media_hygiene.classify.ai.models import Description
from media_hygiene.classify.ai.prompts import (
    NONE_ANSWER,
    describe_request,
    map_request,
    read_description,
    read_mapping,
    version,
)
from media_hygiene.classify.ai.subjects import NONE

CATEGORIES = ("Holidays", "School")


def test_the_describe_request_sends_the_photo_and_a_short_schema() -> None:
    """One message with the picture, no thinking, a JSON schema, few tokens."""
    request = json.loads(json.dumps(describe_request("vision", b"jpeg")))
    (message,) = request["messages"]
    assert message["images"] == [base64.b64encode(b"jpeg").decode()]
    assert request["think"] is False
    assert request["format"]["required"] == ["description", "tags"]
    assert request["options"]["temperature"] == 0


def test_a_description_is_read_trimmed_and_capped() -> None:
    """Tags beyond five are dropped; an answer outside the schema is None."""
    answer = json.dumps({"description": " A beach. ", "tags": list("abcdefg")})
    assert read_description(answer, 2.0) == Description("A beach.", tuple("abcde"), 2.0)
    assert read_description(json.dumps({"description": ""}), 1) is None
    assert read_description("not json", 1) is None
    assert read_description(json.dumps(["list"]), 1) is None
    assert read_description(json.dumps({"description": "x"}), 0) == Description("x")


def test_the_summary_adds_the_tags() -> None:
    """The mapping step reads the description and its tags."""
    assert Description("A beach.", ("sea",)).summary == "A beach. (sea)"
    assert Description("A beach.").summary == "A beach."


def test_the_map_request_numbers_descriptions_and_enumerates_categories() -> None:
    """One choice per description, from the categories or none."""
    request = json.loads(
        json.dumps(map_request("text", ["A beach.", "A choir."], CATEGORIES))
    )
    content = request["messages"][0]["content"]
    assert "1. A beach.\n2. A choir." in content
    items = request["format"]["properties"]["categories"]
    assert items["items"]["enum"] == [*CATEGORIES, NONE_ANSWER]
    assert items["minItems"] == items["maxItems"] == 2


def test_a_mapping_needs_one_known_choice_per_description() -> None:
    """Case is forgiven; a wrong count or an unknown category is refused."""
    assert read_mapping('{"categories": ["school", "none"]}', 2, CATEGORIES) == (
        "School",
        NONE,
    )
    assert read_mapping('{"categories": ["School"]}', 2, CATEGORIES) is None
    assert read_mapping('{"categories": ["Work", "School"]}', 2, CATEGORIES) is None
    assert read_mapping("[]", 0, CATEGORIES) is None


def test_a_prompt_version_follows_its_text() -> None:
    """Two prompts, two versions; the same prompt, the same version."""
    assert version("describe") != version("map")
    assert version("describe") == version("describe")
