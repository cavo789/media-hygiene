"""`[tags]` — the words of `media-hygiene tags`: their language, the words left out.

The vision model is the one of `[classify.ai]` (url, model, sizes, confirmation): one
model and one server for the whole tool. Without a model, `tags` computes the words
of the folders, names, dates and places only.
"""

from __future__ import annotations

from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field

from media_hygiene.constants import Locale
from media_hygiene.tags.models import TagSource

# Words that describe every photo, so none: measured on a real collection (TODO 0072).
STOP_WORDS: Final = (
    *("sol", "mur", "murs", "intérieur", "extérieur", "plafond", "photo", "image"),
    *("personne", "personnes", "chose", "objet", "fond", "scène", "vue"),
    *("floor", "wall", "indoor", "indoors", "outdoor", "outdoors", "ceiling"),
    *("picture", "person", "people", "thing", "object", "background", "scene", "view"),
)
_TOWN_KM: Final = 20.0
# Folder, name and date words are seen in the path already: only these go into
# sidecars.
XMP_SOURCES: Final = (TagSource.VISION, TagSource.PLACE)


class TagSettings(BaseModel):
    """`[tags]` — the language of the words, the words left out, the town radius."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    language: Literal["", "en", "fr"] = ""  # empty: the language of the interface
    stop_words: tuple[str, ...] = STOP_WORDS
    # A GPS position names its GeoNames town only that close (km): not at sea.
    town_km: float = Field(default=_TOWN_KM, gt=0)
    # The sources whose words `xmp` writes into `dc:subject` (the sentence of the
    # model always goes into `dc:description`).
    xmp_sources: tuple[TagSource, ...] = XMP_SOURCES
    # A photo without GPS in a folder named after a town gets that town's position in
    # its sidecar: approximate, so only when asked (0230).
    xmp_folder_gps: bool = False

    def language_of(self, interface: Locale) -> Locale:
        """The language the words are written in.

        Args:
            interface: The language of the interface (`[general] locale`).

        Returns:
            `language`, or the interface's when empty.
        """
        return Locale(self.language) if self.language else interface
