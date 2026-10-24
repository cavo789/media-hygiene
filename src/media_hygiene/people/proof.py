"""The line the people page shows after a change: what `config.toml` holds now."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.i18n import _, ngettext

if TYPE_CHECKING:
    from media_hygiene.config.people_settings import PeopleSettings
    from media_hygiene.people.changes import Naming
    from media_hygiene.people.roster import Change


def proof_line(back: PeopleSettings, change: Change) -> str:
    """Say what `config.toml` holds now for the change.

    Args:
        back: `[people]` read back from the disk.
        change: The change.

    Returns:
        One line.
    """
    if change.action == "ignore":
        count = len(back.ignored)
        return ngettext(
            "Saved in config.toml, read back: {count} face ignored.",
            "Saved in config.toml, read back: {count} faces ignored.",
            count,
        ).format(count=count)
    folded = change.naming.name.strip().casefold()
    person = next((p for p in back.person if p.name.casefold() == folded), None)
    if person is None:
        return _("Saved in config.toml, read back: nobody is named {name}.").format(
            name=change.naming.name
        )
    return ngettext(
        "Saved in config.toml, read back: {name}, {count} confirmed face.",
        "Saved in config.toml, read back: {name}, {count} confirmed faces.",
        len(person.faces),
    ).format(name=person.name, count=len(person.faces))


def rejected_line(back: PeopleSettings, naming: Naming, *, again: bool) -> str:
    """Say what `config.toml` holds now for the faces of one photo and one name.

    Args:
        back: `[people]` read back from the disk.
        naming: The name, and the faces of the photo.
        again: True after *Put back*, False after a name was taken off.

    Returns:
        One line, from what the file holds, not from what was asked.
    """
    folded = naming.name.strip().casefold()
    person = next((p for p in back.person if p.name.casefold() == folded), None)
    if person is None:
        return _("Saved in config.toml, read back: nobody is named {name}.").format(
            name=naming.name
        )
    count = sum(key in person.rejected for key in naming.faces)
    if again:
        if count:
            return _("Not saved: config.toml still says this is not {name}.").format(
                name=person.name
            )
        return _(
            "Saved in config.toml, read back: {name} is on this photo again."
        ).format(name=person.name)
    return ngettext(
        "Saved in config.toml, read back: {count} face of this photo is not {name}.",
        "Saved in config.toml, read back: {count} faces of this photo are not {name}.",
        count,
    ).format(name=person.name, count=count)


def followed_line(before: PeopleSettings, after: PeopleSettings) -> str:
    """Say how many face ids followed photos moved since they were written (0146).

    Args:
        before: `[people]` as the file held it.
        after: The same, the ids of moved photos followed.

    Returns:
        A sentence to append, starting with a space; empty when nothing moved.
    """
    old = {*_ids(before)}
    count = sum(key not in old for key in _ids(after))
    if not count:
        return ""
    return " " + ngettext(
        "{count} face follows a photo that sort moved: config.toml updated.",
        "{count} faces follow photos that sort moved: config.toml updated.",
        count,
    ).format(count=count)


def _ids(settings: PeopleSettings) -> list[str]:
    """Every face id the settings hold.

    Args:
        settings: `[people]`.

    Returns:
        The ids: confirmed, rejected, ignored.
    """
    return [
        *(key for person in settings.person for key in person.faces),
        *(key for person in settings.person for key in person.rejected),
        *settings.ignored,
    ]
