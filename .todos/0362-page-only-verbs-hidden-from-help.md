# 0362 — Verbs that only open a page: hidden from `mh --help`, decided case by case

- **Priority**: Medium
- **Batch**: home
- **Depends**: 0356
- **Files**: `src/media_hygiene/cli/app.py`, `src/media_hygiene/cli/menu_catalog_*.py`, `src/media_hygiene/cli/safety.py`, `src/media_hygiene/console/advice.py`, `tests/support/docs/scenario.py`, `tests/unit/test_docs_commands.py`, `documentation/en/reference-commands.md`, `documentation/fr/reference-commands.md`, `documentation/en/commands/`, `documentation/fr/commands/`

## Context

Decided by the maintainer (2026-10-24), once the home page opens every page in one click (0356):
*a command with no use in the console is removed, or, when it must stay, hidden from
`mh --help`; case by case* (`mh search "la plage"` prints a table: it stays).

Hidden rather than removed: `mh menu`, the page's fallback (*copy the command*: an older `mh`,
reports in a named volume, `docker run` alone) and the end-to-end tests still run these verbs;
Typer's `hidden=True` keeps them working, as `phone-plan` and the steps of `mh backup` already are
(`cli/app.py`, plumbing).

What each page command does in the console (read in the code, 2026-10-24):

| Verb | Console use | Proposal |
|---|---|---|
| `search` | `search "words"` prints a table (`--limit`) | stays visible |
| `people` | `--sample` (time per photo), `--path` (faces of a folder), `--forget`: work in the console | stays visible |
| `shrink` | lists the heavy videos; `--try`, `--apply` re-encode | stays visible |
| `browse` | `--port` only: opens the page | **hidden** |
| `places` | `--port` only: opens the map | **hidden** |
| `home` | run by `mh` alone, never typed | **hidden** |
| `review` | opens a page; its options choose what to review (`--near`, `--pairs`, `--junk`, `--gone`, `--decisions`) and its filters (`--prefer`, `--protect`, `--exclude`, `--backup`, `--ext`) | **stays visible** (decided) |
| `review-sort` | `--workbook` (which workbook), then the page | **hidden** (decided) |
| `slideshow` | `--album`, `--folder`, `--search`, `--chosen`; `mh slideshow --lan` starts the show on the TV | **stays visible** (decided) |

## Decided (2026-10-25, maintainer, review of the feedback of 2026-10-24)

- `review` stays visible: a filter for one run (`--protect "D:\Archives"`) only the command line
  gives, without touching `config.toml`.
- `review-sort` hidden.
- `slideshow` stays visible: `mh slideshow --lan` is typed in the console for the TV.

## What to do

1. The verbs decided hidden: `hidden=True` (still in `mh menu` and the catalog of the home page,
   which run them); a test lists the visible verbs of `mh --help` against the table above.
2. Docs: `reference-commands.md` lists the visible verbs; the hidden ones keep a page about the
   **page** (what it shows, how to open it from the home page), its command in one line at the
   end (*also `mh browse`, for a script or without the home page*). `COMMANDS_TOO` and
   `test_docs_commands.py` follow (a hidden verb needs no `--help` capture).
3. The "👉 What next" lines (`console/advice.py`, `NextVerb`): a hidden verb is proposed as the
   page to open on the home page, not as a command to type.
4. The guides (`start/`, `clean/`, `sort/`): the step shows the home page's button first, the
   command second, and none for a hidden verb.
5. `docs_screenshots` to run (said, not run): `mh --help` and the guides' captures change.

## Acceptance

- `mh --help` lists only the verbs with a use in the console; every hidden verb still runs when
  typed, from `mh menu` and from the home page.

## Gain

A shorter `mh --help` (4 verbs fewer: `browse`, `places`, `home`, `review-sort`), each verb
listed doing something in the console; the pages reached from the home page, as the maintainer uses them.
