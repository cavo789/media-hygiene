"""A burst shot set aside, purged, then back under another name: proposed (0216)."""

from __future__ import annotations

import os
from dataclasses import replace
from typing import TYPE_CHECKING

from media_hygiene.actions.journal import done_states, journal_file, read_journal
from media_hygiene.actions.kinds import FOLDER_ACTIONS, ActionKind, Phase
from media_hygiene.actions.purge import purge_run
from media_hygiene.actions.runs import summarize
from media_hygiene.cli.clean_confirm import confirm_clean
from media_hygiene.constants import MediaKind, RunKind
from media_hygiene.plan.similar_models import BurstChoice
from media_hygiene.report.actions import ActionCommands, audit_actions
from media_hygiene.report.views import ReportRecord
from media_hygiene.scan.models import MediaFile
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.clean import CleanMode, CleanService
from media_hygiene.services.reporting import write_report
from media_hygiene.services.undo import undo_run
from tests.support.runtime import make_runtime, output_of
from tests.support.scenes import scene

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.locations import Locations
    from media_hygiene.plan.models import AuditFindings
    from media_hygiene.services.runtime import Runtime


def media(path: Path) -> MediaFile:
    """The file as the audit sees it."""
    stat = path.stat()
    return MediaFile(path, stat.st_size, stat.st_mtime_ns, MediaKind.IMAGE)


def shots(data: Path) -> tuple[Path, Path]:
    """Two shots of a series: the one kept, the one set aside."""
    folder = data / "c" / "Photos" / "2024"
    folder.mkdir(parents=True)
    kept, aside = folder / "IMG_0001.jpg", folder / "IMG_0002.jpg"
    scene(1).save(kept, quality=90)
    scene(2).save(aside, quality=90)
    return kept, aside


def audit(runtime: Runtime) -> AuditFindings:
    """Audit the data mount."""
    return AuditService(runtime, NullProgress()).run()


def set_burst_aside(runtime: Runtime, kept: Path, aside: Path) -> str:
    """`clean --decisions` of a review setting one shot aside; the run."""
    findings = audit(runtime)
    choice = BurstChoice(kept=(media(kept),), discarded=(media(aside),))
    service = CleanService(runtime, NullProgress())
    service.ensure_ready(CleanMode(bursts=True))
    run_id, _outcome = service.execute(replace(findings.plan, bursts=(choice,)))
    return run_id


def bring_back(runtime: Runtime, locations: Locations) -> tuple[str, Path, bytes]:
    """A burst shot set aside, its run purged, its bytes back under another name.

    Returns:
        The run that set it aside, where it is back, its content.
    """
    kept, aside = shots(locations.data_dir)
    content = aside.read_bytes()
    first = set_burst_aside(runtime, kept, aside)
    purge_run(locations.quarantine_dir, first)
    back = locations.data_dir / "c" / "Phone backup" / "DCIM" / "20240101_1200.jpg"
    back.parent.mkdir(parents=True)
    back.write_bytes(content)
    return first, back, content


def test_a_purged_burst_shot_back_is_proposed_cleaned_and_undone(
    locations: Locations,
) -> None:
    """Found with its first run, moved by the next clean, forgotten after its undo."""
    runtime = make_runtime(locations)
    first, back, content = bring_back(runtime, locations)
    findings = audit(runtime)
    (found,) = findings.plan.returned
    assert found.file.path == back
    assert (found.remembered.run_id, found.remembered.action) == (
        first,
        ActionKind.QUARANTINE_BURST,
    )
    assert (
        found.remembered.at.date()
        == read_journal(journal_file(locations.journal_dir, first))[0].at.date()
    )
    actions = audit_actions(findings, ActionCommands(clean="mh clean"))
    assert len(actions) == 1
    action = actions[0]
    assert action.text.startswith("1 photo or video you had set aside is back")
    assert action.command == "mh clean"
    report = write_report(runtime, ReportRecord(RunKind.AUDIT, findings))
    assert report is not None
    html = report.read_text(encoding="utf-8")
    assert 'id="returned"' in html
    assert first in html

    assert confirm_clean(runtime, findings.plan, True)  # noqa: FBT003
    assert "↩️ 1 photo or video you had already set aside is back" in output_of(runtime)
    service = CleanService(runtime, NullProgress())
    second, outcome = service.execute(service.feasible(findings.plan))
    assert outcome.quarantined == 1
    assert not back.exists()
    entries = done_states(
        read_journal(journal_file(locations.journal_dir, second)), Phase.CLEAN
    )
    assert [e.action for e in entries if e.action not in FOLDER_ACTIONS] == [
        ActionKind.QUARANTINE_RETURNED  # its folders left empty go too
    ]
    assert summarize(locations.journal_dir, second).returned == 1
    assert not audit(runtime).plan.returned  # in the quarantine, out of /data

    undo_run(runtime, second, NullProgress())
    assert back.read_bytes() == content
    assert not audit(runtime).plan.returned  # the last word: the user wants it


def test_the_setting_off_never_looks(locations: Locations) -> None:
    """`[clean] returned = false`: the file back is a plain file."""
    runtime = make_runtime(locations)
    kept, aside = shots(locations.data_dir)
    content = aside.read_bytes()
    set_burst_aside(runtime, kept, aside)
    (locations.data_dir / "c" / "Photos" / "copy.jpg").write_bytes(content)
    off = make_runtime(locations, {"clean": {"returned": False}})
    assert not audit(off).plan.returned
    assert len(audit(runtime).plan.returned) == 1


def test_a_protected_folder_is_never_proposed(locations: Locations) -> None:
    """The file back in a protected folder stays where it is."""
    runtime = make_runtime(locations)
    kept, aside = shots(locations.data_dir)
    content = aside.read_bytes()
    set_burst_aside(runtime, kept, aside)
    safe = locations.data_dir / "c" / "Safe"
    safe.mkdir()
    (safe / "back.jpg").write_bytes(content)
    assert audit(runtime).plan.returned
    protect = make_runtime(locations, {"folders": {"protected": ["C:\\Safe"]}})
    assert not audit(protect).plan.returned


def test_an_exact_copy_set_aside_is_not_remembered(locations: Locations) -> None:
    """A copy whose content is kept elsewhere is a plain duplicate when it is back."""
    runtime = make_runtime(locations)
    kept, _aside = shots(locations.data_dir)
    copy = kept.with_name("IMG_0001 (1).jpg")
    copy.write_bytes(kept.read_bytes())
    service = CleanService(runtime, NullProgress())
    run_id, _outcome = service.execute(audit(runtime).plan)
    entries = read_journal(journal_file(locations.journal_dir, run_id))
    assert {entry.action for entry in entries} == {ActionKind.QUARANTINE_DUPLICATE}
    copy.write_bytes(kept.read_bytes())
    findings = audit(runtime)
    assert not findings.plan.returned
    assert findings.plan.removable_count == 1


def test_a_file_rewritten_since_the_audit_is_never_moved(
    locations: Locations,
) -> None:
    """Same size, same date, other bytes: the content is read again before the move."""
    runtime = make_runtime(locations)
    _first, back, _content = bring_back(runtime, locations)
    findings = audit(runtime)
    assert findings.plan.returned
    stat = back.stat()
    other = bytearray(back.read_bytes())
    other[-3] ^= 0xFF
    back.write_bytes(bytes(other))
    os.utime(back, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    service = CleanService(runtime, NullProgress())
    _second, outcome = service.execute(service.feasible(findings.plan))
    assert outcome.quarantined == 0
    assert back.read_bytes() == bytes(other)
    assert outcome.skipped
