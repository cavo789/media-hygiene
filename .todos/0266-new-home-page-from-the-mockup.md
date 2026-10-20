# 0266 — The new home page, from the approved mockup: the cycle, the next step, every action a click or Ctrl+K away

- **Priority**: High — asked by the maintainer, mockup approved on 2026-10-20
- **Batch**: home
- **Depends**: 0265
- **Files**: `src/media_hygiene/review/templates/home.html.j2`, `src/media_hygiene/review/templates/home.js.j2`, `src/media_hygiene/review/templates/home_*.css.j2` (new), `src/media_hygiene/review/templates/home_*.js.j2` (new), `src/media_hygiene/review/home_app.py`, `src/media_hygiene/review/http.py`, `src/media_hygiene/review/home_views.py`, `src/media_hygiene/cli/home_state.py`, `src/media_hygiene/cli/home_reports.py`, `src/media_hygiene/services/home.py`, `src/media_hygiene/services/launcher.py`, `src/media_hygiene/cli/templates/mh_menu.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/assets/images/` (exists), `src/media_hygiene/assets/fonts/` (new), `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_home_given.py`, `tests/unit/test_launcher_home.py`, `tests/unit/test_home_page.py` (new), `tests/support/docs/browsing.py`, `README.md`, `README_FR.md`, `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`

## Context

Today the home page (0209, 0211) shows the console menu in a browser: four tables of numbered
`mh …` rows with an "Exécution" button each (capture `documentation/fr/images/home.webp`). The
maintainer asked for "a real web page, pro at once", built for the mouse, usable with the
keyboard and on a phone. It must keep the onboarding (where you are, then the next step) and
accept new features without breaking.

The mockup was approved on 2026-10-20 ("c'est génial"): the maintainer's artifact, and a
private copy in `.claude/plans/home-mockup/` (`home.html` and its images). It is the reference
for the layout, the texts (French), the tokens and the behaviours below. 0265 gives it its
catalog.

## What to do

1. **Port the mockup.** It has, in this order:
   - **the shell**: an indigo sidebar (the five stages with their counts, the tools, "Vos
     dossiers", the version, the author's signature with the avatar, the Auto/Clair/Sombre
     switch, Quit);
   - **the top bar**: the palette field, Undo when a run is undoable, a Documentation link
     following the page (the doc home, then each space's guide) and its English twin;
   - **the next step**: Enter runs it because its button has the focus on load, as in `mh menu`.
     It says why and the risk in words, and the `mh` command stays visible and copyable;
   - the cycle of the five stages, the "where you are" tiles, what the last audit found (each
     finding with its action), the audit run in the page (0211), the recent reports;
   - **one page per space**: the numbered guide, then "go further" cards. Each action has its
     doc links (FR and EN, from 0265's `doc`). The History, Reports and Settings pages show the
     folders, the version, the local AI and the privacy entries;
   - **the dialogs**: a form for the steps with fields (0265), an in-page confirmation for the
     ⚠️ steps, the "running in the PowerShell window" dialog, the copy box when `mh` does not
     relay the steps, and the stopped page (the meerkat asleep).
2. **The logic stays in Python.** `HomeState` carries the catalog with each action's state
   (available, done, proposed, its reason, its command), the tiles, the findings, the folders
   and the version. The page only draws it; the next step and the availability are never
   computed again in JavaScript.
3. **Keyboard and accessibility.**
   - A skip link, landmarks, and a focus ring for the keyboard only (`:focus-visible`).
   - ↑/↓ in the sidebar (roving tabindex), <kbd>Ctrl</kbd>+<kbd>K</kbd> or <kbd>/</kbd> for the
     palette (a combobox with `aria-activedescendant`), <kbd>?</kbd> for the keys, Esc.
   - Native `<dialog>` elements; `aria-live` for the toasts.
   - AA contrast in both themes (the blog's tokens, checked in the mockup), and
     `prefers-reduced-motion` respected.
4. **The look.**
   - The avonture.be design system: the `--mk-*` tokens, light and dark, the drawn keys and
     terminal. The meerkat gives the rest: the indigo of its outline for the sidebar, its
     apricot for "you are here".
   - The theme follows the OS by default; a choice of the switch is kept in `localStorage`
     (wrapped in try/catch).
5. **The assets**, served by the home server under `/assets/` from `media_hygiene/assets/`:
   - long cache; only files under that folder; the right content types;
   - **the CSP must allow the fonts.** `REVIEW_POLICY` (`review/http.py`) is
     `default-src 'none'` with no `font-src` (checked, 2026-10-20), which blocks every font:
     add `font-src 'self'`. Keep CSS and JS inline in the template, as today, since
     `style-src` and `script-src` do not allow `'self'`;
   - the images: avatar and 8 poses, 363 KB of WebP in all (measured);
   - **the fonts, embedded** (decided on 2026-10-20), so the page never asks Google: Bricolage
     Grotesque, Source Sans 3 and JetBrains Mono as WOFF2, Latin subsets, the OFL licences next
     to them. Their size is to measure (about 300 KB estimated from three families).

     Add them to the README's third-party table (both languages, as Leaflet is). Add one line
     there too: the meerkat images are the author's, all rights reserved (`MEERKAT.txt`).
6. **i18n.** Every string through `_()`, French in the `.po`; the page's texts are the
   mockup's, in English in the code.
7. **Docs, both languages.**
   - `commands/home.md`: what the page shows, the keyboard, the palette, the theme.
   - The quick guides where they mention the home page.
   - The `home.webp` capture (`tests/support/docs/browsing.py`) goes stale: say that
     `docs_screenshots` should run (heavy, by the maintainer).

## Decided (2026-10-20)

**How a step's arguments reach `mh`** (an album's name and category, a NAS path, a folder to
remove, how many reports to keep). Today a step's button ends the server with `100 + n` and
`mh` runs the command `mh menu` gives for `n`. `mh home` runs with a terminal (`-it`), so `mh`
cannot read the page's output.

The maintainer chose a **one-shot file**:

- The page posts `{number, fields}`. The server checks each value against its entry's pattern
  (no quote, no control character; a folder path that exists).
- It writes the command as a JSON list of words, so `Noël 2025` stays one argument, into a
  one-shot file in a tool folder that `mh` mounts from the host. Then it ends with `100 + n`.
- `mh` reads the file once (`ConvertFrom-Json` in PowerShell 5.1), removes it, and runs those
  words. Without the file, it runs step `n` as today.
- To check: which tool folder is always a host folder, never a named volume.

Two options were set aside: showing the full command to copy (one more paste each time), and
`mh` asking the arguments again with `Read-Host` (two prompts for the same thing).

Also, for the page itself: its first frame comes from the server's state, with no flash of the
wrong theme, and nothing comes from a CDN: everything is inside the image.

## Acceptance

- Unit (`tests/unit/test_home_page.py`), for each situation of the mockup (first run, audit
  done, after clean, after import, quarantine freed, proposal waiting, everything sorted):
  - the next step, the counts, and each action's state and reason in the JSON state;
  - the template renders with no undefined value;
  - `/assets/` serves only its own files (a `../` is refused) with the right content type.
- The step relay as today: a button ends with `100 + n`, and `mh` runs that step.
- The steps with fields go through the one-shot file:
  - unit tests of the server's checks (a quote, a control character, a missing folder: each
    refused with its reason);
  - a test of the PowerShell text: the file read once, then removed, and its words splatted;
  - a test of the bash text: the same.
- The maintainer looks at the real page on Windows when reviewing the pull request: one step
  relayed by PowerShell 5.1, one album created from its form.
- A keyboard-only walk, written in `commands/home.md`: skip link, sidebar, palette, the next
  step's button.
- Docs in both languages; the captures said to refresh.

## Gain (counted)

- From 20 command rows in four tables (`home.webp`) to the 46 actions of 0265, each one click
  away, or <kbd>Ctrl</kbd>+<kbd>K</kbd> and a word. The commands stay visible and copyable, so
  the page keeps teaching the console.
- The steps that need words no longer send the user to type them in the console: their form
  fills them in.
