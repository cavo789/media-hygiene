"""EXIF text is cleaned once, where it is read: no padding, no control characters."""

from __future__ import annotations

from media_hygiene.scan.exif_values import text


def test_text_ends_at_its_first_nul() -> None:
    """What follows the NUL is leftover bytes some cameras keep (an old Samsung)."""
    assert text(b"SAMSUNG\x00prrotaoin") == "SAMSUNG"
    assert text("\x00\x00 DIGIMAX 350SE\x00\x00") == "DIGIMAX 350SE"


def test_text_drops_control_characters_and_keeps_line_breaks() -> None:
    """Excel refuses control characters; a description may span lines."""
    assert text("Canon\x07 EOS") == "Canon EOS"
    assert text("Day one\nby the sea") == "Day one\nby the sea"


def test_empty_text_is_none() -> None:
    """Padding only, or no text at all."""
    assert text(b"\x00\x00   ") is None
    assert text(42) is None
