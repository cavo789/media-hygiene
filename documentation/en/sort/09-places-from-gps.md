# 9. Places and trips from the GPS

[Documentation](../README.md) › Sorting, step 9 · 🇫🇷 [Français](../../fr/sort/09-places-from-gps.md)

Recent phones write **where** each photo was taken. With that, a photo can say "Home", "At
grandpa's" or "Italy/Turin" without any guess. Older phones and most cameras wrote nothing:
the [first audit](../start/01-first-audit.md) tells how many of your photos hold a GPS position
(*Photos and videos with a GPS position*). This step is **optional**: without positions,
everything else works the same.

## What leaves your computer

**Nothing.** Towns and countries are named from [GeoNames](https://www.geonames.org/) data
shipped with the image: about 160,000 towns of more than 1,000 inhabitants, read on your
computer. No position, no photo, no list of places is ever sent anywhere. Only the map of
`places` (below) loads **map tiles** in your browser: they show the areas you look at, never a
photo.

## Name your places on a map

`places` shows where your photos were taken, from the cache of the audits, and lets you name
the places that matter to you. It needs the cache (`/cache`, where the audits recorded the
positions) and the folder of `config.toml` (`/config`, where the places are saved):

```powershell
docker run --rm -it --name media-hygiene-places -p 127.0.0.1::8080 `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene places
```

As with [`review`](../clean/10-review-bursts.md#step-2-open-the-page), ask Docker for the
address in another window, `docker port media-hygiene-places 8080`, and open it in your browser.

- **The circles** are your photos with a GPS position, grouped by about 200 metres, larger
  where there are more. The list on the left gives the **largest clusters without a name**
  first: home is usually the first one.
- **Click a circle, or anywhere on the map**, to name a place. Give it a name, set its
  **radius** with the slider (a house: 100 to 200 metres; a village: a few kilometres), and
  drag its marker to move it. Tick **Home** for your home: trips are measured from it.
- **Find a town** searches the towns shipped with the image, offline, and zooms there.
- **Save** writes the place into `config.toml` at once, keeping your comments and the rest of
  the file. Click a place to move it, rename it or delete it.

Ctrl+C in the terminal stops the map. A place name becomes a folder name: two places cannot
share one, and the characters Windows refuses are refused.

You can also write the places by hand, the latitude and longitude copied from any map:

```toml
[[classify.places]]
name = "Home"
latitude = 50.0
longitude = 5.0
radius_m = 200
home = true

[[classify.places]]
name = "At grandpa's"
latitude = 50.1
longitude = 5.2
radius_m = 150
```

## Write the rules

The places do nothing on their own: two rules use them, in `[[classify.rules]]`
([step 6](06-write-down-what-you-know.md)):

```toml
[[classify.rules]]
name = "My places"
match = "place"

[[classify.rules]]
name = "Trips"
match = "trip"
```

- **`place`**: a photo whose position lies within the radius of one of your places goes to the
  place's name: `2023/Home`. Its category is `{place}` unless you write another one, such as
  `category = "Family/{place}"`.
- **`trip`**: the photos of an event **farther than `trip_min_km`** (100 km) from home are a
  trip. Its category is `{country}/{city}` unless you write another one, such as
  `category = "Holidays and outings/{country} {year}"`: `2023/Italy/Turin`.

Like a date rule, a GPS rule follows the **events** ([step 4](04-classify.md#read-the-result)):

- a photo **without** a position, in an event whose located photos lie at one of your places,
  goes there too; in a trip, it follows the trip. Its reason is then `place-neighbour` or
  `trip-neighbour`, with a lower score (70): "to check" by default, never a certainty;
- the days of a trip are joined by **distance, not by town**: events less than
  `trip_merge_gap_hours` (48 hours) apart and less than `trip_merge_max_km` (120 km) from each
  other make one trip, so a tour of villages stays one trip. A day without positions between
  two days of a trip joins it; a day back home ends it;
- a trip is named after the **largest town** within 10 km of its main day: a hotel in a suburb
  of Turin gives `Turin`. Country names are written in the language of the interface
  (`Italie` in French); town names are GeoNames' (often their English name, such as `Munich`).

| `[classify]` | Default | Meaning |
|---|---|---|
| `trip_min_km` | 100 | Farther from home than this, an event is a trip. |
| `trip_merge_gap_hours` | 48 | Events of a trip less than this apart are one trip. |
| `trip_merge_max_km` | 120 | …and less than this from each other. |

A `trip` rule needs a place with `home = true`: without one, the file is refused when it is
read, with the rule's name.

Layouts and categories may also use `{place}` (the personal place of the file) and `{country}`,
`{region}`, `{city}` (those of its trip); they are empty for the other files, and an empty
folder level is left out.

## Another map

The map tiles come from OpenStreetMap by default. Another tile server is set in `[places]`;
the page allows that server only:

```toml
[places]
tiles = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
attribution = "© OpenStreetMap contributors"
```

## Credits

Towns, regions and countries: [GeoNames](https://www.geonames.org/), under the
[Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/) licence.
Country names in English and French: [Unicode CLDR](https://cldr.unicode.org/). The map:
[Leaflet](https://leafletjs.com/) (BSD 2-Clause licence), shipped with the image, and the tiles
of the server you configure.

---

← [8. Name the subjects with a local model](08-subjects-from-a-local-model.md) · [Documentation](../README.md)
