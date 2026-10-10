"""A bare `--decisions` names decisions.json: `clean --decisions` is enough."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from media_hygiene.__main__ import main
from media_hygiene.cli.bare_options import with_default_decisions
from media_hygiene.review.place import decisions_flag

if TYPE_CHECKING:
    from collections.abc import Sequence


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        (["clean", "--decisions"], ["clean", "--decisions", "decisions.json"]),
        (
            ["clean", "--decisions", "--yes"],
            ["clean", "--decisions", "decisions.json", "--yes"],
        ),
        (
            ["clean", "--decisions", "other.json"],
            ["clean", "--decisions", "other.json"],
        ),
        (["clean", "--decisions=other.json"], ["clean", "--decisions=other.json"]),
        (["clean", "--yes"], ["clean", "--yes"]),
    ],
)
def test_a_bare_decisions_gets_the_default_file(
    given: Sequence[str], expected: list[str]
) -> None:
    """Last, or followed by another option: decisions.json; else left alone."""
    assert with_default_decisions(given) == expected


def test_the_option_is_written_as_short_as_possible() -> None:
    """The default file needs no name; another one does."""
    assert decisions_flag("decisions.json") == "--decisions"
    assert decisions_flag("other.json") == "--decisions other.json"


def test_the_entry_point_completes_the_command_line(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`clean --decisions --help` parses: the bare option got its file."""
    monkeypatch.setattr(
        sys, "argv", ["media-hygiene", "clean", "--decisions", "--help"]
    )
    with pytest.raises(SystemExit) as stopped:
        main()
    assert stopped.value.code == 0
    assert "--decisions" in capsys.readouterr().out
