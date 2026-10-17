"""`review --junk`: the photos most likely unwanted, set aside by you, then `clean`."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import numpy as np
import pytest
from PIL import Image

from media_hygiene.actions.journal import journal_file, read_journal
from media_hygiene.actions.kinds import ActionKind
from media_hygiene.actions.runs import list_run_ids
from media_hygiene.report.decisions import read_decisions
from media_hygiene.review.place import DecisionsPlace
from media_hygiene.review.unwanted_app import UnwantedApp
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.review_file import review_page
from media_hygiene.services.unwanted_reviewing import open_unwanted_review
from tests.support.cli import run
from tests.support.review import JSON_HEADERS, PAGE, Call, serve_app_and_call
from tests.support.runtime import make_runtime
from tests.support.scenes import scene

if TYPE_CHECKING:
    from pathlib import Path

    from typer.testing import CliRunner

    from media_hygiene.config.layers import Layer
    from media_hygiene.paths.locations import Locations
    from media_hygiene.review.unwanted_session import UnwantedSession

NIGHT = "c/Family Photos/2022/night.jpg"
SCREENSHOT = "c/Users/Public/Pictures/Screenshot_20220101.png"


def add_unwanted(data: Path) -> None:
    """A nearly black photo and a screenshot, next to the demo tree."""
    night = data / NIGHT
    night.parent.mkdir(parents=True, exist_ok=True)
    noise = np.random.default_rng(300).integers(0, 4, (480, 640, 3), dtype=np.uint8)
    Image.fromarray(noise).save(night, quality=92)
    shot = data / SCREENSHOT
    shot.parent.mkdir(parents=True, exist_ok=True)
    scene(301).save(shot)


def junk_session(locations: Locations, cli: Layer | None = None) -> UnwantedSession:
    """Audit the demo tree and open `review --junk` on /reports/decisions.json."""
    runtime = make_runtime(locations, cli)
    findings = AuditService(runtime, NullProgress()).run()
    return open_unwanted_review(
        runtime, findings, locations.reports_dir / "decisions.json"
    )


def rank_of(session: UnwantedSession, name: str) -> int:
    """The rank of a photo on the page, by its name."""
    photos = session.state().photos
    return next(rank for rank, photo in enumerate(photos) if photo.name == name)


def choose(*choices: tuple[int, bool | None]) -> Call:
    """`POST /api/junk`, as the page sends it."""
    body = {"choices": [{"photo": photo, "aside": aside} for photo, aside in choices]}
    return Call("POST", "/api/junk", json.dumps(body).encode(), JSON_HEADERS)


@pytest.mark.usefixtures("cli")
def test_the_page_lists_decides_and_reads_back(locations: Locations) -> None:
    """The dark photo and the screenshot are listed; a choice is saved, read back."""
    add_unwanted(locations.data_dir)
    session = junk_session(locations)
    state = session.state()
    listed = {photo.name: photo.reason for photo in state.photos}
    assert (listed["night.jpg"], listed["Screenshot_20220101.png"]) == (
        "dark",
        "screenshot",
    )
    assert not any(name.startswith("IMG_20") for name in listed)  # burst shots
    assert "Plage.jpg" not in listed  # a near duplicate
    assert all(photo.decision == "" for photo in state.photos)
    night = rank_of(session, "night.jpg")
    shot = rank_of(session, "Screenshot_20220101.png")
    page, got, preview, decided, held, *others = serve_app_and_call(
        lambda pool: UnwantedApp(session, PAGE, pool),
        [
            Call("GET", "/"),
            Call("GET", "/api/state"),
            Call("GET", state.photos[night].preview),
            choose((night, True), (shot, False)),
            Call("GET", "/api/file"),
            choose((999, True)),
            Call("POST", "/api/junk", b'{"choices": []}', JSON_HEADERS),
            choose((shot, None)),
        ],
    )
    assert (page.status, page.body) == (200, PAGE)
    assert got.json() == json.loads(state.model_dump_json())  # before the choices
    assert preview.headers["content-type"] == "image/jpeg"
    reply = json.loads(decided.body)
    assert (reply["decided"], reply["aside"]) == (2, 1)
    assert {(e["photo"], e["aside"]) for e in reply["file"]["entries"]} == {
        (night, True),
        (shot, False),
    }
    assert len(json.loads(held.body)["entries"]) == 2
    assert [reply.status for reply in others] == [422, 400, 200]  # unknown, bad, back
    [entry] = read_decisions(locations.reports_dir / "decisions.json").unwanted
    assert (entry.path.endswith("night.jpg"), entry.aside) == (True, True)


@pytest.mark.usefixtures("cli")
def test_a_protected_photo_is_never_listed(locations: Locations) -> None:
    """The dark photo of a protected folder is left out of the page."""
    add_unwanted(locations.data_dir)
    protect: Layer = {"folders": {"protected": ["C:\\Family Photos\\2022"]}}
    names = {photo.name for photo in junk_session(locations, protect).state().photos}
    assert "night.jpg" not in names
    assert "Screenshot_20220101.png" in names


@pytest.mark.usefixtures("cli")
def test_the_other_keys_are_kept_and_the_review_resumes(locations: Locations) -> None:
    """A pair decided before stays; reopened, the choice is found again."""
    add_unwanted(locations.data_dir)
    session = junk_session(locations)
    target = locations.reports_dir / "decisions.json"
    raw = json.loads(target.read_text(encoding="utf-8"))
    pair = {"kept_in": "C:\\a", "removed_from": "D:\\a", "action": "skip"}
    target.write_text(json.dumps(raw | {"pairs": [pair]}))
    session = junk_session(locations)
    session.decide({rank_of(session, "night.jpg"): True})
    saved = json.loads(target.read_text(encoding="utf-8"))
    assert saved["pairs"] == [pair]
    again = junk_session(locations)
    assert again.state().photos[rank_of(again, "night.jpg")].decision == "aside"
    assert again.dropped == 0


def test_the_clean_moves_only_what_was_set_aside_and_undo_restores(
    cli: CliRunner, locations: Locations
) -> None:
    """The dark photo goes to the quarantine, journaled apart; the screenshot stays."""
    data = locations.data_dir
    add_unwanted(data)
    session = junk_session(locations)
    session.decide(
        {
            rank_of(session, "night.jpg"): True,
            rank_of(session, "Screenshot_20220101.png"): False,
        }
    )
    result = run(cli, "clean", "--yes", "--decisions", "decisions.json")
    assert result.exit_code == 0, result.output
    said = " ".join(result.output.split())
    assert "1 unwanted photo set aside in 'review --junk'" in said
    assert not (data / NIGHT).exists()
    assert (data / SCREENSHOT).is_file()
    [last, *_older] = list_run_ids(locations.journal_dir)
    kinds = {
        entry.action
        for entry in read_journal(journal_file(locations.journal_dir, last))
    }
    assert ActionKind.QUARANTINE_UNWANTED in kinds
    history = " ".join(run(cli, "history").output.split())
    assert "unwan" in history  # its column, cut in a narrow terminal
    assert run(cli, "undo").exit_code == 0
    assert (data / NIGHT).is_file()


def test_the_command_tells_what_to_decide(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Counts by reason first, then where the choices are."""
    add_unwanted(locations.data_dir)
    monkeypatch.setattr(
        "media_hygiene.services.unwanted_reviewing.serve_unwanted_review",
        lambda *_args: None,
    )
    result = run(cli, "review", "--junk")
    assert result.exit_code == 0, result.output
    said = " ".join(result.output.split())
    assert "look unwanted (" in said
    assert "nearly black: 1" in said
    assert "photos decided: 0 of" in said


def test_the_page_renders_with_its_route() -> None:
    """The page names its route; the texts carry no "(s)"."""
    place = DecisionsPlace(argument="decisions.json", host="decisions.json")
    text = review_page("unwanted_review.html.j2", place, ("/api/junk", "/api/file"))
    assert '"/api/junk"' in text.decode()
    assert "(s)" not in text.decode()
