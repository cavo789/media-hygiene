"""The clean report's two blocks: what the run did, what it left for later (0309)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from media_hygiene.actions.outcome import Incident, Outcome
from media_hygiene.constants import MediaKind, RunKind
from media_hygiene.plan.models import AuditFindings, CleanPlan
from media_hygiene.plan.similar_models import (
    BurstChoice,
    BurstSeries,
    NearDecision,
    SimilarFindings,
)
from media_hygiene.report.clean_done import (
    CleanAsked,
    asked_flags,
    clean_done,
    latest_audit_link,
    shown_similar,
)
from media_hygiene.report.summary import ReportSummary
from media_hygiene.report.views import ReportRecord
from media_hygiene.scan.models import MediaFile
from tests.support.report_folders import MINIMAL, write_summary


def media(name: str) -> MediaFile:
    """A picture of 10 bytes."""
    return MediaFile(Path("/data/c") / name, 10, 0, MediaKind.IMAGE)


NEAR = NearDecision(media("kept.jpg"), (media("small.jpg"), media("smaller.jpg")))
OTHER = NearDecision(media("other.jpg"), (media("other-small.jpg"),))
VIDEO = NearDecision(media("clip.mp4"), (media("clip-wa.mp4"),))
SERIES = (
    BurstSeries((media("b1.jpg"), media("b2.jpg")), media("b1.jpg")),
    BurstSeries((media("c1.jpg"), media("c2.jpg")), media("c1.jpg")),
)
SIMILAR = SimilarFindings(near=(NEAR, OTHER), bursts=SERIES, videos=(VIDEO,))


def record(
    plan: CleanPlan, asked: CleanAsked, failed: tuple[Path, ...] = ()
) -> ReportRecord:
    """A clean record over the shared findings."""
    findings = AuditFindings((Path("/data/c"),), plan, similar=SIMILAR)
    incidents = tuple(Incident(path, "busy") for path in failed)
    outcome = Outcome(0, 0, 0, (), incidents)
    return ReportRecord(RunKind.CLEAN, findings, outcome, "run", asked=asked)


def test_a_plain_clean_shows_no_near_group_and_counts_them_as_left() -> None:
    """Without --tier near nothing similar is shown; the groups are only counted."""
    plain = record(CleanPlan(decisions=(), broken=()), CleanAsked())
    shown = shown_similar(plain)
    assert (shown.near, shown.videos, shown.bursts) == ((), (), ())
    done = clean_done(plain)
    assert done is not None
    assert (done.near, done.near_left, done.bursts, done.bursts_left) == (0, 3, 0, 2)


def test_the_near_tier_shows_only_what_it_moved() -> None:
    """The moved groups, less a copy the run failed on; videos apart."""
    plan = CleanPlan(decisions=(), broken=(), near=(NEAR, VIDEO))
    near = record(plan, CleanAsked(near=True), (media("smaller.jpg").path,))
    shown = shown_similar(near)
    assert [d.removable for d in shown.near] == [(media("small.jpg"),)]
    assert shown.videos == (VIDEO,)
    done = clean_done(near)
    assert done is not None
    assert (done.near, done.near_left) == (2, 1)


def test_bursts_with_decisions_count_the_shots_set_aside() -> None:
    """`--decisions`: the shots moved are counted, the other series left."""
    choice = BurstChoice(kept=(media("b1.jpg"),), discarded=(media("b2.jpg"),))
    plan = CleanPlan(decisions=(), broken=(), bursts=(choice,))
    done = clean_done(record(plan, CleanAsked(bursts=True)))
    assert done is not None
    assert (done.bursts, done.bursts_left, done.asked.bursts) == (1, 1, True)


def test_an_audit_has_no_done_block_and_old_summaries_load() -> None:
    """The audit keeps every finding; summary.json without the flags still loads."""
    audit = ReportRecord(
        RunKind.AUDIT,
        AuditFindings((), CleanPlan(decisions=(), broken=()), similar=SIMILAR),
    )
    assert clean_done(audit) is None
    assert shown_similar(audit) is SIMILAR
    assert asked_flags(None) == {"near_tier": False, "bursts_decided": False}
    old = ReportSummary.model_validate({"folder": "x", "kind": "clean", **MINIMAL})
    assert (old.near_tier, old.bursts_decided) == (False, False)


def _report(reports: Path, name: str, roots: tuple[str, ...]) -> str:
    """Write a report folder named `<day>-<kind>` (`02-audit`)."""
    day, kind = name.split("-")
    folder = f"202610{day}-000000-{kind}"
    write_summary(
        reports / folder,
        kind=RunKind(kind),
        roots=roots,
        created_at=datetime(2026, 10, int(day), tzinfo=UTC),
    )
    (reports / folder / "report.html").write_text("x", encoding="utf-8")
    return folder


def test_a_clean_links_the_latest_audit_of_the_same_folders(tmp_path: Path) -> None:
    """Two audits of other folders, two of these: the newest of these, else None."""
    clean = record(CleanPlan(decisions=(), broken=()), CleanAsked())
    assert latest_audit_link(tmp_path, clean) is None
    _report(tmp_path, "01-audit", ("/data/c",))
    second = _report(tmp_path, "02-audit", ("/data/c",))
    _report(tmp_path, "03-audit", ("/data/d",))
    _report(tmp_path, "04-clean", ("/data/c",))
    link = latest_audit_link(tmp_path, clean)
    assert link == f"../{second}/report.html"
    audit = ReportRecord(RunKind.AUDIT, clean.findings)
    assert latest_audit_link(tmp_path, audit) is None
