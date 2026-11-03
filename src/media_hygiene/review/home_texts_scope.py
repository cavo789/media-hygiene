"""The texts of what the audit analyses and ignores, on the home page (0535)."""

from __future__ import annotations

from media_hygiene.i18n import _


def scope_texts() -> dict[str, str]:
    """The texts of the scope line and of its form.

    Returns:
        By key, in the language in use.
    """
    return {
        "scopeAnalysed": _("Analysed:"),
        "scopeIgnored": _("ignored folders:"),
        "scopeNone": _("none but the system ones"),
        "scopeChange": _("Change"),
        "scopeSave": _("Save"),
        "scopeCancel": _("Cancel"),
        "scopeKinds": _("Kinds of files analysed"),
        "scope_photo": _("photos"),
        "scope_raw": _("RAW"),
        "scope_video": _("videos"),
        "scopeNames": _(
            "Folder names ignored wherever they are, one per line (* allowed)"
        ),
        "scopeOthers": _("also kept, written in config.toml: {list}"),
        "scopeSaved": _("Saved in config.toml, read back from the disk."),
        "scopeFailed": _("The settings could not be saved in config.toml."),
        "scopeAuditAgain": _("Run the audit again"),
    }
