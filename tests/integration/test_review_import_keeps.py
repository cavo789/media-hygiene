"""0630: the burst review of an import's series keeps the library's other decisions."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from media_hygiene.report.decisions import read_decisions
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.burst_opening import BurstOpening, open_bursts
from media_hygiene.services.reviewing import open_review
from tests.support.review import write_burst
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations


def test_a_series_left_out_keeps_its_decision(locations: Locations) -> None:
    """Shown again on the import's series only, a set-aside shot stays in the file."""
    write_burst(locations.data_dir)
    runtime = make_runtime(locations)
    findings = AuditService(runtime, NullProgress()).run()
    target = locations.reports_dir / "decisions.json"
    open_review(runtime, findings, target).decide({0: frozenset({1})})
    before = read_decisions(target).bursts
    assert before[0].discarded
    shots = findings.similar.bursts[0].shots
    hidden = frozenset(runtime.mapper.to_host(shot.path) for shot in shots)
    none = replace(findings, similar=replace(findings.similar, bursts=()))
    open_bursts(runtime, BurstOpening(none, target, hidden))
    assert read_decisions(target).bursts == before
    open_bursts(runtime, BurstOpening(none, target))  # nothing hidden: not kept
    assert read_decisions(target).bursts == ()
