"""The home page's confirmation of *Forget every face and every name* (0795).

It is read from `config.toml` each time the page asks for its state: the dialog
states how many names go and lists them, so nothing it deletes is hidden. Without a
name, nor a face ignored, the action is not offered.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from media_hygiene.cli.menu_catalog_settings import FORGET_NAMES
from media_hygiene.i18n import _, ngettext
from media_hygiene.people.config_file import read_people

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.cli.menu_steps import Menu


def with_forget_names(menu: Menu, config: Path) -> Menu:
    """Give *Forget every face and every name* its confirmation, or its reason.

    Args:
        menu: The menu as the page shows it.
        config: `config.toml`.

    Returns:
        The same menu, that step's confirmation stating what the file holds now.
    """
    try:
        written = read_people(config) if config.is_file() else None
    except OSError, ValueError:
        written = None  # a broken file: `config` says why; nothing offered here
    names = sorted(person.name for person in written.person) if written else []
    ignored = len(written.ignored) if written else 0
    steps = []
    for line in menu.steps:
        if line.step.name != FORGET_NAMES:
            steps.append(line)
        elif not names and not ignored:
            steps.append(replace(line, reason=_("config.toml names nobody.")))
        else:
            confirm = (_title(len(names)), _text(names, ignored))
            steps.append(replace(line, step=replace(line.step, confirm=confirm)))
    return replace(menu, steps=tuple(steps))


def _title(count: int) -> str:
    """The dialog's title, stating the count.

    Args:
        count: The names.

    Returns:
        E.g. "Forget 3 names, for good?".
    """
    return ngettext(
        "Forget {count} name, for good?", "Forget {count} names, for good?", count
    ).format(count=count)


def _text(names: list[str], ignored: int) -> str:
    """What goes: every name, the faces ignored, and where the old file stays.

    Args:
        names: The names, sorted.
        ignored: The faces ignored.

    Returns:
        The dialog's text.
    """
    return _(
        "Every face of the cache, these names ({names}) and {ignored} faces "
        "ignored are deleted from config.toml. The previous file is kept in "
        "/config/.history/; your photos do not change."
    ).format(names=", ".join(names) or "-", ignored=ignored)
