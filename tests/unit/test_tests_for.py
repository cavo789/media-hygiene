"""Tests of `.claude/scripts/tests_for.py` (0844): never empty, no e2e, a cap."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / ".claude" / "scripts" / "tests_for.py"


def _tree(root: Path) -> None:
    """Write a tiny repository: a package with one tested module, a browser test."""
    files = {
        "src/media_hygiene/__init__.py": "",
        "src/media_hygiene/person/__init__.py": "",
        "src/media_hygiene/person/cards.py": "X = 1\n",
        "src/media_hygiene/person/fresh.py": "Y = 2\n",
        "src/media_hygiene/person/templates/page.js.j2": "",
        "tests/__init__.py": "",
        "tests/unit/__init__.py": "",
        "tests/unit/test_cards.py": "from media_hygiene.person import cards\n",
        "tests/e2e/__init__.py": "",
        "tests/e2e/test_cards_browser.py": "from media_hygiene.person import cards\n",
    }
    for name, body in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(body, encoding="utf-8")


def _run(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    """Run the script in the tiny repository.

    Returns:
        The finished process.
    """
    return subprocess.run(  # noqa: S603
        [sys.executable, str(SCRIPT), *arguments],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )


def test_a_new_module_gets_its_package_tests_never_an_empty_line(
    tmp_path: Path,
) -> None:
    """No test imports it: the package's tests, said on stderr; e2e left out."""
    _tree(tmp_path)
    run = _run(tmp_path, "src/media_hygiene/person/fresh.py")
    assert run.returncode == 0
    assert run.stdout.split() == ["tests/unit/test_cards.py"]
    assert "of its package" in run.stderr


def test_e2e_only_when_asked(tmp_path: Path) -> None:
    """`--e2e` keeps the browser test."""
    _tree(tmp_path)
    run = _run(tmp_path, "--e2e", "src/media_hygiene/person/cards.py")
    assert run.stdout.split() == [
        "tests/e2e/test_cards_browser.py",
        "tests/unit/test_cards.py",
    ]


def test_a_template_gets_the_page_contract_tests(tmp_path: Path) -> None:
    """A changed `.j2` lists the page tests."""
    _tree(tmp_path)
    run = _run(tmp_path, "src/media_hygiene/person/templates/page.js.j2")
    assert "tests/unit/test_page_frame.py" in run.stdout.split()


def test_nothing_found_prints_a_harmless_target(tmp_path: Path) -> None:
    """A file outside every package: a collect-only target, never an empty line."""
    _tree(tmp_path)
    run = _run(tmp_path, "README.md")
    assert run.returncode == 0
    assert run.stdout.split() == ["--co", "-q", "tests/unit/test_slow_log.py"]


def test_a_conftest_is_over_the_cap(tmp_path: Path) -> None:
    """Every test: nothing printed, exit 3, the caller narrows."""
    _tree(tmp_path)
    run = _run(tmp_path, "tests/conftest.py")
    assert run.returncode == 3
    assert not run.stdout
    assert "narrow it" in run.stderr
