"""A folder pair keeping both names (0213): the plan, the refusals, the wording."""

from __future__ import annotations

from pathlib import Path

from media_hygiene.actions.kinds import LINKS, ActionKind
from media_hygiene.actions.reversal import REVERSALS, Reversal
from media_hygiene.console.link_view import link_phrases
from media_hygiene.constants import KeepReason, MediaKind
from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.plan.keeper import KeepPolicy
from media_hygiene.plan.models import CleanPlan, KeepDecision
from media_hygiene.plan.pair_links import link_refusal, linked_count, linked_size
from media_hygiene.plan.pairs import folder_pairs
from media_hygiene.plan.review import (
    PairAction,
    PairChoice,
    ReviewChoices,
    apply_choices,
)
from media_hygiene.plan.similar_models import BurstChoice
from media_hygiene.scan.models import FileIdentity, MediaFile

DATA = Path("/data")
A, B, C = DATA / "c/A", DATA / "c/B", DATA / "c/C"
OTHER_DRIVE = DATA / "d/B"
MAPPER = HostPathMapper(DATA)
POLICY = KeepPolicy()


def at(folder: Path, name: str = "IMG.jpg", device: int = 1) -> MediaFile:
    """A 10-byte image in `folder`, on `device`."""
    identity = FileIdentity(device, hash((folder, name)) & 0xFFFF)
    return MediaFile(folder / name, 10, 0, MediaKind.IMAGE, identity=identity)


def group(keeper: MediaFile, *removable: MediaFile) -> CleanPlan:
    """A plan of one group."""
    return CleanPlan((KeepDecision("digest", 10, keeper, removable),), ())


def test_link_turns_the_copies_of_the_pair_into_links() -> None:
    """The pair's copy keeps its name; the other pair's copy still goes."""
    plan = group(at(A), at(B), at(C))
    choices = ReviewChoices((PairChoice(A, B, PairAction.LINK),))
    [decision] = apply_choices(plan, choices, POLICY).decisions
    assert decision.removable == (at(C),)
    assert decision.linked == (at(B),)
    assert not decision.spared


def test_a_group_left_with_links_only_stays_in_the_plan() -> None:
    """Nothing to delete, one copy to link: the plan is not empty, counted, sized."""
    plan = apply_choices(
        group(at(A), at(B)),
        ReviewChoices((PairChoice(A, B, PairAction.LINK),)),
        POLICY,
    )
    assert not plan.is_empty
    assert plan.removable_count == 0
    assert (linked_count(plan), linked_size(plan)) == (1, 10)
    assert plan.removed == frozenset()  # the name stays: no sidecar is orphaned
    assert "replace 1 duplicate copy by a link" in link_phrases(plan)[0]


def test_a_swap_in_the_group_spares_the_linked_copies() -> None:
    """A swap changes the keeper the link was decided for: the copy stays as it is."""
    choices = (PairChoice(A, B, PairAction.SWAP), PairChoice(A, C, PairAction.LINK))
    plan = group(at(A), at(B), at(C))
    [decision] = apply_choices(plan, ReviewChoices(choices), POLICY).decisions
    assert decision.keeper == at(B)
    assert decision.removable == (at(A),)
    assert decision.spared == (at(C),)
    assert not decision.linked


def test_a_linked_copy_is_not_moved_by_another_choice() -> None:
    """A burst shot or a file chosen that a link keeps under its name stays."""
    copy = at(B)
    choices = ReviewChoices(
        (PairChoice(A, B, PairAction.LINK),),
        bursts=(BurstChoice(kept=(at(C),), discarded=(copy,)),),
        chosen=(copy,),
    )
    plan = apply_choices(group(at(A), copy), choices, POLICY)
    assert not plan.bursts
    assert not plan.chosen


def test_link_is_refused_across_drives_disks_and_protected_folders() -> None:
    """Two drive letters, two devices, a protected kept folder: no link offered."""
    [same] = folder_pairs(group(at(A), at(B)).decisions)
    assert link_refusal(same, MAPPER) is None
    [drives] = folder_pairs(group(at(A), at(OTHER_DRIVE)).decisions)
    assert "two drives" in (link_refusal(drives, MAPPER) or "")
    [disks] = folder_pairs(group(at(A), at(B, device=2)).decisions)
    assert "two disks" in (link_refusal(disks, MAPPER) or "")
    assert "protected" in (link_refusal(same, MAPPER, (A,)) or "")
    protected = KeepDecision("digest", 10, at(A), (at(B),), reason=KeepReason.PROTECTED)
    [kept] = folder_pairs((protected,))
    assert "protected" in (link_refusal(kept, MAPPER) or "")


def test_link_without_a_known_identity_is_refused() -> None:
    """No device known (a listing without inode): no link is promised."""
    keeper = MediaFile(A / "IMG.jpg", 10, 0, MediaKind.IMAGE)
    [pair] = folder_pairs(group(keeper, at(B)).decisions)
    assert link_refusal(pair, MAPPER) is not None


def test_link_duplicate_has_a_reversal_and_counts_as_a_link() -> None:
    """`undo` knows how to make the name an independent file again."""
    assert REVERSALS[ActionKind.LINK_DUPLICATE] is Reversal.SEPARATE_LINK
    assert ActionKind.LINK_DUPLICATE in LINKS
    assert PairAction("link") is PairAction.LINK
