"""The settings tool: Windows, privacy and the advanced actions."""

from __future__ import annotations

from media_hygiene.cli.menu_catalog_clean import LAUNCHER_SELF
from media_hygiene.cli.menu_entry import Doc, Kind, Risk, Space, Step
from media_hygiene.i18n import _


def settings_steps() -> tuple[Step, ...]:
    """The actions of the settings, after the folders and the update.

    Returns:
        Them, in order.
    """
    space = Space.SETTINGS
    return (
        Step(
            "shortcut",
            space,
            _("An icon on the Desktop and in the Start menu"),
            _("A double click opens the home page."),
            "shortcut",
            Risk.SAFE,
            Kind.HOST,
            icon="window",
            keywords=_("shortcut desktop icon start"),
            doc=LAUNCHER_SELF,
            optional=True,
            windows=True,
        ),
        Step(
            "explorer",
            space,
            _("Media Hygiene in the Explorer's right-click"),
            _("On a folder: the home page, on that folder."),
            "explorer",
            Risk.SAFE,
            Kind.HOST,
            icon="pointer",
            keywords=_("right click explorer context menu"),
            doc=LAUNCHER_SELF,
            optional=True,
            windows=True,
        ),
        Step(
            "explorer-remove",
            space,
            _("Remove Media Hygiene from the right-click"),
            _("The Explorer's menu is as it was."),
            "explorer --remove",
            Risk.SAFE,
            Kind.HOST,
            icon="pointer",
            keywords=_("right click remove delete"),
            doc=LAUNCHER_SELF,
            optional=True,
            windows=True,
        ),
        Step(
            "people-forget",
            space,
            _("Forget every face"),
            _(
                "Deletes them from the cache and shows that none is left; your "
                "photos do not change."
            ),
            "people --forget",
            Risk.SAFE,
            icon="face",
            keywords=_("privacy faces forget delete gdpr"),
            doc=Doc("commands/people/", "#your-privacy", "#votre-vie-privée"),
            optional=True,
        ),
        Step(
            "config",
            space,
            _("See each setting and where it comes from"),
            _("And the state of each folder mounted."),
            "config",
            Risk.SAFE,
            icon="sliders",
            keywords=_("configuration settings config toml ai model"),
            doc=Doc("commands/config/"),
        ),
        Step(
            "status",
            space,
            _("Where am I, in the console"),
            _("The same summary as the home page, in a few lines."),
            "status",
            Risk.SAFE,
            icon="info",
            keywords=_("status state summary"),
            doc=Doc("commands/status/"),
            optional=True,
        ),
        Step(
            "menu",
            space,
            _("The menu in the console"),
            _("Every step numbered; Enter runs the next one."),
            "menu",
            Risk.SAFE,
            icon="terminal",
            keywords=_("menu console powershell numbers"),
            doc=Doc("commands/menu/"),
            optional=True,
        ),
        Step(
            "launcher",
            space,
            _("Write mh again"),
            _("Advanced: the short command that keeps your folders."),
            "launcher",
            Risk.SAFE,
            icon="terminal",
            keywords=_("launcher script mh ps1 write again"),
            doc=Doc("commands/launcher/"),
            optional=True,
        ),
        Step(
            "home",
            space,
            _("The home page"),
            _("mh alone opens it; so does the Desktop shortcut."),
            "home",
            Risk.SAFE,
            Kind.PAGE,
            icon="home",
            keywords=_("home page start"),
            doc=Doc("commands/home/"),
            optional=True,
        ),
    )
