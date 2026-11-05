# 0524 — Seeing first: every bulk action on the library has a visual path, offered first

- **Priority**: High
- **Batch**: one-interface
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/review_obvious.js.j2`, `src/media_hygiene/classify/workbook/`, `src/media_hygiene/review/sort_*.py`, `src/media_hygiene/cli/menu_catalog_*.py`, `.claude/rules/workflow.md`, `documentation/en/`, `documentation/fr/`

## Asked (maintainer, 2026-10-30)

"I never used a blind feature like the Excel workbook for sorting: it is blind, I don't see what
I sort. media-hygiene must reassure the user before launching important actions on the library."

## Precision (maintainer, 2026-10-30)

The fast paths are **not** removed: "I only have 50,000 photos, I prefer to do it by eye.
Someone with 5 or 10 times more would want something much faster." The workbook and the
other bulk paths stay; what is required is that the visual path always exists and is the one
offered first.

## What

1. **Inventory** every path that moves, sets aside, sorts or deletes files without showing them
   as photos: *Validate the obvious series* (bursts), sorting from the classify workbook,
   `clean` from the console without a review page, `classify`/`sort` straight from the CLI,
   rules applied to "every file found". One line per path: what it does, where it is offered,
   whether a visual twin exists.
2. **Rule** in `.claude/rules/workflow.md` (product rules): "every action on the library has a
   path that shows the photos it will touch before it runs, offered first (menu, home page,
   👉 What next, docs); the fast paths (workbook, validate all) stay, named as such, for large
   collections".
3. **Per path without a visual twin**, file one TODO adding it (0520 is the bursts one).
4. Wording: a fast path says what it skips, in one line (e.g. "sorts N files without showing
   them — the page `…` shows them first").

## Done when

The inventory is in this TODO, the rule is in `workflow.md`, and one TODO per path lacking a
visual twin is filed. No fast path is removed.

## Decided (2026-11-05, maintainer, start of /todo:iterate)

Run it unattended: write the inventory, the rule and the follow-up TODOs; the maintainer reviews
the inventory afterwards, on the pull request. No fast path is removed.
