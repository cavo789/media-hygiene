r"""Where the sort files go and in what shape, chosen on the page (0533).

`GET /api/sort-setup` says `[classify] target`, the five layouts, `leave` and
`person_folders` as `config.toml` holds them now, the named models and the tree each
would give on the user's photos. `POST` saves the target and the layouts: edited with
`toml_edit` (comments kept, atomic), then read back from the disk before being shown.
A layout of the user's own stays until another is chosen; nothing moves here: the next
`classify` proposes with the new values.
"""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.config.classify_settings import ClassifySettings
from media_hygiene.i18n import _
from media_hygiene.paths.host_paths import is_within
from media_hygiene.places.toml_edit import (
    document_of,
    host_path,
    loaded,
    table_of,
    write_document,
)
from media_hygiene.review.serving import json_response
from media_hygiene.search.sort_setup_preview import (
    MAIN,
    index_pools,
    plan_pools,
    preview,
)

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Callable

    from media_hygiene.classify.plan_file import ClassifyPlan
    from media_hygiene.review.http import Response
    from media_hygiene.search.folder_role_desk import RoleDesk

SETUP_PATH: Final = "/api/sort-setup"
TABLE: Final = "classify"
_MODELS: Final = ("{year}/{year_month}/{category}", "{year}/{year_month}")  # decided
_OTHERS: Final = ("unsure_layout", "manual_layout", "undated_layout", "received_layout")
_MAX_PATH: Final = 4096
_DEFAULTS: Final = ClassifySettings()


class SetupAsked(BaseModel):
    """`POST /api/sort-setup`: the target (host path; empty: in place), the layouts."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    target: str = Field(max_length=_MAX_PATH)
    layouts: dict[str, str]


@dataclass(frozen=True, slots=True)
class SortSetupDesk:
    """Reads and writes where the sort files go, in `config.toml`."""

    roles: RoleDesk  # `config.toml`, the host paths, the mounted folders
    connection: sqlite3.Connection
    plan: Callable[[], ClassifyPlan | None]  # the latest one

    def _layouts(self) -> dict[str, str]:
        """The five layouts, as the file says them, else their defaults.

        Returns:
            Each by its key.
        """
        table = loaded(self.roles.config_file).get(TABLE, {})
        keys = (MAIN, *_OTHERS)
        return {key: str(table.get(key, getattr(_DEFAULTS, key))) for key in keys}

    def state(self) -> Response:
        """`GET /api/sort-setup`.

        Returns:
            What the file holds, the models and their trees.
        """
        return json_response(HTTPStatus.OK, self.shown())

    def shown(self) -> dict[str, object]:
        """What the page draws, read from the disk.

        Returns:
            The target, the layouts, the models, each one's preview per layout.
        """
        plan = self.plan()
        pools = index_pools(self.connection) if plan is None else plan_pools(plan)
        layouts = self._layouts()
        previews = {
            key: {
                layout: preview(layout, key, pools).model_dump()
                for layout in {*_MODELS, now}
                if layout
            }
            for key, now in layouts.items()
        }
        table = loaded(self.roles.config_file).get(TABLE, {})
        names = (_("Year / Year-month / Event"), _("Year / Month only"))
        models = [
            {"layout": layout, "name": name}
            for layout, name in zip(_MODELS, names, strict=True)
        ]
        return {
            "target": str(table.get("target", "")),
            "layouts": layouts,
            "models": models,
            "previews": previews,
            "from_plan": plan is not None,
            "plan_layout": "" if plan is None else plan.layout,
        }

    def answer(self, body: bytes) -> Response:
        """`POST /api/sort-setup`: save the target and the layouts.

        Args:
            body: The JSON the page sent.

        Returns:
            What the file holds now and the sentence; 400 for another body; 409, the
            file unchanged, for a target or a layout that cannot work.
        """
        try:
            asked = SetupAsked.model_validate_json(body)
        except ValidationError:
            return json_response(
                HTTPStatus.BAD_REQUEST, {"error": _("Not a choice of the page.")}
            )
        target = asked.target.strip()
        refused = self._refused(target, asked.layouts)
        if refused is not None:
            return json_response(HTTPStatus.CONFLICT, {"error": refused})
        document = document_of(self.roles.config_file)
        table = table_of(document, TABLE)
        if target != str(table.get("target", "")):
            table["target"] = host_path(target)
        now = self._layouts()
        for key, layout in asked.layouts.items():
            if layout != now[key]:
                table[key] = layout
        write_document(self.roles.config_file, document)
        said = _(
            "Saved in {file}. Nothing moved: the next classify proposes with these "
            "choices."
        ).format(file=self.roles.mapper.to_host(self.roles.config_file))
        return json_response(HTTPStatus.OK, {**self.shown(), "said": said})

    def _refused(self, target: str, layouts: dict[str, str]) -> str | None:
        """Why a choice cannot be saved.

        Args:
            target: The target, stripped.
            layouts: The layouts asked.

        Returns:
            The reason; None when it can.
        """
        now = self._layouts()
        for key, layout in layouts.items():
            allowed = {*_MODELS, now.get(key, "")} | (set() if key == MAIN else {""})
            if key not in now or layout not in allowed:
                return _("This layout is not one of the page's.")
        return self._target_refused(target) if target else None

    def _target_refused(self, target: str) -> str | None:
        """Why the sort may not write to a folder: not mounted, protected, excluded.

        Whether it is writable is `sort`'s check: the pages may run on read-only mounts.

        Args:
            target: Its host path.

        Returns:
            The reason; None when it may.
        """
        mapper = self.roles.mapper
        inside = mapper.to_container(target)
        if not any(is_within(inside, top) for top in self.roles.roots):
            return _(
                "{path} is not in a mounted folder: the sort could not write there."
            ).format(path=target)
        folders = loaded(self.roles.config_file).get("folders", {})
        for role in ("protected", "excluded"):
            for path in folders.get(role, []):
                if is_within(inside, mapper.to_container(str(path))):
                    return _(
                        "{path} is inside {folder}, a folder the sort never touches."
                    ).format(path=target, folder=path)
        return None
