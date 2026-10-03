# The inventory workbook

[Documentation](README.md) › Reference · 🇫🇷 [Français](../fr/reference-inventory.md)

One Excel file listing every photo, RAW file and video the audits have seen, with everything
they learnt about it: size, dates, device, settings, place, quality, duplicates. Sort and filter
it to answer your own questions: how many photos per year or per camera, which pictures are
blurry or tiny, which camera had its clock wrong.

`inventory` reads the cache ([step 2](start/02-keep-the-cache.md)) and nothing else: **no file
of your folders is opened**, it takes seconds even for tens of thousands of photos. Run an
`audit` first, with the same cache.

## Export it

```powershell
docker run --rm -it `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene inventory
```

No folder of photos is mounted: none is needed. The workbook lands in a new folder of your reports
folder, `<date>-inventory\inventory.xlsx`; the console says where, and when each folder was last
audited completely:

<!-- capture: inventory.txt -->
```text
✅ Inventory of 82 files written:
/reports/20261003-080655-inventory/inventory.xlsx
Last complete audit (UTC)
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
┃ Folder      ┃ Date             ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
│ C:\Photos   │ 2026-10-03 08:06 │
│ D:\Old disk │ 2026-10-03 08:06 │
└─────────────┴──────────────────┘
```

The inventory is as fresh as the last audit: a photo added since then is missing, a photo deleted
by hand is still listed. Audit again, then export again.

## The Files sheet

One row per file, a frozen header row and a filter on every column. Numbers are numbers and dates
are dates, so sorting and filtering work whatever the language of Excel.

- **Where**: the file as you know it (`C:\Photos\…`), its folder, its name, its kind (photo, RAW,
  video), its size and modification date (UTC).
- **When**: the date taken, read as `classify` reads it ([sorting, step 4](sort/04-classify.md)),
  where it comes from (EXIF or the video tags), its year, and the time zone the file records.
- **With what**: the camera, the lens, the focal length, the exposure time, the aperture, the ISO,
  whether the flash fired; the software that last wrote the file.
- **How it looks**: width and height, sharpness, format, estimated JPEG quality, mean brightness
  and the shares of pure black and pure white pixels, the stars given in Windows.
- **Where it was taken**: latitude, longitude, altitude; for a video, the place its tags hold.
- **Videos**: duration, codec, frames per second, bit rate.
- **State**: healthy, not checked, or why it cannot be read, with the decoder's message.
- **Duplicates**: the SHA-256, the number of its group of identical files and how many copies
  that group holds. Only files that looked like another one (same size, same first bytes) have a
  SHA-256: the others cannot have an identical copy. Which copy `clean` would keep depends on your
  settings: that is the job of the report's `plan.csv` ([step 4](clean/04-html-report.md)).

RAW files only have their size, dates and fingerprint: their content is not decoded. Files other
than photos and videos (`--ext pdf`, [step 6](clean/06-file-types.md)) are left out.

## The Summary sheet

First the date of the last complete audit of each folder, then the number of files per kind,
year, camera, format and state, with and without a date, with and without GPS, and the number of
files that have an identical copy.

## Quality and exposure labels

Two columns turn measures into words, **at export time**: *Quality* (blurry, small) and
*Exposure* (dark, bright), or *ok*. Their thresholds are in `config.toml`
([step 7](clean/07-configuration-file.md)):

```toml
[inventory]
blurry_below = 100.0   # sharpness below this: blurry
small_below = 1000     # shorter side, in pixels, below this: small
dark_below = 50.0      # mean brightness (0 to 255) below this: dark
bright_above = 205.0   # mean brightness above this: bright
clipped_above = 0.25   # more than this share of pure black (white) pixels: dark (bright)
```

A night sky is dark on purpose: change a value and export again, nothing is read again.

## A CSV file instead

`inventory --format csv` writes the Files sheet alone, as `inventory.csv`, like `plan.csv`: in
French, `;` between the columns and a decimal comma, so that Excel opens it as is.

A text that starts with `=`, `+`, `-` or `@` (a file named `-2019 trip.jpg`) is written with a
leading apostrophe, `'-2019 trip.jpg`: otherwise Excel would compute it and show `#NAME?`. The
workbook (`xlsx`) needs no apostrophe: it keeps such names exactly.

## The cache itself

The cache is a SQLite file, `index.sqlite`, in the `media-hygiene-cache` volume. Any SQLite
browser opens it, for instance [DB Browser for SQLite](https://sqlitebrowser.org/): copy it out
of the volume first, and open the copy **read-only**, so that nothing changes it by mistake.

---

[Documentation](README.md) · [Commands and options](reference-commands.md)
