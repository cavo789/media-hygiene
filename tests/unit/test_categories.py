"""Extension categories: built-in names, the user's own, and how `--ext` reads them."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from media_hygiene.config.loader import Origin, load_settings
from media_hygiene.config.scan_settings import ScanSettings
from media_hygiene.constants import (
    IMAGE_EXTENSIONS,
    MEDIA_EXTENSIONS,
    RAW_EXTENSIONS,
    VIDEO_EXTENSIONS,
)
from media_hygiene.errors import ConfigError

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations

_PHONE: dict[str, tuple[str, ...]] = {"phone": ("heic", "MP4", ".mov")}


@pytest.mark.parametrize(
    ("asked", "expected"),
    [
        ("video", VIDEO_EXTENSIONS),
        ("photo,raw", IMAGE_EXTENSIONS | RAW_EXTENSIONS),
        ("media", MEDIA_EXTENSIONS),
        ("heic", {".heic"}),
        ("RAF,arw", {".raf", ".arw"}),
    ],
)
def test_builtin_categories_and_extensions(asked: str, expected: set[str]) -> None:
    """Dotless: a category when one has that name, else an extension; dotted: one."""
    scan = ScanSettings(extensions=(asked,))
    assert set(scan.resolved) == expected
    assert len(scan.resolved) == len(expected)


def test_names_are_kept_as_asked() -> None:
    """The settings keep the categories asked for; extensions get their dot."""
    scan = ScanSettings(extensions=("Video", "phone,heic"), categories=_PHONE)
    assert scan.extensions == ("video", "phone", ".heic")
    assert scan.categories == {"phone": (".heic", ".mp4", ".mov")}
    assert not ScanSettings().resolved


def test_user_categories_from_the_file_and_the_environment(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`[scan.categories]` from config.toml; the variable replaces the whole table."""
    locations.config_file.write_text(
        '[scan]\nextensions = ["phone"]\n'
        '[scan.categories]\nphone = ["heic"]\nweb = ["gif"]\n'
    )
    loaded = load_settings(locations)
    assert loaded.settings.scan.resolved == (".heic",)
    assert loaded.origin_of("scan", "categories") is Origin.FILE
    monkeypatch.setenv("MEDIA_HYGIENE_SCAN__CATEGORIES", '{"phone": ["webp"]}')
    scan = load_settings(locations, {"scan": {"extensions": ["phone"]}}).settings.scan
    assert scan.resolved == (".webp",)
    assert "web" not in scan.categories


@pytest.mark.parametrize("value", ["not json", '["heic"]'])
def test_env_categories_must_be_a_json_object(
    locations: Locations, monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    """A malformed table variable is a configuration error with an example."""
    monkeypatch.setenv("MEDIA_HYGIENE_SCAN__CATEGORIES", value)
    with pytest.raises(ConfigError, match="JSON object"):
        load_settings(locations)


@pytest.mark.parametrize(
    ("categories", "message"),
    [
        ({"photo": ["jxl"]}, "built-in category, it cannot be redefined"),
        ({"web": ["png", "xmp"]}, "sidecars follow"),
        ({"my docs": ["heic"]}, "invalid category name"),
        ({"web": ["photo"]}, "lists extensions, not categories; .* write .photo"),
        ({"web": []}, "lists no extension"),
        ({"png": ["png"]}, "png is an extension"),
    ],
)
def test_invalid_categories_say_how_to_fix_them(
    categories: dict[str, list[str]], message: str
) -> None:
    """Each refusal names the problem and the way out."""
    with pytest.raises(ValueError, match=message):
        ScanSettings.model_validate({"categories": categories})


@pytest.mark.parametrize(
    ("asked", "message"),
    [
        ("photos", "photos: unknown category, did you mean photo\\? .* write .photos"),
        ("phon", "did you mean phone\\?"),
        ("xmp", "sidecars follow"),
        (".raw", "only handles photos and videos"),
    ],
)
def test_close_typos_and_sidecars_are_refused(asked: str, message: str) -> None:
    """`--ext photos` would silently analyse nothing: it is refused."""
    with pytest.raises(ValueError, match=message):
        ScanSettings.model_validate({"categories": _PHONE, "extensions": [asked]})
