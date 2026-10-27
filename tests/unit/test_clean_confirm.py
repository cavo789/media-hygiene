"""The confirmation of `clean` says plainly whether anything is erased."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.cli.clean_confirm import confirm_clean
from media_hygiene.constants import MediaKind
from media_hygiene.plan.models import CleanPlan, KeepDecision
from media_hygiene.plan.similar_models import NearDecision
from media_hygiene.scan.models import MediaFile
from tests.support.runtime import make_locations, make_runtime, output_of

if TYPE_CHECKING:
    import pytest


def copies(kind: MediaKind, name: str) -> KeepDecision:
    """A kept file and its copy, in two folders."""
    kept = MediaFile(Path(f"/data/c/A/{name}"), 1, 0, kind)
    return KeepDecision(
        "d", 1, kept, (MediaFile(Path(f"/data/c/B/{name}"), 1, 0, kind),)
    )


def said(tmp_path: Path, plan: CleanPlan) -> str:
    """What `clean --yes` prints before acting."""
    runtime = make_runtime(make_locations(tmp_path))
    assert confirm_clean(runtime, plan, yes=True)
    return " ".join(output_of(runtime).split())


def test_by_default_nothing_is_erased(tmp_path: Path) -> None:
    """Every copy goes to the quarantine, and the line says so."""
    plan = CleanPlan((copies(MediaKind.IMAGE, "a.jpg"),), ())
    assert plan.moved_copies == 1
    assert "🛟 Nothing will be erased: each copy is first compared" in said(
        tmp_path, plan
    )


def test_delete_says_it_erases_and_what_still_moves(tmp_path: Path) -> None:
    """`--delete`: the warning; no copy is said moved."""
    decisions = (copies(MediaKind.IMAGE, "a.jpg"), copies(MediaKind.IMAGE, "b.jpg"))
    text = said(tmp_path, CleanPlan(decisions, (), delete_copies=True))
    assert "--delete: the copies are deleted for good" in text
    assert "will be moved" not in text


def test_the_question_names_where_the_copies_go(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Asked in a terminal: "Move … to the quarantine", or "Delete …" with --delete."""
    asked: list[str] = []
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)

    def refuse(_output: object, question: str) -> bool:
        asked.append(question)
        return False

    monkeypatch.setattr("media_hygiene.console.output.Output.confirm", refuse)
    pair = copies(MediaKind.IMAGE, "n.jpg")
    near = NearDecision(pair.keeper, pair.removable)
    runtime = make_runtime(make_locations(tmp_path))
    for delete in (False, True):
        for extra in ((), (near,)):
            decisions = (copies(MediaKind.IMAGE, "a.jpg"),)
            plan = CleanPlan(decisions, (), near=extra, delete_copies=delete)
            assert not confirm_clean(runtime, plan, yes=False)
    assert [question.split()[0] for question in asked] == [
        "Move",
        "Move",
        "Delete",
        "Delete",
    ]
    assert asked[0] == "Move 1 duplicate copy (1 B) to the quarantine?"
    assert "and 1 near duplicates to the quarantine" in asked[1]
    assert (
        asked[3]
        == "Delete 1 duplicate copy (1 B) and move 1 near duplicate to the quarantine?"
    )


def test_near_duplicates_alone_ask_only_about_them(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No zero counts in the question, no byte comparison promised for look-alikes."""
    asked: list[str] = []
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)

    def refuse(_output: object, question: str) -> bool:
        asked.append(question)
        return False

    monkeypatch.setattr("media_hygiene.console.output.Output.confirm", refuse)
    pair = copies(MediaKind.IMAGE, "n.jpg")
    plan = CleanPlan((), (), near=(NearDecision(pair.keeper, pair.removable),))
    runtime = make_runtime(make_locations(tmp_path))
    assert not confirm_clean(runtime, plan, yes=False)
    assert asked == ["Move 1 near duplicate to the quarantine?"]
    assert "the files are moved to the quarantine" in " ".join(
        output_of(runtime).split()
    )


def test_files_set_aside_in_search_are_asked_apart_with_their_size(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Their count and size, after the duplicates."""
    asked: list[str] = []
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)

    def refuse(_output: object, question: str) -> bool:
        asked.append(question)
        return False

    monkeypatch.setattr("media_hygiene.console.output.Output.confirm", refuse)
    chosen = tuple(
        MediaFile(Path(f"/data/c/E/{n}.jpg"), 1024, 0, MediaKind.IMAGE) for n in "ab"
    )
    plan = CleanPlan((copies(MediaKind.IMAGE, "a.jpg"),), (), chosen=chosen)
    assert not plan.is_empty
    runtime = make_runtime(make_locations(tmp_path))
    assert not confirm_clean(runtime, plan, yes=False)
    assert asked == [
        (
            "Move 1 duplicate copy (1 B) to the quarantine and move 2 files you set "
            "aside (2.0 KB) to the quarantine?"
        )
    ]
