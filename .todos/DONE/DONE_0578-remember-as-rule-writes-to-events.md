# 0578 — "Remember as a rule" writes its date ranges to /config/events/, not config.toml

- **Priority**: Medium
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/classify/event_store.py`, `src/media_hygiene/review/sort_*.py`, `src/media_hygiene/search/`, `documentation/en/`, `documentation/fr/`

## Asked (maintainer, review of 2026-11-02)

0576 (commit 11eb0511) moved the events remembered by *Move to an event…* and *Events found*
into `/config/events/<year>.toml`. *Remember as a rule* on the review-sort and search pages
still writes its `date_range` rules into `config.toml`. Decision: they go to `events/` too —
one place for what the tool remembers; `config.toml` stays the user's.

## What

- *Remember as a rule* writes a `date_range` rule through `event_store` (the year it starts).
- Other rule kinds stay in `config.toml`.
- Docs en + fr where the button is described.

## Tests

- A rule remembered from review-sort and from search lands in `events/<year>.toml`, read back.
- `config.toml` unchanged byte for byte.
