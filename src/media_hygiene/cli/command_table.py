"""The table of the commands, before `--help` sorts them and marks the read-only."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.cli.cmd_audit import audit_command
from media_hygiene.cli.cmd_classify import classify_command
from media_hygiene.cli.cmd_config import config_command
from media_hygiene.cli.cmd_crosscheck import crosscheck_command
from media_hygiene.cli.cmd_history import history_command
from media_hygiene.cli.cmd_inventory import inventory_command
from media_hygiene.cli.cmd_launcher import launcher_command
from media_hygiene.cli.cmd_menu import menu_command
from media_hygiene.cli.cmd_people import people_command
from media_hygiene.cli.cmd_places import places_command
from media_hygiene.cli.cmd_reports import reports_command
from media_hygiene.cli.cmd_review import review_command
from media_hygiene.cli.cmd_review_sort import review_sort_command
from media_hygiene.cli.cmd_search import search_command
from media_hygiene.cli.cmd_status import status_command
from media_hygiene.cli.cmd_tags import tags_command
from media_hygiene.cli.command_actions import action_commands
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Callable


def command_table(
    analyse: str, act: str
) -> tuple[tuple[str, Callable[..., None], str, str], ...]:
    """List the commands, unsorted and before the read-only marker.

    Args:
        analyse: The translated name of the panel of analyses.
        act: The translated name of the panel of actions.

    Returns:
        Name, function, panel and help text of each command.
    """
    return (
        (
            "audit",
            audit_command,
            analyse,
            _("Find exact duplicates and broken files."),
        ),
        (
            "status",
            status_command,
            analyse,
            _("Where am I? The last audit, the quarantine, what is left: no scan."),
        ),
        (
            "menu",
            menu_command,
            analyse,
            _(
                "Every step of the guides with its command, the next one first: "
                "what 'mh' alone shows, Enter runs it."
            ),
        ),
        (
            "crosscheck",
            crosscheck_command,
            analyse,
            _(
                "Run Czkawka, an independent duplicate finder, then compare its "
                "groups with a fresh audit: a second opinion."
            ),
        ),
        (
            "classify",
            classify_command,
            analyse,
            _(
                "Propose where every photo and video should go: year, event, "
                "category, and what lone photos show with an optional local AI 🤖"
            ),
        ),
        (
            "review-sort",
            review_sort_command,
            analyse,
            _("Name the events of the classify proposal one by one in your browser."),
        ),
        (
            "places",
            places_command,
            analyse,
            _(
                "Name your places on a map of where the photos were taken; saved "
                "into config.toml for the 'place' and 'trip' rules."
            ),
        ),
        (
            "review",
            review_command,
            analyse,
            _(
                "Set burst shots aside, one series at a time, with the keyboard in "
                "your browser; 'clean --decisions' then moves them."
            ),
        ),
        *action_commands(act),
        (
            "tags",
            tags_command,
            analyse,
            _(
                "Give every photo words to find it by, kept in the cache, never in "
                "the photos: its folders, name, date and place, and what it shows "
                "with an optional local AI 🤖"
            ),
        ),
        (
            "search",
            search_command,
            analyse,
            _(
                "Find photos by their words in your browser (or as a table): "
                "the words 'tags' gave them."
            ),
        ),
        (
            "people",
            people_command,
            analyse,
            _(
                "Find the faces in the photos, group those alike and name them in "
                "your browser. Faces kept in the cache, never sent anywhere."
            ),
        ),
        (
            "inventory",
            inventory_command,
            analyse,
            _(
                "Export every photo and video with what the audits learnt to Excel,"
                " from the cache alone: no file is read."
            ),
        ),
        (
            "launcher",
            launcher_command,
            analyse,
            _("Write 'mh', a short command holding your folders: mh audit, mh clean."),
        ),
        (
            "history",
            history_command,
            analyse,
            _("List the runs and what they did."),
        ),
        (
            "reports",
            reports_command,
            analyse,
            _("List the HTML reports of previous audits and cleans."),
        ),
        (
            "config",
            config_command,
            analyse,
            _("Show every setting, where it comes from, and the mount points."),
        ),
    )
