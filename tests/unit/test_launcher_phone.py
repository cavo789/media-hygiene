"""`mh phone`: copy only the new photos and videos of a phone over USB (0219).

There is no PowerShell here: the rendered `mh.ps1` is checked as text — the phone read
through Shell.Application only (no Add-Type), `CopyHere` only (never `MoveHere`), the
extended properties measured by step 19 of `mh-measure.ps1`, an empty staging folder,
the wait per file, never an overwrite, ASCII only; the bash `mh` says Windows only.
"""

from __future__ import annotations

import re
from dataclasses import fields, replace
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import Locale
from media_hygiene.i18n import using
from media_hygiene.paths.docker_run import Shell
from media_hygiene.paths.mounts import MountTable
from media_hygiene.services.launcher import (
    LauncherCommands,
    launcher_script,
    render_script,
)
from media_hygiene.services.launcher_phone import (
    COPY_FLAGS,
    STALL_SECONDS,
    phone_command,
)
from media_hygiene.services.phone_known import STAGING_PREFIX
from media_hygiene.services.phone_plan import PHONE_PLAN, PhoneCase
from tests.support.host_bash import run_bash
from tests.support.runtime import make_locations, make_runtime
from tests.unit.test_launcher_ascii import accented_runtime, expanded

if TYPE_CHECKING:
    from pathlib import Path

_COMMANDS: Final = LauncherCommands(("audit", "menu"), (), (), ("menu",), 8088)
_FUNCTIONS: Final = (
    "phone",
    "phone_said",
    "phone_pick",
    "phone_there",
    "phone_dcim",
    "phone_files",
    "phone_size",
    "phone_date",
    "phone_plan",
    "phone_copy",
    "phone_wait",
    "phone_free",
)


def _script(locale: Locale = Locale.EN) -> str:
    """The rendered `mh.ps1`, ASCII, as PowerShell evaluates its strings."""
    with using(locale):
        text = render_script(launcher_script(accented_runtime(), None, _COMMANDS))
    assert text.isascii()
    return expanded(text)


def _phone_part(text: str) -> str:
    """The functions of `mh phone`, from the first to the end of the last."""
    start = text.index("function global:_mh_phone {")
    last = text.index("function global:_mh_phone_free(")
    return text[start : text.index("\n}\n", last) + 3]


def _body(text: str, name: str) -> str:
    """One function of the script."""
    start = text.index(f"function global:_mh_{name}")
    return text[start : text.index("\n}\n", start) + 3]


def test_every_phone_function_is_in_the_script() -> None:
    """The dispatcher calls `_mh_phone`; its helpers are defined once each."""
    text = _script()
    assert "'phone' { _mh_phone @more; return }" in text
    for name in _FUNCTIONS:
        assert len(re.findall(rf"function global:_mh_{name}\b[ (]", text)) == 1, name


def test_the_phone_is_only_read_never_moved_nor_deleted() -> None:
    """CopyHere only, with no window and yes to all; never MoveHere, never a delete."""
    part = _phone_part(_script())
    assert f"$target.CopyHere($file.Item, {COPY_FLAGS})" in part
    assert COPY_FLAGS == 4 + 16 + 1024
    for verb in ("MoveHere", "InvokeVerb", ".Delete(", "Add-Type"):
        assert verb not in part, verb
    assert "New-Object -ComObject Shell.Application" in part
    # Every Remove-Item works on the staging folder or a staged copy only.
    removals = [line for line in part.splitlines() if "Remove-Item" in line]
    assert len(removals) == 3
    assert all(
        "$staging" in line or "$staged" in line or "Filter" in line for line in removals
    )


def test_the_listing_reads_the_extended_properties_measured() -> None:
    """Over MTP .Size is 0, .ModifyDate empty: System.Size, System.DateModified."""
    text = _script()
    assert "$item.ExtendedProperty('System.Size')" in _body(text, "phone_size")
    date = _body(text, "phone_date")
    assert "$item.ExtendedProperty('System.DateModified')" in date
    assert (
        "\"yyyy-MM-dd'T'HH:mm:ss'Z'\", [Globalization.CultureInfo]::InvariantCulture"
        in date
    )
    files = _body(text, "phone_files")
    assert "$entry.ExtendedProperty('System.FileName')" in files
    assert "$below + $entry.Name + '/'" in files


def test_dcim_is_found_by_walking_never_by_a_fixed_path() -> None:
    """The top folder is localised ("Stockage interne"): DCIM found by walking."""
    dcim = _body(_script(), "phone_dcim")
    assert "$entry.Name -ieq 'DCIM'" in dcim
    assert "if ($depth -lt 3)" in dcim


def test_each_file_goes_through_an_empty_staging_folder_then_moves_in_place() -> None:
    """No name is ever already there for CopyHere: no hidden replace dialog."""
    copy = _body(_script(), "phone_copy")
    staging = copy.index(f"$staging = Join-Path $destination ('{STAGING_PREFIX}'")
    copied = copy.index("$target = $shell.Namespace($staging)")
    waited = copy.index("_mh_phone_wait $staged $file.Size")
    moved = copy.index(
        "Move-Item -LiteralPath $staged -Destination $final -ErrorAction Stop"
    )
    assert staging < copied < waited < moved
    assert "Move-Item" in copy
    assert "-Force" not in copy[moved : copy.index("\n", moved)]
    # The staging folder goes at the end, Ctrl+C or a cable pulled included.
    assert copy.index("} finally {") < copy.index(
        "Remove-Item -LiteralPath $staging -Recurse"
    )


def test_each_copy_is_waited_for_until_whole_and_released() -> None:
    """The phone's size reached, the copy engine gone; 60 s without growth: stopped."""
    wait = _body(_script(), "phone_wait")
    assert f"while ($watch.Elapsed.TotalSeconds -lt {STALL_SECONDS})" in wait
    assert "$watch.Restart()" in wait
    assert "[IO.File]::Open($path, 'Open', 'Read', 'None')" in wait
    assert STALL_SECONDS == 60
    copy = _body(_script(), "phone_copy")
    stopped = copy.index("if (-not (_mh_phone_wait $staged $file.Size)) {")
    assert copy.index("Remove-Item -LiteralPath $staged", stopped) < copy.index(
        "break", stopped
    )


def test_a_name_already_there_is_never_overwritten() -> None:
    """name_1.ext, name_2.ext...: the free name, said."""
    free = _body(_script(), "phone_free")
    assert "while (Test-Path -LiteralPath $path)" in free
    assert "('{0}_{1}{2}' -f $stem, $n, $extension)" in free
    assert "${name} was already there: copied as ${final}." in _body(
        _script(), "phone_copy"
    )


def test_the_container_decides_with_the_listing_on_its_stdin() -> None:
    """phone-plan: -i, no -t, photos and destination read-only, UTF-8 both ways."""
    plan = _body(_script(), "phone_plan")
    assert "$plan = @($lines | docker run --rm -i `" in plan
    assert "-it" not in plan
    assert '-v "C:\\Photos\\Vidéos:/data/c/Photos/Vidéos:ro" `' in plan
    assert '-v "${destination}:${point}:ro" `' in plan
    assert '-v "media-hygiene-cache:/cache" `' in plan
    assert '/journal" `' in plan
    assert f"{PHONE_PLAN} --destination $destination)" in plan
    assert "$OutputEncoding = [Text.UTF8Encoding]::new($false)" in plan
    assert "[Console]::OutputEncoding = $console" in plan


def test_the_plan_cases_are_the_containers() -> None:
    """The four first words of phone-plan's lines, as the script reads them."""
    main = _body(_script(), "phone {")
    for case in PhoneCase:
        assert f"'{case.value}' {{" in main


def test_an_unplugged_phone_after_listing_stops_before_anything() -> None:
    """A short listing is never decided on: the phone looked for again first."""
    main = _body(_script(), "phone {")
    there = main.index("if (-not (_mh_phone_there $shell $name))")
    assert there < main.index("_mh_phone_plan $lines $destination")
    assert "Type mh phone again: what is already copied is skipped." in main


def test_the_destination_defaults_to_phone_under_the_first_photo_folder() -> None:
    r"""--to, else <first photo folder>\Phone, then a folder per phone name."""
    main = _body(_script(), "phone {")
    assert "$first = @(_mh_photos) | Select-Object -First 1" in main
    assert "$to = Join-Path $first 'Phone'" in main
    assert "$destination = Join-Path $to $own" in main


def test_the_summary_is_read_back_and_ends_on_the_next_step() -> None:
    """Each copy found again with the phone's size; then one 👉 line, last."""
    text = _script()
    said = _body(text, "phone_said")
    assert "Get-Item -LiteralPath $copy.Path" in said
    assert "$back.Length -eq $copy.Size" in said
    main = _body(text, "phone {")
    assert main.rstrip().splitlines()[-2].strip() == (
        'if ($copies -gt 0) { Write-Host "👉 What next: mh audit (the new files join '
        'your library)." }'
    )


def test_the_french_script_says_it_in_french() -> None:
    """Translated, the accents rebuilt by PowerShell."""
    part = _phone_part(_script(Locale.FR))
    assert "Le téléphone est seulement lu" in part
    assert "Aucun téléphone" in part


def test_phone_texts_are_safe_inside_double_quotes() -> None:
    """No quote, dollar sign or backtick of a translation can break the script."""
    with using(Locale.FR):
        texts = phone_command().texts
    for field in fields(texts):
        value: str = getattr(texts, field.name)
        assert '"' not in value
        assert "`" not in value
        assert not re.search(
            r"\$(?!\{(count|size|speed|destination|name|final|to)\})", value
        )


def test_bash_says_phone_is_for_windows_only(tmp_path: Path) -> None:
    """No phone access from WSL or Linux: one line, status 2, no docker."""
    runtime = replace(
        make_runtime(make_locations(tmp_path)), mounts=MountTable(frozenset())
    )
    path = tmp_path / "mh.sh"
    path.write_text(
        render_script(launcher_script(runtime, Shell.BASH, _COMMANDS)), encoding="utf-8"
    )
    env = {"HOME": str(tmp_path), "PATH": "/usr/bin:/bin"}
    done = run_bash(f"source {path}; mh phone; echo status=$?", env)
    assert done.stderr == "mh phone is for Windows only.\n"
    assert done.stdout == "status=2\n"
