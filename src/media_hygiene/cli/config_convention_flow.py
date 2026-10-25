"""The console side of `config --convention`: old → new, a question, then the proof."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.markup import escape

from media_hygiene.cli.context import user_errors
from media_hygiene.errors import ConfigError
from media_hygiene.i18n import _, ngettext
from media_hygiene.services.config_convention import layout_changes, write_convention

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.services.config_convention import LayoutChange
    from media_hygiene.services.runtime import Runtime


def show_convention(runtime: Runtime, *, dry_run: bool) -> None:
    """List the layouts to change, ask, write them and say what the file now holds.

    Args:
        runtime: Settings, mount points and output.
        dry_run: List only, write nothing.
    """
    output, config_file = runtime.output, runtime.locations.config_file
    host = escape(runtime.mapper.to_host(config_file))
    with user_errors(output):
        changes = _guarded(lambda: layout_changes(config_file))
    if not changes:
        output.success(
            _("The layouts of {path} follow the sort convention.").format(path=host)
        )
        return
    output.info(
        _(
            "The layouts of {path} that differ from the sort convention "
            "(year/year-month/event):"
        ).format(path=host)
    )
    for change in changes:
        output.info(f"  {_line(change)}")
    if dry_run:
        output.info(_("Nothing written (--dry-run)."))
        return
    if not output.confirm(_("Write these layouts into {path}?").format(path=host)):
        output.info(_("Nothing written: your layouts stay as they are."))
        return
    with user_errors(output):
        written = _guarded(lambda: write_convention(config_file))
    output.success(
        ngettext(
            "{count} layout written to {path}, read back from the disk:",
            "{count} layouts written to {path}, read back from the disk:",
            len(written),
        ).format(count=len(written), path=host)
    )
    for change in written:
        output.info(f"  {escape(change.key)} = {escape(repr(change.new))}")


def _line(change: LayoutChange) -> str:
    """One layout, old → new.

    Args:
        change: The change.

    Returns:
        The line, an empty layout said in words.
    """
    new = change.new or _("(empty: the files stay where they are until you decide)")
    return f"{escape(change.key)}: {escape(repr(change.old))} → {escape(new)}"


def _guarded[T](action: Callable[[], T]) -> T:
    """Run a read or a write of `config.toml`, its failure said in one line.

    Args:
        action: The read or the write.

    Returns:
        What it returns.

    Raises:
        ConfigError: The file cannot be read, parsed or written.
    """
    try:
        return action()
    except (OSError, ValueError, TypeError) as exc:
        message = _("config.toml could not be updated: {reason}").format(reason=exc)
        raise ConfigError(message) from exc
