r"""`mh import --phone`: a phone at its factory name is told how to rename it (0450).

The copies go to `<folder>\<phone name>`, the name Windows shows in *This PC*: the
phone's own device name. Two phones of one model left at *Galaxy A71* share a folder;
a name starting with a brand or model word says so, with how to rename the phone.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

from media_hygiene.i18n import _
from media_hygiene.services.launcher_phone_say import say

# The first word of a phone's factory name (brands and model lines).
FACTORY_WORDS: Final = (
    "Galaxy",
    "Samsung",
    "Pixel",
    "iPhone",
    "Apple",
    "Redmi",
    "Xiaomi",
    "POCO",
    "Mi",
    "Huawei",
    "Honor",
    "OnePlus",
    "OPPO",
    "Realme",
    "vivo",
    "Motorola",
    "moto",
    "Nokia",
    "Sony",
    "Xperia",
    "Nothing",
    "Fairphone",
)


@dataclass(frozen=True, slots=True)
class PhoneNaming:
    """The factory names, as a PowerShell `-match` pattern, and the tip said."""

    pattern: str  # case-insensitive in PowerShell's `-match`
    tip: str  # holds `${name}`


def phone_naming() -> PhoneNaming:
    """The pattern of the factory names and the translated tip.

    Returns:
        Them, the tip safe inside double quotes.
    """
    words = "|".join(re.escape(word) for word in FACTORY_WORDS)
    return PhoneNaming(
        pattern=f"^({words})\\b",
        tip=say(
            _(
                "💡 {name} looks like the phone's factory name: two phones of the same"
                " model would share its folder. Give it a name of its own (Samsung:"
                " Settings > About phone > Edit; Pixel: Settings > About phone > Device"
                " name), then plug it in again."
            ),
            "name",
        ),
    )
