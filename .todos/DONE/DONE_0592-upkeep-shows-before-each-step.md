# 0592 — Upkeep routine: what each step will touch, before it runs

- **Priority**: Medium
- **Batch**: one-interface
- **Depends**: 0524 (DONE), 0586
- **Files**: `src/media_hygiene/cli/cmd_upkeep*.py`, `src/media_hygiene/services/upkeep*`, `src/media_hygiene/cli/menu_catalog_clean*.py`, `documentation/en/commands/upkeep.md`, `documentation/fr/commands/upkeep.md`

## Why (inventory of 0524)

`upkeep` (0519) chains `clean`, `purge`… in one click: no photo shown on the way. Each step keeps its
own question, but none points to the page showing its files.

## What

Between two steps that change files, the routine offers the visual path of the next one (the
report of `clean`, the page of 0591 for `purge`) with its count; going straight on stays one key.

## Done when

The routine names, per writing step, the count and the page (test); no step is removed.
