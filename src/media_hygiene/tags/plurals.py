"""Simple plurals, made singular so that `bougie` and `bougies` are one tag.

Only the regular cases, and lists of the words that end like a plural without being
one (`ours`, `tapis`, `bus`): a wrong singular would split a tag in two again. A word
left plural is harmless; a word made wrong (`ours` → `our`) is not.
"""

from __future__ import annotations

from typing import Final

from media_hygiene.constants import Locale

_MIN_LENGTH: Final = 4  # shorter words are left as they are: `des`, `bus`, `gas`
_FR_SAME: Final = frozenset(
    {"ours", "corps", "temps", "fils", "pays", "mois", "bois", "repas", "palais"}
    | {"tapis", "souris", "fois", "puits", "colis", "radis", "paradis", "cassis"}
    | {"pois", "rubis", "ananas", "matelas", "cactus", "virus", "campus", "autobus"}
    | {"minibus", "tennis", "anis", "iris", "lilas", "cyprès", "relais", "marais"}
    | {"avis", "bras", "rhinocéros", "albatros", "atlas", "mars", "gris", "frais"}
    | {"épais", "gras", "gros", "clos", "dos", "jus", "express", "succès"}
    | {"anglais", "français", "chinois", "japonais"}
)
# Adjective plurals under four letters inside a phrase: `arbres nus` -> `arbre nu`.
_FR_SHORT: Final = {"nus": "nu"}
_FR_EUX: Final = frozenset(
    {"jeux", "feux", "cheveux", "lieux", "neveux", "vœux", "voeux", "essieux"}
)
_FR_OUX: Final = frozenset(
    {"bijoux", "genoux", "cailloux", "choux", "hiboux", "joujoux", "poux"}
)
_EN_SAME: Final = frozenset(
    {"clothes", "news", "series", "species", "shorts", "jeans", "pants", "stairs"}
    | {"scissors", "sunglasses", "glasses", "goggles", "lens", "christmas", "canvas"}
    | {"bus", "gas", "physics", "mathematics", "athletics", "gymnastics", "chess"}
)
_EN_ES: Final = ("ches", "shes", "xes", "sses", "zes")


def singular(word: str, language: Locale) -> str:
    """The singular of one word, when it is a simple plural.

    Args:
        word: A lower-case word.
        language: Its language.

    Returns:
        The singular, or the word unchanged.
    """
    if language is Locale.FR and word in _FR_SHORT:
        return _FR_SHORT[word]
    if len(word) < _MIN_LENGTH:
        return word
    if language is Locale.FR:
        return _french(word)
    return _english(word)


def _french(word: str) -> str:
    """The singular of a French word.

    Args:
        word: A lower-case word of four letters or more.

    Returns:
        `gâteaux` → `gâteau`, `jeux` → `jeu`, `fleurs` → `fleur`; else unchanged.
    """
    if word in _FR_SAME:
        return word
    if word.endswith("eaux") or word in _FR_EUX or word in _FR_OUX:
        return word[:-1]
    if word.endswith(("x", "z", "ss")):
        return word
    return word.removesuffix("s")


def _english(word: str) -> str:
    """The singular of an English word.

    Args:
        word: A lower-case word of four letters or more.

    Returns:
        `puppies` → `puppy`, `beaches` → `beach`, `candles` → `candle`; else
        unchanged.
    """
    if word in _EN_SAME or word.endswith(("ss", "us", "is")):
        return word
    if word.endswith("ies") and len(word) > _MIN_LENGTH:
        return word[:-3] + "y"
    if word.endswith(_EN_ES):
        return word[:-2]
    return word.removesuffix("s")
