r"""`mh folders` and `mh update`: `mh` runs `launcher` again and rewrites itself.

TODOs 0176 (`mh folders`: list, add, remove a photo folder) and 0177 (`mh update`: pull
the image, then the same rewrite). The bash tests run the real `launcher` behind a
fake `docker`, so the script written, loaded and read back is the tool's own.
"""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Final

import pytest
from typer.testing import CliRunner

from media_hygiene.cli.app import build_app
from media_hygiene.constants import Locale
from media_hygiene.i18n import using
from media_hygiene.paths.docker_run import (
    IMAGE_VARIABLE,
    PUBLISHED_IMAGE,
    Shell,
    Volume,
)
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.paths.mounts import MountTable
from media_hygiene.services.launcher import (
    LauncherCommands,
    launcher_script,
    render_script,
)
from media_hygiene.services.launcher_file import written
from media_hygiene.services.launcher_folders import FolderChoice, with_folders
from media_hygiene.services.launcher_kept import kept_run, quoted
from media_hygiene.services.launcher_stamp import LAUNCHER_STAMP_VARIABLE, image_stamp
from media_hygiene.services.next_command import LAUNCHER_VARIABLE
from tests.support.runtime import make_locations, make_runtime
from tests.unit.test_launcher_ascii import accented_runtime, expanded

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime

pytestmark = pytest.mark.skipif(shutil.which("bash") is None, reason="no bash")

# The stamp of an older image, as an mh.sh written by it passes it (0290).
_OLDER: Final = f"{LAUNCHER_STAMP_VARIABLE}=0.3.0+000000000000"
# A local build: its name in the image's environment, as the Dockerfile's `local` has.
_LOCAL: Final = {"IMAGE": "media-hygiene", IMAGE_VARIABLE: "media-hygiene"}
_COMMANDS: Final = LauncherCommands(("audit", "menu"), (), (), ("menu",), 8088)
# The image's stand-in: `run` starts the real CLI with the `-e` given, `pull` and
# `image inspect` play a registry whose image id lives in `$FAKE/id`; every call is
# logged in `$FAKE/calls`.
_FAKE_DOCKER: Final = r"""#!/bin/bash
printf '%s\n' "$*" >> "$FAKE/calls"
case "$1" in
    pull)
        if [[ -n "${PULL_FAILS:-}" ]]; then exit 1; fi
        printf 'Pulling %s\n' "$2"
        if [[ -f "$FAKE/next" ]]; then cp "$FAKE/next" "$FAKE/id"; fi
        exit 0 ;;
    image)
        if [[ "$4" == *Size* ]]; then echo 104857600; exit 0; fi
        cat "$FAKE/id" ;;
    run)
        shift
        settings=()
        while [[ $# -gt 0 && "$1" != "$IMAGE" ]]; do
            case "$1" in
                -e) settings+=("$2"); shift 2 ;;
                -v) shift 2 ;;
                *) shift ;;
            esac
        done
        shift
        if [[ "${1:-}" == --version ]]; then
            echo "media-hygiene $(cat "$FAKE/id")"
            exit 0
        fi
        if [[ -n "${LAUNCHER_FAILS:-}" ]]; then echo '# refused'; exit 2; fi
        exec env "${settings[@]}" "$PYTHON" -m media_hygiene "$@" ;;
esac
"""


def _environment(tmp_path: Path, **extra: str) -> dict[str, str]:
    """A clean environment: the fake `docker` first, the tool folders in the test's.

    The interpreter's own settings stay (`PYTHONPYCACHEPREFIX`: no `__pycache__` in
    the tree).
    """
    names = {
        f"MEDIA_HYGIENE_{kind.value.upper()}_DIR": kind.value for kind in MountKind
    }
    folders = {name: str(tmp_path / "in" / value) for name, value in names.items()}
    for folder in folders.values():
        Path(folder).mkdir(parents=True, exist_ok=True)
    python = {
        name: value for name, value in os.environ.items() if name.startswith("PYTHON")
    }
    return {
        **python,
        "HOME": str(tmp_path),
        "PATH": f"{tmp_path / 'bin'}:/usr/bin:/bin",
        "FAKE": str(tmp_path),
        "IMAGE": extra.pop("IMAGE", PUBLISHED_IMAGE),
        "PYTHON": sys.executable,
        **folders,
        **extra,
    }


def _written(tmp_path: Path, *folders: Path, **extra: str) -> Path:
    """Write `mh.sh` with the real `launcher`, as the guides do; `docker` faked."""
    fake = tmp_path / "bin" / "docker"
    fake.parent.mkdir(exist_ok=True)
    fake.write_text(_FAKE_DOCKER, encoding="utf-8")
    fake.chmod(0o755)
    (tmp_path / "id").write_text("old\n", encoding="utf-8")
    photos = [word for folder in folders for word in ("--photos", str(folder))]
    # The tool's own CLI, on the test's folders.
    done = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "media_hygiene", "launcher", "--shell", "bash", *photos],
        capture_output=True,
        text=True,
        check=True,
        env=_environment(tmp_path, **extra),
        timeout=60,
    )
    script = tmp_path / "media-hygiene" / "mh.sh"
    script.parent.mkdir(exist_ok=True)
    script.write_text(done.stdout, encoding="utf-8")
    return script


def _mh(
    tmp_path: Path, script: Path, line: str, **extra: str
) -> subprocess.CompletedProcess[str]:
    """Load `mh.sh`, run `line`, then `_mh_photos` as the shell holds it now."""
    bash = shutil.which("bash") or "bash"
    after = "echo status=$?; printf 'held:%s\\n' \"${_mh_photos[@]}\""
    # Trusted script written by the tool itself, run on the test's folder.
    return subprocess.run(  # noqa: S603
        [bash, "-c", f"source {script}; {line}; {after}"],
        capture_output=True,
        text=True,
        check=False,
        env=_environment(tmp_path, **extra),
        timeout=120,
    )


def _folders(tmp_path: Path, *names: str) -> list[Path]:
    """Create photo folders in the test's folder."""
    made = [tmp_path / name for name in names]
    for folder in made:
        folder.mkdir()
    return made


def _calls(tmp_path: Path) -> str:
    """What the fake `docker` was asked, one call per line; nothing yet: empty."""
    calls = tmp_path / "calls"
    return calls.read_text(encoding="utf-8") if calls.exists() else ""


def _held(done: subprocess.CompletedProcess[str]) -> list[str]:
    """The photo folders the shell holds after the command."""
    return [line[5:] for line in done.stdout.splitlines() if line.startswith("held:")]


def test_folders_add_rewrites_reloads_and_reads_back(tmp_path: Path) -> None:
    """0176: `launcher` again with one more --photos; the file replaced and loaded."""
    photos, more = _folders(tmp_path, "Photos", "L'été $2019")
    script = _written(tmp_path, photos)
    done = _mh(tmp_path, script, f"mh folders add {shlex.quote(f'{more}')}")
    assert "status=0" in done.stdout, done.stderr
    assert _held(done) == [str(photos), str(more)]
    calls = _calls(tmp_path)
    assert f"launcher --shell bash --photos {photos} --photos {more}" in calls
    assert f"Saved, read back from {script}:" in done.stdout
    assert f"    {more}: found" in done.stdout
    assert quoted(str(more), Shell.BASH) in script.read_text(encoding="utf-8")
    assert not script.with_name("mh.sh.new").exists()
    assert "Launcher written" not in done.stderr  # mh loads it itself
    listed = _mh(tmp_path, script, "mh folders")
    assert f"    {more}: found" in listed.stdout
    assert "Your photo folders:" in listed.stdout


def test_folders_remove_takes_a_renamed_folder_out(tmp_path: Path) -> None:
    """0176: a folder renamed in Explorer is gone: removed all the same."""
    photos, old = _folders(tmp_path, "Photos", "Old disk")
    script = _written(tmp_path, photos, old)
    renamed = old.with_name("Renamed disk")
    old.rename(renamed)
    listed = _mh(tmp_path, script, "mh folders")
    assert f"    {old}: not found: is its disk plugged in?" in listed.stdout
    done = _mh(tmp_path, script, f"mh folders remove {shlex.quote(f'{old}/')}")
    assert "status=0" in done.stdout, done.stderr
    assert _held(done) == [str(photos)]
    added = _mh(tmp_path, script, f"mh folders add {shlex.quote(f'{renamed}')}")
    assert _held(added) == [str(photos), str(renamed)]


def test_folders_says_a_quarantine_is_made_by_the_first_clean(tmp_path: Path) -> None:
    """Review of 2026-10-16: a quarantine not made yet is not "not found"."""
    (photos,) = _folders(tmp_path, "Photos")
    script = _written(tmp_path, photos)
    quarantine = tmp_path / "media-hygiene" / "quarantine"
    unborn = _mh(tmp_path, script, "mh folders")
    assert f"    {quarantine}: not created yet: the first clean creates it" in (
        unborn.stdout
    )
    quarantine.mkdir(parents=True)
    assert f"    {quarantine}: found" in _mh(tmp_path, script, "mh folders").stdout


def test_a_failing_launcher_leaves_mh_as_it_was(tmp_path: Path) -> None:
    """0176: no `> mh.sh`: a refusal writes nothing over the old file."""
    photos, more = _folders(tmp_path, "Photos", "More")
    script = _written(tmp_path, photos)
    before = script.read_text(encoding="utf-8")
    done = _mh(
        tmp_path, script, f"mh folders add {shlex.quote(f'{more}')}", LAUNCHER_FAILS="1"
    )
    assert "status=1" in done.stdout
    assert "mh is unchanged: launcher refused it (see above)." in done.stderr
    assert script.read_text(encoding="utf-8") == before
    assert not script.with_name("mh.sh.new").exists()
    assert _held(done) == [str(photos)]


@pytest.mark.parametrize(
    ("line", "said"),
    [
        ("mh folders remove {photos}", "mh needs at least one photo folder"),
        ("mh folders remove /elsewhere", "/elsewhere is not one of your folders"),
        ("mh folders add /no/such/folder", "/no/such/folder cannot be found"),
        ("mh folders add {photos}", "is one of your folders already."),
        ("mh folders move {photos}", "Add or remove a photo folder: mh folders add"),
    ],
)
def test_refusals_leave_mh_untouched(tmp_path: Path, line: str, said: str) -> None:
    """0176: the last folder, an unknown one, a missing one: said, nothing run."""
    (photos,) = _folders(tmp_path, "Photos")
    script = _written(tmp_path, photos)
    before = script.read_text(encoding="utf-8")
    calls = _calls(tmp_path)
    done = _mh(tmp_path, script, line.format(photos=photos))
    assert said in done.stderr
    assert script.read_text(encoding="utf-8") == before
    assert _calls(tmp_path) == calls


def test_update_pulls_rewrites_and_says_both_versions(tmp_path: Path) -> None:
    """0177: pull of the script's image, the same folders, before → after, space."""
    (photos,) = _folders(tmp_path, "Photos")
    script = _written(tmp_path, photos)
    (tmp_path / "next").write_text("new\n", encoding="utf-8")
    done = _mh(tmp_path, script, "mh update")
    assert "status=0" in done.stdout, done.stderr
    calls = _calls(tmp_path).splitlines()
    assert f"pull {PUBLISHED_IMAGE}" in calls
    assert any(
        call.endswith(f"launcher --shell bash --photos {photos}") for call in calls
    )
    assert f"Pulling {PUBLISHED_IMAGE}" in done.stdout
    assert (
        "Updated: media-hygiene old → media-hygiene new. What changed: "
        "https://github.com/cavo789/media-hygiene/releases"
    ) in done.stdout
    assert "still takes 100 MB: docker image prune frees it." in done.stdout
    assert not any(call.startswith(("image prune", "rmi")) for call in calls)
    assert _held(done) == [str(photos)]


def test_update_without_a_new_image_says_already_the_latest(tmp_path: Path) -> None:
    """0177: same image id after the pull: the version, no space line."""
    (photos,) = _folders(tmp_path, "Photos")
    script = _written(tmp_path, photos)
    done = _mh(tmp_path, script, "mh update")
    assert "Already the latest version: media-hygiene old." in done.stdout
    assert "MB" not in done.stdout


def test_a_failed_pull_leaves_mh_as_it_was(tmp_path: Path) -> None:
    """0177: no network: said; the script is not written again."""
    (photos,) = _folders(tmp_path, "Photos")
    script = _written(tmp_path, photos)
    before = script.read_text(encoding="utf-8")
    done = _mh(tmp_path, script, "mh update", PULL_FAILS="1")
    assert "status=1" in done.stdout
    assert "docker pull failed: mh is unchanged." in done.stderr
    assert script.read_text(encoding="utf-8") == before
    calls = _calls(tmp_path)
    assert "launcher --shell bash --photos" not in calls.split("pull ")[-1]


def test_a_local_build_is_written_again_without_a_pull(tmp_path: Path) -> None:
    """0290: a developer's build: nothing pulled, mh written again, same folders."""
    (photos,) = _folders(tmp_path, "Photos")
    script = _written(tmp_path, photos, **_LOCAL)
    stamp = f'{LAUNCHER_STAMP_VARIABLE}={image_stamp()}"'
    older = script.read_text(encoding="utf-8").replace(stamp, f'{_OLDER}"')
    script.write_text(older, encoding="utf-8")
    done = _mh(tmp_path, script, "mh update", **_LOCAL)
    assert "status=0" in done.stdout, done.stderr
    assert "local build: nothing to pull. mh is written again" in done.stdout
    assert "pull" not in _calls(tmp_path)
    assert f"launcher --shell bash --photos {photos}" in _calls(tmp_path)
    assert _held(done) == [str(photos)]
    assert stamp in script.read_text(encoding="utf-8")  # read back from disk


@pytest.mark.parametrize(
    ("stamp", "said"),
    [
        (_OLDER, "written by the image 0.3.0 (build 000000000000), this one is"),
        ("", "written by an older image than"),
    ],
)
def test_an_mh_of_another_image_says_so_until_updated(
    tmp_path: Path, stamp: str, said: str
) -> None:
    """0290: an older mh.sh names mh update at each call; after it, nothing."""
    (photos,) = _folders(tmp_path, "Photos")
    script = _written(tmp_path, photos, **_LOCAL)
    current = f' -e "{LAUNCHER_STAMP_VARIABLE}={image_stamp()}"'
    text = script.read_text(encoding="utf-8")
    assert current in text
    older = f' -e "{stamp}"' if stamp else ""
    script.write_text(text.replace(current, older), encoding="utf-8")
    line = "mh history; mh history"
    before = _said(_mh(tmp_path, script, line, **_LOCAL))
    assert before.count(said) == 2
    assert "type mh update to write it again, with the same folders." in before
    _mh(tmp_path, script, "mh update", **_LOCAL)
    after = _said(_mh(tmp_path, script, line, **_LOCAL))
    assert "No run yet." in after
    assert "mh update" not in after


def _said(done: subprocess.CompletedProcess[str]) -> str:
    """Both streams, the console's line wrapping undone."""
    return " ".join((done.stdout + done.stderr).split())


def _runtime(tmp_path: Path) -> Runtime:
    """A run without any mount: the tool folders default to the home."""
    return replace(
        make_runtime(make_locations(tmp_path)), mounts=MountTable(frozenset())
    )


def test_kept_run_gives_back_what_launcher_cannot_rebuild(tmp_path: Path) -> None:
    """A `-v` elsewhere, a named volume, a tool folder by hand stay `-v`; language."""
    runtime = _runtime(tmp_path)
    script = with_folders(
        runtime,
        launcher_script(runtime, Shell.POWERSHELL, _COMMANDS),
        FolderChoice(("C:\\Photos",), "D:\\quarantine"),
    )
    reports = script.tools[2]
    script = replace(
        script,
        data=(
            *script.data,
            Volume("D:\\Old", Path("/data/old")),
            Volume("photos-volume", Path("/data/volume")),
        ),
        tools=(
            *script.tools[:2],
            replace(reports, host="E:\\reports"),
            *script.tools[3:],
        ),
        environment=('-e "MEDIA_HYGIENE_GENERAL__LOCALE=fr"', '-e "TZ=Europe/Paris"'),
    )
    kept = kept_run(script)
    assert kept.photos == ('"C:\\Photos"',)
    assert kept.fixed == 2  # D:\Old and the named volume: photos all the same
    assert kept.launcher == (
        '"--locale"', '"fr"', '"launcher"', '"--shell"', '"powershell"',
        '"--quarantine"', '"D:\\quarantine"',
    )  # fmt: skip
    assert kept.docker == (
        '"-e"', '"TZ=Europe/Paris"',
        '"-v"', '"D:\\Old:/data/old:ro"',
        '"-v"', '"photos-volume:/data/volume:ro"',
        '"-v"', f'"E:\\reports:{reports.point.as_posix()}"',
    )  # fmt: skip
    assert kept.quarantine == '"D:\\quarantine"'


def test_powershell_keeps_the_run_in_ascii_and_rewrites_safely() -> None:
    """0176: accents rebuilt; the file replaced only after `launcher` succeeded."""
    with using(Locale.FR):
        text = render_script(launcher_script(accented_runtime(), None, _COMMANDS))
    assert text.isascii()
    back = expanded(text)
    assert (
        'function global:_mh_photos { @("C:\\Photos\\Vidéos", "D:\\Été 2019") }'
    ) in back
    assert '$words = @("launcher", "--shell", "powershell")' in back
    run = back.index(
        '$lines = @(docker run --rm -e "MEDIA_HYGIENE_LAUNCHER=powershell"'
    )
    check = back.index("if ($LASTEXITCODE -ne 0 -or $lines.Count -eq 0)")
    save = back.index("Set-Content -LiteralPath $temp -Value $lines -Encoding Ascii")
    move = back.index("Move-Item -LiteralPath $temp -Destination $file -Force")
    load = back.index("    . $file\n")
    assert run < check < save < move < load < back.index("    _mh_list\n", load)
    assert "$file = $MyInvocation.MyCommand.ScriptBlock.File" in back


def test_powershell_folders_says_a_quarantine_is_made_by_the_first_clean() -> None:
    """Review of 2026-10-16: missing on a disk that is there, not "not found"."""
    with using(Locale.FR):
        back = expanded(
            render_script(launcher_script(accented_runtime(), None, _COMMANDS))
        )
    assert "function global:_mh_state($folder, $quarantine = $false) {" in back
    assert '    _mh_state "$HOME\\media-hygiene\\quarantine" $true\n' in back
    assert (
        '(Test-Path -LiteralPath $root)) { $state = "pas encore cr\u00e9\u00e9e' in back
    )


def test_powershell_functions_are_global_and_host_words_splatted() -> None:
    """Loaded again from inside `mh`, the functions must land in the global scope."""
    text = render_script(launcher_script(accented_runtime(), None, _COMMANDS))
    functions = [line for line in text.splitlines() if line.startswith("function ")]
    assert functions
    assert all(line.startswith("function global:") for line in functions)
    assert "    $more = @($rest | Select-Object -Skip 1)" in text
    assert "        'folders' { _mh_folders @more; return }" in text
    assert "        'update' { _mh_update @more; return }" in text


@pytest.mark.parametrize(("image", "pulls"), [("", True), ("media-hygiene", False)])
def test_powershell_update_pulls_the_published_image_only(
    monkeypatch: pytest.MonkeyPatch,
    image: str,
    pulls: bool,  # noqa: FBT001
) -> None:
    """0177: `docker pull` of the image written; a local build says so."""
    monkeypatch.setenv(IMAGE_VARIABLE, image)
    text = render_script(launcher_script(accented_runtime(), None, _COMMANDS))
    assert (f"    $image = '{PUBLISHED_IMAGE}'" in text) is pulls
    assert ("    docker pull $image" in text) is pulls
    assert ("local build: nothing to pull" in text) is not pulls
    assert pulls or "    $null = _mh_rewrite $photos $backups" in text
    assert "docker image prune" in text or not pulls
    assert "image prune\n" not in text  # said, never run


def test_launcher_under_mh_does_not_say_how_to_load_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """0176: `mh` loads the new file and reads it back itself."""
    monkeypatch.delenv(LAUNCHER_VARIABLE, raising=False)
    assert written(Shell.BASH).startswith("Launcher written.")
    monkeypatch.setenv(LAUNCHER_VARIABLE, "bash")
    assert not written(Shell.BASH)


def test_the_menu_ends_on_folders_and_update(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0176, 0177, 0265: entries of the menu now, run by `mh` itself."""
    monkeypatch.setenv("MEDIA_HYGIENE_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv(LAUNCHER_VARIABLE, "bash")
    result = CliRunner().invoke(build_app(), ["menu"])
    assert result.exit_code == 0, result.output
    assert "mh folders " in result.stderr
    assert "mh update " in result.stderr
    assert any(line.endswith("\tfolders") for line in result.stdout.splitlines())
    assert any(line.endswith("\tupdate") for line in result.stdout.splitlines())


def test_folders_add_backup_rewrites_and_keeps_it_apart(tmp_path: Path) -> None:
    """0205: `add --backup`: `launcher --backup`, listed apart, kept by the rewrite."""
    photos, backup, more = _folders(tmp_path, "Photos", "Backup disk", "More")
    script = _written(tmp_path, photos)
    done = _mh(tmp_path, script, f"mh folders add --backup {shlex.quote(f'{backup}')}")
    assert "status=0" in done.stdout, done.stderr
    assert _held(done) == [str(photos)]
    assert f"--photos {photos} --backup {backup}" in _calls(tmp_path)
    text = script.read_text(encoding="utf-8")
    assert f"_mh_backups=({quoted(str(backup), Shell.BASH)})" in text
    mount = next(line for line in text.splitlines() if f'-v "{backup}:' in line)
    assert mount.endswith('Backup disk:ro" \\')
    listed = _mh(tmp_path, script, "mh folders")
    backups = listed.stdout.index("Your backups, compared, never changed:")
    assert listed.stdout.index(f"    {backup}: found", backups) > backups
    # Another folder added: the rewrite gives the backup back.
    added = _mh(tmp_path, script, f"mh folders add {shlex.quote(f'{more}')}")
    assert _held(added) == [str(photos), str(more)]
    assert f"--photos {photos} --photos {more} --backup {backup}" in _calls(tmp_path)
    again = _mh(tmp_path, script, f"mh folders add --backup {shlex.quote(f'{backup}')}")
    assert "is one of your folders already" in again.stderr
    removed = _mh(tmp_path, script, f"mh folders remove {shlex.quote(f'{backup}')}")
    assert "status=0" in removed.stdout, removed.stderr
    assert _held(removed) == [str(photos), str(more)]
    assert "_mh_backups=()" in script.read_text(encoding="utf-8")
    assert "Your backups" not in removed.stdout


def test_removing_the_last_photo_folder_is_refused_even_with_a_backup(
    tmp_path: Path,
) -> None:
    """A backup is no photo folder: `mh` still needs one of those."""
    photos, backup = _folders(tmp_path, "Photos", "Backup")
    script = _written(tmp_path, photos)
    _mh(tmp_path, script, f"mh folders add --backup {shlex.quote(f'{backup}')}")
    done = _mh(tmp_path, script, f"mh folders remove {shlex.quote(f'{photos}')}")
    assert "mh needs at least one photo folder" in done.stderr
    assert _held(done) == [str(photos)]
