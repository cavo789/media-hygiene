"""The home page runs the audit itself: same findings, steps in order, one at a time."""

from __future__ import annotations

import json
import threading
from functools import partial
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest

from media_hygiene.cli.audit_actions import action_list
from media_hygiene.cli.home_audit import page_audit
from media_hygiene.cli.home_state import home_state
from media_hygiene.console.page_progress import (
    AuditPhase,
    AuditStoppedError,
    PageProgress,
)
from media_hygiene.constants import Locale
from media_hygiene.i18n import install
from media_hygiene.report.index_page import load_summaries
from media_hygiene.review.home_app import AUDIT_PATH, HomeApp
from media_hygiene.scan import stopwatch
from media_hygiene.scan.progress import NullProgress, Step
from media_hygiene.services.audit import AuditService
from media_hygiene.services.home import home_page
from media_hygiene.services.home_audit import AuditResult, HomeAudit
from tests.integration.test_home_page import serve
from tests.support.cli import run
from tests.support.review import JSON_HEADERS, Call
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations

_LISTING = "Listing media files"


def ask(action: str, headers: tuple[str, ...] = JSON_HEADERS) -> Call:
    """`POST /api/audit`, as the page sends it."""
    return Call("POST", AUDIT_PATH, json.dumps({"action": action}).encode(), headers)


def test_the_page_audit_finds_what_audit_finds(
    cli: CliRunner, locations: Locations
) -> None:
    """Same copies and actions as `audit`; the steps reported in order, a report."""
    runtime = make_runtime(locations)
    audit = HomeAudit(page_audit(runtime))
    assert audit.state().phase is AuditPhase.IDLE
    assert audit.start()
    audit.wait()
    state = audit.state()
    assert state.phase is AuditPhase.DONE, state.error
    assert state.report == home_state(runtime).reports[0].url
    assert run(cli, "audit").exit_code == 0
    by_page, by_command = (
        summary.model_dump(exclude={"created_at", "folder"})
        for summary in load_summaries(locations.reports_dir)[1::-1]
    )
    assert by_page == by_command
    assert by_page["duplicate_files"]
    findings = AuditService(make_runtime(locations), NullProgress()).run()
    actions = action_list(runtime, findings)
    assert state.actions == tuple(f"{a.icon} {a.text}" for a in actions)
    titles = [step.title for step in state.steps]
    assert titles[0] == _LISTING
    assert all(step.finished for step in state.steps)
    assert state.report is not None
    assert state.report.endswith("/report.html")


def test_the_page_audit_ends_on_the_console_time_per_step(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0241: the line `audit -v` prints, same words and rounding, once it is done."""
    monkeypatch.setattr(stopwatch, "time", SimpleNamespace(monotonic=lambda: 0.0))
    audit = HomeAudit(page_audit(make_runtime(locations)))
    assert audit.start()
    assert audit.state().timed is None  # nothing while it runs
    audit.wait()
    state = audit.state()
    assert state.phase is AuditPhase.DONE, state.error
    assert state.timed is not None
    assert state.timed.startswith("Time per step: listing 0.0 s · ")
    console = run(cli, "--verbosity", "verbose", "audit").output
    assert state.timed in " ".join(console.split())


def test_no_time_per_step_after_a_stop_or_a_failure() -> None:
    """0241: a stopped or failed audit shows no time line."""

    def stopped(_progress: PageProgress) -> AuditResult:
        raise AuditStoppedError

    def broken(_progress: PageProgress) -> AuditResult:
        raise OSError

    for run_ in (stopped, broken):
        audit = HomeAudit(run_)
        assert audit.start()
        audit.wait()
        state = audit.state()
        assert state.phase is not AuditPhase.DONE
        assert state.timed is None
        assert "timed" not in state.model_dump(exclude_none=True)


@pytest.mark.usefixtures("cli")
def test_the_page_audit_speaks_the_language_installed(locations: Locations) -> None:
    """Its thread reads the language `install()` chose: steps and summary in French.

    The maintainer's French page showed "Listing media files — 51,818" and "Last
    audit: …": the thread started with an empty context, hence English.
    """
    install(Locale.FR)
    audit = HomeAudit(page_audit(make_runtime(locations)))
    assert audit.start()
    audit.wait()
    state = audit.state()
    assert state.phase is AuditPhase.DONE, state.error
    assert state.steps[0].title == "Recherche des fichiers médias"
    assert state.lines
    assert state.lines[0].startswith("Dernier audit"), state.lines
    assert not any("Last audit" in line for line in state.lines)


def test_a_second_start_is_refused_while_one_runs() -> None:
    """One audit at a time; a stop ends it between two files."""
    started = threading.Event()

    def endless(progress: PageProgress) -> AuditResult:
        progress.start(Step("Checking"), None)
        started.set()
        while True:
            progress.advance()

    audit = HomeAudit(endless)
    assert audit.start()
    started.wait(5)
    assert not audit.start()
    assert audit.state().phase is AuditPhase.RUNNING
    assert audit.state().steps[0].done >= 0
    audit.stop()
    state = audit.state()
    assert state.phase is AuditPhase.STOPPED
    assert state.steps[0].finished
    assert audit.start()  # stopped: a new one may start
    audit.stop()


@pytest.mark.usefixtures("cli")
def test_a_stop_leaves_an_index_the_next_audit_reuses(locations: Locations) -> None:
    """Stopped at its first step, the audit raises; the next one runs and finds all."""
    runtime = make_runtime(locations)
    progress = PageProgress()
    progress.request_stop()
    with pytest.raises((AuditStoppedError, ExceptionGroup)):
        page_audit(runtime)(progress)
    audit = HomeAudit(page_audit(runtime))
    assert audit.start()
    audit.wait()
    assert audit.state().phase is AuditPhase.DONE


def test_a_failure_is_said_without_a_traceback() -> None:
    """An unexpected error ends the audit as failed, the page told in one line."""

    def broken(_progress: PageProgress) -> AuditResult:
        raise OSError

    audit = HomeAudit(broken)
    assert audit.start()
    audit.wait()
    state = audit.state()
    assert state.phase is AuditPhase.FAILED
    assert state.error


@pytest.mark.usefixtures("cli")
def test_the_audit_routes(locations: Locations) -> None:
    """Start, refuse a second start, stop; forms and other bodies refused."""
    runtime = make_runtime(locations)
    started = threading.Event()

    def endless(progress: PageProgress) -> AuditResult:
        started.set()
        while True:
            progress.advance()

    audit = HomeAudit(endless)
    form = ("Host: 127.0.0.1", "Content-Type: application/x-www-form-urlencoded")
    replies, code = serve(
        lambda ending: HomeApp(
            home_page(),
            partial(home_state, runtime),
            runtime.locations.reports_dir,
            ending,
            audit,
        ),
        [
            Call("GET", AUDIT_PATH),
            ask("start"),
            ask("start"),
            ask("start", form),
            Call("POST", AUDIT_PATH, b'{"action": "dance"}', JSON_HEADERS),
            ask("stop"),
            Call("GET", AUDIT_PATH),
        ],
    )
    idle, start, again, refused, bad, stop, after = replies
    assert code is None
    assert idle.json()["phase"] == "idle"  # type: ignore[index]
    assert start.json()["phase"] == "running"  # type: ignore[index]
    assert again.status == 409
    assert (refused.status, bad.status) == (415, 400)
    assert stop.json()["phase"] == "stopped"  # type: ignore[index]
    assert after.json()["phase"] == "stopped"  # type: ignore[index]
    assert started.is_set()
