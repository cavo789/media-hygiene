"""The function behind each command, apart from its help so the menu reads it alone."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.cli.cmd_album import album_command
from media_hygiene.cli.cmd_audit import audit_command
from media_hygiene.cli.cmd_browse import browse_command
from media_hygiene.cli.cmd_classify import classify_command
from media_hygiene.cli.cmd_clean import clean_command
from media_hygiene.cli.cmd_config import config_command
from media_hygiene.cli.cmd_crosscheck import crosscheck_command
from media_hygiene.cli.cmd_history import history_command
from media_hygiene.cli.cmd_home import home_command
from media_hygiene.cli.cmd_import import import_command
from media_hygiene.cli.cmd_inventory import inventory_command
from media_hygiene.cli.cmd_launcher import launcher_command
from media_hygiene.cli.cmd_menu import menu_command
from media_hygiene.cli.cmd_people import people_command
from media_hygiene.cli.cmd_places import places_command
from media_hygiene.cli.cmd_purge import purge_command
from media_hygiene.cli.cmd_push import push_command
from media_hygiene.cli.cmd_reports import reports_command
from media_hygiene.cli.cmd_review import review_command
from media_hygiene.cli.cmd_review_sort import review_sort_command
from media_hygiene.cli.cmd_search import search_command
from media_hygiene.cli.cmd_share import share_command
from media_hygiene.cli.cmd_shrink import shrink_command
from media_hygiene.cli.cmd_slideshow import slideshow_command
from media_hygiene.cli.cmd_sort import sort_command
from media_hygiene.cli.cmd_status import status_command
from media_hygiene.cli.cmd_tags import tags_command
from media_hygiene.cli.cmd_undo import undo_command
from media_hygiene.cli.cmd_xmp import xmp_command

if TYPE_CHECKING:
    from collections.abc import Callable


def command_functions() -> dict[str, Callable[..., None]]:
    """Map each command name to its function.

    Returns:
        The function of each command, by name.
    """
    return {
        "album": album_command,
        "audit": audit_command,
        "push": push_command,
        "browse": browse_command,
        "classify": classify_command,
        "clean": clean_command,
        "config": config_command,
        "crosscheck": crosscheck_command,
        "history": history_command,
        "home": home_command,
        "import": import_command,
        "inventory": inventory_command,
        "launcher": launcher_command,
        "menu": menu_command,
        "people": people_command,
        "places": places_command,
        "purge": purge_command,
        "reports": reports_command,
        "review": review_command,
        "review-sort": review_sort_command,
        "search": search_command,
        "share": share_command,
        "shrink": shrink_command,
        "slideshow": slideshow_command,
        "sort": sort_command,
        "status": status_command,
        "tags": tags_command,
        "undo": undo_command,
        "xmp": xmp_command,
    }
