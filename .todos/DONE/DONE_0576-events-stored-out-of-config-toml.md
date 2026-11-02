# 0576 — Remembered events live in /config/events/, not in config.toml

- **Priority**: High
- **Batch**: search
- **Depends**: 0575
- **Files**: `src/media_hygiene/classify/rules_file.py`, `src/media_hygiene/classify/event_files.py`, `src/media_hygiene/search/move_event.py`, `src/media_hygiene/search/found_desk.py`, `src/media_hygiene/config/classify_rules.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/cli/` (`config tidy`, 0550), `documentation/en/`, `documentation/fr/`

## Asked (maintainer, 2026-11-02)

Every event remembered (*Move to an event…*, 0556; *Events found in your folders*, 0557) is
written into `config.toml` as a `[[classify.rules]]` block of about 5 lines (name, dates,
devices). 196 found events → about 1 000 more lines (estimated: 5 lines × 196). `config.toml`
is read by every command; these events are used by a few screens only (Events tab, late
files, classify's date rules). The maintainer wants `config.toml` kept small and readable.

## What

1. Events (`match = "date_range"` written by the tool) go to `/config/events/` — the folder
   already holding `<start>-<name>.toml` refusals and `not-events.toml` (`event_files.py`).
   Decide while doing it, say which in the commit: one file per event
   (`events/<start>-<name>.toml`, the refusals file it already links — one place per event)
   or one file per year. `config.toml` keeps at most one line pointing to the folder, or none
   (the folder is found by convention, like `people/`).
2. Readers: one loader (`read_rules` + the TOML-files loader of 858571bf) gives the events
   to the pages and to classify, read only when needed (not on every command).
3. Writers (`add_rule`, `replace_rule`, `remember_event`) write the event file, atomically,
   read back; tomlkit, comments kept.
4. Existing `config.toml` holding such events: moved to `events/` once, by `config tidy`
   (0550) or at the first write — **ask the maintainer which** before coding (a write into
   the user's config without being asked is to avoid). Hand-written rules stay in
   `config.toml`.
5. What happens when an event file is renamed, deleted or edited by hand (workflow rule:
   anything stored by path) — tested.

## Acceptance

- [ ] Remembering 196 events leaves `config.toml` unchanged in size (test).
- [ ] Events tab, late files, classify date rules read the events from `events/` (tests).
- [ ] Migration path chosen by the maintainer, tested on a config.toml holding events.
- [ ] Docs en + fr (config reference, Events tab), `i18n_update` + French.

Related: 0575 (Confirm acts on the rows shown only) first, so no new 196-event write lands
before the storage moves.

## Decided (2026-11-02)

By the maintainer, in `/todo:iterate`: the events already in `config.toml` are moved to
`/config/events/` by `config tidy` (0550), not at the first write; one file per year
(`/config/events/<year>.toml`).
