"""Read what `ffprobe` says about a video: length, codec, size, date, place and device.

All of it comes from the probe that already checks the video can be opened: only its
`-show_entries` list is wider. Tag names differ between Apple, Android and cameras, and
in case: they are compared case-insensitively. A malformed value is ignored.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Final

from media_hygiene.scan.exif_values import text
from media_hygiene.scan.gps import iso6709_position, position_fields
from media_hygiene.scan.metadata import MediaMetadata

PROBE_ENTRIES: Final = (
    "format=duration,bit_rate:format_tags"
    ":stream=codec_type,codec_name,width,height,r_frame_rate"
    ":stream_tags=rotate:stream_side_data=rotation"
)
_MAKE_TAGS: Final = ("com.apple.quicktime.make", "com.android.manufacturer", "make")
_MODEL_TAGS: Final = ("com.apple.quicktime.model", "com.android.model", "model")
_LOCATION_TAGS: Final = (
    "com.apple.quicktime.location.iso6709",
    "location",
    "location-eng",
)
_LOCAL_DATE_TAG: Final = "com.apple.quicktime.creationdate"
# Devices without a clock write the epoch of their format: not a date.
_NO_DATE: Final = ("0000", "1904-01-01T00:00:00", "1970-01-01T00:00:00")
# ffprobe joins the values of a tag found twice with ";".
_SEPARATOR: Final = ";"


def video_metadata(probe: Mapping[str, object]) -> MediaMetadata:
    """Describe a video from the JSON `ffprobe` printed.

    Args:
        probe: The parsed output of `ffprobe -show_entries PROBE_ENTRIES -of json`.

    Returns:
        Its metadata.
    """
    container = _mapping(probe.get("format"))
    tags = {
        key.casefold(): value for key, value in _mapping(container.get("tags")).items()
    }
    video = _video_stream(probe.get("streams"))
    location = _first(tags, _LOCATION_TAGS)
    fields: dict[str, object] = {
        "duration": _number(container.get("duration")),
        "bit_rate": _whole(container.get("bit_rate")),
        "created": _date(tags.get("creation_time")),
        "created_local": _date(tags.get(_LOCAL_DATE_TAG)),
        "make": _first(tags, _MAKE_TAGS),
        "model": _first(tags, _MODEL_TAGS),
        "location": location,
        "codec": text(video.get("codec_name")),
        "width": _whole(video.get("width")),
        "height": _whole(video.get("height")),
        "frame_rate": text(video.get("r_frame_rate")),
        "rotation": _rotation(video),
    }
    return MediaMetadata.model_validate(
        fields | position_fields(iso6709_position(location))
    )


def _mapping(value: object) -> Mapping[str, object]:
    """Return a JSON object, or an empty one when the value is something else.

    Args:
        value: A parsed JSON value.

    Returns:
        The object.
    """
    return value if isinstance(value, Mapping) else {}


def _video_stream(streams: object) -> Mapping[str, object]:
    """Find the first video stream.

    Args:
        streams: The `streams` list of the probe.

    Returns:
        The stream, or an empty object for a file with audio only.
    """
    if not isinstance(streams, list):
        return {}
    videos = (_mapping(stream) for stream in streams)
    return next(
        (stream for stream in videos if stream.get("codec_type") == "video"), {}
    )


def _first(tags: Mapping[str, object], names: tuple[str, ...]) -> str | None:
    """Return the first tag found among several names for one thing.

    Args:
        tags: The container tags, names in lower case.
        names: Candidate names, in lower case, the most precise first.

    Returns:
        Its text, or None.
    """
    return next((found for name in names if (found := text(tags.get(name)))), None)


def _date(value: object) -> str | None:
    """Keep a date as written, the first one when ffprobe joined two.

    Args:
        value: The tag.

    Returns:
        The date, or None when absent or the zero of a device without a clock.
    """
    written = text(value)
    if written is None:
        return None
    first = written.split(_SEPARATOR, 1)[0].strip()
    return None if not first or first.startswith(_NO_DATE) else first


def _number(value: object) -> float | None:
    """Read a number ffprobe printed as text or as a number.

    Args:
        value: The value.

    Returns:
        The number, or None when it is not a finite one.
    """
    if isinstance(value, bool) or not isinstance(value, str | int | float):
        return None
    try:
        result = float(value)
    except ValueError:
        return None
    return result if math.isfinite(result) else None


def _whole(value: object) -> int | None:
    """Read an integer ffprobe printed as text or as a number.

    Args:
        value: The value.

    Returns:
        The integer, or None.
    """
    result = _number(value)
    return round(result) if result is not None else None


def _rotation(video: Mapping[str, object]) -> int | None:
    """Read how the video is turned on display: side data, or the older `rotate` tag.

    Args:
        video: The video stream.

    Returns:
        Degrees, or None when not recorded.
    """
    side_data = video.get("side_data_list")
    if isinstance(side_data, list):
        for item in side_data:
            degrees = _whole(_mapping(item).get("rotation"))
            if degrees is not None:
                return degrees
    return _whole(_mapping(video.get("tags")).get("rotate"))
