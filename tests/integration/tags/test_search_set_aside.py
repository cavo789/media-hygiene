"""`search`: files picked on the page set aside, then moved by `clean --decisions`."""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

from media_hygiene.report.burst_decisions import BurstDecision, BurstStatus
from media_hygiene.report.decisions import (
    DecisionsFile,
    read_decisions,
    write_decisions,
)
from media_hygiene.search import app as search_app
from media_hygiene.services import search_pages as search_service
from tests.integration.tags.test_search_command import _call, fake_server
from tests.support.cli import run

if TYPE_CHECKING:
    from pathlib import Path

    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from media_hygiene.review.http import Response
    from media_hygiene.search.app import SearchApp

_DURBUY = {"text": "durbuy"}


def _serve(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch, calls: list[tuple[str, object]]
) -> tuple[list[Response], str]:
    """Open the search page, send the calls in order, stop it; answers, console."""
    answers: list[Response] = []

    async def browse(app: SearchApp) -> None:
        for route, body in calls:
            answers.append(await _call(app, route, body))

    monkeypatch.setattr(search_service, "serve_until_ended", fake_server(browse))
    result = run(cli, "search")
    assert result.exit_code == 0, result.output
    return answers, result.output


def _hits(answer: Response) -> list[dict[str, object]]:
    """The files a search answer lists."""
    hits: list[dict[str, object]] = json.loads(answer.body)["hits"]
    return hits


def test_picked_files_and_every_file_found_are_saved_and_read_back(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One file, then every file found beyond the page; the other keys are kept."""
    assert run(cli, "tags", "--no-describe").exit_code == 0
    decisions = locations.reports_dir / "decisions.json"
    todo = BurstDecision(status=BurstStatus.TODO, kept=("C:\\x\\IMG_9.jpg",))
    write_decisions(
        decisions,
        DecisionsFile(version=1, report="r1", roots=("C:\\",), bursts=(todo,)),
    )
    monkeypatch.setattr(search_app, "PAGE_HITS", 1)  # the page shows one file
    first, _console = _serve(cli, monkeypatch, [("POST /api/search", _DURBUY)])
    key = _hits(first[0])[0]["key"]
    answers = _serve(
        cli,
        monkeypatch,
        [
            ("POST /api/search", _DURBUY),
            ("POST /api/chosen", {"action": "add", "keys": [key], "search": _DURBUY}),
            ("GET /api/chosen", None),
            ("POST /api/chosen", {"action": "add", "all": True, "search": _DURBUY}),
            ("POST /api/search", _DURBUY),
            ("POST /api/chosen", {"action": "remove", "all": True, "search": _DURBUY}),
        ],
    )[0]
    assert json.loads(answers[0].body)["total"] == 3
    counts = [json.loads(answers[n].body)["count"] for n in (1, 2, 3, 5)]
    assert counts == [1, 1, 3, 0]
    assert "clean --decisions" in json.loads(answers[3].body)["message"]
    assert _hits(answers[4])[0]["chosen"] is True
    kept = read_decisions(decisions)
    assert kept.report == "r1"
    assert kept.bursts == (todo,)
    assert kept.chosen == ()


def test_clean_moves_exactly_the_chosen_files_and_undo_brings_them_back(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A file changed since it was chosen is left and said; the rest come back."""
    assert run(cli, "tags", "--no-describe").exit_code == 0
    answers, console = _serve(
        cli,
        monkeypatch,
        [("POST /api/chosen", {"action": "add", "all": True, "search": _DURBUY})],
    )
    assert json.loads(answers[0].body)["count"] == 3
    assert "clean --decisions" in console.split("What next")[-1]
    burst = locations.data_dir / "c" / "Photos" / "2022" / "Durbuy - ours"
    changed: Path = burst / "IMG_2.jpg"
    os.utime(changed, ns=(1, 1))
    result = run(cli, "clean", "--yes", "--decisions", "decisions.json")
    assert result.exit_code == 0, result.output
    said = " ".join(result.output.split())
    assert "3 files chosen in 'search' are set aside" in said
    assert "Skipped (left untouched) │ 1" in said
    (report,) = locations.reports_dir.glob("*-clean/report.html")
    assert "changed since you chose it" in report.read_text(encoding="utf-8")
    assert sorted(p.name for p in burst.glob("*.jpg")) == ["IMG_2.jpg"]
    moved = sorted(p.name for p in locations.quarantine_dir.rglob("IMG_*.jpg"))
    assert moved[:2] == ["IMG_0.jpg", "IMG_1.jpg"]
    assert run(cli, "undo").exit_code == 0
    assert sorted(p.name for p in burst.glob("*.jpg")) == [
        f"IMG_{n}.jpg" for n in range(3)
    ]


def test_a_file_chosen_in_a_protected_folder_refuses_the_file(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Protected folders are never changed: the whole decisions file is refused."""
    assert run(cli, "tags", "--no-describe").exit_code == 0
    _serve(
        cli,
        monkeypatch,
        [("POST /api/chosen", {"action": "add", "all": True, "search": _DURBUY})],
    )
    chosen = read_decisions(locations.reports_dir / "decisions.json").chosen
    folder = chosen[0].path.rsplit("\\", 1)[0]
    result = run(
        cli, "clean", "--yes", "--decisions", "decisions.json", "--protect", folder
    )
    assert result.exit_code != 0
    assert "is in a protected folder" in " ".join(result.output.split())


def test_nothing_is_saved_without_a_writable_reports_folder(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The page says why, and no decisions file appears."""
    assert run(cli, "tags", "--no-describe").exit_code == 0
    locations.reports_dir.chmod(0o500)
    try:
        answers = _serve(
            cli,
            monkeypatch,
            [
                ("POST /api/chosen", {"action": "add", "all": True}),
                ("POST /api/chosen", {"action": "delete"}),
            ],
        )[0]
    finally:
        locations.reports_dir.chmod(0o700)
    assert [answer.status for answer in answers] == [409, 400]
    assert "cannot write" in json.loads(answers[0].body)["error"]
    assert not (locations.reports_dir / "decisions.json").exists()
