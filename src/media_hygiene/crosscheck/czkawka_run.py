"""Run Czkawka in place: `czkawka_cli` ships in the image, beside media-hygiene.

It reads the same paths as the audit, with its own code and its own hash: only the
packaging is shared. Its results are written under a temporary name, then renamed: a
run stopped halfway never leaves a results file that `crosscheck` would compare.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.errors import CrossCheckError
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.crosscheck.czkawka import CzkawkaScope

_PARTIAL_SUFFIX: Final = ".part"
_NO_CACHE: Final = "-H"  # Czkawka's `--disable-cache`: every file hashed again
_CONFIG_VARIABLE: Final = "XDG_CONFIG_HOME"
_CACHE_VARIABLE: Final = "XDG_CACHE_HOME"  # Czkawka keeps it in <this>/czkawka


@dataclass(frozen=True, slots=True)
class CzkawkaRun:
    """How to run Czkawka here: the executable, its results file and its cache."""

    executable: str
    results: Path
    cache_dir: Path | None = None  # None: nothing kept between two runs
    fresh: bool = False  # ignore the cache: every file is read and hashed again


def run_czkawka(scope: CzkawkaScope, run: CzkawkaRun) -> None:
    """Run Czkawka on what media-hygiene analyses, its progress on the terminal.

    Ctrl+C or `docker stop` stops it too: `subprocess.run` kills it before the
    interruption goes on.

    Args:
        scope: The folder, extensions and exclusions of the audit.
        run: The executable, where its results and its cache go.

    Raises:
        CrossCheckError: Czkawka could not start, failed, or wrote no results.
    """
    partial = run.results.with_name(run.results.name + _PARTIAL_SUFFIX)
    arguments = scope.arguments(str(partial))
    if run.fresh:
        arguments = (*arguments, _NO_CACHE)
    with tempfile.TemporaryDirectory(prefix="czkawka-") as scratch:
        environment = {
            **os.environ,
            _CONFIG_VARIABLE: scratch,  # never /config: it holds config.toml only
            _CACHE_VARIABLE: str(run.cache_dir or scratch),
        }
        try:
            # The executable found on PATH and arguments built here, no shell.
            done = subprocess.run(  # noqa: S603
                (run.executable, *arguments), env=environment, check=False
            )
        except OSError as exc:
            raise CrossCheckError(
                _("Czkawka could not start: {reason}.").format(reason=exc.strerror),
                _("Run 'crosscheck --print-command' to run Czkawka yourself."),
            ) from exc
    if done.returncode != 0 or not partial.is_file():
        partial.unlink(missing_ok=True)
        raise CrossCheckError(
            _("Czkawka stopped with exit code {code}: no second opinion.").format(
                code=done.returncode
            ),
            _(
                "Its messages are above. Run 'crosscheck' again, or "
                "'crosscheck --print-command' to run Czkawka yourself."
            ),
        )
    partial.replace(run.results)
