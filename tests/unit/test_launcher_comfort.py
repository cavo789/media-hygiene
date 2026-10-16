"""What `mh` does around `docker run`: UTF-8, awake, title and sound, browser.

TODOs 0184 (UTF-8 console), 0179 (the computer kept awake during a long run), 0185 (the
window title and a sound at its end) and 0178 (the browser opened on a page).
"""

from __future__ import annotations

import http.server
import os
import shutil
import socket
import subprocess
import threading
from dataclasses import replace
from typing import TYPE_CHECKING, Final, override

import pytest

from media_hygiene.constants import Locale
from media_hygiene.i18n import using
from media_hygiene.paths.docker_run import Shell
from media_hygiene.paths.mounts import MountTable
from media_hygiene.services.launcher import (
    LauncherCommands,
    launcher_script,
    render_script,
)
from media_hygiene.services.next_command import LAUNCHER_VARIABLE
from media_hygiene.services.reviewing import address_tip
from tests.support.runtime import make_locations, make_runtime, output_of
from tests.unit.test_launcher_ascii import accented_runtime, expanded

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

_PORT: Final = 8088


def _commands(port: int = _PORT, wait: int = 5) -> LauncherCommands:
    """A CLI with a long command, a page command and a short one."""
    return LauncherCommands(
        names=("audit", "review", "history"),
        writers=(),
        pages=("review",),
        data=(),
        port=port,
        long=("audit",),
        browse_wait=wait,
    )


def _powershell() -> str:
    """The French `mh.ps1`, as PowerShell evaluates its strings."""
    with using(Locale.FR):
        text = render_script(launcher_script(accented_runtime(), None, _commands()))
    assert text.isascii()
    return expanded(text)


# `docker` stands in for the image: prints its arguments; with `WAIT_FOR`, waits (5 s
# at most) for that file, as a page stays open while the browser comes.
_FAKE_DOCKER: Final = r"""
docker() {
    printf 'ran:%s\n' "$@"
    local tries=100
    if [[ -n "${WAIT_FOR:-}" ]]; then
        while [[ ! -s "$WAIT_FOR" && $tries -gt 0 ]]; do
            sleep 0.1
            tries=$((tries - 1))
        done
    fi
    return "${DOCKER_STATUS:-0}"
}
"""


def _fake(folder: Path, name: str, body: str) -> None:
    """Write an executable `name` into `folder`."""
    path = folder / name
    path.write_text(f"#!/bin/bash\n{body}\n", encoding="utf-8")
    path.chmod(0o755)


def _bash(
    tmp_path: Path, line: str, extra: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Load the bash `mh` with `bin/` first on `PATH`, then run `line`."""
    port = int((extra or {}).get("PORT", _PORT))
    runtime = replace(
        make_runtime(make_locations(tmp_path)), mounts=MountTable(frozenset())
    )
    script = tmp_path / "mh.sh"
    commands = _commands(port, wait=int((extra or {}).get("WAIT", "5")))
    script.write_text(render_script(launcher_script(runtime, Shell.BASH, commands)))
    bash = shutil.which("bash") or "bash"
    env = {"HOME": str(tmp_path), "PATH": f"{tmp_path / 'bin'}:/usr/bin:/bin"}
    env |= extra or {}
    # Trusted script written by the test itself, run on its temporary folder.
    return subprocess.run(  # noqa: S603
        [bash, "-c", f"{_FAKE_DOCKER}\nsource {script}; {line}"],
        capture_output=True,
        text=True,
        check=False,
        env=env,
        timeout=60,
    )


@pytest.fixture
def bin_folder(tmp_path: Path) -> Path:
    """The folder of the fake host programs, first on `PATH`."""
    folder = tmp_path / "bin"
    folder.mkdir()
    return folder


@pytest.fixture
def page_port() -> Iterator[int]:
    """A page answering on a free port of the loopback, as the review does."""

    class Page(http.server.BaseHTTPRequestHandler):
        """Answers 200 to every GET, silently."""

        def do_GET(self) -> None:  # pylint: disable=invalid-name  # the server's name
            """Answer that the page is ready."""
            self.send_response(200)
            self.end_headers()

        @override
        def log_message(self, *args: object) -> None:
            """Keep the test's output clean."""
            del args

    server = http.server.HTTPServer(("127.0.0.1", 0), Page)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server.server_address[1]
    server.shutdown()
    server.server_close()


def _free_port() -> int:
    """A loopback port nothing listens on."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def test_powershell_reads_docker_in_utf8_and_restores_the_console() -> None:
    """0184: set before `docker run`, the user's encoding back in the `finally`."""
    text = _powershell()
    utf8 = "[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)"
    assert "$console = [Console]::OutputEncoding" in text
    assert "$OutputEncoding = [Console]::OutputEncoding" in text
    finally_ = text.index("    } finally {")
    assert text.index(utf8) < text.index("docker run --rm @tty") < finally_
    assert text.index("[Console]::OutputEncoding = $console", finally_) > finally_


def test_powershell_titles_long_commands_only_and_compiles_nothing() -> None:
    """0185: the list comes from the script data; 0179: no Add-Type (Avast)."""
    text = _powershell()
    assert "$long = $command -in @('audit')" in text
    assert "Add-Type" not in text
    assert "SetThreadExecutionState" not in text
    assert '$Host.UI.RawUI.WindowTitle = "mh $command..."' in text
    assert '{ "mh $command : terminé" } else { "mh $command : échec" }' in text
    assert "[Media.SystemSounds]::Asterisk.Play()" in text
    assert "[Media.SystemSounds]::Hand.Play()" in text
    assert "$Host.UI.RawUI.WindowTitle = $global:MediaHygieneTitle" in text


def test_powershell_opens_the_browser_for_pages_only() -> None:
    """0178: a job waits for the page, then `Start-Process`; removed at the end."""
    text = _powershell()
    assert "$page = if ($command -in @('review'))" in text
    job = text.index("if ($page) {")
    start = text.index("Start-Job -ArgumentList 'http://127.0.0.1:8088/', 5")
    assert job < start < text.index("Start-Process $url") < text.index("docker run")
    assert "Invoke-WebRequest -Uri $url -UseBasicParsing" in text
    assert "if ($i -lt $wait) { Start-Process $url }" in text
    assert "if ($browser) { Remove-Job -Job $browser -Force }" in text


def test_bash_wraps_a_long_command_with_systemd_inhibit(
    tmp_path: Path, bin_folder: Path
) -> None:
    """0179: `systemd-inhibit` before docker for `audit`, not for `history`."""
    record = tmp_path / "inhibit.txt"
    _fake(
        bin_folder, "systemd-inhibit", f'[[ "$1" == --list ]] || echo "$*" >> {record}'
    )
    done = _bash(tmp_path, "mh audit; mh history; echo status=$?")
    assert "status=0" in done.stdout
    lines = record.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert lines[0].startswith("--what=sleep --who=media-hygiene --why=audit -- docker")
    assert lines[0].endswith(" audit")


def test_bash_does_not_inhibit_on_wsl(tmp_path: Path, bin_folder: Path) -> None:
    """0179: on WSL, Windows decides; docker runs as is."""
    record = tmp_path / "inhibit.txt"
    _fake(bin_folder, "systemd-inhibit", f'echo "$*" >> {record}')
    done = _bash(tmp_path, "mh audit", {"WSL_DISTRO_NAME": "Ubuntu"})
    assert "ran:audit" in done.stdout
    assert not record.exists()


def test_bash_keeps_the_status_of_docker(tmp_path: Path) -> None:
    """0185: the title is set after, the status of the run is still returned."""
    done = _bash(tmp_path, "mh audit; echo status=$?", {"DOCKER_STATUS": "3"})
    assert "status=3" in done.stdout


def test_bash_opens_the_browser_once_the_page_answers(
    tmp_path: Path, bin_folder: Path, page_port: int
) -> None:
    """0178: `xdg-open` gets the page's address; docker stays in the foreground."""
    record = tmp_path / "opened.txt"
    _fake(bin_folder, "xdg-open", f'echo "$1" > {record}')
    extra = {"PORT": str(page_port), "WAIT_FOR": str(record)}
    done = _bash(tmp_path, "mh review", extra)
    assert "ran:review" in done.stdout
    assert record.read_text(encoding="utf-8") == f"http://127.0.0.1:{page_port}/\n"


def test_bash_opens_nothing_for_a_command_without_page(
    tmp_path: Path, bin_folder: Path
) -> None:
    """0178: `history` serves no page: no browser."""
    record = tmp_path / "opened.txt"
    _fake(bin_folder, "xdg-open", f'echo "$1" > {record}')
    done = _bash(tmp_path, "mh history")
    assert "ran:history" in done.stdout
    assert not record.exists()


def test_bash_gives_up_silently_on_a_page_that_never_answers(
    tmp_path: Path, bin_folder: Path
) -> None:
    """0178: the wait ends, nothing opened, nothing said."""
    record = tmp_path / "opened.txt"
    _fake(bin_folder, "xdg-open", f'echo "$1" > {record}')
    done = _bash(tmp_path, f"_mh_browse {_free_port()} 2; echo status=$?")
    assert done.stdout == "status=0\n"
    assert not done.stderr
    assert not record.exists()


def test_a_page_under_the_launcher_says_the_browser_opens(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0178: under `mh`, the browser line replaces the port tip."""
    runtime = make_runtime(make_locations(tmp_path))
    monkeypatch.setenv(LAUNCHER_VARIABLE, "1")
    address_tip(runtime.output, 8088)
    monkeypatch.delenv(LAUNCHER_VARIABLE)
    address_tip(runtime.output, 8088)
    printed = output_of(runtime)
    assert "Your browser opens on http://127.0.0.1:8088/; if not" in printed
    assert printed.count("-p 127.0.0.1:8088:8088") == 1
    assert os.environ.get(LAUNCHER_VARIABLE) is None
