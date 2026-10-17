"""`review --gone`: the files deleted in the Explorer, confirmed, then proposed back."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.actions.journal import journal_file, read_journal
from media_hygiene.actions.kinds import ActionKind
from media_hygiene.actions.runs import list_run_ids, summarize
from media_hygiene.constants import Sizes
from media_hygiene.report.decisions import read_decisions
from media_hygiene.report.preview_cache import PreviewJob, preview_key
from media_hygiene.review.gone_app import GoneApp
from media_hygiene.review.place import DecisionsPlace
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.gone_reviewing import files_gone, open_gone_review
from media_hygiene.services.review_file import review_page
from tests.support.cli import run
from tests.support.review import JSON_HEADERS, PAGE, Call, serve_app_and_call
from tests.support.runtime import make_runtime
from tests.support.scenes import scene

if TYPE_CHECKING:
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from media_hygiene.plan.models import AuditFindings
    from media_hygiene.review.gone_session import GoneSession

FOLDER = ("c", "Ex", "2023")


def two_deleted(data: Path) -> tuple[bytes, bytes]:
    """Two photos audited, then deleted in the Explorer; their contents."""
    folder = data.joinpath(*FOLDER)
    folder.mkdir(parents=True)
    contents = []
    for seed, name in ((401, "IMG_0401.jpg"), (402, "IMG_0402.jpg")):
        scene(seed).save(folder / name, quality=90)
        contents.append((folder / name).read_bytes())
    return contents[0], contents[1]


def audit(locations: Locations) -> AuditFindings:
    """Audit the data mount."""
    return AuditService(make_runtime(locations), NullProgress()).run()


def gone_session(locations: Locations) -> GoneSession:
    """Audit, then open `review --gone` on /reports/decisions.json."""
    runtime = make_runtime(locations)
    findings = audit(locations)
    return open_gone_review(runtime, findings, locations.reports_dir / "decisions.json")


def rank_of(session: GoneSession, name: str) -> int:
    """The rank of a file on the page, by its name."""
    return next(r for r, f in enumerate(session.state().files) if f.name == name)


def answer(*choices: tuple[int, bool | None]) -> Call:
    """`POST /api/gone`, as the page sends it."""
    body = {"choices": [{"file": file, "deleted": on} for file, on in choices]}
    return Call("POST", "/api/gone", json.dumps(body).encode(), JSON_HEADERS)


def answer_on_the_page(locations: Locations) -> None:
    """Both files gone answered on the page: the first deleted, the second moved."""
    session = gone_session(locations)
    assert len(files_gone(make_runtime(locations))) == 2
    first, second = rank_of(session, "IMG_0401.jpg"), rank_of(session, "IMG_0402.jpg")
    page, state, decided, held, unknown, bad = serve_app_and_call(
        lambda pool: GoneApp(session, PAGE, pool),
        [
            Call("GET", "/"),
            Call("GET", "/api/state"),
            answer((first, True), (second, False)),
            Call("GET", "/api/file"),
            answer((999, True)),
            Call("POST", "/api/gone", b'{"choices": []}', JSON_HEADERS),
        ],
    )
    assert (page.status, len(json.loads(state.body)["files"])) == (200, 2)
    reply = json.loads(decided.body)
    assert (reply["decided"], reply["deleted"]) == (2, 1)
    assert len(json.loads(held.body)["entries"]) == 2
    assert (unknown.status, bad.status) == (422, 400)
    saved = read_decisions(locations.reports_dir / "decisions.json").gone
    assert {(e.path.endswith("IMG_0401.jpg"), e.deleted) for e in saved} == {
        (True, True),
        (False, False),
    }


def test_answered_marked_proposed_back_then_undone(
    cli: CliRunner, locations: Locations
) -> None:
    """D is remembered by the clean; its copy back is proposed, M's is not."""
    data = locations.data_dir
    deleted, moved = two_deleted(data)
    assert run(cli, "audit").exit_code == 0
    for name in ("IMG_0401.jpg", "IMG_0402.jpg"):
        data.joinpath(*FOLDER, name).unlink()
    answer_on_the_page(locations)
    result = run(cli, "clean", "--yes", "--decisions", "decisions.json")
    assert result.exit_code == 0, result.output
    said = " ".join(result.output.split())
    assert "files deleted in the Explorer on purpose: 1, moved elsewhere: 1" in said
    [clean_run, *_older] = list_run_ids(locations.journal_dir)
    marks = [
        entry
        for entry in read_journal(journal_file(locations.journal_dir, clean_run))
        if entry.action is ActionKind.MARK_GONE
    ]
    assert len(marks) == 2
    assert summarize(locations.journal_dir, clean_run).marked == 1
    assert not files_gone(make_runtime(locations))  # both answers forgotten

    phone = data / "c" / "Phone"
    phone.mkdir()
    (phone / "20230101_120000.jpg").write_bytes(deleted)
    (phone / "20230101_120001.jpg").write_bytes(moved)
    (back,) = audit(locations).plan.returned
    assert back.file.path.name == "20230101_120000.jpg"
    assert back.remembered.action is ActionKind.MARK_GONE

    assert run(cli, "undo", "--yes", clean_run).exit_code == 0
    assert not audit(locations).plan.returned


def test_a_review_resumes_and_keeps_the_other_keys(locations: Locations) -> None:
    """A pair decided before stays; reopened, the answer is found again."""
    data = locations.data_dir
    two_deleted(data)
    audit(locations)
    data.joinpath(*FOLDER, "IMG_0401.jpg").unlink()
    session = gone_session(locations)
    target = locations.reports_dir / "decisions.json"
    raw = json.loads(target.read_text(encoding="utf-8"))
    pair = {"kept_in": "C:\\a", "removed_from": "D:\\a", "action": "skip"}
    target.write_text(json.dumps(raw | {"pairs": [pair]}))
    session = gone_session(locations)
    session.decide({rank_of(session, "IMG_0401.jpg"): True})
    assert json.loads(target.read_text(encoding="utf-8"))["pairs"] == [pair]
    again = gone_session(locations)
    assert again.state().files[0].decision == "deleted"
    assert again.dropped == 0


def test_the_page_renders_with_its_route() -> None:
    """The page names its route; the texts carry no "(s)"."""
    place = DecisionsPlace(argument="decisions.json", host="decisions.json")
    text = review_page(
        "gone_review.html.j2", place, ("/api/gone", "/api/file")
    ).decode()
    assert '"/api/gone"' in text
    assert "(s)" not in text


def test_a_preview_kept_in_the_cache_is_shown(locations: Locations) -> None:
    """The file is gone; the preview a report made of it is still served."""
    data = locations.data_dir
    two_deleted(data)
    audit(locations)
    data.joinpath(*FOLDER, "IMG_0401.jpg").unlink()
    session = gone_session(locations)
    runtime = make_runtime(locations)
    (record,) = files_gone(runtime)
    assert runtime.previews_dir is not None
    job = PreviewJob(Path(record.path), Sizes.THUMBNAIL_EDGE, runtime.previews_dir)
    kept = runtime.previews_dir / preview_key(job, record.size, record.mtime_ns)
    kept.parent.mkdir(parents=True, exist_ok=True)
    kept.write_bytes(b"\xff\xd8 a jpeg")
    session = gone_session(locations)
    (state,) = session.state().files
    assert state.preview
    shown, missing = serve_app_and_call(
        lambda pool: GoneApp(session, PAGE, pool),
        [Call("GET", state.preview), Call("GET", "/preview/0123.jpg")],
    )
    assert (shown.status, shown.body) == (200, b"\xff\xd8 a jpeg")
    assert missing.status == 404
