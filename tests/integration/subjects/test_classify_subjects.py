"""`classify` asks a fake local model: describe, map, cache, resume, refusals."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.classify import ClassifyService
from media_hygiene.services.classify_subjects import SubjectStep
from media_hygiene.services.subject_answers import Answering
from tests.support.cli import run
from tests.support.runtime import make_runtime
from tests.support.subjects import CATEGORIES, write_config, write_events

if TYPE_CHECKING:
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from tests.support.fake_ollama import FakeOllama


def test_samples_are_described_mapped_then_read_from_the_cache(
    cli: CliRunner, fake: FakeOllama
) -> None:
    """3 samples per event; the next run, and --no-describe, ask nothing new."""
    first = run(cli, "classify")
    assert first.exit_code == 0, first.output
    assert fake.described() == 9
    assert "9 photos described" in first.output
    assert "Sure │    15" in first.output  # 3 of 3 agree in every event
    for category in CATEGORIES:  # each event, whole, in its category
        assert re.search(rf"{category}\s+│\s+5 ", first.output)
    asked = len(fake.calls)
    again = run(cli, "classify")
    assert again.exit_code == 0, again.output
    assert len(fake.calls) == asked  # descriptions and mappings: all cached
    assert run(cli, "classify", "--no-describe").exit_code == 0
    assert len(fake.calls) == asked


def test_a_model_without_vision_is_refused_by_name(
    cli: CliRunner, fake: FakeOllama
) -> None:
    """Nothing is described; the message names the model."""
    fake.capabilities = ("completion",)
    result = run(cli, "classify")
    assert result.exit_code == 1
    assert "The model vision cannot see images" in result.output
    assert fake.described() == 0


def test_a_long_run_asks_first_and_keeps_to_the_cache_when_refused(
    cli: CliRunner, fake: FakeOllama, locations: Locations
) -> None:
    """Without a terminal the answer is no: the cache only; --yes describes."""
    write_config(locations.config_dir, fake.url, "confirm_above = 2")
    refused = run(cli, "classify")
    assert refused.exit_code == 0, refused.output
    assert fake.described() == 0
    assert "--sample 50" in refused.output
    accepted = run(cli, "classify", "--yes")
    assert accepted.exit_code == 0, accepted.output
    assert fake.described() == 9


def test_a_sample_is_timed_and_kept(cli: CliRunner, fake: FakeOllama) -> None:
    """Two photos: their table, the time per photo, the estimate; no workbook."""
    result = run(cli, "classify", "--sample", "2")
    assert result.exit_code == 0, result.output
    assert fake.described() == 2
    assert "Per photo" in result.output
    assert "A full run would describe" in result.output
    assert "Workbook" not in result.output


def test_without_a_subject_rule_nothing_is_sent(
    cli: CliRunner, fake: FakeOllama, locations: Locations
) -> None:
    """The default rules: the tool works fully without a model."""
    (locations.config_dir / "config.toml").unlink()
    result = run(cli, "classify")
    assert result.exit_code == 0, result.output
    assert fake.calls == []


def test_an_interrupted_run_resumes_where_it_stopped(
    locations: Locations, fake: FakeOllama
) -> None:
    """Stopped after two photos: they are kept; the next run describes the rest."""
    write_events(locations.data_dir)
    write_config(locations.config_dir, fake.url)
    runtime = make_runtime(locations)
    AuditService(runtime, NullProgress()).run()
    inputs = ClassifyService(runtime, NullProgress()).collect()
    with SubjectStep(runtime) as step:
        plan = step.plan(inputs)
        stop = Answering(
            describe=True,
            progress=NullProgress(),
            stopped=lambda: fake.described() >= 2,
        )
        answered = step.answer(plan, stop)
    assert answered.outcome.stopped
    assert answered.outcome.described == 2
    with SubjectStep(runtime) as step:
        plan = step.plan(inputs)
        assert len(plan.missing) == 7
        answered = step.answer(plan, Answering(describe=True, progress=NullProgress()))
    assert fake.described() == 9
    assert len(answered.subjects["Subject"]) == 15
