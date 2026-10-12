"""`[people]` — the faces of `media-hygiene people`: which ones count, who is who.

The faces are found once and kept in the cache with their size and sharpness: these
settings only choose which ones are grouped, so changing them costs no new analysis.
The names live here too (`[[people.person]]`), written by the people page: each one
lists the faces the user confirmed, by photo and face number, never a face vector.
"""

from __future__ import annotations

from typing import Final, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from media_hygiene.faces.cluster import SFACE_SIMILARITY
from media_hygiene.i18n import _

# Measured on sample faces (TODO 0058): below, the vector of a face drifts away from
# the same face seen sharp; to tune on a real collection.
MIN_FACE: Final = 40
MIN_SHARPNESS: Final = 30.0


class Person(BaseModel):
    """`[[people.person]]` — a name and the faces the user confirmed as theirs."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1)
    # The faces confirmed on the page: `<photo path>#<face number>`. Several groups
    # named alike add up: a child's faces of every age.
    faces: tuple[str, ...] = ()
    # Faces removed from this person on the page: never given this name again.
    rejected: tuple[str, ...] = ()


class PeopleSettings(BaseModel):
    """`[people]` — the small and blurry faces left out, the threshold, the names."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    # Cosine similarity from which two faces may be the same person.
    similarity: float = Field(default=SFACE_SIMILARITY, gt=0, lt=1)
    # Faces whose box is smaller (shorter side, pixels) are not grouped.
    min_face: int = Field(default=MIN_FACE, ge=0)
    # Faces blurrier than this (variance of the Laplacian) are not grouped.
    min_sharpness: float = Field(default=MIN_SHARPNESS, ge=0)
    # `audit` looks for faces too, after asking, as with `audit --people`.
    with_audit: bool = False
    # Faces of strangers, posters, statues: never named, their group never shown.
    ignored: tuple[str, ...] = ()
    person: tuple[Person, ...] = ()

    @model_validator(mode="after")
    def _names_once(self) -> Self:
        """Refuse two people of the same name: their faces would be split.

        Returns:
            The settings.

        Raises:
            ValueError: A name is written twice, whatever its case.
        """
        seen: set[str] = set()
        for person in self.person:
            folded = person.name.strip().casefold()
            if folded in seen:
                message = _("two people are named '{name}'").format(name=person.name)
                raise ValueError(message)
            seen.add(folded)
        return self
