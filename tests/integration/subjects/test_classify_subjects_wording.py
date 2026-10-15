"""`classify` explains the numbers of its `subject` lines: groups, samples, cache."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.support.cli import run
from tests.support.fake_ollama import describe, images, map_answer

if TYPE_CHECKING:
    from typer.testing import CliRunner

    from tests.support.fake_ollama import FakeOllama


def test_the_lines_name_groups_samples_and_files(cli: CliRunner) -> None:
    """Three events, three samples each; every group gets a subject."""
    result = run(cli, "classify")
    assert result.exit_code == 0, result.output
    text = " ".join(result.output.split())
    assert "3 groups of photos (events or lone photos) no rule of yours took" in text
    assert "will look at 9 of them (up to 3 per event, the others follow)" in text
    assert "9 to describe with vision, about" in text
    assert "already in the cache" not in text
    assert "Rule 'Subject': 15 files sorted by what the model saw." in text


def test_the_cache_and_the_groups_without_a_subject_are_counted(
    cli: CliRunner, fake: FakeOllama
) -> None:
    """Two photos described by --sample; the cake event mapped to none."""

    def answer(body: dict[str, object]) -> dict[str, object]:
        if images(body):
            return describe(body)
        chosen = map_answer(body)["categories"]
        assert isinstance(chosen, list)
        return {"categories": [c if c != "Parties" else "none" for c in chosen]}

    fake.answer = answer  # before --sample: its mappings are cached too
    assert run(cli, "classify", "--sample", "2").exit_code == 0
    result = run(cli, "classify")
    assert result.exit_code == 0, result.output
    text = " ".join(result.output.split())
    assert "7 to describe with vision (2 already in the cache)" in text, result.output
    assert "10 files sorted by what the model saw; 1 group without a subject" in text
    assert "your other rules, else To sort." in text


def test_no_describe_announces_no_work(cli: CliRunner, fake: FakeOllama) -> None:
    """`--no-describe`: no time to wait for, only what stays undescribed."""
    assert run(cli, "classify", "--sample", "2").exit_code == 0
    result = run(cli, "classify", "--no-describe")
    assert result.exit_code == 0, result.output
    text = " ".join(result.output.split())
    assert "to describe with" not in text
    assert "7 samples not described yet (--no-describe)" in text, result.output
    assert fake.described() == 2
