# 0737 — What 0478 left: Import and be clean in one go: duplicates, bursts, the new event's slideshow (rest of 0475)

- **Priority**: Medium
- **Batch**: phone
- **Depends**: —
- **Files**: `.todos/DONE/0478-import-clean-in-one-go.md`, `src/media_hygiene/services/launcher_phone_end.py`, `src/media_hygiene/config/import_settings.py`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/services/clean.py`

Split from section 0478 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0478-import-clean-in-one-go.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- Decided 2: the burst page opened on the import's bursts only, with tags/places/name running in
- Decided 3: the slideshow of the new event only (`slideshow` has no `--since`/files option yet;
- Decided 4 and 5 (rest of 0475/0476): home-page chain followed live, resume after interruption,
- `copies` runs after `tags` (it lives in `phone-end`): the 🤖 model also describes the copies

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.

## Status — DONE (2026-11-13)

Checked against the code, item by item:
- Decided 2 (burst page on the import's bursts, tags/places beside it): done by 0480
  (`review --imported --since`, step `bursts` of `mh_phone.ps1.j2`, `import-bursts.json`).
- Decided 3 (the new event's slideshow): done, `slideshow --folder <phone folder> --since <period>`
  (`cmd_slideshow.py`, the TV question of `mh_phone.ps1.j2`).
- Decided 4 (chain followed live, resumed after interruption, toggles): done by 0604
  (`import-chain.json`, `review/import_chain_api.py`, `mh import --chain --from-step`) and 0481
  (toggles saved in `[imports] then`).
- `copies` after `tags`: done by 0480 (order audit → copies → bursts → tags).
- Left, refiled as 0785: Decided 5 (the period buttons on the home page) and the end line's
  « N bursts reviewed ».
