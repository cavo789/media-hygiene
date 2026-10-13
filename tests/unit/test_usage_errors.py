"""Command-line mistakes in French too: the frame and Click's own messages."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import pytest
from typer.testing import CliRunner

from media_hygiene.cli.app import build_app
from media_hygiene.constants import ExitCode, Locale
from media_hygiene.i18n import using

if TYPE_CHECKING:
    from collections.abc import Iterator

_ENGLISH: Final = (
    "Error",
    "Try ",
    "for help",
    "No such",
    "Missing",
    "Invalid value",
    "Got unexpected",
    "requires",
    "Possible options",
    "Did you mean",
    "Usage:",
    "is not",
)
_MISTAKES: Final = (
    ["classify", "--nope"],
    ["--nope"],
    ["classsify"],
    ["audit", "--ext"],
    ["classify", "--year", "2015", "extra"],
    ["review", "--port", "abc"],
    ["review", "--port", "0"],
    ["--color", "maybe", "audit"],
    ["audit", "--prefe", "x"],
)


@pytest.fixture(autouse=True)
def _english_frame_after() -> Iterator[None]:
    """The French frame of an error does not leak into the other tests."""
    yield
    with using(Locale.EN):
        build_app()


@pytest.mark.parametrize("args", _MISTAKES)
def test_a_mistake_reads_in_french(args: list[str]) -> None:
    """Under `--locale fr`, no English word of Click or Typer is left.

    Args:
        args: The command line typed.
    """
    with using(Locale.FR):
        result = CliRunner().invoke(build_app(), args)
    assert result.exit_code == ExitCode.USAGE
    assert "Erreur" in result.output
    found = [word for word in _ENGLISH if word in result.output]
    assert not found, result.output


def test_english_stays_english() -> None:
    """The same mistake under English: Click's words, unchanged."""
    with using(Locale.EN):
        result = CliRunner().invoke(build_app(), ["classify", "--nope"])
    assert "No such option: --nope" in result.output
    assert "Error" in result.output
