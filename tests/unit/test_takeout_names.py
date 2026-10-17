"""Which photo a Google Photos Takeout `.json` describes, by its name (0217)."""

from __future__ import annotations

import pytest

from media_hygiene.scan.takeout import (
    edited_original,
    is_edit_pair,
    is_takeout_json,
    takeout_owners,
)

_LONG = "Original_name_of_a_holiday_picture_on_the_bea"  # 45 characters


@pytest.mark.parametrize(
    ("json_name", "names", "expected"),
    [
        ("IMG_1234.jpg.json", ["IMG_1234.jpg", "IMG_1235.jpg"], {"IMG_1234.jpg"}),
        (
            "IMG_1234.jpg.supplemental-metadata.json",
            ["IMG_1234.jpg"],
            {"IMG_1234.jpg"},
        ),
        ("IMG_1234.jpg.supplemental-meta.json", ["IMG_1234.jpg"], {"IMG_1234.jpg"}),
        ("IMG_1234.jpg.supplemental-me.json", ["IMG_1234.jpg"], {"IMG_1234.jpg"}),
        ("IMG_1234.JPG.json", ["img_1234.jpg"], {"img_1234.jpg"}),
        ("IMG_1234.json", ["IMG_1234.jpg"], {"IMG_1234.jpg"}),
        (
            "IMG_1234.jpg(1).json",
            ["IMG_1234.jpg", "IMG_1234(1).jpg"],
            {"IMG_1234(1).jpg"},
        ),
        (
            "IMG_1234.jpg.supplemental-metada(1).json",
            ["IMG_1234.jpg", "IMG_1234(1).jpg"],
            {"IMG_1234(1).jpg"},
        ),
        (
            "IMG_1234.jpg.json",
            ["IMG_1234.jpg", "IMG_1234-edited.jpg"],
            {"IMG_1234.jpg", "IMG_1234-edited.jpg"},
        ),
        ("IMG_1234.jpg.json", ["IMG_1234-edited.jpg"], {"IMG_1234-edited.jpg"}),
        ("Tom _ Jerry.jpg.json", ["Tom & Jerry.jpg"], {"Tom & Jerry.jpg"}),
        (f"{_LONG}.json", [f"{_LONG}ch_2019.jpg"], {f"{_LONG}ch_2019.jpg"}),
        (
            f"{_LONG}.json",
            [f"{_LONG}ch_2019.jpg", f"{_LONG}ch_2019-edited.jpg"],
            {f"{_LONG}ch_2019.jpg", f"{_LONG}ch_2019-edited.jpg"},
        ),
    ],
)
def test_json_finds_its_file(
    json_name: str, names: list[str], expected: set[str]
) -> None:
    """Old and new suffixes, truncated ones, the moved number, edits, `&` → `_`."""
    assert takeout_owners(json_name, names) == expected


@pytest.mark.parametrize(
    ("json_name", "names"),
    [
        ("metadata.json", ["IMG_1234.jpg"]),
        ("print-subtitled.json", ["IMG_1234.jpg"]),
        ("IMG_12.jpg.json", ["IMG_123.jpg"]),
        ("IMG_12.json", ["IMG_123.jpg"]),
        ("IMG_1234.json", ["IMG_1234.jpg", "IMG_1234.mp4"]),
        (f"{_LONG}.json", [f"{_LONG}ch_2019.jpg", f"{_LONG}ch_2020.jpg"]),
        ("IMG_1234.jpg.json", ["other.json"]),
        ("IMG_1234.jpg.xmp", ["IMG_1234.jpg"]),
    ],
)
def test_json_matching_nothing_stays_a_plain_file(
    json_name: str, names: list[str]
) -> None:
    """A short name never matches by prefix; two candidates are no match."""
    assert takeout_owners(json_name, names) == frozenset()


def test_json_names() -> None:
    """Any `.json` may be a Takeout one, in any case."""
    assert is_takeout_json("IMG_1.jpg.JSON")
    assert not is_takeout_json("IMG_1.jpg")


def test_edited_versions() -> None:
    """An edited version names its original; the pair is told in either order."""
    assert edited_original("IMG_1234-edited.jpg") == "IMG_1234.jpg"
    assert edited_original("IMG_1234-EDITED.JPG") == "IMG_1234.JPG"
    assert edited_original("IMG_1234.jpg") is None
    assert edited_original("-edited.jpg") is None
    assert is_edit_pair("IMG_1234-edited.jpg", "img_1234.jpg")
    assert is_edit_pair("IMG_1234.jpg", "IMG_1234-edited.jpg")
    assert not is_edit_pair("IMG_1234.jpg", "IMG_1235-edited.jpg")
    assert not is_edit_pair("IMG_1234.jpg", "IMG_1234 (1).jpg")
