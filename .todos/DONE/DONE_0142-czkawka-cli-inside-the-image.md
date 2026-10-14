# 0142 — `crosscheck` in one run: ship `czkawka_cli` in the image instead of a 485 MB GUI image

- **Priority**: Low — `crosscheck` runs once per collection; the gain is a 485 MB pull and one paste fewer, not a hot path. Decision for the maintainer first.
- **Batch**: cross-check
- **Depends**: —
- **Files**: `Dockerfile`, `src/media_hygiene/crosscheck/czkawka.py`, `src/media_hygiene/crosscheck/compare.py`, `src/media_hygiene/cli/cmd_crosscheck.py`, `src/media_hygiene/constants.py`, `documentation/en/commands/crosscheck.md`, `documentation/fr/commands/crosscheck.md`, `README.md`

## Context

Speed review of 2026-10-14 (second pass). `crosscheck` prints a `docker run … jlesage/czkawka:
v26.09.2 czkawka_cli dup …` command (`crosscheck/czkawka.py`, `CZKAWKA_IMAGE`). The user
pastes it, then runs `crosscheck` again to compare. `jlesage/czkawka` is a GUI image (VNC,
web desktop): **485 MB** on disk, for one command-line tool. The first time, the pull is
longer than the check itself.

`czkawka_cli` is a single Rust binary (MIT), a few MB. Built in a discarded stage like
`ffprobe` and `ffmpeg`, or downloaded from its release by checksum, it would let `crosscheck`
run Czkawka itself, on the same mounts, in one command:

- no second image to pull, no command to paste, no second run;
- the paths match by construction (same container), so the out-of-scope handling of
  `compare.py` stays, but the mount-matching notes of the docs get simpler.

## Trade-offs to weigh before deciding (not on looks)

- **Independence**: the point of `crosscheck` is a second opinion. Czkawka stays another
  codebase with another hash function; only the packaging is shared. The risk is a build or
  packaging fault common to both, e.g. a wrong mount. Today a user can also run Czkawka from
  its own GUI and see it with their own eyes. Keep the printed command as an option
  (`crosscheck --print-command`) for those who want that.
- **Image size and licences**: + a few MB; add MIT Czkawka to the licence label and README.
- **Maintenance**: one more pinned version (Renovate `github-tags`, like FFmpeg) and an
  arm64 binary. Check that the releases publish one; otherwise build it with `cargo` in a
  discarded stage. The arm64 CI runner is native, so that stays reasonable.
- **Speed of Czkawka itself**: unchanged. It reads every file again (by design: independent).

## What to do (if accepted)

1. `Dockerfile`: a `czkawka` stage producing `/usr/local/bin/czkawka_cli`, pinned and
   verified by SHA-256, for both platforms.
2. `crosscheck`: when the results file is missing and `czkawka_cli` is on `PATH`, run it
   (`run_tool`-like, with a progress line and no time limit, Ctrl+C stops it) with the same
   folders, extensions and exclusions as the audit, write `czkawka.json` in the crosscheck
   report folder, then compare in the same run.
3. Docs en + fr: one command instead of three steps; captures regenerated with
   `docs_screenshots`.

## Acceptance

- `crosscheck` on the demo tree gives the same comparison as today's two-step flow (an e2e
  test with the real image).
- `--print-command` still prints today's `jlesage/czkawka` command.
