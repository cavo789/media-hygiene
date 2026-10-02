"""`classify` and a fake model that misbehaves, or settings that change the run."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.support.cli import run
from tests.support.fake_ollama import FakeOllama, describe, images, map_answer

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations


def test_answers_outside_the_schema_describe_nothing(
    cli: CliRunner, fake: FakeOllama
) -> None:
    """Every photo said; no subject; the other rules decide."""
    fake.answer = lambda _body: {"text": "no schema"}
    result = run(cli, "classify")
    assert result.exit_code == 0, result.output
    assert "9 photos could not be described" in result.output
    assert "decided nothing: Subject" in result.output
    assert fake.mapped() == 0


def test_a_server_error_stops_the_run_and_names_it(
    cli: CliRunner, fake: FakeOllama
) -> None:
    """A 500, retried, then the error; nothing is proposed."""
    fake.chat_status = 500
    result = run(cli, "classify")
    assert result.exit_code == 1
    assert "answered 500" in result.output


def test_an_unusable_batch_is_mapped_one_description_at_a_time(
    cli: CliRunner, fake: FakeOllama
) -> None:
    """A batch answer with a choice missing: each description is asked alone."""

    def answer(body: dict[str, object]) -> dict[str, object]:
        if images(body):
            return describe(body)
        chosen = map_answer(body)["categories"]
        assert isinstance(chosen, list)
        return {"categories": chosen[:-1] if len(chosen) > 1 else chosen}

    fake.answer = answer
    result = run(cli, "classify")
    assert result.exit_code == 0, result.output
    assert fake.mapped() == 1 + 3  # the batch, then its three descriptions
    assert "a subject for 15 files" in result.output


def test_a_subject_rule_without_a_model_says_where_to_set_it(
    cli: CliRunner, fake: FakeOllama, locations: Locations
) -> None:
    """`model = ""` is the default: no photo is sent."""
    config = locations.config_dir / "config.toml"
    config.write_text(config.read_text().replace('model = "vision"', 'model = ""'))
    result = run(cli, "classify")
    assert result.exit_code == 1
    assert "needs a vision model" in result.output
    assert "[classify.ai] model" in result.output
    assert fake.calls == []


def test_without_a_cache_the_descriptions_live_for_one_run(
    cli: CliRunner, fake: FakeOllama, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The run still works, in memory; a tip says how to keep them."""
    monkeypatch.delenv("MEDIA_HYGIENE_CACHE_DIR")
    result = run(cli, "classify")
    assert result.exit_code == 0, result.output
    assert ":/cache" in result.output
    assert fake.described() == 9
    assert "a subject for 15 files" in result.output


def test_per_photo_describes_every_photo(
    cli: CliRunner, fake: FakeOllama, locations: Locations
) -> None:
    """15 photos, 15 descriptions; nothing left to describe for --sample."""
    config = locations.config_dir / "config.toml"
    config.write_text(config.read_text() + "per_photo = true\n")
    result = run(cli, "classify")
    assert result.exit_code == 0, result.output
    assert fake.described() == 15
    sample = run(cli, "classify", "--sample", "3")
    assert sample.exit_code == 0, sample.output
    assert "every candidate is in the cache" in sample.output
    assert fake.described() == 15
