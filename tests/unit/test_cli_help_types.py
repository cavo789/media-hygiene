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
    """A repeatable folder option reads FOLDER; a flag shows nothing before its help."""
    result = CliRunner().invoke(build_app(), ["audit", "--help"], env={"COLUMNS": "80"})
    lines = result.output.splitlines()
    assert any("--prefer" in line and "FOLDER" in line for line in lines)
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


def _options(command: Command) -> list[tuple[str, typer.core.TyperOption]]:
    """Every option of every command below `command`, with its command path."""
    found: list[tuple[str, typer.core.TyperOption]] = []
    for path in _paths(command):
        node = command
        for name in path:
            node = node.commands[name]  # type: ignore[attr-defined]
        found.extend(
            (" ".join(path), param)
            for param in name_values(list(node.params))
            if isinstance(param, typer.core.TyperOption)
        )
    return found


def test_every_option_taking_a_value_names_it_with_its_own_word() -> None:
    """`--prefer FOLDER`, `--port PORT`: none falls back to the generic word (0818)."""
    generic = {"TEXT", "NUMBER", "PATH"}
    options = _options(typer.main.get_command(build_app()))
    taking = [(c, o) for c, o in options if not o.is_flag and o.name != "help"]
    assert taking
    bare = [
        f"{command} {option.opts[0]}"
        for command, option in taking
        if option.metavar in generic
    ]
    assert not bare, f"options with no word of their own (cli/metavars.py): {bare}"


def test_audit_help_names_a_folder_a_folder() -> None:
    """The folders of `audit` read FOLDER; the port of a page reads PORT."""
    result = CliRunner().invoke(
        build_app(), ["audit", "--help"], env={"COLUMNS": "100"}
    )
    lines = result.output.splitlines()
    for option in ("--prefer", "--protect", "--exclude "):
        assert any(option in line and "FOLDER" in line for line in lines)
    people = CliRunner().invoke(
        build_app(), ["people", "--help"], env={"COLUMNS": "100"}
    )
    assert any(
        "--port" in line and "PORT" in line for line in people.output.splitlines()
    )
