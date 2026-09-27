"""Drawing primitives of the synthetic pictures: skies, ridges, halos, clouds, grain."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

if TYPE_CHECKING:
    import random
    from collections.abc import Sequence

type Colour = tuple[int, int, int]
type Size = tuple[int, int]
type Point = tuple[float, float]

_RIDGE_POINTS: Final = 2**7 + 1
_WHITE: Final = (250, 250, 252)


@dataclass(frozen=True, slots=True)
class Ridge:
    """A skyline: its mean height, how far it wanders, how rough it is."""

    base: float
    amplitude: float
    roughness: float = 0.55


@dataclass(frozen=True, slots=True)
class Halo:
    """A soft disc of light: sun, moon."""

    centre: Point
    radius: float
    colour: Colour
    strength: int = 160


def gradient(size: Size, stops: Sequence[tuple[float, Colour]]) -> Image.Image:
    """Paint a vertical gradient through colour stops.

    Args:
        size: Width and height.
        stops: Positions (0 at the top, 1 at the bottom) and their colours.

    Returns:
        The picture.
    """
    width, height = size
    rows = np.linspace(0, 1, height)
    positions = [position for position, _ in stops]
    channels = [
        np.interp(rows, positions, [colour[channel] for _, colour in stops])
        for channel in range(3)
    ]
    column = np.stack(channels, axis=1)
    pixels = np.broadcast_to(column[:, None, :], (height, width, 3)).astype(np.uint8)
    return Image.fromarray(np.ascontiguousarray(pixels), "RGB")


def ridge(rnd: random.Random, width: float, shape: Ridge) -> list[Point]:
    """Draw a skyline by midpoint displacement.

    Args:
        rnd: The scene's random source.
        width: Horizontal extent.
        shape: Height, amplitude and roughness.

    Returns:
        The points of the skyline, left to right.
    """
    heights = [0.0] * _RIDGE_POINTS
    heights[0], heights[-1] = rnd.uniform(-1, 1), rnd.uniform(-1, 1)
    step, scale = _RIDGE_POINTS - 1, 1.0
    while step > 1:
        half = step // 2
        for index in range(half, _RIDGE_POINTS - 1, step):
            middle = (heights[index - half] + heights[index + half]) / 2
            heights[index] = middle + rnd.uniform(-1, 1) * scale
        step, scale = half, scale * shape.roughness
    return [
        (index * width / (_RIDGE_POINTS - 1), shape.base - shape.amplitude * height)
        for index, height in enumerate(heights)
    ]


def fill(picture: Image.Image, mask: Image.Image, colour: Colour) -> None:
    """Paint a colour through a greyscale mask.

    Args:
        picture: The picture to paint on.
        mask: Where to paint, and how strongly.
        colour: The colour.
    """
    picture.paste(Image.new("RGB", picture.size, colour), (0, 0), mask)


def glow(picture: Image.Image, halo: Halo) -> None:
    """Paint a soft halo.

    Args:
        picture: The picture to paint on.
        halo: Where, how large, which colour.
    """
    mask = Image.new("L", picture.size, 0)
    (x, y), radius = halo.centre, halo.radius
    box = (x - radius, y - radius, x + radius, y + radius)
    ImageDraw.Draw(mask).ellipse(box, fill=halo.strength)
    fill(picture, mask.filter(ImageFilter.GaussianBlur(radius * 0.8)), halo.colour)


def clouds(picture: Image.Image, rnd: random.Random, band: Point) -> None:
    """Paint a few fluffy clouds.

    Args:
        picture: The picture to paint on.
        rnd: The scene's random source.
        band: Top and bottom of the band the clouds float in.
    """
    mask = Image.new("L", picture.size, 0)
    draw = ImageDraw.Draw(mask)
    for _ in range(rnd.randint(1, 4)):
        centre = (rnd.uniform(0, picture.width), rnd.uniform(*band))
        for _ in range(rnd.randint(5, 9)):
            x = centre[0] + rnd.uniform(-120, 120)
            y = centre[1] + rnd.uniform(-25, 25)
            rx, ry = rnd.uniform(40, 110), rnd.uniform(20, 45)
            draw.ellipse((x - rx, y - ry, x + rx, y + ry), fill=rnd.randint(150, 220))
    fill(picture, mask.filter(ImageFilter.GaussianBlur(14)), _WHITE)


def snowcap(picture: Image.Image, mountain: Image.Image, line: float) -> None:
    """Whiten a mountain above a snow line.

    Args:
        picture: The picture to paint on.
        mountain: The mask of the mountain.
        line: Height of the snow line.
    """
    above = Image.new("L", picture.size, 0)
    ImageDraw.Draw(above).rectangle((0, 0, picture.width, line), fill=255)
    snow = ImageChops.multiply(mountain, above.filter(ImageFilter.GaussianBlur(8)))
    fill(picture, snow, (245, 248, 252))


def grain(picture: Image.Image, seed: int) -> Image.Image:
    """Add film grain and a vignette: flat drawings look like photos.

    Args:
        picture: The drawing.
        seed: Grain identity: two shots of a burst get different grain.

    Returns:
        The finished picture.
    """
    width, height = picture.size
    noise = np.random.default_rng(seed).normal(0, 4.5, (height, width, 1))
    rows, columns = np.mgrid[0:height, 0:width]
    distance = ((columns - width / 2) / (width / 2)) ** 2
    distance = distance + ((rows - height / 2) / (height / 2)) ** 2
    vignette = 1 - 0.125 * distance
    pixels = np.asarray(picture, dtype=np.float64) * vignette[..., None] + noise
    return Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8), "RGB")
