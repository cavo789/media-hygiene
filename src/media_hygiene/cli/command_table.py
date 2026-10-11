"""The table of the commands, in the order of `--help`, before the read-only marker."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.cli.cmd_audit import audit_command
from media_hygiene.cli.cmd_classify import classify_command
from media_hygiene.cli.cmd_config import config_command
from media_hygiene.cli.cmd_crosscheck import crosscheck_command
from media_hygiene.cli.cmd_history import history_command
from media_hygiene.cli.cmd_inventory import inventory_command
from media_hygiene.cli.cmd_launcher import launcher_command
from media_hygiene.cli.cmd_places import places_command
from media_hygiene.cli.cmd_reports import reports_command
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
    """List the commands in the order of `--help`, before the read-only marker.

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
            "crosscheck",
            crosscheck_command,
            analyse,
            _(
                "Compare a fresh audit with Czkawka's results: a second, "
                "independent opinion."
            ),
        ),
        (
            "classify",
            classify_command,
            analyse,
            _("Propose where every photo and video should go: year, event, category."),
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
        *action_commands(act),
        (
            "tags",
            tags_command,
            analyse,
            _(
                "Give every photo words to find it by: its folders, date and place, "
                "and what a local vision model sees. Kept in the cache, never in "
                "the photos."
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
