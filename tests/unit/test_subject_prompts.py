"""The questions asked to the model, and how its answers are read."""

from __future__ import annotations

import base64
import json

from media_hygiene.classify.ai.categories import Offered, names, offered
from media_hygiene.classify.ai.map_prompt import NONE_ANSWER, map_request, read_mapping
from media_hygiene.classify.ai.models import Description
from media_hygiene.classify.ai.prompts import (
    describe_name,
    describe_request,
    read_description,
    version,
)
from media_hygiene.classify.ai.subjects import NONE
from media_hygiene.constants import Locale

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
    assert version("describe_en") != version("map")
    assert version("describe_en") == version("describe_en")


def test_the_describe_prompt_follows_the_interface_language() -> None:
    """One prompt per language: another language is another cache identity."""
    assert describe_name(Locale.FR) == "describe_fr"
    assert version(describe_name(Locale.FR)) != version(describe_name(Locale.EN))
    request = describe_request("vision", b"jpeg", describe_name(Locale.FR))
    messages = request["messages"]
    assert isinstance(messages, list)
    assert "Réponds en français" in messages[0]["content"]


def test_a_category_entry_holds_a_name_and_an_optional_definition() -> None:
    """`Name = definition`: the name is the folder; a plain name has no definition."""
    assert offered("At home = games, meals") == Offered("At home", "games, meals")
    assert offered("At home = games, meals").line == "At home: games, meals"
    assert offered(" School ").line == "School"
    assert names(["At home = games", "School"]) == ("At home", "School")


def test_the_map_request_lists_definitions_and_enumerates_names() -> None:
    """The model reads the definition; it may answer the name only."""
    request = map_request("text", ["A sofa."], ["At home = games, meals", "School"])
    messages = request["messages"]
    assert isinstance(messages, list)
    assert "At home: games, meals\nSchool" in messages[0]["content"]
    assert json.loads(json.dumps(request["format"]))["properties"]["categories"][
        "items"
    ]["enum"] == ["At home", "School", NONE_ANSWER]
