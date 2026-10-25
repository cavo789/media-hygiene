# 11. Name the events in your browser

[Documentation](../README.md) › Sorting, step 11 · 🇫🇷 [Français](../../fr/sort/11-name-events-in-the-browser.md)

**Why name an event?** An [event](../reference-glossary.md#event) is the photos of one moment (a
school fair, a weekend), gathered by `classify` from one folder or phone to another. Its name
becomes **the folder where `sort` puts all its photos**: named `Kermesse`, it goes to
`2016/Kermesse`; without a name, to `2016/To sort/2016-07-14`. What moves on the disk, name or
category: [`review-sort`, what it is for](../commands/review-sort.md#what-it-is-for).

The workbook of [step 5](05-review-the-proposal.md) is good for renaming in bulk, not for
*looking* at photos: naming an event means reading the report in one window and typing in the
other. With hundreds of events, that is hundreds of back-and-forths. `review-sort` puts both in
one page of your browser: **one event at a time, its photos, its proposal, and a field to name
it**, all with the keyboard.

It is optional: the workbook alone is enough, and both can be used together. The page never
touches a photo nor the workbook; `sort` ([step 7](07-sort.md)) applies your choices.

## Start the page

Run `classify` first ([step 4](04-classify.md)). Then start the page with the same folders and
the same reports folder, which `mh` mounts (read-only is enough for the photos: the page only
shows them):

```powershell
mh review-sort
```

<details>
<summary>Without <code>mh</code>: the full command</summary>

```powershell
docker run --rm -it -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene review-sort
```

</details>

As for [the burst review](../clean/10-review-bursts.md#step-1-start-the-review),
`mh` opens the page to your computer only, on port 8088 (`-p 127.0.0.1:8088:8088` in the full
command). The page
reads the workbook of the latest `classify` run, the one `sort` applies; name another one after
the command: `review-sort "C:\Photos triées\reports\20261002-123210-classify\classify.xlsx"`.

```text
412 events to decide: 260 with a sure proposal (one click), 152 to look at.
✅ Review ready, open http://127.0.0.1:8088/ in your browser. Each choice is
saved at once in
C:\Users\you\media-hygiene\reports\20261002-123210-classify\sort-decisions.json.
Ctrl+C stops the review.
💡 The page does not open? docker run must publish the same port on both sides:
-p 127.0.0.1:8088:8088.
```

Ctrl+click the address to open the page.

## Read the page

The events come **in the order of the Events sheet**: the ones still to decide first, the largest
first. The page opens on the first one still to decide (or where you stopped). For each event:

- **at the top**: its name (or its dates), its number of files and how many are still to check or
  to sort, and the share of the work naming the events up to this one covers;
- **From**: the folders its photos come from;
- **Status**: one line: "proposed by classify (its band, why), not validated yet", "changed, not
  saved yet: Enter saves it, Esc drops it", "validated here at 14:32" (the time
  `sort-decisions.json` holds, read back from the disk), or what the workbook decided (in red when
  it says something else than the page);
- **the photos**, in date order, each with its date. A photo whose proposed folder differs from
  the event's shows it (→ …); one you sent elsewhere is framed in green; 🔒 marks a file left as
  it is (protected or `leave` folder), which no choice moves.

The **Folder** field holds the folder of the event under its year (`2011/`, shown before the
field): `Parties/Communions/Manon's communion` gives `2011/Parties/Communions/Manon's communion`.
It is filled with the proposal and completes from the folders already used. The line under it
says, as you type, where the files go, computed as `sort` will: "→ 212 files go to
C:\Photos\2011\Parties\Communions\Manon's communion · 40 files keep their own folder (Budva…)".
The event's **name** (the albums use it) is the last folder; change it under *Name of the event*
(<kbd>E</kbd>). A folder typed and not saved is never lost silently: moving to another event asks
whether to save it, closing the tab warns.

## The keys

| Key | What it does |
|---|---|
| <kbd>Enter</kbd> | No photo framed: save the folder, then go to the next event still to decide. |
| <kbd>N</kbd> / <kbd>P</kbd> (or Page Down / Page Up) | Next or previous event, without deciding: the ← → buttons around *Event 1 of 1137* in the bar. |
| <kbd>U</kbd> | Next event still to decide. |
| <kbd>V</kbd> | Accept every sure proposal at once (see below). |
| <kbd>Shift</kbd>+<kbd>Z</kbd> | Take that batch back. |
| <kbd>F</kbd> / <kbd>E</kbd> | Type the folder / change the event's name; <kbd>Esc</kbd> drops what is typed and not saved. |
| <kbd>Shift</kbd>+<kbd>S</kbd> | Leave the whole event where it is ("(stay where it is)"). |
| <kbd>O</kbd> | Send the picked photos (else the framed one) to another folder: type it, <kbd>Enter</kbd>. |
| <kbd>S</kbd> | Leave the picked photos (else the framed one) where they are. |
| <kbd>Delete</kbd> | Take back the choice made here: of the picked photos, else of the event. The workbook decides again. |

The photos are picked as in [`browse`](../commands/browse.md): a click picks one photo; the ☑ box
of each thumbnail (or Ctrl+click) adds or removes one; Shift+click picks every photo from the last
one clicked; a rectangle dragged with the mouse over the grid picks what it touches (with Ctrl, it
adds to the picking); Ctrl+A every photo of the event. **Invert the picking** (or I) picks the
others. The arrows move the frame, Space picks the framed photo, Enter (or a double click) opens it
large: ← → there go from one photo to the next, F full screen, Esc closes. Once photos are picked,
the bar offers **Send to another folder (O)**, **Leave where they are (S)**, and **Take back the
choice made here** when one of them was chosen here. A photo chosen here carries a green *chosen
here* label.

A photo sent to another folder gets the folder the layout gives it, as if you had typed it in its
**Final folder** cell: `2016/Best of` with `layout = "{year}/{category}"`.

## Accept the sure proposals at once

On a large collection, many events have a **sure** proposal: most of their photos come from a
strong rule (band *Sure*), and the few still to check or to sort propose the same category, or
none. Such an event shows `✔ sure` after its proposal; it only needs a glance.

The button **✔ Accept N sure proposals (M files)** at the top (or <kbd>V</kbd>) accepts
them all, after a confirmation that gives the figures and **lists the events**: each one with
the files that move and its folder, and a click on one shows it on the page, to look before
accepting. Each one is recorded exactly as
<kbd>Enter</kbd> would record it on that event untouched (its proposed category, no name), with
what the workbook said of it, like any other choice. The confirmation counts the files that move,
and those that keep a folder you had named: these are never flattened into the proposed folder.
Nothing is imposed: an event you already
chose, here or in the workbook, is left alone, and a later workbook edit of the same event is
still a conflict, never settled silently.

The batch is **one write** of `sort-decisions.json`, read back from the disk before the page shows
it: the status line gives the time the disk holds it. **↶ Take the batch back** (or
<kbd>Shift</kbd>+<kbd>Z</kbd>) forgets the whole batch in one write too (an event you chose again
since keeps your new choice).

Tick **Only the events to decide** to make <kbd>N</kbd>, <kbd>P</kbd> and <kbd>U</kbd> skip the
events already chosen and those whose proposal is sure: only the ones that need you remain.
Tick **Only the sure proposals** instead to walk the sure ones one by one before accepting them.
One box at a time; the browser remembers it for the next opening of the page.

## Remember an event as a rule

A choice made here holds for this proposal; a **rule** holds for every later `classify`, the
photos added later included (a new copy from the phone, a person's folder of the same days).
**📌 Remember as a rule** (or <kbd>R</kbd>) writes the event shown as a `date_range` rule
([step 6](06-write-down-what-you-know.md#dates)): its name (the last folder), its days (those
of the event, which you can widen), its folder, and `keep_folders = true` so that your own
folders stay below it. Before saving, the dialog says what the rule would take on this
proposal: "236 files: 6 of this event, 230 of other events or folders on the same days.
Elsewhere: Photos Chloé (230)", and the rules whose days it shares (the first listed wins on
those days). Saved, the rule is written into `config.toml` just above *Existing folders*, your
comments kept, read back from the disk and said with its time; the event's folder is chosen at
the same time, so *Sort this event now* works at once. The left column then names the rule
that decides the event's files: *Rule: Montenegro (2019-07-12..2019-07-19)*.

## Sort one event now

**Sort this event now** (or <kbd>M</kbd>) tidies the collection event by event: it saves the
folder if needed, shows where the files go (the line under the field) and asks, then moves the
files of this event only, as [`sort --event`](../commands/sort.md) does: journaled, each run with
its own `undo`. The status line gives what the disk holds after the run: the files moved and
checked at their new place. The event then shows *sorted*, and <kbd>U</kbd> and *Only the events
to decide* skip it; a later `sort` of the whole workbook skips its files. The photos must be
mounted without `:ro`, with a `/journal`: otherwise the page says what is missing, and nothing
moves.

## Where your choices go

Each choice is saved at once in `sort-decisions.json`, **next to `plan.json`** in the folder of
the `classify` run. The workbook is never changed (Excel may have it open). Stop the page with
<kbd>Ctrl</kbd>+<kbd>C</kbd>, start it again: it resumes.

```text
✅ Review stopped — events chosen: 37, photos chosen one by one: 12.
Your choices are in C:\Users\you\media-hygiene\reports\20261002-123210-classify\sort-decisions.json.
```

`sort` reads both, the page's choices **on top of** the workbook, and says so:

```text
12 edits read; workbook saved on 2 October 2026 at 14:32.
49 choices of the review page applied on top of the workbook (3 replacing a workbook edit, 0 the
same in both).
```

You may keep editing the workbook: one source of truth, the plan, and never a silent conflict.
Each choice of the page remembers what the workbook said of that event or file when you made it:

- **the workbook still says the same**: your choice in the page is the newer one, it wins;
- **the workbook says what you chose**: nothing to settle;
- **the workbook was changed since, on the same event or file, to something else**: nobody can
  tell which one you meant. `sort` refuses to move anything and lists them, with both values;
  the page shows them in red. Choose again in the page (it shows both), or press
  <kbd>Delete</kbd> there to let the workbook decide, or set the workbook cell back.

The other rules of [step 5](05-review-the-proposal.md#the-workbook-edit-the-yellow-cells) still
hold: the most precise choice wins (a file, else its event, else its category), and companions
(a Live Photo, a RAW file and its JPEG) follow one folder.

**Run `classify` again** and your choices of the page are carried over like your edits
([step 5](05-review-the-proposal.md#improve-the-proposal-without-losing-your-work)): they land in
the yellow cells of the new workbook, and the new run starts with an empty
`sort-decisions.json`. A choice the workbook contradicts since is not carried: the workbook's
value is, and the page's is listed among the edits left behind.

---

← [10. Sort by person](10-sort-by-person.md) · [Documentation](../README.md) · Next: **[12. Albums](12-albums.md)** →
