# media-hygiene documentation

← [Back to the project](../../README.md) · 🇫🇷 [Version française](../fr/README.md)

This guide takes you from your very first command to a cleaned-up photo library, one step at a
time. Each step adds one thing to the command of the step before. Stop whenever you have what you
need: after step 1 you already know where your duplicates are.

## Start here

Whatever you want to do next, the first three steps are the same: they show what your
folders hold, and change nothing.

1. [Your first audit](start/01-first-audit.md): one folder, one command, and how to read the result.
2. [Keep the cache](start/02-keep-the-cache.md): the next audits take seconds instead of minutes.
3. [Several folders and disks](start/03-several-folders.md): `C:` and `D:` together, the current
   folder, WSL.
## Clean the duplicates

Free the space the extra copies take, safely, and keep the best shots.

**See them** (nothing is changed):

4. [The HTML report](clean/04-html-report.md): the pictures, the folder pairs, the proof.

**Tune the analysis:**

5. [Choose which copy stays](clean/05-choose-the-kept-copy.md): `--prefer`, `--protect`, `--exclude`.
6. [Only some file types](clean/06-file-types.md): `--ext`, and files other than photos.
7. [The configuration file](clean/07-configuration-file.md): write your choices once, in `config.toml`.

**Free the space:**

8. [Clean](clean/08-clean.md): delete the extra copies, with a journal and a quarantine.
9. [Undo, history, purge](clean/09-undo-history-purge.md): change your mind, see what was done, empty
   the quarantine.

**Go further:**

10. [Sort burst series in your browser](clean/10-review-bursts.md): keep the best shots of each burst,
    with the keyboard.
11. [Near duplicates](clean/11-near-duplicates.md): resized and recompressed copies (`--tier near`).
12. [Decide pair by pair](clean/12-decide-pair-by-pair.md): swap or leave alone a folder pair, from the
    report.
13. [A second opinion](clean/13-second-opinion.md): compare with Czkawka, an independent tool.

## Sort the photos

Give your photos a tidy tree, `year/category` or the one you choose. Clean the duplicates first:
otherwise both copies are sorted.

4. [Propose a tidy tree](sort/04-classify.md): `classify` proposes a place for every file, and
   changes nothing.
5. [Review the proposal](sort/05-review-the-proposal.md): correct it in a workbook, look at the
   photos in the report.
6. [Write down what you know](sort/06-write-down-what-you-know.md): rules for your trips, your
   birthdays, your folders and your cameras, applied at every run.
7. [Sort](sort/07-sort.md): `sort` moves the files as the workbook says, journaled, undoable, and
   proves nothing was lost.

**Go further:**

8. [Name the subjects with a local model](sort/08-subjects-from-a-local-model.md): a vision model
   on your computer says what the loose photos show (optional).
9. [Places and trips from the GPS](sort/09-places-from-gps.md): name your places on a map, and
   let the GPS of recent phones sort home, family and trips, offline (optional).
10. [Name the events in your browser](sort/10-name-events-in-the-browser.md): one event at a
    time with its photos, named with the keyboard; `sort` applies your choices (optional).
11. [Albums](sort/11-albums.md): one photo in several folders ("every Christmas", "my best
    photos"), as hard links: no copy, no space used (optional).

## Reference

- [Commands and options](reference-commands.md): every command, every option, and their `--help`.
- [Mount points](reference-mount-points.md): `/data`, `/cache`, `/reports`, `/config`,
  `/journal`, `/quarantine`.
- [How your photos stay safe](reference-safety.md): what counts as a duplicate, what is checked
  before each action, how to check it yourself.
- [Sidecar files](reference-sidecars.md): `.xmp`, `.aae`, `.thm`.
- [Troubleshooting](reference-troubleshooting.md): warnings and error messages.
- [The inventory workbook](reference-inventory.md): every photo and video with what the audits
  learnt, in Excel, from the cache alone (`inventory`).
- [Advanced usage](reference-advanced.md): limit the processors used (`PYTHON_CPU_COUNT`).

## For developers

- [Development](development.md): build the image, the devcontainer helpers, releases.

The screenshots and console outputs of this guide come from a demo library of synthetic pictures
(drawn landscapes, no real photo), audited by the real image.
