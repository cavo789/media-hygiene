"""`media-hygiene upkeep`: the regular chores of `[routine]` in one command (0519)."""

# pylint: disable=import-outside-toplevel  # lazy: a command loads its code when it runs

from __future__ import annotations

import typer

from media_hygiene.cli.context import runtime_of


def upkeep_command(ctx: typer.Context) -> None:
    """Run the steps of `[routine]`, then say the next step.

    Args:
        ctx: Typer context holding the runtime.

    Raises:
        typer.Exit: A step failed: its code.
    """
    from media_hygiene.cli.status_next import advise_status
    from media_hygiene.services.status import read_status
    from media_hygiene.services.upkeep import run_upkeep

    runtime = runtime_of(ctx)
    code = run_upkeep(runtime)
    if code:
        raise typer.Exit(code)
    advise_status(runtime, read_status(runtime))
