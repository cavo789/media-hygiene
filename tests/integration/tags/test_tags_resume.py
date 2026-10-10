"""An interrupted `tags` run keeps what was described; the next one goes on."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.console.tags_view import show_described
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.subject_answers import Answering
from media_hygiene.services.tag_describe import describe_photos
from media_hygiene.services.tags import TagStep
from tests.integration.tags.test_tags_command import ASKED
from tests.support.runtime import make_runtime, output_of

if TYPE_CHECKING:
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from tests.support.fake_ollama import FakeOllama


def test_an_interrupted_run_resumes_where_it_stopped(
    cli: CliRunner,
    locations: Locations,
    fake: FakeOllama,
) -> None:
    """Stopped after two photos: they are kept; the next plan lacks the others."""
    del cli  # the tree, audited
    runtime = make_runtime(locations)
    with TagStep(runtime) as step:
        work = step.plan(())
        stop = Answering(
            describe=True,
            progress=NullProgress(),
            stopped=lambda: fake.described() >= 2,
        )
        outcome = describe_photos(step, work.missing, stop)
        show_described(runtime.output, outcome)
    assert outcome.stopped
    assert outcome.described == 2
    assert "the next tags run goes on" in output_of(runtime)
    with TagStep(runtime) as step:
        assert len(step.plan(()).missing) == ASKED - 2
