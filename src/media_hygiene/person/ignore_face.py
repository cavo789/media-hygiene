"""The cross of a face nobody is named for: "not someone to name", for good (0843).

A reflection in a window, a poster, a stranger: the detector found a face the user
will never name. The cross of `/person` and of every large view adds its id to the
ignored faces of `[people]` (`/config/people/ignored.toml`, as the people page's
*Ignore this group*), read back from the disk. Kept by face id (`<path>#<n>`) and by
its vector: a face found again near an ignored one is ignored too (`Known`), so a
new face scan, whose numbers and boxes may shift, does not offer it again; a photo
moved by `sort`, `undo` or Explorer keeps it, as every name (`follow_ids`). Ignored
faces are not shown on the photo, not grouped on `/people`, never guessed; *show
them* gives each one back (`unignore`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.i18n import _, ngettext
from media_hygiene.people.changes import ignore_faces
from media_hygiene.people.config_file import read_people, save_people
from media_hygiene.people.followed import follow_ids
from media_hygiene.people.naming import How, id_of

if TYPE_CHECKING:
    from media_hygiene.config.people_settings import PeopleSettings
    from media_hygiene.index.face_rows import StoredFace
    from media_hygiene.people.naming import FaceName
    from media_hygiene.person.names import FaceNames


def ignored_tag(
    face: StoredFace, named: FaceName, own: frozenset[str]
) -> dict[str, object] | None:
    """The tag of an ignored face for the page: hidden, `own` when its cross did it.

    Args:
        face: The face of the index.
        named: Its name, as the tool gives it.
        own: The ids `config.toml` ignores (the others are ignored as near one).

    Returns:
        The tag; None for a face that is not ignored.
    """
    if named.how != How.IGNORED:
        return None
    return {"name": "", "how": str(named.how), "not": [], "own": id_of(face) in own}


def unignore_faces(section: PeopleSettings, faces: tuple[str, ...]) -> PeopleSettings:
    """Take faces off the ignored ones: they are to name again.

    Args:
        section: `[people]` as written.
        faces: The faces, by id.

    Returns:
        The section to write.
    """
    taken = frozenset(faces)
    kept = tuple(key for key in section.ignored if key not in taken)
    return section.model_copy(update={"ignored": kept})


def ignored_line(back: PeopleSettings, faces: tuple[str, ...], action: str) -> str:
    """Say what `config.toml` holds now for the faces.

    Args:
        back: `[people]` read back from the disk.
        faces: The faces asked, by id.
        action: `ignore` or `unignore`.

    Returns:
        One line, from what the file holds, not from what was asked.
    """
    held = sum(key in back.ignored for key in faces)
    if action == "ignore":
        if held < len(faces):
            return _("Not saved: config.toml does not ignore this face.")
        return ngettext(
            "Saved in config.toml, read back: this face is ignored, never offered "
            "again ({count} face ignored).",
            "Saved in config.toml, read back: this face is ignored, never offered "
            "again ({count} faces ignored).",
            len(back.ignored),
        ).format(count=len(back.ignored))
    if held:
        return _("Not saved: config.toml still ignores this face.")
    return _("Saved in config.toml, read back: this face is no longer ignored.")


def ignoring(
    names: FaceNames, action: str, faces: tuple[str, ...]
) -> dict[str, object]:
    """Ignore faces, or take them back, saved and read back.

    Args:
        names: The page's names (`config.toml` writable: checked by the caller).
        action: `ignore` or `unignore`.
        faces: The faces, by id.

    Returns:
        The line read back (`saved`) and the names known; or `error`.
    """
    if names.config_file is None:  # pragma: no cover - checked by the caller
        return {
            "error": _(
                "names are kept in config.toml: mount a folder of yours on /config"
            )
        }
    present = {str(face.path) for face in names.faces.every}
    try:
        written = follow_ids(read_people(names.config_file), {}, present)
        change = ignore_faces if action == "ignore" else unignore_faces
        save_people(names.config_file, change(written, faces))
        back = read_people(names.config_file)
    except (ValueError, OSError) as error:
        return {"error": str(error)}
    return {
        "saved": ignored_line(back, faces, action),
        "people": [person.name for person in back.person],
    }
