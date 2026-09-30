"""What folder names say: a date only (generic), or a meaning worth keeping.

`2017/Juillet 2017` says nothing but a date; `Mars 2005 - Travaux maison` says
`Travaux maison`; `2017/Janvier 2017/Bruges` says `Bruges`. The tool's own band folders
(`To check`, `À trier`…) never count as a meaning, in both languages.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.plan.name_rules import compile_patterns

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

MONTHS: Final = (
    ("janvier", "january", "januari", "jan"),
    ("février", "fevrier", "february", "februari", "feb", "fév", "fev"),
    ("mars", "march", "maart", "mar"),
    ("avril", "april", "apr", "avr"),
    ("mai", "may", "mei"),
    ("juin", "june", "juni", "jun"),
    ("juillet", "july", "juli", "jul", "juil"),
    ("août", "aout", "august", "augustus", "aug"),
    ("septembre", "september", "sep", "sept"),
    ("octobre", "october", "oktober", "oct", "okt"),
    ("novembre", "november", "nov"),
    ("décembre", "decembre", "december", "dec", "déc"),
)
_MONTH: Final = "|".join(name for names in MONTHS for name in names)
_YEAR: Final = r"(?P<year>(?:19|20)\d{2})"
DATE_FOLDERS: Final = (
    _YEAR,
    rf"{_YEAR}[-_. ](?P<month>\d{{1,2}})",
    rf"(?P<month_name>{_MONTH})\.?[ _-]*{_YEAR}",
    rf"{_YEAR}[ _-]*(?P<month_name>{_MONTH})",
    rf"(?P<month_name>{_MONTH})",
    rf"{_YEAR}-\d{{2}}-\d{{2}}(?:\.\.[\d-]+)?",  # an event span `sort` wrote
)
# "Mois AAAA - Label": the label is the meaning.
_LABELLED: Final = re.compile(
    rf"(?:(?:{_MONTH})\.?[ _-]*)?{_YEAR}(?:\s+[-\u2013]\s+|\s*:\s*)(?P<label>.+)",
    re.IGNORECASE,
)
UNSURE_FOLDERS: Final = frozenset({"to check", "à vérifier"})
BAND_FOLDERS: Final = frozenset(
    {"to sort", "undated", "received and downloaded"}
    | {"à trier", "sans date", "reçues et téléchargées"}
    | UNSURE_FOLDERS
)


@dataclass(frozen=True, slots=True)
class FolderRules:
    """Which folder names are generic: date-only, device, band folders."""

    generic: tuple[re.Pattern[str], ...]
    dates: tuple[re.Pattern[str], ...]
    bands: frozenset[str] = BAND_FOLDERS
    unsure: frozenset[str] = UNSURE_FOLDERS  # the "to check" band folders

    @classmethod
    def build(
        cls, generic: Iterable[str], bands: tuple[Iterable[str], Iterable[str]]
    ) -> FolderRules:
        """Compile the generic names of `[keep]` and `[classify]`, and the band names.

        Args:
            generic: Extra generic folder patterns.
            bands: The folder names the configured layouts write, then those only the
                "to check" layout writes.

        Returns:
            The rules.
        """
        every, unsure = bands
        folded = frozenset(name.casefold() for name in every) | BAND_FOLDERS
        checked = frozenset(name.casefold() for name in unsure) | UNSURE_FOLDERS
        return cls(
            compile_patterns(generic), compile_patterns(DATE_FOLDERS), folded, checked
        )

    def label(self, name: str) -> str | None:
        """The meaning of one folder name.

        Args:
            name: A folder name.

        Returns:
            The label to keep, or None when the name is generic.
        """
        if name.casefold() in self.bands:
            return None
        if any(p.fullmatch(name) for p in (*self.dates, *self.generic)):
            return None
        labelled = _LABELLED.fullmatch(name.strip())
        if labelled:
            return labelled["label"].strip() or None
        return name

    def meaning(self, folder: Path, root: Path) -> tuple[str, ...]:
        """The meaningful part of a folder, below a root.

        The names below a "to check" band folder are the tool's own guesses: never a
        meaning. Below "to sort", a name the user gave is one (a date is not).

        Args:
            folder: The folder of a file.
            root: The mounted folder or target root it lies in.

        Returns:
            The labels, outermost first; empty for a date-only or generic folder.
        """
        parts = folder.relative_to(root).parts if folder.is_relative_to(root) else ()
        labels: list[str] = []
        for name in parts:
            if name.casefold() in self.unsure:
                return ()
            label = self.label(name)
            if label is not None:
                labels.append(label)
        return tuple(labels)

    def guess(self, folder: Path, root: Path) -> str | None:
        """The category a file was guessed and sorted into, "to check".

        Args:
            folder: The folder of a file.
            root: The mounted folder or target root it lies in.

        Returns:
            The folders below the "to check" band folder (`Vacances`), or None when the
            file is not in one.
        """
        parts = folder.relative_to(root).parts if folder.is_relative_to(root) else ()
        for index, name in enumerate(parts):
            if name.casefold() in self.unsure:
                return "/".join(parts[index + 1 :]) or None
        return None

    def year_month(self, folder: Path) -> tuple[int, int | None] | None:
        """The date a folder name gives, the innermost one first.

        Args:
            folder: The folder of a file.

        Returns:
            Year and month (None when only the year), or None.
        """
        for name in reversed(folder.parts):
            for pattern in self.dates:
                found = pattern.fullmatch(name)
                if found and found.groupdict().get("year"):
                    return int(found["year"]), _month_of(found)
            labelled = _LABELLED.fullmatch(name)
            if labelled:
                return int(labelled["year"]), _month_in(name)
        return None


def _month_of(found: re.Match[str]) -> int | None:
    """The month of a date-folder match.

    Args:
        found: The match.

    Returns:
        1 to 12, or None.
    """
    groups = found.groupdict()
    if groups.get("month"):
        month = int(groups["month"])
        return month if 1 <= month <= len(MONTHS) else None
    return _month_in(groups.get("month_name") or "")


def _month_in(text: str) -> int | None:
    """Find a month name at the start of a text.

    Args:
        text: A folder name.

    Returns:
        1 to 12, or None.
    """
    word = re.split(r"[\s._-]+", text.strip().casefold(), maxsplit=1)[0]
    for index, names in enumerate(MONTHS, 1):
        if word in names:
            return index
    return None
