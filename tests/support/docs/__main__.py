"""`python -m tests.support.docs [en] [fr]`: refresh the screenshots and outputs.

Needs Docker and the `media-hygiene:latest` image (the `docs_screenshots` helper builds
it). Work files live in the system's temporary folder; only `documentation/` changes.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path
from typing import Final

from rich.console import Console

from tests.support.docs.container import Demo, remove, seed
from tests.support.docs.images import publish
from tests.support.docs.library import build_library
from tests.support.docs.names import Locale
from tests.support.docs.pages import refresh
from tests.support.docs.scenario import run_scenario
from tests.support.docs.screenshots import build_browser

DOCUMENTATION: Final = Path(__file__).resolve().parents[3] / "documentation"
console = Console()
USAGE: Final = (
    "Usage: docs_screenshots [LANGUAGE...]\n"
    f"  No language: every one ({' '.join(str(locale) for locale in Locale)}),"
    " one after the other.\n"
    "  docs_screenshots fr   only the French pages."
)


def document(locale: Locale, work: Path) -> None:
    """Build the demo library of a language, play the story, refresh its documentation.

    Args:
        locale: The language.
        work: A scratch folder of its own.
    """
    console.print(f"🧪 [bold]{locale}[/]: drawing the demo library…")
    demo = Demo(build_library(locale, work / "data"), locale)
    seed(demo)
    shots = work / "shots"
    shots.mkdir()
    console.print(f"🐳 [bold]{locale}[/]: running the image and the browser…")
    captures = run_scenario(demo, shots)
    target = DOCUMENTATION / locale
    images = publish(shots, target / "images")
    for page in sorted(target.rglob("*.md")):
        refresh(page, captures)
    remove(demo)
    console.print(
        f"✅ [bold]{locale}[/]: {len(images)} screenshots, {len(captures)} captures"
    )


def main() -> None:
    """Refresh the languages given on the command line, every language by default.

    Raises:
        SystemExit: A language this tool does not know (code 2), with the usage.
    """
    arguments = sys.argv[1:]
    if {"-h", "--help"} & set(arguments):
        console.print(USAGE)
        return
    known = {str(locale) for locale in Locale}
    unknown = [argument for argument in arguments if argument not in known]
    if unknown:
        console.print(f"❌ Unknown language: {', '.join(unknown)}\n\n{USAGE}")
        raise SystemExit(2)
    locales = [Locale(argument) for argument in arguments] or list(Locale)
    root = Path(tempfile.gettempdir()) / "media-hygiene-docs"
    console.print("🌐 Preparing the browser image…")
    build_browser()
    for locale in locales:
        work = root / locale
        shutil.rmtree(work, ignore_errors=True)
        work.mkdir(parents=True)
        document(locale, work)
    console.print(
        "📝 Review the changes with 'git diff documentation/', then run 'check'."
    )


if __name__ == "__main__":
    main()
