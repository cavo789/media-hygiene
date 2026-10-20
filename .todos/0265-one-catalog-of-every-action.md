# 0265 — One catalog of every action: `mh menu`, the home page and its palette read it; a test keeps it exhaustive

- **Priority**: High — the base of 0266, 0267 and 0268; asked by the maintainer (2026-10-20)
- **Batch**: home
- **Depends**: —
- **Files**: `src/media_hygiene/cli/menu_catalog.py`, `src/media_hygiene/cli/menu_catalog_import.py` (new), `src/media_hygiene/cli/menu_catalog_clean.py` (new), `src/media_hygiene/cli/menu_catalog_sort.py` (new), `src/media_hygiene/cli/menu_catalog_find.py` (new), `src/media_hygiene/cli/menu_catalog_tools.py` (new), `src/media_hygiene/cli/menu_steps.py`, `src/media_hygiene/cli/menu_view.py`, `src/media_hygiene/cli/status_step.py`, `src/media_hygiene/cli/home_state.py`, `src/media_hygiene/review/home_views.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_menu.py`, `tests/unit/test_menu_catalog.py` (new), `CLAUDE.md`, `documentation/en/commands/menu.md`, `documentation/fr/commands/menu.md`

## Context

`mh menu` (console) and the home page (`mh` alone) both read `cli/menu_catalog.py`: three
guides plus the Windows setup, 20 numbered steps and one to type (counted, 2026-10-20). Missing
from it, counted against `commands()` (the `--help` list) and `HOST_COMMANDS` the same day:
`phone`, `phone --free`, `import`, `folders` (list, `add`, `add --backup`, `remove`), `update`,
`crosscheck`, `review --near/--pairs/--junk/--gone`, `reports` (and `--prune`), `config`,
`status`, `launcher`, `people --forget`, `clean --delete`, `explorer --remove`. Nothing stops a
new verb from being forgotten: the maintainer asked that the menu stay exhaustive by itself.

The maintainer approved a mockup of the new home page on 2026-10-20 (private copy:
`.claude/plans/home-mockup/home.html`). Its `ACTIONS` and `SPACES` arrays are the reference for
this catalog: 46 entries (counted), titles and texts in French, each with its doc chapter.
Decided with it:

- **A five-stage cycle**: Import → Clean → Sort → Find → Back up (the last one waits for 0264,
  `mh backup`). Three tools sit apart: History and undo, Reports, Settings.
- **The maintainer is the only user**: `mh menu` may be regrouped and renumbered freely.

## What to do

1. **The entries.** `Step` (frozen dataclass) gains:
   - `id` and `space`: an enum of the 5 stages and 3 tools;
   - `title` (what the user gets), `text`, `command`, `risk` (🔒 ↩️ ⚠️ as today);
   - `kind`: console, page or host, i.e. run in the terminal, in its own page, or by `mh` itself;
   - `optional`, `ai`, `windows`, `icon` (a name the page maps to its SVG) and `keywords`
     (translated: the palette's everyday words, e.g. "téléphone", "NAS", "annuler");
   - `doc`: page path plus the English and French anchors. The URL follows the locale as
     `DOC_PAGES` users do today;
   - `fields` for the steps that take arguments (album name and category, a NAS path, a folder
     to remove, how many reports to keep): label, example and pattern. 0266 turns them into
     forms; the console keeps "type it yourself";
   - `planned`: shown but not runnable, for `backup` until 0264.

   Each space has groups: numbered guides, then "go further". Import has two guides, "from a
   phone" and "from your NAS or an old disk", because they are independent.
2. **One module per space or group of tools** (the 200-line cap). `menu_catalog.py` assembles
   them in the cycle's order.
3. **Exhaustive at run time.** `build_menu` adds an "Other commands" group holding every
   visible command of `commands()` and every `HOST_COMMANDS` name that no entry names, with its
   `--help` short text. So a command is never missing from the menu, even before it has a place.
4. **Exhaustive at commit time.** `tests/unit/test_menu_catalog.py`, built like
   `test_docs_commands.py`:
   - every visible command of `commands()`, every `HOST_COMMANDS` name and every `ReviewMode`
     value has an entry, so "Other commands" stays empty in the shipped tool;
   - every entry names an existing verb (no stale entry after a rename);
   - every `doc` page exists in `documentation/en` and `documentation/fr`, with its anchors
     (reuse the helpers of `tests/unit/test_documentation.py`).

   The failure message names the fix: "`<verb>` has no place in the menu: add it to
   `cli/menu_catalog_<space>.py`".
5. **`mh menu` in the console.**
   - Grouped by the five stages, then the tools, numbered across.
   - Unchanged marks: 👉 the proposed step (Enter), ✅ done, the badges.
   - "(type it yourself)" for the steps with fields, "(planned)" for `backup`.
   - The PowerShell side (`mh_menu.ps1.j2`) still reads `number<TAB>command` lines: no change
     there.
6. **The next step.** `next_step` proposes `import` when the NAS (a `--backup` folder) holds
   files the PC lacks. It comes after an old quarantine and before a classify proposal, as in
   the mockup. `backup` joins with 0264.
7. **CLAUDE.md.** "A new verb needs … its entry in `cli/menu_catalog_*.py`", next to the doc
   rule.

## Acceptance

- The new test as described. A fake extra command, registered in a test, appears under
  "Other commands".
- `test_menu.py` updated: the groups, the numbering across them, Enter on the proposed step,
  the Windows steps left out of the bash `mh`.
- The capture of `mh menu` in `documentation/{en,fr}/commands/menu.md` goes stale: say that
  `docs_screenshots` should run (heavy, by the maintainer).

## Gain (counted)

- **The menu**: 20 numbered steps and 1 to type (counted, `menu_catalog.py`) → the 46 actions
  of the mockup's catalog (counted), each linked to its doc chapter.
- **A new verb can no longer be forgotten**: the commit gate fails until it has its entry, and
  until then it still shows in "Other commands".
