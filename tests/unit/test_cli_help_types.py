"""Every `--help` names option values in plain words, never as Python types (0809)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import typer
from typer.core import TyperGroup as Group
from typer.testing import CliRunner

from media_hygiene.cli.app import build_app
from media_hygiene.cli.help_types import name_values

if TYPE_CHECKING:
    from typer._click import Command

_RAW_TYPES = ("<bool>", "list[", "<str>", "<int>", "<float>", "<path>")


def _paths(command: Command, prefix: tuple[str, ...] = ()) -> list[tuple[str, ...]]:
    """Every command path below `command`, itself included."""
    paths = [prefix]
    if isinstance(command, Group):
        for name, sub in command.commands.items():
            paths.extend(_paths(sub, (*prefix, name)))
    return paths


_ALL = _paths(typer.main.get_command(build_app()))


@pytest.mark.parametrize("path", _ALL, ids=lambda path: " ".join(path) or "root")
def test_help_shows_no_python_type(path: tuple[str, ...]) -> None:
    """No help page prints a raw type."""
    result = CliRunner().invoke(build_app(), [*path, "--help"], env={"COLUMNS": "200"})
    assert result.exit_code == 0, result.output
    assert not [raw for raw in _RAW_TYPES if raw in result.output]


def test_audit_help_names_values_and_hides_flag_types() -> None:
    """A repeatable folder option reads TEXT; a flag shows nothing before its help."""
    result = CliRunner().invoke(build_app(), ["audit", "--help"], env={"COLUMNS": "80"})
    lines = result.output.splitlines()
    assert any("--prefer" in line and "TEXT" in line for line in lines)
    help_line = next(line for line in lines if "--help" in line)
    assert help_line.split(" -h ")[1].split()[0] == "Show"


def test_a_metavar_set_by_hand_is_kept() -> None:
    """An option that names its own value keeps that name."""
    option = typer.core.TyperOption(
        param_decls=["--where"],
        type_descriptor=None,  # type: ignore[arg-type]  # never read: metavar is set
        metavar="FOLDER",
    )
    assert option in name_values([option])
    assert option.metavar == "FOLDER"
