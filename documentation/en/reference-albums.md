# Albums

[Documentation](README.md) › Reference · 🇫🇷 [Français](../fr/reference-albums.md)

An **album** is a named list of photos and videos, *Crete 2023*, gathered from any folders. It is
what you show to others: on the TV with [`slideshow`](commands/slideshow.md), on a phone, ready to
send with [`share`](commands/share.md), or as a folder of the Explorer with
[`album`](commands/album.md).

## What an album is here

- **A list of references, nothing else.** No photo is copied, moved or changed: the files are
  only read.
- It is saved in `albums.json`, in your reports folder (`/reports`), **not** in the cache:
  deleting the cache keeps your albums.
- A photo moved since by [`sort`](commands/sort.md) or [`undo`](commands/undo.md), or in a folder
  you renamed (once an audit has seen it), is found again by its content — searched in the
  background, so the page never waits: it shows the photo again a moment later; one found nowhere
  (deleted, or in the quarantine) stays in the list as *missing* until it comes back.

## Fill an album

In [`search`](commands/search.md#put-photos-in-an-album) or [the folders of `search`](commands/search.md#walk-through-your-folders), pick
the photos, type the album's name in **Album** (the albums already made are proposed; a new name
creates it), then **➕ Add to the album**. The page says what it saved, read back from the disk.

## The albums page

`mh` opens it at `/albums` (the home page's *Share* area, *Your albums*). It shows every album
with its cover, its dates and its place; a click opens one, its photos by day, and a photo opens
full screen.

From the page, on the PC (a phone only looks: albums change on the PC), you can:

- **🗑 Delete** the albums ticked in the list: the page asks once, then only `albums.json`
  changes, your photos stay where they are; **↩ Undo** in the message puts them back (the last
  delete is kept next to the albums file, in `albums-deleted.json`);
- **✏️ Rename** an album: a name another album has (whatever its case) is refused; `slideshow`,
  `share` and `album --album` know it by its new name at once. A folder of links already made by
  `mh album` keeps its old name;
- **➖ Take out of the album** a photo: it leaves the list, the file stays where it is;
- **➕ Add to an album** a photo, to another album: pick it in the list of your albums (the most
  recent first), or type a new name under it to create one; a name typed in another case is the
  same album;
- **🖼 Use as cover** a photo: the list of albums shows it from now on, after a restart too. The
  cover follows its photo when the file moves; taken out of the album, the cover goes back to
  the one `mh` picks (the sharpest photo of the first day).

Only `albums.json` changes. Nothing else can be done there: no file is deleted, moved or sent.

### On a phone

Under `mh --lan`, a phone paired by its code on the home Wi-Fi opens the same page, while `mh`
runs on the PC. It sees the pictures of the albums only, sized for a phone, never another photo
of the library nor an original. It changes nothing: no *➖*, *➕*, *🖼*, *🗑* nor *✏️* there.

## Albums and the folders of links

[Step 12 of the sorting guide](sort/12-albums.md) and [`album`](commands/album.md) turn an album
into a **folder of hard links** on the disk, to open in the Explorer. The list is the same: the
folder is one more way to use it, and `undo` removes it. The albums page never makes that folder.

## Go further

- [`search`: put photos in an album](commands/search.md#put-photos-in-an-album)
- [`slideshow`](commands/slideshow.md), [`share`](commands/share.md), [`album`](commands/album.md)

---

← [Documentation](README.md)
