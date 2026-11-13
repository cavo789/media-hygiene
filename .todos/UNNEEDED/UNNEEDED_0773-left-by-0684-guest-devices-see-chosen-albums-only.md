# 0773 — What 0684 left: Guest devices: a tablet or TV at relatives' sees the chosen albums only, never the whole library

- **Priority**: Medium
- **Batch**: lan-security
- **Depends**: —
- **Files**: `.todos/PARTIAL/PARTIAL_0684-guest-devices-see-chosen-albums-only.md`, `src/media_hygiene/review/lan_paths.py`, `src/media_hygiene/review/lan_app.py`, `src/media_hygiene/review/lan_phones.py`, `src/media_hygiene/review/report_files.py`, `src/media_hygiene/share/album_link_door.py`, `src/media_hygiene/share/album_links.py`

Split from section 0684 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/PARTIAL/PARTIAL_0684-guest-devices-see-chosen-albums-only.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- *Until tonight* (a guest pairing ending with the visit): guests last like a family phone and are
- The reports' hidden files (`.mh-*`) are still served to a family phone. **Reason:** decided

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.

## Status — UNNEEDED (2026-11-13)

Redundant: checked against the code.
- *Until tonight*: done by 0709 (`review/lan_guest_day.py`: a guest ends at the next local
  midnight, kept or run-only; `tests/unit/test_lan_guest_day.py`; the card shows `until`).
- The reports' `.mh-*` files: refused to every role by 0710 (`review/report_files.py`,
  `_HIDDEN`; `tests/unit/test_report_hidden_files.py`).
