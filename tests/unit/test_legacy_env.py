"""The `MEDIA_DEDUP_*` variables of media-dedup 0.2 keep working, renamed."""

from __future__ import annotations

from media_hygiene.config.legacy_env import adopt_legacy_variables, legacy_names


def test_old_variables_get_their_new_names() -> None:
    """Each old variable is copied to its new name; other variables are left alone."""
    environ = {"MEDIA_DEDUP_GENERAL__LOCALE": "fr", "HOME": "/home/me"}
    adopt_legacy_variables(environ)
    assert environ == {
        "MEDIA_DEDUP_GENERAL__LOCALE": "fr",
        "MEDIA_HYGIENE_GENERAL__LOCALE": "fr",
        "HOME": "/home/me",
    }


def test_the_new_name_wins_when_both_are_set() -> None:
    """A user who set the new name already keeps its value."""
    environ = {"MEDIA_DEDUP_CACHE_DIR": "/old", "MEDIA_HYGIENE_CACHE_DIR": "/new"}
    adopt_legacy_variables(environ)
    assert environ["MEDIA_HYGIENE_CACHE_DIR"] == "/new"


def test_old_names_are_listed_for_the_warning() -> None:
    """Only the old names are listed, sorted; none gives an empty list."""
    environ = {"MEDIA_DEDUP_REPORTS_DIR": "/r", "MEDIA_DEDUP_CACHE_DIR": "/c"}
    environ["MEDIA_HYGIENE_DATA_DIR"] = "/d"
    assert legacy_names(environ) == ("MEDIA_DEDUP_CACHE_DIR", "MEDIA_DEDUP_REPORTS_DIR")
    assert not legacy_names({"MEDIA_HYGIENE_DATA_DIR": "/d"})
