# media-dedup

Find and safely clean duplicate photos and videos spread over several folders and disks — from
one `docker run`, on Windows (PowerShell) or WSL.

🇫🇷 [Version française](README_FR.md)

![An audit in the terminal: 83 media files scanned, 20 groups of identical files, 32 extra copies, 13.9 MB to free, then the folders sharing identical files, each pair saying which folder keeps its copies](documentation/en/images/terminal-audit.webp)

## Quick start

With Docker installed, one command audits a folder:

```powershell
docker run --rm -it -v "C:\Photos:/data/c/Photos:ro" cavo789/media-dedup audit
```

It lists the duplicate and broken photos and videos of `C:\Photos`, and changes nothing: `:ro`
(read-only) makes Docker itself forbid any write. The first run downloads the image by itself.
[Your first audit](documentation/en/01-first-audit.md) explains this command and its result, part
by part.

What it does:

- **Exact duplicates** — same size and same SHA-256, compared again byte for byte right before
  any deletion. Found across folders *and* disks (`C:` and `D:` in the same run).
- **Broken files** — empty files, images and RAW files that cannot be decoded (truncated JPEG,
  …), videos that cannot be opened.
- **Reversible** — every action is journaled; `undo` restores every deleted copy from the copy
  that was kept, and every quarantined file from the quarantine.
- **Orphan sidecars** — a sidecar file (`.xmp`, `.aae`, `.thm`) left without its photo is
  moved to the quarantine; one next to its photo is never touched.
- **Burst series and near duplicates** — shown side by side in an HTML report; you choose the
  best shots of each burst [with the keyboard, in your browser](documentation/en/10-review-bursts.md).
- **Never touched without your say** — bursts, near duplicates, protected folders.

## Documentation

The [documentation](documentation/en/README.md) walks you through, one step at a time. Each step
adds one thing to the command of the step before.

**User guide — step by step**

1. [Your first audit](documentation/en/01-first-audit.md) — one folder, one command, and how to
   read the result.
2. [Keep the cache](documentation/en/02-keep-the-cache.md) — the next audits take seconds instead
   of minutes.
3. [Several folders and disks](documentation/en/03-several-folders.md) — `C:` and `D:` together,
   the current folder, WSL.
4. [The HTML report](documentation/en/04-html-report.md) — the pictures, the folder pairs, the
   proof.
5. [Choose which copy stays](documentation/en/05-choose-the-kept-copy.md) — `--prefer`,
   `--protect`, `--exclude`.
6. [Only some file types](documentation/en/06-file-types.md) — `--ext`, and files other than
   photos.
7. [The configuration file](documentation/en/07-configuration-file.md) — write your choices once,
   in `config.toml`.
8. [Clean](documentation/en/08-clean.md) — delete the extra copies, with a journal and a
   quarantine.
9. [Undo, history, purge](documentation/en/09-undo-history-purge.md) — change your mind, see what
   was done, empty the quarantine.
10. [Sort burst series in your browser](documentation/en/10-review-bursts.md) — keep the best
    shots of each burst, with the keyboard.
11. [Near duplicates](documentation/en/11-near-duplicates.md) — resized and recompressed copies
    (`--tier near`).
12. [Decide pair by pair](documentation/en/12-decide-pair-by-pair.md) — swap or leave alone a
    folder pair, from the report.
13. [A second opinion](documentation/en/13-second-opinion.md) — compare with Czkawka, an
    independent tool.

**Reference** — [commands and options](documentation/en/reference-commands.md),
[mount points](documentation/en/reference-mount-points.md),
[how your photos stay safe](documentation/en/reference-safety.md),
[sidecar files](documentation/en/reference-sidecars.md),
[troubleshooting](documentation/en/reference-troubleshooting.md).

**For developers** — [build the image, the devcontainer, releases](documentation/en/development.md).

## The complete command

Once through the guide, most people end up with this command: two folders, the cache, the
reports, the configuration, the journal and the quarantine. It cleans; to audit, add `:ro` to
your folders and write `audit` instead of `clean`.

```powershell
mkdir "$HOME\media-dedup\reports", "$HOME\media-dedup\config", "$HOME\media-dedup\journal", "$HOME\media-dedup\quarantine"
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v "D:\Old disk:/data/d/Old disk" `
  -v media-dedup-cache:/cache `
  -v "$HOME\media-dedup\reports:/reports" `
  -v "$HOME\media-dedup\config:/config" `
  -v "$HOME\media-dedup\journal:/journal" `
  -v "$HOME\media-dedup\quarantine:/quarantine" `
  cavo789/media-dedup clean
```

From WSL, write Linux paths and run as yourself, so that new files belong to you:

```bash
mkdir -p ~/media-dedup/{reports,config,journal,quarantine}
docker run --rm -it --user "$(id -u):$(id -g)" \
  -v "/mnt/c/Photos:/data/c/Photos" \
  -v "/mnt/d/Old disk:/data/d/Old disk" \
  -v media-dedup-cache:/cache \
  -v ~/media-dedup/reports:/reports \
  -v ~/media-dedup/config:/config \
  -v ~/media-dedup/journal:/journal \
  -v ~/media-dedup/quarantine:/quarantine \
  cavo789/media-dedup clean
```

`undo` instead of `clean` puts everything back.

## Update

`docker pull cavo789/media-dedup` fetches the latest version; a tag such as
`cavo789/media-dedup:0.2.0` pins one.
