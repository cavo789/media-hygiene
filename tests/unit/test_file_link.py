"""Host paths printed as links the terminal opens with Ctrl+click."""

from __future__ import annotations

from rich.text import Text

from media_hygiene.console.links import file_link

_INDEX = r"C:\Users\John Doe\reports [old]\index.html"


def test_windows_path_is_a_file_link() -> None:
    """Spaces and brackets are encoded in the link and shown as typed."""
    text = Text.from_markup(file_link(_INDEX))
    assert text.plain == _INDEX
    links = {str(span.style) for span in text.spans}
    assert links == {
        "link file:///C:/Users/John%20Doe/reports%20%5Bold%5D/index.html",
    }


def test_container_path_stays_plain() -> None:
    """Without a Windows path, there is nothing to link to."""
    assert file_link("/reports/index.html") == "/reports/index.html"
