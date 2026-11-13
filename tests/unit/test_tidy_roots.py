"""`config tidy`: a path rule aimed at a root the index never covered is left alone."""

from __future__ import annotations

import tomllib
from typing import Final

import pytest

from media_hygiene.config.tidy_find import find_stale
from media_hygiene.config.tidy_roots import aimed_root, covered
from media_hygiene.config.tidy_rules import LibraryFacts

FACTS: Final = LibraryFacts(
    paths=(
        r"C:\Photos\Vacances et sorties\Week-end à Dinant 2020\a.jpg",
        r"C:\Photos\2021\b.jpg",
    ),
)


@pytest.mark.parametrize(
    ("pattern", "root"),
    [
        (r"(?i)^D:\\Archives\\Trip", "d:\\archives"),
        (r"^C:\\Photos\\2010\\", "c:\\photos"),
        (r"(?i)C:/Photos/x", "c:\\photos"),
        (r"(?i)week-end dinant", None),
        (r"(?i)^D:\\Arch.*", None),  # no whole first folder named
        (r"(?i)^[CD]:\\Photos\\", None),
        ("", None),
    ],
)
def test_the_root_a_pattern_names(pattern: str, root: str | None) -> None:
    """Only a literal drive and first folder make a root."""
    assert aimed_root(pattern) == root


def test_covered_ignores_case_and_separators() -> None:
    """A file under the root covers it; a sibling folder sharing a prefix does not."""
    assert covered("c:\\photos", (r"C:\PHOTOS\x.jpg",))
    assert covered("c:\\photos", ("C:/Photos/x.jpg",))
    assert not covered("c:\\photos", (r"C:\Photos2\x.jpg",))


def _rule(name: str, pattern: str) -> str:
    return (
        f"[[classify.rules]]\nname = '{name}'\nmatch = 'path'\n"
        f"pattern = '{pattern}'\ncategory = 'Trips'\n"
    )


def test_only_the_rules_aimed_at_covered_roots_are_judged() -> None:
    """A stick never audited: left alone; a folder sorted away or renamed: stale."""
    text = "\n".join(
        (
            _rule("Stick", r"(?i)^E:\\Stick\\Trip"),  # root never indexed
            _rule("Sorted", r"(?i)^C:\\Photos\\Week-end dinant"),  # moved by sort
            _rule("Renamed", r"(?i)Bretagne 2010"),  # no root: judged as before
            _rule("Kept", r"(?i)^C:\\Photos\\2021"),
        )
    )
    found = find_stale(tomllib.loads(text), FACTS, lambda _path: True)
    assert {entry.label for entry in found.stale} == {"Sorted", "Renamed"}
