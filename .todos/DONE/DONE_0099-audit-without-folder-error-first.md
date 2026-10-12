# 0099 — Audit without any folder: the error comes after a reassurance and a `:ro` tip

- **Priority**: Medium — the very first mistake of a beginner (forgetting `-v`)
- **Batch**: guidance
- **Depends**: —
- **Files**: `src/media_hygiene/cli/cmd_audit.py`, `src/media_hygiene/cli/safety.py`, `src/media_hygiene/services/data_checks.py`, `tests/unit/test_audit_no_folder.py` (new)

## Context

UX review of 2026-10-12. `docker run --rm -it cavo789/media-hygiene audit` (no `-v`, the most
likely first mistake) prints, in this order:

```text
🔒 Read-only: your photos and videos are not touched.
💡 Add :ro to the -v of your photo folders: the system itself then forbids any change.
https://github.com/cavo789/media-hygiene/blob/main/documentation/en/reference-safety.md
──────────────── Audit ────────────────
❌ No folder to analyse under /data.
💡 Mount your folders, e.g. -v "C:\Photos:/data/c/Photos:ro".
```

Three lines speak of photos and of `:ro` that do not exist yet, then a rule, then the real
problem. A beginner reads the first line ("not touched": fine) and may miss the ❌ below.

## Goal

- With no folder under `/data`, check it before the read-only banner and the `:ro` tip: the ❌
  and its 💡 come first and alone, then exit.
- The 💡 says it in beginner words: "The tool only sees the folders you give it with -v." then
  the example, then a link to step 1.
- Same order for the other commands that need `/data` (`classify`, `review`, `clean`…).

## Acceptance

- CLI test: `audit` without `/data` folders prints the ❌ as its first line and no 🔒/`:ro`
  line.
