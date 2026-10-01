"""A decisions file rewritten by PowerShell 5.1 still works for clean and review."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from tests.integration.test_burst_review import DEMO_ROOTS, shots
from tests.support.cli import run
from tests.support.review import BURST_HOST, review_session, write_burst

if TYPE_CHECKING:
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations


def test_clean_reads_a_utf16_file(cli: CliRunner, locations: Locations) -> None:
    """`Out-File` writes UTF-16 with a BOM: the shot set aside still moves."""
    bursts = [{"kept": shots(0, 1, 3), "discarded": shots(2)}]
    content = json.dumps({"version": 1, "roots": DEMO_ROOTS, "bursts": bursts})
    (locations.reports_dir / "decisions.json").write_text(content, encoding="utf-16")
    result = run(cli, "clean", "--yes", "--decisions", "decisions.json")
    assert result.exit_code == 0, result.output
    assert "shots set aside: 1" in result.output


def test_review_resumes_a_file_with_a_bom(locations: Locations) -> None:
    """`Set-Content -Encoding UTF8` adds a BOM: the review resumes it."""
    write_burst(locations.data_dir)
    burst = {
        "kept": [f"{BURST_HOST}\\IMG_0.jpg", f"{BURST_HOST}\\IMG_2.jpg"],
        "discarded": [f"{BURST_HOST}\\IMG_1.jpg"],
    }
    content = json.dumps({"version": 1, "roots": ["C:\\"], "bursts": [burst]})
    target = locations.reports_dir / "decisions.json"
    target.write_text(content, encoding="utf-8-sig")
    assert review_session(locations).progress == (1, 1)
