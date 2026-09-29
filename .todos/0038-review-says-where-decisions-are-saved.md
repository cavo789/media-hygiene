# 0038 — `review` says where the decisions file is, as a host path

- **Priority**: medium
- **Batch**: unassigned
- **Depends**: —
- **Files**: `src/media_hygiene/cli/cmd_review.py`, `src/media_hygiene/services/reviewing.py`, `src/media_hygiene/review/session.py`, `src/media_hygiene/review/views.py`, `src/media_hygiene/review/templates/review.html.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/10-review-bursts.md`, `documentation/fr/10-review-bursts.md`

## Context

User feedback on 0.2.0 (2026-09-29): the page says "Saved in decisions.json" at each choice, and
the terminal ends with "Next: the same 'clean' command with --decisions decisions.json". Nothing
says **where** that file is: a PowerShell user will not guess it lies in the folder they mounted
on `/reports` (`$HOME\media-hygiene\reports`), and cannot open it or keep it.

The container can often name that folder: `HostPathMapper.to_host` already maps any mount
whose Windows source the mount table shows (Docker Desktop, `paths/host_sources.py`), whatever
its mount point — `services/reporting.py` uses it for `/reports`. `ReviewSession.target_name`
only keeps the file name.

## Proposal

- Resolve the host path of the decisions file once (`runtime.mapper.to_host(target)`), e.g.
  `C:\Users\Christophe\media-hygiene\reports\decisions.json`. When the source is unknown (named
  volume, Linux host, no Docker Desktop), say "decisions.json, in the folder mounted on
  /reports" rather than a container path the user never typed.
- Terminal, when the review starts (next to the address of the page): "Your choices are saved
  in <host path>."
- Terminal, after Ctrl+C: the stop summary names the file, even when no shot was set aside
  (the file may hold the report's `pairs`). The "Next" tip keeps `--decisions decisions.json`
  (what `clean` needs) and says it is that file.
- Page: the intro and the "Saved in …" status show the host path (sent in the state, next to
  `decisions_file`).
- Check that `/reports` gets its Windows source on Docker Desktop like `/data/...` mounts do
  (mountinfo shapes of `host_sources.py`); add a unit test with a `/reports` mount line.

## Acceptance

- [ ] With `-v "$HOME\media-hygiene\reports:/reports"` on Docker Desktop, the start message, the
      page and the stop summary show `C:\Users\<name>\media-hygiene\reports\decisions.json`.
- [ ] With a named volume on `/reports`, the messages name the file and the `/reports` mount,
      never an unexplained `/reports/decisions.json`.
- [ ] `--decisions` with another name or an absolute path: the messages follow it.
- [ ] New strings translated (`i18n_update`), docs EN + FR (step 10 says where the file is and
      how to open the folder), console captures refreshed with `docs_screenshots`.
