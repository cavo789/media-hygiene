"""Extension categories: built-in names, the user's own, and how `--ext` reads them."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from media_hygiene.config.loader import Origin, load_settings
from media_hygiene.config.settings import ScanSettings
from media_hygiene.constants import (
    IMAGE_EXTENSIONS,
    MEDIA_EXTENSIONS,
    RAW_EXTENSIONS,
    VIDEO_EXTENSIONS,
)
from media_hygiene.errors import ConfigError

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations

_DOCUMENTS: dict[str, tuple[str, ...]] = {"documents": ("pdf", "DOCX", ".txt")}


@pytest.mark.parametrize(
    ("asked", "expected"),
    [
        ("video", VIDEO_EXTENSIONS),
        ("photo,raw", IMAGE_EXTENSIONS | RAW_EXTENSIONS),
        ("media", MEDIA_EXTENSIONS),
        ("pdf", {".pdf"}),
        (".raw", {".raw"}),
        ("RAF,rar", {".raf", ".rar"}),
    ],
)
def test_builtin_categories_and_extensions(asked: str, expected: set[str]) -> None:
    """Dotless: a category when one has that name, else an extension; dotted: one."""
    scan = ScanSettings(extensions=(asked,))
    assert set(scan.resolved) == expected
    assert len(scan.resolved) == len(expected)


def test_names_are_kept_as_asked() -> None:
    """The settings keep the categories asked for; extensions get their dot."""
    scan = ScanSettings(extensions=("Video", "documents,pdf"), categories=_DOCUMENTS)
    assert scan.extensions == ("video", "documents", ".pdf")
    assert scan.categories == {"documents": (".pdf", ".docx", ".txt")}
    assert scan.other_files == (".pdf", ".docx", ".txt")
    assert not ScanSettings().resolved


def test_user_categories_from_the_file_and_the_environment(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`[scan.categories]` from config.toml; the variable replaces the whole table."""
    locations.config_file.write_text(
        '[scan]\nextensions = ["documents"]\n'
        '[scan.categories]\ndocuments = ["pdf"]\nweb = ["svg"]\n'
    )
    loaded = load_settings(locations)
    assert loaded.settings.scan.resolved == (".pdf",)
    assert loaded.origin_of("scan", "categories") is Origin.FILE
    monkeypatch.setenv("MEDIA_HYGIENE_SCAN__CATEGORIES", '{"documents": ["odt"]}')
    scan = load_settings(
        locations, {"scan": {"extensions": ["documents"]}}
    ).settings.scan
    assert scan.resolved == (".odt",)
    assert "web" not in scan.categories


@pytest.mark.parametrize("value", ["not json", '["pdf"]'])
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
        ({"my docs": ["pdf"]}, "invalid category name"),
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
        ("document", "did you mean documents\\?"),
        ("xmp", "sidecars follow"),
    ],
)
def test_close_typos_and_sidecars_are_refused(asked: str, message: str) -> None:
    """`--ext photos` would silently analyse nothing: it is refused."""
    with pytest.raises(ValueError, match=message):
        ScanSettings.model_validate({"categories": _DOCUMENTS, "extensions": [asked]})
