# media-hygiene documentation

← [Back to the project](../../README.md) · 🇫🇷 [Version française](../fr/README.md)

This guide takes you from your very first command to a cleaned-up photo library, one step at a
time. Each step adds one thing to the command of the step before. Stop whenever you have what you
need: after step 1 you already know where your duplicates are.

**Your photos are safe.** `audit`, `classify` and the other analyses never change a photo; with
`:ro` on your folders, the system itself forbids it. The commands that act (`clean`, `sort`,
`album`, `xmp`, `undo`) only move files or add new ones, never over another one, and can all be undone. Only `purge`
erases, the quarantine, after asking you. Details:
[how your photos stay safe](reference-safety.md).

## Start here

Whatever you want to do next, the first three steps are the same: they show what your
folders hold, and change nothing.

No Docker yet? [Install Docker](start/00-install-docker.md) first, on Windows or Linux: a
few minutes, once.

1. [Your first audit](start/01-first-audit.md): one folder, one command, and how to read the result.
2. [Keep the cache](start/02-keep-the-cache.md): the next audits take seconds instead of minutes.
3. [Several folders and disks](start/03-several-folders.md): `C:` and `D:` together, the current
   folder, WSL.
## Clean the duplicates

Free the space the extra copies take, safely, and keep the best shots.

👉 **In a hurry?** [Clean in short](clean/quick-guide.md): the whole path, every feature in order, on one page.

**See them** (nothing is changed):

4. [The HTML report](clean/04-html-report.md): the pictures, the folder pairs, the proof.

**Tune the analysis:**

5. [Choose which copy stays](clean/05-choose-the-kept-copy.md): `--prefer`, `--protect`, `--exclude`.
6. [Only some file types](clean/06-file-types.md): `--ext`, and files other than photos.
7. [The configuration file](clean/07-configuration-file.md): write your choices once, in `config.toml`.

**Free the space:**

8. [Clean](clean/08-clean.md): set the extra copies aside in the quarantine, with a journal.
9. [Undo, history, purge](clean/09-undo-history-purge.md): change your mind, see what was done, empty
   the quarantine to free the space.

**Go further:**

10. [Sort burst series in your browser](clean/10-review-bursts.md): keep the best shots of each burst,
    with the keyboard.
11. [Near duplicates](clean/11-near-duplicates.md): resized and recompressed copies, the sure ones
    apart, the others decided in your browser (`review --near`, `--tier near`).
12. [Decide pair by pair](clean/12-decide-pair-by-pair.md): swap or leave alone a folder pair, from the
    report.
13. [A second opinion](clean/13-second-opinion.md): compare with Czkawka, an independent tool.

## Sort the photos

Give your photos a tidy tree, `year/category` or the one you choose. Clean the duplicates first:
otherwise both copies are sorted.

👉 **In a hurry?** [Sort in short](sort/quick-guide.md): the whole path, every feature in order, on one page.

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
10. [Sort by person](sort/10-sort-by-person.md): name the faces found in your photos, and let a
    rule file the events where someone appears, offline (optional).
11. [Name the events in your browser](sort/11-name-events-in-the-browser.md): one event at a
    time with its photos, named with the keyboard; `sort` applies your choices (optional).
12. [Albums](sort/12-albums.md): one photo in several folders ("every Christmas", "my best
    photos"), as hard links: no copy, no space used (optional).

## Reference

- [Words of this guide](reference-glossary.md): container, mount, quarantine, journal, near
  duplicate, burst series… in plain language, from A to Z.
- [Commands and options](reference-commands.md): which command for what, then one page per
  command (`audit`, `clean`, `review`, `classify`, `sort`…): what it does, the folders it needs,
  its options, examples and its `--help`.
- [Mount points](reference-mount-points.md): `/data`, `/cache`, `/reports`, `/config`,
  `/journal`, `/quarantine`.
- [How your photos stay safe](reference-safety.md): what counts as a duplicate, what is checked
  before each action, how to check it yourself.
- [Sidecar files](reference-sidecars.md): `.xmp`, `.aae`, `.thm`.
- [Troubleshooting](reference-troubleshooting.md): warnings and error messages.
- [The inventory workbook](reference-inventory.md): every photo and video with what the audits
  learnt, in Excel, from the cache alone (`inventory`).
- [Tags](reference-tags.md): words to find photos by, from their folders, names, dates and places, and
  from a local vision model (`tags`), kept in the cache; `search` finds them in your browser,
  `xmp` writes them into `.xmp` sidecars.
- [People](reference-people.md): find the faces in the photos, group those alike and name them
  in your browser (`people`), then find someone with `search`; kept in the cache, never sent
  anywhere.
- [Advanced usage](reference-advanced.md): limit the processors used (`PYTHON_CPU_COUNT`).

## For developers

- [Development](development.md): build the image, the devcontainer helpers, releases.

The screenshots and console outputs of this guide come from a demo library of synthetic pictures
(drawn landscapes, no real photo), audited by the real image.
