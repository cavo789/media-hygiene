"""The `mh` menu on screen: the three guides, every command, the proposed one first."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from rich.markup import escape
from rich.table import Table

from media_hygiene.cli.menu_catalog import Risk
from media_hygiene.cli.menu_steps import Section
from media_hygiene.constants import DOC_PAGES
from media_hygiene.i18n import _
from media_hygiene.services.next_command import LAUNCHER_FUNCTION

if TYPE_CHECKING:
    from media_hygiene.cli.menu_steps import Menu, MenuStep
    from media_hygiene.services.runtime import Runtime

_DONE: Final = "✅"
_PROPOSED: Final = "👉"
_AI: Final = "🤖"
_DIM: Final = "dim"
_NO_MARK: Final = "  "  # as wide as an emoji


def section_titles() -> dict[Section, str]:
    """The title of each section, as the guides name them.

    Returns:
        Translated titles.
    """
    return {
        Section.CLEAN: _("Clean the duplicates"),
        Section.SORT: _("Sort the photos"),
        Section.FIND: _("Find a photo"),
        Section.SETUP: _("Reach mh without typing (Windows)"),
    }


def show_menu(runtime: Runtime, menu: Menu) -> None:
    """Print every step, then what Enter and a number do.

    While a clean step is proposed, the other guides are dimmed: they come after.

    Args:
        runtime: Settings, mount points and output (on stderr).
        menu: The menu.
    """
    table = Table.grid(padding=(0, 1))
    table.add_column(no_wrap=True)
    table.add_column(no_wrap=True)
    table.add_column()
    table.add_column(no_wrap=True)
    proposed = menu.proposed
    titles = section_titles()
    section: Section | None = None
    for line in menu.steps:
        if line.section is not section:
            section = line.section
            table.add_row("", f"[bold]{titles[section]}[/]")
        dim = proposed is not None and proposed.section is not section
        table.add_row(*_cells(runtime, line), style=_DIM if dim else None)
    runtime.output.show(table)
    runtime.output.blank()
    _footer(runtime, menu)


def _cells(runtime: Runtime, line: MenuStep) -> tuple[str, ...]:
    """The cells of one step: mark, number, command, what it does, badges.

    Args:
        runtime: Settings: whether a local model is set.
        line: The step.

    Returns:
        Four cells, Rich markup escaped where the text comes from the user.
    """
    mark = _PROPOSED if line.proposed else _DONE if line.done else _NO_MARK
    number = str(line.number) if line.number else ""
    shown = line.command or line.step.typed or line.step.command
    command = escape(f"{LAUNCHER_FUNCTION} {shown}")
    text = escape(line.step.text)
    if line.step.typed:
        text += f" [italic]{_('(type it yourself)')}[/]"
    elif not line.command:
        text += f" [italic]{_('(nothing to do yet)')}[/]"
    badges = [line.step.risk.value]
    if line.step.ai and runtime.settings.classify.ai.model:
        badges.append(_AI)
    if line.step.optional:
        badges.append(f"[italic]{_('optional')}[/]")
    return f"{mark} {number:>2}", command, text, " ".join(badges)


def _footer(runtime: Runtime, menu: Menu) -> None:
    """Say what a local model would add, how to type a step, then how to choose.

    Args:
        runtime: Settings, mount points and output.
        menu: The menu.
    """
    output = runtime.output
    output.info(
        _(
            "{safe} your photos are not touched · {undo} can be undone · "
            "{final} for good"
        ).format(safe=Risk.SAFE.value, undo=Risk.UNDO.value, final=Risk.FINAL.value)
    )
    if not runtime.settings.classify.ai.model:
        output.info(
            escape(
                _(
                    "🤖 classify and tags can also ask a local AI model: set "
                    "[classify.ai] model in config.toml (mh config)."
                )
            )
        )
    if any(line.step.typed for line in menu.steps):
        output.info(
            _("A step to type yourself takes words only you know: {url}").format(
                url=f"{DOC_PAGES}/{_('sort/quick-guide/')}"
            )
        )
    # Not steps of a guide: `mh` runs them itself (0176, 0177).
    output.info(
        _("Your folders: {folders}. A new version: {update}.").format(
            folders=f"{LAUNCHER_FUNCTION} folders", update=f"{LAUNCHER_FUNCTION} update"
        )
    )
    proposed = menu.proposed
    if proposed is None:
        output.success(
            _("Nothing left to do: everything is applied. A number runs that step.")
        )
        return
    output.info(
        _(
            "Enter runs step {number} ({command}). Another number runs that step. "
            "Ctrl+C leaves."
        ).format(
            number=proposed.number,
            command=f"{LAUNCHER_FUNCTION} {proposed.command}",
        )
    )
