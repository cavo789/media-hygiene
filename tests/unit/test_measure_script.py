"""`tests/measure/mh-measure.ps1` stays ASCII only (0366, 0098).

An accented byte breaks Windows PowerShell 5.1's console code page: its French questions
are written without accents, or with `[char]`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

SCRIPT: Final = Path(__file__).parents[1] / "measure" / "mh-measure.ps1"


def test_measure_script_is_ascii_only() -> None:
    """No byte outside ASCII, and no step asks to time a page by hand."""
    data = SCRIPT.read_bytes()
    strays = [line for line in data.splitlines() if not line.isascii()]
    assert strays == []
    assert b"ClickTimed" not in data


def test_step_36_asks_its_three_questions_in_french() -> None:
    """Step 36: three yes/no questions, in French; its results in English."""
    text = SCRIPT.read_text("ascii")
    for asked in ("36a. La page", "36b. Cliquez", "36c. Cliquez Quitter"):
        assert asked in text
    assert "(o/n)" in text
    assert 'Log "   36c. Quit, then mh again' in text


def test_every_question_is_in_french_and_o_is_a_yes() -> None:
    """No English yes/no hint is left in a prompt (0422); the code accepts `o` too."""
    text = SCRIPT.read_text("ascii")
    assert "(y/n" not in text
    assert "(y /" not in text
    assert "-eq 'y'" not in text
    assert "-match '^y'" not in text
