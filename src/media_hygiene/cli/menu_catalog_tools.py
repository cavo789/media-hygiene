"""The three tools apart from the cycle: history and undo, reports, settings."""

from __future__ import annotations

from media_hygiene.cli.menu_entry import (
    Area,
    Doc,
    Field,
    FieldKind,
    Group,
    Kind,
    Risk,
    Space,
    Step,
)
from media_hygiene.i18n import _

FOLDERS_DOC = Doc(
    "commands/launcher/",
    "#change-your-folders-mh-folders",
    "#changer-vos-dossiers--mh-folders",
)


def tools_steps() -> tuple[Step, ...]:
    """The actions of the reports and of the folders.

    Returns:
        Them, in order.
    """
    return (
        Step(
            "reports",
            Space.REPORTS,
            _("List the reports"),
            _("And write again the page that gathers them all."),
            "reports",
            Risk.SAFE,
            icon="report",
            keywords=_("reports list index"),
            doc=Doc("commands/reports/"),
        ),
        Step(
            "reports-prune",
            Space.REPORTS,
            _("Keep only the recent reports"),
            _("The reports only: your photos are not concerned."),
            "reports --prune {count}",
            Risk.SAFE,
            icon="trash",
            keywords=_("reports old delete tidy prune"),
            doc=Doc("commands/reports/", "#options", "#options"),
            fields=(
                Field(
                    "count",
                    _("How many reports to keep?"),
                    "10",
                    r"[0-9]{1,4}",
                    FieldKind.NUMBER,
                ),
            ),
            optional=True,
        ),
        Step(
            "folders",
            Space.SETTINGS,
            _("See your folders"),
            _("Each one found or not, and the quarantine."),
            "folders",
            Risk.SAFE,
            Kind.HOST,
            icon="folder",
            keywords=_("folders list disks"),
            doc=FOLDERS_DOC,
        ),
        Step(
            "folders-remove",
            Space.SETTINGS,
            _("Remove a folder"),
            _("mh forgets it; its photos do not move."),
            "folders remove {path}",
            Risk.SAFE,
            Kind.HOST,
            icon="folder",
            keywords=_("remove folder forget"),
            doc=FOLDERS_DOC,
            fields=(
                Field(
                    "path",
                    _("The folder to remove"),
                    r"E:\Archives",
                    kind=FieldKind.FOLDER,
                ),
            ),
            optional=True,
        ),
        Step(
            "update",
            Space.SETTINGS,
            _("Install the new version"),
            _("Downloads the image, then writes mh again with the same folders."),
            "update",
            Risk.SAFE,
            Kind.HOST,
            icon="refresh",
            keywords=_("update version new upgrade docker"),
            doc=Doc(
                "commands/launcher/",
                "#a-new-version-mh-update",
                "#une-nouvelle-version--mh-update",
            ),
        ),
    )


def tools_areas() -> tuple[Area, ...]:
    """History and undo, reports, settings.

    Returns:
        The three, in the sidebar's order.
    """
    history = Area(
        Space.HISTORY,
        _("History and undo"),
        _("History and undo"),
        _("Each run is written in the journal: what it did, and how to undo it."),
        "history",
        (Group(_("The commands"), ("undo", "history", "purge")),),
        Doc("clean/09-undo-history-purge/"),
        _("9. Undo, history, purge"),
    )
    reports = Area(
        Space.REPORTS,
        _("Reports"),
        _("Reports"),
        _("The HTML reports of your audits and cleans, to open in the browser."),
        "report",
        (Group(_("The commands"), ("open", "reports", "reports-prune")),),
        Doc("clean/04-html-report/"),
        _("4. The HTML report"),
    )
    advanced = ("config", "status", "menu", "launcher", "home")
    settings = Area(
        Space.SETTINGS,
        _("Settings"),
        _("Settings"),
        _("Your folders, the update, Windows and the advanced settings."),
        "sliders",
        (
            Group(
                _("Your folders"),
                ("folders", "folders-add", "nas-add", "folders-remove"),
                extra="folders",
            ),
            Group(_("Update"), ("update",), extra="update"),
            Group(_("Windows"), ("shortcut", "explorer", "explorer-remove")),
            Group(_("Local AI"), (), extra="ai"),
            Group(_("Privacy"), ("people-forget",)),
            Group(_("Advanced"), advanced),
            Group(_("About"), (), extra="about"),
        ),
        Doc("commands/launcher/"),
        _("launcher: write your folders once"),
    )
    return history, reports, settings
