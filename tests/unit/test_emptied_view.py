"""What `clean` says of the folders it leaves empty, in English and French (0202)."""

from __future__ import annotations

from io import StringIO
from pathlib import Path

from rich.console import Console

from media_hygiene.actions.outcome import Outcome
from media_hygiene.actions.sort_folders import Fate, FolderReport, Verdict
from media_hygiene.console.emptied_view import show_clean_outcome, tell_emptied
from media_hygiene.console.output import Output
from media_hygiene.constants import Locale
from media_hygiene.i18n import using

_JUNK = Verdict(Path("/data/c/Photos/Trip"), Fate.HOLDS_JUNK)
_FILES = Verdict(Path("/data/c/Photos/Mixed"), Fate.HOLDS_FILES)


def _said(predicted: FolderReport, removed: int = 0) -> str:
    """Print the prediction, then the result, and return the text."""
    buffer = StringIO()
    output = Output(Console(file=buffer, width=200))
    tell_emptied(output, predicted)
    show_clean_outcome(
        output, Outcome(0, 0, 0, (), (), folders_removed=removed), "Clean"
    )
    return buffer.getvalue()


def test_the_counts_are_said_before_and_after() -> None:
    """Two folders to remove, one kept for its junk; two removed."""
    said = _said(FolderReport(2, (_JUNK, _FILES)), removed=2)
    assert "2 folders will be left empty and removed; 'undo' recreates them." in said
    assert "1 folder will hold only system files" in said
    assert "2 folders left empty were removed." in said


def test_nothing_is_said_without_a_folder() -> None:
    """No folder left empty: no line at all."""
    assert "folder" not in _said(FolderReport(0, (_FILES,)))


def test_the_counts_are_said_in_french() -> None:
    """The same lines, translated."""
    with using(Locale.FR):
        said = _said(FolderReport(1, (_JUNK,)), removed=1)
    assert "1 dossier sera laissé vide et supprimé ; 'undo' le recrée." in said
    assert "ne contiendra plus que des fichiers système" in said
    assert "1 dossier laissé vide a été supprimé." in said
