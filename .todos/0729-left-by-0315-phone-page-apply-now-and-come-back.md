# 0729 — What 0315 left: Freeing a phone: "Apply now", then the page again with what is left

- **Priority**: Medium
- **Batch**: phone
- **Depends**: —
- **Files**: `.todos/DONE/0315-phone-page-apply-now-and-come-back.md`, `src/media_hygiene/cli/templates/mh_phone_free.ps1.j2`, `src/media_hygiene/services/launcher_phone_free.py`, `src/media_hygiene/cli/cmd_phone_review.py`, `src/media_hygiene/review/phone_app.py`, `src/media_hygiene/review/phone_session.py`, `src/media_hygiene/review/templates/phone_review.html.j2`
- **Needs maintainer**: a measurement on Windows + Docker Desktop (round trip for 20 files)

Split from section 0315 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0315-phone-page-apply-now-and-come-back.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- Points 1–3: the loop of `_mh_phone_clear` (page → batches proved and moved → phone listed
- The two-round integration test and the `test_launcher_phone.py` loop test: they follow the
- The measure (round trip for 20 files): follows the loop; estimated from 24 MB/s × 2 reads

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.
- Part of this needs the maintainer (see *Needs maintainer*): do the code part, leave the rest said in the report, never guess it.
