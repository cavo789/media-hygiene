# 0850 — The folders-tree picker on every page that asks for a folder

- **Priority**: Medium
- **Batch**: one-interface
- **Depends**: none
- **Files**: `src/media_hygiene/review/templates/folder_tree.js.j2` (`mhPickFolder`, 0824 commit d4748a5a), the import and classify pages

## Why (review of feedback-2026-11-27-iterate, maintainer's choice)

0824 put the library's folders tree in a dialog to pick the albums root. The same picker belongs on every place a folder is typed (feature follows its kind).

## Do

- List every page and entry point where a folder is typed (grep the forms: import `--to`, classify target, others found) and name each in the report.
- Each gets the same 📂 button and dialog from the shared template; typing stays for a folder not yet audited (the tree lists indexed folders only).
- Same tests on every page of the kind (parity).
