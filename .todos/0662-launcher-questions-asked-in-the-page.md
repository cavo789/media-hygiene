# 0662 — The questions `mh` still asks in the console are asked in the page

- **Priority**: Medium
- **Batch**: one-interface
- **Depends**: 0506, 0586
- **Files**: `src/media_hygiene/cli/templates/mh_phone.ps1.j2`, `src/media_hygiene/cli/templates/mh_nas.ps1.j2`, `src/media_hygiene/cli/templates/mh_push.ps1.j2`, `src/media_hygiene/cli/templates/mh_menu.ps1.j2`, `src/media_hygiene/cli/templates/mh_cloud.ps1.j2`, `src/media_hygiene/review/templates/home_run.js.j2`, `tests/unit/`, `tests/measure/mh-measure.ps1`
- **Needs maintainer**: a run on Windows PowerShell 5.1 + Docker Desktop (with Avast) of each question moved

Filed by the UX / speed / security review of 2026-11-10 (asked by the maintainer; analysis only, no code changed).

## Context

0586 moves the *Yes* of the writing steps into the page (`--yes` once confirmed there) and
0506 runs host steps beside the page. What they do not list: the launcher's own questions.
*Measured* (`grep -c Read-Host src/media_hygiene/cli/templates/*.j2`, 2026-11-10): **10**
`Read-Host` — `mh_phone.ps1.j2` 3, `mh_nas.ps1.j2` 3 (user name, password, retry),
`mh_push.ps1.j2` 2, `mh_menu.ps1.j2` 1, `mh_cloud.ps1.j2` 1. Each one sends the user of the
page back to the PowerShell window.

## Proposal

- An inventory first (in this TODO, then a test): each `Read-Host`, what it asks, whether the
  page already knows the answer (a count to confirm, a name, a secret).
- A generic *question* channel next to the step channel of 0586: `mh.ps1` writes the question
  (id, kind: yes/no · text · secret, the sentence) where it writes the step's state; the page
  shows it in the follow dialog; the answer comes back by the same way. The console keeps
  asking when no page is open (0513: the console stays a full interface).
- **The NAS password** is the hard one: typed in the page it crosses the home server. Only
  from the PC's door (never a phone: `write_routes`), never written to a file in clear, handed
  to `mh.ps1` which keeps it as today (encrypted for the Windows user). If no safe hand-over
  is found, the password stays a console question and the page says so in one line — decide
  with a measurement, not by default.
- `mh menu`'s own prompt stays (it is the console's menu).

## Acceptance

- [ ] The inventory table in this TODO, one line per `Read-Host`, with its outcome
- [ ] A test counts the `Read-Host` left and names why each one stays
- [ ] `mh import --phone`, `mh push`, `mh folders add --backup` run from the page without a
      look at the console (a step of `mh-measure.ps1`), no Avast alert
- [ ] Docs EN + FR

## Where the user gains

Before: 10 console questions (measured). After: only those listed as kept on purpose
(estimated: the menu's, perhaps the password).
