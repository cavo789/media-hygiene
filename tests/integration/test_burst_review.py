"""`review` then `clean --decisions`: burst shots set aside go to the quarantine."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services import reviewing
from tests.support.cli import run

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.paths.locations import Locations
    from media_hygiene.review.app import ReviewApp
    from tests.support.media import MediaFactory

RAFALE = "C:\\Family Photos\\Rafale"
BLURRED = "c/Family Photos/Rafale/IMG_202.jpg"
DEMO_ROOTS = ["C:\\", "D:\\"]
PORT = 4242


def shots(*ranks: int) -> list[str]:
    """Host paths of the demo burst's shots."""
    return [f"{RAFALE}\\IMG_20{rank}.jpg" for rank in ranks]


def write_decisions(
    locations: Locations, kept: list[str], discarded: list[str]
) -> None:
    """The decisions file `review` writes for one series."""
    bursts = [{"kept": kept, "discarded": discarded}]
    decisions = {"version": 1, "roots": DEMO_ROOTS, "bursts": bursts}
    (locations.reports_dir / "decisions.json").write_text(json.dumps(decisions))


def test_shots_set_aside_are_moved_and_come_back(
    cli: CliRunner, locations: Locations
) -> None:
    """Quarantined, never deleted; the other shots stay; undo restores."""
    data = locations.data_dir
    write_decisions(locations, shots(0, 1, 3), shots(2))
    result = run(cli, "clean", "--yes", "--decisions", "decisions.json")
    assert result.exit_code == 0, result.output
    assert "burst series reviewed: 1, shots set aside: 1" in result.output
    assert not (data / BLURRED).exists()
    assert [p.name for p in locations.quarantine_dir.rglob("IMG_202.jpg")]
    assert (data / "c/Family Photos/Rafale/IMG_201.jpg").is_file()
    assert run(cli, "undo").exit_code == 0
    assert (data / BLURRED).is_file()


type Case = tuple[list[str], list[str], str]  # discarded, options, error
STALE: Case = (["C:\\elsewhere.jpg"], [], "no longer matches the audit")
PROTECTED: Case = (shots(2), ["--protect", RAFALE], "is in a protected folder")


@pytest.mark.parametrize("case", [STALE, PROTECTED])
def test_stale_or_protected_shots_are_refused(
    cli: CliRunner, locations: Locations, case: Case
) -> None:
    """Nothing is cleaned: the whole file is refused."""
    discarded, options, error = case
    write_decisions(locations, shots(0), discarded)
    result = run(cli, "clean", "--yes", "--decisions", "decisions.json", *options)
    assert result.exit_code == 1
    assert error in result.output
    assert (locations.data_dir / BLURRED).is_file()


def test_shots_set_aside_need_a_quarantine(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Refused before the audit, with a tip."""
    write_decisions(locations, shots(0), shots(2))
    monkeypatch.delenv("MEDIA_HYGIENE_QUARANTINE_DIR")
    result = run(cli, "clean", "--yes", "--delete", "--decisions", "decisions.json")
    assert result.exit_code == 1
    assert "The burst shots and files you set aside go to /quarantine" in result.output
    assert "Audit summary" not in result.output


def test_a_series_kept_whole_moves_nothing(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Seen and kept whole: no shot moves, and no quarantine is needed."""
    write_decisions(locations, shots(0, 1, 2, 3), [])
    monkeypatch.delenv("MEDIA_HYGIENE_QUARANTINE_DIR")
    result = run(cli, "clean", "--yes", "--delete", "--decisions", "decisions.json")
    assert result.exit_code == 0, result.output
    assert "burst series reviewed: 1, shots set aside: 0" in result.output
    assert (locations.data_dir / BLURRED).is_file()


def test_series_still_to_see_never_block_clean(
    cli: CliRunner, locations: Locations
) -> None:
    """A `todo` series moves nothing and is never checked, even when stale."""
    todo = {"status": "todo", "kept": ["C:\\elsewhere.jpg"]}
    done = {"kept": shots(0, 1, 3), "discarded": shots(2)}
    decisions = {"version": 1, "roots": DEMO_ROOTS, "bursts": [todo, done]}
    (locations.reports_dir / "decisions.json").write_text(json.dumps(decisions))
    result = run(cli, "clean", "--yes", "--decisions", "decisions.json")
    assert result.exit_code == 0, result.output
    assert "1 burst series not reviewed yet: its shots stay." in result.output
    assert "burst series reviewed: 1, shots set aside: 1" in result.output
    assert not (locations.data_dir / BLURRED).exists()


def fake_server(action: Callable[[ReviewApp], None]) -> object:
    """A server that says it is ready, lets `action` act, then gets Ctrl+C."""

    async def serve(app: ReviewApp, _port: int, ready: Callable[[int], None]) -> None:
        ready(PORT)
        action(app)
        raise KeyboardInterrupt

    return serve


def test_the_review_command_serves_until_ctrl_c(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Where to open it, the page translated, each choice saved, then what to do."""
    pages: list[bytes] = []

    def choose(app: ReviewApp) -> None:
        pages.append(app.page)
        app.session.decide({0: frozenset({2})})

    monkeypatch.setattr(reviewing, "run_server", fake_server(choose))
    result = run(cli, "review")
    assert result.exit_code == 0, result.output
    assert f"open http://127.0.0.1:{PORT}/ in your browser" in result.output
    assert f"-p 127.0.0.1:{PORT}:{PORT}" in result.output
    assert "1 series to see: " in result.output
    assert "shots set aside: 1" in result.output
    assert "'clean' command with --decisions;" in result.output
    assert "decisions.json, in the folder mounted on" in result.output
    assert b"Burst series review" in pages[0]
    saved = json.loads((locations.reports_dir / "decisions.json").read_text())
    assert saved["bursts"][0]["discarded"] == shots(2)


def test_the_review_needs_somewhere_to_save(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without /reports the decisions would be lost: refused before the audit."""
    monkeypatch.delenv("MEDIA_HYGIENE_REPORTS_DIR")
    result = run(cli, "review")
    assert result.exit_code == 1
    assert "The decisions are saved in /reports" in result.output
    assert "Audit summary" not in result.output


def test_no_burst_nothing_to_review(
    locations: Locations, media: MediaFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A tree without bursts: said at once, no server."""
    media.image("c/Photos/alone.jpg")
    for kind in MountKind:
        path = locations.path_of(kind)
        monkeypatch.setenv(f"MEDIA_HYGIENE_{kind.value.upper()}_DIR", str(path))
    monkeypatch.setattr(reviewing, "run_server", fake_server(lambda _app: None))
    result = run(
        CliRunner(), "review", "--decisions", str(locations.cache_dir / "d.json")
    )
    assert result.exit_code == 0, result.output
    assert "No burst series: nothing to review." in result.output


def test_the_stop_summary_names_the_file_without_any_choice(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The file may hold the report's pairs: always said where it is."""
    monkeypatch.setattr(reviewing, "run_server", fake_server(lambda _app: None))
    result = run(cli, "review")
    assert result.exit_code == 0, result.output
    assert (
        "Your choices are in decisions.json, in the folder mounted on" in result.output
    )
    assert "What next:" not in result.output


def test_audit_ends_on_the_next_step(cli: CliRunner) -> None:
    """The copies come first; once they are gone, the bursts are the next step."""
    first = run(cli, "audit")
    assert "Photos with a shooting date" not in first.output  # 'inventory' has it
    advice = first.output[first.output.index("👉 What next") :]
    assert advice.startswith("👉 What next: run 'clean'")
    assert "burst series: optional" in " ".join(first.output.split())
    assert run(cli, "clean", "--yes").exit_code == 0
    second = run(cli, "audit")
    assert "What next: sort the burst series" in second.output
    assert "👉 What next: run 'clean'" not in second.output
