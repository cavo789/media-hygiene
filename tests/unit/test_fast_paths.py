"""Every fast path says what it skips and names its visual twin (0593, 0590-0592)."""

from __future__ import annotations

from typing import Final

from media_hygiene.cli.menu_catalog import catalog
from media_hygiene.cli.menu_entry import Kind, Risk
from media_hygiene.cli.menu_twins import REPORTS_PAGE, twins
from media_hygiene.review.step_watch import served_here

# Change files without being a page, yet are no fast path: no photo to look at first
# (their own page leads to them, or they write beside the photos).
_NOT_FAST: Final = frozenset({"apply", "album", "people-forget", "xmp", "restore"})


def test_each_writing_console_step_is_a_fast_path_with_a_twin() -> None:
    """New writing step without a page: name its twin, or say why it has none."""
    known = catalog()
    names = {step.name for step in known.steps}
    known_twins = twins()
    for step in known.steps:
        writes = step.risk is not Risk.SAFE and step.kind is Kind.CONSOLE
        if writes and step.name not in _NOT_FAST and not step.planned:
            assert step.name in known_twins, step.name
    for name, twin in known_twins.items():
        assert name in names
        assert twin.says in known.step(name).text  # no fast path removed: it says so
        assert bool(twin.step) != bool(twin.page), name
        assert not twin.step or known.step(twin.step).kind is Kind.PAGE


def test_the_report_twin_is_a_page_of_the_home_server() -> None:
    """The twin's path is the one the server answers."""
    assert served_here(("reports",)) == REPORTS_PAGE


def test_purge_reaches_the_quarantine_in_one_click_of_the_home_page() -> None:
    """*Purge*'s twin is served here: a plain link, no restart (0591, 0594)."""
    step = catalog().step(twins()["purge"].step)
    assert served_here(tuple(step.command.split())) == "/quarantine/"
    assert served_here(("import", "--pick")) == "/import/"


def test_the_stale_sort_wording_is_gone() -> None:
    """The Events tab lists the index's events, not the plan's (0572)."""
    assert "on the page or in the workbook" not in catalog().step("sort").text
