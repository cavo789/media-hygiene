"""`review --pairs`: decide the folder pairs one by one, then `clean --decisions`."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from media_hygiene.errors import DecisionsError
from media_hygiene.plan.review import PairAction
from media_hygiene.report.decisions import DecisionsFile, read_decisions
from media_hygiene.review.pairs_app import PairsApp
from media_hygiene.review.place import DecisionsPlace
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.pairs_reviewing import open_pairs_review
from media_hygiene.services.review_file import review_page
from tests.support.cli import run
from tests.support.pairs import IPHONE, SUMMER, clean_swapped_and_skipped
from tests.support.review import JSON_HEADERS, PAGE, Call, serve_app_and_call
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from typer.testing import CliRunner

    from media_hygiene.config.layers import Layer
    from media_hygiene.paths.locations import Locations
    from media_hygiene.review.pairs_session import PairsSession

PROTECT_IPHONE: Layer = {"folders": {"protected": ["C:\\Family Photos\\iPhone"]}}


def pairs_session(locations: Locations, cli: Layer | None = None) -> PairsSession:
    """Audit the demo tree and open `review --pairs` on /reports/decisions.json."""
    runtime = make_runtime(locations, cli)
    findings = AuditService(runtime, NullProgress()).run()
    return open_pairs_review(runtime, findings, decisions_file(locations))


def decisions_file(locations: Locations) -> Path:
    """The decisions file the review writes."""
    return locations.reports_dir / "decisions.json"


def rank_of(session: PairsSession, key: tuple[str, str]) -> int:
    """The rank of a pair on the page, by its two folders."""
    pairs = session.state().pairs
    return next(
        rank
        for rank, pair in enumerate(pairs)
        if (pair.kept_in, pair.removed_from) == key
    )


def choose(pair: int, action: str | None) -> Call:
    """`POST /api/pairs`, as the page sends it."""
    body = json.dumps({"pair": pair, "action": action}).encode()
    return Call("POST", "/api/pairs", body, JSON_HEADERS)


@pytest.mark.usefixtures("cli")
def test_the_page_lists_decides_and_reads_back(locations: Locations) -> None:
    """The pairs, the most space freed first; a swap saved, read back, undone."""
    session = pairs_session(locations)
    sizes = [pair.size for pair in session.state().pairs]
    assert len(sizes) >= 2
    assert sizes == sorted(sizes, reverse=True)
    iphone = rank_of(session, IPHONE)
    summer = session.state().pairs[rank_of(session, SUMMER)]
    assert summer.reasons
    page, state, preview, swap, held, unknown, bad, back = serve_app_and_call(
        lambda pool: PairsApp(session, PAGE, pool),
        [
            Call("GET", "/"),
            Call("GET", "/api/state"),
            Call("GET", summer.samples[0].preview),
            choose(iphone, "swap"),
            Call("GET", "/api/file"),
            choose(99, "planned"),
            Call("POST", "/api/pairs", b'{"pair": 0, "action": "both"}', JSON_HEADERS),
            choose(iphone, None),
        ],
    )
    assert (page.status, page.body) == (200, PAGE)
    assert state.json() == json.loads(session.state().model_dump_json())
    assert preview.headers["content-type"] == "image/jpeg"
    assert swap.status == 200
    swapped = json.loads(swap.body)
    assert (swapped["decided"], swapped["total"]) == (1, len(sizes))
    expected = [{"pair": iphone, "action": "swap"}]
    assert swapped["file"]["entries"] == expected
    assert json.loads(held.body)["entries"] == expected
    assert unknown.status == 422
    assert bad.status == 400
    assert back.status == 200
    assert not read_decisions(decisions_file(locations)).pairs


@pytest.mark.usefixtures("cli")
def test_a_protected_kept_folder_cannot_be_swapped(locations: Locations) -> None:
    """W is refused when the folder keeping the copies is protected (the report too)."""
    session = pairs_session(locations, PROTECT_IPHONE)
    iphone = rank_of(session, IPHONE)
    assert not session.state().pairs[iphone].swappable
    with pytest.raises(DecisionsError, match="protected"):
        session.decide({iphone: PairAction.SWAP})
    session.decide({iphone: PairAction.SKIP})
    assert read_decisions(decisions_file(locations)).pairs[0].action == "skip"


@pytest.mark.usefixtures("cli")
def test_the_other_keys_of_the_file_are_kept(locations: Locations) -> None:
    """Bursts, near groups and chosen files written by the other reviews stay."""
    first = pairs_session(locations)
    roots = read_decisions(decisions_file(locations)).roots
    others: dict[str, list[dict[str, object]]] = {
        "bursts": [{"status": "done", "kept": ["C:\\a.jpg"], "discarded": []}],
        "near": [
            {"kept": "C:\\b.jpg", "copies": ["D:\\b.jpg"], "action": "leave"},
        ],
        "chosen": [
            {"path": "C:\\c.jpg", "size": 1, "mtime_ns": 1, "found_by": "x"},
        ],
    }
    raw = {"version": 1, "roots": list(roots), **others}
    decisions_file(locations).write_text(json.dumps(raw))
    session = pairs_session(locations)
    assert first.decided[1] == session.decided[1]
    session.decide({rank_of(session, SUMMER): PairAction.SKIP})
    saved = json.loads(decisions_file(locations).read_text(encoding="utf-8"))
    for key, value in others.items():
        assert saved[key][0].items() >= value[0].items()
    assert saved["pairs"] == [
        {"kept_in": SUMMER[0], "removed_from": SUMMER[1], "action": "skip"}
    ]


@pytest.mark.usefixtures("cli")
def test_the_review_resumes_and_drops_what_is_gone(locations: Locations) -> None:
    """Reopened, the choices are found again; a pair that is gone is dropped."""
    session = pairs_session(locations)
    session.decide({rank_of(session, SUMMER): PairAction.PLANNED})
    again = pairs_session(locations)
    assert (again.dropped, again.decided[0]) == (0, 1)
    assert again.state().pairs[rank_of(again, SUMMER)].action == "planned"
    target = decisions_file(locations)
    gone = DecisionsFile.model_validate_json(target.read_text(encoding="utf-8"))
    stale = gone.pairs[0].model_copy(update={"kept_in": "C:\\Gone"})
    target.write_text(gone.model_copy(update={"pairs": (stale,)}).model_dump_json())
    dropped = pairs_session(locations)
    assert (dropped.dropped, dropped.decided[0]) == (1, 0)


def test_the_clean_applies_the_pairs_and_undo_restores(
    cli: CliRunner, locations: Locations
) -> None:
    """Swap keeps the backup's HEIC, skip the summer copies; planned changes nothing."""
    session = pairs_session(locations)
    session.decide({rank_of(session, IPHONE): PairAction.SWAP})
    session.decide({rank_of(session, SUMMER): PairAction.SKIP})
    others = [
        rank
        for rank, pair in enumerate(session.state().pairs)
        if (pair.kept_in, pair.removed_from) not in {IPHONE, SUMMER}
    ]
    session.decide(dict.fromkeys(others, PairAction.PLANNED))
    clean_swapped_and_skipped(cli, locations.data_dir)


def test_the_command_tells_what_to_decide_and_what_next(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Counts first, then the clean command that applies the decisions."""
    monkeypatch.setattr(
        "media_hygiene.services.pairs_reviewing.serve_pairs_review",
        lambda *_args: None,
    )
    result = run(cli, "review", "--pairs")
    assert result.exit_code == 0, result.output
    said = " ".join(result.output.split())
    assert "folder pairs, the most space freed first: 0 decided already" in said
    assert "pairs decided: 0 of" in said
    assert "clean --decisions" in said


def test_one_review_per_run(cli: CliRunner) -> None:
    """--near and --pairs together are refused before the audit."""
    result = run(cli, "review", "--near", "--pairs")
    assert result.exit_code == 1
    assert "separate reviews: one per run" in " ".join(result.output.split())
    assert "Audit summary" not in result.output


def test_the_page_renders_with_its_routes_and_both_plural_forms() -> None:
    """The page names its routes and gets both forms of a count, never "(s)"."""
    place = DecisionsPlace(argument="decisions.json", host="decisions.json")
    page = review_page("pairs_review.html.j2", place, ("/api/pairs", "/api/file"))
    text = page.decode()
    assert '"/api/pairs"' in text
    texts = json.loads(text.split("const T = ", 1)[1].split("\n", 1)[0].rstrip(";"))
    assert texts["files"] == [
        "{n} identical file, {size}",
        "{n} identical files, {size}",
    ]
    assert "(s)" not in text
