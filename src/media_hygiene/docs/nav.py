"""The menu of the docs: `nav` of `.config/mkdocs/mkdocs.yml`, translated like the site.

The site and the docs inside the image list the same pages in the same order; the
French section titles come from `nav_translations` of the i18n plugin. Build time only:
reading YAML needs the `docs` dependency group.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, cast

import yaml

from media_hygiene.docs.pages import NavSection

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

_I18N: Final = "i18n"
_UNTITLED: Final = ""


def read_config(mkdocs_yml: Path) -> Mapping[str, object]:
    """Read the site's configuration.

    Args:
        mkdocs_yml: `.config/mkdocs/mkdocs.yml`.

    Returns:
        Its content.
    """
    loaded = yaml.safe_load(mkdocs_yml.read_text(encoding="utf-8"))
    return cast("Mapping[str, object]", loaded)


def nav_sections(config: Mapping[str, object], locale: str) -> tuple[NavSection, ...]:
    """The sections of the menu, in one language.

    A page listed alone at the top of `nav` makes an untitled section of its own.

    Args:
        config: The site's configuration.
        locale: E.g. `fr`.

    Returns:
        The sections, in the order of `nav`.
    """
    names = _translations(config, locale)
    sections: list[NavSection] = []
    for entry in cast("list[object]", config["nav"]):
        if isinstance(entry, str):
            sections.append(NavSection(_UNTITLED, (entry,)))
            continue
        for title, pages in cast("dict[str, list[str]]", entry).items():
            sections.append(NavSection(names.get(title, title), tuple(pages)))
    return tuple(sections)


def _translations(config: Mapping[str, object], locale: str) -> Mapping[str, str]:
    """The section titles of a language, as the i18n plugin translates them.

    Args:
        config: The site's configuration.
        locale: E.g. `fr`.

    Returns:
        English title → translated title; empty for English.
    """
    for plugin in cast("list[object]", config.get("plugins", [])):
        if not isinstance(plugin, dict) or _I18N not in plugin:
            continue
        languages = cast("dict[str, list[dict[str, object]]]", plugin[_I18N])
        for language in languages["languages"]:
            if language["locale"] == locale:
                return cast("dict[str, str]", language.get("nav_translations", {}))
    return {}


def markdown_extensions(
    config: Mapping[str, object],
) -> tuple[list[str], dict[str, object]]:
    """The Markdown extensions of the site, and their settings.

    Args:
        config: The site's configuration.

    Returns:
        Their names, and each one's settings by name.
    """
    names: list[str] = []
    settings: dict[str, object] = {}
    for entry in cast("list[object]", config["markdown_extensions"]):
        if isinstance(entry, str):
            names.append(entry)
            continue
        for name, values in cast("dict[str, object]", entry).items():
            names.append(name)
            settings[name] = dict(cast("dict[str, object]", values or {}))
    return names, settings
