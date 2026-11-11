"""Compare a bench's figures with the table kept in `tests/measure/pages-budget.md`.

`python -m tests.measure.pages.budget <bench.json>...` reads the table's rows
(`| route | files | cold ms | warm ms | budget ms |`), then fails (exit 1) on a route
whose warm time grew by more than 30 % against the table, or went past its budget. A
route under 5 ms in the table is not compared on growth: its spread is larger than it.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Final

TABLE: Final = Path(__file__).parents[1] / "pages-budget.md"
GROWTH: Final = 1.30
FLOOR_MS: Final = 5.0
_CELLS: Final = 5


def kept(table: Path) -> dict[tuple[str, int], tuple[float, float]]:
    """The warm figure and budget of each route and size in the table.

    Args:
        table: The Markdown file.

    Returns:
        By (route, files): (warm ms, budget ms).
    """
    rows: dict[tuple[str, int], tuple[float, float]] = {}
    for line in table.read_text(encoding="utf-8").splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != _CELLS or not cells[1].replace(",", "").isdigit():
            continue
        route, files, _, warm, budget = cells
        rows[route.strip("`"), int(files.replace(",", ""))] = (
            float(warm.replace(",", "")),
            float(budget.replace(",", "")),
        )
    return rows


def problems(table: Path, results: list[dict[str, object]]) -> list[str]:
    """What grew past 30 % or past its budget.

    Args:
        table: The Markdown file.
        results: The bench's documents.

    Returns:
        One line per problem.
    """
    rows, said = kept(table), []
    for result in results:
        files = int(str(result["files"]))
        routes = result["routes"]
        assert isinstance(routes, dict)
        for route, figures in routes.items():
            known = rows.get((route, files))
            if known is None:
                continue
            warm = float(figures["warm_ms"])
            before, budget = known
            if warm > budget:
                said.append(f"{route} @ {files}: {warm} ms > budget {budget} ms")
            elif before >= FLOOR_MS and warm > before * GROWTH:
                said.append(f"{route} @ {files}: {warm} ms, was {before} ms (+30 %)")
    return said


def main() -> None:
    """Read the bench files given, print the problems, exit 1 if any."""
    results = [
        json.loads(Path(name).read_text(encoding="utf-8")) for name in sys.argv[1:]
    ]
    said = problems(TABLE, results)
    for line in said:
        print(f"❌ {line}")  # noqa: T201 - the helper's output
    if said:
        sys.exit(1)
    print("✅ every route within its budget and the table's figures + 30 %")  # noqa: T201


if __name__ == "__main__":
    main()
