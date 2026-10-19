"""What `mh folders` and `mh update` say: the folders, a refusal, the versions.

Both rewrite the script by running `launcher` again (`services/launcher_kept.py`).
Their messages are written into the script, translated, with the shell variables they
show (`${folder}`, `${old}`, `${new}`, `${size}`), inside double quotes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from media_hygiene.constants import HOME_PAGE
from media_hygiene.i18n import _
from media_hygiene.services.launcher_menu import shell_safe, with_variable

# The notes of each version: a GitHub Release, made by CI at each `vX.Y.Z` tag (0187).
RELEASES: Final = f"{HOME_PAGE}/releases"


@dataclass(frozen=True, slots=True)
class UpdateTexts:  # pylint: disable=too-many-instance-attributes  # one per message
    """The messages of `mh folders` and `mh update`, ready for double quotes."""

    photos: str
    backups: str  # the backups, listed apart (0205)
    quarantine: str
    found: str
    absent: str
    unborn: str  # a quarantine not created yet, its disk there
    usage: str
    usage_windows: str  # mh.ps1: `add` alone opens Windows' folder dialog (0201)
    pick: str  # the title of that dialog
    none: str  # the dialog cancelled
    not_found: str  # holds `${folder}`
    already: str  # holds `${folder}`
    not_listed: str  # holds `${folder}`
    last: str
    unchanged: str
    no_file: str
    local: str  # holds the image's name
    pull_failed: str
    latest: str  # holds `${new}`
    updated: str  # holds `${old}` and `${new}`
    space: str  # holds `${size}`


def update_texts() -> UpdateTexts:
    """Translate the messages of `mh folders` and `mh update`.

    Returns:
        The messages, without what a double-quoted string would read as code.
    """
    folder = "${folder}"
    return UpdateTexts(
        photos=shell_safe(_("Your photo folders:")),
        backups=shell_safe(_("Your backups, compared, never changed:")),
        quarantine=shell_safe(_("The quarantine:")),
        found=shell_safe(_("found")),
        absent=shell_safe(_("not found: is its disk plugged in?")),
        unborn=shell_safe(_("not created yet: the first clean creates it")),
        usage=shell_safe(
            _(
                "Add or remove a photo folder: mh folders add <folder>, "
                "mh folders remove <folder>. A backup, compared, never changed: "
                "mh folders add --backup <folder>."
            )
        ),
        usage_windows=shell_safe(
            _(
                "Add or remove a photo folder: mh folders add (a window to choose it) "
                "or mh folders add <folder>, mh folders remove <folder>. A backup, "
                "compared, never changed: mh folders add --backup <folder>."
            )
        ),
        pick=shell_safe(_("Choose a folder of photos or videos to add")),
        none=shell_safe(_("No folder chosen: nothing changed.")),
        not_found=with_variable(
            _("{folder} cannot be found: check its name, or plug its disk in."),
            "{folder}",
            folder,
        ),
        already=with_variable(
            _("{folder} is one of your folders already."), "{folder}", folder
        ),
        not_listed=with_variable(
            _("{folder} is not one of your folders: mh folders lists them."),
            "{folder}",
            folder,
        ),
        last=shell_safe(
            _(
                "mh needs at least one photo folder: add the new one first, then "
                "remove this one."
            )
        ),
        unchanged=shell_safe(_("mh is unchanged: launcher refused it (see above).")),
        no_file=shell_safe(
            _(
                "mh was not loaded from its file: load it as step 0 of the guides "
                "says, then try again."
            )
        ),
        local=shell_safe(
            _(
                "This image is a local build: nothing to pull. Build it again, then "
                "write mh with launcher."
            )
        ),
        pull_failed=shell_safe(_("docker pull failed: mh is unchanged.")),
        latest=with_variable(
            _("Already the latest version: {version}."), "{version}", "${new}"
        ),
        updated=with_variable(
            _("Updated: {before} → {after}. What changed: {notes}"),
            "{before}",
            "${old}",
        )
        .replace("{after}", "${new}")
        .replace("{notes}", RELEASES),
        space=with_variable(
            _("The previous image still takes {size} MB: docker image prune frees it."),
            "{size}",
            "${size}",
        ),
    )
