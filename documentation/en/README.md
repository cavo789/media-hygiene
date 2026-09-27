# media-dedup documentation

← [Back to the project](../../README.md) · 🇫🇷 [Version française](../fr/README.md)

This guide takes you from your very first command to a cleaned-up photo library, one step at a
time. Each step adds one thing to the command of the step before. Stop whenever you have what you
need: after step 1 you already know where your duplicates are.

## User guide — step by step

**Find the duplicates** (nothing is changed):

1. [Your first audit](01-first-audit.md): one folder, one command, and how to read the result.
2. [Keep the cache](02-keep-the-cache.md): the next audits take seconds instead of minutes.
3. [Several folders and disks](03-several-folders.md): `C:` and `D:` together, the current
   folder, WSL.
4. [The HTML report](04-html-report.md): the pictures, the folder pairs, the proof.

**Tune the analysis:**

5. [Choose which copy stays](05-choose-the-kept-copy.md): `--prefer`, `--protect`, `--exclude`.
6. [Only some file types](06-file-types.md): `--ext`, and files other than photos.
7. [The configuration file](07-configuration-file.md): write your choices once, in `config.toml`.

**Free the space:**

8. [Clean](08-clean.md): delete the extra copies, with a journal and a quarantine.
9. [Undo, history, purge](09-undo-history-purge.md): change your mind, see what was done, empty
   the quarantine.

**Go further:**

10. [Sort burst series in your browser](10-review-bursts.md): keep the best shots of each burst,
    with the keyboard.
11. [Near duplicates](11-near-duplicates.md): resized and recompressed copies (`--tier near`).
12. [Decide pair by pair](12-decide-pair-by-pair.md): swap or leave alone a folder pair, from the
    report.
13. [A second opinion](13-second-opinion.md): compare with Czkawka, an independent tool.

## Reference

- [Commands and options](reference-commands.md): every command, every option, and their `--help`.
- [Mount points](reference-mount-points.md): `/data`, `/cache`, `/reports`, `/config`,
  `/journal`, `/quarantine`.
- [How your photos stay safe](reference-safety.md): what counts as a duplicate, what is checked
  before each action, how to check it yourself.
- [Sidecar files](reference-sidecars.md): `.xmp`, `.aae`, `.thm`.
- [Troubleshooting](reference-troubleshooting.md): warnings and error messages.

## For developers

- [Development](development.md): build the image, the devcontainer helpers, releases.

The screenshots and console outputs of this guide come from a demo library of synthetic pictures
(drawn landscapes, no real photo), audited by the real image.
