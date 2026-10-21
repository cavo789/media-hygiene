"""The public site wears the tool's look from the tool's own files (0281)."""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MKDOCS = ROOT / ".config" / "mkdocs"
ASSETS = ROOT / "src" / "media_hygiene" / "assets"
SHEETS = MKDOCS / "overrides" / "stylesheets"
TOKENS = (ASSETS / "theme" / "tokens.css").read_text(encoding="utf-8")
DEFINED = set(re.findall(r"(--(?:mk|mh)-[\w-]+)\s*:", TOKENS))
USED = re.compile(r"var\((--(?:mk|mh)-[\w-]+)")


def published() -> dict[str, str]:
    """The `PUBLISHED` map of hooks.py, loaded by its path."""
    spec = importlib.util.spec_from_file_location("site_hooks", MKDOCS / "hooks.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return dict(module.PUBLISHED)


def test_published_files_exist() -> None:
    """Every file the site takes from the tool's assets is there."""
    files = published()
    assert files
    assert all((ASSETS / source).is_file() for source in files.values())


def test_site_refers_to_published_files() -> None:
    """The logo, favicon, tokens and fonts of theme.css are published."""
    files = published()
    config = (MKDOCS / "mkdocs.yml").read_text(encoding="utf-8")
    for key in ("logo", "favicon"):
        match = re.search(rf"^  {key}: (\S+)", config, re.MULTILINE)
        assert match is not None
        assert match[1] in files
    assert "stylesheets/tokens.css" in files
    theme = (SHEETS / "theme.css").read_text(encoding="utf-8")
    fonts = re.findall(r'url\("\.\./(fonts/[^"]+)"\)', theme)
    assert fonts
    assert set(fonts) <= set(files)


def test_stylesheets_use_only_tokens_the_tool_defines() -> None:
    """No variable of theme.css or guide.css is unknown to the tokens."""
    own = set()
    for sheet in ("theme.css", "guide.css"):
        text = (SHEETS / sheet).read_text(encoding="utf-8")
        own |= set(re.findall(r"^\s*(--mh-[\w-]+)\s*:", text, re.MULTILINE))
        unknown = set(USED.findall(text)) - DEFINED - own
        assert unknown == set(), f"{sheet}: {sorted(unknown)}"
