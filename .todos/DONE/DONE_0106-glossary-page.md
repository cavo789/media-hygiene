# 0106 — A glossary: the words a beginner meets before they are explained

- **Priority**: Medium — the vocabulary is the main barrier for a non-technical reader
- **Batch**: docs
- **Depends**: —
- **Files**: `documentation/en/reference-glossary.md` (new), `documentation/fr/reference-glossary.md` (new), `documentation/en/README.md`, `documentation/fr/README.md`, `README.md`, `README_FR.md`

## Context

UX review of 2026-10-12, read as a "John Doe" who has never used a terminal. Step 1 explains
its command part by part, very well; but the words keep coming afterwards, each explained once
on the page that introduces it, if at all: *container*, *image*, *volume* (step 2), *mount* /
*mount point*, *`:ro`*, *cache*, *quarantine*, *journal*, *run*, *sidecar*, *orphan sidecar*,
*near duplicate*, *re-encoded video*, *burst series*, *SHA-256* / *fingerprint*, *tier*
(`--tier near`, `near-all`), *decisions*, *port* (`8088`), *workbook*, *plan*, *hard link*,
*GPS cluster*, *vision model*. The audit summary itself shows four of them on its first screen
(*orphan sidecars*, *near duplicates*, *re-encoded videos*, *burst series*). A reader who
lands on a command page from a search never saw step 1.

## Goal

- One reference page, *Words of this guide* / *Les mots de ce guide*: one line per word, plain
  language, an everyday example, and the link to the page that shows it. Alphabetical, short.
- Linked from the documentation index (Reference), the README, and on the first use of a word in
  the command pages ("In short" sections).

## Acceptance

- Both languages, same anchors; `test_documentation` passes.
