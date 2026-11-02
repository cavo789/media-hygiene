"""A step the tool folders prove done is off, its reason dated (0540)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.actions.journal import journal_file
from media_hygiene.actions.kinds import ActionKind, Phase
from media_hygiene.cli.menu_steps import build_menu
from media_hygiene.cli.status_step import Slot
from media_hygiene.constants import CLASSIFY_PLAN_FILE_NAME
from media_hygiene.services.status import read_status
from tests.support.audit_summary import Found, write_audit
from tests.support.journaled import done_line
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.cli.menu_steps import MenuStep
    from media_hygiene.services.runtime import Runtime

_HINT: Final = 30
_FUTURE_SORT: Final = "20991231-120000"  # started after the proposal written now
# Steps that may run again once done: each run gives a new, useful result.
_REPEATABLE: Final = frozenset({Slot.AUDIT, Slot.CLASSIFY, Slot.TAGS, Slot.PEOPLE})


def _audit(runtime: Runtime, copies: int, broken: int = 0) -> None:
    """Write the summary of an audit of 2026-10-14."""
    write_audit(runtime, Found(copies, broken))


def _proposal(runtime: Runtime) -> None:
    """A classify proposal, written now."""
    folder = runtime.locations.reports_dir / "20261010-120000-classify"
    folder.mkdir()
    (folder / CLASSIFY_PLAN_FILE_NAME).write_text("{}", "utf-8")


def _sort_run(runtime: Runtime, moves: int) -> None:
    """A sort run after the proposal, that moved `moves` files."""
    lines = []
    for number in range(moves):
        entry = done_line(ActionKind.MOVE, f"/data/c/Photos/{number}.jpg")
        update = {"phase": Phase.SORT, "seq": number, "target": f"/data/c/S/{number}"}
        lines.append(entry.model_copy(update=update).model_dump_json())
    journal = journal_file(runtime.locations.journal_dir, _FUTURE_SORT)
    journal.write_text("".join(f"{line}\n" for line in lines), "utf-8")


def _by_slot(runtime: Runtime) -> dict[Slot, MenuStep]:
    """The menu's lines, by slot."""
    menu = build_menu(read_status(runtime), _HINT)
    return {line.step.slot: line for line in menu.steps if line.step.slot}


def test_clean_is_off_after_an_audit_with_nothing_to_set_aside(tmp_path: Path) -> None:
    """✅ and off, the audit's date in the reason; no number to type."""
    runtime = make_runtime(make_locations(tmp_path))
    _audit(runtime, 0)
    line = _by_slot(runtime)[Slot.CLEAN]
    assert line.done
    assert line.number is None
    assert "2026-10-14" in line.reason


def test_clean_stays_on_with_copies_or_broken_files(tmp_path: Path) -> None:
    """A broken file is something to set aside too: the same test as the command."""
    runtime = make_runtime(make_locations(tmp_path))
    _audit(runtime, 0, broken=2)
    line = _by_slot(runtime)[Slot.CLEAN]
    assert not line.done
    assert not line.reason
    assert line.number


def test_a_sort_that_moved_nothing_is_not_sorted(tmp_path: Path) -> None:
    """The proposal stays to apply."""
    runtime = make_runtime(make_locations(tmp_path))
    _proposal(runtime)
    _sort_run(runtime, 0)
    line = _by_slot(runtime)[Slot.SORT]
    assert not line.done
    assert not line.reason


def test_a_sort_that_moved_files_says_when_and_how_many(tmp_path: Path) -> None:
    """The reason names both days and the files moved."""
    runtime = make_runtime(make_locations(tmp_path))
    _proposal(runtime)
    _sort_run(runtime, 2)
    line = _by_slot(runtime)[Slot.SORT]
    assert line.done
    assert "2099-12-31" in line.reason
    assert "2 files moved" in line.reason
    assert "workbook" not in line.step.title


def test_a_done_step_is_off_unless_it_may_run_again(tmp_path: Path) -> None:
    """Every slot: done ⇒ a reason in place of its number, or repeatable."""
    runtime = make_runtime(make_locations(tmp_path))
    _audit(runtime, 0)
    _proposal(runtime)
    _sort_run(runtime, 1)
    for slot, line in _by_slot(runtime).items():
        if line.done and slot not in _REPEATABLE:
            assert line.reason, slot
            assert line.number is None, slot
