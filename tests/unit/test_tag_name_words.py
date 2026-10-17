"""The words of the file name: chosen names give words, generated ones give none."""

from __future__ import annotations

from pathlib import Path

import pytest

from media_hygiene.classify.models import MediaInput
from media_hygiene.config.settings import KeepSettings, Settings
from media_hygiene.config.tags_settings import TagSettings
from media_hygiene.constants import Locale
from media_hygiene.name_patterns import GENERATED_NAMES
from media_hygiene.tags.context import TagContext, tag_context
from media_hygiene.tags.models import Tag, TagSource
from media_hygiene.tags.normalize import WordRules
from media_hygiene.tags.producers import cheap_tags, name_words

ROOT = Path("/data/c/Photos")
# One name per pattern of `GENERATED_NAMES`, in the same order.
GENERATED: tuple[str, ...] = (
    "IMG_1234.jpg",
    "IMG_20190712_143000_1.jpg",
    "VID-20190712-WA0001.mp4",
    "_MG_0042.CR2",
    "P1000042.JPG",
    "PXL_20230101_120000123.jpg",
    "20190712_143000.jpg",
    "2019-07-12 14.30.00.jpg",
    "GOPR0042.MP4",
    "DJI_0042.JPG",
    "FB_IMG_1562938400.jpg",
    "Screenshot_2019-07-12-14-30-00.png",
    "image42.png",
    "0b8f4a52-9c1e-4f0e-8d33-2a6f3e4b9c10.jpg",
    "a3f9c2e1b4d5f6a7.jpg",
    "162.mp4",
)


def context(settings: Settings | None = None) -> TagContext:
    """The producers' context, words in French."""
    tags = TagSettings(language="fr")
    return tag_context(settings or Settings(), WordRules.of(tags, Locale.EN))


def media(relative: str) -> MediaInput:
    """A file below the root, without facts."""
    return MediaInput(ROOT / relative, ROOT, 10, 1)


def test_one_example_per_generated_pattern() -> None:
    """The examples cover every pattern of the keep policy."""
    assert len(GENERATED) == len(GENERATED_NAMES)


@pytest.mark.parametrize("name", GENERATED)
def test_a_generated_name_gives_no_word(name: str) -> None:
    """`IMG_1234.jpg`, `VID-…-WA0001.mp4`, a bare number: nothing to search for."""
    assert not name_words(media(f"Vacances/{name}"), context())


@pytest.mark.parametrize(
    ("name", "words"),
    [
        ("Anniversaire Léa.mp4", ("Anniversaire", "Léa")),
        ("2019-07-12 Plage (petite).jpg", ("Plage", "petite")),
        ("Anniversaire Léa (1).jpg", ("Anniversaire", "Léa")),
        (
            "Saint-Nicolas_chez_les_grands-parents.jpg",
            ("Saint-Nicolas", "grands-parents"),
        ),
        ("Juillet 2019 - le lac.jpg", ("lac",)),
        ("photo du 12.jpg", ()),
        ("IMG_1234 Anniversaire Léa.jpg", ("Anniversaire", "Léa")),
        ("VID-20190712-WA0001 Plage.mp4", ("Plage",)),
        ("Ski GOPR0042 DSC_7.jpg", ("Ski",)),
        ("IMG_plage_0.jpg", ("plage",)),
    ],
)
def test_a_chosen_name_gives_its_words(name: str, words: tuple[str, ...]) -> None:
    """Split like the folders; no date, number, month, link word, generated start."""
    assert name_words(media(name), context()) == words


def test_the_generated_names_come_from_keep() -> None:
    """A pattern added to `[keep] generated_names` silences those names too."""
    keep = KeepSettings(generated_names=(r"Scan \d+",))
    settings = Settings(keep=keep)
    assert name_words(media("Scan 12.jpg"), context()) == ("Scan",)
    assert not name_words(media("Scan 12.jpg"), context(settings))


def test_cheap_tags_carry_the_name_words() -> None:
    """`Vidéos/Anniversaire.mp4`: the folder says nothing, the name does."""
    tags = cheap_tags(media("Vidéos/Anniversaire.mp4"), context())
    assert tags == (Tag(TagSource.NAME, "Anniversaire"),)
