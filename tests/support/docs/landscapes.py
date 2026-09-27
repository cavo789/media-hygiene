"""Landscapes of the synthetic pictures: beaches, mountains, sunsets, meadows."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from PIL import Image, ImageDraw

from tests.support.docs.painting import (
    Halo,
    Ridge,
    clouds,
    fill,
    glow,
    gradient,
    ridge,
    snowcap,
)

if TYPE_CHECKING:
    import random

    from tests.support.docs.painting import Colour, Size

_UMBRELLAS: Final = ((220, 60, 60), (240, 170, 40), (40, 120, 200), (60, 170, 90))
_FLOWERS: Final = (
    (230, 60, 80),
    (250, 210, 60),
    (250, 250, 250),
    (170, 90, 200),
    (250, 140, 40),
)
# Colour, height (share of the picture) and amplitude of each range, farthest first.
_RANGES: Final = (
    ((160, 175, 195), 0.45, 170),
    ((110, 135, 150), 0.58, 120),
    ((60, 100, 80), 0.72, 80),
    ((35, 70, 50), 0.86, 50),
)
_DUSK: Final = (40, 25, 50)


def _umbrella(
    draw: ImageDraw.ImageDraw, foot: tuple[float, float], colour: Colour
) -> None:
    """A beach umbrella and its towel."""
    x, y = foot
    draw.line((x, y - 150, x + 8, y + 40), fill=(90, 70, 60), width=6)
    draw.pieslice((x - 130, y - 230, x + 130, y - 70), 180, 360, fill=colour)
    draw.rectangle((x - 60, y + 40, x + 90, y + 75), fill=(250, 250, 250))


def beach(rnd: random.Random, size: Size) -> Image.Image:
    """A sunny beach: sea, sand, umbrellas.

    Args:
        rnd: The scene's random source.
        size: Width and height.

    Returns:
        The drawing.
    """
    width, height = size
    horizon = int(height * rnd.uniform(0.45, 0.55))
    sky = (horizon / height, (185, 215, 238))
    picture = gradient(size, [(0, (60, 120, 200)), sky, (1, sky[1])])
    glow(
        picture,
        Halo(
            (rnd.uniform(0.15, 0.85) * width, 0.15 * height), 70, (255, 250, 220), 230
        ),
    )
    clouds(picture, rnd, (height * 0.08, horizon * 0.7))
    shore = int(height * rnd.uniform(0.68, 0.76))
    picture.paste(
        gradient((width, shore - horizon), [(0, (30, 90, 150)), (1, (60, 170, 180))]),
        (0, horizon),
    )
    draw = ImageDraw.Draw(picture)
    for _ in range(90):
        y, x = rnd.uniform(horizon + 5, shore), rnd.uniform(0, width)
        length = rnd.uniform(20, 90) * (y - horizon) / (shore - horizon + 1)
        draw.line((x, y, x + length, y), fill=(170, 215, 225), width=2)
    sand = ridge(rnd, width, Ridge(shore, 18, 0.4))
    draw.polygon([*sand, (width, height), (0, height)], fill=(226, 205, 160))
    draw.line(sand, fill=(245, 245, 240), width=6)
    for _ in range(rnd.randint(1, 3)):
        foot = (rnd.uniform(0.1, 0.9) * width, rnd.uniform(shore + 60, height - 60))
        _umbrella(draw, foot, rnd.choice(_UMBRELLAS))
    return picture


def _firs(draw: ImageDraw.ImageDraw, rnd: random.Random, size: Size) -> None:
    """Dark fir trees in the foreground."""
    width, height = size
    for _ in range(rnd.randint(8, 18)):
        x, y = rnd.uniform(0, width), rnd.uniform(height * 0.8, height * 0.98)
        tall = rnd.uniform(60, 140)
        tree = [(x, y - tall), (x - tall / 3.5, y), (x + tall / 3.5, y)]
        draw.polygon(tree, fill=(20, 50, 30))


def mountains(rnd: random.Random, size: Size) -> Image.Image:
    """Mountain ranges fading in the distance, snow on the farthest one, fir trees.

    Args:
        rnd: The scene's random source.
        size: Width and height.

    Returns:
        The drawing.
    """
    width, height = size
    picture = gradient(
        size, [(0, (90, 140, 205)), (0.6, (205, 225, 240)), (1, (205, 225, 240))]
    )
    clouds(picture, rnd, (height * 0.05, height * 0.3))
    for rank, (colour, base, amplitude) in enumerate(_RANGES):
        points = ridge(rnd, width, Ridge(height * base, amplitude))
        mask = Image.new("L", size, 0)
        ImageDraw.Draw(mask).polygon([*points, (width, height), (0, height)], fill=255)
        fill(picture, mask, colour)
        if rank == 0:
            summit = min(y for _, y in points)
            snowcap(picture, mask, summit + (height * base - summit) * 0.45)
    _firs(ImageDraw.Draw(picture), rnd, size)
    return picture


def sunset(rnd: random.Random, size: Size) -> Image.Image:
    """The sun setting on a lake, its reflection, a dark shore and birds.

    Args:
        rnd: The scene's random source.
        size: Width and height.

    Returns:
        The drawing.
    """
    width, height = size
    horizon = int(height * rnd.uniform(0.55, 0.65))
    glowing = (horizon / height, (250, 180, 90))
    picture = gradient(
        size, [(0, (60, 40, 110)), (0.35, (200, 90, 110)), glowing, (1, glowing[1])]
    )
    sun = rnd.uniform(0.3, 0.7) * width
    glow(picture, Halo((sun, horizon - 20), 160, (255, 220, 140), 200))
    draw = ImageDraw.Draw(picture)
    draw.ellipse((sun - 70, horizon - 90, sun + 70, horizon + 50), fill=(255, 235, 170))
    picture.paste(
        gradient((width, height - horizon), [(0, (180, 100, 90)), (1, (50, 30, 70))]),
        (0, horizon),
    )
    for line in range(40):
        y = horizon + 6 + line * (height - horizon) / 40
        half = 90 * (1 - line / 50) * rnd.uniform(0.6, 1.2)
        draw.line((sun - half, y, sun + half, y), fill=(250, 200, 130), width=3)
    shore = ridge(rnd, width, Ridge(horizon, 45, 0.5))
    shore = shore[: len(shore) // 3]  # a headland on the left
    draw.polygon([*shore, (shore[-1][0], horizon), (0, horizon)], fill=_DUSK)
    for _ in range(rnd.randint(2, 4)):
        x, y = rnd.uniform(0, width), rnd.uniform(height * 0.1, height * 0.35)
        draw.arc((x - 18, y - 8, x, y + 8), 200, 340, fill=_DUSK, width=3)
        draw.arc((x, y - 8, x + 18, y + 8), 200, 340, fill=_DUSK, width=3)
    return picture


def meadow(rnd: random.Random, size: Size) -> Image.Image:
    """A meadow full of flowers under a blue sky.

    Args:
        rnd: The scene's random source.
        size: Width and height.

    Returns:
        The drawing.
    """
    width, height = size
    horizon = int(height * rnd.uniform(0.35, 0.5))
    sky = (horizon / height, (215, 232, 245))
    picture = gradient(size, [(0, (100, 160, 220)), sky, (1, sky[1])])
    clouds(picture, rnd, (height * 0.05, horizon * 0.8))
    draw = ImageDraw.Draw(picture)
    hills = ridge(rnd, width, Ridge(horizon + 10, 40, 0.45))
    draw.polygon([*hills, (width, height), (0, height)], fill=(110, 160, 80))
    grass = gradient(
        (width, height - horizon - 60), [(0, (100, 150, 70)), (1, (50, 110, 40))]
    )
    picture.paste(grass, (0, horizon + 60))
    for _ in range(700):
        y, x = rnd.uniform(horizon + 60, height), rnd.uniform(0, width)
        radius = 2 + 11 * (y - horizon) / (height - horizon)
        draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius), fill=rnd.choice(_FLOWERS)
        )
    return picture
