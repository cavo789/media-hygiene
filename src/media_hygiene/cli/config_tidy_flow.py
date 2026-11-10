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
from media_hygiene.services.events_move import events_to_move, move_events

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.config.tidy_rules import OptIn, StaleEntry
    from media_hygiene.services.runtime import Runtime


def show_tidy(runtime: Runtime, *, apply: bool, opt_in: frozenset[OptIn]) -> None:
    """List what points at nothing; with `apply`, remove the ticked entries.

    Args:
        runtime: Settings, mount points and output.
        apply: Remove the ticked entries (a copy kept first).
        opt_in: The entries shown unticked to tick too (`--dates`, `--superseded`).
    """
    output = runtime.output
    _move_events(runtime, apply=apply)
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
    chosen = [e for e in findings.stale if e.ticked or e.opt_in in opt_in]
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


def _move_events(runtime: Runtime, *, apply: bool) -> None:
    """The events the tool wrote in `config.toml`: listed, moved to `events/` (0576).

    Args:
        runtime: Settings, mount points and output.
        apply: Move them (a copy of `config.toml` kept first).
    """
    output = runtime.output
    rules = events_to_move(runtime.locations.config_file)
    if not rules:
        return
    if not apply:
        output.info(
            ngettext(
                "{count} event of config.toml moves to the events folder with --apply.",
                "{count} events of config.toml move to the events folder with --apply.",
                len(rules),
            ).format(count=human_number(len(rules)))
        )
        return
    with user_errors(output):
        backup = move_events(runtime, rules)
    output.success(
        ngettext(
            "{count} event moved to the events folder, read back from the disk.",
            "{count} events moved to the events folder, read back from the disk.",
            len(rules),
        ).format(count=human_number(len(rules)))
    )
    shown = on_host(runtime, backup) or str(backup)
    output.tip(_("Copy kept: {backup}.").format(backup=escape(shown)))


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
