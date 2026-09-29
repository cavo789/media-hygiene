"""Folder names: a date only, a meaning to keep, or the tool's own band folders."""

from __future__ import annotations

from pathlib import Path

import pytest

from media_hygiene.classify.folders import FolderRules
from media_hygiene.classify.layout import Values, check_layout, render, safe_name

ROOT = Path("/data/c/Photos")
RULES = FolderRules.build((r"DCIM",), ("Mes photos triées",))


@pytest.mark.parametrize(
    "name",
    [
        "2017",
        "2019-04",
        "Juillet 2017",
        "July 2017",
        "juli 2017",
        "2017 juillet",
        "Décembre",
        "DCIM",
        "To check",
        "À trier",
        "2016-07-14",
        "2016-07-01..07-15",
    ],
)
def test_date_only_and_generic_names_say_nothing(name: str) -> None:
    """Years, months in fr/en/nl, device and band folders are not meanings."""
    assert RULES.label(name) is None


@pytest.mark.parametrize(
    ("name", "label"),
    [
        ("Mars 2005 - Travaux maison", "Travaux maison"),
        ("Décembre 2003 - Saint-Nicolas", "Saint-Nicolas"),
        ("2019 \u2013 Vacances", "Vacances"),
        ("Kermesse", "Kermesse"),
    ],
)
def test_meaningful_names_are_kept(name: str, label: str) -> None:
    """`Mois AAAA - Label` gives its label; any other name is a meaning."""
    assert RULES.label(name) == label


def test_the_meaning_of_a_folder_keeps_its_sub_folders() -> None:
    """`2017/Janvier 2017/Bruges/Jour 1` means `Bruges/Jour 1`."""
    folder = ROOT / "2017" / "Janvier 2017" / "Bruges" / "Jour 1"
    assert RULES.meaning(folder, ROOT) == ("Bruges", "Jour 1")


def test_under_to_check_nothing_is_a_meaning_under_to_sort_a_name_is() -> None:
    """The tool's guesses never stick; a name the user gave in "to sort" does."""
    assert not RULES.meaning(ROOT / "2016" / "To check" / "Vacances", ROOT)
    assert not RULES.meaning(ROOT / "2016" / "À trier" / "2016-07-14", ROOT)
    assert RULES.meaning(ROOT / "2016" / "À trier" / "Kermesse", ROOT) == ("Kermesse",)


def test_folders_give_a_year_and_a_month() -> None:
    """The innermost dated folder wins."""
    assert RULES.year_month(ROOT / "2016" / "Juillet 2016") == (2016, 7)
    assert RULES.year_month(ROOT / "2019") == (2019, None)
    assert RULES.year_month(ROOT / "Mars 2005 - Travaux maison") == (2005, 3)
    assert RULES.year_month(ROOT / "Kermesse") is None


def test_layouts_render_and_leave_empty_segments_out() -> None:
    """`{place}` without positions leaves no empty folder; an empty layout stays."""
    values = Values(2016, 7, 14, category="Vacances", event="2016-07-14")
    assert render("{year}/{category}", values) == "2016/Vacances"
    assert render("{year}/Q{quarter}/{place}", values) == "2016/Q3"
    assert render("{year}/{month} - {month_name}", values) == "2016/07 - July"
    assert render("", values) is None


def test_an_unknown_placeholder_is_refused_with_the_allowed_list() -> None:
    """A typo is caught when the configuration loads."""
    with pytest.raises(ValueError, match=r"\{catgory\}.*allowed: .*\{category\}"):
        check_layout("{year}/{catgory}")
    with pytest.raises(ValueError, match="Windows"):
        check_layout("{year}/What?")


@pytest.mark.parametrize(
    ("name", "safe"),
    [("a:b", "a_b"), ("Fin. ", "Fin"), ("CON", "CON_"), ("été", "été")],
)
def test_names_windows_accepts(name: str, safe: str) -> None:
    """Forbidden characters, trailing dots, device names; NFC."""
    assert safe_name(name) == safe
