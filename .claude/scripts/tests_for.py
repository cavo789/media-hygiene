#!/usr/bin/env python3
"""List the test files that exercise the Python files changed in the working tree.

The quick loop between two edits: the tests that import a changed module (DEPTH 0),
or a module importing it (DEPTH 1, and so on), instead of the whole suite. Imports are
read with `ast` over the source and test roots, so a test is found by what it imports,
not by its name. The full suite stays the gate (`check`, CI): an indirect dependency
deeper than DEPTH, or a template read at run time, is not followed.

Never an empty line (0844: an empty `pytest $(…)` runs the whole suite): a
changed file no test imports falls back to the tests of its package (the tests
importing any module of its folder); a changed template (`.j2`, `.css`, `.js`)
adds the page contract tests (`PAGE_TESTS`); still nothing, a harmless target
(`HARMLESS`), said on stderr. `tests/e2e/` is left out unless `--e2e`. Over
`CAP` test files (or a changed `conftest.py`), nothing is printed, exit 3.

Usage: tests_for.py [--depth N] [--base REV] [--e2e] [file...]
  file...      the changed files (default: `git status`, untracked included; with
               --base, also what changed since REV, e.g. main for a work branch)
  --depth N    importers followed between a test and a changed module (default 0;
               measured on plan/keeper.py: 0 = 83 tests in 1 s, 1 = 244 in 76 s)
  --e2e        keep the tests of `tests/e2e/` (skipped by their marker, slow to collect)

Output: one test file (or pytest argument) per line, sorted. On stderr: the
changed files no test was found for, and each fallback taken.
"""

from __future__ import annotations

import argparse
import ast
import shutil
import subprocess
import sys
from pathlib import Path

ROOTS = {"src": "", "tests": "tests"}  # folder -> package prefix of its modules
CAP = 40  # test files: past it the caller narrows (2026-11-27: 326 listed)
TEMPLATES = frozenset({".j2", ".css", ".js"})
PAGE_TESTS = (  # the page contract (.claude/rules/pages.md) every template answers to
    "tests/unit/test_page_frame.py",
    "tests/unit/test_page_script_names.py",
    "tests/unit/test_same_features_on_pages.py",
    "tests/unit/test_shell_pages.py",
)
HARMLESS = ("--co", "-q", "tests/unit/test_slow_log.py")
TOO_MANY = 3  # exit status past CAP
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


def tests_of(
    names: set[str], graph: tuple[dict[str, Path], Graph], depth: int
) -> set[str]:
    """Give the test files reaching any of the modules within `depth` importers."""
    modules, importers = graph
    return {
        str(modules[hit])
        for name in names
        for hit in reach(name, importers, depth)
        if modules[hit].name.startswith("test_")
    }


def package_of(path: Path, modules: dict[str, Path]) -> set[str]:
    """Give the modules of the package holding `path` (its folder), by name."""
    name = module_name(path.parent / "__init__.py")
    if not name or name == "media_hygiene":
        return set()
    return {
        module for module in modules if module == name or module.startswith(f"{name}.")
    }


def select(
    files: list[Path], graph: tuple[dict[str, Path], Graph], depth: int
) -> set[str]:
    """Give the tests for the files, with the template and package fallbacks."""
    modules, importers = graph
    tests: set[str] = set()
    for path in files:
        if path.name == "conftest.py":
            return {"tests"}
        name = module_name(path)
        found = tests_of({name}, graph, depth) if name in importers else set()
        if path.suffix in TEMPLATES and path.parts[:1] == ("src",):
            found |= set(PAGE_TESTS)
        if not found and path.exists() and path.parts[:1] == ("src",):
            found = tests_of(package_of(path, modules), graph, 0)
            sys.stderr.write(
                f"no test imports {path}: the {len(found)} of its package\n"
            )
        elif not found:
            sys.stderr.write(f"no test found for {path}\n")
        tests |= found
    return tests


def main() -> int:
    """Print the test files for the changed files; exit 0, or 3 past `CAP`."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="*", type=Path)
    parser.add_argument("--depth", type=int, default=0)
    parser.add_argument("--base")
    parser.add_argument("--e2e", action="store_true")
    options = parser.parse_args()
    files = options.files or changed(options.base)
    modules = {
        name: path
        for root in ROOTS
        for path in Path(root).rglob("*.py")
        if (name := module_name(path)) and "__pycache__" not in path.parts
    }
    tests = select(files, (modules, reverse_imports(modules)), options.depth)
    if not options.e2e:
        tests = {test for test in tests if not test.startswith("tests/e2e/")}
    if "tests" in tests or len(tests) > CAP:
        size = "every test" if "tests" in tests else f"{len(tests)} test files"
        sys.stderr.write(
            f"{size}, over {CAP}: narrow it (--depth 0, the files by name)\n"
        )
        return TOO_MANY
    if not tests:
        sys.stderr.write(f"nothing to run: {' '.join(HARMLESS)} instead\n")
        sys.stdout.write("".join(f"{arg}\n" for arg in HARMLESS))
        return 0
    sys.stdout.write("".join(f"{test}\n" for test in sorted(tests)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
