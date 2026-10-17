"""`review --near`: decide group by group, then `clean --tier near --decisions`."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from media_hygiene.errors import DecisionsError
from media_hygiene.plan.near_review import NearAction
from media_hygiene.report.decisions import read_decisions
from media_hygiene.review.near_app import NearApp
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.near_reviewing import open_near_review
from tests.support.cli import run
from tests.support.review import JSON_HEADERS, PAGE, Call, serve_app_and_call
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from typer.testing import CliRunner

    from media_hygiene.config.layers import Layer
    from media_hygiene.paths.locations import Locations
    from media_hygiene.review.near_session import NearSession

KEPT = "c/Family Photos/2021/Plage.jpg"
PROTECT_KEPT: Layer = {"folders": {"protected": ["C:\\Family Photos\\2021"]}}


def near_session(locations: Locations, cli: Layer | None = None) -> NearSession:
    """Audit the demo tree and open `review --near` on /reports/decisions.json."""
    runtime = make_runtime(locations, cli)
    findings = AuditService(runtime, NullProgress()).run()
    return open_near_review(runtime, findings, decisions_file(locations))


def decisions_file(locations: Locations) -> Path:
    """The decisions file the review writes."""
    return locations.reports_dir / "decisions.json"


def choose(group: int, action: str | None) -> Call:
    """`POST /api/near`, as the page sends it."""
    body = json.dumps({"choices": [{"group": group, "action": action}]}).encode()
    return Call("POST", "/api/near", body, JSON_HEADERS)


@pytest.mark.usefixtures("cli")
def test_the_page_decides_and_reads_back(locations: Locations) -> None:
    """One group to check; a swap is saved, read back, and undone again."""
    session = near_session(locations)
    [group] = session.state().groups
    assert not group.sure
    assert len(group.copies) == 2
    assert group.kept.name == "Plage.jpg"
    page, state, preview, swap, held, unknown, bad, back = serve_app_and_call(
        lambda pool: NearApp(session, PAGE, pool),
        [
            Call("GET", "/"),
            Call("GET", "/api/state"),
            Call("GET", group.kept.preview),
            choose(0, "swap"),
            Call("GET", "/api/file"),
            choose(7, "planned"),
            Call("POST", "/api/near", b'{"choices": []}', JSON_HEADERS),
            choose(0, None),
        ],
    )
    assert (page.status, page.body) == (200, PAGE)
    assert state.json() == json.loads(session.state().model_dump_json())
    assert preview.headers["content-type"] == "image/jpeg"
    assert swap.status == 200
    body = swap.json()
    assert isinstance(body, dict)
    assert (body["decided"], body["total"]) == (1, 1)
    assert body["file"]["entries"] == [
        {"group": 0, "action": "swap", "keep": body["file"]["entries"][0]["keep"]}
    ]
    assert held.json()["entries"][0]["action"] == "swap"  # type: ignore[index]
    assert unknown.status == 422
    assert bad.status == 400
    assert back.status == 200
    assert not read_decisions(decisions_file(locations)).near


@pytest.mark.usefixtures("cli")
def test_a_protected_kept_version_cannot_be_swapped(locations: Locations) -> None:
    """The page refuses W; the version stays where it is."""
    session = near_session(locations, PROTECT_KEPT)
    assert not session.state().groups[0].swappable
    with pytest.raises(DecisionsError, match="protected folder"):
        session.decide({0: NearAction.SWAP})
    with pytest.raises(DecisionsError, match="protected folder"):
        session.decide({0: NearAction.NONE})


def test_a_group_kept_none_of_goes_whole_and_undo_restores(
    cli: CliRunner, locations: Locations
) -> None:
    """X: every version to the quarantine, the kept one too; undo brings all back."""
    session = near_session(locations)
    group = session.state().groups[0]
    names = [group.kept.name, *(copy.name for copy in group.copies)]
    before = {p for p in locations.data_dir.rglob("*") if p.name in names}
    assert len(before) == len(names)
    session.decide({0: NearAction.NONE})
    result = run(
        cli, "clean", "--yes", "--tier", "near", "--decisions", "decisions.json"
    )
    assert result.exit_code == 0, result.output
    assert "none kept: 1" in result.output
    assert not any(path.exists() for path in before)
    assert run(cli, "undo").exit_code == 0
    assert all(path.is_file() for path in before)


def test_a_group_kept_none_of_refuses_a_protected_kept_version(
    cli: CliRunner, locations: Locations
) -> None:
    """Protected since the review: the clean refuses the file, nothing moves."""
    near_session(locations).decide({0: NearAction.NONE})
    result = run(
        cli,
        "clean",
        "--yes",
        "--tier",
        "near",
        "--decisions",
        "decisions.json",
        "--protect",
        "C:\\Family Photos\\2021",
    )
    assert result.exit_code == 1
    assert "is in a protected folder" in " ".join(result.output.split())
    assert (locations.data_dir / KEPT).is_file()


def test_the_clean_applies_a_swap_and_undo_restores(
    cli: CliRunner, locations: Locations
) -> None:
    """--tier near alone leaves the group; decided, the chosen copy is kept."""
    data = locations.data_dir
    session = near_session(locations)
    kept_copy = session.state().groups[0].copies[0].name
    session.decide({0: NearAction.SWAP})
    result = run(
        cli, "clean", "--yes", "--tier", "near", "--decisions", "decisions.json"
    )
    assert result.exit_code == 0, result.output
    assert "another version kept: 1" in result.output
    assert not (data / KEPT).exists()
    assert list(data.rglob(kept_copy)), kept_copy
    assert run(cli, "undo").exit_code == 0
    assert (data / KEPT).is_file()


def test_a_group_left_alone_never_moves(cli: CliRunner, locations: Locations) -> None:
    """Even with --tier near-all."""
    session = near_session(locations)
    session.decide({0: NearAction.LEAVE})
    before = {path for path in locations.data_dir.rglob("*") if path.is_file()}
    copies = {path for path in before if "WA0001" in path.name or "petite" in path.name}
    result = run(
        cli, "clean", "--yes", "--tier", "near-all", "--decisions", "decisions.json"
    )
    assert result.exit_code == 0, result.output
    assert "left alone: 1" in result.output
    assert all(path.is_file() for path in copies)


def test_decisions_wait_for_a_near_tier(cli: CliRunner, locations: Locations) -> None:
    """A plain clean with the decisions says they wait for --tier near."""
    near_session(locations).decide({0: NearAction.PLANNED})
    result = run(cli, "clean", "--yes", "--decisions", "decisions.json")
    assert result.exit_code == 0, result.output
    assert "waits for --tier near" in " ".join(result.output.split())


def test_a_stale_or_protected_decision_refuses_the_file(
    cli: CliRunner, locations: Locations
) -> None:
    """A group that changed since, or a swap of a protected file: nothing moves."""
    session = near_session(locations)
    session.decide({0: NearAction.SWAP})
    protect = ("--protect", "C:\\Family Photos\\2021")
    protected = run(
        cli,
        "clean",
        "--yes",
        "--tier",
        "near",
        "--decisions",
        "decisions.json",
        *protect,
    )
    assert protected.exit_code == 1
    assert "is in a protected folder" in " ".join(protected.output.split())
    target = decisions_file(locations)
    stale = json.loads(target.read_text())
    stale["near"][0]["kept"] = "C:\\Gone\\Plage.jpg"
    target.write_text(json.dumps(stale))
    result = run(
        cli, "clean", "--yes", "--tier", "near", "--decisions", "decisions.json"
    )
    assert result.exit_code == 1
    assert "changed since" in result.output
    assert (locations.data_dir / KEPT).is_file()


def test_the_command_tells_what_to_decide_and_what_next(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Counts first, then the clean command that applies the decisions."""
    monkeypatch.setattr(
        "media_hygiene.services.near_reviewing.serve_near_review", lambda *_args: None
    )
    result = run(cli, "review", "--near")
    assert result.exit_code == 0, result.output
    said = " ".join(result.output.split())
    assert "1 group of near duplicates: 0 sure, 1 to check" in said
    assert "groups decided: 0 of 1" in said
    assert "clean --tier near --decisions" in said


@pytest.mark.usefixtures("cli")
def test_the_review_resumes_and_drops_what_changed(locations: Locations) -> None:
    """Reopened, a decision is found again; a group that changed is to decide again."""
    near_session(locations).decide({0: NearAction.LEAVE})
    again = near_session(locations)
    assert (again.dropped, again.state().groups[0].action) == (0, "leave")
    target = decisions_file(locations)
    changed = json.loads(target.read_text())
    changed["near"][0]["copies"] = changed["near"][0]["copies"][:1]
    target.write_text(json.dumps(changed))
    stale = near_session(locations)
    assert (stale.dropped, stale.decided) == (1, (0, 1))
