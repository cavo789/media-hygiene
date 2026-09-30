# 13. A second opinion

[Documentation](../README.md) › Cleaning, step 13 of 13 · 🇫🇷 [Français](../../fr/clean/13-second-opinion.md)

Before deleting family photos, a second opinion is reassuring.
[Czkawka](https://github.com/qarmin/czkawka) is an independent, open-source duplicate finder,
written differently and with another hash function. Two tools written independently rarely make
the same mistake: when they agree, you can clean with confidence.

This step is optional: `clean` never requires it.

## Step 1: audit, with a reports folder

When it finds duplicates, `audit` ends with a *Second opinion* tip and the exact Czkawka command
for your folders: the same `-v` options, the same extensions, the same excluded folders, every
file size. It looks like this (the community image `jlesage/czkawka`, about 500 MB, ships
Czkawka's command-line tool):

```powershell
docker run --rm -v "C:\Photos:/data/c/Photos:ro" -v "D:\Old disk:/data/d/Old disk:ro" `
  -v "$HOME\media-hygiene\reports:/out" `
  jlesage/czkawka:v26.09.2 czkawka_cli dup -d /data -m 1 -W -N -C /out/czkawka.json `
  -x 3g2,3gp,arw,avi,avif,bmp,cr2,cr3,dng,flv,gif,heic,heif,jpe,jpeg,jpg,m2ts,m4v,mkv,mov,mp4,mpeg,mpg,mts,nef,orf,pef,png,raf,rw2,srw,tif,tiff,ts,webm,webp,wmv
```

## Step 2: run Czkawka

Copy the command printed by your own audit; where it shows
`<the folder you mount on /reports>`, write your reports folder. Paste it and run it. Czkawka
writes its results, `czkawka.json`, in your reports folder. From WSL, write your folders as `/mnt/c/...` instead of `C:\...`.

## Step 3: compare

Run `crosscheck` with the same options as the audit:

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "D:\Old disk:/data/d/Old disk:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene crosscheck
```

`crosscheck` audits again (quickly, thanks to the cache) and compares the two tools group by
group. After the usual summary:

<!-- capture: crosscheck.txt|re:^Czkawka results|agrees -->
```text
Czkawka results of 2026-09-30 19:11 UTC.
✅ Czkawka agrees: the same 32 extra copies in 20 groups.
```

- *Czkawka agrees: the same N extra copies in G groups*: both tools found exactly the same
  duplicates.
- Or *Czkawka disagrees on N groups*, followed by each group found by one tool only. Look at them
  before cleaning.

Files media-hygiene deliberately leaves out are set aside and counted, not reported as
differences: other file types, excluded or system folders, broken files.

## Where the verdict appears

- In the HTML report of the crosscheck, at the top.
- In every later `clean`, right before its question (*Czkawka results of … UTC*), as a reminder.
- In the clean report:

![The top of a clean report with the note: Czkawka agrees: the same 32 extra copies in 20 groups](../images/clean-report.webp)

It is information only: `clean` never requires it.

## You have seen it all

That is the whole tool. From here on, the [reference pages](../README.md#reference) answer precise
questions: every option, the mount points, what is checked before each deletion.

---

← [12. Decide pair by pair](12-decide-pair-by-pair.md) · [Documentation](../README.md)
