# `places`: name your places on a map

[Documentation](../README.md) › [Commands](../reference-commands.md) › `places` · 🇫🇷 [Français](../../fr/commands/places.md)

## In short

**Name the places that matter to you on a map (home, grandpa's, a village), so that `classify`
sorts your photos by place and by trip.**

Recent phones write **where** each photo was taken. `places` shows those positions on a map in
your browser, grouped in circles, and saves the places you name into `config.toml`, where the
`place` and `trip` rules of [`classify`](classify.md) use them.

**When**: before [`classify`](classify.md), once an audit run with the [cache](../reference-glossary.md#cache) has read the
positions; again whenever a new place matters.

**Try it**:

```powershell
docker run --rm -it `
  -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene places
```

## At a glance

| | |
|---|---|
| Your photos | 🔒 Never changed: the positions come from the cache. The photo folders, read-only (`:ro`), show the photos of a cluster; without them, the map works but shows no photo. |
| Needs | `/cache` (the positions the audits recorded, and the previews), `/config` (where the places are saved), your photo folders read-only, and `-p 127.0.0.1:8088:8088`. |
| Writes | `[[classify.places]]` entries in `config.toml`, keeping your comments and the rest of the file. |
| Undo | Delete a place on the map, or its lines in `config.toml`. |
| With `mh` | `mh places`: your photo folders are mounted read-only and the port is published for you. |

## Run it

```powershell
docker run --rm -it -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene places
```

Ctrl+click the address it prints, `http://127.0.0.1:8088/`. Ctrl+C stops the map.

![The places map: OpenStreetMap tiles of the Cinquantenaire park in Brussels, the circle of the photos taken there, the green circle of the place Parc du Cinquantenaire just saved, and on the left the list of places and of the largest clusters without a name](../images/places.webp)

## On the map

- **The circles** are your photos with a GPS position, grouped by about 200 metres. The list on
  the left gives the largest clusters without a name first: home is usually the first one.
- **Click the number of photos** (for instance "11 photos") on a line of that list to see the
  photos of the cluster (24 at most) and recognise the place before naming it; hover a photo to see where it was taken.
  Click again, or ✕, to close them.
- **Fold a list** by clicking its title: *Your places (10)* folds by itself from 8 places on,
  so that the clusters stay in reach; your browser remembers your choice.
- **Folders named after a town** lists the folders whose name is a town's (`Douarnenez`,
  `Saint-Jean de Luz`) and that hold photos without GPS: *📁 Douarnenez — 37 photos without GPS*.
  Click one: the map goes to the town, a green pin marks its centre and the photos show below.
  Drag the pin where they were taken (the beach, not the town hall) and click **Save this
  position**: it goes into `config.toml` as `[[places.folders]]`, read back and shown with 📌.
  [`xmp`](xmp.md#a-position-from-the-folders-town) then writes that position into the photos'
  sidecars. **Forget its position** takes it out; **Not a town** adds the folder's name to
  `[classify] folder_town_ignore` (a folder `Martin` is a first name, not Martin in Slovakia).
  A saved folder renamed or moved since shows ⚠ *not found*: rename it back, or forget it.
- **Click a circle, or anywhere**, to name a place; set its radius with the slider, drag its
  marker. Tick **Home** for your home: trips are measured from it.
- **Find a town** searches the towns shipped with the image, offline.
- **Search OpenStreetMap** finds a village, a district or a park with its outline: the photo then
  belongs to it when it was taken inside.
- **Save** writes the place into `config.toml` at once; its line flashes in *Your places*. Click
  a place to move, rename or delete it.

## Options

| Option | What it does |
|---|---|
| `--port PORT` | Port of the page, 8088 by default; publish the same one. |

## What leaves your computer

No position, no photo, no list of places. The photos of a cluster are shown by the tool itself,
from your folders; their previews stay in `/cache`. The map loads **tiles** (the areas you look at) from
the server of `[places] tiles`; **Search OpenStreetMap** sends the **text you typed**, on your
click only, to `[places] nominatim_url` (empty turns that search off). `classify` never goes
online.

## Good to know

- A place name becomes a folder name: two places cannot share one, and the characters Windows
  refuses are refused.
- The places do nothing on their own: add a `place` or a `trip` rule in `[[classify.rules]]`. A
  `trip` rule needs a place with `home = true`.
- Places can also be written by hand in `config.toml`, the latitude and longitude copied from any
  map.

## Go further

- [Sorting, step 9: places and trips from the GPS](../sort/09-places-from-gps.md)
- [Sorting, step 6: the rules](../sort/06-write-down-what-you-know.md)

## The built-in help

<details>
<summary><code>places --help</code></summary>

<!-- capture: help-places.txt -->
```text
 Usage: media-hygiene places [OPTIONS]

 🔒 Read-only: never changes your photos. Name your places on a map of where
 the photos were taken; saved into config.toml for the 'place' and 'trip'
 rules.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --port          <int range> [x>=1]  Port of the page. docker run publishes   │
│                                     it under the same number on your         │
│                                     computer: -p 127.0.0.1:9000:9000 for     │
│                                     --port 9000. Default: 8088.              │
│ --help  -h                          Show this message and exit.              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
