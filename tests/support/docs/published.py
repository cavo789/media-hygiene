r"""The commands the tool suggests, as a reader of the documentation would see them.

The demo runs on Docker volumes of its own, in a language given by `--locale`, without
colours: the `docker run` lines the tool prints name all of that, written for bash. Most
readers are on Windows: the documentation shows them as the tool writes them for
PowerShell instead (`C:\Photos`, the tool folders in the home, a backtick at the end of
each continued line, no `--user`).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

from tests.support.docs.names import Locale

if TYPE_CHECKING:
    from tests.support.docs.container import Demo

_HOME: Final = "$HOME\\media-hygiene"
_BASH_HOME: Final = "$HOME/media-hygiene/"  # a default folder the tool suggests
_CACHE: Final = "media-hygiene-cache"  # the named volume the guides advise
_ALWAYS_GIVEN: Final = " --color never"
_BASH_USER: Final = re.compile(r'(?m)^ *--user "\$\(id -u\):\$\(id -g\)" \\\n')
_CONTINUED: Final = re.compile(r"(?m) \\$")
_MKDIR: Final = re.compile(r'(?m)^(\s*)mkdir -p ((?:"[^"]*" ?)+)$')
_QUOTED: Final = re.compile(r'"[^"]*"')


def _hosts(demo: Demo) -> dict[str, str]:
    """What stands for each volume of the demo in the documentation."""
    hosts = {
        "c": "C:\\Photos",
        "d": f"D:\\{demo.library.names.old_disk}",
        "cache": _CACHE,
    }
    for kind in ("config", "reports", "journal", "quarantine"):
        hosts[kind] = f"{_HOME}\\{kind}"
    return hosts


def as_published(demo: Demo, text: str) -> str:
    """Rewrite the suggested commands of a capture for the documentation.

    Args:
        demo: The demo the capture comes from.
        text: The capture.

    Returns:
        The capture in PowerShell, its volumes named as a Windows user's folders,
        without the options every documentation run adds (`--color never`,
        `--locale en`: English is the default).
    """
    for kind, host in _hosts(demo).items():
        text = text.replace(f'"{demo.volume(kind)}:', f'"{host}:')
    text = text.replace(_BASH_HOME, f"{_HOME}\\")
    text = _BASH_USER.sub("", text)
    text = _CONTINUED.sub(" `", text)
    text = _MKDIR.sub(_mkdir_force, text)
    text = text.replace(_ALWAYS_GIVEN, "")
    if demo.locale == Locale.EN:
        text = text.replace(f" --locale {Locale.EN}", "")
    return text


def _mkdir_force(found: re.Match[str]) -> str:
    """`mkdir -p "a" "b"` as PowerShell writes it: `mkdir -Force "a", "b"`.

    Args:
        found: The `mkdir` line.

    Returns:
        The PowerShell line.
    """
    folders = _QUOTED.findall(found.group(2))
    return f"{found.group(1)}mkdir -Force " + ", ".join(folders)
