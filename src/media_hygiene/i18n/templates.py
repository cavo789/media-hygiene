"""Jinja environments whose `_()` uses the active language (reports, config.toml)."""

from __future__ import annotations

from typing import Final

from jinja2 import ChoiceLoader, Environment, PackageLoader, select_autoescape

from media_hygiene.i18n import active
from media_hygiene.theme import avatar_data_uri, theme_tokens

# The fragments every local page includes (the "⌂ Home" link): found from any package.
_SHARED_PAGES: Final = "media_hygiene.review"


def translated_environment(package: str, escaped: tuple[str, ...]) -> Environment:
    """Create a Jinja environment loading `<package>/templates`, translated.

    A template not found there is looked for among the pages' shared fragments.

    Args:
        package: The package holding a `templates` directory.
        escaped: Template extensions to HTML-escape (none for plain text such as TOML).

    Returns:
        The environment.
    """
    environment = Environment(
        loader=ChoiceLoader(
            (
                PackageLoader(package, "templates"),
                PackageLoader(_SHARED_PAGES, "templates"),
            )
        ),
        autoescape=select_autoescape(enabled_extensions=escaped),
        extensions=["jinja2.ext.i18n"],
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    environment.globals["theme_tokens"] = theme_tokens
    environment.globals["avatar_data_uri"] = avatar_data_uri
    # pylint: disable-next=no-member
    environment.install_gettext_translations(  # type: ignore[attr-defined]
        active(),
        newstyle=True,
    )
    return environment
