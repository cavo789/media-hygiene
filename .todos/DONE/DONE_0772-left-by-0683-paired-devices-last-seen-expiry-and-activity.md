# 0772 — What 0683 left: Paired phones and TVs: last seen, expiry when unused, *Forget all*, and what each one did

- **Priority**: Medium
- **Batch**: lan-security
- **Depends**: —
- **Files**: `.todos/DONE/0683-paired-devices-last-seen-expiry-and-activity.md`, `src/media_hygiene/review/lan_phones.py`, `src/media_hygiene/review/lan_phones_api.py`, `src/media_hygiene/review/lan_app.py`, `src/media_hygiene/review/templates/home.js.j2`, `tests/unit/test_lan_phones.py`

Split from section 0683 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0683-paired-devices-last-seen-expiry-and-activity.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- Flush of the activity counts at stop.
- TVs' `last_seen`: not written (`slideshow/screens.py` at 199 lines caches tokens in memory).
- The card lists name, paired on, last seen, address; rename and forget read back
- Expiry tested with a clock; *Forget all* tested
- What happens when `/lan` moves or is restored from an older copy: written and tested
- Docs EN + FR

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.
