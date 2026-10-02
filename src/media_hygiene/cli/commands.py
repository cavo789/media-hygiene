"""The commands of the CLI: name, function, help panel and one-line help each."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.cli.cmd_album import album_command
from media_hygiene.cli.cmd_audit import audit_command
from media_hygiene.cli.cmd_classify import classify_command
from media_hygiene.cli.cmd_clean import clean_command
from media_hygiene.cli.cmd_config import config_command
from media_hygiene.cli.cmd_crosscheck import crosscheck_command
from media_hygiene.cli.cmd_history import history_command
from media_hygiene.cli.cmd_inventory import inventory_command
from media_hygiene.cli.cmd_places import places_command
from media_hygiene.cli.cmd_purge import purge_command
from media_hygiene.cli.cmd_reports import reports_command
from media_hygiene.cli.cmd_review import review_command
from media_hygiene.cli.cmd_review_sort import review_sort_command
from media_hygiene.cli.cmd_sort import sort_command
from media_hygiene.cli.cmd_undo import undo_command
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Callable


def commands() -> tuple[tuple[str, Callable[..., None], str, str], ...]:
    """List the commands in the order of `--help`, their help translated.

    Returns:
        Name, function, panel and help text of each command.
    """
    analyse, act = _("Analyse"), _("Act")
    return (
        (
            "audit",
            audit_command,
            analyse,
            _(
                "Find exact duplicates and broken files. "
                "Read-only: mount folders with :ro."
            ),
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
            _(
                "Propose where every photo and video should go: year, event, "
                "category. Read-only."
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
            act,
            _(
                "Set burst shots aside, one series at a time, with the keyboard in "
                "your browser; 'clean --decisions' then moves them."
            ),
        ),
        (
            "clean",
            clean_command,
            act,
            _(
                "Audit, confirm, then really delete duplicate "
                "copies (journaled, undoable)."
            ),
        ),
        (
            "sort",
            sort_command,
            act,
            _(
                "Move the photos and videos as the edited classify workbook says "
                "(journaled, undoable)."
            ),
        ),
        (
            "album",
            album_command,
            act,
            _(
                "Gather a selection of the classify plan into a folder of hard "
                "links: nothing is copied nor moved (journaled, undoable)."
            ),
        ),
        (
            "undo",
            undo_command,
            act,
            _(
                "Restore every file of a run, from the kept copy, the quarantine "
                "or where it was moved; remove the links of an album."
            ),
        ),
        (
            "purge",
            purge_command,
            act,
            _("Permanently delete the quarantined broken files of a run."),
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
