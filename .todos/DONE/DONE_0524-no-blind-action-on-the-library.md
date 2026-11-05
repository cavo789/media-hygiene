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

## Inventory (2026-11-05, read from the catalog, the templates and the docs; to review on the PR)

| Path | What it does | Where it is offered | Visual twin |
|---|---|---|---|
| *Validate the obvious series* (bursts) | sets aside the shots proposed, every obvious series, one write, one Z undoes | `review` | yes: contact sheet (0520) |
| `sort`, from the classify workbook | moves every file of the plan | sort stage, console | yes: the classify report (look), 🗂 Events (one event); not named by the step → 0593 |
| `classify` | moves nothing; the workbook is a blind editing surface | sort stage | yes: report, 🗂 Events; → 0593 |
| `clean` (exact copies) | quarantines the copies | clean stage, console | yes: the audit's report shows groups, kept copy; not named at its question → 0593 |
| `clean --tier near` | also the sure near duplicates | console, guide | yes: `review --near`; → 0593 |
| `clean --tier near-all` | every near duplicate | console | yes: `review --near`, report; → 0593 |
| `clean --delete` | erases instead of quarantine | clean stage (⚠️) | same as `clean`; → 0593 |
| `apply` (`clean --decisions`) | applies what the pages recorded | *Apply now*, clean stage | yes: the pages it comes from |
| `upkeep` | chains clean, purge…, each asking | clean stage | **no** → 0592 |
| `purge` | erases a quarantine for good | history, disk space page | partly: `undo --pick` exists, not offered, docs say Explorer → 0591 |
| `undo` | restores a whole run | history, console | yes: `undo --pick` → 0593 |
| `import`, `import <folder>` | copies what only a folder holds | import stage | **no**: a count and text paths → 0590 |
| `import --phone` | copies from the phone | import stage | yes: the phone page |
| `import --phone --free` | deletes from the phone what is proven | clean stage (⚠️) | yes: the phone page's ticks |
| Rule's GO, "every file found" (search) | moves / sets aside a found set | search | yes: trial tiles; the button states the count |
| *Sort here now* | moves one event | 🗂 Events | is the visual path |
| `shrink` | re-encodes | clean stage | yes: `--try` page |
| Out of scope (touch no library file) | `album`, `xmp` (sidecars), `push`, `share`, `reports --prune` | | |

Item 4 (wording) is filed as 0593 since half of it needs the twins of 0590–0592.
