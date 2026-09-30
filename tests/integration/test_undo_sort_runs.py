"""`undo` of a sort resumed over several runs: every run of the plan, one question."""

from __future__ import annotations

import shutil
from types import SimpleNamespace
from typing import TYPE_CHECKING

from media_hygiene.actions.journal import JournalEntry, JournalWriter, journal_file
from media_hygiene.actions.kinds import ActionKind, Phase, Status
from media_hygiene.actions.plan_runs import runs_of_plan
from media_hygiene.actions.runs import list_run_ids
from tests.support.cli import run
from tests.support.runtime import make_runtime
from tests.support.sorting import (
    build_library,
    classify,
    folders,
    name_first_event,
    snapshot,
    sort_in_two_runs,
    undo,
)

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from media_hygiene.services.runtime import Runtime

type Library = tuple[dict[str, tuple[str, int]], set[str]]


def sorted_twice(locations: Locations) -> tuple[Runtime, Library]:
    """The library alone, classified, then sorted in two runs; its state before."""
    shutil.rmtree(locations.data_dir)
    build_library(locations.data_dir)
    before = snapshot(locations.data_dir), folders(locations.data_dir)
    runtime = make_runtime(locations)
    name_first_event(classify(runtime))
    sort_in_two_runs(runtime)
    return runtime, before


def answer_yes(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """A terminal whose user answers yes; the questions asked."""
    asked: list[str] = []
    terminal = SimpleNamespace(stdin=SimpleNamespace(isatty=lambda: True))
    monkeypatch.setattr("media_hygiene.cli.cmd_undo.sys", terminal)

    def confirm(_self: object, question: str) -> bool:
        asked.append(question)
        return True

    monkeypatch.setattr("media_hygiene.console.output.Output.confirm", confirm)
    return asked


def test_one_undo_one_question_every_file_back(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Both runs listed, one question, every file back byte- and mtime-identical."""
    _runtime, (files, tree) = sorted_twice(locations)
    newest, older = list_run_ids(locations.journal_dir)
    asked = answer_yes(monkeypatch)
    result = run(cli, "undo")
    assert result.exit_code == 0, result.output
    assert len(asked) == 1
    assert "Undo these 2 runs" in asked[0]
    assert newest in result.output
    assert older in result.output
    assert "Undo the 2 runs of the sort" in result.output
    assert snapshot(locations.data_dir) == files
    assert folders(locations.data_dir) == tree
    again = run(cli, "undo", "--yes")  # all undone: the latest run alone, nothing to do
    assert again.exit_code == 0, again.output
    assert "Undo the sort run" in again.output


def test_without_a_terminal_it_refuses_and_changes_nothing(
    cli: CliRunner, locations: Locations
) -> None:
    """No terminal and no --yes: refused before the first file moves."""
    sorted_twice(locations)
    moved = snapshot(locations.data_dir)
    result = run(cli, "undo")
    assert result.exit_code == 1
    assert "--yes" in result.output
    assert snapshot(locations.data_dir) == moved


def test_a_no_changes_nothing(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Anything but yes at the question: nothing moves back."""
    sorted_twice(locations)
    moved = snapshot(locations.data_dir)
    terminal = SimpleNamespace(stdin=SimpleNamespace(isatty=lambda: True))
    monkeypatch.setattr("media_hygiene.cli.cmd_undo.sys", terminal)
    monkeypatch.setattr(
        "media_hygiene.console.output.Output.confirm", lambda _self, _question: False
    )
    result = run(cli, "undo")
    assert result.exit_code == 0, result.output
    assert "Nothing was changed" in result.output
    assert snapshot(locations.data_dir) == moved


def test_naming_the_first_run_starts_from_the_later_one(
    cli: CliRunner, locations: Locations
) -> None:
    """`undo <first run>`: the later run of the plan goes back first, and it says so."""
    _runtime, (files, tree) = sorted_twice(locations)
    newest, older = list_run_ids(locations.journal_dir)
    result = run(cli, "undo", "--yes", older)
    assert result.exit_code == 0, result.output
    assert f"Run {newest} of the same sort came after {older}" in " ".join(
        result.output.split()
    )
    assert snapshot(locations.data_dir) == files
    assert folders(locations.data_dir) == tree


def test_a_run_already_undone_is_left_aside(
    cli: CliRunner, locations: Locations
) -> None:
    """The last run undone alone: `undo` walks on with the earlier one, and says so."""
    runtime, (files, tree) = sorted_twice(locations)
    newest, older = list_run_ids(locations.journal_dir)
    assert not undo(runtime, newest).failed
    plan = runs_of_plan(locations.journal_dir, newest)
    assert [each.run_id for each in plan.runs] == [older]
    assert plan.undone == (newest,)
    result = run(cli, "undo", "--yes")
    assert result.exit_code == 0, result.output
    output = " ".join(result.output.split())
    assert f"Run {newest} of the same sort was already undone" in output
    assert snapshot(locations.data_dir) == files
    assert folders(locations.data_dir) == tree


def test_the_runs_of_another_sort_stay(locations: Locations) -> None:
    """A run of another workbook, older, is not part of this sort's undo."""
    sorted_twice(locations)
    foreign = JournalEntry(
        seq=1,
        phase=Phase.SORT,
        status=Status.DONE,
        action=ActionKind.MOVE,
        path="/data/c/elsewhere.jpg",
        host_path="C:\\elsewhere.jpg",
        size=1,
        mtime_ns=1,
        plan="another plan",
    )
    other = journal_file(locations.journal_dir, "20000101-000000")
    with JournalWriter.open(other) as journal:
        journal.record(foreign)
    newest, older, _foreign = list_run_ids(locations.journal_dir)
    plan = runs_of_plan(locations.journal_dir, older)
    assert [each.run_id for each in plan.runs] == [newest, older]
    assert plan.later == newest
    assert plan.together
