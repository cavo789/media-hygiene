# Sort in short: the whole path

[Documentation](../README.md) › Sort in short · 🇫🇷 [Français](../../fr/sort/quick-guide.md)

Everything the tool can do to **file** your photos and videos, then to **find** them again, in
order, one step at a time, ready to paste into **PowerShell**. Each step takes a few lines and
links to its detailed page, should you want to understand. At the bottom, you have seen it all:
[the last section](#you-have-seen-it-all) lists each command and the step that shows it. Replace
`C:\Photos` with your folder.

The principle: `classify` **proposes** a place for each photo and video (`year/category` by
default), you correct the proposal, and only `sort` moves the files. Nothing moves before, and
`sort` can be undone. The steps marked *optional* can be skipped: the path goes on without them.

> 🤖 **Local AI required**: this sign marks the only commands that work only with a vision model
> installed on your computer ([Ollama](https://ollama.com), step 7). Without one, skip them:
> the rest of the path works, nothing forces it on you.

- **File** (steps 1 to 11): a proposal, your corrections, what you know (dates, places, people,
  subjects), then the sort and the albums.
- **Find** (steps 12 to 15): "Chloé on holiday in the mountains", by words, in your browser, in
  other photo software or in Excel.

## 0. Before you start

**Clean the duplicates first** ([clean in short](../clean/quick-guide.md)): otherwise both copies
of a photo are sorted. The `mh` command written for the clean serves here too; otherwise, write it
once: [clean in short, step 0](../clean/quick-guide.md#0-once-write-the-mh-command). In a new
terminal, load it again:

```powershell
. "$HOME\media-hygiene\mh.ps1"
```

## File

## 1. Ask for a proposal

```powershell
mh classify
```

Nothing is modified: `mh` mounts your folders read-only (`:ro`). `classify` dates each file
(EXIF, name, folder), groups the photos taken a short time apart into **events**, and proposes a
folder for each. At the end, two files in a new `<date>-classify` folder of your reports:

- `classify.xlsx`, the workbook, to open in Excel or LibreOffice: that is where you **edit**;
- `report.html`, the report, to open in your browser: that is where you **look** at the photos.

A large collection? `mh classify --year 2016` proposes one year at a time. Details: [propose a
tidy tree](04-classify.md).

## 2. Correct the proposal in the workbook

Open both side by side. Only the **yellow** cells of the workbook can be edited.

1. **Start with the Events sheet**: the largest first. Type a **Name** (`Italy 2023`): it becomes
   the folder of the event. Naming the first ten rows often settles most of the collection.
2. To understand an event, look for its identifier in the report: its dates, its previews, where
   its photos come from.
3. A file in the wrong place? Files sheet, **Final folder** column (`2016/Kermesse`).
4. **Save and close** the workbook.

Details: [review the proposal](05-review-the-proposal.md).

## 3. … or in your browser (optional)

Rather a photo on screen than a spreadsheet? The same events, one at a time, with their photos:

```powershell
mh review-sort
```

Open `http://127.0.0.1:8088/` (Ctrl+click). <kbd>Enter</kbd> accepts the name and category and
goes to the next one, <kbd>E</kbd> types a name, <kbd>O</kbd> sends the chosen photos elsewhere,
<kbd>V</kbd> accepts every sure proposal at once. Your choices go into `sort-decisions.json`,
next to the workbook, never inside it: `sort` reads both, and a row changed on both sides is
reported to you, never settled silently. Details: [name the events in the
browser](11-name-events-in-the-browser.md).

## 4. Write down what you know (optional)

Your trips, your parties, your existing folders: written once as rules in
`$HOME\media-hygiene\config\config.toml`, they serve every `classify`. For instance:

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

The rules are read in order: the first sure one decides. Your own tree is set in `[classify]`:
`layout = "{year}/{month}"` (by month), `target` (build it elsewhere), `leave` (a folder never
sorted). Details: [write down what you know](06-write-down-what-you-know.md), [your own
structure](04-classify.md#your-own-structure).

## 5. Places and trips from the GPS (optional)

Recent phones write where each photo was taken; the audit says how many of yours have a position.
Name your places on a map:

```powershell
mh places
```

Open `http://127.0.0.1:8088/`: the circles are your photos, the largest unnamed groups first.
Click, name ("Home", "Grandpa's"), set the radius, tick **Home** for yours, **Save**: the place
is written into `config.toml`. A whole village or park? **Search OpenStreetMap** takes its
outline. Then three rules:

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

`place` files into the name of the place (`2023/Home`), `trip` names each trip more than 100 km
from home after its country and town (`2023/Italy/Turin`), `folder_town` reads the folders named
like a town (`2017\Durbuy`). Towns are named offline: no position leaves your computer. Details:
[places and trips from the GPS](09-places-from-gps.md).

## 6. People (optional)

No AI to install: the tool brings its own face models (39 MB, downloaded once). Name the faces of
your photos once; they serve to file (here) and to find (step 13). Finding the faces takes time
the first time: measure first, then open the page.

```powershell
mh people --sample 200
mh people
```

Open `http://127.0.0.1:8088/`: faces that look alike are grouped, the largest groups first.
**Type a name** on a group, Enter: it is written into `config.toml`. `x` chooses several groups
of the same person, × removes a face, `i` ignores strangers, `y` confirms a "Chloé?" suggestion.
Naming the ten largest groups is often enough. To file the events where someone appears:

```toml
[[classify.rules]]
name = "With Chloé"
match = "person"
names = ["Chloé"]
category = "People/Chloé"
```

Place it **below** your date and place rules: otherwise it takes every event where Chloé appears.
The faces stay in the cache, never sent; `mh people --forget` deletes them all. Later,
`mh audit --people` looks for the faces of the new photos with the audit. Details: [sort by
person](10-sort-by-person.md), [people](../reference-people.md).

## 7. Subjects, with a local AI (optional)

> 🤖 **This whole step needs Ollama installed on your computer.** Without it, skip it: dates,
> places and people already file most of it.

The photos in folders that only carry a date (`DCIM`, `July 2016`) have no subject. A vision model
**on your computer** can say what they show:

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

3. 🤖 Measure the cost on a few photos: `mh classify --sample 50`.

Only the photos no other rule filed are sent, a few per event, to the `url` you give and nowhere
else. With WSL or Linux without Docker Desktop, see the detailed page. Details: [name subjects
with a local model](08-subjects-from-a-local-model.md).

## 8. Ask for the proposal again

After your rules, your places, your people, run step 1 again:

```powershell
mh classify
```

The edits already made in the old workbook and in `review-sort` are carried over. The *Why* table
counts the files each rule decided; a rule listed under *Rules that decided nothing* is placed
too low, or recognises nothing. Correct again (steps 2 and 3), as many times as needed: nothing
moves before `sort`.

## 9. Sort

```powershell
mh sort
```

For `sort`, `mh` mounts your folders writable (`sort` moves files) and adds the journal and the
quarantine. `sort` takes the workbook of the last `classify`, checks it, says how many edits it read (too
few? the workbook was not saved) and asks for confirmation: answer `y`. It ends by proving that
nothing is lost: as many files, of the same size, before and after. Details: [sort](07-sort.md).

## 10. Check, or undo

```powershell
explorer "C:\Photos"
```

You change your mind? `mh undo`: each file goes back where it was. A `classify` run again after a
sort does not propose elsewhere what is already filed. Details: [change your
mind](07-sort.md#change-your-mind).

## 11. Albums (optional)

A Christmas photo that is also among your best? An album puts it in a second folder without
copying it: a hard link, no space taken.

```powershell
mh album "Christmas" --category Christmas
mh album "Christmas" --category Christmas --apply
```

The first line shows what it would do, the second creates the album in
`C:\Photos\Albums\Christmas`. What it gathers: `--category`, `--event`, `--rule`, or `--rating 4`
(at least 4 stars in Windows), together if you like (`--category Christmas --rating 4`).
`mh undo` deletes its links, never a photo. Details: [albums](12-albums.md).

## Find

## 12. Give your photos words

```powershell
mh tags
```

In a few seconds, each photo and video receives the words of its folders and name
(`2022/Durbuy - bears` gives `Durbuy`, `bears`), of its date (year, month, season, Christmas,
your date rules) and of its place (your place, the nearest town and its country). They stay in
the cache, never inside your photos.

This command needs no AI. With Ollama ([step 7](#7-subjects-with-a-local-ai-optional)), the same
command also adds what each photo **shows** ("mountain", "snow", "cake"):

> 🤖 **Local AI required**: only when `[classify.ai] model` is filled in `config.toml`. Otherwise,
> `tags` says so in one line and keeps to folders, names, dates and places.

```powershell
mh tags --sample 20
mh tags
```

About 2 seconds per photo, so often a night or more: `--sample 20` measures first; Ctrl+C stops,
the next run resumes, the most recent first. Its answers also serve the `subject` rule, never
asked twice. Details: [tags](../reference-tags.md).

## 13. Find a photo: `search`

```powershell
mh search
```

Open `http://127.0.0.1:8088/`: type what you remember, the grid shows the photos, the best first;
Enter enlarges one. Filters: years, part of the path, one source of words.

| You type | It finds |
|---|---|
| `Chloé mountain` | Chloé (step 6) on a photo where "mountain" comes from a folder or a name (`Mountain holidays`), or, 🤖 with a local AI, from what the photo shows (step 12). |
| `person:"Granny Jane"` | The name among the people only. |
| `snow 2008` | The snow of 2008: the year is a word of the date. |
| `place:durbuy` | The word among the places only. |
| `birth*`, `"seaside town"` | The start of a word, a phrase. |

Without a browser, `mh search Chloé mountain` prints the first results as a table. New photos?
`mh audit` then `mh tags` first. Details: [`search`](../commands/search.md).

## 14. Carry the words into other photo software (optional)

You want the same words in digiKam, darktable, Lightroom or Immich?

```powershell
mh xmp
mh xmp --apply
```

The first line shows what it would write; the second writes an `.xmp` sidecar next to each photo
(`IMG_1.jpg.xmp`): the photo itself is never modified, an `.xmp` already there is completed,
never replaced. The names of people go in only if you add `person` to `[tags] xmp_sources`.
`mh undo` removes what it wrote. Details: [carry the words with the
photos](../reference-tags.md#carry-the-words-with-the-photos-xmp).

## 15. Answer your own questions in Excel (optional)

```powershell
mh inventory
```

An `inventory.xlsx` workbook, in your reports: each photo and video with its date, camera,
position, size, quality words (*blurry*, *small*) and exposure words (*dark*, *bright*), and its
`tags` words. Read from the cache alone, in seconds: filter, sort, count. `--format csv` for a CSV
file. Details: [the inventory workbook](../reference-inventory.md).

## Later: new photos

The same path, shorter, as the cache remembers everything: `mh audit` and `mh clean` ([clean in
short](../clean/quick-guide.md)), `mh people` for the new faces, `mh tags`, then `mh classify`,
the workbook and `mh sort`. What is already filed stays in place. Lost? `mh status` says where you
are, and whether the last proposal was sorted.

## You have seen it all

Each command of the sort and of the search, and the step of this page that shows it:

| Command | Step | What it does |
|---|---|---|
| [`classify`](../commands/classify.md) | 1, 4, 7, 8 | Proposes a place for each file, without modifying anything; 🤖 the `subject` rule and `--sample` need a local AI. |
| [`review-sort`](../commands/review-sort.md) | 3 | Names the events in the browser. |
| [`places`](../commands/places.md) | 5 | Names your places on a map. |
| [`people`](../commands/people.md) | 6 | Finds and names the faces; `--forget` deletes them. |
| [`sort`](../commands/sort.md) | 9 | Moves the files as the workbook says. |
| [`undo`](../commands/undo.md) | 10, 11, 14 | Undoes a sort, an album, `.xmp` files. |
| [`album`](../commands/album.md) | 11 | One photo in several folders, without a copy. |
| [`tags`](../commands/tags.md) | 12 | Gives words to each photo and video; 🤖 what they show, with a local AI only. |
| [`search`](../commands/search.md) | 13 | Finds a photo by a word, a place, a year, a person. |
| [`xmp`](../commands/xmp.md) | 14 | Writes the words into `.xmp` sidecars. |
| [`inventory`](../commands/inventory.md) | 15 | Each photo and video in an Excel workbook. |
| [`status`](../commands/status.md) | Later | Says where you are and the next step. |

The other commands find and clean duplicates (`audit`, `clean`, `review`, `purge`, `history`,
`crosscheck`, `reports`, `config`, `launcher`): **[clean in short](../clean/quick-guide.md)**. A
word escapes you? [Words of this guide](../reference-glossary.md). An error message?
[Troubleshooting](../reference-troubleshooting.md).

<details>
<summary>Without <code>mh</code>: the full commands</summary>

For the ones that modify nothing (`classify`, `tags`, `inventory`, and `xmp` without `--apply`),
read-only; add `-p 127.0.0.1:8088:8088` after `-it` for the ones that open a page (`review-sort`,
`places`, `people`, `search`):

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene classify
```

For `sort`, `undo`, `album --apply` and `xmp --apply`: `:ro` is gone, `/journal` and
`/quarantine` are added; replace `sort` with the command of the step:

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

</details>

---

[Documentation](../README.md) · Step by step: **[4. Propose a tidy tree](04-classify.md)** →
