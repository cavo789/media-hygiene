"""What the people page says of the work: who is there, and what is left to do.

The people list (TODO 0324) holds each person of the sections, in alphabetical order
without case nor accents, with their verified faces and the attributed ones still to
confirm. The progress line (TODO 0325) counts what is left: attributed faces (and for
how many people), groups nobody is given (and their faces), groups ignored. Both are
counted from the sections the server sends, never from what the page remembers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.people.folding import folded

if TYPE_CHECKING:
    from media_hygiene.people.sections import Sections


def people_list(sections: Sections) -> list[dict[str, object]]:
    """The people of the sections, alphabetical, with their counts.

    Args:
        sections: What the page shows.

    Returns:
        One entry per person: `name`, `verified` and `attributed` faces.
    """
    counts: dict[str, list[int]] = {}
    for section in sections.shown:
        if section.name:
            entry = counts.setdefault(section.name, [0, 0])
            entry[0 if section.verified else 1] += len(section.faces)
    return [
        {"name": name, "verified": counts[name][0], "attributed": counts[name][1]}
        for name in sorted(counts, key=lambda one: (folded(one), one))
    ]


def left_to_do(sections: Sections) -> dict[str, int]:
    """What is left to do on the page.

    Args:
        sections: What the page shows.

    Returns:
        `attributed` faces to confirm and the `people` they go to, `unnamed` groups
        and their `unnamed_faces`, the `ignored` groups.
    """
    attributed = [s for s in sections.shown if s.name and not s.verified and s.faces]
    unnamed = [s for s in sections.shown if not s.name and s.faces]
    return {
        "attributed": sum(len(s.faces) for s in attributed),
        "people": len({s.name for s in attributed}),
        "unnamed": len(unnamed),
        "unnamed_faces": sum(len(s.faces) for s in unnamed),
        "ignored": sections.ignored,
    }
