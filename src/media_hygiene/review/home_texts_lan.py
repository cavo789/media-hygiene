"""The texts of the home network switches on the home page (0605)."""

from __future__ import annotations

from media_hygiene.i18n import _


def lan_switch_texts() -> dict[str, str]:
    """The texts of the two switches, each with the consequence of its state.

    Returns:
        By key, in the language in use.
    """
    return {
        "lanSwitchTitle": _("Phones on the home Wi-Fi"),
        "lanSwitchOn": _("Open this page to phones"),
        "lanSwitchOnYes": _(
            "On: a phone on the same Wi-Fi can open this page after typing a code. "
            "Never the internet."
        ),
        "lanSwitchOnNo": _("Off: this page stays on this PC only."),
        "lanSwitchOriginals": _("Phones may download the originals"),
        "lanSwitchOriginalsYes": _(
            "On: a paired phone downloads photos and videos at full size, GPS "
            "position included. It never changes anything."
        ),
        "lanSwitchOriginalsNo": _(
            "Off: a paired phone sees the previews only, never the originals."
        ),
        "lanSwitchFailed": _("The settings could not be saved in config.toml."),
        "lanSwitchSaved": _("Saved in config.toml, read back from the disk."),
    }


def lan_pairing_texts() -> dict[str, str]:
    """The texts of the pairing's report on the PC's card (0681).

    Returns:
        By key, in the language in use.
    """
    return {
        "lanAttempt": _("⚠ {count} wrong codes from {address} at {time}"),
        "lanClosed": _(
            "Too many wrong codes: pairing is closed, the phones already paired "
            "stay paired."
        ),
        "lanReopen": _("Open pairing again"),
        "lanReopened": _("New code: the previous one opens nothing any more."),
        "lanSeen": _("It was me"),
        "lanNewTitle": _("Paired during this run"),
        "lanNewPaired": _("A new device is paired: {name} at {time}."),
    }
