"""The console side of `config tidy`: list the stale entries, remove the ticked ones."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.markup import escape
from rich.table import Table

from media_hygiene.cli.config_mounts import on_host
from media_hygiene.cli.context import user_errors
from media_hygiene.console.formatting import human_number
from media_hygiene.i18n import _, ngettext
from media_hygiene.services.config_tidy import stale_entries, tidy

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.config.tidy_find import StaleEntry
    from media_hygiene.services.runtime import Runtime


def show_tidy(runtime: Runtime, *, apply: bool, dates: bool) -> None:
    """List what points at nothing; with `apply`, remove the ticked entries.

    Args:
        runtime: Settings, mount points and output.
        apply: Remove the ticked entries (a copy kept first).
        dates: Tick the `date_range` rules with no photo too.
    """
    output = runtime.output
    findings = stale_entries(runtime)
    for folder in findings.unknown:
        output.info(
            _("Not judged, its drive is not mounted: {folder}").format(
                folder=escape(folder)
            )
        )
    if not findings.stale:
        output.success(_("Every entry of config.toml points at something."))
        return
    chosen = [entry for entry in findings.stale if entry.ticked or dates]
    output.show(_table(findings.stale, chosen))
    if not apply:
        output.info(_("🔒 Nothing was written."))
        output.next_step(
            _("Remove the ticked entries (a copy is kept first):"),
            "mh config tidy --apply",
        )
        return
    if not chosen:
        output.info(_("No entry is ticked: nothing was written."))
        return
    with user_errors(output):
        done = tidy(runtime, chosen)
    output.success(
        ngettext(
            "{count} entry removed from config.toml, read back from the disk.",
            "{count} entries removed from config.toml, read back from the disk.",
            len(done.removed),
        ).format(count=human_number(len(done.removed)))
    )
    backup = on_host(runtime, done.backup) or str(done.backup)
    config = on_host(runtime, runtime.locations.config_file) or "config.toml"
    output.tip(
        _("Changed your mind? Copy {backup} over {config}.").format(
            backup=escape(backup), config=escape(config)
        )
    )


def _table(stale: Sequence[StaleEntry], chosen: Sequence[StaleEntry]) -> Table:
    """The stale entries, the ticked ones marked.

    Args:
        stale: Every stale entry.
        chosen: Those removed by `--apply`.

    Returns:
        The table.
    """
    table = Table(title=_("Entries pointing at nothing"), title_justify="left")
    for header in ("", _("Where"), _("Entry"), _("Why")):
        table.add_column(header, overflow="fold")
    for entry in stale:
        tick = "☑" if entry in chosen else "☐"
        where = f"{entry.section} #{entry.rank + 1}"
        table.add_row(tick, where, escape(entry.label), escape(entry.reason))
    return table


def tidy_tip(runtime: Runtime) -> None:
    """After `sort`: one line when entries of `config.toml` point at nothing.

    Args:
        runtime: Settings, mount points and output.
    """
    try:
        stale = stale_entries(runtime).stale
    except ValueError, OSError:
        return  # an unreadable file is said by the commands that read it
    count = len([entry for entry in stale if entry.ticked])
    if count:
        runtime.output.tip(
            ngettext(
                "{count} entry of config.toml points at nothing: mh config tidy",
                "{count} entries of config.toml point at nothing: mh config tidy",
                count,
            ).format(count=human_number(count))
        )
