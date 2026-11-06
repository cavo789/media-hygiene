# 0612 — Late photos: "remember as an event" ticked by default there only

- **Priority**: Low
- **Batch**: events
- **Depends**: 0573 (DONE), 0558
- **Files**: move to an event dialog

## Why (review of feedback-2026-11-03-iterate (2026-11-05))

0573 left the box unticked everywhere. Decided: in the late photos flow (0558), which widens an event, it is ticked by default; elsewhere unchanged.

## Resolution (2026-11-06)

DONE: `move_dialog.js.j2` ticks the box when the late photos view is shown (`window.mhLate.shown()`), unticked elsewhere. Docs (library.md en/fr) say so. Test: `test_the_dialog_box_is_there_unticked`.
