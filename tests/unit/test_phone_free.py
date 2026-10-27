"""Freeing a phone (0248): each file ticked proven by its content, then journaled.

`phone-prove` against a real index, journals, quarantines and staged copies: the
three cases, what is kept on the phone and why, the two warnings of a set-aside;
`phone-done` and the journal of kind `phone`, `history`, and `undo` refusing it.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Final

import pytest
from typer.testing import CliRunner

from media_hygiene.actions.journal import journal_file, read_journal
from media_hygiene.actions.kinds import ActionKind, Phase, Status
from media_hygiene.actions.runs import summarize
from media_hygiene.cli.app import build_app
from media_hygiene.index.repository import FactsRepository
from media_hygiene.scan.hashing import partial_digest
from media_hygiene.services.phone_free import read_ticked
from media_hygiene.services.phone_holdings import LibraryRow, in_library
from media_hygiene.services.phone_journal import PhoneRun, phone_run, record_done
from media_hygiene.services.phone_plan import (
    PHONE_DONE,
    PHONE_PROVE,
    PhoneCase,
    PhoneFile,
)
from media_hygiene.services.phone_proof import Proof, Proven
from tests.support.cli import point_mounts
from tests.support.journaled import done_line

if TYPE_CHECKING:
    from pathlib import Path

    from typer.testing import Result

    from media_hygiene.paths.locations import Locations

_DATE: Final = "2025-05-12T17:53:43Z"
_RUN: Final = "20260101-120000"
_PHONE: Final = "Galaxy A72"
_STAGING: Final = "C:\\Photos\\Phone\\A72\\.mh-phone-20261019-120000"
_DESTINATION: Final = "C:\\Photos\\Phone\\A72"
_PHOTO: Final = b"\xff\xd8 a photo of the beach \xff\xd9"
_RECOVERABLE: Final = (
    f"Set aside on 2026-03-01, still recoverable with mh undo {_RUN} until mh purge."
)
_OTHER: Final = b"\xff\xd8 a photo of the hills \xff\xd9"  # same size, other content


@pytest.fixture
def runner(locations: Locations, monkeypatch: pytest.MonkeyPatch) -> CliRunner:
    """A runner whose mount points are the test's folders, the data folder empty."""
    point_mounts(locations, monkeypatch)
    locations.data_dir.mkdir(parents=True, exist_ok=True)
    return CliRunner()


def _sha(data: bytes) -> str:
    """The SHA-256 of some bytes."""
    return hashlib.sha256(data).hexdigest()


def _put(locations: Locations, relative: str, data: bytes) -> Path:
    r"""Write a file below the data folder: `c/Photos/a.jpg` is `C:\Photos\a.jpg`."""
    path = locations.data_dir / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _stage(locations: Locations, phone_path: str, data: bytes) -> None:
    """Copy a phone file into the staging folder, as `mh` does before the proof."""
    _put(locations, f"c/Photos/Phone/A72/.mh-phone-20261019-120000/{phone_path}", data)


def _index(locations: Locations, path: Path, digest: str | None) -> None:
    """Put a file of the data folder into the index, as an audit would."""
    locations.cache_dir.mkdir(parents=True, exist_ok=True)
    stat = path.stat()
    with FactsRepository.open(locations.index_file) as repository:
        repository.connection.execute(
            "INSERT INTO files (path, size, mtime_ns, full_digest) VALUES (?, ?, ?, ?)",
            (str(path), stat.st_size, stat.st_mtime_ns, digest),
        )


def _aside(locations: Locations, data: bytes, *, partial: bool = False) -> None:
    """A burst shot of that content set aside by run `_RUN`."""
    locations.journal_dir.mkdir(parents=True, exist_ok=True)
    digests: dict[str, object] = {"sha256": _sha(data)}
    if partial:  # a gone file (0224): only its partial digest kept
        staged = _put(locations, "tmp/partial.bin", data)
        digests = {"partial": partial_digest(staged), "sha256": None}
        staged.unlink()
    entry = done_line(
        ActionKind.QUARANTINE_BURST,
        "/data/c/Photos/burst.jpg",
        host_path="C:\\Photos\\burst.jpg",
        size=len(data),
        at=datetime(2026, 3, 1, 12, tzinfo=UTC),
        **digests,
    )
    with journal_file(locations.journal_dir, _RUN).open("a", encoding="utf-8") as out:
        out.write(entry.model_dump_json() + "\n")


def _line(case: PhoneCase, path: str, size: int, *reason: str) -> str:
    """A plan line of a file ticked in the page."""
    return "\t".join((case.value, path, str(size), _DATE, *reason)) + "\n"


def _prove(runner: CliRunner, ticked: str, *options: str) -> Result:
    """Run `phone-prove` with the files ticked on stdin."""
    args = [PHONE_PROVE, "--phone", _PHONE, "--staging", _STAGING, *options]
    return runner.invoke(build_app(), args, input=ticked, catch_exceptions=False)


def _proofs(result: Result) -> tuple[str, dict[str, list[str]]]:
    """The run, and each file's line by its path: its verdict, then the rest."""
    assert result.exit_code == 0, result.output
    run, *lines = result.stdout.splitlines()
    kind, run_id = run.split("\t")
    assert kind == "run"
    proofs: dict[str, list[str]] = {}
    for line in lines:
        verdict, path, _size, *rest = line.split("\t")
        proofs[path] = [verdict, *rest]
    return run_id, proofs


def _entries(locations: Locations, run_id: str) -> list[ActionKind]:
    """The actions of a run's journal, in write order."""
    return [e.action for e in read_journal(journal_file(locations.journal_dir, run_id))]


def test_a_file_the_library_holds_by_content_is_proven_and_journaled_pending(
    runner: CliRunner, locations: Locations
) -> None:
    """Case 1: the index's digest, the file still there; `pending` before the phone."""
    kept = _put(locations, "c/Photos/2025/IMG_1.jpg", _PHOTO)
    _index(locations, kept, _sha(_PHOTO))
    _stage(locations, "Camera/IMG_1.jpg", _PHOTO)
    ticked = _line(PhoneCase.LIBRARY, "Camera/IMG_1.jpg", len(_PHOTO), "C:\\x")
    run_id, proofs = _proofs(_prove(runner, ticked))
    assert proofs["Camera/IMG_1.jpg"] == [
        "proven",
        Proven.LIBRARY.value,
        _sha(_PHOTO),
        "C:\\Photos\\2025\\IMG_1.jpg",
        "",
    ]
    entries = read_journal(journal_file(locations.journal_dir, run_id))
    assert len(entries) == 1
    entry = entries[0]
    assert entry.phase is Phase.PHONE
    assert entry.status is Status.PENDING
    assert entry.action is ActionKind.PHONE_LIBRARY
    assert entry.path == "Camera/IMG_1.jpg"
    assert entry.host_path == "Galaxy A72\\DCIM\\Camera\\IMG_1.jpg"
    assert entry.size == len(_PHOTO)
    assert entry.sha256 == _sha(_PHOTO)
    assert entry.keeper == "C:\\Photos\\2025\\IMG_1.jpg"
    taken = datetime(2025, 5, 12, 17, 53, 43, tzinfo=UTC)
    assert entry.mtime_ns == int(taken.timestamp()) * 10**9


def test_the_same_name_and_size_with_another_content_stays_on_the_phone(
    runner: CliRunner, locations: Locations
) -> None:
    """Name and size only propose: another content is kept, with its reason."""
    kept = _put(locations, "c/Photos/IMG_1.jpg", _OTHER)
    _index(locations, kept, _sha(_OTHER))
    _stage(locations, "Camera/IMG_1.jpg", _PHOTO)
    ticked = _line(
        PhoneCase.LIBRARY, "Camera/IMG_1.jpg", len(_PHOTO), "C:\\Photos\\IMG_1.jpg"
    )
    run_id, proofs = _proofs(_prove(runner, ticked))
    assert proofs["Camera/IMG_1.jpg"] == [
        "kept",
        "Not the same content as C:\\Photos\\IMG_1.jpg: kept on the phone.",
    ]
    assert not journal_file(locations.journal_dir, run_id).exists()


def test_a_library_file_gone_since_the_audit_proves_nothing(
    runner: CliRunner, locations: Locations
) -> None:
    """The index still names it, the disk no longer holds it: kept on the phone."""
    kept = _put(locations, "c/Photos/IMG_1.jpg", _PHOTO)
    _index(locations, kept, _sha(_PHOTO))
    kept.unlink()
    _stage(locations, "IMG_1.jpg", _PHOTO)
    _run, proofs = _proofs(
        _prove(runner, _line(PhoneCase.LIBRARY, "IMG_1.jpg", len(_PHOTO)))
    )
    assert proofs["IMG_1.jpg"] == [
        "kept",
        "Its content is nowhere on the PC: kept on the phone.",
    ]


def test_a_candidate_without_a_digest_or_changed_since_is_hashed_now(
    tmp_path: Path,
) -> None:
    """No full digest in the index, or a date changed: the content is read now."""
    plain = tmp_path / "plain.jpg"
    plain.write_bytes(_PHOTO)
    changed = tmp_path / "changed.jpg"
    changed.write_bytes(_PHOTO)
    stat = changed.stat()
    rows = (LibraryRow(plain, plain.stat().st_mtime_ns, None),)
    assert in_library(rows, len(_PHOTO), _sha(_PHOTO)) == plain
    # The index's digest said another content, but the file changed since: read now.
    stale = (LibraryRow(changed, stat.st_mtime_ns - 1, _sha(_OTHER)),)
    assert in_library(stale, len(_PHOTO), _sha(_PHOTO)) == changed
    # Unchanged since the audit: its digest is trusted, never read again.
    trusted = (LibraryRow(changed, stat.st_mtime_ns, _sha(_OTHER)),)
    assert in_library(trusted, len(_PHOTO), _sha(_PHOTO)) is None


def test_the_imports_own_copy_proves_case_2_only_when_whole_and_equal(
    runner: CliRunner, locations: Locations
) -> None:
    """Case 2: the copy `import --phone` made, the phone's size and the same SHA-256."""
    _put(locations, "c/Photos/Phone/A72/Camera/IMG_2.jpg", _PHOTO)
    _put(locations, "c/Photos/Phone/A72/Camera/IMG_3.jpg", _PHOTO[:-3])  # truncated
    _stage(locations, "Camera/IMG_2.jpg", _PHOTO)
    _stage(locations, "Camera/IMG_3.jpg", _PHOTO)
    size = len(_PHOTO)
    ticked = _line(PhoneCase.DESTINATION, "Camera/IMG_2.jpg", size, "Camera/IMG_2.jpg")
    ticked += _line(PhoneCase.DESTINATION, "Camera/IMG_3.jpg", size, "Camera/IMG_3.jpg")
    run_id, proofs = _proofs(_prove(runner, ticked, "--destination", _DESTINATION))
    assert proofs["Camera/IMG_2.jpg"][:4] == [
        "proven",
        Proven.IMPORTED.value,
        _sha(_PHOTO),
        "C:\\Photos\\Phone\\A72\\Camera\\IMG_2.jpg",
    ]
    assert proofs["Camera/IMG_3.jpg"] == [
        "kept",
        "Not the same content as Camera/IMG_3.jpg: kept on the phone.",
    ]
    assert _entries(locations, run_id) == [ActionKind.PHONE_IMPORTED]


def test_a_copy_path_leaving_the_destination_proves_nothing(
    runner: CliRunner, locations: Locations
) -> None:
    """`../` in the copy's path: never followed out of the import's folder."""
    _put(locations, "c/Photos/Phone/IMG_2.jpg", _PHOTO)
    _stage(locations, "IMG_2.jpg", _PHOTO)
    ticked = _line(PhoneCase.DESTINATION, "IMG_2.jpg", len(_PHOTO), "../IMG_2.jpg")
    _run, proofs = _proofs(_prove(runner, ticked, "--destination", _DESTINATION))
    assert proofs["IMG_2.jpg"][0] == "kept"


def test_a_set_aside_in_its_quarantine_is_proven_with_its_undo(
    runner: CliRunner, locations: Locations
) -> None:
    """Case 3, still in the quarantine: recoverable with `mh undo <run>`."""
    _aside(locations, _PHOTO)
    (locations.quarantine_dir / _RUN).mkdir(parents=True)
    _stage(locations, "burst.jpg", _PHOTO)
    ticked = _line(PhoneCase.SET_ASIDE, "burst.jpg", len(_PHOTO), _RUN, "quarantine")
    run_id, proofs = _proofs(_prove(runner, ticked))
    assert proofs["burst.jpg"] == [
        "proven",
        Proven.SET_ASIDE.value,
        _sha(_PHOTO),
        _RUN,
        _RECOVERABLE,
    ]
    entries = read_journal(journal_file(locations.journal_dir, run_id))
    assert len(entries) == 1
    entry = entries[0]
    assert entry.action is ActionKind.PHONE_SET_ASIDE
    assert entry.keeper is None


def test_a_purged_set_aside_known_by_its_partial_digest_warns_lost_for_good(
    runner: CliRunner, locations: Locations
) -> None:
    """Case 3, purged, only the partial digest kept: proven, lost for good."""
    _aside(locations, _PHOTO, partial=True)
    _stage(locations, "burst.jpg", _PHOTO)
    ticked = _line(PhoneCase.SET_ASIDE, "burst.jpg", len(_PHOTO), _RUN, "purged")
    _run, proofs = _proofs(_prove(runner, ticked))
    assert proofs["burst.jpg"][:2] == ["proven", Proven.SET_ASIDE.value]
    assert proofs["burst.jpg"][4] == (
        "Set aside on 2026-03-01 and purged since: it is nowhere else. Deleted from "
        "the phone, it is lost for good."
    )


def test_a_missing_or_incomplete_staged_copy_stays_on_the_phone(
    runner: CliRunner, locations: Locations
) -> None:
    """The copy from the phone stopped (cable pulled): nothing is proven on it."""
    kept = _put(locations, "c/Photos/IMG_1.jpg", _PHOTO)
    _index(locations, kept, _sha(_PHOTO))
    _stage(locations, "IMG_1.jpg", _PHOTO[:5])
    size = len(_PHOTO)
    ticked = _line(PhoneCase.LIBRARY, "IMG_1.jpg", size)
    ticked += _line(PhoneCase.LIBRARY, "IMG_9.jpg", size)  # never staged
    _run, proofs = _proofs(_prove(runner, ticked))
    reason = "The copy from the phone is missing or incomplete: kept on the phone."
    assert proofs["IMG_1.jpg"] == ["kept", reason]
    assert proofs["IMG_9.jpg"] == ["kept", reason]


def test_done_follows_pending_and_the_run_goes_on_for_the_next_files(
    runner: CliRunner, locations: Locations
) -> None:
    """`phone-done`: only the files proven before; a second batch, the same run."""
    for name in ("a.jpg", "b.jpg"):
        kept = _put(locations, f"c/Photos/{name}", name.encode() + _PHOTO)
        _index(locations, kept, _sha(name.encode() + _PHOTO))
        _stage(locations, name, name.encode() + _PHOTO)
    size = len(_PHOTO) + 5
    run_id, _proofs_a = _proofs(_prove(runner, _line(PhoneCase.LIBRARY, "a.jpg", size)))
    again = _prove(runner, _line(PhoneCase.LIBRARY, "b.jpg", size), "--run", run_id)
    assert _proofs(again)[0] == run_id
    done = runner.invoke(
        build_app(),
        [PHONE_DONE, "--run", run_id],
        input="a.jpg\nnever.jpg\nb.jpg\na.jpg\n",
        catch_exceptions=False,
    )
    assert done.exit_code == 0, done.output
    assert done.stdout == "done\ta.jpg\ndone\tb.jpg\n"
    entries = read_journal(journal_file(locations.journal_dir, run_id))
    assert [(e.seq, e.status) for e in entries] == [
        (1, Status.PENDING),
        (2, Status.PENDING),
        (1, Status.DONE),
        (2, Status.DONE),
    ]
    summary = summarize(locations.journal_dir, run_id)
    assert summary.kind is Phase.PHONE
    assert (summary.deleted, summary.freed, summary.restored) == (2, 2 * size, 0)


def test_history_says_a_phone_run_and_undo_refuses_it(
    runner: CliRunner, locations: Locations
) -> None:
    """`undo` cannot put a file back on a phone: refused, nothing changed."""
    kept = _put(locations, "c/Photos/a.jpg", _PHOTO)
    _index(locations, kept, _sha(_PHOTO))
    _stage(locations, "a.jpg", _PHOTO)
    run_id, _proofs_a = _proofs(
        _prove(runner, _line(PhoneCase.LIBRARY, "a.jpg", len(_PHOTO)))
    )
    runner.invoke(build_app(), [PHONE_DONE, "--run", run_id], input="a.jpg\n")
    history = runner.invoke(build_app(), ["history"])
    assert "phone" in history.output
    assert "undo cannot put them back" in " ".join(history.output.split())
    undo = runner.invoke(build_app(), ["undo", run_id, "--yes"])
    assert undo.exit_code != 0
    assert "undo cannot put them back on it" in " ".join(undo.output.split())
    assert kept.read_bytes() == _PHOTO
    assert len(read_journal(journal_file(locations.journal_dir, run_id))) == 2


def test_without_a_journal_nothing_is_proven(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No persistent journal: refused, no line `mh` could act on."""
    monkeypatch.delenv("MEDIA_HYGIENE_JOURNAL_DIR")
    result = _prove(runner, _line(PhoneCase.LIBRARY, "a.jpg", 1))
    assert result.exit_code != 0
    assert "No journal mount" in result.output
    assert "proven" not in result.stdout


def test_an_unknown_run_is_refused(runner: CliRunner, locations: Locations) -> None:
    """`--run` names a phone run of this journal, or nothing is written."""
    locations.journal_dir.mkdir(parents=True, exist_ok=True)
    result = runner.invoke(build_app(), [PHONE_DONE, "--run", "../x"], input="a\n")
    assert result.exit_code != 0
    assert "Unknown run ../x." in result.output
    with pytest.raises(Exception, match="Unknown run"):
        phone_run(locations.journal_dir, _RUN, _PHONE)


def test_read_ticked_skips_new_files_and_unreadable_lines() -> None:
    """A new file was not imported: it never leaves the phone; bad lines counted."""
    lines = [
        "\ufeff" + _line(PhoneCase.LIBRARY, "a.jpg", 1, "C:\\a.jpg"),
        _line(PhoneCase.NEW, "b.jpg", 1),
        "library\tc.jpg\tbig\t" + _DATE,
        "library\td.jpg",
        _line(PhoneCase.LIBRARY, "a.jpg", 1),  # the same path once
        "",
    ]
    ticked, skipped = read_ticked(lines)
    assert [(t.case, t.file.path.as_posix(), t.reason) for t in ticked] == [
        (PhoneCase.LIBRARY, "a.jpg", ("C:\\a.jpg",))
    ]
    assert skipped == 3


def test_done_writes_nothing_for_a_path_never_pending(locations: Locations) -> None:
    """A path `mh` names that was never proven: no `done` without its `pending`."""
    locations.journal_dir.mkdir(parents=True, exist_ok=True)
    journal = journal_file(locations.journal_dir, _RUN)
    journal.write_text("", encoding="utf-8")
    assert not record_done(PhoneRun(journal, _PHONE), ["a.jpg"])
    assert _entries(locations, _RUN) == []


def test_the_plumbing_is_hidden_from_the_help(runner: CliRunner) -> None:
    """For `mh` only: not in `--help`."""
    shown = runner.invoke(build_app(), ["--help"]).output
    assert PHONE_PROVE not in shown
    assert PHONE_DONE not in shown


def test_a_proof_kept_on_the_phone_has_no_case() -> None:
    """The default proof keeps the file: nothing leaves the phone by default."""
    proof = Proof(PhoneFile(PurePosixPath("a.jpg"), 1, _DATE))
    assert proof.proven is None
