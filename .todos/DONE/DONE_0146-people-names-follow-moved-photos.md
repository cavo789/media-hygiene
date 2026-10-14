# 0146 — Names confirmed in `people` survive `sort`, `undo` and every move of a photo

- **Priority**: High — after a `sort`, the classify → sort workflow the guides lead to, every name confirmed on the `people` page stops applying, silently
- **Batch**: people
- **Depends**: —
- **Files**: `src/media_hygiene/index/repository.py`, `src/media_hygiene/index/schema.py`, `src/media_hygiene/people/naming.py`, `src/media_hygiene/people/roster.py`, `src/media_hygiene/people/changes.py`, `src/media_hygiene/services/people.py`, `src/media_hygiene/search/people_words.py`, `documentation/en/commands/people.md`, `documentation/fr/commands/people.md`, `documentation/en/sort/07-sort.md`, `documentation/fr/sort/07-sort.md`, `tests/integration/`

## Context

Speed and cache review of 2026-10-14 (third pass). The maintainer asked that `classify` and the
moves that follow keep the cache up to date rather than invalidate it.

The index follows a photo that `sort` or `undo` moves: `FactsRepository.move` runs
`schema.MOVE` on `files`, `descriptions`, `tags`, `face_scans`, `faces` and `measures`. The names
do not follow:

- `config.toml` keeps every confirmed face as `<container path>#<number>`
  (`people/naming.face_id`): `[[people.person]] faces` and `rejected`, `[people] ignored`.
- `Known.of` keeps only the confirmed ids it finds among the faces of the index: "a face id
  no longer in the index is left out".

Checked on 2026-10-14 with the real classes: a face confirmed as "Chloé" at
`/data/c/Photos/2019/IMG_0001.jpg#0` gives `Known.of(...).people == ('Chloé',)`; the same face
stored at `/data/c/Photos/Tri/2019/Noel/IMG_0001.jpg` gives `()`.

After a `sort`, the `people` page therefore shows every group unnamed again, `tags` loses the
people words (`search/people_words.py`), the `person` rule of `classify` (0095) and `xmp` (0111)
see nobody. Nothing is deleted: the confirmations are still in `config.toml`, and an `undo` of
the sort brings the names back. Only the link between an id and its face is lost. Every
future row move breaks the link the same way: 0147 (files moved outside the tool) and 0156
(rows kept in the quarantine) need this TODO first.

## What to do

Keep the ids as the user's file holds them, and resolve old ids through the moves the index
made:

1. `FactsRepository.move` also writes each move into a new `moves` table (old path, new path,
   when), in the same transaction as the rows it moves (schema 11, created on upgrade).
2. One resolver, used by `Known.of`, `people/changes.py` (ignored, rejected) and every other
   place that matches a confirmed id: an id whose path is not in the index follows the moves
   (A → B → C) to the current path. A cycle (`sort` then `undo`: A → B → A) ends on the path
   that exists in the index.
3. The next time `people` saves the names (`roster.py`, then read back as today), it writes
   the current ids, so `config.toml` catches up without a manual step. Say it in one line,
   e.g. "Names of 12 faces follow the photos `sort` moved: config.toml updated."
4. Rejected alternatives, for the record: rewriting `config.toml` during `sort`/`undo`
   (`/config` may be absent or read-only then, and `sort` should not edit the settings file);
   ids based on the content (a digest per photo, see 0148, plus a migration of every
   `config.toml`).
5. Docs en + fr: `commands/people.md` and `sort/07-sort.md` say that the names follow the photos
   `sort` moves.

## Acceptance

- Integration test: confirm a name, move the photo with `FactsRepository.move` (as `sort` does),
  then the same name reaches `people`, `tags` and the `person` rule. Also after `sort` then
  `undo`, and after two successive sorts.
- After the next `people` save, `config.toml` holds the new ids, comments kept, read back.
- An index of schema 10 upgrades (fixture), with an empty `moves` table.
