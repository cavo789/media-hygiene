"""What a video says about itself, from the JSON `ffprobe` prints (synthetic here)."""

from __future__ import annotations

import pytest

from media_hygiene.scan.gps import iso6709_position
from media_hygiene.scan.video_meta import video_metadata

IPHONE = {
    "streams": [
        {"codec_type": "audio", "codec_name": "aac"},
        {
            "codec_type": "video",
            "codec_name": "hevc",
            "width": 1920,
            "height": 1080,
            "r_frame_rate": "30/1",
            "side_data_list": [{"side_data_type": "Display Matrix", "rotation": -90}],
        },
    ],
    "format": {
        "duration": "12.345000",
        "bit_rate": "8123456",
        "tags": {
            "creation_time": "2023-12-31T23:30:00.000000Z",
            "com.apple.quicktime.creationdate": "2024-01-01T00:30:00+0100",
            "com.apple.quicktime.location.ISO6709": "+48.8566+002.3522+035.000/",
            "com.apple.quicktime.make": "Apple",
            "com.apple.quicktime.model": "iPhone 15",
        },
    },
}
ANDROID = {
    "streams": [
        {"codec_type": "video", "codec_name": "h264", "tags": {"rotate": "90"}}
    ],
    "format": {
        "duration": "N/A",
        "tags": {
            "creation_time": "2021-07-12T10:00:00.000000Z;2021-07-12T10:00:00.000000Z",
            "LOCATION": "-22.9068-043.1729/",
            "com.android.manufacturer": "samsung",
            "com.android.model": "SM-G991B",
        },
    },
}


def test_an_iphone_video() -> None:
    """Length, codec, size, rotation, local date, place with altitude, device."""
    metadata = video_metadata(IPHONE)
    assert (metadata.duration, metadata.bit_rate) == (12.345, 8123456)
    assert (metadata.codec, metadata.width, metadata.height) == ("hevc", 1920, 1080)
    assert (metadata.frame_rate, metadata.rotation) == ("30/1", -90)
    assert metadata.created == "2023-12-31T23:30:00.000000Z"  # UTC: another year
    assert metadata.recorded_at == "2024-01-01T00:30:00+0100"  # local, as written
    assert (metadata.latitude, metadata.longitude, metadata.altitude) == (
        48.8566,
        2.3522,
        35.0,
    )
    assert (metadata.make, metadata.model) == ("Apple", "iPhone 15")


def test_an_android_video() -> None:
    """Tags in any case, a date ffprobe joined twice, the older `rotate` tag."""
    metadata = video_metadata(ANDROID)
    assert metadata.recorded_at == "2021-07-12T10:00:00.000000Z"
    assert (metadata.latitude, metadata.longitude) == (-22.9068, -43.1729)
    assert (metadata.make, metadata.model) == ("samsung", "SM-G991B")
    assert metadata.rotation == 90
    assert metadata.duration is None  # "N/A"


@pytest.mark.parametrize(
    "probe",
    [
        {},
        {"streams": "none", "format": []},
        {"format": {"tags": {"creation_time": "1904-01-01T00:00:00.000000Z"}}},
        {"format": {"tags": {"creation_time": "0000-00-00 00:00:00"}}},
    ],
    ids=["empty", "wrong-types", "quicktime-epoch", "zero-date"],
)
def test_nothing_usable_gives_empty_metadata(probe: dict[str, object]) -> None:
    """Missing or malformed values are ignored, never fatal."""
    metadata = video_metadata(probe)
    assert metadata.recorded_at is None
    assert not metadata.located
    assert metadata.codec is None


@pytest.mark.parametrize(
    "text",
    ["", "somewhere", "+95.0+002.0/", "+48.8+200.0/", "+00.0000+000.0000/"],
    ids=["empty", "words", "latitude", "longitude", "no-fix"],
)
def test_impossible_iso6709_positions_are_ignored(text: str) -> None:
    """Only real places are kept."""
    assert iso6709_position(text) is None
