# 10. Name the events in your browser

[Documentation](../README.md) › Sorting, step 10 · 🇫🇷 [Français](../../fr/sort/10-name-events-in-the-browser.md)

The workbook of [step 5](05-review-the-proposal.md) is good for renaming in bulk, not for
*looking* at photos: naming an event means reading the report in one window and typing in the
other. With hundreds of events, that is hundreds of back-and-forths. `review-sort` puts both in
one page of your browser: **one event at a time, its photos, its proposal, and a field to name
it**, all with the keyboard.

It is optional: the workbook alone is enough, and both can be used together. The page never
touches a photo nor the workbook; `sort` ([step 7](07-sort.md)) applies your choices.

## Start the page

Run `classify` first ([step 4](04-classify.md)). Then mount the same folders and the same
reports folder (read-only is enough for the photos: the page only shows them):

```powershell
docker run --rm -it --name media-hygiene-review -p 127.0.0.1::8080 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene review-sort
```

As for [the burst review](../clean/10-review-bursts.md#step-1-start-the-review),
`-p 127.0.0.1::8080` opens the page to your computer only, on a port Docker chooses. The page
reads the workbook of the latest `classify` run, the one `sort` applies; name another one after
the command: `review-sort "C:\Photos triées\reports\20261002-123210-classify\classify.xlsx"`.

```text
✅ Review ready on port 8080: each choice is saved at once in
C:\Users\you\media-hygiene\reports\20261002-123210-classify\sort-decisions.json.
Ctrl+C stops the review.
💡 Its address on your computer: run 'docker port 11f20c1a9952 8080' in another
terminal, then open http://<that address> in your browser.
```

In another window, `docker port media-hygiene-review 8080` gives the address to open, such as
`http://127.0.0.1:49153`.

## Read the page

The events come **in the order of the Events sheet**: the ones still to decide first, the largest
first. The page opens on the first one still to decide (or where you stopped). For each event:

- **at the top**: its name (or its dates), its number of files and how many are still to check or
  to sort, and the share of the work naming the events up to this one covers;
- **From**: the folders its photos come from;
- **Proposed**: the folder `classify` proposes, its band and why;
- **Workbook**: what the Events sheet says of it, if you typed something there;
- **Chosen here**: your choice in the page;
- **the photos**, in date order, each with its date. A photo whose proposed folder differs from
  the event's shows it (→ …); one you sent elsewhere is framed in green; 🔒 marks a file left as
  it is (protected or `leave` folder), which no choice moves.

The **Name** field is the event's name, as in the Events sheet: it becomes its folder unless you
give a **Category**. The category field is filled with the proposal and completes from the
categories already used.

## The keys

| Key | What it does |
|---|---|
| <kbd>Enter</kbd> | Accept the name and category, then go to the next event still to decide. |
| <kbd>N</kbd> / <kbd>P</kbd> (or Page Down / Page Up) | Next or previous event, without deciding. |
| <kbd>U</kbd> | Next event still to decide. |
| <kbd>E</kbd> / <kbd>C</kbd> | Type in the name / the category field; <kbd>Esc</kbd> leaves it. |
| <kbd>Shift</kbd>+<kbd>S</kbd> | Leave the whole event where it is ("(stay where it is)"). |
| <kbd>←</kbd> <kbd>→</kbd> | Move between the photos. |
| <kbd>Space</kbd> | Select the photo (or click it). |
| <kbd>O</kbd> | Send the selected photos (else the current one) to another category: type it, <kbd>Enter</kbd>. |
| <kbd>S</kbd> | Leave the selected photos (else the current one) where they are. |
| <kbd>Delete</kbd> | Take back the choice made here: of the selected photos, else of the event. The workbook decides again. |
| <kbd>Z</kbd> | Enlarge the current photo; <kbd>Esc</kbd> closes it. |

A photo sent to another category gets the folder the layout gives that category, as if you had
typed it in its **Final folder** cell: `2016/Best of` with `layout = "{year}/{category}"`.

## Where your choices go

Each choice is saved at once in `sort-decisions.json`, **next to `plan.json`** in the folder of
the `classify` run. The workbook is never changed (Excel may have it open). Stop the page with
<kbd>Ctrl</kbd>+<kbd>C</kbd>, start it again: it resumes.

```text
✅ Review stopped — events chosen: 37, photos chosen one by one: 12.
Your choices are in C:\Users\you\media-hygiene\reports\20261002-123210-classify\sort-decisions.json.
```

`sort` reads both, the page's choices **on top of** the workbook, and says so:

```text
12 edits read; workbook saved on 2 October 2026 at 14:32.
49 choices of the review page applied on top of the workbook (3 replacing a workbook edit, 0 the
same in both).
```

You may keep editing the workbook: one source of truth, the plan, and never a silent conflict.
Each choice of the page remembers what the workbook said of that event or file when you made it:

- **the workbook still says the same**: your choice in the page is the newer one, it wins;
- **the workbook says what you chose**: nothing to settle;
- **the workbook was changed since, on the same event or file, to something else**: nobody can
  tell which one you meant. `sort` refuses to move anything and lists them, with both values;
  the page shows them in red. Choose again in the page (it shows both), or press
  <kbd>Delete</kbd> there to let the workbook decide, or set the workbook cell back.

The other rules of [step 5](05-review-the-proposal.md#the-workbook-edit-the-yellow-cells) still
hold: the most precise choice wins (a file, else its event, else its category), and companions
(a Live Photo, a RAW file and its JPEG) follow one folder.

**Run `classify` again** and your choices of the page are carried over like your edits
([step 5](05-review-the-proposal.md#improve-the-proposal-without-losing-your-work)): they land in
the yellow cells of the new workbook, and the new run starts with an empty
`sort-decisions.json`. A choice the workbook contradicts since is not carried: the workbook's
value is, and the page's is listed among the edits left behind.

---

← [9. Places and trips from the GPS](09-places-from-gps.md) · [Documentation](../README.md) · Next: **[11. Albums](11-albums.md)** →
