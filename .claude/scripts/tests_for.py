#!/usr/bin/env python3
"""List the test files that exercise the Python files changed in the working tree.

The quick loop between two edits: the tests that import a changed module (DEPTH 0),
or a module importing it (DEPTH 1, and so on), instead of the whole suite. Imports are
read with `ast` over the source and test roots, so a test is found by what it imports,
not by its name. The full suite stays the gate (`check`, CI): an indirect dependency
deeper than DEPTH, or a template read at run time, is not followed.

Usage: tests_for.py [--depth N] [--base REV] [file...]
  file...      the changed files (default: `git status`, untracked included; with
               --base, also what changed since REV, e.g. main for a work branch)
  --depth N    importers followed between a test and a changed module (default 0;
               measured on plan/keeper.py: 0 = 83 tests in 1 s, 1 = 244 in 76 s)

Output: one test file per line, sorted. A changed `conftest.py` prints the test root
(every test). On stderr: the changed files no test was found for.
"""

from __future__ import annotations

import argparse
import ast
import shutil
import subprocess
import sys
from pathlib import Path

ROOTS = {"src": "", "tests": "tests"}  # folder -> package prefix of its modules
type Graph = dict[str, set[str]]


def module_name(path: Path) -> str | None:
    """Give the dotted module name of a Python file under one of the roots, or None."""
    parts = path.with_suffix("").parts
    if path.suffix != ".py" or not parts or parts[0] not in ROOTS:
        return None
    dotted = list(parts[1:]) if parts[0] == "src" else list(parts)
    if dotted and dotted[-1] == "__init__":
        dotted.pop()
    return ".".join(dotted) or None


def imported(tree: ast.Module, module: str, *, package: bool) -> set[str]:
    """Give every module name an import of the tree may refer to (module, attribute)."""
    names: set[str] = set()
    here = module.split(".") if package else module.split(".")[:-1]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = here[: len(here) - node.level + 1] if node.level else []
            stem = ".".join([*base, *([node.module] if node.module else [])])
            names.add(stem)
            names.update(f"{stem}.{alias.name}" for alias in node.names)
    return names


def reverse_imports(modules: dict[str, Path]) -> Graph:
    """Map each known module to the known modules importing it."""
    importers: Graph = {name: set() for name in modules}
    for name, path in modules.items():
        tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
        for target in imported(tree, name, package=path.name == "__init__.py"):
            if target in importers and target != name:
                importers[target].add(name)
    return importers


def reach(start: str, importers: Graph, depth: int) -> set[str]:
    """Give the start module and its importers up to `depth` links away."""
    seen, frontier = {start}, {start}
    for _ in range(depth + 1):
        frontier = {up for name in frontier for up in importers[name]} - seen
        seen |= frontier
    return seen


def git(*arguments: str) -> str:
    """Give the output of a git command run in the current directory."""
    command = [shutil.which("git") or "git", *arguments]
    return subprocess.run(command, check=True, capture_output=True, text=True).stdout  # noqa: S603


def changed(base: str | None) -> list[Path]:
    """Give the files changed in the working tree (and since `base`, when given)."""
    status = git("status", "--porcelain", "--untracked-files=all")
    paths = {line[3:].split(" -> ")[-1] for line in status.splitlines()}
    if base:
        paths |= set(git("diff", "--name-only", f"{base}...HEAD").split())
    return sorted(Path(path) for path in paths)


def main() -> int:
    """Print the test files for the changed files; exit 0."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="*", type=Path)
    parser.add_argument("--depth", type=int, default=0)
    parser.add_argument("--base")
    options = parser.parse_args()
    files = options.files or changed(options.base)
    modules = {
        name: path
        for root in ROOTS
        for path in Path(root).rglob("*.py")
        if (name := module_name(path)) and "__pycache__" not in path.parts
    }
    importers = reverse_imports(modules)
    tests: set[str] = set()
    unmapped: list[str] = []
    for path in files:
        if path.name == "conftest.py":
            tests.add("tests")
            continue
        name = module_name(path)
        if name not in importers or not path.exists():
            unmapped.append(str(path))
            continue
        found = {
            str(modules[hit])
            for hit in reach(name, importers, options.depth)
            if modules[hit].name.startswith("test_")
        }
        tests |= found
        if not found:
            unmapped.append(str(path))
    if "tests" in tests:
        tests = {"tests"}
    sys.stdout.write("".join(f"{test}\n" for test in sorted(tests)))
    if unmapped:
        sys.stderr.write(f"no test found for: {', '.join(unmapped)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
