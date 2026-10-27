"""`tags` run by the home page (0343): figures first, then the model, Stop, resume."""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING

from media_hygiene.cli.home_tags import page_tags
from media_hygiene.review.home_tags_api import TAGS_PATH
from media_hygiene.services.home_audit import AuditResult, HomeAudit
from media_hygiene.services.home_tags import HomeTags
from media_hygiene.services.home_tags_models import TagFigures, TagsPhase, TagsRunner
from media_hygiene.services.tags import TagStep
from tests.integration.tags.test_tags_command import ASKED
from tests.integration.test_home_page import serve
from tests.support.home_app import home_app_of
from tests.support.review import JSON_HEADERS, Call
from tests.support.runtime import make_runtime
from tests.support.tagging import write_tags_config

_POLL = 0.01

if TYPE_CHECKING:
    from collections.abc import Callable

    from typer.testing import CliRunner

    from media_hygiene.console.page_progress import PageProgress
    from media_hygiene.paths.locations import Locations
    from tests.support.fake_ollama import FakeOllama


def _wait(tags: HomeTags) -> None:
    """Wait for the half running to end, as the page polls."""
    while tags.state().phase in {TagsPhase.PREPARING, TagsPhase.RUNNING}:
        time.sleep(_POLL)


def test_the_page_asks_with_figures_then_describes_and_resumes(
    cli: CliRunner, locations: Locations, fake: FakeOllama
) -> None:
    """Prepare: no model call, its figures; a stop keeps; the next run goes on."""
    del cli  # the tree, audited
    runtime = make_runtime(locations)
    tags = HomeTags(page_tags(runtime))
    assert not tags.describe(None)  # nothing prepared yet
    assert tags.prepare()
    _wait(tags)
    state = tags.state()
    assert state.phase is TagsPhase.ASKING, state.error
    assert state.figures is not None
    assert state.figures.to_describe == ASKED
    assert state.figures.model
    assert fake.calls == []  # the figures never ask the model
    holder = {"limit": 2}
    real = page_tags(runtime)

    def some(progress: PageProgress, stopped: Callable[[], bool]) -> tuple[str, ...]:
        """The real model's half, stopped after `limit` photos as by Stop."""
        limit = holder["limit"]
        return real.describe(progress, lambda: stopped() or fake.described() >= limit)

    tags = HomeTags(TagsRunner(real.prepare, some))
    assert tags.prepare()
    _wait(tags)
    assert tags.describe(60)
    _wait(tags)
    assert tags.state().phase is TagsPhase.DONE, tags.state().error
    assert fake.described() == 2
    with TagStep(runtime) as step:
        assert len(step.plan(()).missing) == ASKED - 2
    holder["limit"] = ASKED + 1
    assert tags.prepare()
    _wait(tags)
    assert tags.describe(None)
    _wait(tags)
    assert tags.state().phase is TagsPhase.DONE
    with TagStep(runtime) as step:
        assert not step.plan(()).missing


def test_ollama_absent_is_one_line(
    cli: CliRunner, locations: Locations, fake: FakeOllama
) -> None:
    """The model's server gone: the page says it, never a traceback."""
    del cli, fake
    write_tags_config(locations.config_dir, "http://127.0.0.1:9")  # nobody listens
    tags = HomeTags(page_tags(make_runtime(locations)))
    assert tags.prepare()
    _wait(tags)
    assert tags.describe(None)
    _wait(tags)
    state = tags.state()
    assert state.phase is TagsPhase.FAILED
    assert state.error
    assert "Traceback" not in state.error


def _figures(progress: PageProgress) -> TagFigures:
    del progress
    return TagFigures(files=3, to_describe=2, seconds_per_photo=1.0, model="m")


def _endless(progress: PageProgress, stopped: Callable[[], bool]) -> tuple[str, ...]:
    while not stopped():
        progress.current("…")
    return ("stopped",)


def _ask(body: dict[str, object]) -> Call:
    return Call("POST", TAGS_PATH, json.dumps(body).encode(), JSON_HEADERS)


def test_the_tags_routes(locations: Locations) -> None:
    """Prepare, describe, refuse a second start, stop; bad bodies refused."""
    runtime = make_runtime(locations)
    tags = HomeTags(TagsRunner(_figures, _endless))
    audit = HomeAudit(lambda _progress: AuditResult(lines=()))
    first, code = serve(
        home_app_of(runtime, audit, tags),
        [Call("GET", TAGS_PATH), _ask({"action": "prepare"})],
    )
    assert code is None
    _wait(
        tags
    )  # the prepare thread ends first: on a slow runner, describe would race it
    replies, code = serve(
        home_app_of(runtime, audit, tags),
        [
            Call("GET", TAGS_PATH),
            _ask({"action": "describe", "minutes": 0}),
            _ask({"action": "describe"}),
            _ask({"action": "describe"}),
            _ask({"action": "stop"}),
        ],
    )
    idle, _prepared = first
    _asking, bad, running, again, stop = replies
    assert code is None
    assert idle.json()["phase"] == "idle"  # type: ignore[index]
    assert bad.status == 400
    assert running.json()["phase"] == "running"  # type: ignore[index]
    assert again.status == 409
    assert stop.json()["phase"] == "stopped"  # type: ignore[index]
    assert stop.json()["lines"] == ["stopped"]  # type: ignore[index]


def test_the_time_limit_stops_the_run() -> None:
    """`Describe for 1 h`: the run stops by itself once the time is up."""
    tags = HomeTags(TagsRunner(_figures, _endless))
    assert tags.prepare()
    _wait(tags)
    assert tags.describe(0)  # the time is up at once
    _wait(tags)
    assert tags.state().phase is TagsPhase.DONE
