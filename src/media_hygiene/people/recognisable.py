"""Which faces count at all: large and sharp enough to be shown, so to be checked.

`[people] min_face` and `min_sharpness` mean the same thing everywhere (TODO 0316): a
face smaller or blurrier is never grouped on the people page, so it is never named
either, by `search`, `classify`, the inventory or the XMP sidecars, unless the user
confirmed it: a name nobody can see is a name nobody can correct.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from media_hygiene.config.people_settings import PeopleSettings
    from media_hygiene.index.face_rows import StoredFace


@dataclass(frozen=True, slots=True)
class Thresholds:
    """The smallest side, in pixels, and the least sharpness a face must have."""

    min_face: float = 0.0
    min_sharpness: float = 0.0

    @classmethod
    def of(cls, settings: PeopleSettings) -> Thresholds:
        """The thresholds of `[people]`.

        Args:
            settings: `[people]`.

        Returns:
            Its `min_face` and `min_sharpness`.
        """
        return cls(settings.min_face, settings.min_sharpness)

    def small(self, face: StoredFace) -> bool:
        """Tell whether a face is too small to count.

        Args:
            face: The face.

        Returns:
            True below `min_face`.
        """
        return face.box.side < self.min_face

    def recognisable(self, face: StoredFace) -> bool:
        """Tell whether a face counts: large and sharp enough.

        Args:
            face: The face.

        Returns:
            True from `min_face` and `min_sharpness` on.
        """
        return not self.small(face) and face.sharpness >= self.min_sharpness
