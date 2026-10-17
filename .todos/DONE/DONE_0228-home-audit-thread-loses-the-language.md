# 0228 — `mh home`: the audit run from the page speaks English (its thread loses the language)

- **Priority**: High — a French user sees half of the screen in English
- **Batch**: i18n
- **Depends**: —
- **Files**: `src/media_hygiene/services/home_audit.py`, `src/media_hygiene/services/runtime.py`, `src/media_hygiene/actions/parallel.py`, `src/media_hygiene/index/rematch.py`, `src/media_hygiene/index/takeout_rows.py`, `tests/`

## Symptom

Maintainer, 2026-10-17, `mh home` with `config.toml` set to French:

- In the *Audit in this page* card ("Auditer dans cette page"), the titles and the button are
  French, but the steps are English ("Listing media files — 51,818", "Comparing files of equal
  size", "Proving identity (full SHA-256)", "Recognising what you had set aside"), and so are the
  lines under them ("Last audit: … 51,818 files, 0 extra copies", "3,183 burst series: optional,
  ~35 h 22 min in 'review'…").
- In the terminal, "Accueil prêt…" is French, but the lines the audit prints are English:
  "1,017 unchanged folders taken from the index, 0 read.", the 💡 tip about `audit --full`, and
  "No new or changed file since the last audit…".
- The numbers use English separators (51,818 instead of 51 818).

## Cause (found by reading the code, not reproduced)

- Every one of these messages **has** its French translation in `media_hygiene.po` (checked:
  "Listing media files" → "Recherche des fichiers médias", the `{reused} unchanged folders`
  plural, the `burst series: optional` plural, and so on).
- `i18n/__init__.py` keeps the language in `ContextVar`s (`_LOCALE`, `_ACTIVE`), with English
  as the default.
- `services/home_audit.py:68` starts the audit with a bare `threading.Thread(target=self._work)`.
  A new thread does **not** inherit the context, so `_()` and `ngettext()` fall back to English
  there, and so does the number formatting, if it reads the locale. The routes that use
  `asyncio.to_thread` (`review/home_app.py`) do copy the context, which is why the page's own
  texts are French.

## To do

1. Start the thread inside the caller's context:
   `ctx = contextvars.copy_context(); threading.Thread(target=ctx.run, args=(self._work, progress))`.
   Better, add one helper, e.g. `i18n.in_this_language(fn)` or a `start_thread(...)`, so every
   thread does it the same way.
2. Check the other threads and pools, which have the same problem: `ThreadPoolExecutor` does
   not copy the context for its workers either.
   - `services/runtime.py:87` (a `threading.Thread`)
   - `actions/parallel.py:69` (the workers of `clean`: are their skip and incident reasons
     translated? to check)
   - `index/rematch.py:53` and `index/takeout_rows.py:80`
   - The process pool (`_ImagePool`) starts new processes: does the French survive the fork?
     A decode error message would show it (to check).
3. Test: install French, start `HomeAudit`, wait, then assert that the progress labels and the
   end summary are French ("Recherche des fichiers médias"). A second test does the same for
   one `clean` incident made by a worker.
4. A lint-style test forbidding a bare `threading.Thread(` or `ThreadPoolExecutor(` outside the
   helper, so the mistake does not come back.

## Done

Fixed by commit 53705c4 (branch `iterate/2026-10-17`, PR #11), made in another session of
the same day: `install()` now sets the language for the whole process (`_Installed`). A
`using()` context still overrides it for one thread or task. The home audit thread and every
page server translate, and numbers follow the same locale. Item 2 of *To do* (the
`ThreadPoolExecutor` workers of `clean`) is covered by the same process-wide default.
