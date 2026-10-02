"""Synthetic events for the `subject` rule: a beach, snow and a cake, five shots each.

Plain drawn pictures, never real photos: the fake model tells them by their colour.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Final

from PIL import Image, ImageDraw

if TYPE_CHECKING:
    from pathlib import Path

SIZE: Final = (800, 600)
EVENTS: Final = {
    "beach": ((60, 120, 230), "2021:07:14"),
    "snow": ((250, 250, 252), "2022:02:10"),
    "cake": ((150, 90, 60), "2023:05:20"),
}
SHOTS: Final = 5
_EXIF_IFD: Final = 0x8769
_DATE_TAG: Final = 0x9003
_MAKE_TAG: Final = 0x010F
CATEGORIES: Final = ("Holidays and outings", "Nature and landscapes", "Parties")


def write_events(data_dir: Path) -> Path:
    """Write three events of loose shots in `c/Photos/DCIM`.

    Returns:
        The folder.
    """
    folder = data_dir / "c" / "Photos" / "DCIM"
    folder.mkdir(parents=True, exist_ok=True)
    for name, (colour, day) in EVENTS.items():
        rnd = random.Random(name)  # noqa: S311 - test pictures, not secrets
        for index in range(SHOTS):
            picture = Image.new("RGB", SIZE, colour)
            draw = ImageDraw.Draw(picture)
            for _ in range(index + 1):  # later shots hold more detail: sharper
                left, top = rnd.randrange(700), rnd.randrange(500)
                draw.rectangle((left, top, left + 40, top + 30), fill=colour[::-1])
            exif = Image.Exif()
            exif[_MAKE_TAG] = "Canon"
            exif.get_ifd(_EXIF_IFD)[_DATE_TAG] = f"{day} {10 + index:02d}:00:00"
            picture.save(folder / f"IMG_{name}_{index}.jpg", "JPEG", exif=exif)
    return folder


def write_config(config_dir: Path, url: str, ai: str = "") -> None:
    """Write a config.toml whose only rule asks the model at `url`.

    Args:
        config_dir: The /config mount point.
        url: The fake server.
        ai: More `[classify.ai]` lines.
    """
    categories = ", ".join(f'"{category}"' for category in CATEGORIES)
    text = (
        f'[classify.ai]\nurl = "{url}"\nmodel = "vision"\nmin_edge = 400\n{ai}\n\n'
        '[[classify.rules]]\nname = "Subject"\nmatch = "subject"\n'
        f"categories = [{categories}]\n"
    )
    (config_dir / "config.toml").write_text(text, encoding="utf-8")
