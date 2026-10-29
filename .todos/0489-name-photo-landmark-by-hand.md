# 0489 — Let the user name the monument a photo shows

- **Priority**: medium
- **Batch**: unassigned
- **Depends**: —
- **Files**: TBD
- **Needs maintainer**: choose the storage and the entry point (questions below)

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

## Questions for the maintainer

1. Tag or dedicated landmark field?
2. Written into the XMP sidecar (other tools see it) or kept by media-hygiene only?
3. Where to type it: the large view of search/browse (key + field, skill
   `photo-picking-pages`), the slideshow, a CLI verb?
4. Apply it to the photos taken around the same spot at once?

## Acceptance

- [ ] The options above answered by the maintainer, and a follow-up implementation TODO filed
- [ ] The measured share of the maintainer's GPS photos for which `geo/landmarks` already
      finds a monument (tells whether typing is the exception or the rule)
