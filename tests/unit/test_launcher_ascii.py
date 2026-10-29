r"""`mh.ps1` is pure ASCII: `launcher > mh.ps1` survives any code page (0098)."""

from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import Locale
from media_hygiene.i18n import using
from media_hygiene.paths.docker_run import Shell
from media_hygiene.paths.locations import Locations
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.paths.mounts import MountTable
from media_hygiene.services.launcher import (
    LauncherCommands,
    launcher_script,
    render_script,
)
from media_hygiene.services.launcher_ascii import ascii_powershell
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime

_VIDEOS: Final = Path("/data/c/Photos/Vidéos")
_SUMMER: Final = Path("/data/d/Été 2019")
_COMMANDS: Final = LauncherCommands(("audit",), (), (), (), 8088)
# How PowerShell expands the escapes inside a double-quoted string.
_BMP: Final = re.compile(r"\$\(\[char\]0x([0-9A-F]{4})\)")
_ASTRAL: Final = re.compile(r"\$\(\[char\]::ConvertFromUtf32\(0x([0-9A-F]+)\)\)")


def expanded(text: str) -> str:
    """The strings of the script as PowerShell evaluates them."""
    text = _ASTRAL.sub(lambda match: chr(int(match[1], 16)), text)
    return _BMP.sub(lambda match: chr(int(match[1], 16)), text)


def accented_runtime() -> Runtime:
    """An audit of two accented Windows folders."""
    locations = Locations.model_validate(
        {f"{kind.value}_dir": Path(f"/{kind.value}") for kind in MountKind}
    )
    table = MountTable(
        frozenset({_VIDEOS, _SUMMER}),
        ((_VIDEOS, "C:\\Photos\\Vidéos"), (_SUMMER, "D:\\Été 2019")),
    )
    return replace(make_runtime(locations), mounts=table)


def test_an_accented_folder_is_written_in_ascii_and_read_back() -> None:
    """Every character is ASCII; PowerShell rebuilds the very folder names."""
    with using(Locale.FR):
        text = render_script(launcher_script(accented_runtime(), None, _COMMANDS))
    assert text.isascii()
    assert "Vid$([char]0x00E9)os" in text
    back = expanded(text)
    assert "'-v'; \"C:\\Photos\\Vidéos:/data/c/Photos/Vidéos${mode}\" }" in back
    assert "'-v'; \"D:\\Été 2019:/data/d/Été 2019${mode}\" }" in back


def test_comments_lose_their_accents_only() -> None:
    """A French header stays readable: `à même` becomes `a meme`."""
    script = '# Ajoutez-la à $PROFILE, même ligne\n$a = "x"\n'
    expected = '# Ajoutez-la a $PROFILE, meme ligne\n$a = "x"\n'
    assert ascii_powershell(script) == expected


def test_a_character_beyond_utf16_units_is_rebuilt_whole() -> None:
    """An emoji in a folder name: one ConvertFromUtf32, not two [char]."""
    text = ascii_powershell('-v "C:\\Fêtes 🎉:/data"\n')
    assert text.isascii()
    assert "ConvertFromUtf32(0x1F389)" in text
    assert expanded(text) == '-v "C:\\Fêtes 🎉:/data"\n'


def test_bash_keeps_utf8() -> None:
    """The bash script is UTF-8 end to end: left as is."""
    runtime = accented_runtime()
    text = render_script(launcher_script(runtime, Shell.BASH, _COMMANDS))
    assert "Vidéos" in text
