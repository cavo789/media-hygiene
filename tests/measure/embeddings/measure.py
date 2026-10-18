"""TODO 0220: compare image embedding models on N photos and the maintainer's searches.

Each model runs in a process of its own (its RAM peak is its own); the photos are only
read. The pages it writes (`pages.py`) show, per search, the best pictures of each model
side by side, and the closest pairs the audit does not already call near duplicates.

    python -m embeddings.measure --photos /data/c/Photos --queries /out/queries.txt
        --models-dir /models --out /out --count 1000 --cpus 4

(one line in the shell)
"""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path
from typing import TYPE_CHECKING, Final

from .models import SPECS, fetch
from .pages import write_pages
from .ranking import Bench, ranked, search_hits
from .runs import Job, ModelRun, read_queries, run_job, sample

if TYPE_CHECKING:
    from collections.abc import Sequence

_DEFAULT_COUNT: Final = 1000
_DEFAULT_SEED: Final = 20261017
_DEFAULT_CPUS: Final = 4
_DEFAULT_MODELS: Final = ",".join(SPECS)
_DEFAULT_INDEX: Final = Path("/cache/index.sqlite")


def _arguments(argv: Sequence[str] | None) -> argparse.Namespace:
    """Read the command line.

    Args:
        argv: The arguments, None for the process's own.

    Returns:
        The options.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--photos", type=Path, required=True, help="folder of photos (read only)"
    )
    parser.add_argument(
        "--queries", type=Path, required=True, help="searches, one per line"
    )
    parser.add_argument(
        "--models-dir", type=Path, required=True, help="downloads, kept"
    )
    parser.add_argument("--out", type=Path, required=True, help="folder of the pages")
    parser.add_argument(
        "--count", type=int, default=_DEFAULT_COUNT, help="photos to sample"
    )
    parser.add_argument(
        "--seed", type=int, default=_DEFAULT_SEED, help="seed of the draw"
    )
    parser.add_argument(
        "--cpus", type=int, default=_DEFAULT_CPUS, help="threads per model"
    )
    parser.add_argument(
        "--models", default=_DEFAULT_MODELS, help="names, comma separated"
    )
    parser.add_argument(
        "--index", type=Path, default=_DEFAULT_INDEX, help="index, if any"
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the bench, write its pages.

    Args:
        argv: The arguments, None for the process's own.

    Returns:
        The exit code.
    """
    options = _arguments(argv)
    photos = sample(options.photos, options.count, options.seed)
    queries = read_queries(options.queries)
    names = tuple(name.strip() for name in options.models.split(",") if name.strip())
    sys.stdout.write(f"{len(photos)} photos, {len(queries)} searches, models {names}\n")
    runs: list[ModelRun] = []
    for name in names:
        for remote in SPECS[name].remotes if name in SPECS else ():
            fetch(remote, options.models_dir)
        job = Job(name, options.models_dir, photos, queries, options.cpus)
        with ProcessPoolExecutor(1, mp_context=get_context("spawn")) as pool:
            run = pool.submit(run_job, job).result()
        sys.stdout.write(f"{name}: {run.timing}\n")
        runs.append(run)
    bench = Bench(
        photos, queries, tuple(runs), search_hits(options.index, queries, photos)
    )
    written = write_pages(ranked(bench), options.out)
    sys.stdout.write(f"Pages written: {written}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
