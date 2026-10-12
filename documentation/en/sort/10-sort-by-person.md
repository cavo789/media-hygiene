# 10. Sort by person

[Documentation](../README.md) › Sorting, step 10 · 🇫🇷 [Français](../../fr/sort/10-sort-by-person.md)

Dates, folders and places ([steps 6 to 9](06-write-down-what-you-know.md)) tell **when** and
**where**. This step adds **who**: the events where Chloé appears go to `2023/People/Chloé`, or
to the folder you choose. You name each person once, on a page of your browser; a rule of
`classify` does the rest. This step is **optional**: without it, everything else works the same.

It adds one thing to the commands of the previous steps: `people`, to find and name the faces.
`classify`, the workbook, `review-sort` and `sort` stay as they are.

## What leaves your computer

**Nothing.** The faces are found and compared on your computer; they stay in the cache
(`/cache`), never in your photos, never in the reports. The names go into your `config.toml`, as
text. The only download is the two face models (39 MB), once, from OpenCV Zoo: it sends nothing
about your photos. `people --forget` deletes every face ([below](#forget-the-faces)).

## 1. Measure first

Finding the faces takes time: about a fifth of a second per photo, measured on a home computer,
so hours for a large collection the first time. Each photo is analysed **once**: the next runs
analyse only the new ones. Measure on 200 photos at random before the long run:

```powershell
mh people --sample 200
```

<details>
<summary>Without <code>mh</code>: the full command</summary>

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  cavo789/media-hygiene people --sample 200
```

</details>

It ends with the estimate of the full run (`A full run would analyse 20,000 more photos: about
1 h 10 min.`); the faces found are kept. Rather let it run after your next audit?
`audit --people` audits, says how long the faces take, and **asks** before looking for them
([People](../reference-people.md#during-the-audit-audit---people)). Ctrl+C stops between two
photos and keeps what is done: the next run goes on.

## 2. Find the faces and name them

`people` needs the cache (where the audits listed your photos), the folder of `config.toml`
(`/config`, where the names are saved) and the port of its page, all three given by `mh`:

```powershell
mh people
```

<details>
<summary>Without <code>mh</code>: the full command</summary>

```powershell
docker run --rm -it -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene people
```

</details>

With WSL or Linux:

```bash
mh people
```

<details>
<summary>Without <code>mh</code>: the full command</summary>

```bash
docker run --rm -it -p 127.0.0.1:8088:8088 \
  -v "/mnt/c/Photos:/data/c/Photos:ro" \
  -v media-hygiene-cache:/cache \
  -v "$HOME/media-hygiene/config:/config" \
  cavo789/media-hygiene people
```

</details>

It analyses the photos not seen yet, groups the faces that look alike (probably one person per
group) and prints the address of the page, `http://127.0.0.1:8088/`: Ctrl+click it.

On the page, the largest groups come first. **Type a name** on a group and press Enter; the name
is written into `config.toml`, then read back from the file and shown at the top of the page
("Saved in config.toml, read back: Chloé, 58 confirmed faces."). The keyboard is enough:

- the same person split in two groups (a child at 3 and at 12): pick both with `x`, name them
  at once, or give the second one the same name;
- a wrong face in a group: × on it, it is never given this name again;
- strangers, posters, statues: `i` ignores the group;
- "Chloé?" is a suggestion: `y` confirms it. A suggestion never counts until you confirm it.

Naming the ten largest groups is often enough: the other faces get the name of the nearest
confirmed face when they look alike enough. Ctrl+C in the terminal stops the page. The next
`people` prints who is named, and in how many photos:

```text
✅ Named: Chloé: 412 photos, Manon: 236 photos.
```

Details of the page and its settings: [People](../reference-people.md#name-the-groups).

## 3. Write the rule

In `config.toml`, add a `person` rule ([step 6](06-write-down-what-you-know.md#people)), one
per person to file:

```toml
[[classify.rules]]
name = "With Chloé"
match = "person"
names = ["Chloé"]
category = "People/Chloé"
```

- An **event** (photos taken close together, [step 4](04-classify.md#read-the-result)) goes to
  the rule when at least 10 % of its files show her: she may be the one taking the pictures.
  `min_share = 30` keeps only the events where she is often seen. A photo outside any event
  goes when it shows her.
- `names = ["Chloé", "Manon"]`: the events with either of them; add `all = true` for those
  with both.
- The names are those of the page; case and accents do not matter (`chloe` is `Chloé`).
- **Place it below the rules you are surer of** (your folders, dates, places): the rules are
  read in order, the first sure one decides. Someone on most of your events, above them, would
  take most of the collection, like a "Family" category.

## 4. Classify, look, sort

Then the same commands as steps [4](04-classify.md), [5](05-review-the-proposal.md) and
[7](07-sort.md): `mh classify`, the workbook (or [`mh review-sort`](11-name-events-in-the-browser.md)),
then `mh sort`.

What to check:

- the *Why* table of `classify` has a line **With Chloé**, with the number of files the rule
  decided; the *Reason* column of the workbook names it for each file, and `review-sort` shows
  it under *Proposed*;
- the rule is listed after *Rules that decided nothing*? Its events were decided by a rule
  above it, or nobody named is on enough of their photos: move it up, or lower `min_share`;
- a name nobody has stops `classify` before anything is read, and says who is named:

```text
❌ Rule 'With Chloé': nobody is named "Manon" in [[people.person]]. Named: Chloé.
💡 Name their group on the 'people' page first, or correct the names of the rule in config.toml.
```

The proposal is a proposal: an event wrongly given to Chloé is corrected in the workbook like
any other ([step 5](05-review-the-proposal.md)).

## Undo

- **A sort**: `mh undo`, as in [step 7](07-sort.md): each file goes back where it was.
- **A rule**: delete it from `config.toml` and run `classify` again; nothing moved before
  `sort`.
- **A name**: on the page, × takes a face out of a person, and a group can be named again. The
  names are plain text in `config.toml`: you may also edit or delete a `[[people.person]]`
  table by hand.

## Forget the faces

```powershell
mh people --forget
```

<details>
<summary>Without <code>mh</code>: the full command</summary>

```powershell
docker run --rm -it -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene people --forget
```

</details>

Every face is deleted from the cache, which is then read again to show that none is left. It
then asks whether the names of `config.toml` go too, and reads the file back to show it. Your
photos and your sorted folders are not touched. Why faces deserve this care:
[your privacy](../reference-people.md#your-privacy).

---

← [9. Places and trips from the GPS](09-places-from-gps.md) · [Documentation](../README.md) · Next: **[11. Name the events in your browser](11-name-events-in-the-browser.md)** →
