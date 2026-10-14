"""`[cache]`: the bound of the previews."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from media_hygiene.config.cache_settings import CacheSettings


def test_two_gigabytes_by_default_and_never_zero() -> None:
    """2 GB unless set; a bound of 0 or less is refused."""
    assert CacheSettings().previews_max_bytes == 2 * 1024**3
    with pytest.raises(ValidationError):
        CacheSettings(previews_max_gb=0)
