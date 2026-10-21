"""`mh backup` in the launchers (0264), checked as text: there is no PowerShell here.

The rendered `mh.ps1` is ASCII, never holds `/PURGE` nor `/MIR`, passes the excluded
folders to robocopy, refuses a target overlapping a photo or backup folder, keeps the
target read back from the disk, mounts the photos read-only; the bash `mh` refuses
`mh backup`, saying why and the command to type in Windows PowerShell.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import Locale
from media_hygiene.i18n import using
from media_hygiene.services.backup_lines import BACKUP_STEP, BackupStep, Order
from media_hygiene.services.launcher import (
    LauncherCommands,
    launcher_script,
    render_script,
)
from media_hygiene.services.launcher_backup import EXAMPLE, ROBOCOPY, TARGET_FILE
from tests.support.host_bash import bash_mh, run_bash
from tests.unit.test_launcher_ascii import accented_runtime, expanded

if TYPE_CHECKING:
    from pathlib import Path

_COMMANDS: Final = LauncherCommands(("audit", "menu"), (), (), ("menu",), 8088)
_FUNCTIONS: Final = (
    "backup",
    "backup_run",
    "backup_undo",
    "backup_move",
    "backup_mount",
    "backup_docker",
)


def _script(locale: Locale = Locale.EN) -> str:
    """The rendered `mh.ps1`, checked ASCII, as PowerShell evaluates its strings."""
    with using(locale):
        text = render_script(launcher_script(accented_runtime(), None, _COMMANDS))
    assert text.isascii()
    return expanded(text)


def _part(text: str) -> str:
    """The functions of `mh backup`, from the first to the end of the last."""
    start = text.index("function global:_mh_backup {")
    last = text.index("function global:_mh_backup_docker(")
    return text[start : text.index("\n}\n", last) + 3]


def _body(text: str, name: str) -> str:
    """One function of the script."""
    start = text.index(f"function global:_mh_{name}")
    return text[start : text.index("\n}\n", start) + 3]


def test_every_backup_function_is_in_the_script_once() -> None:
    """The dispatcher calls `_mh_backup`; its helpers are defined once each."""
    text = _script()
    assert "'backup' { _mh_backup @more; return }" in text
    for name in _FUNCTIONS:
        assert len(re.findall(rf"function global:_mh_{name}\b[ (]", text)) == 1, name


def test_robocopy_never_mirrors_nor_purges() -> None:
    """Nothing on the backup is deleted by robocopy: only new or changed files."""
    part = _part(_script())
    for word in ("/PURGE", "/MIR", "/MOV"):
        assert word not in part.upper(), word
    assert "& robocopy $origin $into @options" in part
    for option in ROBOCOPY:
        assert f"'{option}'" in part
    assert '"/MT:$threads"' in part


def test_the_excluded_folders_and_the_broken_files_are_passed() -> None:
    """`/XD` the folders the plan excludes, `/XF` the broken files of that folder."""
    run = _body(_script(), "backup_run")
    assert f"'{Order.EXCLUDE.value}' {{ $excluded += $fields[1] }}" in run
    assert "$options += '/XD'; $options += $excluded" in run
    assert "$options += '/XF'; $options += $mine" in run


def test_the_steps_run_in_order_and_ask_once() -> None:
    """Plan, a question, start (journaled first), renames, robocopy, prove."""
    run = _body(_script(), "backup_run")
    order = [
        run.index(f"@('{BackupStep.PLAN.value}')"),
        run.index("Read-Host"),
        run.index(f"@('{BackupStep.START.value}')"),
        run.index("_mh_backup_move $change[0]"),
        run.index("& robocopy"),
        run.index(f"@('{BackupStep.PROVE.value}'"),
    ]
    assert order == sorted(order)
    assert run.count("Read-Host") == 1
    assert "if ($stop) {" in run


def test_an_overlapping_target_is_refused() -> None:
    """A photo folder or a backup holding the target, or held by it: refused."""
    main = _body(_script(), "backup {")
    assert "foreach ($folder in @(@(_mh_photos) + @(_mh_backups)))" in main
    assert "$mine.StartsWith($theirs" in main
    assert "$theirs.StartsWith($mine" in main
    assert "overlaps ${folder}" in main


def test_the_target_is_kept_and_read_back() -> None:
    """Written next to the NAS passwords, then read back before it is said."""
    main = _body(_script(), "backup {")
    assert f"_mh_nas_file '{TARGET_FILE}'" in main
    written = main.index("Set-Content -LiteralPath $kept")
    read = main.index('$target = "$(Get-Content -LiteralPath $kept', written)
    assert read < main.index("Backup folder kept, read back", read)


def test_the_container_reads_everything_read_only() -> None:
    """Photos `:ro`, the target `:ro` (a NAS volume, or a drive's folder)."""
    text = _script()
    main = _body(text, "backup {")
    assert '"${folder}:$($folders[$folder]):ro"' in main
    mount = _body(text, "backup_mount")
    assert "/unc/$address/${share}:ro" in mount
    assert '"${to}:${point}:ro"' in mount
    docker = _body(text, "backup_docker")
    assert f"'{BACKUP_STEP}' @words --to $run.target" in docker


def test_a_rename_never_overwrites() -> None:
    """A rename only when the old file is there and the new name free."""
    move = _body(_script(), "backup_move")
    assert "(Test-Path -LiteralPath $to)) { return }" in move
    assert "Move-Item -LiteralPath $from -Destination $to -ErrorAction Stop" in move
    assert "-Force" not in move.split("Move-Item", 1)[1].split("\n", 1)[0]


def test_the_messages_are_french_in_french() -> None:
    """Translated, still ASCII in the file."""
    assert "L'appliquer" in _part(_script(Locale.FR))


def test_bash_refuses_backup_and_says_what_to_type(tmp_path: Path) -> None:
    """Why (Windows writes 7 times faster), the command to paste, status 2."""
    loaded = bash_mh(tmp_path, _COMMANDS, "")
    env = {"HOME": str(tmp_path), "PATH": "/usr/bin:/bin"}
    done = run_bash(f"{loaded}; mh backup --to x; echo status=$?", env)
    assert "mh backup is for Windows only" in done.stderr
    assert "7 times faster" in done.stderr
    assert "Windows PowerShell" in done.stderr
    assert done.stderr.endswith(f"    {EXAMPLE}\n")
    assert EXAMPLE == "mh backup --to \\\\<NAS>\\backup_photos"
    assert done.stdout == "status=2\n"
