# 0541 — Messages cut at 80 columns when docker runs without a terminal

- **Priority**: Medium — cosmetic, but seen on every command `mh` runs without `-t`
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/console/output.py`, `tests/unit/test_console_*.py`

## Asked (maintainer, 2026-10-30)

`mh update` printed *mh retient : 1 dossier, langue fr, fuseau horaire celui de l'ordinateur, lu
à* and then *chaque lancement.* on a second line: "why not on the same line?"

## Cause (read in the code 2026-10-30, not measured)

`console/output.py` builds Rich `Console(...)` objects without a `width`. When stderr is not a
terminal (`docker run` without `-t`, which `mh.ps1` does when it captures output or reruns
`launcher`), Rich falls back to 80 columns (Rich's documented default when it cannot find a
terminal size: to check against the pinned version), and inserts real line breaks there. The
PowerShell window then shows those breaks whatever its width. That line itself is gone since
2026-10-30 (`rewritten_by_mh()`), but any message longer than 80 characters from such a run is
cut the same way.

## What

- When the output is not a terminal, write each message as one line (`soft_wrap=True` on
  print, or a very large `width`): the host window wraps it at its own width.
- Keep tables and panels readable: they need a width. List which outputs are tables
  (`console/tables`) and give them the `COLUMNS` the host passes, or 120 by default. `mh.ps1`
  can pass `-e COLUMNS=$Host.UI.RawUI.WindowSize.Width` (check that Rich reads `COLUMNS`, and
  that Windows PowerShell 5.1 reports a width when its output is redirected).
- Report files and logs written to disk: unchanged, never coloured.

## Done when

- A unit test: a 200-character message printed to a non-terminal stream comes out with no
  line break inside.
- On the maintainer's PC, a long message of `mh update` / `mh audit` fills the window and
  wraps at its edge, not at column 80.

## Checked (maintainer, 2026-11-03, image 32cafce7)

`mh people --help` in a window much wider than 80 columns: long lines reach the window's edge.
Not conclusive for this TODO: `--help` is drawn by Typer, not by `console/output.py`. The
unit test of "Done when" settles the rest without the maintainer (a 200-character message to a
non-terminal stream); a real check is still a long message of a run without `-t` (`mh audit`).
`mh audit` too (maintainer, same day): wraps at the edge. Read after: `audit` and `--help` run
with `-it` (`safety.DATA_COMMANDS` lists the commands run without a terminal: `launcher`,
`menu`, the phone and push steps). Only those can cut at 80: the unit test settles it; no
check left for the maintainer.
