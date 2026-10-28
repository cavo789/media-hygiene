"""What a photo's own metadata says, for the large view's facts (key I, 0433).

Facts only, read from the index's `MediaMetadata`: when it was taken, with what, how,
its size in pixels and where. Never a judgment, never written back to the file.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Final

from media_hygiene.classify.dates import exif_datetime
from media_hygiene.i18n import _

_NANO: Final = 1_000_000_000
_DAY_LENGTH: Final = 10
_TIME_LENGTH: Final = 16  # `YYYY-MM-DD HH:MM`
_SLOW: Final = 1.0  # an exposure this long or longer is written in seconds, not 1/x


def taken_text(written: str | None) -> str:
    """The date and time a file was taken, as `2023-07-14 10:32`.

    Args:
        written: The date as the file writes it (`media_date`), or None.

    Returns:
        The day and the time when the file names them, the day alone else; empty
        without a date.
    """
    if not written:
        return ""
    when = exif_datetime(written)
    if when is None:  # a video's ISO date (`2004-12-04T10:00:00Z`)
        try:
            when = datetime.fromisoformat(written)
        except ValueError:
            when = None
    if when is None:
        return written[:_DAY_LENGTH].replace(":", "-")
    return when.isoformat(sep=" ")[:_TIME_LENGTH]


def modified_day(mtime_ns: int) -> str:
    """The day the file was last modified, as Windows Explorer shows it.

    Args:
        mtime_ns: Its modification time in nanoseconds.

    Returns:
        `YYYY-MM-DD` (UTC: a day off near midnight at worst).
    """
    return datetime.fromtimestamp(mtime_ns / _NANO, tz=UTC).date().isoformat()


def exif_lines(metadata: dict[str, object], taken: str) -> tuple[str, ...]:
    """The photo's metadata, one fact per line.

    Args:
        metadata: Its metadata (`MediaMetadata` as stored).
        taken: When it was taken (`taken_text`), or empty.

    Returns:
        Taken, camera, lens, exposure, size and place, those known.
    """
    camera = " ".join(
        str(metadata[name]) for name in ("make", "model") if metadata.get(name)
    )
    lines = (
        _("Taken: {when}").format(when=taken) if taken else _("No date taken"),
        _("Camera: {camera}").format(camera=camera) if camera else "",
        _("Lens: {lens}").format(lens=metadata["lens"]) if metadata.get("lens") else "",
        _exposure(metadata),
        _pixels(metadata),
        _place(metadata),
    )
    return tuple(line for line in lines if line)


def _exposure(metadata: dict[str, object]) -> str:
    """Say how the photo was exposed: `1/250 s · f/2.8 · ISO 400 · 50 mm`.

    Args:
        metadata: Its metadata.

    Returns:
        The values known, joined; empty without any.
    """
    time, number = metadata.get("exposure_time"), metadata.get("f_number")
    iso, focal = metadata.get("iso"), metadata.get("focal_length")
    parts: list[str] = []
    if isinstance(time, int | float) and time > 0:
        parts.append(f"{time:g} s" if time >= _SLOW else f"1/{round(1 / time)} s")
    if isinstance(number, int | float):
        parts.append(f"f/{number:g}")
    if isinstance(iso, int):
        parts.append(f"ISO {iso}")
    if isinstance(focal, int | float):
        parts.append(f"{focal:g} mm")
    return " · ".join(parts)


def _pixels(metadata: dict[str, object]) -> str:
    """Say its size in pixels.

    Args:
        metadata: Its metadata.

    Returns:
        `4000 by 3000 pixels`, or empty.
    """
    width, height = metadata.get("width"), metadata.get("height")
    if not width or not height:
        return ""
    return _("{width} by {height} pixels").format(width=width, height=height)


def _place(metadata: dict[str, object]) -> str:
    """Say where it was taken, by its GPS position.

    Args:
        metadata: Its metadata.

    Returns:
        `GPS: 50.85000, 4.35000`, or empty without a position.
    """
    latitude, longitude = metadata.get("latitude"), metadata.get("longitude")
    if not isinstance(latitude, float | int) or not isinstance(longitude, float | int):
        return ""
    return _("GPS: {where}").format(where=f"{latitude:.5f}, {longitude:.5f}")
