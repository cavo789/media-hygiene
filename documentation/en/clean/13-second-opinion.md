# 13. A second opinion

[Documentation](../README.md) › Cleaning, step 13 of 15 · 🇫🇷 [Français](../../fr/clean/13-second-opinion.md)

Before deleting family photos, a second opinion is reassuring.
[Czkawka](https://github.com/qarmin/czkawka) is an independent, open-source duplicate finder,
written differently and with another hash function. Two tools written independently rarely make
the same mistake: when they agree, you can clean with confidence.

This step is optional: `clean` never requires it.

## Run `crosscheck`

With the same folders as the audit (`mh` mounts them):

```powershell
mh crosscheck
```

<details>
<summary>Without <code>mh</code>: the full command</summary>

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "D:\Old disk:/data/d/Old disk:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene crosscheck
```

</details>

Czkawka ships in the image: nothing else to install, nothing to paste. `crosscheck` audits again
(quickly, thanks to the cache), then runs Czkawka on the same folders: the same extensions, the
same excluded folders, every file size. Czkawka only reads, and shows its own messages. On tens of
thousands of photos, allow a few minutes the first time; with `/cache`, it keeps its own cache
there and the next runs only read what changed (`--fresh` reads everything again). Its results,
`czkawka.json`, go to your reports folder.

<details>
<summary>Prefer to run Czkawka yourself?</summary>

`crosscheck --print-command` does not run Czkawka: it prints the command that runs it in its own
image (the community image `jlesage/czkawka`, about 500 MB), with your folders. Where it shows
`<the folder you mount on /reports>`, write your reports folder. It looks like this:

```powershell
docker run --rm -it -v "C:\Photos:/data/c/Photos:ro" -v "D:\Old disk:/data/d/Old disk:ro" `
  -v "$HOME\media-hygiene\reports:/out" `
  jlesage/czkawka:v26.09.2 czkawka_cli dup -d /data -m 1 -W -N -C /out/czkawka.json `
  -x 3g2,3gp,arw,avi,avif,bmp,cr2,cr3,dng,flv,gif,heic,heif,jpe,jpeg,jpg,m2ts,m4v,mkv,mov,mp4,mpeg,mpg,mts,nef,orf,pef,png,raf,rw2,srw,tif,tiff,ts,webm,webp,wmv
```

From WSL, write your folders as `/mnt/c/...` instead of `C:\...`. Once it has run,
`crosscheck --print-command` compares its results.

</details>

## Read the verdict

After the usual summary and Czkawka's run, the two tools are compared group by group:

<!-- capture: crosscheck.txt|re:^Czkawka results|agrees -->
```text
Czkawka results of 2026-10-25 08:47 UTC.
✅ Czkawka agrees: the same 32 extra copies in 20 groups.
```

- *Czkawka agrees: the same N extra copies in G groups*: both tools found exactly the same
  duplicates.
- Or *Czkawka disagrees on N groups*, followed by each group found by one tool only. Look at them
  before cleaning.

Files media-hygiene deliberately leaves out are not compared, and counted, not reported as
differences: other file types, excluded or system folders (recycle bin, thumbnails), broken files.
Nothing to do about them. The folders never analysed are named, those holding the most files first:
you see at once where Czkawka looked that media-hygiene does not.

If photos were moved or deleted since Czkawka ran (by a `clean`, for instance), its results are out
of date: a later `audit` or `clean` ignores them, and the message gives the two ways out. Either run
`crosscheck` again, or delete the `czkawka.json` file it names (in your reports folder) if you no
longer want a second opinion.

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

← [12. Decide pair by pair](12-decide-pair-by-pair.md) · [Documentation](../README.md) · Next: **[14. Unwanted photos](14-unwanted-photos.md)** →
