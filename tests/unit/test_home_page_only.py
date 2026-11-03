"""The steps the home page already shows stay in `mh menu`, not on the page (0504)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.cli import home_folders
from media_hygiene.cli.home_state import home_state
from media_hygiene.cli.menu_steps import build_menu, full_catalog
from media_hygiene.paths.quarantines import Quarantines
from media_hygiene.services.home import home_page
from media_hygiene.services.status import read_status
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

_CONSOLE_ONLY: Final = frozenset(
    {"folders", "home", "status", "menu", "open", "reports"}
)


def test_the_six_steps_are_marked_console_only() -> None:
    """Exactly the six steps the page repeats carry `web=False`."""
    hidden = {step.name for step in full_catalog().steps if not step.web}
    assert hidden == _CONSOLE_ONLY


def test_the_page_leaves_them_out_and_the_menu_keeps_them(tmp_path: Path) -> None:
    """Absent from the page's actions and groups, present in `mh menu`."""
    runtime = make_runtime(make_locations(tmp_path))
    state = home_state(runtime)
    on_page = {action.name for action in state.actions}
    grouped = {
        name
        for space in state.spaces
        for group in space.groups
        for name in group.actions
    }
    menu = build_menu(read_status(runtime), 30, windows=True)
    in_menu = {line.step.name for line in menu.steps}
    assert not _CONSOLE_ONLY & on_page
    assert not _CONSOLE_ONLY & grouped
    assert in_menu >= _CONSOLE_ONLY
    assert "reports-prune" in on_page


def test_the_folders_panel_lists_each_drive_quarantine(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The default quarantine, then each drive's, found or not, as `mh folders`."""
    runtime = make_runtime(make_locations(tmp_path))
    default = runtime.locations.quarantine_dir
    default.mkdir(parents=True, exist_ok=True)
    drive = default / "e"
    monkeypatch.setattr(
        home_folders,
        "mounted_quarantines",
        lambda _runtime: Quarantines(default, (("E:", drive),)),
    )
    lines = {folder.role: folder.ok for folder in home_folders.home_folders(runtime)}
    assert lines.get("Quarantine") is True
    assert lines.get("Quarantine of E:") is False


def test_the_cycle_comes_first_and_the_audit_lives_on_the_clean_stage() -> None:
    """Cycle, then the compact next step; the in-page audit on Clean only (0483)."""
    page = home_page(relays_steps=True).decode()
    home = page[page.index("function viewHome()") : page.index("// ---- Spaces")]
    assert home.index("STAGES.map(station)") < home.index("${hero()}")
    assert "auditPanel()" not in home
    assert 'clean: ["auditHere"]' in page
    assert 'class="hero is-compact"' in page
