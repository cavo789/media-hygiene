"""The layouts before the sort convention (0401, 0402), for tests about something else.

The rules, events and bands are tested with the folders they wrote for years
(`2016/Vacances`, `2019/To sort/2019-07`): still a valid setting, and the expected
folders stay readable. The convention's own defaults are tested apart.
"""

from __future__ import annotations

from typing import Final

from media_hygiene.config.classify_settings import ClassifySettings

LEGACY_LAYOUTS: Final = {
    "layout": "{year}/{category}",
    "unsure_layout": "{year}/To check/{category}",
    "manual_layout": "{year}/To sort/{event}",
    "undated_layout": "To sort/Undated",
    "received_layout": "To sort/Received and downloaded",
}


def legacy(**fields: object) -> ClassifySettings:
    """`[classify]` with the layouts of before the convention.

    Args:
        **fields: Other settings, or a layout of the test's own.

    Returns:
        The settings.
    """
    return ClassifySettings.model_validate({**LEGACY_LAYOUTS, **fields})
