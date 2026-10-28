# Sort in short: the whole path

[Documentation](../README.md) › Sort in short · 🇫🇷 [Français](../../fr/sort/quick-guide.md)

Give your photos and videos a tidy tree, `year/category` or the one you choose: one command per
step, to paste into **PowerShell**. `classify` **proposes** a place for each file, you correct the
proposal, and only `sort` moves the files. Nothing moves before, and `sort` can be undone.

<div class="mh-path" markdown>

**The strict minimum**, for a first sort: four steps. The others are optional.

- [0 · Before you start](#0-before-you-start)
- [1 · Ask for a proposal](#1-ask-for-a-proposal)
- [2 · Correct it](#2-correct-the-proposal-in-the-workbook)
- [9 · Sort](#9-sort)

</div>

Each step says what it risks: <span class="mh-badge mh-safe">🔒 Photos untouched</span>
<span class="mh-badge mh-undo">↩️ Can be undone</span>. <span class="mh-badge mh-ai">🤖 Local
AI</span> marks the only commands that need a vision model on your computer: without one, skip
them. Only want to **find** a photo, without moving anything? **[Find in
short](../find/quick-guide.md)**.

## 0. Before you start

<span class="mh-badge mh-once">⏱ Once</span>

**Clean the duplicates first** ([clean in short](../clean/quick-guide.md)): otherwise both copies
of a photo are sorted. The `mh` command written for the clean serves here too; otherwise, write it
once: [clean in short, step 0](../clean/quick-guide.md#0-once-write-the-mh-command). Step 0 wrote
it into your PowerShell profile: every new terminal knows it.

**Lost?** Type `mh` alone: the [home page](../commands/home.md) opens in your browser: the next
step proposed, every action a click or Ctrl+K away. In the terminal only: [`mh menu`](../commands/menu.md).

## 1. Ask for a proposal

<span class="mh-badge mh-safe">🔒 Photos untouched</span>

`classify` dates each file, groups the photos taken a short time apart into **events**, and
proposes a folder for each:

```powershell
mh classify
```

At the end, a new `<date>-classify` folder of your reports holds two files:

- `classify.xlsx`, the workbook, to open in Excel or LibreOffice: that is where you **edit**;
- `report.html`, the report, to open in your browser: that is where you **look** at the photos.

![The first page of the classify report: four counters (files, already in place, to check or to sort, events), a table of the years with links to their pages, the events where to start with their share of the work, then the proposed tree of folders with their file counts](../images/classify-report.webp)

??? info "Details"

    Nothing is modified: `mh` mounts your folders read-only (`:ro`). An event's date comes from
    the EXIF, the name or the folder of its files. A large collection? `mh classify --year 2016`
    proposes one year at a time. More: [propose a tidy tree](04-classify.md).

## 2. Correct the proposal in the workbook

<span class="mh-badge mh-safe">🔒 Photos untouched</span>

Open both side by side. Only the **yellow** cells of the workbook can be edited.

1. **Start with the Events sheet**: the largest first. Type a **Name** (`Italy 2023`): it becomes
   the folder of the event. Naming the first ten rows often settles most of the collection.
2. To understand an event, copy its **Id** (the first column, 12 characters), open the page of
   its year in the report and look for it (Ctrl+F): its dates, its previews, the folders its
   photos come from.
3. A file in the wrong place? Files sheet, **Final folder** column (`2016/Kermesse`).
4. **Save and close** the workbook.

![A year page of the classify report: the event Seaside holidays with its id, 38 files of which 3 to check or to sort, the cumulated share of the work, the proposed folder 2019/Seaside holidays marked Sure, the three folders its photos come from, then eight previews spread over its days with their names and times, and a link to all the files](../images/classify-year.webp)

More: [review the proposal](05-review-the-proposal.md).

## 3. … or in your browser (optional)

<span class="mh-badge mh-optional">Optional</span> <span class="mh-badge mh-safe">🔒 Photos untouched</span>

Rather a photo on screen than a spreadsheet? The same events, one at a time, with their photos:

```powershell
mh review-sort
```

Your browser opens on the page (if not: `http://127.0.0.1:8088/`). <kbd>Enter</kbd> accepts the name and category and
goes to the next one, <kbd>E</kbd> types a name, <kbd>O</kbd> sends the chosen photos elsewhere,
<kbd>V</kbd> accepts every sure proposal at once.

??? info "Details"

    Your choices go into `sort-decisions.json`, next to the workbook, never inside it: `sort`
    reads both, and a row changed on both sides is reported to you, never settled silently.
    More: [name the events in the browser](11-name-events-in-the-browser.md).

## 4. Write down what you know (optional)

<span class="mh-badge mh-optional">Optional</span> <span class="mh-badge mh-safe">🔒 Photos untouched</span>

Your trips, your parties, your existing folders: written once as rules in `config.toml`, they
serve every `classify`. The first time, `mh config` creates this file, each setting explained;
then open it:

```powershell
mh config
notepad "$HOME\media-hygiene\config\config.toml"
```

Add your rules at the end of the file, for instance:

```toml
[[classify.rules]]
name = "Italy 2023"
match = "date_range"
dates = "2023-07-01..2023-07-15"
category = "Holidays and outings/Italy 2023"

[[classify.rules]]
name = "Christmas"
match = "calendar"
dates = "12-24..12-26"
category = "Parties/Christmas {year}"
```

The rules are read in order: the first sure one decides.

??? info "Every kind of rule, and your own tree"

    | `match` | Recognises |
    |---|---|
    | `existing_folder` | A folder name you chose (`2019/Seaside holidays`). |
    | `calendar`, `date_range` | Days that come back every year (birthdays, Christmas), or only once (a trip). |
    | `kind` | Screenshots, images received through a messaging app, downloaded films. |
    | `path`, `camera` | A word in the path, a camera brand (a drone, an action camera). |
    | `place`, `trip`, `folder_town` | Your places, your trips, the towns named by your folders: step 5. |
    | `person` | Someone you named: step 6. |
    | `subject` | What a local vision model sees: step 7. |
    | `other_category` | Everything no rule above recognised. |

    Your own tree is set in `[classify]`: `layout = "{year}/{month}"` (by month), `target`
    (build it elsewhere), `leave` (a folder never sorted). More: [write down what you
    know](06-write-down-what-you-know.md), [your own structure](04-classify.md#your-own-structure).

## 5. Places and trips from the GPS (optional)

<span class="mh-badge mh-optional">Optional</span> <span class="mh-badge mh-safe">🔒 Photos untouched</span>

Recent phones write where each photo was taken. Name your places on a map:

```powershell
mh places
```

Your browser opens on the page (if not: `http://127.0.0.1:8088/`): the circles are your photos, the largest unnamed groups first.
Click, name ("Home", "Grandpa's"), set the radius, tick **Home** for yours, **Save**: the place is
written into `config.toml`.

![The places map: OpenStreetMap tiles of the Cinquantenaire park in Brussels, the circle of the photos taken there, the green circle of the place Parc du Cinquantenaire just saved, and on the left the list of places and of the largest clusters without a name](../images/places.webp)

Then add three rules to `config.toml`:

```toml
[[classify.rules]]
name = "My places"
match = "place"

[[classify.rules]]
name = "Trips"
match = "trip"

[[classify.rules]]
name = "Towns of the folders"
match = "folder_town"
```

??? info "Details"

    The audit says how many of your photos have a position. A whole village or park? **Search
    OpenStreetMap** takes its outline. `place` files into the name of the place (`2023/Home`),
    `trip` names each trip more than 100 km from home after its country and town
    (`2023/Italy/Turin`), `folder_town` reads the folders named like a town (`2017\Durbuy`). Towns
    are named offline: no position leaves your computer. More: [places and trips from the
    GPS](09-places-from-gps.md).

## 6. People (optional)

<span class="mh-badge mh-optional">Optional</span> <span class="mh-badge mh-safe">🔒 Photos untouched</span>

Name the faces of your photos once: they serve to file (here) and to find ([find in
short](../find/quick-guide.md)). No AI to install. Finding the faces takes time the first time:
measure first, then open the page.

```powershell
mh people --sample 200
mh people
```

Your browser opens on the page (if not: `http://127.0.0.1:8088/`): faces that look alike are grouped, the largest groups first.
**Type a name** on a group, Enter: it is written into `config.toml`. Naming the ten largest groups
is often enough.

![The people page: the largest group named Chloé, the name read back from config.toml at the top (Saved in config.toml, read back: Chloé, 7 confirmed faces), her seven faces below; then Group 2 and Group 3, not named yet, each with its field to type a name and its buttons Name, Name with others, Ignore this group](../images/people.webp)

To file the events where someone appears, add a rule **below** your date and place rules
(otherwise it takes every event where Chloé appears):

```toml
[[classify.rules]]
name = "With Chloé"
match = "person"
names = ["Chloé"]
category = "People/Chloé"
```

??? info "Details"

    The tool brings its own face models (39 MB, downloaded once). On the page, `x` chooses
    several groups of the same person, × removes a face, `i` ignores strangers, `y` confirms the
    faces attributed to someone (shown apart from the verified ones). The faces stay in the cache, never sent; `mh people --forget` deletes
    them all. Later, `mh audit --people` looks for the faces of the new photos with the audit.
    More: [sort by person](10-sort-by-person.md), [people](../reference-people.md).

## 7. Subjects, with a local AI (optional)

<span class="mh-badge mh-optional">Optional</span> <span class="mh-badge mh-ai">🤖 Local AI</span> <span class="mh-badge mh-safe">🔒 Photos untouched</span>

The photos in folders that only carry a date (`DCIM`, `July 2016`) have no subject. A vision model
**on your computer** can say what they show. Without one, skip this step: dates, places and people
already file most of it.

1. Install [Ollama](https://ollama.com), then a model that sees images:
   `ollama pull qwen2.5vl:7b`.
2. Name it in `config.toml`, with a `subject` rule, at the bottom of the list:

    ```toml
    [classify.ai]
    url = "http://host.docker.internal:11434"
    model = "qwen2.5vl:7b"

    [[classify.rules]]
    name = "Subject"
    match = "subject"
    categories = [
        "School = classrooms, school trips, school shows and parties",
        "Animals = a pet or an animal as the main subject",
    ]
    ```

3. Measure the cost on a few photos: `mh classify --sample 50`.

??? info "Details"

    Only the photos no other rule filed are sent, a few per event, to the `url` you give and
    nowhere else. With WSL or Linux without Docker Desktop, see the detailed page. More: [name
    subjects with a local model](08-subjects-from-a-local-model.md).

## 8. Ask for the proposal again

<span class="mh-badge mh-safe">🔒 Photos untouched</span>

After your rules, your places, your people, run step 1 again:

```powershell
mh classify
```

The edits already made in the old workbook and in `review-sort` are carried over. Correct again
(steps 2 and 3), as many times as needed: nothing moves before `sort`.

??? info "Details"

    The *Why* table counts the files each rule decided; a rule listed under *Rules that decided
    nothing* is placed too low, or recognises nothing.

## 9. Sort

<span class="mh-badge mh-undo">↩️ Can be undone</span>

Move the files as the workbook says:

```powershell
mh sort
```

`sort` says how many edits it read (too few? the workbook was not saved) and asks for
confirmation: answer `y`. It ends by proving that nothing is lost: as many files, of the same
size, before and after.

??? info "Details"

    For `sort`, `mh` mounts your folders writable (`sort` moves files) and adds the journal and
    the quarantine. `sort` takes the workbook of the last `classify` and checks it before moving
    anything. More: [sort](07-sort.md).

## 10. Check, or undo

<span class="mh-badge mh-undo">↩️ undo puts back</span>

```powershell
explorer "C:\Photos"
```

You change your mind? `mh undo`: each file goes back where it was. A `classify` run again after a
sort does not propose elsewhere what is already filed. More: [change your
mind](07-sort.md#change-your-mind).

## 11. Albums (optional)

<span class="mh-badge mh-optional">Optional</span> <span class="mh-badge mh-undo">↩️ Can be undone</span>

A Christmas photo that is also among your best? An album puts it in a second folder without
copying it: a hard link, no space taken. The first line shows what it would do, the second creates
the album in `C:\Photos\Albums\Christmas`:

```powershell
mh album "Christmas" --category Christmas
mh album "Christmas" --category Christmas --apply
```

??? info "Details"

    What it gathers: `--category`, `--event`, `--rule`, or `--rating 4` (at least 4 stars in
    Windows), together if you like (`--category Christmas --rating 4`). `mh undo` deletes its
    links, never a photo. An album made by hand in `search` or `browse` gets its folder the same
    way, without an option: `mh album "Crete 2023"`. More: [albums](12-albums.md).

## Later: new photos

The same path, shorter, as the cache remembers everything: `mh audit` and `mh clean` ([clean in
short](../clean/quick-guide.md)), `mh people` for the new faces, then `mh classify`, the workbook
and `mh sort`. What is already filed stays in place. Lost? `mh status` says where you are, and
whether the last proposal was sorted.

## You have seen it all

Each command of the sort, and the step of this page that shows it:

| Command | Step | What it does |
|---|---|---|
| [`classify`](../commands/classify.md) | 1, 4, 7, 8 | Proposes a place for each file, without modifying anything; 🤖 the `subject` rule and `--sample` need a local AI. |
| [`review-sort`](../commands/search.md#the-events-of-the-latest-classify) | 3 | Names the events in the browser. |
| [`places`](../commands/places.md) | 5 | Names your places on a map. |
| [`people`](../commands/people.md) | 6 | Finds and names the faces; `--forget` deletes them. |
| [`sort`](../commands/sort.md) | 9 | Moves the files as the workbook says. |
| [`undo`](../commands/undo.md) | 10, 11 | Undoes a sort, an album. |
| [`album`](../commands/album.md) | 11 | One photo in several folders, without a copy. |
| [`status`](../commands/status.md) | Later | Says where you are and the next step. |
| [`menu`](../commands/menu.md) | Later | Lists every step with its command; Enter runs the next one. |

To find a photo by a word, a place, a year or a person (`tags`, `search`, `xmp`, `inventory`):
**[find in short](../find/quick-guide.md)**. To find and clean duplicates (`audit`, `clean`,
`review`, `purge`…): **[clean in short](../clean/quick-guide.md)**. A word escapes you? [Words of
this guide](../reference-glossary.md). An error message?
[Troubleshooting](../reference-troubleshooting.md).

??? note "Without `mh`: the full commands"

    For the ones that modify nothing (`classify`), read-only; add `-p 127.0.0.1:8088:8088` after
    `-it` for the ones that open a page (`review-sort`, `places`, `people`):

    ```powershell
    docker run --rm -it `
      -v "C:\Photos:/data/c/Photos:ro" `
      -v media-hygiene-cache:/cache `
      -v "$HOME\media-hygiene\reports:/reports" `
      -v "$HOME\media-hygiene\config:/config" `
      cavo789/media-hygiene classify
    ```

    For `sort`, `undo` and `album --apply`: `:ro` is gone, `/journal` and `/quarantine` are
    added; replace `sort` with the command of the step:

    ```powershell
    docker run --rm -it `
      -v "C:\Photos:/data/c/Photos" `
      -v media-hygiene-cache:/cache `
      -v "$HOME\media-hygiene\reports:/reports" `
      -v "$HOME\media-hygiene\config:/config" `
      -v "$HOME\media-hygiene\journal:/journal" `
      -v "$HOME\media-hygiene\quarantine:/quarantine" `
      cavo789/media-hygiene sort
    ```

---

[Documentation](../README.md) · Step by step: **[4. Propose a tidy tree](04-classify.md)** →
