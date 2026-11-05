# 0619 — A copy from the import page runs `[imports] then`, like the console

- **Priority**: Medium
- **Batch**: import
- **Depends**: 0590 (DONE), 0586
- **Files**: `src/media_hygiene/review/`, `src/media_hygiene/services/`

## Why

Review of 0590: after a copy from `/import/`, the page only says to audit again; the console runs the `[imports] then` chain (places, audit…).

## What

After the page's copy, run the same chain as the console, as steps followed in the page (0514/0586), each keeping its own question (reverse lookup asks its Yes each time).

## Done when

Copy from the page then the chain, same result as the console (test).
