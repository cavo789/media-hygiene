"""The texts of what the audit analyses and ignores, on the home page (0535)."""

from __future__ import annotations

from media_hygiene.i18n import _


def scope_texts() -> dict[str, str]:
    """The texts of the scope line and of its form, and of the import's steps.

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
        **imports_texts(),
    }


def imports_texts() -> dict[str, str]:
    """The texts of the steps after an import (0481).

    Returns:
        By key, in the language in use.
    """
    return {
        "importsThen": _("After the import:"),
        "importsNone": _("nothing, only the copy"),
        "imports_audit": _("add to the library (audit)"),
        "imports_copies": _("set aside the copies"),
        "imports_bursts": _("the burst series page"),
        "imports_tags": _("🤖 describe the photos"),
        "imports_places": _("🌐 name the places"),
        "chainTitle": _("The last import's steps:"),
        "chainRunning": _("running in the window of mh"),
        "chainWaiting": _("waiting"),
        "chainStopped": _("stopped"),
        "chainDone": _("done"),
        "chainFailed": _("it said why in the window of mh"),
        "chainResume": _("▶ Run again from: {step}"),
        "chainType": _("In the window of mh: {command}"),
        "chainBursts": _("📸 Its burst series"),
    }
