"""A tree for `tags`: three events, a burst series, an identical copy, a config.

Plain drawn pictures, never real photos: the fake model tells them by their colour.
"""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING, Final

from PIL import Image, ImageDraw

from tests.support.subjects import SIZE, write_events

if TYPE_CHECKING:
    from pathlib import Path

BURST: Final = 3
_EXIF_IFD: Final = 0x8769
_DATE_TAG: Final = 0x9003
_MAKE_TAG: Final = 0x010F
_SNOW: Final = (250, 250, 252)


def write_tree(data_dir: Path) -> Path:
    """Write the events, a burst in `Durbuy - ours`, and a copy of one shot.

    Args:
        data_dir: The /data mount point.

    Returns:
        The folder of the burst series.
    """
    events = write_events(data_dir)
    burst = data_dir / "c" / "Photos" / "2022" / "Durbuy - ours"
    burst.mkdir(parents=True)
    for index in range(BURST):
        picture = Image.new("RGB", SIZE, _SNOW)
        ImageDraw.Draw(picture).rectangle((10, 10, 12 + index, 12), fill=(0, 0, 0))
        exif = Image.Exif()
        exif[_MAKE_TAG] = "Canon"
        exif.get_ifd(_EXIF_IFD)[_DATE_TAG] = f"2022:12:25 10:00:0{index}"
        picture.save(burst / f"IMG_{index}.jpg", "JPEG", exif=exif)
    copies = data_dir / "c" / "Photos" / "Copies"
    copies.mkdir()
    shutil.copy2(events / "IMG_beach_0.jpg", copies / "IMG_beach_0.jpg")
    return burst


def write_tags_config(config_dir: Path, url: str, ai: str = 'model = "vision"') -> None:
    """Write a config.toml: the fake model, English tags.

    Args:
        config_dir: The /config mount point.
        url: The fake server.
        ai: More `[classify.ai]` lines (the model by default).
    """
    text = (
        f'[classify.ai]\nurl = "{url}"\nmin_edge = 400\n{ai}\n\n'
        '[tags]\nlanguage = "en"\n'
    )
    (config_dir / "config.toml").write_text(text, encoding="utf-8")
