"""The story the documentation tells, run for real: every capture and screenshot."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from tests.support.docs.browsing import places_story, served_pages
from tests.support.docs.container import (
    Command,
    list_files,
    read_file,
    run,
    run_confirmed,
    run_in_colour,
)
from tests.support.docs.names import Locale
from tests.support.docs.people_story import PEOPLE_CAPTURES, people_story
from tests.support.docs.published import as_published
from tests.support.docs.screenshots import Job, shoot
from tests.support.docs.terminal import Window, draw_terminal

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from tests.support.docs.container import Demo

type Captures = dict[str, str]

COMMANDS: Final = ("audit", "review", "clean", "undo", "history", "reports", "purge")
COMMANDS_TOO: Final = ("crosscheck", "config", "classify", "sort", "album", "inventory",
                       "places", "status", "launcher", "review-sort", "tags", "search",
                       "people", "xmp")  # fmt: skip
_WINDOWS: Final[Mapping[Locale, Window]] = {
    Locale.EN: Window("Audit summary", "'clean'", "media-hygiene audit"),
    Locale.FR: Window(
        "Résumé de l'audit", "'clean'", "media-hygiene --locale fr audit"
    ),
}
_CSV_LINES: Final = 6
# Every capture the scenario produces: the documentation's markers may name these only.
CAPTURES: Final = frozenset(
    {
        "audit-photos.txt",
        "config-first.txt",
        "config.txt",
        "config.toml",
        "audit.txt",
        "audit-prefer.txt",
        "audit-exclude.txt",
        "audit-ext.txt",
        "classify.txt",
        "inventory.txt",
        "crosscheck.txt",
        "review.txt",
        "review-near.txt",
        "decisions.json",
        "clean.txt",
        "undo.txt",
        "clean-near.txt",
        "history.txt",
        "reports.txt",
        "quarantine.txt",
        "plan-csv.txt",
        "purge.txt",
        "sort.txt",
        "undo-sort.txt",
        "help.txt",
        *(f"help-{command}.txt" for command in (*COMMANDS, *COMMANDS_TOO)),
        *PEOPLE_CAPTURES,
    }
)


def _audits(demo: Demo) -> Captures:
    """The first audit on one folder, the configuration, then audits with options."""
    names = demo.library.names
    captures = {
        "audit-photos.txt": run(demo, Command(("audit",), photos_only=True)),
        "config-first.txt": run(demo, Command(("config",))),
        "config.txt": run(demo, Command(("config",))),
        "config.toml": read_file(demo, "config", "config.toml"),
        "audit.txt": run(demo, Command(("audit",))),
    }
    prefer = ("audit", "--prefer", f"C:\\Photos\\{names.old_phone}")
    captures["audit-prefer.txt"] = run(demo, Command(prefer))
    exclude = ("audit", "--exclude", f"D:\\{names.old_disk}")
    captures["audit-exclude.txt"] = run(demo, Command(exclude))
    captures["audit-ext.txt"] = run(demo, Command(("audit", "--ext", "heic,video")))
    captures["classify.txt"] = run(demo, Command(("classify",)))
    captures["inventory.txt"] = run(demo, Command(("inventory",)))
    return captures


def _crosscheck(demo: Demo) -> Captures:
    """The second opinion: `crosscheck` runs Czkawka itself, then compares."""
    return {"crosscheck.txt": run(demo, Command(("crosscheck",)))}


def _clean(demo: Demo) -> Captures:
    """Clean, undo, clean again with near duplicates and the review's decisions."""
    clean = Command(("clean",), read_only=False)
    choices = ("--decisions", "decisions.json")
    near = Command(("clean", "--tier", "near-all", *choices), read_only=False)
    captures = {
        "clean.txt": run_confirmed(demo, clean),
        "undo.txt": run(demo, Command(("undo",), read_only=False)),
        "clean-near.txt": run_confirmed(demo, near),
        "history.txt": run(demo, Command(("history",))),
        "reports.txt": run(demo, Command(("reports",))),
    }
    captures["quarantine.txt"] = "\n".join(list_files(demo, "quarantine")) + "\n"
    return captures


def _reports(demo: Demo, shots: Path) -> Captures:
    """The pages of the first audit, the last clean and the classify; the CSV."""
    files = list_files(demo, "reports")
    folders = sorted({path.split("/")[1] for path in files if path.count("/") > 1})
    audit = next(folder for folder in folders if folder.endswith("-audit"))
    clean = [folder for folder in folders if folder.endswith("-clean")][-1]
    classify = next(folder for folder in folders if folder.endswith("-classify"))
    shoot(demo, Job("none", ("reports", audit, clean, classify)), shots)
    # The byte order mark tells Excel the file is UTF-8; the documentation needs none.
    csv = read_file(demo, "reports", f"{audit}/plan.csv").lstrip("\ufeff").splitlines()
    return {"plan-csv.txt": "\n".join(csv[:_CSV_LINES]) + "\n"}


def _terminal(demo: Demo, shots: Path) -> None:
    """The audit in colour, drawn as a terminal window for the READMEs."""
    ansi = run_in_colour(demo, Command(("audit",)))
    svg = draw_terminal(ansi, _WINDOWS[demo.locale])
    (shots / "terminal-audit.svg").write_text(svg, encoding="utf-8")
    shoot(demo, Job("none", ("terminal", "terminal-audit")), shots)
    (shots / "terminal-audit.svg").unlink()


def _help(demo: Demo) -> Captures:
    """The built-in help of the tool and of each command."""
    captures = {"help.txt": run(demo, Command(("--help",)))}
    for command in (*COMMANDS, *COMMANDS_TOO):
        captures[f"help-{command}.txt"] = run(demo, Command((command, "--help")))
    return captures


def _sort(demo: Demo) -> Captures:
    """Classify the cleaned library, sort it as proposed, then undo the sort."""
    run(demo, Command(("classify",)))
    return {
        "sort.txt": run_confirmed(demo, Command(("sort",), read_only=False)),
        "undo-sort.txt": run(demo, Command(("undo",), read_only=False)),
    }


def run_scenario(demo: Demo, shots: Path) -> Captures:
    """Play the whole story on freshly seeded volumes, in the documentation's order.

    Args:
        demo: The seeded demo library of one language.
        shots: Where the screenshots land (PNG).

    Returns:
        Every console capture, by name, its suggested commands as published.
    """
    captures = _audits(demo)
    _terminal(demo, shots)
    captures |= _crosscheck(demo)
    captures |= served_pages(demo, shots)
    captures |= _clean(demo)
    captures |= _reports(demo, shots)
    captures |= _help(demo)
    captures["purge.txt"] = run_confirmed(demo, Command(("purge",), read_only=False))
    captures |= people_story(demo, shots)
    captures |= _sort(demo)
    places_story(demo, shots)
    return {name: as_published(demo, text) for name, text in captures.items()}
