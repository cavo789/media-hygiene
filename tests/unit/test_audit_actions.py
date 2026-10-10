"""What an audit lets the user do: gain and effort per action, at most three lines."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

import pytest

from media_hygiene.report.actions import ActionCommands, audit_actions, effort

if TYPE_CHECKING:
    from media_hygiene.plan.models import AuditFindings

_COMMANDS = ActionCommands(clean="docker clean", near="docker near", review="docker r")


def _findings(copies: int, near: int, bursts: int) -> AuditFindings:
    """Stand-in findings with these counts.

    Args:
        copies: Extra identical copies, in one group each (1 KB each).
        near: Groups of near duplicates.
        bursts: Burst series.

    Returns:
        What `audit_actions` reads.
    """
    plan = SimpleNamespace(
        decisions=(object(),) * copies,
        removable_count=copies,
        reclaimable=copies * 1024,
    )
    similar = SimpleNamespace(
        near=(object(),) * near, videos=(), bursts=(object(),) * bursts
    )
    return cast("AuditFindings", SimpleNamespace(plan=plan, similar=similar))


@pytest.mark.parametrize(
    ("seconds", "said"),
    [
        (0, "1 min"),
        (30, "1 min"),
        (61, "2 min"),
        (3600, "1 h 00 min"),
        (3901, "1 h 06 min"),
    ],
)
def test_effort_is_rounded_up_to_the_minute(seconds: int, said: str) -> None:
    """Never "0 min"; hours beyond sixty minutes."""
    assert effort(seconds) == said


def test_each_action_says_its_gain_and_its_effort() -> None:
    """Copies first (no risk), near duplicates to look at, bursts optional."""
    actions = audit_actions(_findings(12, 1, 3), _COMMANDS)
    assert [action.icon for action in actions] == ["✅", "👀", "🎞️"]
    assert actions[0].text == "12 identical copies, 12.0 KB: no risk, one command."
    assert "1 group of near duplicates to look at (~1 min)" in actions[1].text
    assert actions[2].text.startswith("3 burst series: optional, ~2 min in 'review'")
    assert [action.command for action in actions] == [
        "docker clean",
        "docker near",
        "docker r",
    ]


def test_nothing_found_means_no_action() -> None:
    """A clean library: no line at all."""
    assert not audit_actions(_findings(0, 0, 0), _COMMANDS)
