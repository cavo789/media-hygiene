"""Which near duplicates a clean moves: the tier, then the review --near decisions."""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType

import pytest
from pydantic import ValidationError

from media_hygiene.constants import MediaKind, NearReason
from media_hygiene.plan.near_review import (
    NearAction,
    NearSelection,
    NearVerdict,
    selected,
)
from media_hygiene.plan.similar_models import NearDecision, SureReason
from media_hygiene.report.decisions import DecisionsFile
from media_hygiene.report.near_decisions import NearGroupDecision
from media_hygiene.report.near_reasons import near_why
from media_hygiene.scan.models import MediaFile


def media(name: str) -> MediaFile:
    """A file below /data/c."""
    return MediaFile(Path("/data/c") / name, 100, 0, MediaKind.IMAGE)


SURE = NearDecision(
    media("a.jpg"), (media("WhatsApp/a.jpg"),), sure=SureReason.MESSAGING_COPY
)
CHECK = NearDecision(media("b.jpg"), (media("small/b.jpg"), media("mail/b.jpg")))


def keepers(groups: tuple[NearDecision, ...]) -> list[str]:
    """The kept versions' names, for readable assertions."""
    return [str(group.keeper.path.relative_to("/data/c")) for group in groups]


def test_the_tier_alone() -> None:
    """near: the sure groups; near-all: every group."""
    assert keepers(selected((SURE, CHECK), NearSelection())) == ["a.jpg"]
    every = NearSelection(every=True)
    assert keepers(selected((SURE, CHECK), every)) == ["a.jpg", "b.jpg"]


def test_decisions_override_the_tier() -> None:
    """A sure group left alone stays; a group to check swapped keeps its copy."""
    verdicts = {
        SURE.keeper.path: NearVerdict(NearAction.LEAVE),
        CHECK.keeper.path: NearVerdict(NearAction.SWAP, media("small/b.jpg")),
    }
    [swapped] = selected((SURE, CHECK), NearSelection(verdicts=verdicts))
    assert keepers((swapped,)) == ["small/b.jpg"]
    assert [file.path.name for file in swapped.removable] == ["b.jpg", "b.jpg"]
    assert swapped.reason is NearReason.CHOSEN
    assert near_why(swapped, lambda _file: 1) == "Kept: your choice in 'review --near'."
    planned = {CHECK.keeper.path: NearVerdict(NearAction.PLANNED)}
    chosen = selected((CHECK,), NearSelection(verdicts=MappingProxyType(planned)))
    assert chosen == (CHECK,)


def test_a_group_kept_none_of_moves_every_version() -> None:
    """X: the copies first, then the version the audit kept."""
    verdicts = {CHECK.keeper.path: NearVerdict(NearAction.NONE)}
    [whole] = selected((CHECK,), NearSelection(verdicts=verdicts))
    assert whole.keeper == CHECK.keeper
    assert whole.removable == (*CHECK.removable, CHECK.keeper)


@pytest.mark.parametrize(
    "decision",
    [
        {"kept": "C:\\a.jpg", "copies": ["C:\\b.jpg"], "action": "swap"},
        {"kept": "C:\\a.jpg", "copies": ["C:\\b.jpg"], "action": "swap", "keep": "x"},
        {"kept": "C:\\a.jpg", "copies": [], "action": "leave", "keep": "C:\\b.jpg"},
    ],
)
def test_an_inconsistent_decision_is_refused(decision: dict[str, object]) -> None:
    """A swap keeps one of the copies; only a swap keeps one."""
    with pytest.raises(ValidationError):
        NearGroupDecision.model_validate(decision)


def test_a_group_decided_twice_refuses_the_file() -> None:
    """Which decision would win?"""
    group = {"kept": "C:\\a.jpg", "copies": ["C:\\b.jpg"], "action": "leave"}
    with pytest.raises(ValidationError, match="decided twice"):
        DecisionsFile.model_validate(
            {"version": 1, "roots": ["C:\\"], "near": [group, group]}
        )
