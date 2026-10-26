"""The audit run by `mh` offers to open `review --gone` at once."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest
import typer

from media_hygiene.cli import audit_gone
from media_hygiene.cli.audit_gone import offer_gone_review
from media_hygiene.console.output import Output
from media_hygiene.constants import ExitCode
from media_hygiene.services.next_command import LAUNCHER_VARIABLE
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True, slots=True)
class _Case:
    """Whether a terminal is there, and the answer typed."""

    terminal: bool
    yes: bool


def _offer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: _Case) -> list[str]:
    """Offer the review; the questions asked."""
    asked: list[str] = []

    def confirm(_output: Output, question: str) -> bool:
        asked.append(question)
        return case.yes

    monkeypatch.setattr(audit_gone, "has_terminal", lambda: case.terminal)
    monkeypatch.setattr(Output, "confirm", confirm)
    offer_gone_review(make_runtime(make_locations(tmp_path)))
    return asked


def test_a_yes_in_mh_ends_with_the_code_mh_follows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Under `mh`, in a terminal: a yes ends the audit with GONE_REVIEW."""
    monkeypatch.setenv(LAUNCHER_VARIABLE, "powershell")
    with pytest.raises(typer.Exit) as ended:
        _offer(tmp_path, monkeypatch, _Case(terminal=True, yes=True))
    assert ended.value.exit_code == ExitCode.GONE_REVIEW


def test_a_no_keeps_the_audit_a_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A no: the question asked, the audit ends normally."""
    monkeypatch.setenv(LAUNCHER_VARIABLE, "powershell")
    asked = _offer(tmp_path, monkeypatch, _Case(terminal=True, yes=False))
    assert asked == ["Open the review of the vanished files now?"]


def test_no_question_without_mh(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A plain `docker run` cannot serve the page."""
    monkeypatch.delenv(LAUNCHER_VARIABLE, raising=False)
    assert not _offer(tmp_path, monkeypatch, _Case(terminal=True, yes=True))


def test_no_question_without_a_terminal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No terminal: no one could answer."""
    monkeypatch.setenv(LAUNCHER_VARIABLE, "powershell")
    assert not _offer(tmp_path, monkeypatch, _Case(terminal=False, yes=True))
