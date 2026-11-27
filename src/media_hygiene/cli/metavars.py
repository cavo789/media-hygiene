"""One word per kind of value in `--help`: `--prefer FOLDER`, `--port PORT` (0818).

The same word names the same kind of value in every command, in the interface
language (`DOSSIER`, `NOMBRE`...). An option the table does not know keeps the generic
word of `help_types.value_word` (`TEXT`, `NUMBER`, `PATH`); a test fails for a new
option left in that case, and an option that sets its own `metavar` keeps it.
Arguments get theirs the same way, by parameter name (review of 2026-11-27).
"""

from __future__ import annotations

from media_hygiene.i18n import _


def option_words() -> dict[str, str]:
    """The word of each option's value, translated now (the locale is known).

    Returns:
        The word by the option's long name.
    """
    folder, file, name = _("FOLDER"), _("FILE"), _("NAME")
    count, period, pattern = _("COUNT"), _("PERIOD"), _("PATTERN")
    return {
        **dict.fromkeys(
            (
                "--prefer",
                "--protect",
                "--exclude",
                "--backup",
                "--path",
                "--leave",
                "--target",
                "--folder",
                "--to",
                "--imported",
                "--destination",
                "--staging",
                "--photos",
                "--quarantine",
            ),
            folder,
        ),
        **dict.fromkeys(("--decisions", "--workbook", "--carry-over"), file),
        **dict.fromkeys(
            ("--album", "--event", "--rule", "--category", "--phone"), name
        ),
        **dict.fromkeys(("--limit", "--prune", "--sample"), count),
        "--port": _("PORT"),
        "--rating": _("STARS"),
        **dict.fromkeys(("--exclude-name", "--layout"), pattern),
        "--since": period,
        "--year": _("YEAR"),
        "--ext": _("EXTENSIONS"),
        "--search": _("WORDS"),
        "--run": _("RUN"),
        "--seconds": _("SECONDS"),
        "--expect": _("NAMES/IGNORED"),
        "--trial": _("latest|MONTH|FOLDER"),
    }


def argument_words() -> dict[str, str]:
    """The word of each argument's value, translated now.

    Returns:
        The word by the argument's parameter name.
    """
    file = _("FILE")
    return {
        "folder": _("FOLDER"),
        "workbook": file,
        "archive": file,
        "photo": file,
        "name": _("NAME"),
        "run_id": _("RUN"),
        "words": _("WORDS"),
        "step": _("STEP"),
        "action": _("ACTION"),
    }
