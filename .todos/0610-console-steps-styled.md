# 0610 — Read-only steps in the page: styled output, not plain text

- **Priority**: Low
- **Batch**: one-interface
- **Depends**: 0567 (PARTIAL)
- **Files**: `/console/<step>/` page

## Why (review of feedback-2026-11-03-iterate (2026-11-05))

0567 shows status, reports, inventory and config as plain text in a <pre>. Decided: style them (tables) from the same recording Rich console (`export_html` or equivalent), one source of truth with the terminal.
