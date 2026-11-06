# `spots`: where your photos were taken, kept in the index

[Documentation](../README.md) › [Commands](../reference-commands.md) › `spots` · 🇫🇷 [Français](../../fr/commands/spots.md)

## In short

**A monument or a town you remember finds the photo.**

For each photo with a GPS position, the index keeps the landmark it was taken at (within
200 m), its town, its two levels of region and its country. [`library`](library.md) then
finds it by any of them ("Montagne de Bueren", "Colmar", "Haut-Rhin"), shows
`📍 Montagne de Bueren · Liège` under the date, and the [slideshow](slideshow.md) reads it
instead of working it out at each show.

**Every `audit` does it for you**, new photos included. Run `spots` once after an upgrade if
you do not want to wait for the next audit; it is on the home page too, under *Find*. *Give your
photos words*, on the same page, does it first, with its progress line.

## At a glance

| | |
|---|---|
| Your photos | 🔒 Not read, never changed: only the positions the index already holds (`--vision` 🤖 reads them, never changes them). |
| Needs | `/cache` (the index): run [`audit`](audit.md) once before. |
| Writes | In the index only. |
| Sends | Nothing. The towns and landmarks come from the GeoNames copy inside the image. With `--vision` 🤖, the photos go to your local model only. |

## Run it

In Windows PowerShell:

```powershell
mh spots
```

A second run writes nothing and takes a moment: a position is named once. Stopped halfway, it
goes on where it stopped.

## What is shown

- Your own [place](places.md) first, else the town: `Home`, `Liège`. A place you draw applies
  at once.
- The landmark comes before it: the name you accepted from OpenStreetMap after an
  [`import`](import.md) (never sent without your Yes), else GeoNames'.
- The regions (`Grand Est`, `Haut-Rhin`) can be searched, and are not shown. A folder called
  "Alsace" comes from your own place: GeoNames only knows today's regions.
- More than `[tags] town_km` (20 km) from any town, no town is named.

A photo moved by [`sort`](sort.md) or [`undo`](undo.md) keeps its row. A folder renamed in
Explorer is named again at the next audit.

## 🤖 The building the photo shows: `--vision`

The GPS alone names the nearest monument within 200 m: a cathedral photographed from across
the square gets nothing, a photo taken next to a castle, facing away, gets the castle. With
your own local vision model (Ollama, set in `[classify.ai] model`, like [`tags`](tags.md)):

```powershell
mh spots --vision   # 🤖 needs a local AI model
```

The model sees each located photo and picks, among the landmarks within 1 km (the 10 nearest),
the one it shows, or none. A short list to pick from, never a free guess: an answer outside it
leaves the photo as it was. Each pick is kept in the index at once, searchable, and asked once.
A name you typed by hand always wins: such a photo is never sent. Without a model, or with the
server not answering, nothing changes. The photos go to your local model only.

## The built-in help

<details>
<summary><code>spots --help</code></summary>

<!-- capture: help-spots.txt -->
```text
 Usage: media-hygiene spots [OPTIONS]

 🔒 Read-only: never changes your photos. Name where the photos already indexed
 were taken (landmark, town, regions), offline; the audit does it for new ones.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help  -h        Show this message and exit.                                │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
