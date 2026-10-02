"""The `subject` rule: its fields, its place among the rules, its confidence."""

# classify works on naive local dates, as EXIF writes them.
# ruff: noqa: DTZ001

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from media_hygiene.classify.ai.models import Subject
from media_hygiene.classify.engine import Scope, classify
from media_hygiene.classify.models import Band, MediaInput, SortReason
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.config.classify_ai import AiSettings
from media_hygiene.config.classify_rules import ClassifyRule
from media_hygiene.config.classify_settings import ClassifySettings
from media_hygiene.config.layers import read_env_layer
from media_hygiene.scan.models import VisualFacts

if TYPE_CHECKING:
    from media_hygiene.classify.models import Proposal

ROOT = Path("/data/c/Photos")
SUBJECT = ClassifyRule(
    name="Subject", match=RuleMatch.SUBJECT, categories=("Holidays", "School")
)


def test_a_subject_rule_needs_categories_and_no_category() -> None:
    """The model chooses among `categories`; `category` and placeholders are refused."""
    with pytest.raises(ValidationError, match="needs categories"):
        ClassifyRule(name="S", match=RuleMatch.SUBJECT)
    with pytest.raises(ValidationError, match="category is not used"):
        ClassifyRule(name="S", match=RuleMatch.SUBJECT, categories=("A",), category="B")
    for bad in ("", "Trips {year}", "A:B"):
        with pytest.raises(ValidationError, match="rule 'S'"):
            ClassifyRule(name="S", match=RuleMatch.SUBJECT, categories=(bad,))


def test_only_a_subject_rule_takes_categories_and_per_photo() -> None:
    """Elsewhere they would be silently ignored: refused instead."""
    with pytest.raises(ValidationError, match="per_photo is not used"):
        ClassifyRule(name="P", match=RuleMatch.PATH, pattern="x", per_photo=True)
    with pytest.raises(ValidationError, match="categories is not used"):
        ClassifyRule(name="P", match=RuleMatch.PATH, pattern="x", categories=("A",))


def test_the_model_settings_come_from_one_json_variable() -> None:
    """`[classify.ai]` is a table: one JSON object replaces it."""
    layer = read_env_layer({"MEDIA_HYGIENE_CLASSIFY__AI": '{"model": "qwen"}'})
    settings = ClassifySettings.model_validate(layer["classify"])
    assert settings.ai == AiSettings(model="qwen")
    assert settings.ai.text_model == "qwen"
    assert AiSettings(model="a", map_model="b").text_model == "b"


def event(folder: str) -> list[MediaInput]:
    """Five photos of one day, one hour apart."""
    start = datetime(2021, 7, 14, 10)
    files = []
    for index in range(5):
        taken = (start + timedelta(hours=index)).strftime("%Y:%m:%d %H:%M:%S")
        visual = VisualFacts(0, 0, 1024, 768, 1.0, taken, "Canon")
        files.append(MediaInput(ROOT / folder / f"{index}.jpg", ROOT, 10, 0, visual))
    return files


def proposals(subject: Subject, *rules: ClassifyRule) -> list[Proposal]:
    """Classify one event whose files all got this subject."""
    files = event("DCIM")
    subjects = {"Subject": {file.path: subject for file in files}}
    settings = ClassifySettings(rules=rules or (SUBJECT,))
    return list(classify(files, settings, Scope(subjects=subjects)).proposals)


def test_agreed_samples_are_sure_others_to_check() -> None:
    """3 of 3 reach `sure`; a disagreement is capped at `unsure`."""
    sure = proposals(Subject("Holidays", agreed=True))[0]
    assert (sure.band, sure.reason, sure.rule) == (
        Band.SURE,
        SortReason.SUBJECT,
        "Subject",
    )
    assert sure.folder == "2021/Holidays"
    unsure = proposals(Subject("Holidays", agreed=False))[0]
    assert (unsure.band, unsure.verdict.score) == (Band.UNSURE, 50)
    assert unsure.folder == "2021/To check/Holidays"


def test_a_rule_above_the_subject_wins_and_score_zero_turns_it_off() -> None:
    """Rules are read in order: the model is asked last."""
    summer = ClassifyRule(
        name="Summer",
        match=RuleMatch.DATE_RANGE,
        dates="2021-07-01..2021-07-31",
        category="Summer",
    )
    first = proposals(Subject("Holidays", agreed=True), summer, SUBJECT)[0]
    assert first.rule == "Summer"
    off = SUBJECT.model_copy(update={"score": 0})
    assert proposals(Subject("Holidays", agreed=True), off)[0].reason is (
        SortReason.NO_SIGNAL
    )
