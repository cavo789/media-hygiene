"""Files edited on Windows: a BOM, UTF-16, all read back; JSON written bare."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from media_hygiene.config.layers import read_file_layer
from media_hygiene.errors import ConfigError, DecisionsError
from media_hygiene.report.decisions import read_decisions, write_decisions

if TYPE_CHECKING:
    from pathlib import Path

SHOT = "C:\\Photos\\2005\\Décembre 2005 - Manon & Chloé\\IMG_1.jpg"
DECISIONS = {
    "version": 1,
    "roots": ["C:\\Photos"],
    "bursts": [{"kept": [], "discarded": [SHOT]}],
}
ENCODINGS = ["utf-8", "utf-8-sig", "utf-16", "utf-16-le-bom", "utf-16-be-bom"]


def encode(text: str, encoding: str) -> bytes:
    """Encode as Notepad or PowerShell would: `utf-16` alone adds the native BOM."""
    if encoding.endswith("-bom"):
        codec = encoding.removesuffix("-bom")
        bom = b"\xff\xfe" if codec.endswith("le") else b"\xfe\xff"
        return bom + text.encode(codec)
    return text.encode(encoding)


@pytest.mark.parametrize("encoding", ENCODINGS)
def test_decisions_load_whatever_the_bom(tmp_path: Path, encoding: str) -> None:
    """Accented host paths survive every encoding."""
    path = tmp_path / "decisions.json"
    path.write_bytes(encode(json.dumps(DECISIONS, ensure_ascii=False), encoding))
    assert read_decisions(path).bursts[0].discarded == (SHOT,)


def test_other_bytes_are_refused(tmp_path: Path) -> None:
    """Windows-1252 without BOM is not guessed: refused, with the reason."""
    path = tmp_path / "decisions.json"
    path.write_bytes(json.dumps(DECISIONS, ensure_ascii=False).encode("cp1252"))
    with pytest.raises(DecisionsError, match="not a valid decisions file"):
        read_decisions(path)


def test_decisions_are_written_without_bom(tmp_path: Path) -> None:
    """UTF-8, no BOM, accents as they are."""
    path = tmp_path / "decisions.json"
    path.write_bytes(encode(json.dumps(DECISIONS), "utf-16"))
    write_decisions(path, read_decisions(path))
    raw = path.read_bytes()
    assert raw.startswith(b"{")
    assert "Chloé".encode() in raw


@pytest.mark.parametrize("encoding", ENCODINGS)
def test_config_loads_whatever_the_bom(tmp_path: Path, encoding: str) -> None:
    """config.toml saved by Notepad or PowerShell."""
    path = tmp_path / "config.toml"
    path.write_bytes(encode("[folders]\nprotected = ['C:\\Photos\\Chloé']\n", encoding))
    assert read_file_layer(path) == {"folders": {"protected": ["C:\\Photos\\Chloé"]}}


def test_config_in_another_encoding_is_refused(tmp_path: Path) -> None:
    """Not UTF-8 nor UTF-16: a clear error, not a traceback."""
    path = tmp_path / "config.toml"
    path.write_bytes("[folders]\nprotected = ['Chloé']\n".encode("cp1252"))
    with pytest.raises(ConfigError, match="not valid TOML"):
        read_file_layer(path)
