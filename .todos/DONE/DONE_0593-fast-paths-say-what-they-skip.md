# 0593 — Fast paths say what they skip, and the visual path is offered first

- **Priority**: Medium
- **Batch**: one-interface
- **Depends**: 0524 (DONE)
- **Files**: `src/media_hygiene/cli/menu_catalog_*.py`, `src/media_hygiene/cli/cmd_sort.py`, `src/media_hygiene/cli/cmd_clean.py`, `src/media_hygiene/cli/next_step*.py`, `documentation/en/`, `documentation/fr/`

## Why (inventory of 0524, point 4)

Twins exist for `sort` (the classify report, the 🗂 Events tab), `clean` (the audit's report),
`clean --tier near-all` and `--delete` (`review --near`, the report), `undo` (`undo --pick`), but those
verbs do not say so. Also: the `sort` step still says "on the page or in the workbook" while the Events
tab now lists the index's events, not the plan's (0572).

## What

One line per fast path, in the catalog and at the console's question: "moves N files without showing
them: the report … shows them first". The guides and 👉 What next offer the visual path first.

## Done when

A test lists the fast paths of the catalog and checks each names its twin; no fast path removed.
