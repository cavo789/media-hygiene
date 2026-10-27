"""What each command may do to the photos, said where the user looks: help and console.

The commands of `READ_ONLY_COMMANDS` never write, move nor delete anything in the
folders to analyse (the pages of `GO_PAGES` move the files of a group only on the
user's GO, journaled): they only write the tool's own files (reports, cache, journal
reading, `config.toml`, a decisions file). They all work with the photo folders mounted
read-only (`:ro`), where the operating system itself forbids any change. A test pins
this list to the help marker and runs these commands on read-only folders.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.constants import DOC_PAGES
from media_hygiene.i18n import _
from media_hygiene.paths.mounts import is_read_only
from media_hygiene.services.data_checks import nothing_mounted
from media_hygiene.services.phone_plan import (
    PHONE_DONE,
    PHONE_PLAN,
    PHONE_PROVE,
    PHONE_REVIEW,
)
from media_hygiene.services.push_lines import PUSH_STEP

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime

READ_ONLY_COMMANDS: Final = frozenset(
    {"audit", "crosscheck", "classify", "places", "review"}
    | {"inventory", "history", "reports", "config", "status", "launcher", "tags"}
    | {"people", "menu", PHONE_PLAN, "slideshow"}
    | {"share"}
)
# The read-only commands that read the photos themselves: they say so when they start.
PHOTO_READERS: Final = frozenset(
    {"audit", "crosscheck", "classify", "places", "review", "tags"}
    | {"people", "slideshow", "share"}
)
# The pages that sort the files of a group checked on them (0397): mounted writable,
# with `/journal`; nothing moves without the user's GO, every move is journaled.
GO_PAGES: Final = frozenset({"review-sort", "search", "browse", "home"})
# The commands serving a page in the browser, on the port published by `-p`.
PAGE_COMMANDS: Final = frozenset(
    {"review", "review-sort", "places", "search", "browse", "people", "home"}
    | {"slideshow", "shrink"}
)
# The commands whose output stream is data (a script, the steps of the menu): every
# message goes to stderr, and the launcher runs them without a terminal (`-t`) and
# without the keyboard (`-i`), which stays for the `mh` that reads their output.
DATA_COMMANDS: Final = frozenset(
    {"launcher", "menu", PHONE_PLAN, PHONE_REVIEW, PHONE_PROVE, PHONE_DONE}
    | {PUSH_STEP}
)
# The commands that may run for hours: the launcher keeps the computer awake during
# them, and says in the window title, with a sound, when they end (0179, 0185).
LONG_COMMANDS: Final = frozenset(
    {"audit", "clean", "inventory", "classify", "sort", "tags", "people", "undo"}
    | {"import", "shrink"}
)


def read_only_marker() -> str:
    """The marker opening the own help of every read-only command.

    Returns:
        The translated sentence.
    """
    return _("🔒 Read-only: never changes your photos.")


def go_line() -> str:
    """The line of the pages that move files only on the user's GO (0397).

    Returns:
        The translated sentence.
    """
    return _(
        "🔒 Nothing moves without your GO on the page; every move is journaled: "
        "'undo' puts it back."
    )


def safety_doc() -> str:
    """The page of the documentation on safety, in the user's language.

    Returns:
        Its URL on the documentation site.
    """
    return f"{DOC_PAGES}/{_('reference-safety/')}"


def help_of(name: str, text: str) -> str:
    """The own help of a command, opened by the read-only marker when it applies.

    The command list does not repeat it: its panel title says it once.

    Args:
        name: The command.
        text: Its translated help.

    Returns:
        The help shown by the command's own `--help`.
    """
    return f"{read_only_marker()} {text}" if name in READ_ONLY_COMMANDS else text


def announce_read_only(runtime: Runtime, command: str | None) -> None:
    """Say, in one line, that a command reading the photos does not touch them.

    A page of `GO_PAGES` says instead that nothing moves without the user's GO.

    When a photo folder is mounted writable, one tip tells how to let the operating
    system guarantee it (`:ro`). Without any folder, nothing is said: the command's
    own error (no folder to analyse) must be the first line the user reads.

    Args:
        runtime: Settings, mount points and output.
        command: The command about to run.
    """
    if command not in PHOTO_READERS | GO_PAGES or nothing_mounted(runtime):
        return
    output = runtime.output
    if command in GO_PAGES:
        output.info(go_line())
        return
    output.info(_("🔒 Read-only: your photos and videos are not touched."))
    roots = runtime.mounts.data_roots(runtime.locations.data_dir)
    if any(root.is_dir() and not is_read_only(root) for root in roots):
        output.tip(
            _(
                "Add :ro to the -v of your photo folders: the system itself then "
                "forbids any change. {url}"
            ).format(url=safety_doc())
        )
