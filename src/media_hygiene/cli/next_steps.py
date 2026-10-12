"""Close a command with the full command of the next one, ready to paste."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.console.advice import Advice, TipKind
from media_hygiene.services.next_command import NextVerb, next_command

if TYPE_CHECKING:
    import typer

    from media_hygiene.services.runtime import Runtime

# Options shared by audit, crosscheck and clean: the next one sees the same files.
_FOLDER_OPTIONS: Final = ("prefer", "protect", "exclude", "ext", "exclude_name")


def suggest(runtime: Runtime, text: str, verb: NextVerb) -> None:
    """Set the next step: what to do, then its full `docker run`.

    Args:
        runtime: Settings, mount points and output.
        text: Translated step, starting in lower case after the label.
        verb: The command that comes next.
    """
    command = next_command(runtime, verb)
    note = command.note()
    runtime.output.next_step(f"{text} {note}" if note else text, command.command)


def safety(runtime: Runtime, text: str, verb: NextVerb) -> None:
    """Add a safety line (how to undo), never cut, with its full `docker run`.

    Args:
        runtime: Settings, mount points and output.
        text: Translated line.
        verb: The command that undoes.
    """
    command = next_command(runtime, verb).command
    runtime.output.advise(Advice(TipKind.SAFETY, text, command))


def carried(runtime: Runtime, verb: str, ctx: typer.Context | None = None) -> str:
    r"""Write `verb` with the global options and, given `ctx`, the folder options.

    Args:
        runtime: Settings, mount points and output; its command-line layer holds the
            global options (`--locale`, `--verbosity`, `--color`).
        verb: The next command, e.g. `clean`.
        ctx: Typer context of the running command, whose folder options (`--prefer`,
            `--ext`…) the next command takes too; None for a command that does not.

    Returns:
        E.g. `--locale fr clean --prefer "C:\Photos\Best"`.
    """
    general = runtime.cli_layer.get("general", {})
    globals_ = [f"--{name} {value}" for name, value in general.items()]
    params = ctx.params if ctx is not None else {}
    options = [
        f'--{name.replace("_", "-")} "{value}"'
        for name in _FOLDER_OPTIONS
        for value in params.get(name) or ()
    ]
    return " ".join((*globals_, verb, *options))
