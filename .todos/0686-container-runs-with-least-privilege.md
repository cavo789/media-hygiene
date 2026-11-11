# 0686 — `mh` runs its containers with the least privilege: no capabilities, no network where none is needed

- **Priority**: Medium
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/services/launcher.py`, `tests/e2e/`, `tests/measure/mh-measure.ps1`, `documentation/en/reference-safety.md`, `documentation/fr/reference-safety.md`
- **Needs maintainer**: a run on Windows PowerShell 5.1 + Docker Desktop of every verb with the new flags (a step of `mh-measure.ps1`)

Filed by the UX / speed / security review of 2026-11-10 (asked by the maintainer; analysis only, no code changed).

## Context

The image runs as a non-root user (`USER` in the `Dockerfile`) and mounts the photos `:ro`
for read-only verbs: good. *Measured* (`grep` over `cli/templates/` and
`services/launcher*.py`, 2026-11-10): the `docker run` lines carry **no** `--cap-drop`, no
`--security-opt no-new-privileges`, no `--network`, no `--read-only`, no `--pids-limit`.

Why it matters: the audit decodes **every file of the library** with Pillow, the HEIF and
RAW decoders and a built `ffmpeg` — parsers where memory bugs are found regularly — and a
photo can come from anywhere (mail, WhatsApp, a download). A crafted file exploiting one
runs code in the container with the default capabilities and **the default network**: it
can read every photo mounted and send them out.

## Proposal

- Every `docker run` of the launcher: `--cap-drop ALL --security-opt no-new-privileges`,
  `--pids-limit` (a generous figure: the process pool + ffmpeg).
- `--network none` for the verbs that neither serve a page nor call a service: `audit`,
  `clean`, `sort`, `undo`, `purge`, `inventory`, `classify` (without AI), `backup`… — a
  flag per catalog entry (`needs_network`), tested like the read-only flag. Verbs with a
  page keep their published port; those using Ollama / Nominatim keep the network.
  This is the strongest line: no network, no exfiltration, whatever the bug.
- `--read-only` root file system with a `tmpfs` for `/tmp`: to try (Python caches, fonts,
  `openssl` for the LAN certificates write where?) — keep only if every verb passes.
- Said in `reference-safety.md` in one paragraph: "what if a photo is malicious".
- The same flags in the `docker run` lines the docs show (captures: `docs_screenshots`).

## Acceptance

- [ ] The e2e suite passes with the flags (CI), and the Windows step (maintainer)
- [ ] A test over the catalog: each verb declares whether it needs the network; the
      launcher's line carries `--network none` for the others
- [ ] The audit's time unchanged (the flags cost nothing — to confirm by one timed run)

## Where the user gains

Before: a decoder bug gives code with the default capabilities and internet access next to
the whole library. After: no capability, no way out for the verbs that read everything.
