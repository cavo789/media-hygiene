"""What `mh` runs on the host itself, without the container: open, shortcut, explorer.

TODOs 0175 (`mh open`: the reports in the browser), 0180 (`mh shortcut`: an icon
opening the menu) and 0181 (`mh explorer`: the right-click entry of a folder, and
`mh --photos X` alone: the menu on that folder).
"""

from __future__ import annotations

import os
from dataclasses import replace
from pathlib import Path, PureWindowsPath
from typing import TYPE_CHECKING, Final

import pytest
from PIL import Image
from typer.testing import CliRunner

from media_hygiene.cli.app import build_app
from media_hygiene.cli.menu_steps import Section, build_menu
from media_hygiene.cli.report_where import announce_report
from media_hygiene.constants import Locale
from media_hygiene.i18n import using
from media_hygiene.paths.docker_run import Shell, Volume
from media_hygiene.paths.mounts import MountTable
from media_hygiene.services.launcher import (
    LauncherCommands,
    LauncherScript,
    launcher_script,
    render_script,
)
from media_hygiene.services.launcher_host import (
    BACKGROUND_KEY,
    EXPLORER_KEY,
    FROM_EXPLORER,
    HOST_COMMANDS,
    ICON,
    ICON_NAME,
)
from media_hygiene.services.next_command import LAUNCHER_VARIABLE
from media_hygiene.services.status import read_status
from tests.support.host_bash import fake_program, run_bash
from tests.support.runtime import make_locations, make_runtime, output_of
from tests.unit.test_launcher_ascii import accented_runtime, expanded

if TYPE_CHECKING:
    import subprocess

    from media_hygiene.services.runtime import Runtime

_COMMANDS: Final = LauncherCommands(("audit", "menu"), (), (), ("menu",), 8088)
# The image's stand-in: the menu has one step, audit; the rest is echoed word by word.
_FAKE_DOCKER: Final = r"""
docker() {
    case " $* " in
        *" menu "*) printf '1\taudit\n' ;;
        *) printf 'ran:%s\n' "$@" ;;
    esac
}
"""
_HINT: Final = 30


def _runtime(tmp_path: Path) -> Runtime:
    """A run without any mount: the tool folders default to the home."""
    return replace(
        make_runtime(make_locations(tmp_path)), mounts=MountTable(frozenset())
    )


def _bash_script(tmp_path: Path, script: LauncherScript | None = None) -> Path:
    """Write the bash `mh` into the test's folder."""
    path = tmp_path / "mh.sh"
    built = script or launcher_script(_runtime(tmp_path), Shell.BASH, _COMMANDS)
    path.write_text(render_script(built), encoding="utf-8")
    return path


def _bash(
    tmp_path: Path, line: str, script: Path | None = None
) -> subprocess.CompletedProcess[str]:
    """Load the bash `mh` with `bin/` first on `PATH`, then run `line`."""
    path = script or _bash_script(tmp_path)
    env = {"HOME": str(tmp_path), "PATH": f"{tmp_path / 'bin'}:/usr/bin:/bin"}
    return run_bash(f"{_FAKE_DOCKER}\nsource {path}; {line}; echo status=$?", env)


def _index(tmp_path: Path) -> Path:
    """Write the catalogue of the reports where `mh` looks for it."""
    reports = tmp_path / "media-hygiene" / "reports"
    reports.mkdir(parents=True)
    index = reports / "index.html"
    index.write_text("<html></html>", encoding="utf-8")
    return index


def _powershell() -> str:
    """The French `mh.ps1`, as PowerShell evaluates its strings."""
    with using(Locale.FR):
        text = render_script(launcher_script(accented_runtime(), None, _COMMANDS))
    assert text.isascii()
    return expanded(text)


def test_bash_open_gives_the_index_to_the_opener(tmp_path: Path) -> None:
    """0175: `xdg-open` gets the catalogue's host path; docker is not called."""
    index = _index(tmp_path)
    record = tmp_path / "opened.txt"
    fake_program(tmp_path / "bin", "xdg-open", f'echo "$1" > {record}')
    done = _bash(tmp_path, "mh open")
    assert "status=0" in done.stdout
    assert "ran:" not in done.stdout
    assert record.read_text(encoding="utf-8") == f"{index}\n"


def test_bash_open_on_wsl_gives_explorer_a_windows_path(tmp_path: Path) -> None:
    """0175: without wslview, `explorer.exe` gets the path `wslpath -w` gives."""
    _index(tmp_path)
    record = tmp_path / "opened.txt"
    fake_program(tmp_path / "bin", "wslpath", r'echo "C:\\fake\\$(basename "$2")"')
    fake_program(tmp_path / "bin", "explorer.exe", f'echo "$1" > {record}; exit 1')
    done = _bash(tmp_path, "mh open")
    assert "status=0" in done.stdout  # explorer.exe says 1 even when it opened it
    assert record.read_text(encoding="utf-8") == "C:\\fake\\index.html\n"


def test_bash_open_without_a_report_says_to_audit_first(tmp_path: Path) -> None:
    """0175: no `index.html`: one line, nothing opened."""
    record = tmp_path / "opened.txt"
    fake_program(tmp_path / "bin", "xdg-open", f'echo "$1" > {record}')
    done = _bash(tmp_path, "mh open")
    assert "status=1" in done.stdout
    assert done.stderr == "No report yet: type mh audit first.\n"
    assert not record.exists()


def test_bash_open_without_an_opener_names_the_file(tmp_path: Path) -> None:
    """0175: nothing to open a page: the file to open by hand."""
    index = _index(tmp_path)
    (tmp_path / "bin").mkdir()  # alone on PATH: no xdg-open of the machine's own
    done = _bash(tmp_path, 'OSTYPE=linux-gnu PATH="$HOME/bin" mh open')
    assert "status=1" in done.stdout
    assert f"open {index} yourself." in done.stderr


def test_open_on_a_named_volume_says_how_to_mount_a_folder(tmp_path: Path) -> None:
    """0175: a volume is no folder of the host: said, with the `-v` to use."""
    script = launcher_script(_runtime(tmp_path), Shell.BASH, _COMMANDS)
    tools = tuple(
        Volume("media-hygiene-reports", volume.point)
        if volume.point.name == "reports"
        else volume
        for volume in script.tools
    )
    path = _bash_script(tmp_path, replace(script, tools=tools))
    done = _bash(tmp_path, "mh open", path)
    assert "status=1" in done.stdout
    assert "Docker volume media-hygiene-reports" in done.stderr
    assert "-v <a folder of yours>:/reports" in done.stderr


@pytest.mark.parametrize("name", ["shortcut", "explorer"])
def test_bash_says_windows_only(tmp_path: Path, name: str) -> None:
    """0180, 0181: one line, status 2, no docker."""
    done = _bash(tmp_path, f"mh {name} --remove")
    assert done.stderr == f"mh {name} is for Windows only.\n"
    assert done.stdout == "status=2\n"


def test_bash_photos_and_menu_open_the_menu_on_that_folder(tmp_path: Path) -> None:
    """0181: the folder said, the step chosen runs with it, mounted under /data."""
    folder = tmp_path / "L'été 2019"
    folder.mkdir()
    done = _bash(tmp_path, f'mh menu --photos "{folder}" <<< 1')
    assert f"The step you choose also analyses: {folder}" in done.stderr
    ran = [line for line in done.stdout.splitlines() if line.startswith("ran:")]
    assert ran[-1] == "ran:audit"
    assert f"ran:{folder}:/data{folder}:ro" in ran


def test_powershell_dispatches_host_commands_before_docker() -> None:
    """One mechanism: each host command by its first word, before `docker run`."""
    text = _powershell()
    switch = text.index("    switch ($rest[0]) {")
    for name in HOST_COMMANDS:
        line = f"'{name}' {{ _mh_{name} @more; return }}"
        assert switch < text.index(line) < text.index("docker run --rm")
        assert f"function global:_mh_{name} {{" in text


def test_powershell_open_invokes_the_index_of_the_reports() -> None:
    """0175: `Invoke-Item` on the host folder of /reports; missing: the line."""
    text = _powershell()
    assert '$index = "$HOME\\media-hygiene\\reports\\index.html"' in text
    assert "Invoke-Item -LiteralPath $index" in text
    assert "Pas encore de rapport : tapez d'abord mh audit." in text


def test_powershell_shortcut_writes_then_reads_back_both_links() -> None:
    """0180: Desktop and Start menu, `-NoExit`, this file loaded; read back."""
    text = _powershell()
    assert "foreach ($place in 'Desktop', 'Programs') {" in text
    assert "[Environment]::GetFolderPath($place)) 'Media Hygiene.lnk'" in text
    assert "System32\\WindowsPowerShell\\v1.0\\powershell.exe" in text
    assert "'-NoExit -Command \"' + $load + '; ' + $words + '\"'" in text
    assert '$load = "try { . \'" + $file.Replace("\'", "\'\'") + "\' }' in text
    assert "$file = $MyInvocation.MyCommand.ScriptBlock.File" in text
    save = text.index("try { $link.Save() } catch { $reason, $refused = _mh_why $_;")
    back = text.index("$back = $shell.CreateShortcut($path)")
    assert save < back < text.index("$back.Arguments -eq $arguments")
    body = text[text.index("function global:_mh_shortcut {") :]
    assert "Enregistr\u00e9, relu depuis" not in body[: body.index("\n}\n")]


def test_powershell_shortcut_says_why_and_suggests_a_click_only_once_written() -> None:
    """0190: why a write failed, the refusal hint; one line when written."""
    text = _powershell()
    body = text[text.index("function global:_mh_shortcut {") :]
    body = body[: body.index("\n}\n")]
    assert 'Write-Host "Impossible d\'\u00e9crire ${path}."' in body
    assert 'if ($reason) { Write-Host "    $reason" }' in body
    counted = body.index("$written++")
    assert counted < body.index('Write-Host "Impossible d')
    assert 'if ($denied) { Write-Host "Acc\u00e8s refus\u00e9 : un antivirus' in body
    assert (
        'if ($written -gt 0) { Write-Host "Raccourci Media Hygiene cr\u00e9\u00e9'
        in body
    )


def test_powershell_why_keeps_the_innermost_message_and_spots_a_refusal() -> None:
    """0190: the COM wrapper unwrapped, access refused by type or by its HRESULT."""
    text = _powershell()
    assert "function global:_mh_why($record) {" in text
    assert "while ($exception.InnerException) {" in text
    assert "($exception -is [UnauthorizedAccessException])" in text
    assert "($exception.HResult -eq -2147024891)" in text
    assert -2147024891 == 0x80070005 - 2**32  # E_ACCESSDENIED


def test_powershell_explorer_writes_both_keys_and_reads_them_back() -> None:
    """0181, 0188: a folder and an open folder's background, HKCU, `%V`; `--remove`."""
    text = _powershell()
    assert f"$keys = '{EXPLORER_KEY}', '{BACKGROUND_KEY}'" in text
    assert EXPLORER_KEY.startswith("HKCU:\\")
    assert BACKGROUND_KEY == (
        "HKCU:\\Software\\Classes\\Directory\\Background\\shell\\MediaHygiene"
    )
    assert f"_mh_start 'mh {FROM_EXPLORER} #\" \"%V'" in text
    body = text[text.index("function global:_mh_explorer {") :]
    body = body[: body.index("\n}\n")]
    removing = body.index("if ($args -contains '--remove') {")
    assert body.count("foreach ($key in $keys) {") == 2
    assert removing < body.index("Remove-Item -LiteralPath $key -Recurse -Force")
    assert '$null = New-Item -Path "$key\\command" -Value $command -Force' in body
    assert "$read = if ($back) { $back.GetValue('') } else { $null }" in body
    assert "if ($read -eq $command) {" in body
    assert "Enregistr\u00e9, relu depuis" not in body
    assert body.count("Write-Host \"Impossible d'\u00e9crire ${path}") == 1
    assert body.count('Write-Host "Entr\u00e9e du clic droit retir\u00e9e') == 1
    hint = body.index('if ($written -gt 0) { Write-Host "Media Hygiene ajout\u00e9')
    assert hint > body.rindex("foreach ($key in $keys) {")


def test_powershell_explorer_catches_its_errors_and_says_why() -> None:
    """0190: each write stops on error, so the catch sees it; no red error record."""
    text = _powershell()
    body = text[text.index("function global:_mh_explorer {") :]
    body = body[: body.index("\n}\n")]
    assert body.count("-Force -ErrorAction Stop") == 4
    assert body.count("$reason, $denied = _mh_why $_") == 2
    assert body.count('if ($reason) { Write-Host "    $reason" }') == 2
    assert body.count('if ($denied) { Write-Host "Acc\u00e8s refus\u00e9') == 2


def test_the_icon_ships_in_the_package_at_every_windows_size() -> None:
    """0194: one `.ico`, 16 to 256 px, where `mh` copies it from."""
    with Image.open(ICON) as icon:
        sizes = icon.info["sizes"]
    assert sizes == {(16, 16), (24, 24), (32, 32), (48, 48), (256, 256)}
    assert Path(ICON).name == ICON_NAME


def test_powershell_icon_is_copied_by_docker_next_to_the_script() -> None:
    """0194: `docker cp` writes it (no script writes an image file); missing: a line."""
    text = _powershell()
    body = text[text.index("function global:_mh_icon($powershell) {") :]
    body = body[: body.index("\n}\n")]
    assert f"Join-Path (Split-Path -Parent $file) '{ICON_NAME}'" in body
    create = body.index("$container = docker create ")
    copy = body.index(f'$null = docker cp "${{container}}:{ICON}" $icon 2>$null')
    assert create < copy < body.index("$null = docker rm $container 2>$null")
    assert "if (Test-Path -LiteralPath $icon) { return $icon }" in body
    assert "L'ic\u00f4ne de Media Hygiene n'a pas pu \u00eatre copi\u00e9e" in body
    assert body.rstrip().endswith("$powershell")
    assert "FromBase64String" not in text


def test_powershell_shortcut_and_explorer_show_the_icon_read_back() -> None:
    """0194: both point to the copied icon; the read back is said only on failure."""
    text = _powershell()
    for name in ("shortcut", "explorer"):
        body = text[text.index(f"function global:_mh_{name}") :]
        body = body[: body.index("\n}\n")]
        checked = body.index("if (-not $arguments) { return }")
        assert checked < body.index("$icon = _mh_icon $powershell")
    assert '$link.IconLocation = "$icon,0"' in text
    assert "$($back.IconLocation)" not in text
    assert "-Name Icon -Value $icon -Force -ErrorAction Stop" in text


def _from_command_line(line: str) -> str:
    """What `mh --from-explorer` reads, as its PowerShell lines do."""
    at = line.rindex('#" "')
    return line[at + 4 :].rstrip().rstrip('"')


@pytest.mark.parametrize(
    "folder", ["C:\\Photos", "D:\\Mes photos\\L'été 2019", "E:\\", "F:\\a $b `c"]
)
def test_any_folder_name_comes_back_whole(folder: str) -> None:
    """0181: spaces, apostrophes, `$`, a drive root: Explorer's `%V`, read back."""
    text = _powershell()
    assert "$folder = $line.Substring($line.LastIndexOf('#\" \"') + 4)" in text
    command = (
        '"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -NoExit '
        "-Command \"try { . 'C:\\Users\\O''Neil\\mh.ps1' } catch { function "
        "global:mh { Write-Host 'PowerShell refused' } }; "
        f'mh {FROM_EXPLORER} #" "%V"'
    )
    line = command.replace("%V", folder)  # what Explorer starts
    code = line[: line.rindex("#")]
    assert folder not in code  # the name sits after the comment sign only
    assert _from_command_line(line) == folder
    assert PureWindowsPath(_from_command_line(line)) == PureWindowsPath(folder)


def test_powershell_photos_alone_open_the_menu_with_them() -> None:
    """0181: `--photos` parsed first; the menu's step gets them."""
    text = _powershell()
    parsed = text.index("$typed += '--photos', $found.ProviderPath")
    alone = text.index("    if ($rest.Count -eq 0) {")
    assert parsed < alone < text.index("        try { mh @words @typed }")
    assert 'Write-Host "L\'\u00e9tape choisie analyse aussi : ${shown}"' in text
    explorer = text.index(f"$args[0] -eq '{FROM_EXPLORER}'")
    assert explorer < parsed
    assert "        mh --photos $folder" in text


def test_the_launcher_tells_the_image_its_shell() -> None:
    """The menu hides the Windows steps from the bash `mh` only."""
    assert f'-e "{LAUNCHER_VARIABLE}=powershell"' in _powershell()


def test_menu_lists_open_after_audit_and_setup_on_windows(tmp_path: Path) -> None:
    """0175: `open` right after `audit`; 0180, 0181: setup last, not for bash."""
    status = read_status(make_runtime(make_locations(tmp_path)))
    menu = build_menu(status, _HINT)
    commands = [line.step.command for line in menu.steps]
    assert commands[commands.index("audit") + 1] == "open"
    setup = [line.step.command for line in menu.steps if line.section is Section.SETUP]
    assert setup == ["shortcut", "explorer"]
    assert menu.steps[-1].section is Section.SETUP
    bash = build_menu(status, _HINT, windows=False)
    assert not any(line.section is Section.SETUP for line in bash.steps)
    assert "open" in [line.step.command for line in bash.steps]


def test_under_the_launcher_the_report_tip_is_mh_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0175: `mh open` replaces where `index.html` lies; without mh, unchanged."""
    runtime = make_runtime(make_locations(tmp_path))
    report = runtime.locations.reports_dir / "report.html"
    monkeypatch.setenv(LAUNCHER_VARIABLE, "powershell")
    announce_report(runtime, report)
    runtime.output.finish()
    printed = output_of(runtime)
    assert "Type mh open: your browser shows every report." in printed
    assert "Open index.html" not in printed
    monkeypatch.delenv(LAUNCHER_VARIABLE)
    announce_report(runtime, report)
    runtime.output.finish()
    assert "Open index.html in the folder mounted on /reports" in output_of(runtime)
    assert os.environ.get(LAUNCHER_VARIABLE) is None


@pytest.mark.parametrize("shell", ["bash", "powershell"])
def test_the_menu_shows_the_windows_steps_to_powershell_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, shell: str
) -> None:
    """0180, 0181: `mh shortcut` and `mh explorer` are not offered to bash."""
    listed = shell == "powershell"
    monkeypatch.setenv("MEDIA_HYGIENE_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv(LAUNCHER_VARIABLE, shell)
    result = CliRunner().invoke(build_app(), ["menu"])
    assert result.exit_code == 0, result.output
    assert ("mh shortcut" in result.stderr) is listed
    assert ("mh explorer" in result.stderr) is listed
    assert "mh open" in result.stderr
