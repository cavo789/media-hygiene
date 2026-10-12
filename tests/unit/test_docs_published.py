"""The suggested commands of the captures, as a reader of the guides would type them."""

from __future__ import annotations

from pathlib import Path

from tests.support.docs.container import Demo
from tests.support.docs.names import NAMES, Library, Locale
from tests.support.docs.published import as_published

_CAPTURED = """docker run --rm -it \\
  --user "$(id -u):$(id -g)" \\
  -v "media-hygiene-docs-{locale}-c:/data/c/Photos" \\
  -v "media-hygiene-docs-{locale}-d:/data/d/{disk}" \\
  -v "media-hygiene-docs-{locale}-cache:/cache" \\
  -v "media-hygiene-docs-{locale}-journal:/journal" \\
  cavo789/media-hygiene --locale {locale} --color never undo 20261011-100607
"""


def _demo(locale: Locale) -> Demo:
    """A demo of one language; its files are never written."""
    return Demo(Library(Path("/unused"), NAMES[locale]), locale)


def _captured(locale: Locale) -> str:
    """A suggested command as the documentation run prints it."""
    return _CAPTURED.format(locale=locale, disk=NAMES[locale].old_disk)


def test_english_reads_like_powershell() -> None:
    """Windows folders, backticks, no --user; the options of every run disappear."""
    published = as_published(_demo(Locale.EN), _captured(Locale.EN))
    assert published.startswith("docker run --rm -it `\n")
    assert '-v "C:\\Photos:/data/c/Photos" `' in published
    assert '-v "D:\\Old disk:/data/d/Old disk" `' in published
    assert '-v "media-hygiene-cache:/cache" `' in published
    assert '-v "$HOME\\media-hygiene\\journal:/journal" `' in published
    assert "cavo789/media-hygiene undo 20261011-100607" in published
    assert "media-hygiene-docs-" not in published
    assert "--user" not in published
    assert "\\\n" not in published


def test_folders_are_made_as_in_powershell() -> None:
    """`mkdir -p` and its folders become `mkdir -Force`, separated by commas."""
    captured = 'mkdir -p "$HOME/media-hygiene/journal" "$HOME/media-hygiene/reports"\n'
    published = as_published(_demo(Locale.EN), captured)
    assert published == (
        'mkdir -Force "$HOME\\media-hygiene\\journal", '
        '"$HOME\\media-hygiene\\reports"\n'
    )


def test_french_keeps_its_locale() -> None:
    """French is not the default: `--locale fr` stays, as in the French guides."""
    published = as_published(_demo(Locale.FR), _captured(Locale.FR))
    assert '-v "D:\\Ancien disque:/data/d/Ancien disque" `' in published
    assert "cavo789/media-hygiene --locale fr undo 20261011-100607" in published


def test_other_text_unchanged() -> None:
    """A capture without a suggested command is left as it is."""
    text = "Media files scanned │ 85\n"
    assert as_published(_demo(Locale.EN), text) == text
