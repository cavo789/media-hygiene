r"""Keep `mh.ps1` pure ASCII: PowerShell decodes `launcher > mh.ps1` with a code page.

Windows PowerShell 5.1 and PowerShell 7 both decode the output of a native program with
the console's code page (850, 437…) before `>` writes it: the UTF-8 `é` of
`C:\Photos\Vidéos` became `├®`, and `mh` mounted a folder that does not exist (TODO
0098). An ASCII script survives any code page. In its code, every other character
becomes a `$([char]0x00E9)` subexpression, which PowerShell expands inside the
double-quoted strings that hold every path and option. In comments, accents are
dropped (`à` → `a`): nothing reads them back.
"""

from __future__ import annotations

import unicodedata
from typing import Final

_COMMENT: Final = "#"
_LAST_ASCII: Final = 0x7F
_LAST_BMP: Final = 0xFFFF  # beyond it, one character is two UTF-16 units
_UNKNOWN: Final = "?"


def ascii_powershell(script: str) -> str:
    """Rewrite a PowerShell script so that it holds ASCII characters only.

    Args:
        script: The script, any characters.

    Returns:
        The same script: its code evaluates to the same strings, its comments read
        without their accents.
    """
    return "".join(
        _ascii_comment(line) if line.lstrip().startswith(_COMMENT) else _escaped(line)
        for line in script.splitlines(keepends=True)
    )


def _escaped(line: str) -> str:
    """Escape the non-ASCII characters of a line of code.

    Args:
        line: A line whose non-ASCII characters lie in double-quoted strings.

    Returns:
        The line, each such character written as a PowerShell subexpression.
    """
    return "".join(_char(character) for character in line)


def _char(character: str) -> str:
    """Write one character as PowerShell rebuilds it inside a double-quoted string.

    Args:
        character: The character.

    Returns:
        Itself when ASCII, else a `$(...)` subexpression.
    """
    code = ord(character)
    if code <= _LAST_ASCII:
        return character
    if code <= _LAST_BMP:
        return f"$([char]0x{code:04X})"
    return f"$([char]::ConvertFromUtf32(0x{code:X}))"


def _ascii_comment(line: str) -> str:
    """Drop the accents of a comment line, and what no ASCII letter stands for.

    Args:
        line: A comment line.

    Returns:
        The line in ASCII.
    """
    decomposed = unicodedata.normalize("NFKD", line)
    kept = (
        character
        for character in decomposed
        if ord(character) <= _LAST_ASCII or not unicodedata.combining(character)
    )
    return "".join(
        character if ord(character) <= _LAST_ASCII else _UNKNOWN for character in kept
    )
