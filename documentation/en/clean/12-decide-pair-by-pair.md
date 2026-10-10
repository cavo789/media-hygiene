# 12. Decide pair by pair

[Documentation](../README.md) › Cleaning, step 12 of 13 · 🇫🇷 [Français](../../fr/clean/12-decide-pair-by-pair.md)

[`--prefer`](05-choose-the-kept-copy.md) changes the choice for a whole folder, everywhere. Sometimes
you only disagree with one pair: keep the other side, or leave that pair alone. The audit report
lets you decide pair by pair, with a click.

## Step 1: choose in the report

In the *Folder pairs* table of an **audit** report, each pair has a *Your decision* list:

| Choice | What `clean` will do with that pair |
|---|---|
| As planned | Keep the copies of the first folder, set those of the second one aside. |
| Swap the folders | Keep the copies of the **second** folder, set those of the first one aside. |
| Leave alone | Touch nothing of that pair. |

Here, the videos are left alone and the `Old phone` pair is swapped:

![The folder pairs of the report, with Leave alone chosen for C:\Photos\Videos and Swap the folders for C:\Photos\Old phone; the button below reads Download decisions.json (2)](../images/report-pairs.webp)

Your browser remembers the choices, even if you close the page. *Swap the folders* is not
offered for copies inside one folder: there is nothing to swap.

## Step 2: download the file

Click **Download decisions.json**; the number between brackets counts your decisions. Save the
file in your reports folder (`C:\Users\<you>\media-hygiene\reports`), next to `index.html`.

## Step 3: clean with your decisions

Run your `clean` command of [step 8](08-clean.md) with `--decisions`: alone, it reads
`decisions.json` from the reports folder (another file: `--decisions other.json`):

```powershell
cavo789/media-hygiene clean --decisions
```

(with the same `docker run … -v …` part as in step 8)

The page itself never deletes anything. `clean` audits again, applies your decisions, shows the
folder pairs that result, and asks before cleaning, with every safeguard: byte comparison, journal,
`undo`. Once the clean is done, the file is archived as `decisions.applied-<run>.json`, next to
itself: after an `undo`, `--decisions` with that name applies it again.

## When the file is refused

To stay safe, `clean` refuses the file rather than guessing when:

- other folders are mounted than for the report;
- a decided pair no longer exists (files changed since the report): audit again, decide again;
- a swap would set aside the copies of a protected folder.

## One file for everything

The same `decisions.json` can hold the folder pairs, the burst shots of
[step 10](10-review-bursts.md) **and** the near-duplicate groups of
[step 11](11-near-duplicates.md#decide-in-your-browser-review---near): `review` and
`review --near` keep what is already in the file, and one `clean --tier near --decisions` applies
all three.

---

← [11. Near duplicates](11-near-duplicates.md) · [Documentation](../README.md) · Next: **[13. A second opinion](13-second-opinion.md)** →
