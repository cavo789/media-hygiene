"""0397: a group checked on the search page, sorted exactly, journaled, undone.

The files a period's rule takes (0396's trial) are written as file choices into
`sort-decisions.json` of the latest classify run, read back, then `sort` runs cut to
those rows: only them move; two groups are two runs, two undos.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from typing import TYPE_CHECKING

import pytest

from media_hygiene.classify.page_decisions import PAGE_DECISIONS_FILE_NAME
from media_hygiene.classify.plan_file import ClassifyPlan
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.config.classify_rules import ClassifyRule
from media_hygiene.errors import MediaHygieneError
from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.scan.progress import NullProgress
from media_hygiene.search.rule_models import RuleTry
from media_hygiene.services.audit import AuditService
from media_hygiene.services.group_sort import sort_group
from media_hygiene.services.rule_trial import try_rule
from media_hygiene.services.runtime import Runtime
from tests.integration.test_sort_event import SPRING, SPRING_SHOTS, two_events
from tests.support.scenes import Shot, write_shot
from tests.support.sorting import PARTY, PARTY_SHOTS, PHOTOS, snapshot, undo

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.locations import Locations


def _folders(runtime: Runtime, folder: Path, days: str) -> dict[Path, str]:
    """Where the rule of `days` would put the photos of `folder`, as the page shows."""
    rule = ClassifyRule(
        name="Group", match=RuleMatch.DATE_RANGE, dates=days, category="Fêtes/Groupe"
    )
    files = [
        PhotoVersion(path, path.stat().st_size, path.stat().st_mtime_ns)
        for path in sorted(folder.glob("*.jpg"))
    ]
    assert runtime.index_file is not None
    with closing(sqlite3.connect(runtime.index_file)) as connection:
        tried = try_rule(runtime, connection, RuleTry(rule, "", files))
    return {path: where.folder for path, where in tried.items() if where.folder}


def test_two_groups_sorted_then_undone_one_by_one(locations: Locations) -> None:
    """Only each group's files move, to the folder shown; each run undone on its own."""
    runtime, workbook, _sizes = two_events(locations)
    data = locations.data_dir
    before = snapshot(data)
    spring = _folders(runtime, data / SPRING, "2017-05-01..2017-05-01")
    assert len(spring) == SPRING_SHOTS
    assert set(spring.values()) == {"2017/Fêtes/Groupe"}
    first = sort_group(runtime, spring, "Fêtes/Groupe")
    assert (first.moved, first.verified, first.intact) == (SPRING_SHOTS,) * 2 + (True,)
    assert not list((data / SPRING).glob("*.jpg"))
    assert len(list((data / PARTY).glob("*.jpg"))) == PARTY_SHOTS
    decisions = (workbook.parent / PAGE_DECISIONS_FILE_NAME).read_text("utf-8")
    assert decisions.count("2017/Fêtes/Groupe") == SPRING_SHOTS
    party = _folders(runtime, data / PARTY, "2016-07-14..2016-07-14")
    second = sort_group(runtime, party, "Fêtes/Groupe")
    assert second.moved == PARTY_SHOTS
    assert second.run_id != first.run_id
    undo(runtime, second.run_id)
    assert len(list((data / PARTY).glob("*.jpg"))) == PARTY_SHOTS
    undo(runtime, first.run_id)
    after = snapshot(data)
    assert {p: f for p, f in after.items() if p.endswith(".jpg")} == {
        p: f for p, f in before.items() if p.endswith(".jpg")
    }


def test_a_file_the_run_does_not_know_is_counted_not_moved(
    locations: Locations,
) -> None:
    """A photo added after classify: left where it is, counted."""
    runtime, _workbook, _sizes = two_events(locations)
    data = locations.data_dir
    spring = _folders(runtime, data / SPRING, "2017-05-01..2017-05-01")
    late = data / SPRING / "late.jpg"
    late.write_bytes(next(iter(spring)).read_bytes())
    done = sort_group(runtime, {**spring, late: "2017/Fêtes/Groupe"}, "Fêtes/Groupe")
    assert (done.moved, done.unknown) == (SPRING_SHOTS, 1)
    assert late.exists()


def test_a_file_audited_after_classify_joins_the_plan_then_moves(
    locations: Locations,
) -> None:
    """0452: photos imported since classify, audited: a row each, moved, undone."""
    runtime, workbook, _sizes = two_events(locations)
    data = locations.data_dir
    plan_file = workbook.with_name("plan.json")
    before = ClassifyPlan.model_validate_json(plan_file.read_text("utf-8"))
    late = data / PHOTOS / "Phone" / "Camera" / "late.jpg"
    write_shot(late, Shot(99, taken_at="2017:05:01 20:00:00"))
    AuditService(runtime, NullProgress()).run()
    spring = _folders(runtime, data / SPRING, "2017-05-01..2017-05-01")
    done = sort_group(runtime, {**spring, late: "2017/Fêtes/Groupe"}, "Fêtes/Groupe")
    assert (done.moved, done.unknown) == (SPRING_SHOTS + 1, 0)
    assert not late.exists()
    assert (data / "c" / "2017" / "Fêtes" / "Groupe" / "late.jpg").is_file()
    # The plan and its workbook are left as classify wrote them: still one pair.
    assert ClassifyPlan.model_validate_json(plan_file.read_text("utf-8")) == before
    again = _folders(
        runtime, data / "c" / "2017" / "Fêtes" / "Groupe", "2017-05-01..2017-05-01"
    )
    second = sort_group(runtime, again, "Fêtes/Groupe")
    assert (second.run_id, second.unknown) == ("", 0)
    undo(runtime, done.run_id)
    assert late.is_file()


def test_without_a_journal_nothing_is_written_nor_moved(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The guard first: no decision written, no file moved, the sentence raised."""
    runtime, workbook, _sizes = two_events(locations)
    data = locations.data_dir
    spring = _folders(runtime, data / SPRING, "2017-05-01..2017-05-01")
    before = snapshot(data)
    monkeypatch.setattr(Runtime, "persistent", lambda _self, _kind: False)
    with pytest.raises(MediaHygieneError, match=r"(?i)journal"):
        sort_group(runtime, spring, "Fêtes/Groupe")
    assert snapshot(data) == before
    assert not (workbook.parent / PAGE_DECISIONS_FILE_NAME).exists()


def test_a_group_sorted_twice_moves_nothing_and_makes_no_run(
    locations: Locations,
) -> None:
    """The files at their new place are known as sorted: no 'run classify', no run."""
    runtime, _workbook, _sizes = two_events(locations)
    data = locations.data_dir
    spring = _folders(runtime, data / SPRING, "2017-05-01..2017-05-01")
    first = sort_group(runtime, spring, "Fêtes/Groupe")
    runs = sorted(locations.journal_dir.glob("*.jsonl"))
    moved_to = data / "c" / "2017" / "Fêtes" / "Groupe"  # the drive is the root here
    again = _folders(runtime, moved_to, "2017-05-01..2017-05-01")
    assert len(again) == SPRING_SHOTS, again
    second = sort_group(runtime, again, "Fêtes/Groupe")
    assert first.moved == SPRING_SHOTS
    assert (second.run_id, second.already, second.unknown) == ("", SPRING_SHOTS, 0)
    assert sorted(locations.journal_dir.glob("*.jsonl")) == runs


def test_a_group_sort_counts_only_the_folders_it_touches(locations: Locations) -> None:
    """The manifest's census covers the source and target folders, not the tree."""
    runtime, _workbook, _sizes = two_events(locations)
    spring = _folders(runtime, locations.data_dir / SPRING, "2017-05-01..2017-05-01")
    done = sort_group(runtime, spring, "Fêtes/Groupe")
    manifest = next(locations.reports_dir.glob(f"{done.run_id}-sort/manifest.json"))
    roots = json.loads(manifest.read_text("utf-8"))["roots"]
    assert all("Mai 2017" in root or "Groupe" in root for root in roots), roots
