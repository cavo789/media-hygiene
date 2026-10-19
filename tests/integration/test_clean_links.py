"""A pair keeping both names (0213): each copy becomes a hard link, `undo` separates.

On real files: the bytes are compared first, the two names share one inode after,
a run stopped halfway leaves the copy or the link under each name (never nothing),
and `undo` gives two independent files with the same bytes and the copy's date.
"""

from __future__ import annotations

import errno
import html
import json
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.actions.clean import CleanExecutor
from media_hygiene.actions.clean_links import draft_of
from media_hygiene.actions.journal import JournalWriter, journal_file, read_journal
from media_hygiene.actions.kinds import ActionKind, Status
from media_hygiene.actions.runs import summarize
from media_hygiene.actions.undo import UndoExecutor
from media_hygiene.constants import MediaKind
from media_hygiene.plan.models import CleanPlan, KeepDecision
from media_hygiene.plan.review import PairAction
from media_hygiene.scan.hashing import full_digest
from media_hygiene.scan.models import MediaFile
from media_hygiene.scan.progress import NullProgress
from tests.support.cli import run
from tests.support.journaled import JOURNAL_NAME, journaled

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner

    from media_hygiene.actions.outcome import Outcome
    from media_hygiene.paths.locations import Locations

VACANCES = "C:\\Family Photos\\2019\\Vacances"
ETE = "C:\\Users\\Public\\Pictures\\Été 2019"
SELECT = re.compile(
    r'<select class="decision" data-kept-in="([^"]*)" '
    r'data-removed-from="([^"]*)"[^>]*>(.*?)</select>',
    re.DOTALL,
)
LINK_OPTION = '<option value="link">'


def offered(report: Path) -> dict[tuple[str, str], bool]:
    """Each pair of the report, and whether it offers to keep both names."""
    page = report.read_text(encoding="utf-8")
    return {
        (html.unescape(kept), html.unescape(removed)): LINK_OPTION in body
        for kept, removed, body in SELECT.findall(page)
    }


def test_both_names_kept_as_links_then_undone(
    cli: CliRunner, locations: Locations
) -> None:
    """Demo tree: the two C: folders linked both ways, then undone; D: never offered."""
    data = locations.data_dir
    vacances, ete = (
        data / "c/Family Photos/2019/Vacances",
        data / "c/Users/Public/Pictures/Été 2019",
    )
    dates = {name: (ete / name).stat().st_mtime_ns for name in ("IMG_0001.jpg",)}
    assert run(cli, "audit").exit_code == 0
    [report] = locations.reports_dir.glob("*-audit/report.html")
    pairs = offered(report)
    assert pairs[VACANCES, ETE]
    assert pairs[ETE, VACANCES]
    assert not any(ok for (kept, removed), ok in pairs.items() if kept[0] != removed[0])
    link_both_ways(report, locations.reports_dir / "decisions.json")
    result = run(cli, "clean", "--yes", "--decisions", "decisions.json")
    assert result.exit_code == 0, result.output
    said = " ".join(result.output.split())  # the console wraps its lines
    assert "pairs keeping both names (links): 2" in said
    assert "one photo under two names" in said
    for index in (1, 2, 3):
        name = f"IMG_000{index}.jpg"
        assert (vacances / name).samefile(ete / name), name
    assert not (vacances / "IMG_0001 (1).jpg").exists()  # its pair was not linked
    [journal] = locations.journal_dir.glob("*.jsonl")
    links = [e for e in read_journal(journal) if e.action is ActionKind.LINK_DUPLICATE]
    assert {e.status for e in links} == {Status.PENDING, Status.DONE}
    assert all(e.keeper and e.sha256 for e in links)
    again = run(cli, "audit")
    assert "reachable through two paths" in " ".join(again.output.split())
    assert (VACANCES, ETE) not in offered(_newest(locations))
    assert run(cli, "undo").exit_code == 0
    for index in (1, 2, 3):
        name = f"IMG_000{index}.jpg"
        assert not (vacances / name).samefile(ete / name), name
        assert full_digest(vacances / name) == full_digest(ete / name)
    assert (ete / "IMG_0001.jpg").stat().st_mtime_ns == dates["IMG_0001.jpg"]
    assert (vacances / "IMG_0001 (1).jpg").is_file()


def link_both_ways(report: Path, target: Path) -> None:
    """Write the decisions linking the two C: folders both ways, as the page would."""
    decided = [
        {"kept_in": kept, "removed_from": removed, "action": PairAction.LINK.value}
        for kept, removed in ((VACANCES, ETE), (ETE, VACANCES))
    ]
    roots = json.loads(re.findall(r"const roots = (.*);", report.read_text())[0])
    decisions = {"version": 1, "roots": roots, "pairs": decided}
    target.write_text(json.dumps(decisions))


def _newest(locations: Locations) -> Path:
    """The report of the latest audit.

    Two audits in the same second write `<stamp>-audit` then `<stamp>-audit-2`: the
    newest is the last written, not the last name (a CI failure, 2026-10-19).
    """
    reports = locations.reports_dir.glob("*-audit*/report.html")
    return max(reports, key=lambda report: report.stat().st_mtime_ns)


def photo(path: Path, data: bytes = b"photo") -> MediaFile:
    """Write a file and describe it as the audit saw it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    info = path.stat()
    return MediaFile(path, info.st_size, info.st_mtime_ns, MediaKind.IMAGE)


def linking(
    tmp_path: Path, copy_bytes: bytes = b"photo"
) -> tuple[Path, Path, CleanPlan]:
    """A kept file in `A`, its copy in `B`, and the plan linking the copy."""
    keeper, copy = photo(tmp_path / "A/a.jpg"), photo(tmp_path / "B/a.jpg")
    copy.path.write_bytes(copy_bytes)
    decision = KeepDecision("digest", 5, keeper, (), linked=(copy,))
    return keeper.path, copy.path, CleanPlan((decision,), ())


def clean_links(tmp_path: Path, plan: CleanPlan) -> Outcome:
    """Execute the plan, journaled in `tmp_path`."""
    with journaled(tmp_path) as context:
        return CleanExecutor(context).run(plan)


def undo(tmp_path: Path) -> Outcome:
    """Undo the run journaled in `tmp_path`."""
    journal = tmp_path / JOURNAL_NAME
    entries = read_journal(journal)
    with JournalWriter.open(journal) as writer:
        return UndoExecutor(writer, NullProgress()).run(entries)


def test_the_copy_becomes_a_link_after_the_byte_comparison(tmp_path: Path) -> None:
    """One inode under two names; the draft name is gone; `undo` separates them."""
    keeper, copy, plan = linking(tmp_path)
    outcome = clean_links(tmp_path, plan)
    assert (outcome.done, outcome.bytes_done, outcome.skipped) == (1, 5, ())
    assert keeper.samefile(copy)
    assert not draft_of(copy).exists()
    assert sorted(p.name for p in copy.parent.iterdir()) == ["a.jpg"]
    assert not undo(tmp_path).skipped
    assert not keeper.samefile(copy)
    assert copy.read_bytes() == keeper.read_bytes() == b"photo"
    assert sorted(p.name for p in copy.parent.iterdir()) == ["a.jpg"]


def test_a_copy_that_differs_is_never_linked(tmp_path: Path) -> None:
    """Same size, other bytes since the audit: skipped, both files as they were."""
    keeper, copy, plan = linking(tmp_path, b"other")
    outcome = clean_links(tmp_path, plan)
    assert outcome.done == 0
    assert "no longer identical" in outcome.skipped[0].reason
    assert not keeper.samefile(copy)
    assert copy.read_bytes() == b"other"


def test_a_link_across_disks_is_refused_and_said(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`os.link` refuses another device: the copy stays whole, the reason is told."""
    keeper, copy, plan = linking(tmp_path)

    def cross(_source: Path, _target: Path) -> None:
        raise OSError(errno.EXDEV, os.strerror(errno.EXDEV))

    monkeypatch.setattr(os, "link", cross)
    outcome = clean_links(tmp_path, plan)
    assert "two disks or two mounts" in outcome.failed[0].reason
    assert copy.read_bytes() == b"photo"
    assert not keeper.samefile(copy)
    assert not draft_of(copy).exists()
    assert not undo(tmp_path).skipped  # pending, never happened: nothing to undo


def test_a_run_stopped_before_the_rename_leaves_the_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The rename fails: the copy is still under its name, the draft removed."""
    keeper, copy, plan = linking(tmp_path)
    renaming = Path.replace

    def stopped(self: Path, target: Path) -> Path:
        if self == draft_of(copy):
            raise OSError(errno.EIO, os.strerror(errno.EIO))
        return renaming(self, target)

    monkeypatch.setattr(Path, "replace", stopped)
    outcome = clean_links(tmp_path, plan)
    assert len(outcome.failed) == 1
    assert copy.read_bytes() == b"photo"
    assert not keeper.samefile(copy)
    assert not draft_of(copy).exists()
    monkeypatch.undo()
    assert undo(tmp_path).done == 0


def test_a_run_killed_after_the_rename_is_undone(tmp_path: Path) -> None:
    """Killed before its `done` line: the link is made, `undo` still separates it."""
    keeper, copy, plan = linking(tmp_path)
    clean_links(tmp_path, plan)
    journal = tmp_path / JOURNAL_NAME
    lines = journal.read_text(encoding="utf-8").splitlines()
    journal.write_text(lines[0] + "\n", encoding="utf-8")  # the pending line only
    assert read_journal(journal)[0].status is Status.PENDING
    assert undo(tmp_path).done == 1
    assert not keeper.samefile(copy)
    assert copy.read_bytes() == b"photo"


def test_a_draft_left_by_a_killed_run_is_taken_over(tmp_path: Path) -> None:
    """A run killed after `os.link`: its draft is a name of the kept file, replaced."""
    keeper, copy, plan = linking(tmp_path)
    draft_of(copy).hardlink_to(keeper)
    assert clean_links(tmp_path, plan).done == 1
    assert keeper.samefile(copy)
    assert not draft_of(copy).exists()


def test_a_foreign_file_under_the_draft_name_stops_the_link(tmp_path: Path) -> None:
    """Never replaced: a file of the user under the draft name is left, said."""
    keeper, copy, plan = linking(tmp_path)
    draft_of(copy).write_bytes(b"mine")
    outcome = clean_links(tmp_path, plan)
    assert "in the way" in outcome.failed[0].reason
    assert draft_of(copy).read_bytes() == b"mine"
    assert not keeper.samefile(copy)


def test_undo_leaves_a_name_that_is_no_link_any_more(tmp_path: Path) -> None:
    """Saved since through a new file (an editor), or its kept file gone: kept."""
    keeper, copy, plan = linking(tmp_path)
    clean_links(tmp_path, plan)
    edited = copy.with_name("edit.tmp")
    edited.write_bytes(b"edited")
    edited.replace(copy)  # an atomic save: a new inode under the name
    [skipped] = undo(tmp_path).skipped
    assert "independent file already" in skipped.reason
    assert copy.read_bytes() == b"edited"
    assert keeper.read_bytes() == b"photo"


def test_undo_with_the_kept_file_moved_still_separates(tmp_path: Path) -> None:
    """The kept file moved since: the name may still share it, made independent."""
    keeper, copy, plan = linking(tmp_path)
    clean_links(tmp_path, plan)
    moved = keeper.with_name("moved.jpg")
    keeper.replace(moved)
    assert undo(tmp_path).done == 1
    assert not moved.samefile(copy)
    assert copy.read_bytes() == moved.read_bytes() == b"photo"


def test_history_counts_the_links_and_their_space(tmp_path: Path) -> None:
    """The run frees the copy's bytes, deletes nothing: listed as linked."""
    _keeper, _copy, plan = linking(tmp_path)
    clean_links(tmp_path, plan)
    journal_dir = tmp_path / "journal"
    journal_dir.mkdir()
    (tmp_path / JOURNAL_NAME).replace(journal_file(journal_dir, "20261019-120000"))
    summary = summarize(journal_dir, "20261019-120000")
    assert (summary.deleted, summary.linked, summary.freed) == (0, 1, 5)
