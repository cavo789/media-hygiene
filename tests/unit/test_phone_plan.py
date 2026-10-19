"""`phone-plan`: which files of a phone `mh phone` copies, why not the others (0219).

A listing on stdin against an index, journals and a destination: each reason to skip,
names compared without case, ties broken by path, the output format.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Final

import pytest
from typer.testing import CliRunner

from media_hygiene.actions.journal import journal_file
from media_hygiene.actions.kinds import ActionKind, Phase
from media_hygiene.cli.app import build_app
from media_hygiene.index.repository import FactsRepository
from media_hygiene.services.phone_known import STAGING_PREFIX
from media_hygiene.services.phone_plan import (
    PHONE_PLAN,
    AsideState,
    Known,
    PhoneCase,
    PhoneFile,
    SetAside,
    Verdict,
    decide,
    read_listing,
)
from tests.support.cli import point_mounts
from tests.support.journaled import done_line

if TYPE_CHECKING:
    from pathlib import Path

    from typer.testing import Result

    from media_hygiene.actions.journal import JournalEntry
    from media_hygiene.paths.locations import Locations

_DATE: Final = "2025-05-12T17:53:43Z"
_START: Final = datetime(2026, 1, 1, tzinfo=UTC)
_RUN: Final = "20260101-120000"
_LATER: Final = "20260301-120000"


@pytest.fixture
def runner(locations: Locations, monkeypatch: pytest.MonkeyPatch) -> CliRunner:
    """A runner whose mount points are the test's folders, the data folder empty."""
    point_mounts(locations, monkeypatch)
    locations.data_dir.mkdir(parents=True, exist_ok=True)
    return CliRunner()


def _plan(runner: CliRunner, listing: str, *options: str) -> Result:
    """Run `phone-plan` with the listing on stdin."""
    return runner.invoke(
        build_app(), [PHONE_PLAN, *options], input=listing, catch_exceptions=False
    )


def _line(path: str, size: int) -> str:
    """One line of the listing `mh` pipes in."""
    return f"{path}\t{size}\t{_DATE}\n"


def _index(locations: Locations, *rows: tuple[str, int]) -> None:
    """Put files into the index file, as an audit would: `c/Photos/a.jpg`, its size."""
    locations.cache_dir.mkdir(parents=True, exist_ok=True)
    data = locations.data_dir.as_posix()
    with FactsRepository.open(locations.index_file) as repository:
        repository.connection.executemany(
            "INSERT INTO files (path, size, mtime_ns) VALUES (?, ?, 1)",
            [(f"{data}/{path}", size) for path, size in rows],
        )


def _aside(locations: Locations, run_id: str, entry: JournalEntry) -> None:
    """Write a run's journal holding one set-aside."""
    locations.journal_dir.mkdir(parents=True, exist_ok=True)
    path = journal_file(locations.journal_dir, run_id)
    with path.open("a", encoding="utf-8") as lines:
        lines.write(entry.model_dump_json() + "\n")


def _burst(name: str, size: int, minutes: int = 0) -> JournalEntry:
    """A burst shot set aside, by its host path."""
    return done_line(
        ActionKind.QUARANTINE_BURST,
        f"/data/c/Photos/{name}",
        host_path=f"C:\\Photos\\{name}",
        size=size,
        sha256="ab" * 32,
        at=_START + timedelta(minutes=minutes),
    )


def _cases(result: Result) -> dict[str, list[str]]:
    """The plan printed on stdout, by path: the case then the reason."""
    assert result.exit_code == 0, result.output
    plan: dict[str, list[str]] = {}
    for line in result.stdout.splitlines():
        case, path, _size, _date, *reason = line.split("\t")
        plan[path] = [case, *reason]
    return plan


def test_a_file_the_library_holds_by_name_and_size_is_not_copied(
    runner: CliRunner, locations: Locations
) -> None:
    """Same name, case ignored, same size: in the library, its host path said."""
    _index(
        locations,
        ("c/Photos/2025/img_0001.JPG", 1000),
        ("c/Photos/2025/IMG_0002.jpg", 999),  # same name, another size
    )
    listing = _line("Camera/IMG_0001.jpg", 1000) + _line("Camera/IMG_0002.jpg", 1000)
    plan = _cases(_plan(runner, listing))
    assert plan["Camera/IMG_0001.jpg"] == [
        PhoneCase.LIBRARY.value,
        "C:\\Photos\\2025\\img_0001.JPG",
    ]
    assert plan["Camera/IMG_0002.jpg"] == [PhoneCase.NEW.value]


def test_identical_copies_in_the_library_name_the_first_path(
    runner: CliRunner, locations: Locations
) -> None:
    """Ties between copies of one name and size: the first path, on every run."""
    _index(
        locations,
        ("e/Backup/IMG_1.jpg", 10),
        ("c/Photos/IMG_1.jpg", 10),
        ("d/Old/IMG_1.jpg", 10),
    )
    plan = _cases(_plan(runner, _line("IMG_1.jpg", 10)))
    assert plan["IMG_1.jpg"] == [PhoneCase.LIBRARY.value, "C:\\Photos\\IMG_1.jpg"]


def test_a_file_set_aside_on_purpose_says_its_run_and_quarantine_state(
    runner: CliRunner, locations: Locations
) -> None:
    """In the quarantine still, or purged: the run, the date, the kind."""
    _aside(locations, _RUN, _burst("burst_01.jpg", 500))
    _aside(locations, _LATER, _burst("BURST_02.JPG", 600, minutes=5))
    (locations.quarantine_dir / _LATER).mkdir(parents=True)  # the other run purged
    listing = _line("Camera/burst_01.jpg", 500) + _line("Camera/burst_02.jpg", 600)
    plan = _cases(_plan(runner, listing))
    first = plan["Camera/burst_01.jpg"]
    assert first[:3] == [PhoneCase.SET_ASIDE.value, _RUN, AsideState.PURGED.value]
    assert datetime.fromisoformat(first[3]) == _START
    assert first[4] == ActionKind.QUARANTINE_BURST.value
    second = plan["Camera/burst_02.jpg"]
    assert second[:3] == [PhoneCase.SET_ASIDE.value, _LATER, "quarantine"]


def test_a_file_restored_by_undo_is_no_longer_set_aside(
    runner: CliRunner, locations: Locations
) -> None:
    """The last word wins: the user wanted it back, the phone's copy is new."""
    done = _burst("burst_01.jpg", 500)
    _aside(locations, _RUN, done)
    undo = done.model_copy(
        update={"phase": Phase.UNDO, "at": _START + timedelta(minutes=9)}
    )
    _aside(locations, _RUN, undo)
    plan = _cases(_plan(runner, _line("burst_01.jpg", 500)))
    assert plan["burst_01.jpg"] == [PhoneCase.NEW.value]


def test_the_latest_set_aside_of_a_name_and_size_is_said(
    runner: CliRunner, locations: Locations
) -> None:
    """Two contents set aside under one name and size: the latest one."""
    _aside(locations, _RUN, _burst("x.jpg", 7))
    other = _burst("x.jpg", 7, minutes=60).model_copy(update={"sha256": "cd" * 32})
    _aside(locations, _LATER, other)
    plan = _cases(_plan(runner, _line("x.jpg", 7)))
    assert plan["x.jpg"][1] == _LATER


def test_a_file_already_at_the_destination_is_not_copied_again(
    runner: CliRunner, locations: Locations
) -> None:
    """A second `mh phone`: the destination holds it; staging never counts."""
    destination = locations.data_dir / "c" / "Photos" / "Phone" / "A72"
    (destination / "Camera").mkdir(parents=True)
    (destination / "Camera" / "IMG_9.jpg").write_bytes(b"x" * 30)
    staging = destination / f"{STAGING_PREFIX}20260101-120000"
    staging.mkdir()
    (staging / "IMG_8.jpg").write_bytes(b"x" * 20)  # a stopped run's partial copy
    listing = _line("Camera/img_9.JPG", 30) + _line("Camera/IMG_8.jpg", 20)
    plan = _cases(_plan(runner, listing, "--destination", "C:\\Photos\\Phone\\A72"))
    assert plan["Camera/img_9.JPG"] == [
        PhoneCase.DESTINATION.value,
        "Camera/IMG_9.jpg",
    ]
    assert plan["Camera/IMG_8.jpg"] == [PhoneCase.NEW.value]


def test_the_library_comes_before_the_journals_and_the_destination(
    runner: CliRunner, locations: Locations
) -> None:
    """A file in every place: the library is its reason (0248 frees it first)."""
    _index(locations, ("c/Photos/a.jpg", 5))
    _aside(locations, _RUN, _burst("a.jpg", 5))
    plan = _cases(_plan(runner, _line("a.jpg", 5)))
    assert plan["a.jpg"][0] == PhoneCase.LIBRARY.value


def test_an_empty_cache_says_to_audit_first(runner: CliRunner) -> None:
    """Without any audit, every photo is new: said on stderr, never on stdout."""
    result = _plan(runner, _line("a.jpg", 5))
    assert result.stdout == f"new\ta.jpg\t5\t{_DATE}\n"
    assert "mh audit" in result.stderr


def test_unreadable_lines_are_skipped_and_counted(runner: CliRunner) -> None:
    """Not three fields, a size that is no number, a path leaving DCIM: said once."""
    listing = (
        "\ufeff"
        + _line("ok.jpg", 1)
        + "only\ttwo\n"
        + _line("big.jpg", 1).replace("\t1\t", "\tlots\t")
        + _line("../up.jpg", 1)
        + _line("/root.jpg", 1)
        + "\n"
    )
    result = _plan(runner, listing)
    assert [line.split("\t")[1] for line in result.stdout.splitlines()] == ["ok.jpg"]
    assert "4 lines of the phone's listing could not be read" in result.stderr


def test_accented_names_cross_stdin_and_stdout_in_utf8(runner: CliRunner) -> None:
    """A name with accents comes back as it went, in UTF-8."""
    result = _plan(runner, _line("Été/Noël.jpg", 3))
    assert result.stdout_bytes.decode("utf-8").split("\t")[1] == "Été/Noël.jpg"


def test_read_listing_keeps_each_path_once_and_windows_separators() -> None:
    r"""A path listed twice counts once; `\` becomes `/`."""
    files, skipped = read_listing(
        [_line("Camera\\a.jpg", 1), _line("Camera/a.jpg", 1), _line("b.jpg", 2)]
    )
    assert [file.path.as_posix() for file in files] == ["Camera/a.jpg", "b.jpg"]
    assert skipped == 0


def test_the_line_replaces_tabs_inside_a_reason() -> None:
    """A tab in a host path would start a field: written as a space."""
    file = PhoneFile(PurePosixPath("a.jpg"), 1, _DATE)
    verdict = Verdict(file, PhoneCase.LIBRARY, ("C:\\odd\tname.jpg",))
    assert verdict.line() == f"library\ta.jpg\t1\t{_DATE}\tC:\\odd name.jpg"


def test_decide_without_anything_known_copies_everything() -> None:
    """Nothing known: every file is new, in the order given."""
    files = (
        PhoneFile(PurePosixPath("b.jpg"), 1, _DATE),
        PhoneFile(PurePosixPath("a.jpg"), 1, _DATE),
    )
    verdicts = decide(files, Known())
    assert [verdict.case for verdict in verdicts] == [PhoneCase.NEW, PhoneCase.NEW]
    assert [verdict.file for verdict in verdicts] == list(files)


def test_set_aside_reason_holds_run_state_date_and_kind() -> None:
    """The fields 0248 reads to warn before freeing the phone."""
    file = PhoneFile(PurePosixPath("a.jpg"), 1, _DATE)
    aside = SetAside(_RUN, _START, "quarantine-near", AsideState.QUARANTINE)
    (verdict,) = decide((file,), Known(set_aside={file.key: aside}))
    assert verdict.reason == (_RUN, "quarantine", _START.isoformat(), "quarantine-near")


def test_phone_plan_is_hidden_from_the_help(runner: CliRunner) -> None:
    """Plumbing for `mh` only: not in `--help`, its own help still there."""
    app = build_app()
    assert PHONE_PLAN not in runner.invoke(app, ["--help"]).output
    assert "--destination" in runner.invoke(app, [PHONE_PLAN, "--help"]).output


def test_a_missing_destination_holds_nothing(runner: CliRunner, tmp_path: Path) -> None:
    """The first import: the folder is not there yet, every file new."""
    result = _plan(runner, _line("a.jpg", 1), "--destination", str(tmp_path / "none"))
    assert _cases(result)["a.jpg"] == [PhoneCase.NEW.value]
