"""The closing advice: ranked by kind, cut to a budget, setup merged, safety kept."""

from __future__ import annotations

import io
from typing import TYPE_CHECKING

import pytest
from rich.console import Console

from media_hygiene.cli import cmd_audit
from media_hygiene.console.advice import TIP_BUDGET, Advice, TipKind, select
from media_hygiene.console.output import Output
from media_hygiene.paths.mount_kind import MountKind
from tests.support.runtime import make_locations, make_runtime, output_of

if TYPE_CHECKING:
    from pathlib import Path

_SAFETY = Advice(TipKind.SAFETY, "undo")
_NEXT = Advice(TipKind.NEXT, "review")
_FIND = Advice(TipKind.DISCOVERY, "crosscheck")
_PREFER = Advice(TipKind.DISCOVERY, "prefer")


def _output(*, verbose: bool = False) -> tuple[Output, io.StringIO]:
    """An output writing to memory.

    Args:
        verbose: Keep every tip.

    Returns:
        The output and its buffer.
    """
    buffer = io.StringIO()
    return Output(Console(file=buffer, width=200), verbose=verbose), buffer


def test_tips_are_ranked_by_kind_and_cut_to_the_budget() -> None:
    """Discovery comes after the next step and setup; the rest is counted."""
    setup = Advice(TipKind.SETUP, "set")
    selection = select((_FIND, _PREFER, _NEXT), setup, verbose=False)
    assert selection.shown == (_NEXT, setup)
    assert selection.hidden == 2
    assert len(selection.shown) == TIP_BUDGET


def test_a_tip_that_changes_clean_comes_before_the_setup_line() -> None:
    """`--prefer` (ranked NEXT by audit) is not hidden by the ⚙️ line."""
    prefer = Advice(TipKind.NEXT, "prefer")
    setup = Advice(TipKind.SETUP, "set")
    selection = select((_FIND, prefer), setup, verbose=False)
    assert selection.shown == (prefer, setup)


def test_safety_lines_are_never_cut() -> None:
    """However many tips, the undo line stays, apart from the budget."""
    selection = select((_FIND, _SAFETY, _PREFER, _NEXT), None, verbose=False)
    assert selection.safety == (_SAFETY,)
    assert selection.shown == (_NEXT, _FIND)
    assert selection.hidden == 1


def test_verbose_keeps_every_tip() -> None:
    """--verbosity verbose shows all of them, in order of importance."""
    selection = select((_FIND, _PREFER, _NEXT), None, verbose=True)
    assert selection.shown == (_NEXT, _FIND, _PREFER)
    assert selection.hidden == 0


def test_finish_prints_the_step_then_the_best_tips() -> None:
    """Safety, 👉 with its command, two tips, the setup merged, a hidden count."""
    output, buffer = _output()
    output.advise(_FIND)
    output.advise(_FIND)  # said once
    output.advise(_PREFER)
    output.advise(Advice(TipKind.SAFETY, "Undo it:", "docker run undo"))
    output.setting("-v cache:/cache")
    output.setting("-e TZ=Europe/Brussels")
    output.next_step("run clean:", "docker run clean")
    output.finish()
    lines = buffer.getvalue().splitlines()
    assert lines[:4] == [
        "💡 Undo it:",
        "docker run undo",
        "👉 What next: run clean:",
        "docker run clean",
    ]
    assert lines[4] == "⚙️  To set once: -v cache:/cache; -e TZ=Europe/Brussels."
    assert lines[5] == "💡 crosscheck"
    assert "1 more tip" in lines[6]
    output.finish()  # drained: nothing printed twice
    assert buffer.getvalue().count("What next") == 1


def test_finish_without_advice_prints_a_blank_line_only() -> None:
    """A command with nothing to suggest ends with the empty line alone."""
    output, buffer = _output(verbose=True)
    output.finish()
    assert buffer.getvalue() == "\n"


_NO_CONFIG = ((MountKind.CACHE, MountKind.CONFIG), "-e TZ=Europe/Brussels")
_CONFIG = ((MountKind.CACHE,), 'timezone = "Europe/Brussels" in section [general]')


@pytest.mark.parametrize("case", [_NO_CONFIG, _CONFIG])
def test_the_settings_to_add_once_share_one_line(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case: tuple[tuple[MountKind, ...], str],
) -> None:
    """No cache, no time zone: one ⚙️ line names both, config.toml when mounted."""
    missing, said = case
    monkeypatch.setattr("media_hygiene.config.zone.timezone_unknown", lambda: True)
    runtime = make_runtime(make_locations(tmp_path, *missing))
    cmd_audit._setup_tips(runtime)  # noqa: SLF001  # pylint: disable=protected-access
    runtime.output.finish()
    line = " ".join(output_of(runtime).split())
    assert line.startswith("⚙️ To set once: -v media-hygiene-cache:/cache")
    assert said in line
