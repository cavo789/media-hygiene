# 0091 — People: name the groups on the page, then find them with `search` ("Chloé montagne")

- **Priority**: Medium — asked by the maintainer (2026-10-11); the most visible use of `people`
- **Batch**: people
- **Depends**: —
- **Files**: `src/media_hygiene/people/app.py`, `src/media_hygiene/people/board.py`, `src/media_hygiene/people/templates/people.html.j2`, `src/media_hygiene/people/` (new `config_file.py`, like `places/config_file.py`), `src/media_hygiene/services/people.py`, `src/media_hygiene/services/people_groups.py`, `src/media_hygiene/services/people_page.py`, `src/media_hygiene/config/people_settings.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/tags/models.py`, `src/media_hygiene/tags/producers.py`, `src/media_hygiene/search/fts.py`, `src/media_hygiene/search/query.py`, `src/media_hygiene/console/people_view.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/reference-people.md`, `documentation/fr/reference-people.md`, `documentation/en/commands/people.md`, `documentation/fr/commands/people.md`, `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`, `documentation/en/reference-tags.md`, `documentation/fr/reference-tags.md`, `tests/unit/`, `tests/integration/people/`

## Context

`people` (0058, first slice) finds the faces, groups them and shows the groups on a local
read-only page. The groups have no names: the page cannot say "this is Chloé", and `search`
does not know who is on a photo. The maintainer asked (2026-10-11):

> name the groups ("this one is my daughter Chloé, here Manon, there me"), then
> `search` "photos of Chloé in the mountains".

Naming and its uses are listed under "Not done" in `PARTIAL_0058-people-from-faces.md`. This
TODO takes the naming and the `search` part out of 0058. The `match = "person"` classify rule,
the XMP `PersonInImage` field (0074) and the `inventory` column stay for later. The sort step
(0088) waits for the classify rule.

"Montagne" already comes from the other tag sources: the vision words (`tags`, Ollama), the
folder names, the GeoNames town. `search` puts both words together (AND, any source). So
only the `person` source is missing.

## Goal

### 1. Name the groups (`people` page, no longer read-only for names)

- On a group: type a name (with suggestions from the names already given), Enter saves it. Also:
  **merge** two groups (same person split in two), **remove** a wrong face from a group,
  **ignore** a group (strangers, posters, statues). Keyboard driven, like `review`.
- Stored in `config.toml` as `[[people]]` (`name`, the confirmed reference face ids, an
  `ignored` list), written with tomlkit (comments kept, atomic write) like
  `[[classify.places]]`. Each save is read back from disk and shown (proof, not promise).
  A face id must survive a new grouping. Key it by file identity + face index, not by the
  group number.
- Several reference sets per person (children who grow up): naming a second group "Chloé"
  adds references, never replaces them.
- **Assignment**: a face gets the name of the nearest confirmed reference above
  `[people] similarity`. Below that threshold, it stays unnamed. A new grouping never loses a
  name. Named groups come first on the page with their name. A new face close to a person is
  a **suggestion** ("Chloé?") until the user confirms it.
- Same server rules as `places`: loopback `Host`, JSON-only `POST`. The page writes only
  `config.toml`, never the photos or the face index.
- The console summary lists the people by name (`Chloé: 1,234 photos`), then the unnamed groups.

### 2. Find them (`search`)

- New `TagSource.PERSON = "person"`. Its words are the names of the people on the photo
  (confirmed or assigned, not suggestions), produced from the faces + `[[people]]` at each
  `search` start, like the other sources. No separate tagging run is needed.
- `search Chloé montagne` finds the photos with Chloé and "montagne" from any source.
  `search person:Chloé montagne` limits the name to the people. `person:chloe` works too
  (the index folds accents and case). A name of several words (`"Mamie Jeanne"`) is a phrase.
- An unknown name gets one line telling the user to name the group in `people` first. It is
  never an empty result with no explanation.
- XMP (0074) and the label layer: write `PersonInImage` only in a later TODO. Do not write it here.

### 3. Privacy

- The names are in `config.toml`, the vectors stay in `/cache`. `people --forget` still deletes
  the faces. Ask, with a confirmation, whether it also deletes the `[[people]]` entries, and say
  what was deleted. Nothing leaves the machine.

## Before building

The 0058 measurement on the real collection (group quality at 2–3 thresholds) tells whether
the groups are clean enough to name as a whole, or whether "remove a wrong face" is the most
used action. Do it first with `people --sample` / `--path` on one year.

## Acceptance

- Naming, merging, removing and ignoring on the page; `config.toml` keeps its comments and is
  read back after each save; a new grouping keeps every name.
- `search Chloé montagne` and `search person:chloe` return the expected photos in tests
  (synthetic faces and fake vectors only, never a real face).
- An unknown person name explains itself in one line.
- Docs en + fr (`reference-people.md`, `commands/people.md`, `commands/search.md`,
  `reference-tags.md`), `--help` captures; `.po` translated.
- 0058's "Not done" points to this TODO for naming and search.
