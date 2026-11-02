# 0489 — Let the user name the monument a photo shows

- **Priority**: medium
- **Batch**: unassigned
- **Depends**: 0545, 0553
- **Files**: TBD
- **Needs maintainer**: the measured share of their GPS photos for which `geo/landmarks` already finds a monument (storage decided 2026-11-02)

## Context

The maintainer sometimes pastes a photo into Google Images to learn the building it shows
("Sacra di San Michele") on top of the town the GPS already gives. There is no way to keep
that name with the photo today. Two pieces already exist: the tags (`tags/`, written to XMP
by `xmp_*`) and the offline GeoNames landmarks (`geo/landmarks.py`, 0472) which may already
suggest the monument from the GPS position, without any typing. This is a thinking TODO:
list the options, then ask.

## Options to weigh

- **A plain manual tag** (`TagSource` "user"): cheapest, reuses the tags pipeline and search;
  but the name is lost among the other words, and the slideshow/classify cannot tell it is a
  place.
- **A dedicated landmark field**: written as XMP `Iptc4xmpCore:Location` / `photoshop`
  sublocation (`Iptc4xmpExt:LocationShown/Sublocation`), read by Lightroom, digiKam, Immich;
  shown in the slideshow's place corner ("Sacra di San Michele · Sant'Ambrogio di Torino"),
  usable by `classify` folder names and search.
- **Where it lives**: XMP sidecar only (survives moves, readable by other tools), index only
  (lost if the index is rebuilt, path-keyed: see the move rules of `workflow.md`), or both
  (XMP the truth, index a cache).
- **Spread to neighbours**: one name typed once applied to the other photos of the same spot
  (same GPS cluster, same burst/day) — offered, never silent.
- **Suggestion first**: when `geo/landmarks` finds a monument within `NEAR_M`, propose it so
  the user only confirms; the Google Images lookup stays for the cases GeoNames misses. No
  reverse image search from the tool itself (a photo would leave the machine).

## Maintainer's request (2026-10-31)

A photo of Liège (`20261029_124120.jpg`, stairs of Montagne de Bueren) got
"Montagne de Bueren" in the slideshow. The maintainer wants to **say a name is wrong**
and **be offered other names**: the GeoNames landmarks around the spot (e.g. within
500 m, nearest first, with their distance), the OSM name if one was fetched, and a free
field. A rejected name must not come back at the next show or scan (stored with the
correction). Ask the questions below when running it.

## Maintainer's answer to question 1 (2026-10-31)

**A monument confirmed becomes a place** (`[[classify.places]]`, its photos in
`places/<name>.toml`, 0551) — no new procedure, no new storage:

- GeoNames proposes the name from the GPS ("Montagne de Bueren, 120 m"); the user confirms,
  picks another, or types one. Confirmed → a place whose circle is already drawn around the
  landmark's position: every GPS photo inside gets it at once, future ones too.
- Photos without GPS: the search's *📍 Place…* on a selection (0553), like any place.
- Seen on the photo as a **📍 chip** beside its tags (tile, large view), searchable, so it
  looks like a tag while the data stays a place (slideshow corner, `classify`, XMP location
  fields `Iptc4xmpExt:LocationShown/Sublocation`).
- A rejected suggestion is stored (`rejected`, like `people/`) and never proposed again.
- Not a hand tag (0555): those are for words that are not places ("anniversaire Léa").

## Questions for the maintainer

1. ~~Tag or dedicated landmark field?~~ Answered above.
2. Written into the XMP sidecar (other tools see it) or kept by media-hygiene only?
3. Where to type it: the large view of search/browse (key + field, skill
   `photo-picking-pages`), the slideshow, a CLI verb?
4. ~~Apply it to the photos taken around the same spot at once?~~ Yes, by the place circle (above).

## Acceptance

- [ ] The options above answered by the maintainer, and a follow-up implementation TODO filed
- [ ] The measured share of the maintainer's GPS photos for which `geo/landmarks` already
      finds a monument (tells whether typing is the exception or the rule)

## Decided (2026-11-02)

By the maintainer, in `/todo:iterate`: the name is written into the XMP sidecar (the truth,
read by other tools, survives moves) and cached in the index; it is typed in the large view of
search/browse (skill `photo-picking-pages`).
