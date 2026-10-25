"""`decisions.json` follows the moves of a run, path by path (0382)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.report.chosen_decisions import ChosenFile
from media_hygiene.report.decisions import (
    DecisionsFile,
    read_decisions,
    write_decisions,
)
from media_hygiene.report.decisions_moves import DecisionMoves, follow_decisions

if TYPE_CHECKING:
    from pathlib import Path

_A, _B = r"C:\Photos\x\IMG_1.jpg", r"C:\Photos\y\IMG_1.jpg"  # two identical copies


def _moves(moves: dict[str, str]) -> DecisionMoves:
    r"""Moves inside `C:\Photos`, every folder present.

    Args:
        moves: New host path by old one.

    Returns:
        The moves.
    """
    return DecisionMoves(
        moves, dict.fromkeys(moves.values(), r"C:\Photos"), lambda _f: True
    )


def test_two_identical_copies_each_follow_their_own_file(tmp_path: Path) -> None:
    """Same size and date: each entry is renamed by its own path, never merged."""
    path = tmp_path / "decisions.json"
    chosen = tuple(ChosenFile(path=p, size=10, mtime_ns=1) for p in (_A, _B))
    write_decisions(
        path, DecisionsFile(version=1, roots=(r"C:\Photos",), chosen=chosen)
    )
    moves = {
        _A: r"C:\Photos\2009\2009-11\T\IMG_1.jpg",
        _B: r"C:\Photos\2009\2009-11\T\IMG_1 (1).jpg",
    }
    followed = follow_decisions(path, _moves(moves))
    assert followed.paths == 2
    back = read_decisions(path)
    assert [entry.path for entry in back.chosen] == [moves[_A], moves[_B]]
    assert back.roots == (r"C:\Photos",)  # already holds the destinations


def test_a_destination_outside_the_roots_joins_them(tmp_path: Path) -> None:
    """`clean --decisions` still accepts the file after a sort into another root."""
    path = tmp_path / "decisions.json"
    chosen = (ChosenFile(path=_A, size=10, mtime_ns=1),)
    write_decisions(
        path, DecisionsFile(version=1, roots=(r"C:\Photos\x",), chosen=chosen)
    )
    new = r"D:\Sorted\2009\2009-11\IMG_1.jpg"
    follow_decisions(
        path, DecisionMoves({_A: new}, {new: "D:\\Sorted"}, lambda _f: True)
    )
    assert read_decisions(path).roots == (r"C:\Photos\x", "D:\\Sorted")


def test_no_file_or_nothing_moved_writes_nothing(tmp_path: Path) -> None:
    """A missing file stays missing; an unchanged one is not written again."""
    path = tmp_path / "decisions.json"
    assert follow_decisions(path, _moves({_A: _B})).paths == 0
    assert not path.exists()
    write_decisions(path, DecisionsFile(version=1, roots=(r"C:\Photos",)))
    stamp = path.stat().st_mtime_ns
    follow_decisions(path, _moves({_A: _B}))
    assert path.stat().st_mtime_ns == stamp
