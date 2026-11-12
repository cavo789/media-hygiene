"""The texts of the home network switches on the home page (0605)."""

from __future__ import annotations

from media_hygiene.i18n import _
from media_hygiene.review.lan_activity import ACTIVITY_DAYS
from media_hygiene.review.lan_phone_care import EXPIRY_DAYS


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
        "lanRefused": _(
            "⛔ {count} connections refused from {address} at {time}: too many at "
            "once from that device."
        ),
        "lanClosed": _(
            "Too many wrong codes: pairing is closed, the phones already paired "
            "stay paired."
        ),
        "lanReopen": _("Open pairing again"),
        "lanReopened": _("New code: the previous one opens nothing any more."),
        "lanSeen": _("It was me"),
        "lanNewTitle": _("Paired during this run"),
        "lanNewPaired": _("A new device is paired: {name} at {time}."),
        **lan_device_texts(),
    }


def lan_device_texts() -> dict[str, str]:
    """The texts of the devices paired for good on the PC's card (0683).

    Returns:
        By key, in the language in use.
    """
    return {
        "lanRename": _("Rename"),
        "lanRenamed": _("Name saved, read back from the disk."),
        "lanDevice": _("Paired on {paired} · last seen {seen} · {address}"),
        "lanNeverSeen": _("not yet"),
        "lanTv": _("TV"),
        "lanGuest": _("Guest until {until}: the albums chosen for guests only"),
        "lanActivity": _(
            "Last {days} days: {pages} pages opened, {pictures} pictures viewed "
            "(last on {day})"
        ).replace("{days}", str(ACTIVITY_DAYS)),
        "lanNoActivity": _("Last {days} days: nothing opened").format(
            days=ACTIVITY_DAYS
        ),
        "lanExpired": _(
            "Forgotten at this start, unseen for {days} days: {names}"
        ).replace("{days}", str(EXPIRY_DAYS)),
        "lanForgetAll": _("Forget every device"),
        # 0684: which code the card shows, family or guests
        "lanFamilyCode": _("👪 Family: the whole library"),
        "lanGuestCode": _("🧳 Guest: the albums ticked Show to guests, nothing else"),
        "lanGuestUntil": _(  # 0709
            "🌙 A guest sees them until midnight tonight; tomorrow it types the "
            "guests' code again."
        ),
        "lanForgetSure": _(
            "Forget all {count} devices? Each one must type a code again to open "
            "this page."
        ),
        "lanForgetYes": _("Yes, forget them all"),
        "lanForgotAll": _("Every device is forgotten, read back from the disk."),
    }
