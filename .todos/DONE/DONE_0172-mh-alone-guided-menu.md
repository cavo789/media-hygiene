# 0172 — `mh` alone opens a guided menu: every step in order, the next one first

- **Priority**: Medium
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/services/launcher.py`, `src/media_hygiene/cli/cmd_launcher.py`, `src/media_hygiene/cli/command_table.py`, `src/media_hygiene/cli/safety.py`, `src/media_hygiene/cli/status_next.py`, `src/media_hygiene/services/status.py`, new `src/media_hygiene/cli/cmd_menu.py` (+ `menu_*.py` modules), `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/menu.md`, `documentation/fr/commands/menu.md`, `documentation/en/reference-commands.md`, `documentation/fr/reference-commands.md`, `documentation/en/{clean,sort,find}/quick-guide.md`, `documentation/fr/{clean,sort,find}/quick-guide.md`, `tests/support/docs/scenario.py`, `.config/mkdocs/mkdocs.yml`, `tests/unit/test_launcher.py`, `tests/unit/test_status.py`, `tests/e2e/`
- **Needs maintainer**: one run on Windows PowerShell 5.1 + Docker Desktop of `mh` alone (choose a number, Enter for the proposed step, Ctrl+C), the console shown as it looks there

## Why

Reviews of the documentation (2026-10-15, with the maintainer, and a second opinion from Gemini)
agree: the guides are now clear, but a newcomer still has to remember command names and flags.
Today `mh` typed alone runs the image with no argument, so Typer prints the whole `--help`
(`no_args_is_help=True`, `src/media_hygiene/cli/app.py`). That is a reference, not a guide.

`status` already knows where the user is (last audit, quarantine, decisions not applied, a
`classify` proposal not sorted, tag and face coverage: `services/status.py`) and already picks
**one** next step in the order of the guide (`cli/status_next.py`, `_next_step`). The menu turns
that into a guided path the user can follow without knowing any command, while **teaching** them.

## What the user sees

`mh` alone (no argument) prints, translated, in the order of the three guides
(Clean → Sort → Find, as in `documentation/*/{clean,sort,find}/quick-guide.md`):

```text
media-hygiene — where you are: last audit 2 days ago, 32 copies to set aside

 Clean the duplicates
   ✅  1  mh audit                 Find the duplicates and the broken files      🔒
   👉  2  mh clean                 Set the extra copies aside (asks first)       ↩️
       3  mh review                Choose the best shots of each burst           ↩️  optional
       4  mh history               What each run did                             🔒
       5  mh purge 20261015-…      Free the space of the quarantine, for good    ⚠️
 Sort the photos
       6  mh classify              Propose a tidy tree                           🔒
       …
 Find a photo
      12  mh tags                  Give your photos words (812 of 900 done)      🔒
       …

Enter runs step 2 (mh clean). Another number runs that step. Ctrl+C leaves.
```

- **Every step is listed**, with its full `mh …` command: the user reads the commands they will
  later type themselves (the pedagogy asked for). Not only the next one.
- **One step is proposed** (👉), chosen by the same logic as `status`, chronological: the action to
  run before the others. Enter runs it. Done steps show ✅ when the state proves it (an audit
  seen, a sort applied, tags or faces covered); unknown states show nothing rather than a guess.
- The badges are the documentation's: 🔒 photos untouched, ↩️ can be undone, ⚠️ for good,
  *optional*, 🤖 local AI (only `tags`/`classify` with a model; shown only when
  `[classify.ai] model` is set, otherwise the 🤖 line says what it would need).
- After the chosen command ends: one line **"Next time, type it directly: `mh clean`"**, then the
  usual single 👉 What next line of that command (no second menu loop by default).
- A step that needs an argument the tool knows takes it from the state (`purge <run>`,
  `undo <run>`). A step it cannot fill (`album "name" --category …`) is listed as *type it
  yourself*, with a link to its guide step, and is not selectable.

## Design constraint: the host runs the choice, not the container

The container cannot start the chosen command with the right mounts: `mh` (PowerShell or bash,
`cli/templates/mh.*.j2`) decides per command whether the photos are `:ro`, which tool folders and
which port (`-p 127.0.0.1:8088:8088`) it adds (`cli/safety.py`: `READ_ONLY_COMMANDS`,
`PAGE_COMMANDS`, `DATA_COMMANDS`). So:

1. `mh` with no argument runs a new read-only verb, `menu`, like the `launcher` data command
   (`-i` without `-t`, messages on stderr): it renders the menu on **stderr** (Rich, forced colour
   when the host terminal supports it) and writes the selectable steps on **stdout**, one per line
   (`number<TAB>command`).
2. The `mh` function reads those lines, asks for the number (`Read-Host` in PowerShell 5.1,
   `read` in bash), Enter = the proposed one, then calls itself with the chosen command:
   `mh clean`. The mounts stay exactly those of a typed command.
3. Commands that change files still ask their own confirmation (`clean`, `sort`, `purge`): the
   menu never answers for the user and never passes `--yes`.

Alternatives considered (to settle when implementing): bare `media-hygiene` showing the menu
(rejected: a `docker run cavo789/media-hygiene` without `mh` could not run the choice, keep
`--help` there); a menu that only prints, user types the command (simpler, but loses the
"Enter runs it" hand-holding the maintainer asked for).

## To decide while implementing (say it in the feedback)

- Loop or not: after a step ends, show the menu again (a guided session) or stop on the
  "type it directly" line. Proposed: stop; `mh` again shows the updated menu.
- Whether the Sort and Find sections stay folded until the clean is done (shorter screen) or are
  always shown (the pedagogy). Proposed: always shown, dimmed while a clean step is proposed.
- A setting? `[general] menu = true/false` for users who prefer `mh` alone to print `--help`:
  propose it in the feedback rather than adding it unasked.

## Acceptance

- Unit: the step list and the proposed step for each state `_next_step` covers today (blank,
  audit with copies, bursts to see, decisions not applied, old quarantine, proposal not sorted,
  nothing left) — the menu's 👉 must equal the step `status` prints, one test per state.
- Unit: `menu` writes only `number<TAB>command` lines on stdout, everything else on stderr;
  no traceback in any state (missing mounts reported as in `status`).
- Launcher templates: `mh` alone → `menu` → the chosen command run through `mh` itself; tests in
  `tests/unit/test_launcher.py` (PowerShell 5.1 syntax only, ASCII-safe like
  `test_launcher_ascii.py`) and the bash twin.
- e2e: `mh` (bash) with the choice fed on stdin runs `audit` on the demo tree.
- New verb `menu`: its page in both languages, its name in `COMMANDS_TOO`
  (`tests/support/docs/scenario.py`) and in `nav`; the three quick guides say at step 0
  "Lost? Type `mh` alone"; `docs_screenshots` gets a capture of the menu (say it must run).
- Every string through `_()`, `i18n_update`, French translated.

## Gain (estimated)

From the documentation review: today a newcomer must type at least five different command names
to reach a first clean (`audit`, `clean`, `history`, `undo`, `purge`), copied from the guide.
With the menu: one (`mh`), then Enter at each step; the names are learnt by reading them in the
menu and in the "type it directly" line. To confirm with the maintainer's run (Needs maintainer).

## Status — DONE (2026-10-16): the Windows run is measured (end of file); formerly PARTIAL (2026-10-15)

### Done
- New read-only data verb `menu` (`cli/cmd_menu.py`, `menu_catalog.py`, `menu_steps.py`,
  `menu_view.py`): the menu on stderr, `number<TAB>command` on stdout, `0` = the line Enter
  runs (written first, only when a step is proposed). Under `-t` (`docker run -it … menu`) the
  menu is shown and no line is written.
- The proposed step is the step of `status`: `_next_step` moved to `cli/status_step.py`
  (`next_step` → `NextStep` with a `Slot`), used by both; `status` output unchanged.
- 17 steps in the guides' order (clean 7, sort 6, find 4); ✅ only on proof (audit seen, no
  copy left / a clean, a proposal, a sort applied, tags, faces); `purge <run>` / `undo <run>`
  from the state, without a number when there is nothing to purge or undo; `album` listed as
  "type it yourself" with the link to the sort guide; 🤖 shown when `[classify.ai] model` is
  set, otherwise one footer line says what it would need.
- `mh.ps1.j2` / `mh.sh.j2`: `mh` alone runs `mh menu` (colour forced when the host terminal
  supports it: `-t 2` in bash, `$Host.UI.SupportsVirtualTerminal` in PowerShell), reads the
  number (`Read-Host` / `read`), Enter = line 0, then calls `mh <command>` itself; never `--yes`.
  Data commands (`launcher`, `menu`) now run without `-i` too, so the menu's docker cannot eat
  the keystrokes typed for the prompt.
- Tests: `tests/unit/test_menu.py` (one per `_next_step` state, 👉 == `status`; stdout lines
  only; missing mounts; `-t`), `tests/unit/test_launcher_menu.py` (bash `mh` really run with a
  fake `docker`; PowerShell ASCII in French; no translation can break the script), the
  read-only integration run, e2e `test_mh_alone_runs_the_step_typed_on_the_demo_tree`.
- Docs: `commands/menu.md` in both languages, `reference-commands.md` (both tables), the three
  quick guides ("Lost? Type `mh` alone" before step 1, a `menu` row in their tables), `nav`,
  `COMMANDS_TOO`, a `menu.txt` capture in the scenario. French translated.

### Decisions (to confirm)
- No loop: after the step, `mh` stops; `mh` again shows the updated menu.
- Sort and find always shown, dimmed while a clean step is proposed.
- The "Next time, type it directly: mh clean" line is printed **before** the step runs, so the
  step's own single 👉 What next line stays the last one on screen.
- No `[general] menu` setting added. Proposed: only if a user asks; `mh --help` still gives
  the help.

### Not done
- One run on Windows PowerShell 5.1 + Docker Desktop: `mh` alone, a number, Enter, Ctrl+C;
  check that the colours (`--color always` when `$Host.UI.SupportsVirtualTerminal`) show as
  colours and not as escape codes once the docker output is not a `-t` terminal, and that the
  emoji columns line up. If the codes show raw, drop the `$color` line of `mh.ps1.j2`.
  **Reason:** Needs maintainer (Windows machine).
  → step 14 of `tests/measure/mh-measure.ps1` added (inbox, 2026-10-16).
- The e2e test and `docs_screenshots` (the `menu.txt` and `help-menu.txt` captures, the
  `--help` capture of `reference-commands.md` now listing `menu`) were not run here.
  **Reason:** image build + browser, heavy: CI runs e2e; `docs_screenshots` to be run by the
  maintainer.

### Measured on Windows (2026-10-16, step 14 of mh-measure.ps1, PowerShell 5.1)
The `mh` menu, opened by hand (`. mh.ps1; mh`) in the old console (`conhost.exe
powershell.exe`) and in the usual one: colours shown as colours, emoji and step columns lined
up, the number + Enter ran `audit`, Ctrl+C at the question gave the prompt back with no red
error — in both. The `$color` line stays. No antivirus alert (the harness no longer launches
the console itself).
