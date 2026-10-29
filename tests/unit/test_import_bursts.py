"""After an import: the review page shows the import's burst series only (0480)."""

from __future__ import annotations

from pathlib import Path

from media_hygiene.constants import MediaKind
from media_hygiene.plan.models import AuditFindings, CleanPlan
from media_hygiene.plan.similar_models import BurstSeries, SimilarFindings
from media_hygiene.scan.models import MediaFile
from media_hygiene.services.import_bursts import import_bursts


def _media(name: str) -> MediaFile:
    return MediaFile(Path("/data/c") / name, 10, 0, MediaKind.IMAGE)


def test_only_the_series_holding_a_new_shot_are_kept() -> None:
    """A library series stays out; a series mixing old and new shots is in."""
    library = BurstSeries((_media("old1.jpg"), _media("old2.jpg")), _media("old1.jpg"))
    phone = BurstSeries(
        (_media("Phone/a.jpg"), _media("Phone/b.jpg")), _media("Phone/a.jpg")
    )
    mixed = BurstSeries((_media("old3.jpg"), _media("Phone/c.jpg")), _media("old3.jpg"))
    findings = AuditFindings(
        (),
        CleanPlan(decisions=(), broken=()),
        similar=SimilarFindings(bursts=(library, phone, mixed)),
    )
    new = {Path("/data/c/Phone/a.jpg"), Path("/data/c/Phone/c.jpg")}
    assert import_bursts(findings, new).similar.bursts == (phone, mixed)
    assert import_bursts(findings, ()).similar.bursts == ()
