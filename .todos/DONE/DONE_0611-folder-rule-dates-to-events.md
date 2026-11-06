# 0611 — A folder rule turned into dates moves to events/

- **Priority**: Low
- **Batch**: events
- **Depends**: 0578 (DONE)
- **Files**: `src/media_hygiene/classify/remember_rule.py`

## Why (review of feedback-2026-11-03-iterate (2026-11-05))

0578 still replaces in place, in config.toml, a folder rule turned into dates (0393). Decided: move it to `events/` (removed from config.toml with tomlkit, comments kept): one place for events, config.toml no longer written by *Remember as a rule*. Test the move byte for byte.

## Resolution (2026-11-06)

DONE: `remember_rule` removes the folder rule from config.toml (`remove_rules`, tomlkit, comments kept) then adds the event to `events/<year>.toml`; config.toml put back byte for byte if the event cannot be written. Tests: `test_a_folder_rule_turned_into_dates_moves_to_events`, `test_a_folder_name_rule_is_turned_into_dates_in_events`.
