"""Yes/no questions show the answers they expect."""

from __future__ import annotations

import io
from typing import override

import pytest
from rich.console import Console

from media_hygiene.console.output import Output


class _Terminal(io.StringIO):
    """A standard input that claims to be a terminal."""

    @override
    def isatty(self) -> bool:
        """Pretend to be interactive, as with `docker run -it`."""
        return True


@pytest.mark.parametrize(("answer", "accepted"), [("y", True), ("", False)])
def test_the_question_shows_its_answers(
    monkeypatch: pytest.MonkeyPatch,
    answer: str,
    accepted: bool,  # noqa: FBT001
) -> None:
    """`[y/N]` is printed, not swallowed as a Rich style tag; only yes accepts."""
    monkeypatch.setattr("sys.stdin", _Terminal())
    monkeypatch.setattr("builtins.input", lambda: answer)
    buffer = io.StringIO()
    assert Output(Console(file=buffer, width=100)).confirm("Delete?") is accepted
    assert "❓ Delete? [y/N]" in buffer.getvalue()
