"""Read a text file the user may have edited on Windows, whatever its byte order mark.

Notepad saves "UTF-8 with BOM" on request, Windows PowerShell 5.1 adds a BOM with
`Set-Content -Encoding UTF8` and writes UTF-16 with `>` or `Out-File`. The tool writes
UTF-8 without BOM, and reads all of these back.
"""

from __future__ import annotations

import codecs
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from pathlib import Path

_UTF8: Final = "utf-8"
_UTF16: Final = "utf-16"  # reads the BOM to choose the byte order
_UTF16_BOMS: Final = (codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)


def decode_user_text(raw: bytes) -> str:
    """Decode bytes by their byte order mark: UTF-8 (with or without it), UTF-16.

    Args:
        raw: The content of the file.

    Returns:
        The text, without its byte order mark.

    Raises:
        UnicodeDecodeError: The content is not text in these encodings.
    """
    if raw.startswith(codecs.BOM_UTF8):
        return raw[len(codecs.BOM_UTF8) :].decode(_UTF8)
    if raw.startswith(_UTF16_BOMS):
        return raw.decode(_UTF16)
    return raw.decode(_UTF8)


def read_user_text(path: Path) -> str:
    """Read a text file by its byte order mark (see `decode_user_text`).

    Args:
        path: The file.

    Returns:
        Its text.

    Raises:
        OSError: The file cannot be read.
        UnicodeDecodeError: It is not text in these encodings.
    """
    return decode_user_text(path.read_bytes())
