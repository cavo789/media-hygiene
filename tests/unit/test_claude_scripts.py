"""Tests of the backlog tooling in `.claude/scripts/` (0845, 0846, 0847)."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import ModuleType

    import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / ".claude" / "scripts"


def _load(name: str) -> ModuleType:
    """Import a script of `.claude/scripts/` by its path.

    Returns:
        The module.
    """
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _todo(folder: Path, name: str, body: str) -> Path:
    """Write a TODO file.

    Returns:
        Its path.
    """
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_text(body, encoding="utf-8")
    return path


def test_pending_ignores_the_reviewed_folder(tmp_path: Path) -> None:
    """A file moved to `reviewed/` is not listed, whatever it holds."""
    feedback = _load("feedback_pending")
    (tmp_path / "feedback-a.md").write_text("**Question**: x\n", encoding="utf-8")
    _todo(tmp_path / "reviewed", "feedback-b.md", "**Question**: y\n")
    lines = feedback.pending(tmp_path)
    assert lines == [f"{tmp_path / 'feedback-a.md'}\t1Q\t0D", "PENDING: 1"]


def test_done_appends_the_heading_and_moves(tmp_path: Path) -> None:
    """`done` appends `## Reviewed (<date>)` with the note, then moves the file."""
    feedback = _load("feedback_pending")
    path = tmp_path / "feedback-a.md"
    path.write_text("# Run\n", encoding="utf-8")
    code = feedback.main(["x", "done", str(path), "--note", "all decided"])
    moved = tmp_path / "reviewed" / "feedback-a.md"
    assert code == 0
    assert not path.exists()
    text = moved.read_text(encoding="utf-8")
    assert text.startswith("# Run\n\n## Reviewed (")
    assert text.endswith("\nall decided\n")
    assert feedback.pending(tmp_path) == ["PENDING: 0"]


def test_done_refuses_a_missing_file(tmp_path: Path) -> None:
    """A wrong `done` call exits 2."""
    feedback = _load("feedback_pending")
    assert feedback.main(["x", "done", str(tmp_path / "none.md")]) == 2


def test_risky_globs_merge_the_file_and_defaults(tmp_path: Path) -> None:
    """The project's globs come after the defaults, comments dropped."""
    model = _load("todo_model")
    _todo(
        tmp_path / ".config",
        "todo_model_risky_paths.txt",
        "# c\nsrc/app/store/*  # db\n\n",
    )
    globs = model.risky_globs(tmp_path / ".todos")
    assert globs == (*model.DEFAULT_RISKY, "src/app/store/*")
    assert model.is_risky("src/app/store/rows.py", globs)
    assert model.is_risky("deploy/Dockerfile.prod", globs)
    assert not model.is_risky("src/app/view.py", globs)


def test_several_ids_print_one_line_each(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Each ID gets `<id> <model>: <reason>`; a missing one exits 2."""
    model = _load("todo_model")
    todos = tmp_path / ".todos"
    header = "# {0} — t\n\n- **Priority**: Low\n- **Files**: `{1}`\n"
    _todo(todos, "0448-a.md", header.format("0448", "docs/a.md"))
    _todo(todos, "0450-b.md", header.format("0450", "compose.yaml"))
    assert model.main(["x", "0448", "0450", str(todos)]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "0448 sonnet: text only (docs, translations, backlog)",
        "0450 opus: touches compose.yaml (user files or what protects them)",
    ]
    assert model.main(["x", "0448", "0999", str(todos)]) == 2


def test_known_ids_list_every_status(tmp_path: Path) -> None:
    """ID, status and title for every TODO; `--open` keeps the flat backlog."""
    todos = tmp_path / ".todos"
    _todo(todos, "0012-open.md", "# 0012 — Open one\n")
    _todo(todos / "PARTIAL", "PARTIAL_0007-half.md", "# 0007 — Half done\n")
    _todo(todos / ".hidden", "0099-x.md", "# 0099 — hidden\n")
    script = str(SCRIPTS / "todo_known_ids.sh")
    every = subprocess.run(  # noqa: S603
        [script, str(todos)], capture_output=True, text=True, check=True
    )
    assert every.stdout == "0007\tPARTIAL\tHalf done\n0012\tOPEN\tOpen one\n"
    flat = subprocess.run(  # noqa: S603
        [script, str(todos), "--open"], capture_output=True, text=True, check=True
    )
    assert flat.stdout == "0012\tOPEN\tOpen one\n"
