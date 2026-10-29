# 0475 — After an import: a chain of follow-up actions the user switches on or off

- **Priority**: Medium
- **Batch**: phone
- **Depends**: 0474, 0476, 0477
- **Files**: `src/media_hygiene/services/launcher_phone_end.py`, `src/media_hygiene/cli/cmd_import.py`, `src/media_hygiene/config/`, `src/media_hygiene/review/templates/` (home page run)

## Why

The maintainer, 2026-10-29: `import` now runs `audit` at once (0451,
`services/launcher_phone_end.py`). Go further: after an import, a list of actions to run in a
row (audit, then `tags`, then the place names of 0474…), each one switched on or off by the user.

## What

- One ordered list, shown before it starts (« After the import: ✅ audit · ✅ tags 🤖 · ☐ place
  names 🌐 »), each line a toggle; the choice is kept in `config.toml` (`[import] then = ["audit", "tags"]`,
  a setting: it differs between users) and changeable from the list itself.
- `audit` stays first and cannot be removed while another action needs it (tags and places read
  the index). Each action runs only on the **new files** of the import when it can (tags:
  the files not yet described).
- 🤖 flag on `tags` (needs the local AI model): skipped with one line when Ollama is not
  reachable, the chain goes on. 🌐 flag on 0474's online step: it keeps its own consent.
- Same chain in the console and on the home page (the run shown step by step, as the audit today).
- Interrupted (Ctrl+C, PC asleep): the done steps stay done; the next `mh` offers the rest.

## To decide

Defaults: audit on (today's behaviour); tags on or off (time: to measure on the maintainer's PC
for a typical import, e.g. 100 photos); place names off (0474).

## Acceptance

- Toggles saved and read back from `config.toml`; a disabled action never runs; tags without
  Ollama skips cleanly; a chain stopped halfway resumes from the next step.

## Decided (2026-10-29, the maintainer)

Defaults: audit, tags and place names all on (place names still ask their own consent, 0474).

## Decided (2026-10-29, the maintainer): the goal, end to end

Plug the phone, import, and minutes later the slideshow is ready: import (0476, a period) →
audit → tags → places (0472, 0474) → events named (0477) → the last line, on the console and the
home page: « 📺 Your slideshow *Promenade à Liège* is ready: send it to the TV? » (one click
starts `slideshow` on the new event). Measure the whole chain for 100 photos on the
maintainer's PC (a step of `mh-measure.ps1`); tags is the slow step.
