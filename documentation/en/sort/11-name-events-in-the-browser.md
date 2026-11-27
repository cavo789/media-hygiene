# 11. Name the events in your browser

[Documentation](../README.md) › Sorting, step 11 · 🇫🇷 [Français](../../fr/sort/11-name-events-in-the-browser.md)

**Why name an event?** An [event](../reference-glossary.md#event) is the photos of one moment (a
school fair, a weekend). Its name becomes **the folder where its photos go**: named `Kermesse`,
it goes to `2016/2016-07/Kermesse`. What moves on the disk:
[the 🗂 Events tab of `library`, what it is for](../commands/library.md#the-events-of-the-latest-classify).

The 🗂 Events tab of `library` shows **one event at a time, its photos, and where they go**, in
your browser, with the keyboard. It groups the files **not sorted yet** (not in a
`YYYY/YYYY-MM/<name>` folder) of the period searched, cut where no photo was taken for several
hours. It needs no `classify` run and no workbook: the workbook of
[step 5](05-review-the-proposal.md) stays the fast path for large collections.

## Start the page

```powershell
mh library
```

<details>
<summary>Without <code>mh</code>: the full command</summary>

```powershell
docker run --rm -it -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\cache:/cache" `
  cavo789/media-hygiene library
```

</details>

As for [the burst review](../clean/10-review-bursts.md#step-1-start-the-review),
`mh` opens the page to your computer only, on port 8088. Click the **🗂 Events** tab on top of
the left column. Give a period (*From*, *To*) to look at one year or one month only.

## Read the page

The left column lists the events, in date order, each with its days and its number of files
(⏸ marks one you chose not to sort). Click one: its **card** says in one sentence where its files
go, computed as the move will do it (the files set aside never counted), and its photos fill the
grid. Then:

- **Sort here now**: its files move to that folder, journaled (`undo` puts them back), and the
  next event to decide is shown;
- **Another folder…**: the bar's **📂 Move to an event…**, on the photos picked, else on the whole
  event;
- **Do not sort this event**: its files stay where they are, the event counts as decided (saved
  in `/config/events/left.toml`, read back); **Undo my choice** makes it to decide again.
  Skipping it with → is not this: a skipped event stays to decide;
- **📚 Make an album**, **📺 On the TV** (once a TV is paired): the event's files, nothing moved;
- **📌 Remember as a rule**, under the buttons (see below).

## The keys

| Key | What it does |
|---|---|
| <kbd>N</kbd> / <kbd>P</kbd> (or Page Down / Page Up) | Next or previous event, without deciding: the ← → buttons around *Event 1 of 137*. |
| <kbd>U</kbd> | Next event to decide. |
| <kbd>M</kbd> | Sort here now. |
| <kbd>O</kbd> | Another folder…: the photos picked, else the whole event. |
| <kbd>Shift</kbd>+<kbd>S</kbd> | Do not sort this event. |
| <kbd>T</kbd> | Undo my choice: the event is to decide again. |
| <kbd>Delete</kbd> / <kbd>⌫</kbd> | Set the picked files aside / take them back out, as on every tile page. |

The photos are picked as in [the folders of `library`](../commands/library.md#walk-through-your-folders): a click picks one photo; the ☑ box
of each thumbnail (or Ctrl+click) adds or removes one; Shift+click picks every photo from the last
one clicked; a rectangle dragged with the mouse over the grid picks what it touches; Ctrl+A every
photo of the event. **Invert the picking** (or I) picks the others. Enter (or a double click)
opens the framed photo large.

## Events made on the pages, never by hand

An event you name is **remembered** for every later `classify`: its name, its days and the
cameras of its photos. You never write it in `config.toml` yourself: three gestures of the pages
do it, and each one says what it saved, read back from the disk.

- **Move to an event…** On the search page, give a period or open a folder, pick the photos,
  then *Move to an event…* and type its name. Before the move, the dialog says what will be
  remembered: "It will be remembered as the event 'Turin' (events/)", or "in the event
  'Turin'" when the photos widen one already known, and the cameras ("Cameras: Apple iPhone
  12."). After the move: "The event 'Turin' is remembered: 2019-07-12..2019-07-19."
- **The events found in your folders.** Folders you already sorted by hand
  (`2019\2019-07\Montenegro`) are events too. At the top of the 🗂 Events tab, *N events found
  in your folders* lists them, each with its days and its number of files, all ticked: untick
  those that are not events worth remembering, then **Confirm these N**. Confirm acts on the
  rows shown only: with a filter typed, or a group folded, the hidden rows stay to decide, untouched. The ticked ones are
  remembered; the unticked ones are noted as "not events" and never proposed again (*N folders
  said not to be events*, folded below, lets you tick one back). A folder whose photos are far
  apart in time (`Prints jan10`) is a batch, not one event: it is listed apart, never proposed.
- **New photos during an event.** A spouse's phone, a USB stick, a friend's photos: files of a
  remembered event's days that are in none of its folders. The Events tab and the home page say
  "N new photos during 'Turin' — see them?". *See them* shows them on the grid, those of the
  event's camera ticked; then **Add the picked to the event…** (the move above, journaled: `undo`
  puts them back) or **Refuse the picked** (never proposed to this event again).

**The same name, several events.** `Turin` every two or three years is one event each time: a
move to `Turin` joins the `Turin` whose days touch the photos' days (a day apart at most), else
it starts another one, saved as `Turin (April 2022)`. The page says so before the move ("It
will be remembered as a new 'Turin (April 2022)': 'Turin' is another event") and names each one
with its month when several share a name: `Turin (July 2019)`.

**Two events on the same days.** You at the seaside, your daughter at a scout camp the same
week: two events whose days overlap. Their cameras tell their photos apart (your phone, hers),
so they live side by side without a warning. A late photo is ranked by its camera: the event's
own (*✔ Probably: the event's camera*), another one (*During the event, but another camera:
elsewhere?*), the camera of the other event of those days (*Rather the event 'Camp' (its
camera)*). A photo with no camera in its EXIF (a scan, a picture received) is never guessed:
*No camera in this file: is it of the event?*

**Where your "no" goes.** Not in `config.toml`, which must not keep growing: the photos refused
for an event go to `/config/events/<start>-<name>.toml` (`C:\Users\you\media-hygiene\config\events\2019-07-12-Turin.toml`),
the folders said not to be events to `/config/events/not-events.toml`. Both list the files'
content (their SHA-256), not their paths: a refusal still holds after the photo moved or was
renamed.

**Where your events go.** Not in `config.toml` either: each event is a `[[rules]]` table of
`/config/events/<year>.toml`, the year it starts in (`…\config\events\2019.toml`), read with
the rules of `config.toml` by `classify` and the pages, just above *Existing folders*. You may
rename such a file (every `events\*.toml` holding `[[rules]]` is read) or edit it; deleting it
forgets its events. Events written into `config.toml` by an older version move there with
[`mh config tidy --apply`](../commands/config.md#tidy-it-config-tidy), once, a copy kept first.

## Remember an event as a rule

A move holds for the files moved; a **rule** holds for every later `classify`, the photos added
later included (a new copy from the phone, a person's folder of the same days).
**📌 Remember as a rule** opens the rule dialog of the search page on the event's days
([`library`](../commands/library.md#make-a-period-a-rule)): its name, its days (which you can
widen), its folder. Before saving, the dialog shows the photos the rule would take; saved, the
rule is written into `/config/events/<year>.toml` (`config.toml` stays as you wrote it), read
back from the disk and said with its time.

## Where your choices go

- **Sort here now** and **Another folder…** move the files at once, journaled: each run has its
  own `undo` ([`undo`](../commands/undo.md)), and `mh status` counts them sorted.
- **Do not sort this event** is kept in `/config/events/left.toml`, read back from the disk.
- Nothing is written next to a `classify` plan any more. A `sort-decisions.json` an older
  version wrote there is still read by `sort`, **on top of** the workbook, and a workbook edit
  of the same event or file made since is a conflict `sort` lists, never settled silently.

---

← [10. Sort by person](10-sort-by-person.md) · [Documentation](../README.md) · Next: **[12. Albums](12-albums.md)** →
