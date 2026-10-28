"""`mh import --phone`: copy only the new photos and videos of a phone over USB (0219).

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
    FAST_FOR_MILLISECONDS,
    FAST_POLL_MILLISECONDS,
    POLL_MILLISECONDS,
    STALL_SECONDS,
    WAKE_EVERY_SECONDS,
    WAKE_FOR_SECONDS,
    phone_command,
)
from media_hygiene.services.launcher_phone_free import (
    FREE_FLAG,
    GONE_SECONDS,
    MOVED_PREFIX,
    PHONE_MB_PER_SECOND,
)
from media_hygiene.services.launcher_phone_name import phone_naming
from media_hygiene.services.phone_free import PROVEN
from media_hygiene.services.phone_known import STAGING_PREFIX
from media_hygiene.services.phone_plan import (
    PHONE_DONE,
    PHONE_PLAN,
    PHONE_PROVE,
    PHONE_REVIEW,
    PhoneCase,
)
from tests.support.host_bash import run_bash
from tests.support.runtime import make_locations, make_runtime
from tests.unit.test_launcher_ascii import accented_runtime, expanded

if TYPE_CHECKING:
    from pathlib import Path

_COMMANDS: Final = LauncherCommands(("audit", "menu"), (), (), ("menu",), 8088)
_FUNCTIONS: Final = (
    "phone",
    "phone_audit",
    "phone_said",
    "phone_pick",
    "phone_there",
    "phone_dcim",
    "phone_files",
    "phone_name",
    "phone_size",
    "phone_date",
    "phone_docker",
    "phone_copy",
    "phone_wait",
    "phone_free",
    "phone_clear",
    "phone_page",
    "phone_stage",
    "phone_move",
    "phone_gone",
)


def _script(locale: Locale = Locale.EN) -> str:
    """The rendered `mh.ps1`, ASCII, as PowerShell evaluates its strings."""
    with using(locale):
        text = render_script(launcher_script(accented_runtime(), None, _COMMANDS))
    assert text.isascii()
    return expanded(text)


def _phone_part(text: str) -> str:
    """The functions of `mh import --phone`, first to end of the last."""
    start = text.index("function global:_mh_phone {")
    last = text.index("function global:_mh_phone_free(")
    return text[start : text.index("\n}\n", last) + 3]


def _body(text: str, name: str) -> str:
    """One function of the script."""
    start = text.index(f"function global:_mh_{name}")
    return text[start : text.index("\n}\n", start) + 3]


def test_every_phone_function_is_in_the_script() -> None:
    """`mh import --phone` calls `_mh_phone`; its helpers are defined once each."""
    text = _script()
    assert "if ($rest[0] -eq 'import' -and $more -contains '--phone') {" in text
    assert "_mh_phone @words" in text
    assert "'phone' {" not in text  # `mh phone` is gone, no alias (0379)
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
    assert "$item.ExtendedProperty('System.FileName')" in _body(text, "phone_name")
    files = _body(text, "phone_files")
    assert "$name = _mh_phone_name $entry" in files
    assert "$below + $entry.Name + '/'" in files
    assert "Folder = $folder" in files  # listed again after a move (0248)


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


def test_the_wait_looks_before_its_first_pause_then_polls_fast_for_a_second() -> None:
    """A photo copied in 50 ms is seen at once, not after 200 ms then 200 ms (0251)."""
    wait = _body(_script(), "phone_wait")
    looked = wait.index("$copy = Get-Item -LiteralPath $path")
    paused = wait.index("Start-Sleep")
    assert looked < paused
    assert (
        f"if ($since.ElapsedMilliseconds -lt {FAST_FOR_MILLISECONDS}) "
        f"{{ Start-Sleep -Milliseconds {FAST_POLL_MILLISECONDS} }} "
        f"else {{ Start-Sleep -Milliseconds {POLL_MILLISECONDS} }}"
    ) in wait
    assert FAST_POLL_MILLISECONDS < POLL_MILLISECONDS
    # The proof is unchanged: the phone's size, or no growth when it is unknown.
    assert (
        "if (($size -gt 0 -and $length -eq $size) -or ($size -le 0 -and -not $grew))"
        in wait
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
    text = _script()
    plan = _body(text, "phone_docker")
    assert "$out = @($lines | docker run --rm -i @page `" in plan
    assert "-it" not in plan
    assert '-v "C:\\Photos\\Vidéos:/data/c/Photos/Vidéos:ro" `' in plan
    assert '-v "${destination}:${point}:ro" `' in plan
    assert '-v "media-hygiene-cache:/cache" `' in plan
    assert '/journal" `' in plan
    assert "media-hygiene @words)" in plan
    assert (
        f"_mh_phone_docker $lines $destination @() @('{PHONE_PLAN}', '--destination', "
        "$destination)"
    ) in _body(text, "phone {")
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
    assert there < main.index("_mh_phone_docker $lines $destination")
    assert "Type mh import --phone again: what is already copied is skipped." in main


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
        "if ($copies -gt 0) { _mh_phone_audit }"
    )


def test_the_files_copied_are_audited_by_the_open_home_page_else_here() -> None:
    """0451: the home page asked first, as its own button does; else `mh audit`."""
    audit = _body(_script(), "phone_audit")
    assert (
        "Invoke-WebRequest -Uri 'http://127.0.0.1:8088/api/audit' -Method Post "
        "-ContentType 'application/json' -Body '{\"action\": \"start\"}'"
    ) in audit
    asked = audit.index("Invoke-WebRequest")
    assert audit.index("The home page audits the new files now") > asked
    assert audit.index("return") < audit.index("    mh audit\n")
    assert audit.rstrip().splitlines()[-2].strip() == "mh audit"


def test_the_skipped_set_aside_are_said_to_be_on_the_phone() -> None:
    """The count is of the phone's files, never of the files copied."""
    main = _body(_script(), "phone {")
    assert "Also on the phone, skipped: ${count} you set aside earlier" in main


def test_the_french_script_says_it_in_french() -> None:
    """Translated, the accents rebuilt by PowerShell."""
    part = _phone_part(_script(Locale.FR))
    assert "Le téléphone est seulement lu" in part
    assert "Aucun téléphone" in part


def test_phone_texts_are_safe_inside_double_quotes() -> None:
    """No quote, dollar sign or backtick of a translation can break the script."""
    with using(Locale.FR):
        command = phone_command()
    for texts in (command.texts, command.free.texts):
        for field in fields(texts):
            _safe(getattr(texts, field.name))


def _safe(value: str) -> None:
    """A message stays inside its double quotes; only its own fields expand."""
    assert '"' not in value
    assert "`" not in value
    assert not re.search(
        r"\$(?!\{(count|size|speed|destination|name|final|to|minutes|path"
        r"|reason|folder)\})",
        value,
    )


def _free_part(text: str) -> str:
    """The functions of `import --phone --free`, first to end of the last."""
    start = text.index("function global:_mh_phone_clear(")
    last = text.index("function global:_mh_phone_gone(")
    return text[start : text.index("\n}\n", last) + 3]


def test_only_one_folder_of_dcim_is_copied_and_offered() -> None:
    """`--only Camera`: the other files are neither copied nor offered (0248)."""
    main = _body(_script(), "phone {")
    assert (
        "elseif ($word -eq '--only' -and $i + 1 -lt $words.Count) { $i++; $only = "
        "(\"$($words[$i])\" -replace '\\\\', '/').Trim('/') }"
    ) in main
    skipped = main.index(
        "if ($only -and -not $entry.Path.StartsWith($only + '/', "
        "[StringComparison]::OrdinalIgnoreCase)) { continue }"
    )
    assert skipped < main.index("$lines.Add(")
    assert 'else { Write-Host "mh import --phone copies only' in main


def test_free_is_asked_for_and_said_before_anything() -> None:
    """`--free` only: without it the phone is only read, as before (0219)."""
    main = _body(_script(), "phone {")
    assert f"if ($word -eq '{FREE_FLAG}') {{ $free = $true }}" in main
    assert (
        'if ($free) { Write-Host "🔒 Nothing leaves the phone before you tick it on a '
        "page and press Delete; each file is first proven on the PC by its content."
        '" } else { Write-Host "🔒 The phone is only read'
    ) in main
    cleared = main.index("if ($free) { _mh_phone_clear $shell $name $items $plan")
    assert main.index("$copies = _mh_phone_said") < cleared


def test_a_file_leaves_the_phone_only_after_the_page_and_its_proof() -> None:
    """Page, staged copy, proof (pending), then the move, then done: in that order."""
    clear = _body(_script(), "phone_clear")
    page = clear.index("$ticked = _mh_phone_page $offered $destination $name")
    staged = clear.index("_mh_phone_stage $shell $one.File $staging")
    proven = clear.index(f"$words = @('{PHONE_PROVE}', '--phone', $name")
    kept = clear.index(f"if ($fields[0] -ne '{PROVEN}' -or $fields.Count -lt 5) {{")
    moved = clear.index("switch (_mh_phone_move $shell $name $file $moved $fields[4])")
    done = clear.index(f"@('{PHONE_DONE}', '--run', $run)")
    assert page < staged < proven < kept < moved < done
    # A file not proven goes on to the next one before any move.
    assert "continue" in clear[kept:moved]
    # A copy that stalled: nothing of its batch is proven nor moved.
    assert "if ($stopped -or $staged.Count -eq 0) { break }" in clear[staged:proven]


def test_movehere_is_the_only_way_off_the_phone_never_a_delete_verb() -> None:
    """MoveHere into a PC folder (no dialog, measured), in one function only."""
    text = _script()
    free = _free_part(text)
    assert free.count(".MoveHere(") == 1
    assert "$shell.Namespace($folder).MoveHere($file.Item, 1044)" in _body(
        text, "phone_move"
    )
    for verb in ("InvokeVerb", ".Delete(", "Add-Type", "-ExecutionPolicy"):
        assert verb not in free, verb
        assert verb not in _phone_part(text), verb


def test_the_moved_copy_is_dropped_only_once_gone_and_equal() -> None:
    """Listed again, the phone no longer holds it; its SHA-256 the proven one."""
    move = _body(_script(), "phone_move")
    moved = move.index("MoveHere")
    listed = move.index("$phone = _mh_phone_gone $shell $name $file")
    hashed = move.index("(Get-FileHash -Algorithm SHA256 -LiteralPath $landed).Hash")
    differs = move.index("if ($hash -ne $digest) { return 'differs' }")
    dropped = move.rindex("Remove-Item -LiteralPath $landed")
    assert moved < listed < hashed < differs < dropped
    # Still on the phone: the PC copy goes, the phone holds the file.
    there = move.index("if ($phone -eq 'there') {")
    assert move.index("Remove-Item -LiteralPath $landed", there) < move.index(
        "return 'still'", there
    )
    # Never over a name already there.
    assert move.index("if (Test-Path -LiteralPath $landed) { return 'still' }") < moved
    gone = _body(_script(), "phone_gone")
    assert "foreach ($entry in $file.Folder.Items())" in gone
    assert "if (-not (_mh_phone_there $shell $name)) { return 'unknown' }" in gone
    assert f"-ge {GONE_SECONDS}) {{ return 'there' }}" in gone


def test_the_moved_folder_goes_only_when_empty() -> None:
    """A copy left there may be the only one: the folder stays then."""
    clear = _body(_script(), "phone_clear")
    assert f"$moved = Join-Path $destination ('{MOVED_PREFIX}' + $stamp)" in clear
    assert (
        "if ((Test-Path -LiteralPath $moved) -and -not (Get-ChildItem -LiteralPath "
        "$moved -Recurse -File -Force -ErrorAction SilentlyContinue)) { Remove-Item "
        "-LiteralPath $moved"
    ) in clear
    removals = [line for line in clear.splitlines() if "Remove-Item" in line]
    assert all("$staging" in line or "$moved" in line for line in removals)


def test_the_page_is_served_on_the_loopback_after_the_port_check() -> None:
    """Like every page: the port freed first, published on 127.0.0.1 only."""
    page = _body(_script(), "phone_page")
    assert page.index("if (-not (_mh_page_free)) { return $null }") < page.index(
        "-p', '127.0.0.1:8088:8088'"
    )
    assert (
        f"@('{PHONE_REVIEW}', '--phone', $name, '--destination', $destination" in page
    )
    assert "return ,$out" in page


def test_the_estimate_counts_two_reads_from_the_phone() -> None:
    """Said before starting, at the speed measured."""
    clear = _body(_script(), "phone_clear")
    assert f"[Math]::Ceiling(2 * $bytes / 1MB / {PHONE_MB_PER_SECOND} / 60)" in clear
    assert clear.index('Write-Host "Checking then deleting') < clear.index(
        "_mh_phone_stage"
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
    done = run_bash(f"source {path}; mh import --phone; echo status=$?", env)
    assert done.stderr == "mh import --phone is for Windows only.\n"
    assert done.stdout == "status=2\n"


def test_from_home_the_page_offers_its_way_back_in_the_home_tab() -> None:
    """0332: the relay from the home loop; no second tab, the home one follows."""
    page = _body(_script(), "phone_page")
    assert (
        "if ($global:MediaHygieneRelay) "
        "{ $page += '-e', 'MEDIA_HYGIENE_LAUNCHER_STEPS=1' }"
    ) in page
    assert "if (-not $global:MediaHygieneTab) { $browser = Start-Job" in page
    assert "if ($browser) { Remove-Job -Job $browser -Force }" in page


def test_from_home_a_closed_tab_deletes_nothing_and_ends_the_loop() -> None:
    """0332: the page's exit code kept for the loop of `mh`, nothing deleted said."""
    clear = _body(_script(), "phone_clear")
    closed = clear.index(
        "if ($null -eq $ticked -and $LASTEXITCODE -eq 3) "
        '{ Write-Host "Nothing was deleted from the phone."; return }'
    )
    assert closed < clear.index('if ($null -eq $ticked) { Write-Host "The check')


def test_a_phone_with_no_storage_is_waited_for_not_said_without_dcim() -> None:
    """0336: asleep or locked, the phone shows nothing: unlock it, a bounded wait."""
    script = _script()
    awake = _body(script, "phone_awake(")
    texts = phone_command().texts
    assert "@($phone.GetFolder.Items()).Count -eq 0" in awake
    assert f"-ge {WAKE_FOR_SECONDS})" in awake
    assert f"Start-Sleep -Seconds {WAKE_EVERY_SECONDS}" in awake
    assert texts.asleep in awake
    assert texts.none in awake
    assert texts.no_dcim not in awake
    assert "unlock it" in texts.asleep
    main = _body(script, "phone {")
    assert main.index("_mh_phone_awake $phone") < main.index(texts.no_dcim)


def test_a_phone_asleep_during_a_copy_is_said() -> None:
    """0336: keep it unlocked, said up front and when it stops answering."""
    texts = phone_command().texts
    assert "keep the phone unlocked" in texts.copying
    assert "asleep" in texts.unplugged
    assert "asleep" in phone_command().free.texts.stopped


def test_a_factory_name_is_told_how_to_rename_the_phone() -> None:
    """A brand or model word first: one tip, before the listing; an own name: none."""
    naming = phone_naming()
    main = _body(_script(), "phone {")
    tip = main.index(f"if ($name -match '{naming.pattern}')")
    assert main.index("$destination = Join-Path $to $own") < tip
    assert tip < main.index('Write-Host "Listing')
    assert "looks like the phone's factory name" in main
    factory = re.compile(naming.pattern, re.IGNORECASE)
    for name in ("Galaxy A71", "Pixel 8", "iPhone de Manon", "redmi note 12"):
        assert factory.search(name), name
    for name in ("Christophe A71", "Manon S23", "Mike's phone"):
        assert not factory.search(name), name
    _safe(naming.tip)
