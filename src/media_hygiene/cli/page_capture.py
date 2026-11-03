"""Run a read-only console step for a page, its output recorded as text (0567).

`status`, `reports`, `inventory` and `config` started from the home page used to print
in the terminal only. The home server now runs the very same command function, its
runtime's output a recording console, and shows what it printed in the page: one
source for both, and the console output is unchanged when the command is typed.
"""

from __future__ import annotations

import dataclasses
import importlib
import io
from typing import TYPE_CHECKING, Final

import typer
from rich.console import Console

from media_hygiene.cli.safety import PAGE_CAPTURED
from media_hygiene.console.output import Output

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime

# Loaded when a step runs: every command imports the home server's modules.
_FUNCTIONS: Final = "media_hygiene.cli.command_functions"
_WIDTH: Final = 100


def captured_step(runtime: Runtime, name: str) -> str:
    """Run a step as typed without options, and return what it printed.

    Args:
        runtime: Settings, mount points and output (its output is replaced).
        name: One of `PAGE_CAPTURED`.

    Returns:
        The plain text the console would have shown.

    Raises:
        KeyError: The step is not one a page shows.
    """
    if name not in PAGE_CAPTURED:
        raise KeyError(name)
    console = Console(
        file=io.StringIO(), record=True, width=_WIDTH, no_color=True, highlight=False
    )
    recorded = dataclasses.replace(runtime, output=Output(console))
    single = typer.Typer(add_completion=False)
    functions = importlib.import_module(_FUNCTIONS).command_functions()
    single.command(name=name)(functions[name])
    command = typer.main.get_command(single)
    command.main(args=[], prog_name=name, obj=recorded, standalone_mode=False)
    return console.export_text()
