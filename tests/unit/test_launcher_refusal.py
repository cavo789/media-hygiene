"""`docker run -it … launcher`: a refusal script, since `-t` joins the streams."""

from __future__ import annotations

import shutil
import subprocess
from typing import TYPE_CHECKING

from media_hygiene.constants import Locale
from media_hygiene.i18n import install
from media_hygiene.paths.docker_run import Shell
from media_hygiene.services.launcher_refusal import refusal_script

if TYPE_CHECKING:
    from pathlib import Path


def test_powershell_reads_the_advice_then_stops_in_ascii() -> None:
    """Comments to read on screen, then a `throw` PowerShell 5.1 cannot garble."""
    install(Locale.FR)
    lines = refusal_script(Shell.POWERSHELL).splitlines()
    assert lines[0] == (
        "# Rien n'a été écrit : le lanceur va dans un fichier, pas à l'écran."
    )
    assert lines[1].startswith("# Relancez la même commande sans -it")
    assert lines[1].endswith('> "$HOME\\media-hygiene\\mh.ps1"')
    assert lines[2].isascii()
    assert lines[2].startswith("throw ('Rien n''a ' + [char]::ConvertFromUtf32(0xE9)")
    assert "[char]::ConvertFromUtf32(0xEA) + 'me commande sans -it" in lines[2]
    assert len(lines) == len(set(lines)) == 3


def test_bash_prints_the_advice_and_stops_loading(tmp_path: Path) -> None:
    r"""Sourced with the \r\n of the pseudo-terminal: the advice, status 2, no mh."""
    script = tmp_path / "mh.sh"
    script.write_bytes(refusal_script(Shell.BASH).replace("\n", "\r\n").encode())
    bash = shutil.which("bash") or "bash"
    line = f"source {script}; echo status=$?; type mh"
    # Trusted script written by the test itself, run on its temporary folder.
    done = subprocess.run(  # noqa: S603
        [bash, "-c", line], capture_output=True, text=True, check=False
    )
    assert "status=2" in done.stdout
    assert "Run the same command without -it" in done.stderr
    assert '> "$HOME/media-hygiene/mh.sh"' in done.stderr
    assert "\r" not in done.stderr
