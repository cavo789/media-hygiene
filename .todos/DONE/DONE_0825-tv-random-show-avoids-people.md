# 0825 — TV random show: "avoid photos of these people"

- **Priority**: Medium
- **Batch**: tv-slideshow
- **Depends**: none
- **Files**: `src/media_hygiene/review/templates/home_run.js.j2`, `src/media_hygiene/services/slideshow_random_pick.py`, `src/media_hygiene/services/slideshow_choices.py`, `src/media_hygiene/person/likeness.py`, `src/media_hygiene/config/people_files.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/slideshow.md`, `documentation/fr/commands/slideshow.md`
- **Needs maintainer**: try it with a real named person on the family TV

## Reported (maintainer, 2026-11-15)

A daughter's new partner watches the family slideshow; the PC still holds many photos with
her former partner. The 🎲 *At random* choice (0508, `tvRandomBox` in `home_run.js.j2`)
should ask "Avoid showing photos of some people?" and list the people named (`[people]`,
`/config/people/<name>.toml`, 0300) as checkboxes, e.g. tick "Antoine": none of his photos
reaches the TV.

## What

- **Phone/home side**: in every TV choice (under the length and years of `tvRandomBox`, and on the folder/month choices), a folded line "Avoid
  some people" opening one checkbox per named person (name only, no face thumbnail needed
  on the TV; the phone may show the person's cover face if the shared component exists).
  No person named → the line is not shown. Each choice's body carries `avoid: [names]`.
- **PC side**: the selection (`slideshow_random_pick` before `journey` draws its events, and the folder/month selections) drops every photo
  where a face belongs to an avoided person. "Belongs" must be generous — a photo missed
  is the embarrassing case, an extra photo left out costs nothing: the person's named
  faces **and** the index faces close to their mean (`person/likeness.py`, the same
  `LOOK_ALIKE` distance `/person` uses), not only the photos explicitly named.
- **Say it**: the phone's confirmation states it ("60 min, 1 234 photos left out: Antoine"),
  a count the user can trust (product rule: never act on hidden without a stated size).
- **Never stored by default**: the choice is for this show only (privacy: who is avoided
  is nobody's business on a shared TV); nothing shown on the TV about it.

## Decided (maintainer, 2026-11-15)

1. **Every TV choice**, not only *At random*: the same shared "Avoid some people" block
   on the folder and month choices too (a folder "Holidays 2022" has the same problem);
   the filter applies to whatever selection is sent.
2. **Asked each time**: nothing stored in `config.toml`; the ticked boxes live for the
   page's session only.
3. **No link to `/people`** from the block: naming is a PC-only action, the phone stays
   read-only. Unnamed faces are covered by the generous likeness match only.

## Tests

- A random show with a person avoided holds none of their named photos nor a photo whose
  face is within `LOOK_ALIKE` of their mean; a photo with only other people stays.
- A folder or month show with a person avoided drops their photos the same way.
- No person named → no `avoid` block in the page; an unknown name in `avoid` is ignored.
- The stated count matches the photos dropped.
