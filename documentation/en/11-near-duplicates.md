# 11. Near duplicates

[Documentation](README.md) › Step 11 of 13 · 🇫🇷 [Français](../fr/11-near-duplicates.md)

Some copies are not identical files, yet they are the same picture: the photo sent through
WhatsApp (smaller), the one "reduced for email", a copy saved again with another quality, turned
upright, or without its date. The audit finds them too, as **near duplicates**, and leaves them
alone unless you ask.

## How the tool recognises them

While it checks that each photo can be read, the audit also describes what it looks like
(perceptual fingerprints, sharpness, EXIF date and camera) and keeps it in the cache. Two photos
are near duplicates only if **every** test agrees:

- nearly identical perceptual fingerprints;
- the same shape (proportions);
- the same shot date, or no date at all on the smaller copy.

Blank or black pictures never count, and a shot of a [burst series](10-review-bursts.md) is
never taken for a near duplicate. In each group, the **highest resolution** is kept.

## Look at them first

The *Near duplicates* section of the [HTML report](04-html-report.md) shows each group side by
side, with the resolution, size and sharpness of every copy:

![Near duplicates in the report: a meadow photo kept in 1500 × 1000 pixels, its 1024 × 683 copy from an Email folder; a beach photo kept, its 800 × 533 WhatsApp copy, both copies marked to the quarantine with --tier near](images/report-near.webp)

Compare each copy with the kept one. The audit summary counts them on the line
*Near duplicates (moved only with --tier near)*.

## Move them: `clean --tier near`

Add `--tier near` to your `clean` command of [step 8](08-clean.md). Here it is combined with the
burst decisions of step 10; each option works on its own too:

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v "D:\Old disk:/data/d/Old disk" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene clean --tier near --decisions decisions.json
```

The question now mentions the near duplicates:

<!-- capture: clean-near.txt|re:^2 |❓ -->
```text
2 burst shots you set aside will be moved to the quarantine.
1 orphan sidecar (.xmp, .aae, .thm) will be moved to the quarantine.
❓ Delete 32 duplicate copies (13.9 MB), move 2 near duplicates to the
quarantine and handle 3 broken files? [y/N] y
```

<!-- capture: clean-near.txt|re:^─+ Clean| -->
```text
──────────────────────────────────── Clean ─────────────────────────────────────
Clean 20260929-192930
┌──────────────────────────┬─────────┐
│ Files processed          │      40 │
│ Size                     │ 16.2 MB │
│ Moved to the quarantine  │       7 │
│ Skipped (left untouched) │       0 │
│ Failed                   │       0 │
│ Duration                 │     0 s │
└──────────────────────────┴─────────┘
✅ HTML report: /reports/20260929-192930-clean/report.html
💡 Open index.html in the folder mounted on /reports: it lists every report.
💡 Changed your mind? 'media-hygiene undo 20260929-192930' restores everything.
💡 Moved files are in /quarantine/20260929-192930; 'purge' deletes them.
```

Near duplicates are **moved to the quarantine**, never deleted: they are not identical to the
kept photo, so nothing could rebuild them. The quarantine now holds, below the folder of this
clean, the near duplicates, the burst shots set aside, the unreadable files and the orphan
sidecar:

<!-- capture: quarantine.txt -->
```text
./20260929-192930/c/Photos/2022/Birthday/IMG_3003.jpg
./20260929-192930/c/Photos/2023/Lake/IMG_4004.jpg
./20260929-192930/c/Photos/WhatsApp/IMG-20190712-WA0003.jpg
./20260929-192930/d/Old disk/2020/IMG_1203.jpg
./20260929-192930/d/Old disk/Email/IMG_0110 small.jpg
./20260929-192930/d/Old disk/Photos 2019/IMG_0102.xmp
./20260929-192930/d/Old disk/Videos/Birthday (cut).mp4
```

Before moving each copy, `clean` checks that the kept photo still exists and that the copy is
the very file the audit saw. `undo` puts them back; `purge` deletes them for good
([step 9](09-undo-history-purge.md)).

---

← [10. Sort burst series in your browser](10-review-bursts.md) · [Documentation](README.md) · Next: **[12. Decide pair by pair](12-decide-pair-by-pair.md)** →
