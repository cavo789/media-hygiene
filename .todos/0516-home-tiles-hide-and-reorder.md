# 0516 — Home page: the user hides and reorders the *Where you are* tiles

- **Priority**: Low
- **Batch**: home
- **Depends**: 0515
- **Files**: `src/media_hygiene/cli/home_tiles.py`, `src/media_hygiene/review/home_parts.py`, `src/media_hygiene/review/templates/home_draw.js.j2`, `src/media_hygiene/review/templates/home_parts.css.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/`, `documentation/fr/`

## Reported (maintainer, 2026-10-30)

After 0515 (9 tiles, 3 × 3), let the user hide, move… the blocks of *Where you are*.

## Questions to settle first

1. **Where the choice lives.** Browser storage (per browser, lost with site data, the phone
   would differ) or the tool folders (survives, same on every browser)? `/config` holds only
   `config.toml`: a `[home] tiles = ["audit", "copies", …]` list (order = order, missing =
   hidden) written with tomlkit like `places`, proven by reading it back. Proposed: `config.toml`,
   but it is a new setting — `few-settings` asks whether it is worth one.
2. **Which blocks.** Only the tiles, or also the page's sections (cycle, findings, reports)?
   Proposed: tiles only first.
3. **How.** An *Edit* button on the box: each tile gets ✕ (hide) and ← → (move, keyboard
   reachable; drag optional), *Reset* brings back the default; hidden tiles listed to bring back.
   A tile asking for action (`Pill.TODO`, e.g. intruders) hidden: still hidden? Proposed: yes,
   the user chose; the Clean badge and the 👉 next step still tell.
4. The phone (read-only, `phone-read-only`): it shows the PC's layout, never edits it.

## To do (once settled)

1. Stable tile ids (`HomeTile.id`), the stored order applied, unknown ids ignored, new tiles of
   a later version appended at the end (never hidden by an old list).
2. The edit mode, saved and read back, *Reset*.
3. Tests: order applied, hidden, unknown id, a new tile appears, reset, a save read back.
4. Docs EN + FR (home page chapter); `docs_screenshots` should then run — not run by the TODO.
