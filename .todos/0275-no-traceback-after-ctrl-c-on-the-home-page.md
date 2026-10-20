# 0275 — No traceback after Ctrl+C on the home page

- **Priority**: medium
- **Batch**: unassigned
- **Depends**: —
- **Files**: TBD

## Context

The maintainer opened the home page from the `mh` menu loop (PowerShell console) and pressed
Ctrl+C several times. The page ended cleanly, then a further Ctrl+C printed a Python traceback
(2026-10-20):

```text
La prochaine fois, tapez-la directement : mh home
✅ Accueil prêt, ouvrez http://127.0.0.1:8088/ dans votre navigateur. Ctrl+C l'arrête.
Votre navigateur s'ouvre sur http://127.0.0.1:8088/ ; sinon, ouvrez cette adresse.
^C
^C
✅ Accueil fermé ; vos photos n'ont pas été modifiées.

^CException ignored on threading shutdown:
Traceback (most recent call last):
  File "/usr/local/lib/python3.14/threading.py", line 1577, in _shutdown
    atexit_call()
  File "/usr/local/lib/python3.14/threading.py", line 1548, in <lambda>
    _threading_atexits.append(lambda: func(*arg, **kwargs))
  File "/usr/local/lib/python3.14/concurrent/futures/thread.py", line 31, in _python_exit
    t.join()
  File "/usr/local/lib/python3.14/threading.py", line 1133, in join
    self._os_thread_handle.join(timeout)
KeyboardInterrupt:
```

The shipped image must never show a traceback (product rule). The likely cause, not yet
checked: when the interpreter exits, it waits for a `ThreadPoolExecutor` worker that is still
running. Candidates are asyncio's default executor (`asyncio.to_thread` for `GET /api/state`,
`/reports/`, `/assets/`) and the page's audit thread. A Ctrl+C during that wait breaks into
`threading._shutdown`. One `GET /api/state` can take seconds since 0266/0267: it counts the
quarantine, lists the top of each folder, and may ask Docker Hub (3 s at most).

Where to look: `src/media_hygiene/services/home.py` (`serve_home`, the `KeyboardInterrupt`
handling), `src/media_hygiene/services/home_audit.py`, `src/media_hygiene/__main__.py`, and
the other page servers that handle `KeyboardInterrupt` the same way
(`services/review_serving.py`, `reviewing.py`, `search_pages.py`, `people_page.py`,
`sort_reviewing.py`, `phone_review.py`): the same exit may hit every page.

## Acceptance

- [ ] Reproduce first and say what the thread still running is (measured, not guessed).
- [ ] Ctrl+C, pressed any number of times while a page is open or closing, ends with the
      page's own message and exit code, never a traceback (in the image, `MEDIA_HYGIENE_DEBUG`
      unset).
- [ ] The fix covers every page server that shares the exit path, not only `home`.
- [ ] A test proves it, e.g. a worker thread still busy at exit plus a second
      `KeyboardInterrupt`: nothing on stderr but the expected lines.
- [ ] Checked by the maintainer on Windows from the `mh` menu loop (PowerShell 5.1).
