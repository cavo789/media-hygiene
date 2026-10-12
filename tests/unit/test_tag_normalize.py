"""The words of a vision model, made stable: case, plurals, stop words, duplicates."""

from __future__ import annotations

from datetime import date

import pytest

from media_hygiene.config.tags_settings import TagSettings
from media_hygiene.constants import Locale
from media_hygiene.tags.normalize import WordRules, normalize
from media_hygiene.tags.plurals import singular
from media_hygiene.tags.vocabulary import easter_sunday, is_easter

FRENCH = WordRules.of(TagSettings(language="fr"), Locale.EN)
ENGLISH = WordRules.of(TagSettings(), Locale.EN)


def test_the_measured_faults_are_fixed() -> None:
    """Plural, case, split phrase, stop words, short words, edges, repeats."""
    words = ["Bougies", "bougie", "salle à manger", "à", "Sol", "mur", "  Fleurs. "]
    assert normalize(words, FRENCH) == ("bougie", "salle à manger", "fleur")


@pytest.mark.parametrize(
    ("word", "expected"),
    [
        ("gâteaux", "gâteau"),
        ("jeux", "jeu"),
        ("bijoux", "bijou"),
        ("chevaux", "chevaux"),  # left plural: never made wrong
        ("ours", "ours"),
        ("tapis", "tapis"),
        ("skis", "ski"),
        ("nez", "nez"),
        ("bus", "bus"),
        ("express", "express"),
    ],
)
def test_french_singulars(word: str, expected: str) -> None:
    """Simple plurals only; words ending like one stay as they are."""
    assert singular(word, Locale.FR) == expected


@pytest.mark.parametrize(
    ("word", "expected"),
    [
        ("candles", "candle"),
        ("puppies", "puppy"),
        ("beaches", "beach"),
        ("glasses", "glasses"),
        ("grass", "grass"),
        ("cactus", "cactus"),
        ("toys", "toy"),
    ],
)
def test_english_singulars(word: str, expected: str) -> None:
    """The regular English plurals."""
    assert singular(word, Locale.EN) == expected


def test_the_language_follows_the_interface_unless_set() -> None:
    """Empty: the interface's; set: that one, whatever the interface."""
    assert ENGLISH.language is Locale.EN
    assert WordRules.of(TagSettings(), Locale.FR).language is Locale.FR
    assert FRENCH.language is Locale.FR


def test_phrases_stay_whole_and_singular() -> None:
    """Each word of a phrase is made singular; the phrase stays one tag."""
    assert normalize(["Birthday Candles", "birthday candle"], ENGLISH) == (
        "birthday candle",
    )


def test_own_stop_words_replace_the_list() -> None:
    """A configured list replaces the built-in one, case ignored."""
    rules = WordRules.of(TagSettings(stop_words=("Chat",)), Locale.FR)
    assert normalize(["chat", "mur", "123"], rules) == ("mur",)


@pytest.mark.parametrize(
    ("year", "sunday"),
    [(2007, date(2007, 4, 8)), (2024, date(2024, 3, 31)), (2025, date(2025, 4, 20))],
)
def test_easter_sunday(year: int, sunday: date) -> None:
    """The Gregorian computus, on known years."""
    assert easter_sunday(year) == sunday


def test_easter_is_sunday_and_monday() -> None:
    """Two days, not the Saturday before nor the Tuesday after."""
    assert is_easter(date(2007, 4, 8))
    assert is_easter(date(2007, 4, 9))
    assert not is_easter(date(2007, 4, 7))
    assert not is_easter(date(2007, 4, 10))
