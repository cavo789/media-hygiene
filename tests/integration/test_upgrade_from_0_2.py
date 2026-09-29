"""After the rename to media-hygiene, what media-dedup 0.2.0 left behind still works.

`tests/fixtures/0.2.0/` holds files written by the real 0.2.0: an audit and a clean of
two identical photos, then its own models for the decisions and a cross-checked summary.
Their paths were made neutral.
"""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from media_hygiene.__main__ import main
from media_hygiene.actions.journal import read_journal
from media_hygiene.constants import ActionKind, MediaKind, Status
from media_hygiene.index.repository import FactsRepository
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.plan.review import PairAction
from media_hygiene.report.decisions import read_decisions
from media_hygiene.report.index_page import load_summaries
from media_hygiene.scan.file_check import Need, need_of
from media_hygiene.scan.models import MediaFile

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "0.2.0"
DIGEST = "5948b2640eb33f26077d63b7bea077b2172b789d629f7f8298f2cd66244a99db"


def test_a_journal_of_0_2_0_is_read() -> None:
    """Its write-ahead entries load: a duplicate deleted, pending then done."""
    entries = read_journal(FIXTURES / "journal.jsonl")
    assert [entry.status for entry in entries] == [Status.PENDING, Status.DONE]
    assert {entry.action for entry in entries} == {ActionKind.DELETE_DUPLICATE}
    assert entries[0].keeper == "/data/c/Photos/2019/Plage.jpg"


def test_a_decisions_file_of_0_2_0_is_read() -> None:
    """Its pair and burst decisions load."""
    decisions = read_decisions(FIXTURES / "decisions.json")
    assert decisions.pairs[0].action is PairAction.SWAP
    assert decisions.bursts[0].discarded == ("C:\\Photos\\2019\\Plage (2).jpg",)


def test_a_report_of_0_2_0_stays_in_the_catalogue(tmp_path: Path) -> None:
    """Its summary, cross-check included (`only_media_dedup`), is still listed."""
    report = tmp_path / "20260929-192140-audit"
    report.mkdir()
    shutil.copy(FIXTURES / "summary.json", report / "summary.json")
    (summary,) = load_summaries(tmp_path)
    assert summary.crosscheck is not None
    assert summary.crosscheck.only_ours == 1


def test_an_index_of_0_2_0_is_used(tmp_path: Path) -> None:
    """Its facts are reused: nothing hashed again, images only get their header read."""
    index = tmp_path / "index.sqlite"
    with sqlite3.connect(index) as connection:
        connection.executescript((FIXTURES / "index.sql").read_text("utf-8"))
    connection.close()
    photo = MediaFile(
        Path("/data/c/Photos/2019/Plage.jpg"), 677, 1790709700326787004, MediaKind.IMAGE
    )
    with FactsRepository.open(index) as repository:
        facts = repository.get(photo)
    assert facts.full_digest == DIGEST
    assert facts.visual is not None
    assert need_of(photo, facts) is Need.METADATA  # its header only, once


def _unset_after_test(monkeypatch: pytest.MonkeyPatch, name: str) -> None:
    """Make pytest remove `name` at the end, even when the code under test sets it."""
    monkeypatch.setenv(name, "")
    monkeypatch.delenv(name)


def test_the_variables_of_0_2_0_still_apply(
    locations: Locations,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`MEDIA_DEDUP_*` set the mounts and the language, and one warning names them."""
    old = {"MEDIA_DEDUP_GENERAL__LOCALE": "fr"}
    old |= {
        f"MEDIA_DEDUP_{kind.value.upper()}_DIR": str(locations.path_of(kind))
        for kind in MountKind
    }
    for name, value in old.items():
        monkeypatch.setenv(name, value)
        _unset_after_test(monkeypatch, name.replace("MEDIA_DEDUP_", "MEDIA_HYGIENE_"))
    monkeypatch.setattr("sys.argv", ["media-hygiene", "history"])
    with pytest.raises(SystemExit) as caught:
        main()
    assert caught.value.code == 0
    output = " ".join(capsys.readouterr().out.split())
    assert "MEDIA_DEDUP_GENERAL__LOCALE" in output
    assert "MEDIA_HYGIENE_" in output
    assert "Aucun nettoyage" in output
