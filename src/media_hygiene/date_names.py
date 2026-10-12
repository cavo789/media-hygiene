"""Folder names that say only a date: `2018`, `2018-07`, `Juillet 2018`, `July`.

Shared by the choice of the kept copy (such a folder says nothing a photo's date does
not) and by `classify` (it is no meaning to keep). Month names in French, English and
Dutch, full and short.
"""

from __future__ import annotations

from typing import Final

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
MONTH: Final = "|".join(name for names in MONTHS for name in names)
YEAR: Final = r"(?P<year>(?:19|20)\d{2})"
DATE_FOLDERS: Final = (
    YEAR,
    rf"{YEAR}[-_. ](?P<month>\d{{1,2}})",
    rf"(?P<month_name>{MONTH})\.?[ _-]*{YEAR}",
    rf"{YEAR}[ _-]*(?P<month_name>{MONTH})",
    rf"(?P<month_name>{MONTH})",
    rf"{YEAR}-\d{{2}}-\d{{2}}(?:\.\.[\d-]+)?",  # an event span `sort` wrote
)
