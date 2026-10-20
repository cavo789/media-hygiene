"""`menu`: every step of the guides, the one proposed equal to the step of `status`."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Final

import pytest
from typer.testing import CliRunner

from media_hygiene.actions.journal import journal_file
from media_hygiene.actions.kinds import ActionKind, Phase
from media_hygiene.cli.app import build_app
from media_hygiene.cli.commands import commands
from media_hygiene.cli.menu_entry import Space
from media_hygiene.cli.menu_steps import build_menu, choice_lines
from media_hygiene.cli.menu_view import show_menu
from media_hygiene.cli.status_step import Slot, next_step
from media_hygiene.constants import CLASSIFY_PLAN_FILE_NAME, RunKind
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.status import read_status
from media_hygiene.services.update_check import UpdateNotice
from tests.support.journaled import done_line
from tests.support.runtime import make_locations, make_runtime, output_of

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime

_OLD_RUN: Final = "20200101-120000"
_HINT: Final = 30


def _decisions(runtime: Runtime, document: dict[str, object]) -> None:
    """Write `decisions.json` in the reports folder."""
    path = runtime.locations.reports_dir / "decisions.json"
    path.write_text(json.dumps({"version": 1, "roots": [], **document}), "utf-8")


def _report(runtime: Runtime, copies: int, *, backup_only: int = 0) -> None:
    """Write the summary of an audit that found `copies` extra copies."""
    folder = runtime.locations.reports_dir / "20261014-100000-audit"
    folder.mkdir()
    summary = {
        "folder": folder.name,
        "kind": RunKind.AUDIT.value,
        "created_at": "2026-10-14T10:00:00+00:00",
        "files_scanned": 10,
        "duplicate_groups": copies,
        "duplicate_files": copies,
        "reclaimable_bytes": 100,
        "broken_files": 0,
        "backup_only": backup_only,
    }
    (folder / "summary.json").write_text(json.dumps(summary), "utf-8")


def _blank(runtime: Runtime) -> None:
    """Nothing done yet."""
    del runtime


def _copies(runtime: Runtime) -> None:
    """An audit that found copies."""
    _report(runtime, 3)


def _bursts(runtime: Runtime) -> None:
    """A burst review left half way."""
    _report(runtime, 0)
    _decisions(runtime, {"bursts": [{"status": "todo", "kept": ["a.jpg"]}]})


def _decided(runtime: Runtime) -> None:
    """Shots set aside and near groups decided, not applied."""
    _report(runtime, 0)
    near = {"kept": "a.jpg", "copies": ["b.jpg"], "action": "planned"}
    bursts = [{"kept": ["c.jpg"], "discarded": ["d.jpg"]}]
    _decisions(runtime, {"bursts": bursts, "near": [near]})


def _old_quarantine(runtime: Runtime) -> None:
    """A quarantine older than `purge_hint_days`."""
    _report(runtime, 0)
    folder = runtime.locations.quarantine_dir / _OLD_RUN / "c"
    folder.mkdir(parents=True)
    (folder / "IMG_1.jpg").write_bytes(b"x")


def _proposal(runtime: Runtime) -> None:
    """A classify proposal not sorted."""
    _report(runtime, 0)
    folder = runtime.locations.reports_dir / "20261010-120000-classify"
    folder.mkdir()
    (folder / CLASSIFY_PLAN_FILE_NAME).write_text("{}", "utf-8")


def _nothing_left(runtime: Runtime) -> None:
    """An audit with no copy, nothing else."""
    _report(runtime, 0)


def _backup_only(runtime: Runtime) -> None:
    """An audit that saw files only the NAS holds, never imported."""
    _report(runtime, 0, backup_only=4)


def _imported(runtime: Runtime) -> None:
    """The same audit, then an `import` run."""
    _backup_only(runtime)
    entry = done_line(ActionKind.COPY_IN, "/data/c/Photos/From NAS/a.jpg")
    entry = entry.model_copy(update={"phase": Phase.IMPORT})
    journal = journal_file(runtime.locations.journal_dir, "20261015-090000")
    journal.write_text(entry.model_dump_json() + "\n", "utf-8")


_STATES: Final[dict[str, tuple[Callable[[Runtime], None], Slot | None, str]]] = {
    "blank": (_blank, Slot.AUDIT, "audit"),
    "copies": (_copies, Slot.CLEAN, "clean"),
    "bursts": (_bursts, Slot.REVIEW, "review"),
    "decided": (_decided, Slot.APPLY, "clean --tier near --decisions"),
    "old quarantine": (_old_quarantine, Slot.PURGE, f"purge {_OLD_RUN}"),
    "proposal": (_proposal, Slot.SORT, "sort"),
    "nothing left": (_nothing_left, None, ""),
    "backup only": (_backup_only, Slot.IMPORT, "import"),
}


@pytest.mark.parametrize("state", list(_STATES))
def test_the_proposed_step_is_the_step_of_status(tmp_path: Path, state: str) -> None:
    """One state each: 👉 on the slot `status` chooses, with its very command."""
    runtime = make_runtime(make_locations(tmp_path))
    prepare, slot, command = _STATES[state]
    prepare(runtime)
    status = read_status(runtime)
    menu = build_menu(status, _HINT)
    step = next_step(status, _HINT)
    proposed = menu.proposed
    if slot is None:
        assert step is None
        assert proposed is None
        assert all(not line.startswith("0\t") for line in choice_lines(menu))
        return
    assert step is not None
    assert proposed is not None
    assert (step.slot, step.command) == (slot, command)
    assert (proposed.step.slot, proposed.command) == (slot, command)
    assert choice_lines(menu)[0] == f"0\t{command}"
    assert f"{proposed.number}\t{command}" in choice_lines(menu)


def test_every_action_is_listed_once_by_space_and_numbered_across(
    tmp_path: Path,
) -> None:
    """The five stages, then the tools; numbers follow; typed and planned have none."""
    menu = build_menu(read_status(make_runtime(make_locations(tmp_path))), _HINT)
    spaces = [line.area.space for line in menu.steps]
    assert spaces == sorted(spaces, key=list(Space).index)
    assert spaces[0] is Space.IMPORT
    names = [line.step.name for line in menu.steps]
    assert len(names) == len(set(names))
    numbers = [line.number for line in menu.steps if line.number]
    assert numbers == list(range(1, len(numbers) + 1))
    for name in ("album", "nas-add", "backup", "backup-to"):
        line = next(line for line in menu.steps if line.step.name == name)
        assert line.number is None
        assert not line.command
    assert Space.OTHER not in spaces


def test_an_import_run_after_the_audit_ends_the_import_proposal(
    tmp_path: Path,
) -> None:
    """Once imported, the files only the NAS held are no longer proposed."""
    runtime = make_runtime(make_locations(tmp_path))
    _imported(runtime)
    status = read_status(runtime)
    assert status.imported == "20261015-090000"
    step = next_step(status, _HINT)
    assert step is None or step.slot is not Slot.IMPORT


def test_the_windows_actions_stay_out_of_the_bash_mh(tmp_path: Path) -> None:
    """phone, shortcut, explorer: PowerShell only."""
    status = read_status(make_runtime(make_locations(tmp_path)))
    windows = {line.step.name for line in build_menu(status, _HINT, windows=True).steps}
    bash = {line.step.name for line in build_menu(status, _HINT, windows=False).steps}
    only = {"phone", "phone-free", "shortcut", "explorer", "explorer-remove"}
    assert only <= windows
    assert not only & bash
    assert "open" in bash


def test_a_command_with_no_entry_shows_under_other_commands(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A new verb not in the catalog yet is still listed, with its help text."""
    real = commands()
    extra = ("teleport", real[0][1], real[0][2], "Send the photos to the Moon.")
    monkeypatch.setattr("media_hygiene.cli.menu_steps.commands", lambda: (*real, extra))
    runtime = make_runtime(make_locations(tmp_path))
    menu = build_menu(read_status(runtime), _HINT)
    line = menu.steps[-1]
    assert line.area.space is Space.OTHER
    assert (line.step.name, line.command) == ("teleport", "teleport")
    assert line.number
    show_menu(runtime, menu)
    shown = output_of(runtime)
    assert "Other commands" in shown
    assert "mh teleport" in shown
    assert "Send the photos to the Moon." in shown


def test_done_only_on_proof_and_arguments_from_the_state(tmp_path: Path) -> None:
    """Audit seen ✅, nothing else claimed; purge and undo take no run they lack."""
    runtime = make_runtime(make_locations(tmp_path))
    _old_quarantine(runtime)
    menu = build_menu(read_status(runtime), _HINT)
    by_slot = {line.step.slot: line for line in menu.steps if line.step.slot}
    assert by_slot[Slot.AUDIT].done
    assert by_slot[Slot.CLEAN].done  # the audit found no copy
    assert not by_slot[Slot.SORT].done
    assert not by_slot[Slot.TAGS].done
    assert by_slot[Slot.PURGE].command == f"purge {_OLD_RUN}"
    assert by_slot[Slot.UNDO].number is None


def test_the_screen_says_what_enter_runs(tmp_path: Path) -> None:
    """The commands to learn, the badges, and the line for Enter."""
    runtime = make_runtime(make_locations(tmp_path))
    _copies(runtime)
    show_menu(runtime, build_menu(read_status(runtime), _HINT))
    shown = output_of(runtime)
    assert "👉" in shown
    assert "mh audit" in shown
    assert "mh purge" in shown
    assert "(nothing to do yet)" in shown
    assert "(type it yourself)" in shown
    assert "(planned)" in shown
    assert "Import photos" in shown
    assert "From your NAS or an old disk" in shown
    assert "[classify.ai] model" in shown
    menu = build_menu(read_status(runtime), _HINT)
    assert menu.proposed is not None
    assert f"Enter runs step {menu.proposed.number} (mh clean)." in shown
    assert "🔒 your photos are not touched · ↩️ can be undone · ⚠️ for good" in shown


def test_a_newer_version_is_said_before_the_line_for_enter(tmp_path: Path) -> None:
    """0267: one line, the command to type; Enter's line stays the last."""
    runtime = make_runtime(make_locations(tmp_path))
    _copies(runtime)
    menu = build_menu(read_status(runtime), _HINT)
    show_menu(runtime, menu, UpdateNotice(version="0.5.0"))
    shown = output_of(runtime)
    assert "A new version, 0.5.0: mh update" in shown
    assert shown.index("A new version") < shown.index("Enter runs step")


def test_nothing_left_says_so(tmp_path: Path) -> None:
    """No proposal: no Enter line, the success said."""
    runtime = make_runtime(make_locations(tmp_path))
    _nothing_left(runtime)
    show_menu(runtime, build_menu(read_status(runtime), _HINT))
    shown = output_of(runtime)
    assert "Nothing left to do" in shown
    assert "Enter runs" not in shown


def test_the_command_writes_only_choices_on_stdout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """stdout: `number<TAB>command` lines only; tool folders missing, no traceback."""
    for kind in (MountKind.CONFIG, MountKind.CACHE, MountKind.REPORTS):
        folder = tmp_path / kind.value
        folder.mkdir()
        monkeypatch.setenv(f"MEDIA_HYGIENE_{kind.value.upper()}_DIR", str(folder))
    result = CliRunner().invoke(build_app(), ["menu"])
    assert result.exit_code == 0, result.output
    lines = result.stdout.splitlines()
    assert lines
    assert all(line.split("\t")[0].isdigit() for line in lines)
    assert lines[0] == "0\taudit"
    assert "Traceback" not in result.stderr
    assert "Not looked at (not mounted): /journal, /quarantine." in result.stderr
    assert "write it once with 'launcher'" in result.stderr


def test_on_a_terminal_the_menu_is_shown_without_choices(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`docker run -it … menu`: one screen, the menu on it, no line for `mh`."""
    monkeypatch.setenv("MEDIA_HYGIENE_CONFIG_DIR", str(tmp_path))
    monkeypatch.setattr("media_hygiene.console.output.data_on_terminal", lambda: True)
    result = CliRunner().invoke(build_app(), ["menu"])
    assert result.exit_code == 0, result.output
    assert "\t" not in result.stdout
    assert "mh audit" in result.stderr
    assert "then type mh menu" in result.stderr
