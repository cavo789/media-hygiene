"""`classify` again leaves every sorted file in place, however it got there (0404).

With the convention (0401), a file in `YYYY/YYYY-MM/<name>`, or right in `YYYY/YYYY-MM`,
is in place. One test per way a file arrives there: arrange, audit, `classify`, then no
row to move for those files.
"""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING

from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.classify.rules_file import add_rule
from media_hygiene.config.classify_rules import ClassifyRule
from media_hygiene.config.loader import write_default_config
from media_hygiene.constants import Locale
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.classify import ClassifyService
from media_hygiene.services.selection_models import Picked
from media_hygiene.services.selection_move import SelectionMover
from media_hygiene.services.sort_disk import disk_progress
from media_hygiene.services.sort_event import sort_event
from tests.support.runtime import make_runtime
from tests.support.scenes import Shot, write_shot
from tests.support.sorting import (
    PARTY,
    WEDDING,
    audited_library,
    classify,
    name_first_event,
    sort,
)

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.locations import Locations
    from media_hygiene.services.runtime import Runtime

_MONTH = "c/2016/2016-07"  # the drive is the root of the tests' tree


def _moving(runtime: Runtime) -> list[tuple[Path, str | None]]:
    """Audit again, classify again: the files sorted (in `2016/`) that would move.

    Args:
        runtime: The runtime.

    Returns:
        Each of them proposed elsewhere than where it is, and its folder.
    """
    AuditService(runtime, NullProgress()).run()
    proposals = ClassifyService(runtime, NullProgress()).run().classification.proposals
    year = runtime.locations.data_dir / "c" / "2016"
    sorted_here = [p for p in proposals if p.file.path.is_relative_to(year)]
    assert sorted_here  # the files sorted are known to the new run
    return [(p.file.path, p.folder) for p in sorted_here if not p.in_place]


def _with_config(locations: Locations) -> Runtime:
    """The library audited, with a `config.toml` to write rules into.

    Args:
        locations: Mount points.

    Returns:
        The runtime.
    """
    write_default_config(locations.config_file, Locale.EN)
    return audited_library(locations)


def test_1_sorted_by_a_rule_stays(locations: Locations) -> None:
    """A date rule names the party; `sort` of the whole plan; then nothing moves."""
    runtime = _with_config(locations)
    rule = ClassifyRule(
        name="Fair",
        match=RuleMatch.DATE_RANGE,
        dates="2016-07-14..2016-07-14",
        category="Kermesse",
    )
    add_rule(locations.config_file, rule)
    runtime = make_runtime(locations)  # config.toml read again
    classify(runtime)
    assert sort(runtime).moves.moved
    assert (locations.data_dir / _MONTH / "Kermesse").is_dir()
    assert not _moving(runtime)


def test_2_sorted_by_one_event_stays(locations: Locations) -> None:
    """*Sort this event now* (`sort --event`), then nothing moves."""
    runtime = audited_library(locations)
    workbook = classify(runtime)
    name_first_event(workbook)
    plan = workbook.with_name("plan.json").read_text("utf-8")
    event_id = plan.split('"events"')[1].split('"id": "')[1].split('"')[0]
    assert sort_event(runtime, str(workbook), event_id) is not None
    assert not _moving(runtime)


def test_3_moved_from_the_search_page_stays(locations: Locations) -> None:
    """*Move to an event…*, no rule saved: then nothing moves."""
    runtime = audited_library(locations)
    classify(runtime)
    party = dict(enumerate(sorted((locations.data_dir / PARTY).glob("*.jpg"))))
    assert SelectionMover(runtime).move(Picked(party), "Kermesse")["moved"] == len(
        party
    )
    assert not _moving(runtime)


def test_4_moved_by_hand_in_explorer_stays(locations: Locations) -> None:
    """Never seen by the tool: moved by hand into `2016/2016-07/Kermesse`."""
    runtime = audited_library(locations)
    shutil.move(locations.data_dir / PARTY, locations.data_dir / _MONTH / "Kermesse")
    assert not _moving(runtime)
    progress = disk_progress(runtime)
    assert progress is not None
    assert progress.sorted >= 6


def test_5_an_event_folder_renamed_by_hand_stays_under_its_new_name(
    locations: Locations,
) -> None:
    """`Kermesse` renamed `School fair` in Explorer: stays under the new name."""
    runtime = audited_library(locations)
    sorted_to = locations.data_dir / _MONTH / "Kermesse"
    shutil.move(locations.data_dir / PARTY, sorted_to)
    AuditService(runtime, NullProgress()).run()
    sorted_to.rename(sorted_to.with_name("School fair"))
    assert not _moving(runtime)


def test_6_a_file_directly_in_its_month_stays_beside_a_named_event(
    locations: Locations,
) -> None:
    """Nothing special that month, though the party of that month has its folder."""
    runtime = audited_library(locations)
    month = locations.data_dir / _MONTH
    shutil.move(locations.data_dir / PARTY, month / "Kermesse")
    write_shot(month / "plain.jpg", Shot(90, taken_at="2016:07:14 12:30:00"))
    assert not _moving(runtime)


def test_7_a_stage_below_the_event_stays(locations: Locations) -> None:
    """`2016/2016-07/Holidays/Budva`: the stage the user named is kept."""
    runtime = audited_library(locations)
    shutil.move(
        locations.data_dir / PARTY, locations.data_dir / _MONTH / "Holidays" / "Budva"
    )
    assert not _moving(runtime)


def test_8_a_date_rule_written_later_leaves_a_folder_named_otherwise(
    locations: Locations,
) -> None:
    """The wedding sorted into `2018/2018-06/Mariage`; then a rule of that day.

    Decided with the maintainer (2026-10-25), in the engine: a date rule of another
    name takes none of the files sorted already; the rule's own name would.
    """
    runtime = _with_config(locations)
    sorted_to = locations.data_dir / "c/2018/2018-06/Mariage"
    shutil.move(locations.data_dir / WEDDING, sorted_to)
    AuditService(runtime, NullProgress()).run()
    for name, category in (("Garden", "Garden party"), ("Wedding", "Mariage")):
        rule = ClassifyRule(
            name=name,
            match=RuleMatch.DATE_RANGE,
            dates="2018-06-02..2018-06-02",
            category=category,
        )
        add_rule(locations.config_file, rule)
        runtime = make_runtime(locations)
        found = ClassifyService(runtime, NullProgress()).run().classification.proposals
        wedding = [p for p in found if p.file.path.is_relative_to(sorted_to)]
        assert wedding
        expected = {"Existing folders"} if name == "Garden" else {"Wedding"}
        assert {p.rule for p in wedding} == expected
        assert all(p.in_place for p in wedding)
