"""An interrupted `tags` run keeps what was described; the next one goes on."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

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
        outcome = describe_photos(step, work, stop)
        show_described(runtime.output, outcome)
    assert outcome.stopped
    assert outcome.described == 2
    assert "the next tags run goes on" in output_of(runtime)
    with TagStep(runtime) as step:
        assert len(step.plan(()).missing) == ASKED - 2


class _Lines(NullProgress):
    """A progress that keeps each line said under the bar."""

    def __init__(self) -> None:
        """Start with no line."""
        self.lines: list[str] = []

    @override
    def current(self, text: str) -> None:
        """Keep the line.

        Args:
            text: The line.
        """
        self.lines.append(text)


def test_each_photo_described_says_its_words_on_the_progress_line(
    cli: CliRunner,
    locations: Locations,
    fake: FakeOllama,
) -> None:
    """The line under the bar names the last photo and its words (0421)."""
    del cli, fake  # the tree, audited; the model answering
    runtime = make_runtime(locations)
    progress = _Lines()
    with TagStep(runtime) as step:
        work = step.plan(())
        outcome = describe_photos(step, work, Answering(True, progress))  # noqa: FBT003
    assert len(progress.lines) == outcome.described > 0
    names = {photo.path.name for photo in work.missing}
    for line in progress.lines:
        name, _sep, words = line.partition(": ")
        assert name in names
        assert words
