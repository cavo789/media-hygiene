"""Near duplicates settled in rounds: what each round leaves is decided again."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.constants import MediaKind, NearReason
from media_hygiene.plan.keeper import KeepPolicy
from media_hygiene.plan.near_keeper import NearChoice
from media_hygiene.plan.near_rounds import Grouping, in_rounds
from media_hygiene.scan.models import MediaFile

if TYPE_CHECKING:
    from collections.abc import Sequence

DATA = Path("/data/c")
KEEPER = MediaFile(DATA / "K.jpg", 300, 0, MediaKind.IMAGE)
FIRST = MediaFile(DATA / "B.jpg", 200, 0, MediaKind.IMAGE)
SECOND = MediaFile(DATA / "C.jpg", 100, 0, MediaKind.IMAGE)
SHIELDED = MediaFile(DATA / "master/P.jpg", 100, 0, MediaKind.IMAGE)


def together(files: Sequence[MediaFile]) -> list[list[MediaFile]]:
    """Every file linked to every other, when there are two or more."""
    return [list(files)] if len(files) > 1 else []


def one_copy_at_a_time(cluster: list[MediaFile]) -> tuple[NearChoice, list[MediaFile]]:
    """K is kept; it takes the first unprotected copy left, and the protected one."""
    copies = [file for file in (FIRST, SECOND) if file in cluster][:1]
    return NearChoice(KEEPER, NearReason.SIZE), [*copies, SHIELDED]


def test_the_rounds_of_one_keeper_are_merged() -> None:
    """Two rounds give K two copies: one decision, its protected copy listed once."""
    grouping = Grouping(
        together, one_copy_at_a_time, KeepPolicy(protected=(DATA / "master",))
    )
    (decision,) = in_rounds([KEEPER, FIRST, SECOND, SHIELDED], grouping)
    assert decision.removable == (FIRST, SECOND)
    assert decision.protected == (SHIELDED,)
