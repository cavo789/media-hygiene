"""The Czkawka tip: before a large clean, or when asked; not on a small first try."""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

import pytest

from media_hygiene.cli.audit_actions import SECOND_OPINION_FROM, second_opinion
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.plan.models import CleanPlan


def _plan(copies: int) -> CleanPlan:
    """A stand-in plan setting this many copies aside, one group each.

    Args:
        copies: The copies.

    Returns:
        What `second_opinion` reads.
    """
    plan = SimpleNamespace(decisions=(object(),) * copies, removable_count=copies)
    return cast("CleanPlan", plan)


@pytest.mark.parametrize(
    "case",
    [
        (0, True, False),
        (1, False, False),
        (1, True, True),
        (SECOND_OPINION_FROM, False, True),
    ],
)
def test_second_opinion_waits_for_a_large_clean(
    tmp_path: Path, case: tuple[int, bool, bool]
) -> None:
    """A first audit with one copy keeps its tips for the cache and --prefer."""
    copies, verbose, shown = case
    runtime = make_runtime(make_locations(tmp_path))
    runtime = replace(runtime, output=replace(runtime.output, verbose=verbose))
    second_opinion(runtime, _plan(copies))
    _step, tips, _settings = runtime.output.board.drain()
    assert any("Czkawka" in tip.text for tip in tips) is shown
