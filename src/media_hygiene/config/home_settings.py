"""`[home]` — the home page's own choices (0484).

`favorites`: the actions starred on the home page, in their order, by their name in
the catalog (`library`, `import`…). The page writes it (`cli/home_favourites.py`); a
name this version does not know (a verb renamed or removed) is ignored, not an error.
`family_title`: the title a paired phone's family view shows (0461); empty: "Our
photos".
"""

from __future__ import annotations

from typing import Final

from pydantic import BaseModel, ConfigDict, Field

_LONGEST_TITLE: Final = 80


class HomeSettings(BaseModel):
    """`[home]` — the actions starred on the home page, the family view's title."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    favorites: tuple[str, ...] = ()
    family_title: str = Field(default="", max_length=_LONGEST_TITLE)
