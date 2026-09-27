"""Festive synthetic pictures: a snowy Christmas night, a birthday party."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from PIL import ImageDraw

from tests.support.docs.painting import Halo, Ridge, glow, gradient, ridge

if TYPE_CHECKING:
    import random

    from PIL import Image

    from tests.support.docs.painting import Colour, Size

_LIGHTS: Final = ((255, 80, 80), (255, 220, 90), (120, 200, 255))
_BALLOONS: Final = (
    (230, 60, 70),
    (250, 190, 40),
    (60, 140, 220),
    (90, 190, 110),
    (200, 90, 200),
    (250, 130, 60),
)
_WALLS: Final = ((250, 235, 215), (225, 240, 245), (245, 230, 240))
_SNOW: Final = (250, 250, 255)


@dataclass(frozen=True, slots=True)
class _Stage:
    """The party room: its size and the height of the table."""

    width: int
    height: int
    table: float


def _fir(
    draw: ImageDraw.ImageDraw, rnd: random.Random, foot: tuple[float, float]
) -> None:
    """A fir tree with its fairy lights."""
    x, y = foot
    tall = rnd.uniform(180, 320)
    for level in range(4):
        top = y - tall + level * tall / 5
        half = tall / 5 + level * tall / 10
        draw.polygon(
            [(x, top), (x - half, top + tall / 3), (x + half, top + tall / 3)],
            fill=(20, 80, 45),
        )
    for _ in range(18):
        lx, ly = x + rnd.uniform(-tall / 3, tall / 3), y - rnd.uniform(0, tall * 0.8)
        draw.ellipse((lx - 4, ly - 4, lx + 4, ly + 4), fill=rnd.choice(_LIGHTS))


def _house(draw: ImageDraw.ImageDraw, left: float, height: int) -> None:
    """A small house with a snowy roof and lit windows."""
    draw.rectangle((left, height * 0.55, left + 260, height * 0.74), fill=(120, 60, 50))
    roof = [
        (left - 30, height * 0.56),
        (left + 130, height * 0.42),
        (left + 290, height * 0.56),
    ]
    draw.polygon(roof, fill=(235, 240, 250))
    for window in (left + 40, left + 170):
        draw.rectangle(
            (window, height * 0.6, window + 50, height * 0.66), fill=(255, 205, 110)
        )


def christmas(rnd: random.Random, size: Size) -> Image.Image:
    """A Christmas night: stars, the moon, a house, fir trees, falling snow.

    Args:
        rnd: The scene's random source.
        size: Width and height.

    Returns:
        The drawing.
    """
    width, height = size
    picture = gradient(
        size, [(0, (10, 15, 40)), (0.7, (40, 55, 100)), (1, (40, 55, 100))]
    )
    draw = ImageDraw.Draw(picture)
    for _ in range(160):
        draw.point(
            (rnd.uniform(0, width), rnd.uniform(0, height * 0.6)), fill=(240, 240, 255)
        )
    moon = (rnd.uniform(0.1, 0.9) * width, rnd.uniform(0.08, 0.2) * height)
    glow(picture, Halo(moon, 60, (230, 235, 255), 120))
    draw.ellipse(
        (moon[0] - 35, moon[1] - 35, moon[0] + 35, moon[1] + 35), fill=(245, 245, 235)
    )
    ground = ridge(rnd, width, Ridge(height * 0.72, 40, 0.45))
    draw.polygon([*ground, (width, height), (0, height)], fill=(225, 232, 245))
    _house(draw, rnd.uniform(0.15, 0.6) * width, height)
    for _ in range(rnd.randint(4, 7)):
        _fir(
            draw,
            rnd,
            (rnd.uniform(0, width), rnd.uniform(height * 0.72, height * 0.95)),
        )
    for _ in range(260):
        x, y, radius = (
            rnd.uniform(0, width),
            rnd.uniform(0, height),
            rnd.uniform(1.5, 4),
        )
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=_SNOW)
    return picture


def _balloon(draw: ImageDraw.ImageDraw, rnd: random.Random, stage: _Stage) -> None:
    """A balloon on its string, with a highlight."""
    x, y = rnd.uniform(0.05, 0.95) * stage.width, rnd.uniform(0.18, 0.5) * stage.height
    rx, ry = rnd.uniform(55, 80), rnd.uniform(70, 100)
    colour: Colour = rnd.choice(_BALLOONS)
    shine = (
        min(255, colour[0] + 70),
        min(255, colour[1] + 70),
        min(255, colour[2] + 70),
    )
    string = (x, y + ry, x + rnd.uniform(-60, 60), stage.table)
    draw.line(string, fill=(110, 110, 110), width=2)
    draw.ellipse((x - rx, y - ry, x + rx, y + ry), fill=colour)
    draw.ellipse((x - rx * 0.5, y - ry * 0.65, x - rx * 0.15, y - ry * 0.2), fill=shine)
    draw.polygon(
        [(x - 8, y + ry + 12), (x + 8, y + ry + 12), (x, y + ry - 2)], fill=colour
    )


def _cake(draw: ImageDraw.ImageDraw, rnd: random.Random, stage: _Stage) -> None:
    """A two-layer cake and its five candles."""
    centre, table = rnd.uniform(0.35, 0.65) * stage.width, stage.table
    draw.rectangle(
        (centre - 150, table - 110, centre + 150, table), fill=(250, 240, 230)
    )
    draw.rectangle(
        (centre - 110, table - 190, centre + 110, table - 110), fill=(245, 170, 190)
    )
    for candle in range(5):
        x = centre - 80 + candle * 40
        draw.rectangle(
            (x - 5, table - 250, x + 5, table - 190), fill=rnd.choice(_BALLOONS)
        )
        draw.ellipse((x - 8, table - 280, x + 8, table - 252), fill=(255, 200, 60))


def _bunting(draw: ImageDraw.ImageDraw, width: int) -> None:
    """A garland of little flags across the top of the wall."""
    string = [
        (x, 60 + 70 * math.sin(math.pi * x / width)) for x in range(0, width + 1, 20)
    ]
    draw.line(string, fill=(120, 100, 90), width=3)
    for index in range(0, len(string) - 3, 3):
        (x1, y1), (x2, y2) = string[index], string[index + 3]
        flag = [(x1, y1), (x2, y2), ((x1 + x2) / 2, (y1 + y2) / 2 + 70)]
        draw.polygon(flag, fill=_BALLOONS[(index // 3) % len(_BALLOONS)])


def balloons(rnd: random.Random, size: Size) -> Image.Image:
    """A birthday party: bunting, a cake, balloons.

    Args:
        rnd: The scene's random source.
        size: Width and height.

    Returns:
        The drawing.
    """
    width, height = size
    wall = rnd.choice(_WALLS)
    shade = (int(wall[0] * 0.85), int(wall[1] * 0.85), int(wall[2] * 0.85))
    picture = gradient(size, [(0, wall), (1, shade)])
    draw = ImageDraw.Draw(picture)
    _bunting(draw, width)
    stage = _Stage(width, height, height * 0.78)
    draw.rectangle((0, stage.table, width, height), fill=(150, 100, 70))
    _cake(draw, rnd, stage)
    for _ in range(rnd.randint(7, 11)):
        _balloon(draw, rnd, stage)
    return picture
