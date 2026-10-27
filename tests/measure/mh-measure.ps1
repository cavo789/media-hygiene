# mh-measure.ps1 - the measurements only the maintainer's Windows + Docker Desktop can give.
#
# Runs, one after the other, the measurements the PARTIAL TODOs wait for, and writes the lines
# that matter to one text file Claude reads afterwards (from the devcontainer, through a
# read-only mount of C:\): %TEMP%\mh-measure-results\measures-<stamp>.txt, the 30 latest kept.
# Nothing of the script's own is left in $HOME\media-hygiene: it holds only what mh keeps. Windows PowerShell 5.1, ASCII only (an accented byte breaks the
# console code page, TODO 0098).
#
#   1. a first audit of a test folder with duplicates, fresh cache   (0148: checks, fingerprints;
#      0159: its estimate of the checks, against their time per step)
#   2. the same audit again, nothing changed                         (warm audit, 0159 line)
#   3. one photo added to the big flat folder, audit                 (0153: listing)
#   4. a folder renamed, audit                                        (0147: files followed)
#   5. clean, then undo, then audit                                   (0149 clean time, 0156)
#      clean --delete, then undo: no move, against 5a                 (0150: share of the moves)
#      clean, then undo, one file at a time ([clean] workers = 1)     (0149: K = 1 against 5a/5b)
#   6. C:\Photos read-only with your usual cache, audit twice         (0147 one-time pass, 0152)
#      people --sample 200 on it: seconds per photo, faces            (0058; adds the faces of
#      those 200 photos and the two face models, 39 MB, to that cache)
#   7. classify, sort (NTFS file ids before/after), undo of the test folder  (0138: moves on NTFS)
#      sort, then undo, one file at a time ([clean] workers = 1)       (0163: 4 at once against 7b)
#   8. each file operation of a sort by link and its undo, alone           (0138: what is refused)
#   9. the mh launcher around docker run, in the old console (conhost)    (0184 accents, 0179 awake,
#      0185 title and sound, 0178 browser): asks what you heard and saw; the awake check
#      (powercfg /requests) needs an administrator PowerShell
#  10. mh open, mh shortcut, mh explorer (right-click a folder, then the empty space of an
#      open folder), each read back   (0175, 0180, 0181, 0188): asks what you saw; your own
#      Media Hygiene shortcut or entries are put back after; a page window closed with its X,
#      the next page stopping what it left running                              (0250);
#      the start without -ExecutionPolicy Bypass, any antivirus alert, the same right-click
#      with mh.ps1 under %USERPROFILE%\media-hygiene (the real place) against -Work  (0257);
#      the page names the folder clicked, Run says which window runs the step     (0258);
#      another program listening on 8088: mh review names it, the probe timed     (0253);
#      -Only 10f runs this port check alone, without the questions above
#  11. mh folders add / remove (mh rewrites its own file), a new terminal audits the folder added;
#      mh update: with the local image it says there is nothing to pull; then, if you agree, the
#      local image tagged cavo789/media-hygiene plays an older one and mh update pulls the
#      published one, writes mh again and says both versions                (0176, 0177);
#      mh folders add alone: the folder window, a folder chosen, then cancelled       (0201);
#      mh folders add --backup (on -OtherDrive when given): its mount line, mh audit's two
#      lines, mh clean leaving it whole, Docker refusing a write in it          (0205);
#      its drive's type and its mount in a container before and after mh: a USB stick shared
#      by mh with Docker Desktop's VM, unshared after each command; on a stick, asks whether
#      Windows then lets you eject it safely                                    (0252);
#      from WSL: the interop, /mnt/x of the stick, what a container sees before and after a
#      mount -t drvfs in the distribution (the line mh.sh says)           (0254, 0259)
#  12. clean of photos on another drive (-OtherDrive, else the first drive but C: with 2 GB
#      free), quarantine on C:: the line before the question names both drives, the size and
#      C:'s free space (checked against Windows'); quarantine on that drive: no line   (0182)
#  13. 1 GB set aside from another drive (-OtherDrive, else the first drive but C: with 3 GB
#      free): to the quarantine on C: (copy E: -> C:), then to that drive's own quarantine
#      /quarantine/x (copy E: -> E:): wall time of each clean and undo; then undo without
#      the drive's quarantine mounted must refuse, naming the drive                  (0183)
#  14. mh menu by hand, old console then your usual one: colours, columns, a number +
#      Enter, Ctrl+C; then mh alone: the home page, a step run from it, the page back,
#      a review page in the same tab and back to its space, the tabs counted   (0172, 0210, 0280)
#  15. the launcher line of the guide (launcher --photos), mh audit, the hour in mh history
#      against this PC's clock, mh --photos on -OtherDrive, a folder not plugged in   (0173)
#  16. asks you to quit Docker Desktop: records docker run's exact message and exit code; then
#      mh starts it by itself: the check of mh alone, timed, and mh audit after another quit:
#      the "type the command again" line, the audit typed again              (0174, 0200)
#  17. mh.ps1 kept in memory, written in variants (without / with only: keep-awake, browser,
#      shortcut, right-click): which one the antivirus refuses   (Avast IDP.Generic, 2026-10-16)
#  18. OneDrive cloud-only files played by a folder whose files are marked offline, OneDrive
#      pointed at it for this window only: mh audit says the line and asks (N, then y, then
#      not again); mh folders add says the line; PowerShell 5.1's own run of the check  (0199)
#  19. a phone plugged in over USB (MTP), read through Shell.Application: the devices of This
#      PC, DCIM, listing time and properties, the 20 most recent files copied once (CopyHere
#      only: nothing is written to the phone), speed and dates of the copies   (0218, for 0219);
#      then, if you agree, mh phone end to end: every file of DCIM copied, again (nothing
#      copied), then the cable pulled out during a copy, plugged in again       (0219);
#      then, if you agree, ONE synthetic test file written to the phone and deleted (InvokeVerb,
#      InvokeVerbEx, MoveHere), DCIM counted before and after, the gallery's trash; the 20 files
#      copied into an empty folder and their SHA-256: MB/s of each         (0247, for 0248)
#  20. image embeddings: -Sample photos of C:\Photos (read-only), your searches, three models on
#      -Cpus CPUs; pages to tick, seconds per photo, RAM; downloads 2.5 GB of models once (0220)
#  21. the Synology NAS (-Nas, -NasShare, -NasUser), read-only: its ports; SMB from Windows (a
#      drive mapped, a listing, 20 photos read), SMB from Docker (that drive letter, then a CIFS
#      volume), FTP from Docker (FEAT, MLSD, partial and whole reads); the password asked once,
#      never logged; nothing written on the NAS                          (0246, for 0245)
#  22. a folder pair keeping both names: audit, the pair offered "link" in the report, clean
#      --decisions, fsutil hardlink list of each copy, C:'s free space before/after; asks what
#      Explorer shows, then for one photo edited and saved in the Photos app: does its other
#      name change too; undo: one name each again                         (0213)
#  23. the home page opened by your own mh (your real folders): GET / and GET /api/state from
#      Windows, each part of the state timed inside its container (docker exec), the DNS of
#      Docker Hub from it, the files of the tool folders; then an empty docker run, the price
#      of each step's round trip; nothing written                          (0277)
#  24. C:\Photos read-only with your usual cache: tags --meaning (downloads the CLIP model,
#      894 MB, into that cache once, then a vector per photo: seconds per photo on your PC),
#      then a search by meaning, timed (text model loaded)                  (0263)
#  25. mh.ps1 loaded, written again, then mh version: the line saying the file changed since the
#      window loaded it (expected once written again, absent after loading it again and
#      when the file is removed); one stat, timed                              (0276)
#  26. your own mh (the image of this branch): mh shortcut, then the Desktop icon: the window
#      minimised and its keep-open line, a console step from the page (window forward, button
#      flashing with bellStyle taskbar, or nothing; minimised, then normal), the bold line, the window
#      closed then the stop shown by the page; asks what you saw            (0284, 0285)
#  27. mh push to the NAS (-Nas, -NasTarget: a shared folder of its own, created in DSM first):
#      robocopy of 20 photos into <target>\mh-measure-test with /MT:1 then /MT:8 (MB/s of NAS
#      writes), 20 renames there timed, whether a credential-only New-PSDrive lets robocopy in;
#      then in a test mh: mh push twice (the second copies nothing), once stopped by Ctrl+C
#      and typed again, once after a folder renamed (renames only); the test folder removed (0264)
#  28. an mh.ps1 older than its image: a test mh written by -Image, its stamp changed, then
#      removed: mh history says the line naming mh update (expected), mh update of the local
#      build writes it again without a pull, folders read back, the line gone      (0290)
#  29. mh alone (0367; was mh --lan), the home page on a phone of the home Wi-Fi: the address mh finds (timed) and
#      Windows' category of that network; then, in a new window, mh --lan by hand: Windows'
#      firewall prompt, the ports Docker publishes, the QR code and the code on the PC's page,
#      the phone paired by the QR code then by the code, the audit run from the phone, a step
#      refused there, the phone still paired after a step run on the PC, the phone on mobile
#      data (Wi-Fi off) never reaching it                                       (0269)
#  30. mh slideshow --lan, the photos on the TV driven from the phone: a test mh audits the
#      test folder (timed), then, in a new window, mh slideshow --lan by hand: the TV's code
#      on the Chromecast's browser, the phone paired, the TV paired by its code, full screen;
#      the time from a tap on the phone to the photo whole on the TV (Enter pressed twice,
#      5 times "next", 5 times a far thumbnail), bands seen or not, the timer, "do not show",
#      the TV reloaded, the phone asleep; then the same on the TV's own browser     (0291)
#  31. mh slideshow --lan plays the videos: a few phone videos of C:\Photos copied (the smallest
#      .mov and .mp4 found first, plus one HEVC video you name), audited; on the Chromecast's
#      browser: a .mov played (sound or muted, tap -> first frame timed), the show moving on at
#      its end, pause/play during a video, the next photo after it; the HEVC one labelled on the
#      phone, then opened by its address to learn whether the Chromecast plays HEVC; then the
#      TV's own browser: videos passed over, the phone saying why                  (0292)
#  32. mh share: an album of 60 photos of the test folder (albums.json written here), mh share
#      timed, its lines; the originals unchanged; the copies' size per photo and the zip's; GPS
#      in the originals and in the copies (System.Drawing); asks whether the Explorer opened on
#      $HOME\media-hygiene\Shares; the test album removed from it at the end      (0296)
#  33. an album on the phone at home: an album of the test folder's photos (and 2 videos of
#      C:\Photos), then, in a new window, mh --lan by hand: the album list and an album timed
#      from the PC (cold, warm), one phone-sized picture timed and weighed; on the phone: the
#      albums opened from its home page, scroll smoothness, tap -> photo full screen (asked),
#      swipe, a video in place, a photo taken out and added to another album (albums.json read
#      back), another photo's address refused                                  (0297)
#  34. shrink: two of your videos re-encoded by the image's ffmpeg, timed, played    (0303)
#  35. the pages opened from the home page: an empty container, mh menu, what mh search does
#      before its page answers (your cache and config, read-only); the clicks themselves are
#      timed by Chromium in the CI (0366); nothing written                     (0354)
#  36. the home page by hand: three yes/no questions (it opens; a console step runs in the
#      window of mh while the page stays open; Quit then mh again)       (0355, 0366)
#
# The test folder is a copy of a few photos of C:\Photos, made under -Work and removed at the
# end (-Keep to keep it); C:\Photos itself is only read. Build the image from the branch to
# measure first (devcontainer: `build`, or `docker build --tag media-hygiene .`).
#
# Usage (PowerShell, from any folder; once after the download: Unblock-File .\mh-measure.ps1).
# No -ExecutionPolicy Bypass, anywhere: Avast's Behavior Shield flagged a script launching
# conhost -> powershell -ExecutionPolicy Bypass twice (IDP.HELU.PSD11, 2026-10-16); the
# windows of steps 9d and 14 are opened by you, as a user does.
#   .\mh-measure.ps1
#   .\mh-measure.ps1 -Count 3000 -Image media-hygiene
#   .\mh-measure.ps1 -Only 8 -Count 10   (step 8 only)
#   .\mh-measure.ps1 -Only 9 -Count 300  (step 9 only)
#   .\mh-measure.ps1 -Only 10 -Count 20  (step 10 only)
#   .\mh-measure.ps1 -Only 11 -Count 20  (step 11 only)
#   .\mh-measure.ps1 -Only 12 -Count 20 -OtherDrive E:
#   .\mh-measure.ps1 -Only 13 -Count 20 -OtherDrive E:
#   .\mh-measure.ps1 -Only 14,15,16 -Count 20 -OtherDrive E:
#   .\mh-measure.ps1 -Only 17 -Count 5
#   .\mh-measure.ps1 -Only 18 -Count 5
#   .\mh-measure.ps1 -Only 19 -Count 1   (a phone plugged in over USB; -Count 1: the test folder is not used)
#                                         (19l-19o write ONE test file to the phone, after a y, then delete it)
#                                         (19p: mh phone --free on 3 test files written to the phone, after a y)
#                                         (19q: the phone locked then unlocked: what Windows shows of it, read only)
#                                         (19r: 20 test files written to the phone, CopyHere vs MoveHere back, after a y)
#   .\mh-measure.ps1 -Only 20 -Count 1 -Sample 1000 -Cpus 4 -Branch iterate/2026-10-17   (image embeddings)
#   .\mh-measure.ps1 -Only 21 -Count 1 -Nas 192.168.1.2 -NasShare photo -NasUser me   (the NAS, read-only)
#   .\mh-measure.ps1 -Only 22 -Count 3   (a pair keeping both names: hard links, 0213)
#   .\mh-measure.ps1 -Only 23 -Count 1   (the home page of your own mh, timed: 0277)
#   .\mh-measure.ps1 -Only 24 -Count 1   (search by meaning on C:\Photos: 0263)
#   .\mh-measure.ps1 -Only 25 -Count 1   (mh.ps1 written again after loading: 0276)
#   .\mh-measure.ps1 -Only 26 -Count 1   (the shortcut minimised, a console step brought forward: 0284, 0285)
#   .\mh-measure.ps1 -Only 27 -Count 20 -Nas 192.168.1.2 -NasTarget backup_photos -NasUser me   (mh push: 0264)
#   .\mh-measure.ps1 -Only 28 -Count 1   (an mh older than its image, then mh update: 0290)
#   .\mh-measure.ps1 -Only 29 -Count 20   (mh --lan: the home page on a phone of the home Wi-Fi: 0269)
#   .\mh-measure.ps1 -Only 30 -Count 30   (mh slideshow --lan: the photos on the TV, the phone as remote: 0291)
#   .\mh-measure.ps1 -Only 31 -Count 10   (mh slideshow --lan plays the videos on the TV: 0292)
#   .\mh-measure.ps1 -Only 32 -Count 60   (mh share: an album ready to send, sizes and GPS: 0296)
#   .\mh-measure.ps1 -Only 33 -Count 120  (an album on the phone at home, mh --lan: 0297)
#   .\mh-measure.ps1 -Only 34 -Count 1   (shrink: two of your videos re-encoded, timed, played: 0303)
#   .\mh-measure.ps1 -Only 35 -Count 1   (the pages opened from the home page, each phase timed: 0354)
#   .\mh-measure.ps1 -Only 36 -Count 1   (the home page by hand, three yes/no questions: 0355, 0366)

param(
    [string]$Photos = "C:\Photos",
    [string]$Work = (Join-Path $env:TEMP "mh-measure"),
    [int]$Count = 2000,
    [string]$Image = "media-hygiene",
    [string]$Cache = "media-hygiene-cache",
    [switch]$Keep,
    [string]$Only = "",
    [string]$OtherDrive = "",
    [int]$Sample = 1000,
    [int]$Cpus = 4,
    [string]$Branch = "main",
    [string]$Nas = "",
    [string]$NasShare = "photo",
    [string]$NasUser = "",
    [string]$NasTarget = "backup_photos"
)

$ErrorActionPreference = "Stop"
# The tool writes UTF-8 (emoji, table borders): read docker's output as such, not as the
# console code page, which garbles them.
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$stamp = Get-Date -Format "yyyyMMdd-HHmm"
# Next to -Work, not in it: each run empties -Work. $HOME\media-hygiene is mh's, never ours.
$outDir = Join-Path $env:TEMP "mh-measure-results"
$mhHome = Join-Path $HOME "media-hygiene"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
Get-ChildItem -LiteralPath $outDir -File -Filter "measures-*.txt" | Sort-Object Name -Descending | Select-Object -Skip 29 | Remove-Item -Force
$out = Join-Path $outDir "measures-$stamp.txt"
$wanted = 'Time per step|Duration|Report written|moved or renamed|unchanged folder|Reading 128 KB|copies|Error|first time|Next audit|No new or changed|per photo|A full run|faces in|Left out|Source folders removed|will be copied|Not enough room|not mounted|by what|to look at|Downloading the model|files found'

function Log([string]$text) {
    Add-Content -Path $out -Value $text -Encoding UTF8
    Write-Host $text
}

# Each test mh.ps1 dot-sourced below defines global functions (mh, _mh_*): run as
# .\mh-measure.ps1, they stayed in the console after the run, and `mh` then named a removed
# test folder ("phone-library cannot be found", 2026-10-20). Saved here, put back at the end.
$mhBefore = @{}
foreach ($function in @(Get-ChildItem Function: | Where-Object { $_.Name -eq 'mh' -or $_.Name -like '_mh_*' })) { $mhBefore[$function.Name] = $function.ScriptBlock }

function MhRestore {
    foreach ($function in @(Get-ChildItem Function: | Where-Object { $_.Name -eq 'mh' -or $_.Name -like '_mh_*' })) {
        if (-not $mhBefore.ContainsKey($function.Name)) { Remove-Item -Path "Function:\$($function.Name)" -Force }
    }
    foreach ($name in $mhBefore.Keys) { Set-Item -Path "Function:\global:$name" -Value $mhBefore[$name] }
}
trap { MhRestore; break }

function MhLeftovers([string]$part) {
    foreach ($id in @(& docker ps --quiet)) {
        $binds = "$(& docker inspect $id --format '{{json .HostConfig.Binds}}' 2>$null)"
        # Explorer passes the folder as on disk (C:\Temp), -Work as typed (C:\temp): any case.
        if ($binds.IndexOf($Work.Replace('\', '\\'), [StringComparison]::OrdinalIgnoreCase) -lt 0) { continue }
        $name = "$(& docker inspect $id --format '{{.Name}} {{json .Config.Cmd}} {{json .NetworkSettings.Ports}}')"
        Log "   $part. container of this run still running after its window closed: $name; stopped"
        & docker stop $id | Out-Null
    }
}

function Measure-Mh([string]$title, [string[]]$mounts, [string[]]$arguments) {
    Log ""
    Log "== $title"
    $watch = [Diagnostics.Stopwatch]::StartNew()
    $lines = & docker run --rm --env COLUMNS=160 @mounts $Image --locale en --verbosity verbose @arguments 2>&1
    $watch.Stop()
    foreach ($line in $lines) {
        $text = "$line"
        if ($text -match $wanted) { Log ("   " + $text.Trim()) }
    }
    Log ("   wall time: {0:N1} s, exit code {1}" -f $watch.Elapsed.TotalSeconds, $LASTEXITCODE)
}

# -Only "7,8": with -File, PowerShell hands the list over as one string; split it here.
$steps = @($Only -split '[,; ]+' | Where-Object { $_ -ne "" })

# -OtherDrive given but not there (a USB key not plugged in): said once, here; steps 12, 13
# and 15d skip it instead of picking another drive or stopping on Join-Path.
$unplugged = ""
if ($OtherDrive -ne "") {
    $OtherDrive = $OtherDrive.TrimEnd('\')
    if (-not (Test-Path -LiteralPath ($OtherDrive + "\"))) {
        $unplugged = $OtherDrive
        $OtherDrive = ""
        Log "-OtherDrive ${unplugged}: this drive is not accessible (not plugged in?). Steps 12, 13 and 15d skip it: plug it in, then run them again."
    }
}

function Wanted([int]$group) {
    return ($steps.Count -eq 0) -or ($steps -contains "$group")
}

# A USB stick: steps 12 and 13 run docker run by hand on it, which Docker Desktop cannot
# see without the sharing mh does (0252): they need a fixed disk (2026-10-20, a stick gave
# exit code 1 four times, then 2 GB were copied to it for nothing).
function Removable([string]$drive) {
    $volume = Get-Volume -DriveLetter $drive.Substring(0, 1) -ErrorAction SilentlyContinue
    return "$($volume.DriveType)" -eq 'Removable'
}

# NTFS file ids (no administrator rights needed): a file renamed or linked keeps its id, a
# copy gets a new one. That is what proves 0138 (sort moves without copying). Compiled only for
# step 7: an antivirus's behaviour shield may flag C# calling kernel32 (Avast IDP.Generic,
# 2026-10-16), and steps 9+ must show whether the mh.ps1 users get is flagged, not this.
if (Wanted 7) {
Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Runtime.InteropServices;
public static class MhFileId {
    [StructLayout(LayoutKind.Sequential)]
    struct Info {
        public uint Attributes;
        public System.Runtime.InteropServices.ComTypes.FILETIME Created, Accessed, Written;
        public uint Volume, SizeHigh, SizeLow, Links, IndexHigh, IndexLow;
    }
    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool GetFileInformationByHandle(IntPtr handle, out Info info);
    public static string Of(string path) {
        using (FileStream stream = File.Open(path, FileMode.Open, FileAccess.Read,
                FileShare.ReadWrite | FileShare.Delete)) {
            Info info;
            if (!GetFileInformationByHandle(stream.SafeFileHandle.DangerousGetHandle(), out info)) {
                throw new IOException("GetFileInformationByHandle: " + Marshal.GetLastWin32Error());
            }
            return String.Format("{0:x8}{1:x8}", info.IndexHigh, info.IndexLow);
        }
    }
}
'@
}

function FileIds([string]$root) {
    $ids = @{}
    foreach ($file in Get-ChildItem -LiteralPath $root -Recurse -File) {
        $ids[[MhFileId]::Of($file.FullName)] = $file.FullName
    }
    return $ids
}

# --- the test folder: photos copied twice (exact duplicates), one big flat folder --------
$data = Join-Path $Work "data"
$tool = Join-Path $Work "tool"
if (Test-Path $Work) {
    if (-not (Test-Path (Join-Path $Work ".mh-measure"))) {
        throw "$Work exists and was not made by this script: choose another -Work."
    }
    Remove-Item -Recurse -Force $Work
}
foreach ($folder in "data\flat", "data\copies", "tool\journal", "tool\quarantine", "tool\reports") {
    New-Item -ItemType Directory -Force -Path (Join-Path $Work $folder) | Out-Null
}
Set-Content -Path (Join-Path $Work ".mh-measure") -Value "made by mh-measure.ps1"

Log "mh-measure $stamp - image $Image $(docker image inspect $Image --format '{{.Id}}')"
Log "Copying $Count photos of $Photos into $data (twice: exact duplicates)..."
$picked = Get-ChildItem -Path $Photos -Recurse -File -Include *.jpg, *.jpeg |
    Where-Object { $_.FullName -notmatch '\\#recycle\\' } | Select-Object -First $Count
$index = 0
foreach ($photo in $picked) {
    $index++
    $name = "{0:D6}-{1}" -f $index, $photo.Name
    Copy-Item -LiteralPath $photo.FullName -Destination (Join-Path $data "flat\$name")
    Copy-Item -LiteralPath $photo.FullName -Destination (Join-Path $data "copies\$name")
}
$megabytes = ($picked | Measure-Object -Property Length -Sum).Sum * 2 / 1MB
Log ("Test folder: {0} files, {1:N0} MB" -f ($index * 2), $megabytes)

$volume = "mh-measure-cache"
docker volume rm -f $volume | Out-Null
docker volume create $volume | Out-Null
$readOnly = @("-v", "${data}:/data/c/measure:ro", "-v", "${volume}:/cache")
$writable = @(
    "-v", "${data}:/data/c/measure",
    "-v", "${volume}:/cache",
    "-v", "$(Join-Path $tool 'journal'):/journal",
    "-v", "$(Join-Path $tool 'quarantine'):/quarantine",
    "-v", "$(Join-Path $tool 'reports'):/reports"
)

# --- 1-5: the test folder ------------------------------------------------------------------
if (Wanted 1) {
    Measure-Mh "1. first audit, fresh cache (0148)" $readOnly @("audit")
}
if (Wanted 2) {
    Measure-Mh "2. audit again, nothing changed" $readOnly @("audit")
}
if (Wanted 3) {
    Copy-Item -LiteralPath $picked[0].FullName -Destination (Join-Path $data "flat\new-photo.jpg")
    Measure-Mh "3. one photo added to a folder of $Count (0153)" $readOnly @("audit")
}
if (Wanted 4) {
    Rename-Item -LiteralPath (Join-Path $data "copies") -NewName "copies renamed"
    Measure-Mh "4. a folder renamed in Explorer (0147)" $readOnly @("audit")
}
if (Wanted 5) {
    Measure-Mh "5a. clean of the duplicates (0149)" $writable @("clean", "--yes")
    Measure-Mh "5b. undo of that clean" $writable @("undo", "--yes")
    Measure-Mh "5c. audit after undo: nothing decoded again (0156)" $readOnly @("audit")
    Measure-Mh "5d. clean --delete: no move, against 5a (0150)" $writable @("clean", "--yes", "--delete")
    Measure-Mh "5e. undo of that clean: copies rebuilt from the kept files" $writable @("undo", "--yes")
    $oneAtATime = @("--env", "MEDIA_HYGIENE_CLEAN__WORKERS=1") + $writable
    Measure-Mh "5f. clean, one file at a time: against 5a (0149)" $oneAtATime @("clean", "--yes")
    Measure-Mh "5g. undo, one file at a time: against 5b (0149)" $oneAtATime @("undo", "--yes")
}

# --- 6: the real collection, read-only, with the usual cache -------------------------------
$real = @("-v", "${Photos}:/data/c/Photos:ro", "-v", "${Cache}:/cache")
if (Wanted 6) {
    Measure-Mh "6a. C:\Photos, first audit with this image (one-time 128 KB pass, 0147)" $real @("audit")
    Measure-Mh "6b. C:\Photos, warm audit (near duplicates, 0152)" $real @("audit")
    Measure-Mh "6c. C:\Photos, people --sample 200 (0058)" $real @("people", "--sample", "200")
}

# --- 7: sort on the test folder: moves within one NTFS mount (0138) --------------------------
# 7b and 7d print 'Time per step' (0170): counts, moves, cache update, move checks, manifest.
if (Wanted 7) {
    Measure-Mh "7a. classify the test folder" $writable @("classify")
    $before = FileIds $data
    Measure-Mh "7b. sort, the default proposal (0138: renamed or linked, not copied)" $writable @("sort", "--yes")
    $after = FileIds $data
    $kept = @($after.Keys | Where-Object { $before.ContainsKey($_) }).Count
    $moved = @($after.Keys | Where-Object { $before.ContainsKey($_) -and $before[$_] -ne $after[$_] }).Count
    Log ("   NTFS ids: {0} of {1} files kept their id ({2} at a new path: renamed or linked), {3} new ids (copied)" -f $kept, $after.Count, $moved, ($after.Count - $kept))
    Measure-Mh "7c. undo of that sort" $writable @("undo", "--yes")
    $back = FileIds $data
    $same = @($back.Keys | Where-Object { $before.ContainsKey($_) -and $before[$_] -eq $back[$_] }).Count
    Log ("   NTFS ids after undo: {0} of {1} files back at their first path with their first id" -f $same, $back.Count)
    $oneByOne = @("--env", "MEDIA_HYGIENE_CLEAN__WORKERS=1") + $writable
    Measure-Mh "7d. sort, one file at a time: against 7b, 4 at once (0163)" $oneByOne @("sort", "--yes")
    Measure-Mh "7e. undo of that sort" $writable @("undo", "--yes")
}

# --- 8: which file operations Docker Desktop's NTFS mount allows (0138: undo after a link) ----
# Each line: probe <scenario> <operation> ok|<errno name>. Same sequence as a sort by link,
# then its undo: renameat2(RENAME_NOREPLACE), link, unlink, rmdir, mkdir, then the way back.
if (Wanted 8) {
    $probeDir = Join-Path $tool "probe"
    New-Item -ItemType Directory -Force -Path $probeDir | Out-Null
    Set-Content -Path (Join-Path $probeDir "probe.py") -Encoding Ascii -Value @'
import ctypes, errno, os, time

ROOT = '/data/c/measure/probe'
LIBC = ctypes.CDLL(None, use_errno=True)


def renameat2(source, target):
    if LIBC.renameat2(-100, source.encode(), -100, target.encode(), 1) != 0:
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code))


def create(path):
    with open(path, 'xb') as stream:
        stream.write(b'x' * 1000)


def attempt(label, action):
    try:
        action()
        print('probe', label, 'ok', flush=True)
    except OSError as exc:
        print('probe', label, errno.errorcode.get(exc.errno, exc.errno), flush=True)


def scenario(name, linked, remove_folder, pause):
    base = os.path.join(ROOT, name)
    old_dir, new_dir = os.path.join(base, 'from'), os.path.join(base, 'to')
    os.makedirs(old_dir)
    os.makedirs(new_dir)
    old, new = os.path.join(old_dir, 'a.jpg'), os.path.join(new_dir, 'a.jpg')
    if linked:
        create(old)
        attempt(name + ' sort-renameat2', lambda: renameat2(old, new))
        attempt(name + ' sort-link', lambda: os.link(old, new))
        attempt(name + ' sort-unlink', lambda: os.unlink(old))
    else:
        create(new)
    if remove_folder:
        attempt(name + ' sort-rmdir', lambda: os.rmdir(old_dir))
        attempt(name + ' undo-mkdir', lambda: os.mkdir(old_dir))
    time.sleep(pause)
    attempt(name + ' undo-renameat2', lambda: renameat2(new, old))
    attempt(name + ' undo-link', lambda: os.link(new, old))
    if os.path.lexists(old):
        attempt(name + ' undo-unlink-new', lambda: os.unlink(new))
    else:
        attempt(name + ' undo-create', lambda: create(old))
        attempt(name + ' undo-remove-created', lambda: os.unlink(old))
        attempt(name + ' undo-rename', lambda: os.rename(new, old))


def times(label, path):
    info = os.stat(path)
    print('probe', label, 'owner', info.st_uid, 'me', os.getuid(), flush=True)
    attempt(label + ' utime', lambda: os.utime(path, ns=(info.st_mtime_ns, info.st_mtime_ns)))


os.makedirs(ROOT)
create(os.path.join(ROOT, 'made-here.jpg'))
times('made-by-the-tool', os.path.join(ROOT, 'made-here.jpg'))
times('made-by-windows', os.path.join('/data/c/measure/flat', sorted(os.listdir('/data/c/measure/flat'))[0]))
scenario('fresh', linked=False, remove_folder=False, pause=0)
scenario('linked', linked=True, remove_folder=False, pause=0)
scenario('linked-rmdir', linked=True, remove_folder=True, pause=0)
scenario('linked-rmdir-wait', linked=True, remove_folder=True, pause=5)
'@
    Log ""
    Log "== 8. file operations on the NTFS mount (0138: undo after a move by link)"
    $probeRun = @("-v", "${data}:/data/c/measure", "-v", "${probeDir}:/probe:ro")
    $lines = & docker run --rm @probeRun --entrypoint python $Image /probe/probe.py 2>&1
    foreach ($line in $lines) { Log ("   " + "$line".Trim()) }
}

# --- 9: the mh launcher around docker run (0184, 0179, 0185, 0178) ---------------------------
# mh is written by the image under test, French, with the tool folders of the test folder.
if (Wanted 9) {
    $mhDir = Join-Path $tool "mh"
    New-Item -ItemType Directory -Force -Path $mhDir, (Join-Path $tool "config") | Out-Null
    $mhFile = Join-Path $mhDir "mh.ps1"
    $toolMounts = @(
        "-v", "${volume}:/cache",
        "-v", "$(Join-Path $tool 'config'):/config",
        "-v", "$(Join-Path $tool 'journal'):/journal",
        "-v", "$(Join-Path $tool 'quarantine'):/quarantine",
        "-v", "$(Join-Path $tool 'reports'):/reports"
    )
    & docker run --rm -e "MEDIA_HYGIENE_IMAGE=$Image" @toolMounts $Image --locale fr launcher --photos $data > $mhFile
    $result = Join-Path $mhDir "probe.txt"
    $probe = Join-Path $mhDir "probe.ps1"
    Set-Content -Path $probe -Encoding Ascii -Value @'
param([string]$mh, [string]$result)
function Note([string]$text) { Add-Content -Path $result -Value $text -Encoding UTF8 }
Note ("   9a. console code page before mh: " + [Console]::OutputEncoding.CodePage)
. $mh
# The menu asks for a step number since 0210: answered here with one it does not know, so it
# lists the steps and runs none.
function global:Read-Host { 'x' }
$menu = @(mh menu 2>&1 | ForEach-Object { "$_" })
Remove-Item -Path Function:\Read-Host
$text = $menu -join "`n"
Note ("   9a. French menu holds accented letters: " + ($text -match '[\u00E0-\u00FC]') + "; an e-acute garbled as in code page 850: " + ($text -match '\u251C\u00AE'))
Note ("   9a. its first line: " + ($menu | Where-Object { "$_".Trim() } | Select-Object -First 1))
Note ("   9a. console code page after mh: " + [Console]::OutputEncoding.CodePage)
$Host.UI.RawUI.WindowTitle = "mh-measure"
mh audit
Note ("   9c. exit code " + $LASTEXITCODE + ", window title after mh audit: " + $Host.UI.RawUI.WindowTitle)
mh history | Out-Null
Note ("   9c. window title at the next mh call: " + $Host.UI.RawUI.WindowTitle)
'@
    Log ""
    Log "== 9. the mh launcher in the old console (0184, 0179, 0185, 0178)"
    Remove-Item -Force -ErrorAction SilentlyContinue $result
    $arguments = "powershell.exe -NoProfile -File `"$probe`" -mh `"$mhFile`" -result `"$result`""
    $child = Start-Process -FilePath conhost.exe -ArgumentList $arguments -PassThru
    $admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    $awake = $false
    while (-not $child.HasExited) {
        if ($admin -and ((powercfg /requests) -join " ") -match 'powershell') { $awake = $true }
        Start-Sleep -Seconds 1
    }
    if (Test-Path $result) { Get-Content -Path $result -Encoding UTF8 | ForEach-Object { Log $_ } }
    if ($admin) {
        $after = ((powercfg /requests) -join " ") -match 'powershell'
        Log ("   9b. awake request of powershell.exe during mh audit: {0}; still there after: {1}" -f $awake, $after)
    } else {
        Log "   9b. skipped: powercfg /requests needs an administrator PowerShell (run -Only 9 from one)"
    }
    $heard = Read-Host "9c. Did you hear a sound when mh audit ended in the other window? (y/n)"
    Log "   9c. sound heard at the end: $heard"
    Write-Host "9d. Open a console yourself: Win+R, type conhost.exe powershell.exe, Enter. In it, type:"
    Write-Host "    . '$mhFile'; mh review"
    $opened = Read-Host "9d. A window runs mh review: did your browser open on the review page by itself? (y/n; n/a if it said there is nothing to review)"
    Log "   9d. browser opened by mh review: $opened"
    Write-Host "Press Ctrl+C in the review window, then close it."
}

# --- 10: what mh does by itself, without docker run (0175, 0180, 0181) ----------------------
# mh open, mh shortcut, mh explorer: each one read back here; a Media Hygiene shortcut or
# right-click entry you already had is saved first and put back at the end.
# -Only 10f: the port check alone (0253), without the questions of 10a-10e.
$portOnly = $steps -contains '10f'
if ((Wanted 10) -or $portOnly) {
    $ErrorActionPreference = "Continue"
    $mhDir = Join-Path $tool "mh"
    New-Item -ItemType Directory -Force -Path $mhDir, (Join-Path $tool "config") | Out-Null
    $mhFile = Join-Path $mhDir "mh.ps1"
    $toolMounts = @(
        "-v", "${volume}:/cache",
        "-v", "$(Join-Path $tool 'config'):/config",
        "-v", "$(Join-Path $tool 'journal'):/journal",
        "-v", "$(Join-Path $tool 'quarantine'):/quarantine",
        "-v", "$(Join-Path $tool 'reports'):/reports"
    )
    & docker run --rm -e "MEDIA_HYGIENE_IMAGE=$Image" @toolMounts $Image launcher --photos $data > $mhFile
    . $mhFile
    Log ""
    Log "== 10. what mh does by itself (0175 open, 0180 shortcut, 0181 and 0188 explorer)"
    if (-not $portOnly) {
        $index = Join-Path $tool "reports\index.html"
        if (-not (Test-Path $index)) {
            $said = @(mh open 6>&1 | ForEach-Object { "$_" })
            Log ("   10a. mh open before any report says: " + ($said -join ' / '))
            mh audit | Out-Null
        }
        mh open
        $opened = Read-Host "10a. mh open: did your browser open the list of the reports? (y/n)"
        Log "   10a. browser opened on index.html by mh open: $opened"

        # 10b: the shortcuts, yours saved first.
        $shell = New-Object -ComObject WScript.Shell
        $links = @(foreach ($place in 'Desktop', 'Programs') { Join-Path ([Environment]::GetFolderPath($place)) 'Media Hygiene.lnk' })
        foreach ($link in $links) { if (Test-Path -LiteralPath $link) { Copy-Item -LiteralPath $link -Destination "$link.mh-measure" -Force } }
        $said = @(mh shortcut 6>&1 | ForEach-Object { "$_" })
        foreach ($line in $said) { Log ("   10b. " + $line) }
        foreach ($link in $links) {
            $back = $shell.CreateShortcut($link)
            Log ("   10b. {0} exists: {1}; target {2}; arguments {3}" -f $link, (Test-Path -LiteralPath $link), $back.TargetPath, $back.Arguments)
            Log ("   10b. {0} arguments hold Bypass (0257, expected False): {1}" -f $link, ($back.Arguments -match 'Bypass'))
        }
        $clicked = Read-Host "10b. Double-click Media Hygiene on your Desktop: does a PowerShell window open, stay open, and the home page open in your browser? (y/n)"
        Log "   10b. the icon opens the window and the home page: $clicked"
        $alert = Read-Host "10b. Did Avast or Windows Defender show anything since that double-click (an alert, a blocked file)? (none, or what it said)"
        Log "   10b. antivirus after the double-click (0257): $alert"
        $null = Read-Host "10b. Close that window with its X (top right). Then press Enter here"
        MhLeftovers "10b"

        # 10c: the right-click entries (a folder; the background of an open folder, 0188), yours
        # exported first; a folder whose name has a space and an apostrophe.
        $entries = @('Directory\shell\MediaHygiene', 'Directory\Background\shell\MediaHygiene')
        $had = @{}
        foreach ($entry in $entries) {
            $had[$entry] = Test-Path -LiteralPath "HKCU:\Software\Classes\$entry"
            if ($had[$entry]) { & reg.exe export "HKCU\Software\Classes\$entry" (Join-Path $Work ("explorer-key-{0}.reg" -f ($entry -replace "\\", "-"))) /y | Out-Null }
        }
        $said = @(mh explorer 6>&1 | ForEach-Object { "$_" })
        foreach ($line in $said) { Log ("   10c. " + $line) }
        foreach ($entry in $entries) {
            $command = (Get-Item -LiteralPath "HKCU:\Software\Classes\$entry\command" -ErrorAction SilentlyContinue)
            Log ("   10c. registry command of {0} read back: {1}" -f $entry, $(if ($command) { $command.GetValue('') } else { '(none)' }))
            Log ("   10c. {0} command holds Bypass (0257, expected False): {1}" -f $entry, ($command -and ($command.GetValue('') -match 'Bypass')))
        }
        $odd = Join-Path $Work "L'ete 2019"
        New-Item -ItemType Directory -Force -Path $odd | Out-Null
        Get-ChildItem -Path (Join-Path $data "flat") -File | Select-Object -First 3 | Copy-Item -Destination $odd
        explorer.exe $Work
        $menu = Read-Host "10c. In the Explorer window, right-click the folder L'ete 2019, then Media Hygiene: do a PowerShell window and the home page open? (y/n)"
        Log "   10c. right-click opens the window and the home page: $menu"
        $alert = Read-Host "10c. Did Avast or Windows Defender show anything since that right-click (an alert, a blocked file)? (none, or what it said)"
        Log "   10c. antivirus after the right-click (0257): $alert"
        $where = Read-Host "10c. Where was Media Hygiene: in the first menu, or under Show more options? (first/more)"
        Log "   10c. entry found in: $where (Windows $([Environment]::OSVersion.Version))"
        $named = Read-Host "10c. On the page, under 'Where you are', is the first line 'This page also analyses: ...\L'ete 2019', in bold? (y/n, or what it says)"
        Log "   10c. the page names the folder clicked (0258): $named"
        $popup = Read-Host "10c. Click Run on the line mh audit. Does the page say 'mh audit runs in the PowerShell window of mh (in the taskbar)'? If the page has not come back after 30 s, does it add 'Nothing moves? Look at ...'? (y/back: the page came back before 30 s, no hint expected; y/y; y/n; n/...)"
        Log "   10c. Run names the window, then the 30 s hint (0258): $popup"
        $audit = Read-Host "10c. In the PowerShell window, how many media files does the audit say it scanned? (43 with L'ete 2019's 3 photos; type the number)"
        Log "   10c. audit run from the page, files scanned (43 expected): $audit"
        $back = Read-Host "10c. When the audit ended, did the home page come back by itself? (y/n)"
        Log "   10c. the page came back after the step: $back"
        $null = Read-Host "10c. Close that mh window with its X (top right), as a user would. Then press Enter here"
        # 0250: the page of a closed window keeps running; the next mh page must stop it itself.
        $pages = @(& docker ps --filter "publish=8088" --format '{{.ID}};{{.Labels}}' 2>$null | ForEach-Object { "$_" -replace ';.*?(media-hygiene\.page=[^,]*).*', ';$1' })
        Log ("   10c. containers on port 8088 after the X (0250): " + $(if ($pages) { $pages -join ' / ' } else { '(none)' }))
        $inside = Read-Host "10c. In Explorer, open L'ete 2019, right-click the EMPTY SPACE next to its photos, then Media Hygiene: does the home page open, naming L'ete 2019 under 'Where you are'? (y/n)"
        Log "   10c. right-click on the background of the open folder opens the menu on it (0188): $inside"
        $freed = Read-Host "10c. Did that window first say 'An mh page left open by a closed window was stopped.' and open the page, with no 'port is already allocated'? (y/n, or what it said)"
        Log "   10c. the next page stopped the leftover and opened (0250): $freed"
        $where = Read-Host "10c. Where was Media Hygiene on the background: in the first menu, or under Show more options? (first/more)"
        Log "   10c. background entry found in: $where"
        $null = Read-Host "10c. Close that mh window too, with its X. Then press Enter here"
        MhLeftovers "10c"

        # 10e (0257): the same right-click with mh.ps1 where users keep it, under
        # %USERPROFILE%\media-hygiene (a folder of its own, removed after), against -Work above:
        # tells whether the path weighs in an antivirus alert.
        $home10e = Join-Path $env:USERPROFILE "media-hygiene\mh-measure-10e"
        New-Item -ItemType Directory -Force -Path $home10e | Out-Null
        $mhHome = Join-Path $home10e "mh.ps1"
        Copy-Item -LiteralPath $mhFile -Destination $mhHome -Force
        . $mhHome
        $said = @(mh explorer 6>&1 | ForEach-Object { "$_" })
        foreach ($line in $said) { Log ("   10e. " + $line) }
        $menu = Read-Host "10e. Right-click L'ete 2019 again, then Media Hygiene (mh.ps1 now under $home10e): do the window and the home page open? (y/n)"
        Log "   10e. right-click with mh.ps1 under the user's folder: $menu"
        $alert = Read-Host "10e. Did Avast or Windows Defender show anything this time? (none, or what it said)"
        Log "   10e. antivirus, mh.ps1 under %USERPROFILE%\media-hygiene: $alert"
        $null = Read-Host "10e. Close that mh window with its X (top right). Then press Enter here"
        MhLeftovers "10e"
        . $mhFile
        Remove-Item -LiteralPath $home10e -Recurse -Force -ErrorAction SilentlyContinue
    }

    # 10f (0253): which program Windows names for a port a container publishes (Docker
    # Desktop's own listener, never "another program"), then another program on 8088: mh
    # review must name it in one line, never Docker's raw error; the probe timed.
    # A page still open (a window not closed) would answer instead of the program: stopped.
    foreach ($id in @(& docker ps --quiet --filter "publish=8088" 2>$null)) {
        Log "   10f. a page still on 8088 stopped first: $id"
        $null = & docker stop $id 2>$null
    }
    $page = & docker run -d --rm -p 127.0.0.1:8088:8088 --entrypoint sleep $Image 60 2>$null
    Start-Sleep -Seconds 2
    $names = @(Get-NetTCPConnection -LocalPort 8088 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { "$((Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).ProcessName) ($($_.OwningProcess))" })
    Log ("   10f. listeners of a port a container publishes (Docker's own): " + $(if ($names) { $names -join ' / ' } else { '(none)' }))
    if ($page) { $null = & docker stop $page 2>$null }
    $listener = Start-Job -ScriptBlock {
        $socket = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, 8088)
        $socket.Start()
        Start-Sleep -Seconds 120
        $socket.Stop()
    }
    Start-Sleep -Seconds 3
    $watch = [Diagnostics.Stopwatch]::StartNew()
    $null = @(Get-NetTCPConnection -LocalPort 8088 -State Listen -ErrorAction SilentlyContinue)
    $watch.Stop()
    Log ("   10f. the probe (Get-NetTCPConnection) took {0:N0} ms (estimated 100-500)" -f $watch.Elapsed.TotalMilliseconds)
    $said = @(mh review 6>&1 2>&1 | ForEach-Object { "$_".Trim() } | Where-Object { $_ })
    Log ("   10f. mh review with another program on 8088 (one line naming powershell and its process, expected): exit code $LASTEXITCODE, " + ($said -join ' / '))
    Log ("   10f. Docker's raw error shown (expected False): " + [bool]($said -match 'already allocated|address already in use'))
    Stop-Job -Job $listener -ErrorAction SilentlyContinue
    Remove-Job -Job $listener -Force -ErrorAction SilentlyContinue

    if (-not $portOnly) {
        # 10d: --remove, then what you had put back.
        $said = @(mh explorer --remove 6>&1 | ForEach-Object { "$_" })
        foreach ($line in $said) { Log ("   10d. " + $line) }
        foreach ($entry in $entries) {
            Log ("   10d. key {0} still there after --remove: {1}" -f $entry, (Test-Path -LiteralPath "HKCU:\Software\Classes\$entry"))
            if ($had[$entry]) { & reg.exe import (Join-Path $Work ("explorer-key-{0}.reg" -f ($entry -replace "\\", "-"))) 2>&1 | Out-Null }
        }
        foreach ($link in $links) {
            Remove-Item -LiteralPath $link -Force -ErrorAction SilentlyContinue
            if (Test-Path -LiteralPath "$link.mh-measure") { Move-Item -LiteralPath "$link.mh-measure" -Destination $link -Force }
        }
        Log "   10d. your own shortcuts and right-click entry, if any, are back; close the mh windows."
    }
    $ErrorActionPreference = "Stop"
}

# --- 11: mh folders and mh update, mh rewriting its own file (0176, 0177) ------------------
# mh is written by the image under test; a folder added here is audited from a new terminal.
if (Wanted 11) {
    $ErrorActionPreference = "Continue"
    $mhDir = Join-Path $tool "mh11"
    New-Item -ItemType Directory -Force -Path $mhDir, (Join-Path $tool "config") | Out-Null
    $mhFile = Join-Path $mhDir "mh.ps1"
    $toolMounts = @(
        "-v", "${volume}:/cache",
        "-v", "$(Join-Path $tool 'config'):/config",
        "-v", "$(Join-Path $tool 'journal'):/journal",
        "-v", "$(Join-Path $tool 'quarantine'):/quarantine",
        "-v", "$(Join-Path $tool 'reports'):/reports"
    )
    & docker run --rm -e "MEDIA_HYGIENE_IMAGE=$Image" @toolMounts $Image launcher --photos $data > $mhFile
    . $mhFile
    Log ""
    Log "== 11. mh folders and mh update (0176, 0177)"
    $said = @(mh folders 6>&1 | ForEach-Object { "$_" })
    foreach ($line in $said) { Log ("   11a. " + $line) }
    $scanned = @(mh audit 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -match 'Media files scanned' })
    Log ("   11a. audit before add: " + ($scanned -join ' / '))

    # 11b: one more folder, then a new terminal (its own powershell.exe) loads the file and audits.
    $extra = Join-Path $Work "Extra photos"
    New-Item -ItemType Directory -Force -Path $extra | Out-Null
    Get-ChildItem -Path (Join-Path $data "flat") -File | Select-Object -First 3 | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $extra ("extra-" + $_.Name)) }
    $said = @(mh folders add $extra 6>&1 | ForEach-Object { "$_" })
    foreach ($line in $said) { Log ("   11b. " + $line) }
    Log ("   11b. the file names the folder: " + [bool](Select-String -LiteralPath $mhFile -SimpleMatch -Pattern $extra -Quiet))
    Log ("   11b. no temporary file left: " + (-not (Test-Path -LiteralPath "$mhFile.new")))
    $result = Join-Path $mhDir "probe.txt"
    $probe = Join-Path $mhDir "probe.ps1"
    Set-Content -Path $probe -Encoding Ascii -Value @'
param([string]$mh, [string]$result)
function Note([string]$text) { Add-Content -Path $result -Value $text -Encoding UTF8 }
. $mh
foreach ($line in @(mh folders 6>&1 | ForEach-Object { "$_" })) { Note ("   11b. new terminal: " + $line) }
$lines = @(mh audit 2>&1 | ForEach-Object { "$_" })
Note ("   11b. new terminal, exit code " + $LASTEXITCODE + ": " + (@($lines | Where-Object { $_ -match 'Media files scanned' }) -join ' / '))
'@
    Remove-Item -Force -ErrorAction SilentlyContinue $result
    Start-Process -FilePath powershell.exe -ArgumentList "-NoProfile -File `"$probe`" -mh `"$mhFile`" -result `"$result`"" -Wait
    if (Test-Path $result) { Get-Content -Path $result -Encoding UTF8 | ForEach-Object { Log $_ } }

    # 11c: refused folders leave the file as it was; 11d: the folder taken out again.
    $before = (Get-FileHash -LiteralPath $mhFile).Hash
    $inside = Join-Path $data "flat"
    $said = @(mh folders add $inside 6>&1 | ForEach-Object { "$_" })
    foreach ($line in $said) { Log ("   11c. add a folder inside another: " + $line) }
    Log ("   11c. mh.ps1 unchanged: " + ($before -eq (Get-FileHash -LiteralPath $mhFile).Hash))
    $said = @(mh folders remove $data 6>&1 | ForEach-Object { "$_" })
    $said += @(mh folders remove $extra 6>&1 | ForEach-Object { "$_" })
    $said += @(mh folders remove $data 6>&1 | ForEach-Object { "$_" })
    foreach ($line in $said) { Log ("   11d. " + $line) }

    # 11e: mh update. The local build has nothing to pull.
    $said = @(mh update 6>&1 | ForEach-Object { "$_" })
    foreach ($line in $said) { Log ("   11e. local image: " + $line) }
    $agree = Read-Host "11e. Try mh update for real? Your local image is tagged cavo789/media-hygiene, then the published one is pulled over that tag (y/n)"
    Log "   11e. real update tried: $agree"
    if ($agree -eq 'y') {
        & docker tag $Image "cavo789/media-hygiene:latest"
        & docker run --rm -e "MEDIA_HYGIENE_IMAGE=cavo789/media-hygiene" @toolMounts $Image launcher --photos $data > $mhFile
        . $mhFile
        $said = @(mh update 6>&1 | ForEach-Object { "$_" })
        foreach ($line in $said) { Log ("   11e. " + $line) }
        Log ("   11e. mh.ps1 still names the folder: " + [bool](Select-String -LiteralPath $mhFile -SimpleMatch -Pattern $data -Quiet))
        Log ("   11e. images: " + ((& docker image ls --format '{{.Repository}}:{{.Tag}} {{.Size}}' | Where-Object { $_ -match 'media-hygiene' }) -join ' / '))
        # mh now runs the published image, older than the image under test: it refuses the
        # settings the newer image wrote into config.toml (11f-11i all failed so, 2026-10-19).
        & docker run --rm -e "MEDIA_HYGIENE_IMAGE=$Image" @toolMounts $Image launcher --photos $data > $mhFile
        . $mhFile
        Log "   11e. mh written again with ${Image}: 11f-11i measure the image under test"
    }

    # 11f: mh folders add alone: Windows' folder window (0201), chosen, then cancelled.
    $pickedDir = Join-Path $Work "Picked photos"
    New-Item -ItemType Directory -Force -Path $pickedDir | Out-Null
    Get-ChildItem -Path (Join-Path $data "flat") -File | Select-Object -First 2 | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $pickedDir ("picked-" + $_.Name)) }
    Write-Host "11f. A folder window opens: choose $pickedDir (This PC, then the folders), then OK."
    $said = @(mh folders add 6>&1 | ForEach-Object { "$_" })
    foreach ($line in $said) { Log ("   11f. " + $line) }
    # The folder window gives the long path, %TEMP% may be the short one (CHRIST~1): its name.
    Log ("   11f. the file names the folder chosen: " + [bool](Select-String -LiteralPath $mhFile -SimpleMatch -Pattern "\Picked photos" -Quiet))
    $front = Read-Host "11f. Did the window open in front of this console, without Alt+Tab? (y/n)"
    Log "   11f. window in front of the console: $front"
    $before = (Get-FileHash -LiteralPath $mhFile).Hash
    Write-Host "11g. The folder window opens again: click Cancel."
    $said = @(mh folders add 6>&1 | ForEach-Object { "$_" })
    foreach ($line in $said) { Log ("   11g. cancelled: " + $line) }
    Log ("   11g. mh.ps1 unchanged after cancel: " + ($before -eq (Get-FileHash -LiteralPath $mhFile).Hash))
    $avast = Read-Host "11g. Did your antivirus say anything during 11f or 11g? (n, or what it said)"
    Log "   11g. antivirus: $avast"
    $null = @(mh folders remove $pickedDir 6>&1)

    # 11h: a backup (0205): mounted read-only for every command, clean included. Its files are
    # copies of the test folder's, two of them twice: clean must leave all of them. On
    # -OtherDrive when given (a backup is often another disk), else in the test folder.
    $backupDir = if ($OtherDrive -ne "") { Join-Path $OtherDrive "mh-measure-11-backup" } else { Join-Path $Work "Backup copy" }
    New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
    $sources = @(Get-ChildItem -Path (Join-Path $data "flat") -File | Select-Object -First 3)
    foreach ($photo in $sources) { Copy-Item -LiteralPath $photo.FullName -Destination (Join-Path $backupDir $photo.Name) }
    Copy-Item -LiteralPath $sources[0].FullName -Destination (Join-Path $backupDir ("planted-" + $sources[0].Name))
    Copy-Item -LiteralPath $sources[1].FullName -Destination (Join-Path $backupDir ("planted-" + $sources[1].Name))
    $planted = @(Get-ChildItem -LiteralPath $backupDir -File).Count
    $said = @(mh folders add --backup $backupDir 6>&1 | ForEach-Object { "$_" })
    foreach ($line in $said) { Log ("   11h. " + $line) }
    $mounts = @(Select-String -LiteralPath $mhFile -SimpleMatch -Pattern "-v `"${backupDir}:" | ForEach-Object { $_.Line.Trim() })
    Log ("   11h. mount line of the backup in mh.ps1: " + ($mounts -join ' / '))
    # 0252: a removable drive (a USB stick) is not shared by WSL; mh shares it before the run.
    $letter = $backupDir.Substring(0, 1)
    $kind = (Get-Volume -DriveLetter $letter -ErrorAction SilentlyContinue).DriveType
    Log "   11h. drive ${letter}: of the backup is $kind (Get-Volume)"
    $before = @(& docker run --rm -v "${backupDir}:/data/backup:ro" --entrypoint sh $Image -c "grep ' /data' /proc/self/mountinfo; ls /data/backup | wc -l" 2>&1 | ForEach-Object { "$_" })
    Log ("   11h. the backup in a docker run before mh (mountinfo, then files seen): " + ($before -join ' / '))
    $lines = @(mh audit 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -match 'this backup|nowhere else|only in it|Media files scanned|removable|cannot see|Docker Desktop' })
    foreach ($line in $lines) { Log ("   11h. mh audit: " + $line.Trim()) }
    # mh unshares the stick after each command: a docker run by hand sees it empty again.
    $vm = @(& wsl.exe -d docker-desktop sh -c "grep ' /mnt/host/$($letter.ToLower()) ' /proc/mounts || echo none" 2>&1 | ForEach-Object { "$_" })
    Log ("   11h. drive ${letter}: in Docker Desktop's VM after mh audit (none = unshared): " + ($vm -join ' / '))
    $after = @(& docker run --rm -v "${backupDir}:/data/backup:ro" --entrypoint sh $Image -c "grep ' /data' /proc/self/mountinfo; ls /data/backup | wc -l" 2>&1 | ForEach-Object { "$_" })
    Log ("   11h. the backup in a docker run after mh (mountinfo, then files seen, planted: $planted; 0 on a stick, unshared): " + ($after -join ' / '))
    $lines = @(mh clean --yes 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -match 'backup|read-only|Read-only|Error|moved|set aside' })
    foreach ($line in $lines) { Log ("   11i. mh clean: " + $line.Trim()) }
    $left = @(Get-ChildItem -LiteralPath $backupDir -File).Count
    Log "   11i. files in the backup after mh clean: $left (planted: $planted, all must stay)"
    $refused = @(& docker run --rm -v "${backupDir}:/backup:ro" --entrypoint sh $Image -c "touch /backup/written-by-docker" 2>&1 | ForEach-Object { "$_" })
    Log ("   11i. a write in a :ro mount of it, by Docker: exit code $LASTEXITCODE, says: " + ($refused -join ' / '))
    $said = @(mh undo --yes 2>&1 | ForEach-Object { "$_".Trim() } | Where-Object { $_ })
    Log ("   11i. mh undo of that clean: exit code $LASTEXITCODE, says: " + (($said | Select-Object -Last 6) -join ' / '))
    if ("$kind" -eq 'Removable') {
        # 0252: after each command mh unshares the stick, so Windows can eject it. A WSL
        # distribution started while the stick is in mounts it (/mnt/d) and may hold it:
        # listed here without starting any (wsl -e would start one, and mount the stick).
        $running = @(& wsl.exe --list --running --quiet 2>$null | ForEach-Object { "$_" -replace "`0", '' } | Where-Object { $_.Trim() })
        Log ("   11j. WSL distributions running before the eject: " + $(if ($running) { $running -join ', ' } else { 'none' }))
        $ejected = Read-Host "11j. Safely remove ${letter}: now (taskbar, Safely Remove Hardware, Eject). Did Windows let you, without 'This device is currently in use'? (y/n, or what it said)"
        Log "   11j. ${letter}: ejected safely after the mh commands: $ejected"
        $null = Read-Host "11j. Plug ${letter}: back in (same letter), then press Enter"
        # 11k (0254): from your WSL distribution (Docker Desktop's integration on): is the
        # interop on, is the stick in /mnt, and which mount does a container started from
        # WSL see: the distribution's /mnt/x once mounted there (the line mh.sh says to type), or not.
        $low = $letter.ToLower()
        $wslPath = "/mnt/$low/" + ($backupDir.Substring(3) -replace '\\', '/')
        $distro = "$(& wsl.exe -e printenv WSL_DISTRO_NAME 2>$null)".Trim()
        $interop = "$(& wsl.exe -e sh -c 'command -v cmd.exe' 2>$null)".Trim()
        Log "   11k. WSL distribution: $distro; cmd.exe reachable (interop on): $(if ($interop) { $interop } else { 'no' })"
        $null = & wsl.exe -e mountpoint -q "/mnt/$low" 2>$null
        Log "   11k. /mnt/$low a mount in $distro before (0 = mounted; expected 1 for a stick plugged in after WSL started): $LASTEXITCODE"
        $seen = @(& wsl.exe -e docker run --rm -v "${wslPath}:/x:ro" --entrypoint ls $Image /x 2>&1)
        Log ("   11k. files a container from WSL sees, nothing mounted (planted: $planted): exit code $LASTEXITCODE, " + @($seen).Count + " lines: " + (($seen | Select-Object -First 3) -join ' / '))
        $null = & wsl.exe -u root -e mkdir -p "/mnt/$low" 2>$null
        $said = @(& wsl.exe -u root -e mount -t drvfs "${letter}:" "/mnt/$low" -o uid=1000,gid=1000 2>&1 | ForEach-Object { "$_" })
        Log ("   11k. mount -t drvfs ${letter}: /mnt/$low in $distro (the line mh.sh says to type): exit code $LASTEXITCODE " + ($said -join ' / '))
        $seen = @(& wsl.exe -e docker run --rm -v "${wslPath}:/x:ro" --entrypoint ls $Image /x 2>&1)
        Log ("   11k. files a container from WSL sees, mounted in $distro (planted: $planted expected): exit code $LASTEXITCODE, " + @($seen).Count + " lines")
        $vm = @(& wsl.exe -d docker-desktop sh -c "grep ' /mnt/host/$low ' /proc/mounts || echo none" 2>&1 | ForEach-Object { "$_" })
        Log ("   11k. drive ${letter}: in Docker Desktop's VM meanwhile (none: the distribution's mount is what counts): " + ($vm -join ' / '))
        $said = @(& wsl.exe -u root -e umount "/mnt/$low" 2>&1 | ForEach-Object { "$_" })
        Log ("   11k. umount /mnt/$low in ${distro}: exit code $LASTEXITCODE " + ($said -join ' / '))
        # 11j asked after the mh commands alone; here, after WSL's own mount and Docker's try.
        $ejected = Read-Host "11k. Safely remove ${letter}: again now. Did Windows let you this time? (y/n, or what it said)"
        Log "   11k. ${letter}: ejected after the WSL checks: $ejected"
        if ("$ejected" -notmatch '^y') {
            Write-Host "11k. In another PowerShell (on C:), type: wsl --shutdown   (it stops Docker Desktop too)"
            $shut = Read-Host "11k. Then Safely remove ${letter}: again. Did Windows let you now? (y/n, or what it said)"
            Log "   11k. ${letter}: ejected after wsl --shutdown: $shut"
            $null = Read-Host "11k. Start Docker Desktop again (Start menu), wait until it runs, plug ${letter}: back in, then press Enter"
        } else {
            $null = Read-Host "11k. Plug ${letter}: back in (same letter), then press Enter"
        }
    }
    $null = @(mh folders remove $backupDir 6>&1)
    if ($OtherDrive -ne "" -and -not $Keep) { Remove-Item -Recurse -Force -LiteralPath $backupDir }
    $ErrorActionPreference = "Stop"
}

# --- 12: photos on another drive than the quarantine (0182) --------------------------------
# A few duplicates copied to X:\mh-measure-12 (removed at the end); the quarantine is the test
# folder's, on C:. 12a must show the line with X:, C: and C:'s free space; 12c must not.
$otherRoot = ""
if (Wanted 12) {
    if ($OtherDrive -eq "" -and $unplugged -eq "") {
        $found = Get-PSDrive -PSProvider FileSystem |
            Where-Object { $_.Name -ne 'C' -and $_.Free -gt 2GB } | Select-Object -First 1
        if ($found) { $OtherDrive = $found.Name + ":" }
    }
    Log ""
    if ($unplugged -ne "") {
        Log "== 12. skipped: -OtherDrive $unplugged is not accessible"
    } elseif ($OtherDrive -eq "") {
        Log "== 12. skipped: no drive other than C: with 2 GB free (give one with -OtherDrive)"
    } elseif (Removable $OtherDrive) {
        Log "== 12. skipped: $OtherDrive is a removable drive (a USB stick): steps 12 and 13 need a fixed disk, an external hard disk for instance (-OtherDrive)"
    } else {
        $otherRoot = Join-Path ($OtherDrive.TrimEnd('\') + "\") "mh-measure-12"
        $otherData = Join-Path $otherRoot "data"
        $otherQuarantine = Join-Path $otherRoot "quarantine"
        foreach ($folder in "a", "b") {
            New-Item -ItemType Directory -Force -Path (Join-Path $otherData $folder) | Out-Null
        }
        New-Item -ItemType Directory -Force -Path $otherQuarantine | Out-Null
        foreach ($photo in ($picked | Select-Object -First 10)) {
            Copy-Item -LiteralPath $photo.FullName -Destination (Join-Path $otherData "a\$($photo.Name)")
            Copy-Item -LiteralPath $photo.FullName -Destination (Join-Path $otherData "b\$($photo.Name)")
        }
        $letter = $OtherDrive.Substring(0, 1).ToLower()
        $otherMounts = @(
            "-v", "${otherData}:/data/${letter}/mh-measure-12",
            "-v", "${volume}:/cache",
            "-v", "$(Join-Path $tool 'journal'):/journal",
            "-v", "$(Join-Path $tool 'reports'):/reports"
        )
        $onC = $otherMounts + @("-v", "$(Join-Path $tool 'quarantine'):/quarantine")
        $onOther = $otherMounts + @("-v", "${otherQuarantine}:/quarantine")
        Log ("== 12. data on $OtherDrive, Windows says C: has {0:N1} GB free" -f ((Get-PSDrive C).Free / 1GB))
        Measure-Mh "12a. clean, quarantine on C:: one line names $OtherDrive and C: (0182)" $onC @("clean", "--yes")
        Measure-Mh "12b. undo of that clean" $onC @("undo", "--yes")
        Measure-Mh "12c. clean, quarantine on ${OtherDrive}: no line expected (0182)" $onOther @("clean", "--yes")
        Measure-Mh "12d. undo of that clean" $onOther @("undo", "--yes")
    }
}

# --- 13: one quarantine per drive: copy E: -> C: against E: -> E: (0183) -------------------
# 1 GB of photos of -Photos copied twice to X:\mh-measure-13 (removed at the end): each clean
# sets 1 GB aside. 13a/13b: quarantine on C: only; 13c/13d: X:'s own on /quarantine/x too.
# If 13c is not faster than 13a, the gain of 0183 is the space on C: only (say it in the docs).
$driveRoot = ""
if (Wanted 13) {
    $drive13 = $OtherDrive
    if ($drive13 -eq "" -and $unplugged -eq "") {
        $found = Get-PSDrive -PSProvider FileSystem |
            Where-Object { $_.Name -ne 'C' -and $_.Free -gt 3GB } | Select-Object -First 1
        if ($found) { $drive13 = $found.Name + ":" }
    }
    Log ""
    if ($unplugged -ne "") {
        Log "== 13. skipped: -OtherDrive $unplugged is not accessible"
    } elseif ($drive13 -eq "") {
        Log "== 13. skipped: no drive other than C: with 3 GB free (give one with -OtherDrive)"
    } elseif (Removable $drive13) {
        Log "== 13. skipped: $drive13 is a removable drive (a USB stick): step 13 needs a fixed disk (-OtherDrive)"
    } else {
        $driveRoot = Join-Path ($drive13.TrimEnd('\') + "\") "mh-measure-13"
        $driveData = Join-Path $driveRoot "data"
        $driveQuarantine = Join-Path $driveRoot "quarantine"
        foreach ($folder in "data\a", "data\b", "quarantine") {
            New-Item -ItemType Directory -Force -Path (Join-Path $driveRoot $folder) | Out-Null
        }
        $bytes = 0
        $files = 0
        Write-Host "13. Copying 1 GB of photos twice to $drive13 first (minutes on a slow disk)..."
        foreach ($photo in (Get-ChildItem -Path $Photos -Recurse -File -Include *.jpg, *.jpeg)) {
            if ($bytes -ge 1GB) { break }
            $name = "{0:D6}-{1}" -f $files, $photo.Name
            Copy-Item -LiteralPath $photo.FullName -Destination (Join-Path $driveData "a\$name")
            Copy-Item -LiteralPath $photo.FullName -Destination (Join-Path $driveData "b\$name")
            $bytes += $photo.Length
            $files++
        }
        $letter13 = $drive13.Substring(0, 1).ToLower()
        $driveMounts = @(
            "-v", "${driveData}:/data/${letter13}/mh-measure-13",
            "-v", "${volume}:/cache",
            "-v", "$(Join-Path $tool 'journal'):/journal",
            "-v", "$(Join-Path $tool 'reports'):/reports",
            "-v", "$(Join-Path $tool 'quarantine'):/quarantine"
        )
        $ownQuarantine = $driveMounts + @("-v", "${driveQuarantine}:/quarantine/${letter13}")
        Log ("== 13. {0} files ({1:N2} GB) to set aside on $drive13" -f $files, ($bytes / 1GB))
        Measure-Mh "13a. clean, quarantine on C: (copy $drive13 -> C:) (0183)" $driveMounts @("clean", "--yes")
        Measure-Mh "13b. undo of that clean (copy C: -> $drive13)" $driveMounts @("undo", "--yes")
        Measure-Mh "13c. clean, $drive13's own quarantine (copy $drive13 -> $drive13) (0183)" $ownQuarantine @("clean", "--yes")
        $aside = @(Get-ChildItem -Path $driveQuarantine -Recurse -File).Count
        Log "   13c. files in $driveQuarantine after the clean: $aside (expected: $files)"
        Measure-Mh "13d. undo without $drive13's quarantine mounted: must refuse, naming $drive13" $driveMounts @("undo", "--yes")
        Measure-Mh "13e. undo of that clean (copy $drive13 -> $drive13)" $ownQuarantine @("undo", "--yes")
    }
}

# --- 14: the mh menu by hand, in the old console and in your usual one (0172) --------------
# mh menu lists the steps; a number then Enter runs one. Watch the colours and the columns.
# Then mh alone opens the home page; the step chosen there runs in the console (0210).
if (Wanted 14) {
    $ErrorActionPreference = "Continue"
    $mhDir = Join-Path $tool "mh14"
    New-Item -ItemType Directory -Force -Path $mhDir, (Join-Path $tool "config") | Out-Null
    $mhFile = Join-Path $mhDir "mh.ps1"
    $toolMounts = @(
        "-v", "${volume}:/cache",
        "-v", "$(Join-Path $tool 'config'):/config",
        "-v", "$(Join-Path $tool 'journal'):/journal",
        "-v", "$(Join-Path $tool 'quarantine'):/quarantine",
        "-v", "$(Join-Path $tool 'reports'):/reports"
    )
    & docker run --rm -e "MEDIA_HYGIENE_IMAGE=$Image" @toolMounts $Image launcher --photos $data > $mhFile
    Log ""
    Log "== 14. the mh menu by hand (0172)"
    foreach ($console in 'conhost', 'usual') {
        if ($console -eq 'conhost') {
            Write-Host "14 (old console): Win+R, type conhost.exe powershell.exe, Enter."
        } else {
            Write-Host "14 (usual console): open Windows PowerShell as you usually do."
        }
        Write-Host "    In it, type: . '$mhFile'; mh menu"
        Write-Host "    The mh menu shows. Type the number of 'audit', Enter; when it ends, type mh menu again, then Ctrl+C at the question."
        $colours = Read-Host "14. Colours shown as colours, not as codes like [32m? (y/n)"
        $columns = Read-Host "14. Emoji and step columns lined up? (y/n)"
        $ran = Read-Host "14. The number + Enter ran audit? (y/n)"
        $stopped = Read-Host "14. Ctrl+C at the question gave the prompt back, no red error? (y/n)"
        Log "   14 ($console): colours $colours, columns $columns, number ran $ran, Ctrl+C clean $stopped"
        Write-Host "Close that window."
    }
    # mh alone: the home page in the browser; its buttons run the steps in the console (0210).
    Write-Host "14 (home page): open Windows PowerShell as you usually do."
    Write-Host "    In it, type: . '$mhFile'; mh"
    Write-Host "    The home page opens in your browser. Click Run on the 'clean' step: it runs in the"
    Write-Host "    PowerShell window and asks its question there; answer n. The page must come back."
    Write-Host "    Then go to the Clean space; click 'Open the page' on its 'review' step: the review"
    Write-Host "    page must show in the SAME tab. On it, click 'Back to the home page' in the top bar."
    Write-Host "    Count the browser tabs on 127.0.0.1 (0280: one tab from start to end)."
    Write-Host "    Finally press Ctrl+C in the PowerShell window (the home page has no Quit button)."
    $opened = Read-Host "14h. mh alone opened the home page in the browser? (y/n)"
    $asked = Read-Host "14h. Run on 'clean' ran it in the PowerShell window, with its question? (y/n)"
    $back = Read-Host "14h. After it, the home page came back by itself (reloaded)? (y/n)"
    $sameTab = Read-Host "14h. The review page showed in the same tab, no new tab? (y/n)"
    $homeLink = Read-Host "14h. 'Back to the home page' came back to the Clean space? (y/n)"
    $tabs = Read-Host "14h. How many tabs on 127.0.0.1 at the end? (a number)"
    $quit = Read-Host "14h. Ctrl+C gave the PowerShell prompt back, no red error? (y/n)"
    Log "   14h (home page): opened $opened, clean in the console $asked, page back $back, review in the same tab $sameTab, back to Clean $homeLink, tabs $tabs, Ctrl+C clean $quit"
    Write-Host "Close that window."
}

# --- 15: the launcher line of the guide, then mh audit and mh --photos (0173) ----------------
# The same line as "Clean in short", step 0, with the test folder; nothing under your $HOME.
if (Wanted 15) {
    $ErrorActionPreference = "Continue"
    $mhDir = Join-Path $tool "mh15"
    New-Item -ItemType Directory -Force -Path $mhDir | Out-Null
    $mhFile = Join-Path $mhDir "mh.ps1"
    Log ""
    Log "== 15. launcher --photos, then mh (0173)"
    $errFile = Join-Path $mhDir "launcher-said.txt"
    & docker run --rm $Image launcher --photos $data > $mhFile 2> $errFile
    Log "   15a. launcher exit code: $LASTEXITCODE"
    foreach ($line in @(Get-Content -Path $errFile)) { if ("$line".Trim()) { Log ("   15a. launcher says: " + "$line".Trim()) } }
    Log ("   15a. mh.ps1 written: {0} bytes; holds Get-TimeZone: {1}" -f (Get-Item $mhFile).Length, ((Get-Content $mhFile -Raw) -match 'Get-TimeZone'))
    . $mhFile
    mh audit | Out-Null
    Log "   15b. mh audit: exit code $LASTEXITCODE"
    $lines = @(mh history 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -match '\d\d:\d\d' } | Select-Object -First 2)
    foreach ($line in $lines) { Log ("   15c. mh history: " + $line.Trim()) }
    Log ("   15c. clock of this PC: " + (Get-Date -Format "yyyy-MM-dd HH:mm") + " (" + (Get-TimeZone).Id + "): the history must show the same hour")
    if ($OtherDrive -ne "") {
        $other = Join-Path $OtherDrive "mh-measure-15"
        New-Item -ItemType Directory -Force -Path $other | Out-Null
        Copy-Item -Path (Join-Path $data "flat\*") -Destination $other -ErrorAction SilentlyContinue
        mh --photos $other audit | Out-Null
        Log "   15d. mh --photos $other audit: exit code $LASTEXITCODE"
        if (-not $Keep) { Remove-Item -Recurse -Force $other }
    } else {
        if ($unplugged -ne "") { Log "   15d. skipped: -OtherDrive $unplugged is not accessible" }
        else { Log "   15d. skipped: give -OtherDrive E: (a USB key) to audit a second folder with --photos" }
    }
    $said = @(mh --photos "Q:\mh-measure-not-plugged" audit 6>&1 2>&1 | ForEach-Object { "$_" })
    Log ("   15e. a folder not plugged in: exit code $LASTEXITCODE, says: " + ($said -join ' / '))
}

# --- 16: Docker Desktop closed: the exact message of docker run (0174), mh starting it (0200) --
# You quit Docker Desktop when asked; its own message and exit code are recorded as they are.
# Then mh starts it by itself: the check of `mh` alone, timed, and `mh audit` after a quit.
if (Wanted 16) {
    $ErrorActionPreference = "Continue"
    Log ""
    Log "== 16. docker run with Docker Desktop closed (0174), mh starting it (0200)"
    # mh is written while Docker Desktop still runs: launcher needs it.
    $mhDir = Join-Path $tool "mh16"
    New-Item -ItemType Directory -Force -Path $mhDir | Out-Null
    $mhFile = Join-Path $mhDir "mh.ps1"
    & docker run --rm $Image launcher --photos $data > $mhFile
    . $mhFile
    Log ("   16. Docker Desktop client: " + "$(& docker version --format '{{.Client.Version}}' 2>$null)")
    Read-Host "16. Quit Docker Desktop now (its icon near the clock, right-click, Quit), wait 20 s, then press Enter"
    $said = @(& docker run --rm $Image --version 2>&1 | ForEach-Object { "$_" })
    $code = $LASTEXITCODE
    foreach ($line in $said) { Log ("   16a. docker run says: " + $line.Trim()) }
    Log "   16a. docker run exit code: $code"
    & docker version --format '{{.Server.Version}}' 2>&1 | Out-Null
    Log "   16b. docker version exit code with Docker Desktop closed: $LASTEXITCODE"
    # 16c: what `mh` alone (the shortcut, the right-click) runs before the home page.
    Write-Host "16c. mh starts Docker Desktop now (up to 3 minutes); do not touch it."
    $watch = [Diagnostics.Stopwatch]::StartNew()
    $said = @(_mh_desktop 6>&1 | ForEach-Object { "$_" })
    $watch.Stop()
    foreach ($line in $said) { Log ("   16c. mh alone says: " + $line) }
    Log ("   16c. mh alone: Docker Desktop answering after {0:N0} s (the home page would open now)" -f $watch.Elapsed.TotalSeconds)
    & docker version --format '{{.Server.Version}}' 2>&1 | Out-Null
    Log "   16c. docker version exit code afterwards: $LASTEXITCODE"
    # 16d: another command after a quit: Docker Desktop started, the command not run twice.
    Read-Host "16d. Quit Docker Desktop again, wait 20 s, then press Enter (mh audit runs, then mh starts Docker Desktop)"
    $watch = [Diagnostics.Stopwatch]::StartNew()
    $said = @(mh audit 6>&1 2>&1 | ForEach-Object { "$_" })
    $code = $LASTEXITCODE
    $watch.Stop()
    foreach ($line in $said) { if ("$line".Trim()) { Log ("   16d. mh audit says: " + "$line".Trim()) } }
    Log ("   16d. mh audit: exit code {0}, {1:N0} s, says type the command again: {2}" -f $code, $watch.Elapsed.TotalSeconds, [bool]($said -match 'type the command again'))
    $scanned = @(mh audit 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -match 'Media files scanned' })
    Log ("   16e. mh audit typed again: exit code $LASTEXITCODE, " + ($scanned -join ' / '))
}

# --- 17: which part of mh.ps1 an antivirus refuses on write (Avast IDP.Generic) -----------
# mh.ps1 is kept in memory, then written to %TEMP%\mh-avast in variants, each without one
# part (or with only one): keep-awake (Add-Type kernel32), browser (Start-Job polling a URL),
# shortcut (WScript.Shell), right-click (HKCU registry). Refused or removed = flagged.
if (Wanted 17) {
    $ErrorActionPreference = "Continue"
    Log ""
    Log "== 17. which part of mh.ps1 is refused on write (antivirus)"
    $lines = @(& docker run --rm $Image launcher --shell powershell --photos $data 2>$null)
    Log ("   17. mh.ps1 in memory: {0} lines" -f $lines.Count)
    $parts = [ordered]@{
        awake    = 'Add-Type|DllImport|SetThreadExecutionState|MediaHygiene\.Power'
        browser  = 'Start-Job|Invoke-WebRequest|Start-Process \$url|Receive-Job|Stop-Job|Remove-Job'
        shortcut = 'WScript|CreateShortcut|ExecutionPolicy Bypass|\.lnk'
        registry = 'HKCU|New-ItemProperty|Classes\\Directory|%V'
    }
    $variants = [ordered]@{ 'full' = @() }
    foreach ($name in $parts.Keys) { $variants["without-$name"] = @($name) }
    $variants['without-all'] = @($parts.Keys)
    foreach ($name in $parts.Keys) { $variants["only-$name"] = @($parts.Keys | Where-Object { $_ -ne $name }) }
    $folder = Join-Path $env:TEMP "mh-avast"
    New-Item -ItemType Directory -Force -Path $folder | Out-Null
    $written = @{}
    foreach ($variant in $variants.Keys) {
        $drop = @($variants[$variant] | ForEach-Object { $parts[$_] })
        $kept = @($lines | Where-Object { $line = "$_"; -not ($drop | Where-Object { $line -match $_ }) })
        $text = ($kept -join "`r`n") + "`r`n"
        $path = Join-Path $folder "$variant.ps1"
        try {
            [IO.File]::WriteAllText($path, $text, (New-Object Text.UTF8Encoding $false))
            $written[$variant] = $text
            Log ("   17. {0,-18} {1,4} lines: written" -f $variant, $kept.Count)
        } catch {
            Log ("   17. {0,-18} {1,4} lines: REFUSED ({2})" -f $variant, $kept.Count, $_.Exception.GetType().Name)
        }
    }
    Start-Sleep -Seconds 15
    foreach ($variant in $written.Keys) {
        $path = Join-Path $folder "$variant.ps1"
        $still = (Test-Path -LiteralPath $path) -and ([IO.File]::ReadAllText($path) -eq $written[$variant])
        Log ("   17. {0,-18} still there, unchanged, 15 s later: {1}" -f $variant, $still)
    }
    $seen = Read-Host "17. Did the antivirus show alerts? Which file names did they give? (type them, or none)"
    Log "   17. antivirus alerts: $seen"
    if (-not $Keep) { Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $folder }
}

# --- 18: photos in OneDrive's cloud only, played without OneDrive (0199) ------------------
# A folder under a fake OneDrive root, 3 of its files marked Offline (0x00001000, one of the
# two attributes mh checks; a cloud provider alone sets the other). $env:OneDrive is changed
# for this window only and put back; nothing of your own OneDrive is read or changed.
if (Wanted 18) {
    $ErrorActionPreference = "Continue"
    $root = Join-Path $Work "OneDrive"
    $cloud = Join-Path $root "Pictures"
    $later = Join-Path $root "Later"
    New-Item -ItemType Directory -Force -Path $cloud, $later, (Join-Path $tool "config") | Out-Null
    Get-ChildItem -Path (Join-Path $data "flat") -File | Select-Object -First 5 | Copy-Item -Destination $cloud
    Get-ChildItem -Path (Join-Path $data "flat") -File | Select-Object -First 2 | Copy-Item -Destination $later
    foreach ($file in @(Get-ChildItem -LiteralPath $cloud -File | Select-Object -First 3) + @(Get-ChildItem -LiteralPath $later -File)) {
        $file.Attributes = $file.Attributes -bor [IO.FileAttributes]::Offline
    }
    $mhDir = Join-Path $tool "mh18"
    New-Item -ItemType Directory -Force -Path $mhDir | Out-Null
    $mhFile = Join-Path $mhDir "mh.ps1"
    $toolMounts = @(
        "-v", "${volume}:/cache",
        "-v", "$(Join-Path $tool 'config'):/config",
        "-v", "$(Join-Path $tool 'journal'):/journal",
        "-v", "$(Join-Path $tool 'quarantine'):/quarantine",
        "-v", "$(Join-Path $tool 'reports'):/reports"
    )
    & docker run --rm -e "MEDIA_HYGIENE_IMAGE=$Image" @toolMounts $Image launcher --photos $cloud > $mhFile
    . $mhFile
    $ownOneDrive = $env:OneDrive
    $env:OneDrive = $root
    $global:MediaHygieneCloud = $null
    Log ""
    Log "== 18. photos in OneDrive's cloud only, played by offline files (0199)"
    Write-Host "18a. mh audit follows: it should say 3 files of $cloud are in the cloud only. Type N."
    $watch = [Diagnostics.Stopwatch]::StartNew()
    mh audit
    Log ("   18a. mh audit answered N: exit code {0}, {1:N1} s (an audit would take longer)" -f $LASTEXITCODE, $watch.Elapsed.TotalSeconds)
    $line = Read-Host "18a. Did mh say '3 files (... GB) of $cloud are in OneDrive's cloud only' with the free space of $($cloud.Substring(0, 2))? Type what was wrong, or ok"
    Log "   18a. the line: $line"
    Write-Host "18b. mh audit again: no new count, the same question. Type y."
    mh audit | Out-Null
    Log "   18b. mh audit answered y: exit code $LASTEXITCODE"
    Write-Host "18c. mh audit a third time: no question expected."
    mh audit | Out-Null
    $asked = Read-Host "18c. Was the question asked again? (y/n)"
    Log "   18c. asked again after y in the same window (n expected): $asked"
    $said = @(mh folders add $later 6>&1 | ForEach-Object { "$_" })
    foreach ($said1 in $said) { Log ("   18d. mh folders add: " + $said1) }
    $env:OneDrive = $ownOneDrive
    $global:MediaHygieneCloud = $null
    $said = @(mh folders 6>&1 | ForEach-Object { "$_" })
    Log ("   18e. OneDrive put back to your own ({0}); mh folders: {1}" -f $(if ($ownOneDrive) { 'set' } else { 'none' }), ($said -join ' / '))
}

# --- 19: a phone plugged in over USB (MTP), read from PowerShell (0218) ---------------------
# Shell.Application only (a COM object of Windows: no Add-Type, no compilation). Nothing is
# written to the phone but the test files of 19l-19o (0247), after a y: CopyHere copies. Its
# copies go to temporary folders under -Work, removed at the end. The phone must be unlocked,
# in "File transfer" mode.
function PhoneFiles($folder, [int]$depth) {
    foreach ($entry in $folder.Items()) {
        if ($entry.IsFolder) {
            if ($depth -lt 8) { PhoneFiles $entry.GetFolder ($depth + 1) }
        } else {
            $entry
        }
    }
}
function PhoneFindDcim($folder, [int]$depth) {
    foreach ($entry in $folder.Items()) {
        if ($entry.IsFolder) {
            if ($entry.Name -ieq "DCIM") { return $entry }
            if ($depth -lt 3) {
                $found = PhoneFindDcim $entry.GetFolder ($depth + 1)
                if ($found) { return $found }
            }
        }
    }
    return $null
}
# Over MTP, .Size is 0 and .ModifyDate 1899-12-30 (measured 2026-10-19, Android): the real
# values are the extended properties (System.DateModified in UTC).
function PhoneSize($item) {
    $size = $item.ExtendedProperty('System.Size')
    if ($size) { return [int64]$size }
    return [int64]$item.Size
}
function PhoneDate($item) {
    $date = $item.ExtendedProperty('System.DateModified')
    if ($date) { return [datetime]$date }
    return $item.ModifyDate
}
function PhoneWait($item, [string]$folder) {
    $target = Join-Path $folder $item.Name
    $size = PhoneSize $item
    $watch = [Diagnostics.Stopwatch]::StartNew()
    while ($watch.Elapsed.TotalSeconds -lt 60) {
        if (Test-Path -LiteralPath $target) {
            $length = (Get-Item -LiteralPath $target).Length
            if ($length -eq $size -or $size -le 0) { return $watch.Elapsed.TotalSeconds }
        }
        Start-Sleep -Milliseconds 200
    }
    return -1
}
if (Wanted 19) {
    $ErrorActionPreference = "Continue"
    $phoneTmp = Join-Path $Work "phone"
    $shell = New-Object -ComObject Shell.Application
    Log ""
    Log "== 19. a phone over USB, read through Shell.Application (0218)"
    Log "   19. Windows PowerShell $($PSVersionTable.PSVersion), Shell.Application; nothing is written to the phone before 19l"
    Read-Host "19a. Plug the phone in, unlock it (Android: choose File transfer; iPhone: Trust this computer), then press Enter" | Out-Null
    $devices = @()
    $phone = $null
    $dcim = $null
    foreach ($entry in $shell.Namespace(17).Items()) {
        if (-not $entry.IsFileSystem) { $devices += $entry }
    }
    $number = 0
    foreach ($device in $devices) {
        $number++
        Log ("   19a. {0}: name '{1}', Type '{2}', IsFileSystem {3}, IsFolder {4}" -f $number, $device.Name, $device.Type, $device.IsFileSystem, $device.IsFolder)
    }
    if ($devices.Count -eq 0) {
        Log "   19a. no item of This PC without a file system: the phone is not seen (cable, unlock, File transfer?)"
    } else {
        $answer = Read-Host "19a. Number of the phone (1 to $($devices.Count))"
        $phone = $devices[[int]$answer - 1]
        Log "   19a. phone picked: '$($phone.Name)' (Type '$($phone.Type)')"
        $dcim = PhoneFindDcim $phone.GetFolder 0
        for ($try = 1; -not $dcim -and $try -le 3; $try++) {
            # A locked phone, or USB left on "Charging only", shows the phone without its storage.
            $top = @(foreach ($entry in $phone.GetFolder.Items()) { $entry.Name })
            Log ("   19b. try {0}: no DCIM folder within three levels of the phone; it shows: {1}" -f $try, $(if ($top.Count) { $top -join ' / ' } else { '(nothing)' }))
            $again = Read-Host "19b. Unlock the phone, choose File transfer in its USB notification, open it in Explorer until you see DCIM, then press Enter to look again (s to skip the phone)"
            if ($again -eq 's') { break }
            foreach ($entry in $shell.Namespace(17).Items()) {
                if (-not $entry.IsFileSystem -and $entry.Name -eq $phone.Name) { $phone = $entry }
            }
            $dcim = PhoneFindDcim $phone.GetFolder 0
        }
        if (-not $dcim) {
            Log "   19b. no DCIM folder on the phone: 19c-19o skipped (nothing to list, copy or delete)"
        } else {
            Log "   19b. DCIM found: $($dcim.Path)"
            $top = @()
            foreach ($entry in $phone.GetFolder.Items()) { $top += $entry.Name }
            Log "   19b. top folders of the phone: $($top -join ' / ')"
            $watch = [Diagnostics.Stopwatch]::StartNew()
            $all = @(PhoneFiles $dcim.GetFolder 0)
            Log ("   19c. DCIM listed: {0} files in {1:N1} s" -f $all.Count, $watch.Elapsed.TotalSeconds)
            $kinds = $all | ForEach-Object { [IO.Path]::GetExtension($_.Name).ToLower() } | Group-Object | Sort-Object Count -Descending
            Log ("   19c. extensions: " + (($kinds | ForEach-Object { "$($_.Name) x$($_.Count)" }) -join ', '))
            foreach ($item in ($all | Select-Object -First 10)) {
                Log ("   19c. '{0}' Size {1} ModifyDate {2} | System.Size {3} System.DateModified {4} System.DateCreated {5} System.FileName '{6}'" -f $item.Name, $item.Size, $item.ModifyDate, $item.ExtendedProperty('System.Size'), $item.ExtendedProperty('System.DateModified'), $item.ExtendedProperty('System.DateCreated'), $item.ExtendedProperty('System.FileName'))
            }
            $seen = @{}
            $recent = @()
            foreach ($item in ($all | Sort-Object { PhoneDate $_ } -Descending)) {
                if ($recent.Count -ge 20) { break }
                if (-not $seen.ContainsKey($item.Name)) { $seen[$item.Name] = 1; $recent += $item }
            }
            New-Item -ItemType Directory -Force -Path $phoneTmp | Out-Null
            $target = $shell.Namespace($phoneTmp)
            # One round only: copying the same files again opens Windows' "Replace or Skip"
            # dialogs behind the console, flag 16 ignored over MTP (measured 2026-10-19: 386 s for
            # 20 files, twice). mh phone copies into an empty staging folder instead (0219).
            Log "   19f. second copy of the same files: not run (its hidden Replace or Skip dialogs are measured; mh phone avoids them)"
            foreach ($round in 1) {
                $bytes = 0
                $late = 0
                $round1 = [Diagnostics.Stopwatch]::StartNew()
                foreach ($item in $recent) {
                    $target.CopyHere($item, 4 + 16 + 1024)
                    $took = PhoneWait $item $phoneTmp
                    if ($took -lt 0) {
                        $late++
                        Log "   19d$round. never arrived within 60 s: '$($item.Name)' (phone said $(PhoneSize $item) bytes)"
                    } else {
                        $bytes += PhoneSize $item
                        Log ("   19d$round. '{0}' ({1:N1} MB): {2:N1} s" -f $item.Name, ((PhoneSize $item) / 1MB), $took)
                    }
                }
                $seconds = [Math]::Max($round1.Elapsed.TotalSeconds, 0.001)
                Log ("   19d{0}. {1} files asked, {2} missing, {3:N1} MB in {4:N1} s = {5:N2} MB/s" -f $round, $recent.Count, $late, ($bytes / 1MB), $seconds, ($bytes / 1MB / $seconds))
                foreach ($item in ($recent | Select-Object -First 5)) {
                    $copy = Get-Item -LiteralPath (Join-Path $phoneTmp $item.Name) -ErrorAction SilentlyContinue
                    if ($copy) { Log ("   19e. '{0}': phone System.DateModified {1} (UTC), copy modified {2}, copy created {3}" -f $item.Name, (PhoneDate $item), $copy.LastWriteTime, $copy.CreationTime) }
                }
            }
        }
    }
    if (Test-Path -LiteralPath $phoneTmp) { Remove-Item -Recurse -Force -LiteralPath $phoneTmp }
    Log "   19g. temporary copies removed; the phone was only read (CopyHere), nothing deleted, moved or renamed on it"

    # 19h-19k: mh phone end to end (0219), with mh written by the image under test. Its photo
    # folder is an empty test folder: the first run copies every file of DCIM into
    # <that folder>\Phone\<phone name>, the second copies nothing; then the largest copies are
    # removed and copied again while you pull the cable out. All under -Work, removed at the end.
    $answer = if ($dcim) { Read-Host "19h. mh phone copies EVERY photo and video of the phone's DCIM into $Work (see the size in 19c). Run it? (y/n)" } else { 'n' }
    if ($answer -eq 'y') {
        $phoneLibrary = Join-Path $Work "phone-library"
        $mhDir = Join-Path $tool "mh19"
        New-Item -ItemType Directory -Force -Path $phoneLibrary, $mhDir, (Join-Path $tool "config") | Out-Null
        $mhFile = Join-Path $mhDir "mh.ps1"
        $toolMounts = @(
            "-v", "${volume}:/cache",
            "-v", "$(Join-Path $tool 'config'):/config",
            "-v", "$(Join-Path $tool 'journal'):/journal",
            "-v", "$(Join-Path $tool 'quarantine'):/quarantine",
            "-v", "$(Join-Path $tool 'reports'):/reports"
        )
        & docker run --rm -e "MEDIA_HYGIENE_IMAGE=$Image" @toolMounts $Image launcher --photos $phoneLibrary > $mhFile
        . $mhFile
        foreach ($round in 'first', 'second') {
            $watch = [Diagnostics.Stopwatch]::StartNew()
            $said = @(mh phone 6>&1 | ForEach-Object { "$_" })
            $seconds = $watch.Elapsed.TotalSeconds
            foreach ($line in ($said | Where-Object { $_ -notmatch '^\s+\d+/\d+ ' })) { Log ("   19h. $round mh phone: " + $line) }
            Log ("   19h. $round mh phone: {0:N1} s wall time, {1} files copied (lines 'n/m')" -f $seconds, @($said | Where-Object { $_ -match '^\s+\d+/\d+ ' }).Count)
        }
        $copies = @(Get-ChildItem -LiteralPath (Join-Path $phoneLibrary 'Phone') -Recurse -File -Force -ErrorAction SilentlyContinue)
        Log ("   19i. read back: {0} files, {1:N1} MB under {2}\Phone; staging folders left: {3}" -f $copies.Count, (($copies | Measure-Object Length -Sum).Sum / 1MB), $phoneLibrary, @(Get-ChildItem -LiteralPath (Join-Path $phoneLibrary 'Phone') -Recurse -Directory -Force -Filter '.mh-phone-*' -ErrorAction SilentlyContinue).Count)
        foreach ($copy in ($copies | Select-Object -First 3)) { Log ("   19i. '{0}': modified {1}, created {2}" -f $copy.Name, $copy.LastWriteTime, $copy.CreationTime) }
        # Enough to copy for a minute: 5 videos (0.19 GB) took 8.8 s at 29.5 MB/s, too fast to
        # pull the cable in time (measured 2026-10-19). The largest copies up to 2 GB, 5 at least.
        $largest = @()
        $sum = 0
        foreach ($copy in ($copies | Sort-Object Length -Descending)) {
            if ($largest.Count -ge 5 -and $sum -ge 2GB) { break }
            $largest += $copy
            $sum += $copy.Length
        }
        if ($largest.Count -gt 0) {
            foreach ($copy in $largest) { Remove-Item -LiteralPath $copy.FullName -Force }
            Log ("   19j. the {0} largest copies removed ({1:N1} MB): the next mh phone copies them again" -f $largest.Count, (($largest | Measure-Object Length -Sum).Sum / 1MB))
            Read-Host "19j. Next: when the line '2/$($largest.Count)' appears, PULL THE CABLE OUT, then wait (up to 60 s). Press Enter to start" | Out-Null
            $watch = [Diagnostics.Stopwatch]::StartNew()
            # Shown as it comes (the '2/N' line to wait for), and logged after: captured alone,
            # the maintainer saw nothing (2026-10-20).
            $said = @(mh phone 6>&1 | ForEach-Object { $text = "$_"; Write-Host $text; $text })
            foreach ($line in $said) { Log ("   19j. cable pulled: " + $line) }
            Log ("   19j. cable pulled: {0:N1} s wall time; staging folders left: {1}" -f $watch.Elapsed.TotalSeconds, @(Get-ChildItem -LiteralPath (Join-Path $phoneLibrary 'Phone') -Recurse -Directory -Force -Filter '.mh-phone-*' -ErrorAction SilentlyContinue).Count)
            $dialog = Read-Host "19j. Did Windows show any window or question (look with Alt+Tab)? (n or what it said)"
            Log "   19j. a window during the cable pulled (none expected): $dialog"
            Read-Host "19k. Plug the phone in again, unlock it (File transfer), then press Enter" | Out-Null
            $said = @(mh phone 6>&1 | ForEach-Object { "$_" })
            foreach ($line in ($said | Where-Object { $_ -notmatch '^\s+\d+/\d+ ' })) { Log ("   19k. after the cable: " + $line) }
        }
        # A name the phone does not hold: mh gave it _1, _2... (a regex on _<digits> also caught
        # every camera name such as 20250512_195342.jpg: 530 false hits, 2026-10-19).
        $onPhone = @{}
        foreach ($item in $all) {
            $name = "$($item.ExtendedProperty('System.FileName'))"
            $onPhone[$(if ($name) { $name } else { $item.Name })] = 1
        }
        $names = @(Get-ChildItem -LiteralPath (Join-Path $phoneLibrary 'Phone') -Recurse -File -Force -ErrorAction SilentlyContinue | Where-Object { -not $onPhone.ContainsKey($_.Name) })
        Log "   19k. copies under a name the phone does not hold (_1...): $($names.Count) (0 expected: no name was taken)"
        foreach ($copy in ($names | Select-Object -First 5)) { Log "   19k. renamed: $($copy.Name)" }
    } else {
        Log "   19h. mh phone end to end: skipped"
    }

    # 19l-19o: a file deleted on the phone over MTP (0247, for 0248). ONE synthetic test file at
    # a time (a 16x16 grey JPEG made here, never a photo), written into DCIM\mh-measure on the
    # phone, then deleted: InvokeVerb, InvokeVerbEx, MoveHere to the PC, each on its own test
    # file. Every other file of the phone is left alone: DCIM is counted before and after.
    $answer = if ($dcim) { Read-Host "19l. Next: this writes ONE test file to the phone (in DCIM\mh-measure), then deletes it, three ways in turn; no other file of the phone is touched. Go on? (y/n)" } else { 'n' }
    $device = $null
    if ($answer -eq 'y' -and $phone) {
        foreach ($entry in $shell.Namespace(17).Items()) {
            if (-not $entry.IsFileSystem -and $entry.Name -eq $phone.Name) { $device = $entry }
        }
        if (-not $device) { Log "   19l. the phone '$($phone.Name)' is not seen any more (plugged in, unlocked, File transfer?): 19l-19o skipped" }
    } elseif ($answer -eq 'y') {
        Log "   19l. no phone picked in 19a: 19l-19o skipped"
    } else {
        Log "   19l. writing and deleting a test file on the phone: skipped"
    }
    $dcimAgain = if ($device) { PhoneFindDcim $device.GetFolder 0 } else { $null }
    if ($device -and -not $dcimAgain) { Log "   19l. no DCIM folder on the phone any more: 19l-19o skipped" }
    if ($dcimAgain) {
        $jpeg = '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDABALDA4MChAODQ4SERATGCgaGBYWGDEjJR0oOjM9PDkzODdASFxOQERXRTc4UG1RV19iZ2hnPk1xeXBkeFxlZ2P/2wBDARESEhgVGC8aGi9jQjhCY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2P/wAARCAAQABADASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwBv3f8Ad/lTqKb93/d/lS2K+L1P/9k='
        $phoneDelete = Join-Path $Work "phone-delete"
        $phoneMoved = Join-Path $Work "phone-moved"
        New-Item -ItemType Directory -Force -Path $phoneDelete, $phoneMoved | Out-Null
        $dcimFolder = $dcimAgain.GetFolder
        $watch = [Diagnostics.Stopwatch]::StartNew()
        $countBefore = @(PhoneFiles $dcimFolder 0).Count
        Log ("   19l. DCIM before: {0} files (listed in {1:N1} s)" -f $countBefore, $watch.Elapsed.TotalSeconds)
        # PhoneFind: an item of a phone folder by its name (over MTP, Name may lack the
        # extension), or $null once $seconds have passed. PhoneGone: the seconds it took to
        # disappear from the folder, -1 when it is still there after $seconds.
        function PhoneFind($folder, [string]$name, [int]$seconds) {
            $bare = [IO.Path]::GetFileNameWithoutExtension($name)
            $wait = [Diagnostics.Stopwatch]::StartNew()
            do {
                foreach ($entry in $folder.Items()) {
                    if ($entry.Name -eq $name -or $entry.Name -eq $bare -or $entry.ExtendedProperty('System.FileName') -eq $name) { return $entry }
                }
                Start-Sleep -Milliseconds 300
            } while ($wait.Elapsed.TotalSeconds -lt $seconds)
            return $null
        }
        function PhoneGone($folder, [string]$name, [int]$seconds) {
            $wait = [Diagnostics.Stopwatch]::StartNew()
            do {
                if (-not (PhoneFind $folder $name 0)) { return $wait.Elapsed.TotalSeconds }
                Start-Sleep -Milliseconds 300
            } while ($wait.Elapsed.TotalSeconds -lt $seconds)
            return -1
        }
        $watch = [Diagnostics.Stopwatch]::StartNew()
        $dcimFolder.NewFolder('mh-measure')
        $testItem = PhoneFind $dcimFolder 'mh-measure' 30
        Log ("   19l. NewFolder('mh-measure') in DCIM: {0} after {1:N1} s" -f $(if ($testItem) { 'seen' } else { 'NOT seen' }), $watch.Elapsed.TotalSeconds)
        $deleted = @()
        if ($testItem) {
            $testFolder = $testItem.GetFolder
            $number = 0
            $onPhone = $null
            foreach ($way in 'InvokeVerb', 'InvokeVerbEx', 'MoveHere') {
                if (-not $onPhone) {
                    $number++
                    $name = "mh-measure-$stamp-$number.jpg"
                    $local = Join-Path $phoneDelete $name
                    [IO.File]::WriteAllBytes($local, [Convert]::FromBase64String($jpeg))
                    $watch = [Diagnostics.Stopwatch]::StartNew()
                    $testFolder.CopyHere($local, 4 + 16 + 1024)
                    $onPhone = PhoneFind $testFolder $name 60
                    if (-not $onPhone) {
                        Log ("   19l. test file {0} ({1} bytes) NOT seen on the phone within 60 s: 19m stops here" -f $name, (Get-Item -LiteralPath $local).Length)
                        break
                    }
                    Log ("   19l. test file {0} written: seen after {1:N1} s as '{2}', System.Size {3} (local {4} bytes)" -f $name, $watch.Elapsed.TotalSeconds, $onPhone.Name, $onPhone.ExtendedProperty('System.Size'), (Get-Item -LiteralPath $local).Length)
                    if ($number -eq 1) { Log ("   19l. verbs of a phone file: " + ((@($onPhone.Verbs()) | ForEach-Object { $_.Name -replace '&', '' }) -join ' / ')) }
                }
                Log "   19m. $way on $name next: Windows may open a dialog BEHIND this window (look with Alt+Tab); if it asks, answer Yes"
                $watch = [Diagnostics.Stopwatch]::StartNew()
                $failed = ''
                try {
                    if ($way -eq 'InvokeVerb') { $onPhone.InvokeVerb('delete') }
                    elseif ($way -eq 'InvokeVerbEx') { $onPhone.InvokeVerbEx('delete') }
                    else { $shell.Namespace($phoneMoved).MoveHere($onPhone, 4 + 16 + 1024) }
                } catch { $failed = $_.Exception.Message }
                $called = $watch.Elapsed.TotalSeconds
                $gone = PhoneGone $testFolder $name 60
                Log ("   19m. {0}: call returned after {1:N1} s{2}; {3}" -f $way, $called, $(if ($failed) { " with an error: $failed" } else { '' }), $(if ($gone -ge 0) { "gone from the phone after {0:N1} s" -f ($called + $gone) } else { 'STILL on the phone after 60 s' }))
                if ($way -eq 'MoveHere') {
                    $moved = Get-Item -LiteralPath (Join-Path $phoneMoved $name) -ErrorAction SilentlyContinue
                    Log ("   19m. MoveHere: copy on the PC {0}" -f $(if ($moved) { "there, $($moved.Length) bytes" } else { 'NOT there' }))
                }
                $dialog = Read-Host "19m. $way : did Windows show a dialog or question (look with Alt+Tab)? (n or what it said)"
                Log "   19m. $way : dialog: $dialog"
                if ($gone -ge 0) { $deleted += $way; $onPhone = $null }
            }
            if ($onPhone) { Log "   19m. $name is still on the phone (DCIM\mh-measure): delete it by hand in Explorer" }
            # 19n: the test folder removed the first way that worked; DCIM counted again.
            $folderItem = PhoneFind $dcimFolder 'mh-measure' 5
            if ($deleted.Count -gt 0 -and $folderItem -and -not $onPhone) {
                $way = $deleted[0]
                Log "   19n. removing DCIM\mh-measure with ${way}: a dialog may open BEHIND this window (look with Alt+Tab); if it asks, answer Yes"
                $watch = [Diagnostics.Stopwatch]::StartNew()
                try {
                    if ($way -eq 'InvokeVerb') { $folderItem.InvokeVerb('delete') }
                    elseif ($way -eq 'InvokeVerbEx') { $folderItem.InvokeVerbEx('delete') }
                    else { $shell.Namespace($phoneMoved).MoveHere($folderItem, 4 + 16 + 1024) }
                } catch { Log "   19n. $way on the folder: error $($_.Exception.Message)" }
                $gone = PhoneGone $dcimFolder 'mh-measure' 60
                Log ("   19n. DCIM\mh-measure removed with {0}: {1}" -f $way, $(if ($gone -ge 0) { "gone after {0:N1} s" -f ($watch.Elapsed.TotalSeconds) } else { 'STILL there after 60 s: delete it by hand' }))
                $dialog = Read-Host "19n. Did Windows show a dialog or question (look with Alt+Tab)? (n or what it said)"
                Log "   19n. dialog on the folder: $dialog"
            } else {
                Log "   19n. DCIM\mh-measure left on the phone (no way deleted the test file, or it is not empty): delete it by hand in Explorer"
            }
        }
        $after = @(PhoneFiles $dcimFolder 0)
        $left = @($after | Where-Object { $_.Name -like 'mh-measure-*' })
        Log ("   19n. DCIM after: {0} files, before: {1} ({2}); test files left: {3}" -f $after.Count, $countBefore, $(if ($after.Count -eq $countBefore) { 'the same: no other file touched' } else { 'DIFFERENT' }), $left.Count)
        $trash = Read-Host "19n. On the phone, open the Gallery, then its Trash (Recycle bin): is a mh-measure-... picture there? (n or what you see)"
        Log "   19n. phone gallery trash after the deletions over USB: $trash"

        # 19o: the read speed of 0248's proof: the 20 files of 19d copied into an EMPTY folder
        # (no dialog), then the SHA-256 of each.
        $phoneRead = Join-Path $Work "phone-read"
        if (Test-Path -LiteralPath $phoneRead) { Remove-Item -Recurse -Force -LiteralPath $phoneRead }
        New-Item -ItemType Directory -Force -Path $phoneRead | Out-Null
        $names = @{}
        foreach ($item in $recent) { $names[$item.Name] = 1 }
        $again = @($after | Where-Object { $names.ContainsKey($_.Name) } | Select-Object -First 20)
        $target = $shell.Namespace($phoneRead)
        $bytes = 0
        $late = 0
        $watch = [Diagnostics.Stopwatch]::StartNew()
        foreach ($item in $again) {
            $target.CopyHere($item, 4 + 16 + 1024)
            if ((PhoneWait $item $phoneRead) -lt 0) { $late++ } else { $bytes += PhoneSize $item }
        }
        $seconds = [Math]::Max($watch.Elapsed.TotalSeconds, 0.001)
        Log ("   19o. copy into an empty folder: {0} files, {1} missing, {2:N1} MB in {3:N1} s = {4:N2} MB/s" -f $again.Count, $late, ($bytes / 1MB), $seconds, ($bytes / 1MB / $seconds))
        $copies = @(Get-ChildItem -LiteralPath $phoneRead -File)
        $watch = [Diagnostics.Stopwatch]::StartNew()
        foreach ($copy in $copies) { $null = Get-FileHash -LiteralPath $copy.FullName -Algorithm SHA256 }
        $seconds = [Math]::Max($watch.Elapsed.TotalSeconds, 0.001)
        $hashed = ($copies | Measure-Object Length -Sum).Sum
        Log ("   19o. SHA-256 of the copies: {0} files, {1:N1} MB in {2:N1} s = {3:N2} MB/s" -f $copies.Count, ($hashed / 1MB), $seconds, ($hashed / 1MB / $seconds))
        foreach ($folder in $phoneDelete, $phoneMoved, $phoneRead) { Remove-Item -Recurse -Force -LiteralPath $folder -ErrorAction SilentlyContinue }
        Log "   19o. the PC's temporary folders of 19l-19o removed"
    }

    # 19p: mh phone --free end to end (0248), on THREE synthetic test files only (16x16 grey
    # JPEGs made here, a tail of bytes making each one unique), written into DCIM\mh-measure-free
    # on the phone; --only mh-measure-free keeps every other file of the phone out of the import
    # and of the page. A and C are new: imported, then proven and deleted from the phone. B has a
    # twin in the destination with its name and size but another content: kept on the phone.
    $answer = if ($phone) { Read-Host "19p. Next: mh phone --free on 3 test files written to the phone (DCIM\mh-measure-free); no other file of the phone is touched. Go on? (y/n)" } else { 'n' }
    $device = $null
    if ($answer -eq 'y') {
        foreach ($entry in $shell.Namespace(17).Items()) {
            if (-not $entry.IsFileSystem -and $entry.Name -eq $phone.Name) { $device = $entry }
        }
        if (-not $device) { Log "   19p. the phone '$($phone.Name)' is not seen any more: 19p skipped" }
    } else {
        Log "   19p. mh phone --free on test files: skipped"
    }
    $dcimFree = if ($device) { PhoneFindDcim $device.GetFolder 0 } else { $null }
    if ($dcimFree) {
        $jpeg = '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDABALDA4MChAODQ4SERATGCgaGBYWGDEjJR0oOjM9PDkzODdASFxOQERXRTc4UG1RV19iZ2hnPk1xeXBkeFxlZ2P/2wBDARESEhgVGC8aGi9jQjhCY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2P/wAARCAAQABADASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwBv3f8Ad/lTqKb93/d/lS2K+L1P/9k='
        $freeLocal = Join-Path $Work "phone-free-local"
        $freeTo = Join-Path $Work "phone-free"
        $freeAside = Join-Path $Work "phone-free-aside"
        foreach ($folder in $freeLocal, $freeTo, $freeAside) {
            if (Test-Path -LiteralPath $folder) { Remove-Item -Recurse -Force -LiteralPath $folder }
            New-Item -ItemType Directory -Force -Path $folder | Out-Null
        }
        $dcimFolder = $dcimFree.GetFolder
        $countBefore = @(PhoneFiles $dcimFolder 0).Count
        Log "   19p. DCIM before: $countBefore files"
        $dcimFolder.NewFolder('mh-measure-free')
        $testItem = $null
        $watch = [Diagnostics.Stopwatch]::StartNew()
        while (-not $testItem -and $watch.Elapsed.TotalSeconds -lt 30) {
            foreach ($entry in $dcimFolder.Items()) { if ($entry.Name -eq 'mh-measure-free') { $testItem = $entry } }
            if (-not $testItem) { Start-Sleep -Milliseconds 300 }
        }
        if (-not $testItem) { Log "   19p. DCIM\mh-measure-free NOT seen on the phone within 30 s: 19p stops here" }
    }
    if ($dcimFree -and $testItem) {
        $testFolder = $testItem.GetFolder
        $names = @()
        foreach ($letter in 'A', 'B', 'C') {
            $name = "mh-free-$stamp-$letter.jpg"
            $bytes = [Convert]::FromBase64String($jpeg) + [Text.Encoding]::ASCII.GetBytes("mh-measure $stamp $letter")
            [IO.File]::WriteAllBytes((Join-Path $freeLocal $name), [byte[]]$bytes)
            $testFolder.CopyHere((Join-Path $freeLocal $name), 4 + 16 + 1024)
            $names += $name
        }
        $watch = [Diagnostics.Stopwatch]::StartNew()
        while (@($testFolder.Items()).Count -lt 3 -and $watch.Elapsed.TotalSeconds -lt 60) { Start-Sleep -Milliseconds 300 }
        Log ("   19p. test files on the phone: {0} of 3 after {1:N1} s" -f @($testFolder.Items()).Count, $watch.Elapsed.TotalSeconds)
        # B's twin: the destination already holds its name and size, with another content.
        if (-not (Get-Command mh -ErrorAction SilentlyContinue)) {
            $mhDir = Join-Path $tool "mh19"
            New-Item -ItemType Directory -Force -Path $mhDir, (Join-Path $tool "config"), $Work | Out-Null
            $mhFile = Join-Path $mhDir "mh.ps1"
            $toolMounts = @(
                "-v", "${volume}:/cache",
                "-v", "$(Join-Path $tool 'config'):/config",
                "-v", "$(Join-Path $tool 'journal'):/journal",
                "-v", "$(Join-Path $tool 'quarantine'):/quarantine",
                "-v", "$(Join-Path $tool 'reports'):/reports"
            )
            & docker run --rm -e "MEDIA_HYGIENE_IMAGE=$Image" @toolMounts $Image launcher --photos $freeAside > $mhFile
            . $mhFile
        }
        $own = ($phone.Name -replace '[\\/:*?"<>|]', '_').Trim().TrimEnd('.')
        $twinFolder = Join-Path (Join-Path $freeTo $own) 'mh-measure-free'
        New-Item -ItemType Directory -Force -Path $twinFolder | Out-Null
        $twin = [IO.File]::ReadAllBytes((Join-Path $freeLocal $names[1]))
        $twin[$twin.Length - 1] = [byte](($twin[$twin.Length - 1] + 1) % 256)
        [IO.File]::WriteAllBytes((Join-Path $twinFolder $names[1]), $twin)
        Log "   19p. B's twin written in the destination: same name and size, another content"
        Read-Host "19p. Next: a page opens in your browser; leave the ticks as they are (A, B, C), press Delete, confirm. Press Enter to start" | Out-Null
        $watch = [Diagnostics.Stopwatch]::StartNew()
        $said = @(mh phone --to $freeTo --only mh-measure-free --free 6>&1 | ForEach-Object { "$_" })
        $seconds = $watch.Elapsed.TotalSeconds
        foreach ($line in $said) { Log ("   19p. mh phone --free: " + $line) }
        Log ("   19p. mh phone --free: {0:N1} s wall time (the page included)" -f $seconds)
        $dialog = Read-Host "19p. Did Windows show any window or question (look with Alt+Tab)? (n or what it said)"
        Log "   19p. a window during mh phone --free (none expected): $dialog"
        $left = @(foreach ($entry in $testFolder.Items()) { "$($entry.ExtendedProperty('System.FileName'))" })
        Log ("   19p. left on the phone in DCIM\mh-measure-free: {0} (expected: only {1})" -f ($left -join ', '), $names[1])
        $onPc = @(Get-ChildItem -LiteralPath $freeTo -Recurse -File -Force -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName.Substring($freeTo.Length) })
        Log ("   19p. on the PC under {0}: {1}" -f $freeTo, ($onPc -join ', '))
        $tmp = @(Get-ChildItem -LiteralPath $freeTo -Recurse -Directory -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name -like '.mh-*' })
        Log "   19p. staging or moved folders left: $($tmp.Count) (0 expected)"
        foreach ($line in @(mh history 6>&1 | ForEach-Object { "$_" })) { Log ("   19p. mh history: " + $line) }
        # The test files left on the phone, then their folder, moved to the PC (no dialog, 19m).
        foreach ($entry in @($testFolder.Items())) { $shell.Namespace($freeAside).MoveHere($entry, 4 + 16 + 1024) }
        Start-Sleep -Seconds 2
        foreach ($entry in @($dcimFolder.Items())) { if ($entry.Name -eq 'mh-measure-free') { $shell.Namespace($freeAside).MoveHere($entry, 4 + 16 + 1024) } }
        Start-Sleep -Seconds 2
        $countAfter = @(PhoneFiles $dcimFolder 0).Count
        Log ("   19p. DCIM after: {0} files, before: {1} ({2})" -f $countAfter, $countBefore, $(if ($countAfter -eq $countBefore) { 'the same: no other file touched' } else { 'DIFFERENT' }))
        foreach ($folder in $freeLocal, $freeTo, $freeAside) { Remove-Item -Recurse -Force -LiteralPath $folder -ErrorAction SilentlyContinue }
        Log "   19p. the PC's temporary folders of 19p removed"
    }
    # 19q: what Shell.Application shows of a LOCKED phone (0336): Windows lists it by name, but
    # does it show no storage (no item), or an empty storage? Read only, then once unlocked.
    $answer = if ($phone) { Read-Host "19q. Next: lock the phone (screen off), keep it plugged in, wait 10 s, then type y (n skips)" } else { 'n' }
    if ($answer -eq 'y') {
        foreach ($state in 'locked', 'unlocked') {
            if ($state -eq 'unlocked') { $null = Read-Host "19q. Now unlock the phone (File transfer if asked), wait 10 s, then press Enter" }
            $device = $null
            foreach ($entry in $shell.Namespace(17).Items()) {
                if (-not $entry.IsFileSystem -and $entry.Name -eq $phone.Name) { $device = $entry }
            }
            if (-not $device) { Log "   19q. $state`: the phone '$($phone.Name)' is NOT listed in This PC"; continue }
            $tops = @($device.GetFolder.Items())
            Log ("   19q. {0}: listed; {1} top item(s): {2}" -f $state, $tops.Count, (($tops | ForEach-Object { "'$($_.Name)' ($(@($_.GetFolder.Items()).Count) inside)" }) -join ', '))
            $found = PhoneFindDcim $device.GetFolder 0
            Log ("   19q. {0}: DCIM {1}" -f $state, $(if ($found) { 'found' } else { 'NOT found' }))
        }
    } else {
        Log "   19q. a locked phone: skipped"
    }
    # 19r: one read instead of two (0337). 20 synthetic test files (4 MB of random bytes each,
    # never a photo) written to DCIM\mh-measure-speed, then read back twice: CopyHere into one PC
    # folder (the proof's copy of today), then MoveHere into another (today's deletion). Both
    # copies hashed against the originals; DCIM counted before and after.
    $answer = if ($phone) { Read-Host "19r. Next: 20 test files (80 MB, random bytes) written to the phone (DCIM\mh-measure-speed), copied back, then moved back to the PC; no other file of the phone is touched. Go on? (y/n)" } else { 'n' }
    $device = $null
    if ($answer -eq 'y') {
        foreach ($entry in $shell.Namespace(17).Items()) {
            if (-not $entry.IsFileSystem -and $entry.Name -eq $phone.Name) { $device = $entry }
        }
        if (-not $device) { Log "   19r. the phone '$($phone.Name)' is not seen any more: 19r skipped" }
    } else {
        Log "   19r. CopyHere vs MoveHere on 20 test files: skipped"
    }
    $dcimSpeed = if ($device) { PhoneFindDcim $device.GetFolder 0 } else { $null }
    if ($dcimSpeed) {
        $speedLocal = Join-Path $Work "phone-speed-local"
        $speedCopied = Join-Path $Work "phone-speed-copied"
        $speedMoved = Join-Path $Work "phone-speed-moved"
        foreach ($folder in $speedLocal, $speedCopied, $speedMoved) {
            if (Test-Path -LiteralPath $folder) { Remove-Item -Recurse -Force -LiteralPath $folder }
            New-Item -ItemType Directory -Force -Path $folder | Out-Null
        }
        $dcimFolder = $dcimSpeed.GetFolder
        $countBefore = @(PhoneFiles $dcimFolder 0).Count
        Log "   19r. DCIM before: $countBefore files"
        $dcimFolder.NewFolder('mh-measure-speed')
        $speedItem = $null
        $watch = [Diagnostics.Stopwatch]::StartNew()
        while (-not $speedItem -and $watch.Elapsed.TotalSeconds -lt 30) {
            foreach ($entry in $dcimFolder.Items()) { if ($entry.Name -eq 'mh-measure-speed') { $speedItem = $entry } }
            if (-not $speedItem) { Start-Sleep -Milliseconds 300 }
        }
        if (-not $speedItem) { Log "   19r. DCIM\mh-measure-speed NOT seen on the phone within 30 s: 19r stops here" }
    }
    if ($dcimSpeed -and $speedItem) {
        $speedFolder = $speedItem.GetFolder
        $random = New-Object Random
        $originals = @{}
        foreach ($number in 1..20) {
            $name = "mh-speed-$stamp-$number.bin"
            $bytes = New-Object byte[] (4MB)
            $random.NextBytes($bytes)
            $local = Join-Path $speedLocal $name
            [IO.File]::WriteAllBytes($local, $bytes)
            $originals[$name] = (Get-FileHash -LiteralPath $local -Algorithm SHA256).Hash
            $speedFolder.CopyHere($local, 4 + 16 + 1024)
        }
        $watch = [Diagnostics.Stopwatch]::StartNew()
        while (@($speedFolder.Items()).Count -lt 20 -and $watch.Elapsed.TotalSeconds -lt 120) { Start-Sleep -Milliseconds 500 }
        Start-Sleep -Seconds 3
        Log ("   19r. test files on the phone: {0} of 20 after {1:N1} s" -f @($speedFolder.Items()).Count, $watch.Elapsed.TotalSeconds)
        foreach ($way in 'CopyHere', 'MoveHere') {
            $into = if ($way -eq 'CopyHere') { $speedCopied } else { $speedMoved }
            $watch = [Diagnostics.Stopwatch]::StartNew()
            foreach ($entry in @($speedFolder.Items())) {
                if ($way -eq 'CopyHere') { $shell.Namespace($into).CopyHere($entry, 4 + 16 + 1024) }
                else { $shell.Namespace($into).MoveHere($entry, 4 + 16 + 1024) }
            }
            while (@(Get-ChildItem -LiteralPath $into -File).Count -lt 20 -and $watch.Elapsed.TotalSeconds -lt 300) { Start-Sleep -Milliseconds 300 }
            $seconds = $watch.Elapsed.TotalSeconds
            $same = 0
            foreach ($copy in @(Get-ChildItem -LiteralPath $into -File)) {
                if ($originals[$copy.Name] -eq (Get-FileHash -LiteralPath $copy.FullName -Algorithm SHA256).Hash) { $same++ }
            }
            Log ("   19r. {0}: 20 files (80 MB) on the PC after {1:N1} s = {2:N1} MB/s; {3} of 20 equal to their original (SHA-256)" -f $way, $seconds, (80 / $seconds), $same)
        }
        Start-Sleep -Seconds 2
        Log ("   19r. test files left on the phone after MoveHere: {0} (0 expected)" -f @($speedFolder.Items()).Count)
        $dialog = Read-Host "19r. Did Windows show any window or question (look with Alt+Tab)? (n or what it said)"
        Log "   19r. a window during 19r (none expected): $dialog"
        foreach ($entry in @($dcimFolder.Items())) { if ($entry.Name -eq 'mh-measure-speed') { $shell.Namespace($speedMoved).MoveHere($entry, 4 + 16 + 1024) } }
        Start-Sleep -Seconds 2
        $countAfter = @(PhoneFiles $dcimFolder 0).Count
        Log ("   19r. DCIM after: {0} files, before: {1} ({2})" -f $countAfter, $countBefore, $(if ($countAfter -eq $countBefore) { 'the same: no other file touched' } else { 'DIFFERENT' }))
        foreach ($folder in $speedLocal, $speedCopied, $speedMoved) { Remove-Item -Recurse -Force -LiteralPath $folder -ErrorAction SilentlyContinue }
        Log "   19r. the PC's temporary folders of 19r removed"
    }
}

# --- 20: image embeddings, a bench on photos of C:\Photos (0220, for 0221) ------------------
# Downloads the bench (tests/measure/embeddings of the -Branch) under -Work; the models once
# into %TEMP%\mh-measure-results\embeddings-models (2.5 GB, kept for the next runs: delete that
# folder to get the room back); the pages into %TEMP%\mh-measure-results\embeddings-<stamp>. The
# searches come from %TEMP%\mh-measure-results\embeddings-queries.txt: the first time, the step
# writes it with examples and stops, so you write your 20 searches (UTF-8, one per line).
# C:\Photos and the index (-Cache) are mounted read-only; -Sample photos drawn at random.
$benchFiles = @(
    "__init__.py", "embedders.py", "measure.py", "models.py", "pages.py", "ranking.py", "runs.py",
    "templates/base.html", "templates/index.html", "templates/queries.html", "templates/pairs.html"
)
if (Wanted 20) {
    # Native stderr (pip, the ONNX runtime's warnings) must not stop the script in PS 5.1.
    $saved = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $queries = Join-Path $outDir "embeddings-queries.txt"
    if (-not (Test-Path -LiteralPath $queries)) {
        $examples = @(
            "# One search per line, in French, as you would type it; lines starting with # are left out.",
            "# Accents are welcome: keep this file in UTF-8 (Notepad: Save as, Encoding UTF-8).",
            "gateau d'anniversaire",
            "plage au coucher du soleil",
            "neige en montagne"
        )
        Set-Content -LiteralPath $queries -Value $examples -Encoding UTF8
        Log ""
        Log "== 20. image embeddings (0220)"
        Log "   20a. write your 20 searches in $queries (examples inside), then run -Only 20 again"
    } else {
        $bench = Join-Path $Work "embeddings"
        $models = Join-Path $outDir "embeddings-models"
        $pages = Join-Path $outDir "embeddings-$stamp"
        foreach ($folder in $bench, (Join-Path $bench "templates"), $models, $pages) {
            New-Item -ItemType Directory -Force -Path $folder | Out-Null
        }
        $base = "https://raw.githubusercontent.com/cavo789/media-hygiene/$Branch/tests/measure/embeddings"
        foreach ($name in $benchFiles) {
            Invoke-WebRequest -UseBasicParsing -Uri "$base/$name" -OutFile (Join-Path $bench ($name -replace '/', '\'))
        }
        Copy-Item -LiteralPath $queries -Destination (Join-Path $pages "queries.txt")
        $mounts = @(
            "--cpus", "$Cpus",
            "--mount", "type=bind,source=$Photos,target=/data/c/Photos,readonly",
            "--mount", "type=volume,source=$Cache,target=/cache,readonly",
            "--mount", "type=bind,source=$bench,target=/bench/embeddings,readonly",
            "-v", "${models}:/models",
            "-v", "${pages}:/out"
        )
        $inside = "/usr/local/bin/python3 -m pip install -q --no-cache-dir --disable-pip-version-check --target /tmp/wheels tokenizers==0.23.2" +
            " && PYTHONPATH=/tmp/wheels:/bench python -m embeddings.measure --photos /data/c/Photos --queries /out/queries.txt" +
            " --models-dir /models --out /out --count $Sample --cpus $Cpus"
        Log ""
        Log "== 20. image embeddings on $Sample photos of $Photos, $Cpus CPUs (0220)"
        $watch = [Diagnostics.Stopwatch]::StartNew()
        $lines = & docker run --rm @mounts --entrypoint sh $Image -c $inside 2>&1
        $watch.Stop()
        foreach ($line in $lines) { Log ("   " + "$line".Trim()) }
        Log ("   20b. wall time: {0:N1} s, exit code {1}" -f $watch.Elapsed.TotalSeconds, $LASTEXITCODE)
        $size = (Get-ChildItem -LiteralPath $models -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB
        Log ("   20c. models folder: {0:N0} MB in {1}" -f $size, $models)
        Log "   20d. open $(Join-Path $pages 'index.html'), every box starts ticked: untick the misses (searches, then pairs), download both JSON files, then tell Claude where they are"
    }
    $ErrorActionPreference = $saved
}

# --- 21: the Synology NAS by SMB or FTP, from Windows and from Docker, read-only (0246) -------
# For 0245: which of three ways in works. Nothing is written, moved, renamed or deleted on the
# NAS: listings and reads only, Docker mounts with ro, FTP sends no write command. The password
# is asked once, never logged (every line logged has it masked), passed to the container by the
# name of a variable only; the drive, the mapping, the Docker volume and the variable are
# removed in a finally, even after an error.
function NasLog([string]$text) {
    if ($script:nasSecret) { $text = $text.Replace($script:nasSecret, '***') }
    Log $text
}
function NasPort([string]$address, [int]$port) {
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $pending = $client.BeginConnect($address, $port, $null, $null)
        if (-not $pending.AsyncWaitHandle.WaitOne(2000)) { return $false }
        $client.EndConnect($pending)
        return $true
    } catch { return $false } finally { $client.Close() }
}
# Docker runs the probe (python of the image) with the mounts given; its lines logged, masked.
function NasDocker([string]$label, [string[]]$arguments) {
    $said = @(& docker run --rm @arguments 2>&1 | ForEach-Object { "$_" })
    $code = $LASTEXITCODE
    foreach ($line in $said) { if ($line.Trim()) { NasLog ("   ${label}. " + $line.Trim()) } }
    NasLog "   ${label}. exit code $code"
    return @{ Code = $code; Lines = $said }
}
if (Wanted 21) {
    $saved = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    Log ""
    Log "== 21. the NAS by SMB or FTP, from Windows and from Docker, read-only (0246)"
    if ($Nas -eq "") {
        Log "   21. skipped: give -Nas <name or IP address> -NasUser <user> (and -NasShare, default photo)"
    } else {
        $script:nasSecret = ""
        $letter = ""
        $nasVolume = "mh-measure-nas"
        $smbWindows = "not tried (port 445 closed)"
        $smbDocker = "not tried (port 445 closed)"
        $ftpDocker = "not tried (port 21 closed)"
        $nasProbe = Join-Path $Work "nas"
        New-Item -ItemType Directory -Force -Path $nasProbe | Out-Null
        Set-Content -Path (Join-Path $nasProbe "nas_probe.py") -Encoding Ascii -Value @'
import ftplib, os, re, sys, time

# Read-only: listings and reads. FTP sends USER/PASS, then only FEAT, PWD, CWD, MLSD or LIST,
# TYPE, PASV, SIZE, MDTM, REST, RETR, QUIT (no ABOR: a partial read closes its data link).
YEAR = re.compile(r'^(19|20)[0-9][0-9]$')
LIMIT = 2000
CHUNK = 65536
PHOTOS = ('.jpg', '.jpeg', '.heic')


def say(text):
    print(text, flush=True)


def listed():
    try:
        with open('/probe/photos.txt', encoding='utf-8-sig') as handle:
            return [line.strip() for line in handle if line.strip()]
    except OSError:
        return []


def first_year(names):
    # The latest year folder: the earliest may hold a single file (1998, 2026-10-20).
    names = sorted((name for name in names if not name.startswith(('@', '#'))), reverse=True)
    return next((name for name in names if YEAR.match(name)), names[0] if names else '')


def speed(count, size, seconds):
    seconds = max(seconds, 0.001)
    return '%d photos, %.1f MB in %.1f s = %.2f MB/s' % (count, size / 1e6, seconds, size / 1e6 / seconds)


def smb(year):
    root = '/nas'
    tops = [name for name in os.listdir(root) if os.path.isdir(os.path.join(root, name))]
    say('top folders: ' + ' / '.join(sorted(tops)[:30]))
    year = year or first_year(tops)
    start = time.monotonic()
    files, size, skipped, found = 0, 0, 0, []
    for folder, dirs, names in os.walk(os.path.join(root, year)):
        if '@eaDir' in dirs:
            skipped += 1
            dirs.remove('@eaDir')
        dirs.sort()
        for name in sorted(names):
            if files >= LIMIT:
                break
            files += 1
            size += os.path.getsize(os.path.join(folder, name))
            if name.lower().endswith(PHOTOS) and len(found) < 20:
                found.append(os.path.relpath(os.path.join(folder, name), root))
        if files >= LIMIT:
            break
    say('listing of %s: %d files (at most %d), %.1f MB, %d @eaDir skipped, %.1f s' % (year, files, LIMIT, size / 1e6, skipped, time.monotonic() - start))
    chosen = listed() or found
    total, count, start = 0, 0, time.monotonic()
    for relative in chosen[:20]:
        try:
            with open(os.path.join(root, relative.replace('\\', '/')), 'rb') as handle:
                while True:
                    block = handle.read(1 << 20)
                    if not block:
                        break
                    total += len(block)
            count += 1
        except OSError as error:
            say('cannot read %s: %s' % (relative, error))
    say('read whole: ' + speed(count, total, time.monotonic() - start))
    sys.exit(0 if files else 3)


def names_encoding(ftp, mlsd):
    """The NAS's names as bytes: UTF-8, or Latin-1 though FEAT says UTF8 (2026-10-20)."""
    raw = bytearray()
    ftp.retrbinary('MLSD' if mlsd else 'NLST', raw.extend)
    try:
        raw.decode('utf-8')
    except UnicodeDecodeError:
        return 'latin-1'
    return 'utf-8'


def reopen(host, user, home, encoding):
    """A new session in the share: the NAS closes one whose read stopped early (2026-10-20)."""
    ftp = ftplib.FTP(timeout=30)
    ftp.encoding = encoding
    ftp.connect(host, 21)
    ftp.login(user, os.environ.get('MH_NAS_PASSWORD', ''))
    ftp.file = ftp.sock.makefile('r', encoding=encoding)
    ftp.cwd(home)
    ftp.voidcmd('TYPE I')
    return ftp


def partial(ftp, path, rest):
    connection = ftp.transfercmd('RETR ' + path, rest=rest)
    got = 0
    try:
        while got < CHUNK:
            block = connection.recv(CHUNK - got)
            if not block:
                break
            got += len(block)
    finally:
        connection.close()
    try:
        ftp.voidresp()
    except ftplib.all_errors:
        pass
    return got


def walk(ftp, year, mlsd):
    files, skipped, sample, accented = [], 0, '', ''
    queue = [year]
    while queue and len(files) < LIMIT:
        folder = queue.pop(0)
        if mlsd:
            entries = sorted(ftp.mlsd(folder))
            for name, facts in entries:
                kind = facts.get('type', '')
                if not accented and kind in ('dir', 'file') and not name.isascii():
                    accented = name
                if kind == 'dir':
                    if name == '@eaDir':
                        skipped += 1
                    else:
                        queue.append(folder + '/' + name)
                elif kind == 'file' and len(files) < LIMIT:
                    files.append((folder + '/' + name, int(facts.get('size', 0))))
                    sample = sample or '%s %s' % (name, facts)
        else:
            lines = []
            ftp.retrlines('LIST ' + folder, lines.append)
            for line in lines:
                name = line.split(None, 8)[-1]
                sample = sample or line
                if not accented and not name.isascii():
                    accented = name
                if line.startswith('-') and len(files) < LIMIT:
                    files.append((folder + '/' + name, 0))
    return files, skipped, sample, accented


def ftp_probe(host, share, user):
    ftp = ftplib.FTP(timeout=30)
    ftp.encoding = 'utf-8'
    start = time.monotonic()
    say('welcome: ' + ftp.connect(host, 21))
    ftp.login(user, os.environ.get('MH_NAS_PASSWORD', ''))
    say('login: %.1f s' % (time.monotonic() - start))
    try:
        feat = ftp.sendcmd('FEAT').upper()
    except ftplib.error_perm as error:
        feat = ''
        say('FEAT refused: %s' % error)
    offered = {name: name in feat for name in ('MLSD', 'MLST', 'REST STREAM', 'SIZE', 'MDTM', 'UTF8')}
    say('FEAT: ' + ', '.join('%s %s' % (name, 'yes' if on else 'no') for name, on in offered.items()))
    say('PWD at login: ' + ftp.pwd())
    try:
        ftp.cwd(share)
    except ftplib.error_perm:
        try:
            ftp.cwd('/' + share)
        except ftplib.error_perm:
            # The password worked: say the folders there are, not a traceback (2026-10-20).
            names = sorted(name for name, facts in ftp.mlsd() if facts.get('type') == 'dir') if 'MLSD' in feat else ftp.nlst()
            say('no folder %r at the top of the NAS; its folders: %s (run again with -NasShare <one of them>)' % (share, ', '.join(names)))
            ftp.quit()
            return
    say('the share as FTP shows it: ' + ftp.pwd())
    mlsd = offered['MLSD'] or offered['MLST']
    ftp.encoding = names_encoding(ftp, mlsd)
    # The replies too (a path with an accent in a 550 or 150 line): ftplib reads them through a
    # file made at connect time, in UTF-8.
    ftp.file = ftp.sock.makefile('r', encoding=ftp.encoding)
    say('names on the NAS: ' + ('UTF-8' if ftp.encoding == 'utf-8' else 'Latin-1, though FEAT says UTF8'))
    if mlsd:
        tops = [name for name, facts in ftp.mlsd() if facts.get('type') == 'dir']
    else:
        lines = []
        ftp.retrlines('LIST', lines.append)
        tops = [line.split(None, 8)[-1] for line in lines if line.startswith('d')]
    say('top folders: ' + ' / '.join(sorted(tops)[:30]))
    year = first_year(tops)
    start = time.monotonic()
    files, skipped, sample, accented = walk(ftp, year, mlsd)
    say('listing of %s by %s: %d files (at most %d), %d @eaDir skipped, %.1f s' % (year, 'MLSD' if mlsd else 'LIST (this folder only)', len(files), LIMIT, skipped, time.monotonic() - start))
    say('one line: ' + sample)
    say('a name with accents: %s %s' % (accented, ascii(accented)) if accented else 'a name with accents: none in this listing')
    photos = [path for path, _size in files if path.lower().endswith(PHOTOS)]
    ftp.voidcmd('TYPE I')
    if photos:
        say('MDTM of %s: %s' % (photos[0], ftp.sendcmd('MDTM ' + photos[0])))
    home = ftp.pwd()
    start = time.monotonic()
    parts, closed = 0, 0
    for path in photos[:10]:
        size = ftp.size(path) or 0
        for rest in (None, max(size - CHUNK, 0)):
            try:
                partial(ftp, path, rest)
            except (EOFError, *ftplib.all_errors):
                closed += 1
                ftp = reopen(host, user, home, ftp.encoding)
        parts += 1
    say('first and last 64 KiB: %d photos, %.2f s per photo; the NAS closed the session after %d of %d partial reads (a new login each time)' % (parts, (time.monotonic() - start) / max(parts, 1), closed, parts * 2))
    try:
        ftp.close()
    except ftplib.all_errors:
        pass
    ftp = reopen(host, user, home, ftp.encoding)  # the whole reads on a session surely alive
    total, count, start = [0], 0, time.monotonic()
    for path in photos[:20]:
        ftp.retrbinary('RETR ' + path, lambda block: total.__setitem__(0, total[0] + len(block)))
        count += 1
    read = speed(count, total[0], time.monotonic() - start)
    say('read whole: ' + read)
    ftp.quit()
    say('summary: works, MLSD %s, %s' % ('yes' if mlsd else 'no', read))


if sys.argv[1] == 'smb':
    smb(sys.argv[2] if len(sys.argv) > 2 else '')
else:
    ftp_probe(sys.argv[2], sys.argv[3], sys.argv[4])
'@
        try {
            # 21a: the NAS powered on and answering; the PC's adapter on that link.
            Read-Host "21a. Power the NAS on, then press Enter (this script waits up to 3 minutes for it)" | Out-Null
            $watch = [Diagnostics.Stopwatch]::StartNew()
            $up = $false
            while (-not $up -and $watch.Elapsed.TotalSeconds -lt 180) {
                $up = Test-Connection -ComputerName $Nas -Count 1 -Quiet
                if (-not $up) { Start-Sleep -Seconds 10 }
            }
            Log ("   21a. {0} answers: {1}, after {2:N0} s" -f $Nas, $up, $watch.Elapsed.TotalSeconds)
            $ip = "$(@([Net.Dns]::GetHostAddresses($Nas) | Where-Object { $_.AddressFamily -eq 'InterNetwork' })[0])"
            Log "   21a. IPv4 address of the NAS: $ip"
            try {
                $adapter = @(Find-NetRoute -RemoteIPAddress $ip -ErrorAction Stop | Where-Object { $_.IPAddress }) | Select-Object -First 1
                Log ("   21a. PC adapter on that link: '{0}', {1}" -f $adapter.InterfaceAlias, $adapter.IPAddress)
            } catch { Log ("   21a. adapter not found: " + $_.Exception.Message) }

            # 21b: which services answer.
            $open = @{}
            foreach ($port in 21, 445, 139, 22, 5000, 5001) {
                $open[$port] = NasPort $ip $port
                Log ("   21b. port {0}: {1}" -f $port, $(if ($open[$port]) { 'open' } else { 'closed' }))
            }

            # 21c: the password, once, kept in a credential and in this process's environment only.
            # Kept encrypted by Windows for this user on this PC only (Export-Clixml uses DPAPI):
            # asked once, read back next time; deleting the file forgets it.
            $kept = Join-Path $outDir "nas-credential.xml"
            $credential = $null
            if (Test-Path -LiteralPath $kept) {
                try { $credential = Import-Clixml -LiteralPath $kept } catch { $credential = $null }
                if ($credential -and $NasUser -ne "" -and $credential.UserName -ne $NasUser) { $credential = $null }
                if ($credential) { Log "   21c. password read back from $kept (delete it to forget it)" }
            }
            if (-not $credential) {
                if ($NasUser -eq "") { $NasUser = Read-Host "21c. User name on the NAS" }
                $secure = Read-Host "21c. Password of $NasUser on the NAS (never logged)" -AsSecureString
                $credential = New-Object System.Management.Automation.PSCredential($NasUser, $secure)
                if ((Read-Host "21c. Keep it, encrypted for your Windows account, in $kept? (y/n)") -match '^y') {
                    $credential | Export-Clixml -LiteralPath $kept
                    Log "   21c. password kept in $kept (encrypted for this Windows user; delete the file to forget it)"
                }
            }
            $NasUser = $credential.UserName
            $script:nasSecret = $credential.GetNetworkCredential().Password
            $env:MH_NAS_PASSWORD = $script:nasSecret

            $yearName = ""
            if ($open[445]) {
                # 21d: SMB from Windows, a drive letter mapped by the credential (no password on
                # a command line); the same letter is given to Docker in 21e.
                try {
                    $letter = @(foreach ($l in 'Z', 'Y', 'X', 'W', 'V', 'U', 'T', 'S', 'R', 'Q', 'P') { if (-not (Test-Path -LiteralPath "${l}:\")) { $l } })[0]
                    $null = New-PSDrive -Name $letter -PSProvider FileSystem -Root "\\$ip\$NasShare" -Credential $credential -Persist -Scope Global -ErrorAction Stop
                    $root = "${letter}:\"
                    Log "   21d. \\$ip\$NasShare mapped on ${letter}: (this logon only, removed at the end)"
                    $shares = @(net view "\\$ip" /all 2>&1 | ForEach-Object { "$_".Trim() } | Where-Object { $_ -match '\sDisk' })
                    Log ("   21d. net view: " + ($shares -join ' / '))
                    $tops = @([IO.Directory]::GetDirectories($root) | ForEach-Object { [IO.Path]::GetFileName($_) } | Sort-Object)
                    Log ("   21d. top folders: " + (($tops | Select-Object -First 30) -join ' / '))
                    # The latest year folder: the earliest may hold a single file (1998, 2026-10-20).
                    $yearName = @($tops | Where-Object { $_ -match '^(19|20)\d\d$' } | Sort-Object -Descending)[0]
                    if (-not $yearName) { $yearName = @($tops | Where-Object { $_ -notmatch '^[@#]' })[0] }
                    # At most 2,000 files below the first year folder, @eaDir (thumbnails) skipped.
                    $queue = New-Object System.Collections.Queue
                    $queue.Enqueue((Join-Path $root $yearName))
                    $files = New-Object System.Collections.ArrayList
                    $eaDirs = 0
                    $watch = [Diagnostics.Stopwatch]::StartNew()
                    while ($queue.Count -gt 0 -and $files.Count -lt 2000) {
                        $folder = New-Object IO.DirectoryInfo ($queue.Dequeue())
                        foreach ($sub in ($folder.GetDirectories() | Sort-Object Name)) {
                            if ($sub.Name -eq '@eaDir') { $eaDirs++ } else { $queue.Enqueue($sub.FullName) }
                        }
                        foreach ($file in ($folder.GetFiles() | Sort-Object Name)) { if ($files.Count -lt 2000) { $null = $files.Add($file) } }
                    }
                    $listed = $watch.Elapsed.TotalSeconds
                    $bytes = ($files | Measure-Object -Property Length -Sum).Sum
                    Log ("   21d. listing of {0}: {1} files (at most 2000), {2:N1} MB, {3} @eaDir skipped, {4:N1} s" -f $yearName, $files.Count, ($bytes / 1MB), $eaDirs, $listed)
                    # 20 photos read whole into memory: nothing copied to disk. Not $photos: PowerShell names
                    # ignore case, and the [string] -Photos parameter turned the list into a string.
                    $nasPhotos = @($files | Where-Object { $_ -and $_.FullName -and $_.Extension -match '^\.(jpe?g|heic)$' } | Select-Object -First 20)
                    $buffer = New-Object byte[] 1048576
                    $read = 0
                    $watch = [Diagnostics.Stopwatch]::StartNew()
                    foreach ($nasPhoto in $nasPhotos) {
                        $stream = [IO.File]::OpenRead($nasPhoto.FullName)
                        try { while (($count = $stream.Read($buffer, 0, $buffer.Length)) -gt 0) { $read += $count } } finally { $stream.Close() }
                    }
                    $seconds = [Math]::Max($watch.Elapsed.TotalSeconds, 0.001)
                    $speed = "{0} photos, {1:N1} MB in {2:N1} s = {3:N2} MB/s" -f $nasPhotos.Count, ($read / 1MB), $seconds, ($read / 1MB / $seconds)
                    Log "   21d. read whole: $speed"
                    # The same photos for the container (21e, 21f), relative to the share.
                    $relative = @($nasPhotos | ForEach-Object { $_.FullName.Substring($root.Length).Replace('\', '/') })
                    [IO.File]::WriteAllLines((Join-Path $nasProbe "photos.txt"), [string[]]$relative)
                    $smbWindows = "works, listing {0} files in {1:N1} s, read {2}" -f $files.Count, $listed, $speed
                } catch {
                    $smbWindows = "does not work: " + $_.Exception.Message
                    NasLog "   21d. SMB from Windows: $smbWindows"
                }

                # 21e: Docker given the mapped drive letter, read-only.
                $smbDocker = "does not work"
                if ($letter -ne "" -and (Test-Path -LiteralPath "${letter}:\")) {
                    $run = NasDocker "21e" @("-v", "${letter}:\:/nas:ro", "-v", "${nasProbe}:/probe:ro", "--entrypoint", "python", $Image, "/probe/nas_probe.py", "smb", $yearName)
                    if ($run.Code -eq 0) { $smbDocker = "works with the drive letter ${letter}:" }
                }
                # 21f: a Docker CIFS volume, read-only; SMB 3.0, else 2.1, 2.0, 1.0. The volume keeps the
                # password in its options: removed right after, and in the finally.
                if ($script:nasSecret -match '[,"]') {
                    Log "   21f. skipped: the password holds a comma or a double quote, which the CIFS options cannot carry"
                } else {
                    # An older NAS may speak 2.0 or 1.0 only: 3.0 and 2.1 were refused (2026-10-20).
                    foreach ($version in '3.1.1,sec=ntlmssp', '3.0', '3.0,sec=ntlmssp', '2.1', '2.0', '1.0') {
                        & docker volume rm -f $nasVolume 2>&1 | Out-Null
                        $made = @(& docker volume create --driver local --opt type=cifs --opt "device=//$ip/$NasShare" --opt "o=addr=$ip,username=$NasUser,password=$($script:nasSecret),ro,vers=$version" $nasVolume 2>&1 | ForEach-Object { "$_" })
                        if ($LASTEXITCODE -ne 0) { NasLog ("   21f. vers=${version}: volume refused: " + ($made -join ' / ')); continue }
                        $run = NasDocker "21f vers=$version" @("-v", "${nasVolume}:/nas:ro", "-v", "${nasProbe}:/probe:ro", "--entrypoint", "python", $Image, "/probe/nas_probe.py", "smb", $yearName)
                        & docker volume rm -f $nasVolume 2>&1 | Out-Null
                        # The kernel's own reason ('Dialect not supported', 'Permission denied'...).
                        $why = @(& wsl.exe -d docker-desktop sh -c "dmesg | grep -i cifs | tail -n 3" 2>$null | ForEach-Object { "$_".Trim() } | Where-Object { $_ })
                        if ($run.Code -ne 0 -and $why) { NasLog ("   21f vers=${version}. kernel says: " + ($why -join ' / ')) }
                        if ($run.Code -eq 0) {
                            $smbDocker = if ($smbDocker -like 'works*') { "$smbDocker; and with a CIFS volume, vers=$version" } else { "works with a CIFS volume, vers=$version" }
                            break
                        }
                    }
                }
            }

            # 21g: FTP from the container, passive mode, read commands only.
            if ($open[21]) {
                $run = NasDocker "21g" @("-e", "MH_NAS_PASSWORD", "-v", "${nasProbe}:/probe:ro", "--entrypoint", "python", $Image, "/probe/nas_probe.py", "ftp", $ip, $NasShare, $NasUser)
                $summary = @($run.Lines | Where-Object { $_ -match '^summary: ' })
                $ftpDocker = if ($run.Code -eq 0 -and $summary.Count -gt 0) { $summary[0].Substring(9) } else { "does not work (see 21g)" }
            }
        } catch {
            NasLog ("   21. stopped: " + $_.Exception.Message)
        } finally {
            if ($letter -ne "") {
                Remove-PSDrive -Name $letter -Force -ErrorAction SilentlyContinue
                & net use "${letter}:" /delete /y 2>&1 | Out-Null
            }
            & docker volume rm -f $nasVolume 2>&1 | Out-Null
            Remove-Item -Path Env:\MH_NAS_PASSWORD -ErrorAction SilentlyContinue
            NasLog "   21. cleaned up: mapped drive, Docker volume and password variable removed; nothing was written on the NAS"
            $script:nasSecret = ""
        }
        NasLog "   21. SMB in Docker: $smbDocker"
        NasLog "   21. SMB in Windows: $smbWindows"
        NasLog "   21. FTP in Docker: $ftpDocker"

        # 21h (0245): the NAS as mh's backup in a test mh: added once (user name and password
        # asked, kept or not), listed, then an audit with it. Never an import here: the test
        # folder holds one photo, so nearly the whole NAS would be proposed.
        $unc = "\\$Nas\$NasShare"
        $go = Read-Host "21h. Try 'mh folders add --backup $unc' in a test mh (it asks the user name, the password, then whether to keep it), then 'mh audit' with it? (y/n)"
        if ($go -match '^y') {
            $mhDir = Join-Path $tool "mh21"
            New-Item -ItemType Directory -Force -Path $mhDir, (Join-Path $tool "config") | Out-Null
            $mhFile = Join-Path $mhDir "mh.ps1"
            $toolMounts = @(
                "-v", "${volume}:/cache",
                "-v", "$(Join-Path $tool 'config'):/config",
                "-v", "$(Join-Path $tool 'journal'):/journal",
                "-v", "$(Join-Path $tool 'quarantine'):/quarantine",
                "-v", "$(Join-Path $tool 'reports'):/reports"
            )
            & docker run --rm -e "MEDIA_HYGIENE_IMAGE=$Image" @toolMounts $Image launcher --photos $data > $mhFile
            . $mhFile
            mh folders add --backup $unc
            Log ("   21h. mh.ps1 names the share: " + [bool](Select-String -LiteralPath $mhFile -SimpleMatch -Pattern $unc -Quiet))
            $said = @(mh folders 6>&1 | ForEach-Object { "$_" })
            foreach ($line in $said) { Log ("   21h. mh folders: " + $line) }
            $watch = [Diagnostics.Stopwatch]::StartNew()
            $said = @(mh audit 2>&1 | ForEach-Object { "$_".Trim() } | Where-Object { $_ -match 'only in it|not in this backup|set aside or deleted|does not answer|could not be read|refused|Media files scanned' })
            foreach ($line in $said) { Log ("   21h. mh audit: " + $line) }
            Log ("   21h. mh audit with the NAS: {0:N1} s, exit code {1}" -f $watch.Elapsed.TotalSeconds, $LASTEXITCODE)
            Log ("   21h. Docker volumes of the NAS left after it (none expected): " + ((@(& docker volume ls -q --filter name=mh-nas-) -join ' / ') -replace '^$', 'none'))
            $kept = Join-Path $mhHome ('nas-' + (("$Nas-$NasShare") -replace '[^A-Za-z0-9._-]+', '-').Trim('-') + '.xml')
            Log "   21h. password kept by mh: $(Test-Path -LiteralPath $kept)"
            $null = @(mh folders remove $unc 6>&1)
            Log "   21h. after mh folders remove: password file left: $(Test-Path -LiteralPath $kept)"
        }
    }
    $ErrorActionPreference = $saved
}

# --- 22: a pair keeping both names: each copy a hard link (0213) ----------------------------
if (Wanted 22) {
    Log ""
    Log "== 22. a folder pair keeping both names (links), through Docker Desktop (0213)"
    $links = Join-Path $Work "links"
    foreach ($folder in "Best of", "2019-07") {
        New-Item -ItemType Directory -Force -Path (Join-Path $links $folder) | Out-Null
    }
    foreach ($photo in ($picked | Select-Object -First 3)) {
        Copy-Item -LiteralPath $photo.FullName -Destination (Join-Path $links "Best of\$($photo.Name)")
        Copy-Item -LiteralPath $photo.FullName -Destination (Join-Path $links "2019-07\$($photo.Name)")
    }
    $linkMounts = @(
        "-v", "${links}:/data/c/mh-measure-22",
        "-v", "${volume}:/cache",
        "-v", "$(Join-Path $tool 'journal'):/journal",
        "-v", "$(Join-Path $tool 'quarantine'):/quarantine",
        "-v", "$(Join-Path $tool 'reports'):/reports"
    )
    $saved = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & docker run --rm --env COLUMNS=160 @linkMounts $Image --locale en audit 2>&1 | Out-Null
    $report = Get-ChildItem -Path (Join-Path $tool "reports") -Recurse -Filter "report.html" |
        Where-Object { $_.Directory.Name -like "*-audit" } |
        Sort-Object LastWriteTime | Select-Object -Last 1
    $page = [IO.File]::ReadAllText($report.FullName)
    $pattern = '<select class="decision" data-kept-in="([^"]*)" data-removed-from="([^"]*)"[^>]*>([\s\S]*?)</select>'
    $pair = [regex]::Matches($page, $pattern) | Where-Object { $_.Groups[3].Value -match 'value="link"' } |
        Select-Object -First 1
    if (-not $pair) {
        Log "   22. stopped: the report offers no pair to link (see $($report.FullName))"
    } else {
        $kept = [Net.WebUtility]::HtmlDecode($pair.Groups[1].Value)
        $removed = [Net.WebUtility]::HtmlDecode($pair.Groups[2].Value)
        $roots = [regex]::Match($page, 'const roots = (.*);').Groups[1].Value
        $quote = { param($text) '"' + $text.Replace('\', '\\').Replace('"', '\"') + '"' }
        $json = '{"version": 1, "roots": ' + $roots + ', "pairs": [{"kept_in": ' + (& $quote $kept) +
            ', "removed_from": ' + (& $quote $removed) + ', "action": "link"}]}'
        [IO.File]::WriteAllText((Join-Path $tool "reports\decisions.json"), $json)
        $copiesFolder = if ($removed.EndsWith("Best of")) { "Best of" } else { "2019-07" }
        $keptFolder = if ($copiesFolder -eq "Best of") { "2019-07" } else { "Best of" }
        Log "   22. pair: kept in $kept, linked in $removed"
        $before = (Get-PSDrive C).Free
        $lines = & docker run --rm --env COLUMNS=160 @linkMounts $Image --locale en clean --yes --decisions decisions.json 2>&1
        foreach ($line in $lines) {
            $text = "$line"
            if ($text -match 'link|names|Files processed|Skipped|Failed|Error') { Log ("   " + $text.Trim()) }
        }
        $after = (Get-PSDrive C).Free
        Log ("   22a. C: free space: {0:N0} bytes before, {1:N0} after (+{2:N0}; the copies weigh {3:N0})" -f
            $before, $after, ($after - $before),
            ((Get-ChildItem -LiteralPath (Join-Path $links $copiesFolder) -File | Measure-Object -Property Length -Sum).Sum))
        foreach ($file in Get-ChildItem -LiteralPath (Join-Path $links $copiesFolder) -File) {
            $names = @(& fsutil hardlink list $file.FullName 2>&1)
            $twin = Join-Path (Join-Path $links $keptFolder) $file.Name
            $same = (Get-FileHash -LiteralPath $file.FullName).Hash -eq (Get-FileHash -LiteralPath $twin).Hash
            Log ("   22b. {0}: {1} name(s) [{2}], same bytes as its twin: {3}" -f $file.Name, $names.Count, ($names -join " | "), $same)
        }
        $first = Get-ChildItem -LiteralPath (Join-Path $links $copiesFolder) -File | Select-Object -First 1
        $twin = Join-Path (Join-Path $links $keptFolder) $first.Name
        Write-Host ""
        Write-Host "22c. Open $(Join-Path $links $copiesFolder) and $(Join-Path $links $keptFolder) in Explorer."
        $seen = Read-Host "Do both folders show the photos, and do both open? (y/n, then any remark)"
        Log "   22c. Explorer shows both, both open: $seen"
        $hashBefore = (Get-FileHash -LiteralPath $twin).Hash
        Write-Host "22d. Open $($first.FullName) in the Photos app, rotate or edit it, and SAVE it (not 'Save a copy')."
        Read-Host "Press Enter once it is saved and Photos is closed" | Out-Null
        $edited = (Get-FileHash -LiteralPath $first.FullName).Hash
        $twinNow = (Get-FileHash -LiteralPath $twin).Hash
        $names = @(& fsutil hardlink list $first.FullName 2>&1)
        Log ("   22d. after the edit in Photos: the edited name changed: {0}; its twin {1} changed too: {2}; names now: {3}" -f
            ($edited -ne $hashBefore), $first.Name, ($twinNow -ne $hashBefore), ($names -join " | "))
        $lines = & docker run --rm --env COLUMNS=160 @linkMounts $Image --locale en undo --yes 2>&1
        foreach ($line in $lines) {
            $text = "$line"
            if ($text -match 'Files processed|Skipped|Failed|Error|independent|no longer') { Log ("   " + $text.Trim()) }
        }
        foreach ($file in Get-ChildItem -LiteralPath (Join-Path $links $copiesFolder) -File) {
            $names = @(& fsutil hardlink list $file.FullName 2>&1)
            Log ("   22e. after undo, {0}: {1} name(s), modified {2}" -f $file.Name, $names.Count, $file.LastWriteTime.ToString("s"))
        }
    }
    $ErrorActionPreference = $saved
}

# --- 23: the home page of your own mh, timed (0277) ------------------------------------------
# Blank for about 45 s, then slow clicks (2026-10-20). Read-only: the state is read, as the page does.
if (Wanted 23) {
    $saved = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    Log ""
    Log "== 23. the home page of your own mh, timed (0277)"
    Write-Host "23: open Windows PowerShell as you usually do, type mh, Enter."
    Write-Host "    Wait until the home page shows in the browser (time it if you can), then come back here."
    $seen = Read-Host "23. Seconds between Enter and the page shown (your estimate, empty if unknown)"
    Log "   23a. estimated by you: $seen s from mh to the page shown"
    $page = @(& docker ps --quiet --filter "label=media-hygiene.page")
    if ($page.Count -eq 0) {
        Log "   23a. no home page container running (label media-hygiene.page): step skipped"
    } else {
        $id = $page[0]
        $port = "8088"
        $mapped = "$(& docker port $id 2>$null)"
        if ($mapped -match ':(\d+)\s*$') { $port = $Matches[1] }
        # Inside the container: its own mounts and settings, each part of home_state() timed.
        $code = @'
import os, socket, time
from media_hygiene.i18n import install
from media_hygiene.i18n.bootstrap import resolve_locale
install(resolve_locale([]))
from media_hygiene.cli.context import build_runtime
import media_hygiene.cli.home_state as hs
import media_hygiene.services.status as st
runtime = build_runtime({})
spent = {}
for name in ('load_summaries', 'list_run_ids', 'summarize', 'can_undo', 'last_walk', 'mounted_quarantines',
             'quarantine_state', 'review_state', 'sort_state', 'face_coverage', 'tag_coverage'):
    if not hasattr(st, name):
        continue
    def inner(*args, _f=getattr(st, name), _n='status.' + name, **kwargs):
        start = time.perf_counter()
        result = _f(*args, **kwargs)
        spent[_n] = spent.get(_n, 0.0) + time.perf_counter() - start
        return result
    setattr(st, name, inner)
names = ('read_status', 'windows_menu', 'build_menu', 'full_catalog', 'home_update', 'home_folders',
         'latest_reports', 'audit_previews', 'status_lines', 'home_spaces', 'home_actions', 'home_next',
         'home_tiles', 'home_findings', 'home_quarantine', 'home_undo', 'next_step')
for name in names:
    def timed(*args, _f=getattr(hs, name), _n=name, **kwargs):
        start = time.perf_counter()
        result = _f(*args, **kwargs)
        spent[_n] = spent.get(_n, 0.0) + time.perf_counter() - start
        return result
    setattr(hs, name, timed)
for run in (1, 2):
    spent.clear()
    start = time.perf_counter()
    hs.home_state(runtime)
    total = (time.perf_counter() - start) * 1000
    parts = ', '.join(f'{n} {s * 1000:.0f}' for n, s in sorted(spent.items(), key=lambda x: -x[1])[:10])
    print(f'23c. home_state run {run}: {total:.0f} ms ({parts})')
start = time.perf_counter()
try:
    socket.getaddrinfo('hub.docker.com', 443)
    found = 'resolved'
except OSError as error:
    found = f'failed: {error}'
print(f'23d. DNS of hub.docker.com: {(time.perf_counter() - start) * 1000:.0f} ms, {found}')
for root in ('/journal', '/quarantine', '/reports', '/cache'):
    start = time.perf_counter()
    count = sum(len(files) for _, _, files in os.walk(root))
    print(f'23e. {root}: {count} files, listed in {(time.perf_counter() - start) * 1000:.0f} ms')
'@
        $encoded = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($code))
        $lines = & docker exec $id python -c "import base64; exec(base64.b64decode('$encoded'))" 2>&1
        foreach ($line in $lines) { Log ("   " + "$line".Trim()) }
        # Then from Windows, as the browser asks (the old image reads the state for / too).
        foreach ($path in "/", "/api/state") {
            $watch = [Diagnostics.Stopwatch]::StartNew()
            try {
                $answer = Invoke-WebRequest -Uri "http://127.0.0.1:$port$path" -UseBasicParsing -TimeoutSec 300
                $watch.Stop()
                Log ("   23b. GET {0}: {1:N2} s, {2} bytes" -f $path, $watch.Elapsed.TotalSeconds, $answer.RawContentLength)
            } catch {
                Log ("   23b. GET {0}: failed after {1:N2} s: {2}" -f $path, $watch.Elapsed.TotalSeconds, $_.Exception.Message)
            }
        }
        Write-Host "23: you may close the home page now (Ctrl+C in its PowerShell window)."
    }
    # Each step chosen on the page is one docker run for the step, then one for the page again.
    foreach ($try in 1, 2) {
        $watch = [Diagnostics.Stopwatch]::StartNew()
        & docker run --rm $Image --version 2>&1 | Out-Null
        $watch.Stop()
        Log ("   23f. an empty docker run of {0} (try {1}): {2:N2} s" -f $Image, $try, $watch.Elapsed.TotalSeconds)
    }
    $ErrorActionPreference = $saved
}

# --- 24: search by meaning on C:\Photos, with your usual cache (0263) ----------------------
# The vectors and the model stay in your cache: the next tags --meaning only looks at new
# photos, and search uses them. Ctrl+C keeps what is done.
if (Wanted 24) {
    Measure-Mh "24a. C:\Photos, tags --meaning (model downloaded once, then each photo)" $real @("tags", "--no-describe", "--meaning")
    Measure-Mh "24b. the same again: nothing left to look at" $real @("tags", "--no-describe", "--meaning")
    Measure-Mh "24c. search by meaning, the text model loaded" $real @("search", "--limit", "5", "une plage")
}

# --- 25: mh.ps1 written again after loading: the line of the stale check (0276) -------------
# A copy of mh.ps1 under -Work is loaded, written again, and `mh version` run: the line must show;
# after loading it again, and after removing the file, it must not. Your own mh is put back.
if (Wanted 25) {
    $saved = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    Log ""
    Log "== 25. mh.ps1 written again after loading (0276)"
    $folder = Join-Path $Work "stale"
    New-Item -ItemType Directory -Force -Path $folder | Out-Null
    $copy = Join-Path $folder "mh.ps1"
    $lines = @(& docker run --rm $Image launcher --shell powershell --photos $data 2>$null)
    Set-Content -LiteralPath $copy -Value $lines -Encoding Ascii
    . $copy
    $first = @(mh version 2>&1 | ForEach-Object { "$_" })
    Log ("   25a. loaded, not written again: line said = {0} (expected False)" -f [bool]($first -match 'changed on disk'))
    Add-Content -LiteralPath $copy -Value "# written again" -Encoding Ascii
    $watch = [Diagnostics.Stopwatch]::StartNew()
    $second = @(mh version 2>&1 | ForEach-Object { "$_" })
    $watch.Stop()
    Log ("   25b. written again: line said = {0} (expected True), the whole mh version call took {1:N2} s" -f [bool]($second -match 'changed on disk'), $watch.Elapsed.TotalSeconds)
    Log ("   25b. the line: {0}" -f (($second | Where-Object { $_ -match 'changed on disk' }) -join ' / '))
    . $copy
    $third = @(mh version 2>&1 | ForEach-Object { "$_" })
    Log ("   25c. loaded again: line said = {0} (expected False)" -f [bool]($third -match 'changed on disk'))
    Add-Content -LiteralPath $copy -Value "# and again" -Encoding Ascii
    Remove-Item -LiteralPath $copy -Force
    $fourth = @(mh version 2>&1 | ForEach-Object { "$_" })
    Log ("   25d. file removed: line said = {0} (expected False), mh still ran = {1}" -f [bool]($fourth -match 'changed on disk'), [bool]($fourth.Count -gt 0))
    $ErrorActionPreference = $saved
}

# --- 26: the shortcut's window minimised, a console step brought forward (0284, 0285) ---------
# Your own mh, by hand: it rewrites your Desktop and Start menu shortcut (as mh shortcut does).
# The bell, AppActivate and the minimised shortcut live in mh.ps1, not in the image: a local
# build never rewrites mh.ps1 (mh update: nothing to pull), so an older file is rewritten
# first, by its own _mh_rewrite: same folders, same image (2026-10-21: run on an older file).
if (Wanted 26) {
    Log ""
    Log "== 26. the shortcut's window minimised, a console step brought forward (0284, 0285)"
    $own = Join-Path $mhHome "mh.ps1"
    $fresh = (Test-Path -LiteralPath $own) -and (Select-String -LiteralPath $own -Pattern '_mh_forward' -SimpleMatch -Quiet)
    if ((Test-Path -LiteralPath $own) -and -not $fresh) {
        . $own
        $null = _mh_rewrite @(_mh_photos) @(_mh_backups)
        $fresh = [bool](Select-String -LiteralPath $own -Pattern '_mh_forward' -SimpleMatch -Quiet)
        Log "   26: $own was older than 0285: rewritten with its folders, now holds the bell = $fresh"
    } else {
        Log "   26: $own holds the bell of 0285 = $fresh"
    }
    if (-not $fresh) {
        Log "   26: skipped: write your mh with the launcher line of the image $Image first (its image may be another one)"
    }
}
if ((Wanted 26) -and $fresh) {
    Write-Host "26: open a NEW Windows PowerShell window (it loads the mh just written), type: mh shortcut"
    Write-Host "    Close that window. Double-click the Media Hygiene icon of the Desktop."
    $minimised = Read-Host "26a. The PowerShell window started minimised in the taskbar? (y/n)"
    $line = Read-Host "26b. In it (click its button): 'Keep this window open (minimised is fine)...'? (y/n)"
    Write-Host "    Windows Terminal: Settings, Open JSON file; in profiles, defaults, add"
    Write-Host '        "bellStyle": "taskbar",'
    Write-Host "    save. Then minimise the mh window (or tab away from it). On the home page, Run 'clean'."
    Write-Host "    The bell rings before the step, whether it asks or not ('Nothing to clean' is fine)."
    $bold = Read-Host "26c. The page showed at once, in bold, 'Switch to ... now'? (y/n)"
    $min = Read-Host "26d. Window minimised: it came forward (f), its taskbar button flashed (b), or nothing (n)?"
    Write-Host "    If clean asks, answer n. When the page is back, leave the window open (not minimised),"
    Write-Host "    click on the browser, then Run 'clean' again."
    $normal = Read-Host "26e. Window open behind the browser: forward (f), button flashed (b), or nothing (n)?"
    Write-Host "    If it asks, answer n. When the page is back, close the PowerShell window (its X), look at the page."
    $stop = Read-Host "26f. The page showed 'Media Hygiene is stopped' within about 10 s, by itself? (y/n)"
    Log "   26: minimised $minimised, keep-open line $line, bold line $bold, console step minimised $min, normal $normal, stop shown $stop"
}

# --- 27: mh push, Windows writing to the NAS (0264) ----------------------------------------
# Writes ONLY below \\<Nas>\<NasTarget>\mh-measure-test, removed at the end. The password is
# asked once (or read back from step 21's kept credential), never logged.
if (Wanted 27) {
    $saved = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    Log ""
    Log "== 27. mh push: Windows writes to the NAS (0264)"
    if ($Nas -eq "") {
        Log "   27. skipped: give -Nas <name or IP address> -NasTarget <shared folder of its own> -NasUser <user>"
    } else {
        $share = "\\$Nas\$NasTarget"
        $test = Join-Path $share "mh-measure-test"
        $credFile = Join-Path $outDir "nas-credential.xml"
        $nasCred = $null
        if (Test-Path -LiteralPath $credFile) { try { $nasCred = Import-Clixml -LiteralPath $credFile } catch { } }
        if (-not $nasCred) {
            if ($NasUser -eq "") { $NasUser = Read-Host "27. User name on the NAS" }
            $secure = Read-Host "27. Password of $NasUser on the NAS (never logged)" -AsSecureString
            $nasCred = New-Object System.Management.Automation.PSCredential($NasUser, $secure)
        }
        # 27a: can Windows open the share before, and after a credential-only New-PSDrive?
        Log "   27a. Windows opens $share before: $(Test-Path -LiteralPath $share)"
        $drive = "mh27"
        try {
            $null = New-PSDrive -Name $drive -PSProvider FileSystem -Root $share -Credential $nasCred -Scope Global -ErrorAction Stop
            Log "   27a. New-PSDrive (no letter, no -Persist): made"
        } catch { Log ("   27a. New-PSDrive refused: " + $_.Exception.Message) }
        Log "   27a. Windows opens $share after: $(Test-Path -LiteralPath $share)"
        $sample = Join-Path $Work "backup27"
        New-Item -ItemType Directory -Force -Path $sample | Out-Null
        foreach ($photo in ($picked | Select-Object -First 20)) { Copy-Item -LiteralPath $photo.FullName -Destination $sample }
        $bytes = (Get-ChildItem -LiteralPath $sample -File | Measure-Object -Property Length -Sum).Sum
        foreach ($threads in 1, 8) {
            $into = Join-Path $test "mt$threads"
            $watch = [Diagnostics.Stopwatch]::StartNew()
            $null = & robocopy $sample $into /E "/MT:$threads" /R:1 /W:1 /FFT /NP /NFL /NDL /NJH /NJS
            $code = $LASTEXITCODE
            $seconds = $watch.Elapsed.TotalSeconds
            $copied = @(Get-ChildItem -LiteralPath $into -File -ErrorAction SilentlyContinue).Count
            Log ("   27b. robocopy /MT:{0}: {1} files ({2:N1} MB) in {3:N2} s = {4:N1} MB/s, exit code {5}" -f $threads, $copied, ($bytes / 1MB), $seconds, ($bytes / 1MB / [Math]::Max($seconds, 0.001)), $code)
            $first = Get-ChildItem -LiteralPath $into -File -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($first) {
                $source = Get-Item -LiteralPath (Join-Path $sample $first.Name)
                Log ("   27b. dates kept: PC {0:o}, NAS {1:o}" -f $source.LastWriteTimeUtc, $first.LastWriteTimeUtc)
            }
        }
        $renamed = Join-Path $test "renamed"
        New-Item -ItemType Directory -Force -Path $renamed | Out-Null
        $watch = [Diagnostics.Stopwatch]::StartNew()
        foreach ($file in @(Get-ChildItem -LiteralPath (Join-Path $test "mt8") -File)) { Move-Item -LiteralPath $file.FullName -Destination (Join-Path $renamed $file.Name) }
        Log ("   27c. 20 renames on the NAS: {0:N2} s" -f $watch.Elapsed.TotalSeconds)
        # 27d: mh push end to end, in a test mh whose photo folder is the 20 photos.
        if ((Read-Host "27d. Run mh push in a test mh into $test\mh (it asks before applying: answer y)? (y/n)") -match '^y') {
            $mhDir = Join-Path $tool "mh27"
            New-Item -ItemType Directory -Force -Path $mhDir, (Join-Path $tool "config") | Out-Null
            $mhFile = Join-Path $mhDir "mh.ps1"
            $toolMounts = @(
                "-v", "${volume}:/cache",
                "-v", "$(Join-Path $tool 'config'):/config",
                "-v", "$(Join-Path $tool 'journal'):/journal",
                "-v", "$(Join-Path $tool 'quarantine'):/quarantine",
                "-v", "$(Join-Path $tool 'reports'):/reports"
            )
            & docker run --rm -e "MEDIA_HYGIENE_IMAGE=$Image" @toolMounts $Image launcher --photos $sample > $mhFile
            . $mhFile
            # mh keeps its target next to yours: yours is put back at the end.
            $keptTarget = Join-Path $mhHome "push-target.txt"
            $yours = if (Test-Path -LiteralPath $keptTarget) { Get-Content -LiteralPath $keptTarget -Raw } else { $null }
            $target = Join-Path $test "mh"
            foreach ($round in "first", "second") {
                $watch = [Diagnostics.Stopwatch]::StartNew()
                $said = @(mh push --to $target 2>&1 | ForEach-Object { "$_".Trim() } | Where-Object { $_ -match 'Copied|Renamed|To copy|Already there|Moved on|up to date|Not in the backup|robocopy|refused|cannot' })
                foreach ($line in $said) { Log "   27d. $round mh push: $line" }
                Log ("   27d. $round mh push: {0:N1} s, exit code {1}" -f $watch.Elapsed.TotalSeconds, $LASTEXITCODE)
            }
            Write-Host "27e. Now: 20 more photos are added; press Ctrl+C while robocopy runs, then mh push runs again."
            foreach ($photo in ($picked | Select-Object -Skip 20 -First 20)) { Copy-Item -LiteralPath $photo.FullName -Destination $sample }
            try { mh push 2>&1 | Out-Host } catch { }
            $said = @(mh push 2>&1 | ForEach-Object { "$_".Trim() } | Where-Object { $_ -match 'Copied|To copy|Already there|up to date|Not in the backup' })
            foreach ($line in $said) { Log "   27e. after Ctrl+C, again: $line" }
            $sub = Join-Path $sample "sorted"
            New-Item -ItemType Directory -Force -Path $sub | Out-Null
            Get-ChildItem -LiteralPath $sample -File | Select-Object -First 10 | ForEach-Object { Move-Item -LiteralPath $_.FullName -Destination $sub }
            $watch = [Diagnostics.Stopwatch]::StartNew()
            $said = @(mh push 2>&1 | ForEach-Object { "$_".Trim() } | Where-Object { $_ -match 'Copied|Renamed|To copy|Moved on|Not in the backup' })
            foreach ($line in $said) { Log "   27f. after 10 photos moved into a folder: $line" }
            Log ("   27f. {0:N1} s" -f $watch.Elapsed.TotalSeconds)
            Log ("   27g. Docker volumes of the NAS left (none expected): " + ((@(& docker volume ls -q --filter name=mh-nas-) -join ' / ') -replace '^$', 'none'))
            if ($null -ne $yours) { Set-Content -LiteralPath $keptTarget -Value $yours.Trim() -Encoding Ascii } else { Remove-Item -LiteralPath $keptTarget -ErrorAction SilentlyContinue }
        }
        Remove-Item -LiteralPath $test -Recurse -Force -ErrorAction SilentlyContinue
        Log "   27h. test folder on the NAS removed: $(-not (Test-Path -LiteralPath $test))"
        Remove-PSDrive -Name $drive -Force -ErrorAction SilentlyContinue
    }
    $ErrorActionPreference = $saved
}

# --- 28: an mh older than its image says so; mh update of a local build writes it again (0290) --
# A test mh.ps1 under -Work (your own mh is put back at the end): written by -Image, then made
# to look written by another image (its stamp changed), then by one older than the check (no
# stamp). mh history must say the line each time; mh update rewrites the test file only.
if (Wanted 28) {
    $saved = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    Log ""
    Log "== 28. an mh older than its image, then mh update (0290)"
    $folder = Join-Path $Work "older"
    New-Item -ItemType Directory -Force -Path $folder | Out-Null
    $copy = Join-Path $folder "mh.ps1"
    $lines = @(& docker run --rm $Image launcher --shell powershell --photos $data 2>$null)
    Set-Content -LiteralPath $copy -Value $lines -Encoding Ascii
    $mark = 'MEDIA_HYGIENE_LAUNCHER_STAMP='
    $written = @($lines | Where-Object { $_ -match $mark }) -join ' '
    Log ("   28a. stamp written: {0}" -f $written.Trim())
    . $copy
    $said = (@(mh history 2>&1 | ForEach-Object { "$_" }) -join ' ') -replace '\s+', ' '
    Log ("   28a. fresh file: line said = {0} (expected False)" -f [bool]($said -match 'mh update to write it again'))
    $other = @($lines | ForEach-Object { $_ -replace ($mark + '[0-9a-f.+]+'), ($mark + '0.3.0+000000000000') })
    Set-Content -LiteralPath $copy -Value $other -Encoding Ascii
    . $copy
    $said = (@(mh history 2>&1 | ForEach-Object { "$_" }) -join ' ') -replace '\s+', ' '
    Log ("   28b. another stamp: line said = {0} (expected True)" -f [bool]($said -match 'mh update to write it again'))
    $none = @($lines | Where-Object { $_ -notmatch $mark })
    Set-Content -LiteralPath $copy -Value $none -Encoding Ascii
    . $copy
    $watch = [Diagnostics.Stopwatch]::StartNew()
    $said = (@(mh history 2>&1 | ForEach-Object { "$_" }) -join ' ') -replace '\s+', ' '
    $watch.Stop()
    Log ("   28c. no stamp (older than 0290): line said = {0} (expected True), mh history took {1:N2} s" -f [bool]($said -match 'older image'), $watch.Elapsed.TotalSeconds)
    Log ("   28c. the line: {0}" -f ([regex]::Match($said, 'This mh was written[^:]+:[^.]+\.')).Value)
    $said = (@(mh update 2>&1 | ForEach-Object { "$_" }) -join ' ') -replace '\s+', ' '
    Log ("   28d. mh update: nothing to pull said = {0}, pulled = {1}, exit code {2}" -f [bool]($said -match 'nothing to pull'), [bool]($said -match 'Pulling|Digest:'), $LASTEXITCODE)
    $back = [bool](Select-String -LiteralPath $copy -Pattern $mark -SimpleMatch -Quiet)
    Log ("   28d. file written again with a stamp = {0}, folder read back = {1}" -f $back, [bool](@(_mh_photos) -contains $data))
    $said = (@(mh history 2>&1 | ForEach-Object { "$_" }) -join ' ') -replace '\s+', ' '
    Log ("   28e. after mh update: line said = {0} (expected False)" -f [bool]($said -match 'mh update to write it again'))
    $ErrorActionPreference = $saved
}

# --- 29: mh --lan, the home page on a phone of the home Wi-Fi (0269) -------------------------
# A test mh.ps1 under -Work written by -Image (your own mh is put back at the end). The address
# mh takes is read here; the phone part is by hand, in a new window: mh --lan holds its window.
if (Wanted 29) {
    $saved = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    Log ""
    Log "== 29. mh --lan, the home page on a phone of the home Wi-Fi (0269)"
    $folder = Join-Path $Work "lan"
    New-Item -ItemType Directory -Force -Path $folder | Out-Null
    $copy = Join-Path $folder "mh.ps1"
    $lines = @(& docker run --rm $Image launcher --shell powershell --photos $data 2>$null)
    Set-Content -LiteralPath $copy -Value $lines -Encoding Ascii
    . $copy
    $watch = [Diagnostics.Stopwatch]::StartNew()
    $found = _mh_lan_address  # @{ address; problem } since 0367
    $watch.Stop()
    $address = if ($found) { $found.address } else { $null }
    Log ("   29a. address found = {0}, in {1:N2} s" -f $address, $watch.Elapsed.TotalSeconds)
    foreach ($network in @(Get-NetConnectionProfile -ErrorAction SilentlyContinue)) {
        Log ("   29a. network {0} on {1}: category {2}" -f $network.Name, $network.InterfaceAlias, $network.NetworkCategory)
    }
    if ($address) {
        Write-Host "29: open a NEW Windows PowerShell window and type these two lines:"
        Write-Host "        . '$copy'"
        Write-Host "        mh"
        Write-Host "    (mh alone, as the desktop shortcut runs it: open to the home Wi-Fi by default, 0367.)"
        Write-Host "    Wait for the home page in the browser."
        $firewall = Read-Host "29b. Did Windows ask whether Docker Desktop may accept connections? (n / p: allowed on private / b: both ticked)"
        $ports = @(docker ps --format '{{.Ports}}' 2>$null) -join ' | '
        Log "   29b. firewall prompt $firewall; ports published: $ports"
        $card = Read-Host "29c. The PC's page shows 'On your phone' with a QR code, an address and a code of 8 digits? (y/n)"
        Write-Host "    On the phone, on the same Wi-Fi: scan the QR code with its camera."
        $qr = Read-Host "29d. The phone opened the home page by the QR code? (y / n / c: it asked the code)"
        Write-Host "    On the phone, open a private tab, type the address shown, then the code."
        $typed = Read-Host "29e. The code typed opened the page? (y/n)"
        Write-Host "    On the phone: Run the audit of the page (the audit space, 'Run the audit here')."
        $audit = Read-Host "29f. The audit ran to its end, its progress shown on the phone? (y/n)"
        Write-Host "    On the phone: tap the button of any other step (clean, status...)."
        $refused = Read-Host "29g. The phone said 'Run this step on the PC', nothing ran on the PC? (y/n)"
        Write-Host "    On the PC's page: run 'status' (it runs in the mh window, then the page comes back). Then reload the phone."
        $kept = Read-Host "29h. After the step, the phone's page answered again without the code? (y/n)"
        Write-Host "    On the phone: Wi-Fi off (mobile data on), reload the page."
        $outside = Read-Host "29i. From mobile data the page did NOT open? (y/n)"
        # 0384: a device of the Wi-Fi forging the PC's Host header must get the pairing, never the PC's rights.
        # curl.exe (Windows 10 1803+): Invoke-WebRequest of PowerShell 5.1 refuses to set Host.
        $port = 8088
        $forged = & curl.exe -s -o NUL -w '%{http_code}' -H "Host: 127.0.0.1:$port" "http://${address}:$port/api/state" 2>$null
        $plain = & curl.exe -s -o NUL -w '%{http_code}' "http://127.0.0.1:$port/api/state" 2>$null
        Log "   29j. forged Host by the home network address: HTTP $forged (401/403 expected, 200 = hole); the PC by 127.0.0.1: HTTP $plain (200 expected)"
        Write-Host "    On the PC: close the home page's tab."
        Write-Host "    Start it a second time in the same way (. '$copy' then mh), wait for the home page."
        $again = Read-Host "29j. The second time, did Windows ask about Docker Desktop again? (y/n)"
        $blocked = @(Get-NetFirewallRule -Action Block -Enabled True -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -match 'Docker' }).Count
        Log "   29j. firewall prompt again $again; enabled Docker block rules readable without admin: $blocked"
        Write-Host "    On the PC: close the home page's tab."
        Log "   29: card $card, by QR $qr, by code $typed, audit $audit, step refused $refused, paired after a step $kept, unreachable from mobile data $outside"
    } else {
        Log "   29: skipped the phone part: no private address found (mh --lan says the same)"
    }
    $ErrorActionPreference = $saved
}

# --- 30: mh slideshow --lan, the photos on the TV driven from the phone (0291) --------------
# A test mh with the test cache audits the test folder here; the slideshow runs in a new window
# (it holds it), the TV and the phone by hand. Times: Enter as you tap on the phone, Enter when
# the photo is whole on the TV (your two reactions roughly cancel out).
function SlideTimes([string]$what, [int]$times) {
    $taken = @()
    for ($i = 1; $i -le $times; $i++) {
        $null = Read-Host "    $what ${i}/${times}: press Enter as you tap on the phone"
        $watch = [Diagnostics.Stopwatch]::StartNew()
        $null = Read-Host "    ... press Enter when the new photo is whole on the TV"
        $watch.Stop()
        $taken += $watch.Elapsed.TotalSeconds
    }
    $sorted = @($taken | Sort-Object)
    $median = $sorted[[int][Math]::Floor($sorted.Count / 2)]
    return ("{0} (median {1:N1} s)" -f (($taken | ForEach-Object { '{0:N1}' -f $_ }) -join ' '), $median)
}

if (Wanted 30) {
    $saved = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    Log ""
    Log "== 30. mh slideshow --lan, the photos on the TV driven from the phone (0291)"
    $showDir = Join-Path $tool "slideshow"
    New-Item -ItemType Directory -Force -Path $showDir, (Join-Path $tool "config") | Out-Null
    $showFile = Join-Path $showDir "mh.ps1"
    $showMounts = @(
        "-v", "${volume}:/cache",
        "-v", "$(Join-Path $tool 'config'):/config",
        "-v", "$(Join-Path $tool 'journal'):/journal",
        "-v", "$(Join-Path $tool 'quarantine'):/quarantine",
        "-v", "$(Join-Path $tool 'reports'):/reports"
    )
    & docker run --rm -e "MEDIA_HYGIENE_IMAGE=$Image" @showMounts $Image launcher --photos $data > $showFile
    . $showFile
    $watch = [Diagnostics.Stopwatch]::StartNew()
    mh audit | Out-Null
    $watch.Stop()
    Log ("   30a. mh audit of the test folder: exit code {0}, {1:N1} s" -f $LASTEXITCODE, $watch.Elapsed.TotalSeconds)
    $address = _mh_lan_address
    $shown = Join-Path $data "flat"
    if ($address) {
        Log "   30a. address found = $address"
        Write-Host "30: open a NEW Windows PowerShell window and type these two lines:"
        Write-Host "        . '$showFile'"
        Write-Host "        mh slideshow --folder '$shown' --lan"
        Write-Host "    The PC's browser opens the remote."
        $card = Read-Host "30b. The PC's page shows the TV's address (http://${address}:.../screen), a QR code and a code of 8 digits? (y/n)"
        Write-Host "    On the Chromecast: open its browser, type the TV's address of the PC's page."
        $tvCode = Read-Host "30c. The TV shows a code of 6 digits, big and readable from the sofa? (y/n)"
        Write-Host "    On the phone (same Wi-Fi): scan the QR code of the PC's page."
        $phone = Read-Host "30d. The phone opened the remote, with the thumbnails? (y / n / c: it asked the code)"
        Write-Host "    On the phone: type the TV's code in 'The code the TV shows', then 'Pair the TV'."
        $paired = Read-Host "30e. The first photo appeared on the TV, black borders, no file name? (y/n)"
        Write-Host "    On the TV: press OK on the remote."
        $full = Read-Host "30f. Full screen? (y / n / b: the browser's bar stays)"
        Write-Host "    Next: tap the right arrow on the phone; wait each time for the photo."
        $next = SlideTimes "next" 5
        Log "   30g. tap -> photo on the TV, next (loaded in advance): $next"
        Write-Host "    Jump: each time tap a thumbnail far down the grid (never the next one)."
        $jump = SlideTimes "jump" 5
        Log "   30g. tap -> photo on the TV, a far thumbnail: $jump"
        $bands = Read-Host "30g. Did you ever see a photo drawn in bands, or half a photo? (n / y: when)"
        Write-Host "    On the phone: 'Each photo' 5 s, then Play; wait 20 s."
        $timer = Read-Host "30h. The TV moved on alone every 5 s or so? (y/n)"
        Write-Host "    On the phone: Pause, then 'Do not show'."
        $skip = Read-Host "30h. The TV moved on, and the thumbnail is dimmed on the phone? (y/n)"
        Write-Host "    On the TV: reload the page (or open the bookmark again)."
        $reload = Read-Host "30i. Still paired (no code), the same photo back? (y/n)"
        Write-Host "    On the phone: lock it, wait one minute, unlock it."
        $sleep = Read-Host "30j. The remote shows the photo the TV shows, its buttons work? (y/n)"
        Log "   30: PC card $card, TV code $tvCode, phone $phone, TV paired $paired, full screen $full, bands $bands, timer $timer, do not show $skip, TV reload $reload, phone asleep $sleep"
        $own = Read-Host "30k. Now the TV's own browser (Samsung: the Internet app): try it? (y/n)"
        if ($own -eq 'y') {
            Write-Host "    On the TV's Internet app: type the TV's address; type its code on the phone."
            $ownCode = Read-Host "30k. The TV showed its code, then the photo once paired? (y/n)"
            $ownNext = SlideTimes "next (TV's browser)" 3
            $ownJump = SlideTimes "jump (TV's browser)" 3
            $ownBands = Read-Host "30k. Bands seen on the TV's own browser? (n / y)"
            Log "   30k. TV's own browser: code then photo $ownCode, next $ownNext, jump $ownJump, bands $ownBands"
        }
        Write-Host "    In the slideshow's window: Ctrl+C, then close it."
    } else {
        Log "   30: skipped the TV part: no private address found (mh --lan says the same)"
    }
    $ErrorActionPreference = $saved
}

# --- 31: mh slideshow --lan plays the videos (0292) ------------------------------------------
# A few phone videos of $Photos are COPIED into the test folder (C:\Photos is only read), with
# one HEVC video you name (the Codec column of inventory.xlsx says hevc); a test mh audits them,
# the slideshow runs in a new window, the TV and the phone by hand.
if (Wanted 31) {
    $saved = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    Log ""
    Log "== 31. mh slideshow --lan plays the videos on the TV (0292)"
    $filmDir = Join-Path $data "videos"
    $filmTool = Join-Path $tool "slideshow-videos"
    New-Item -ItemType Directory -Force -Path $filmDir, $filmTool, (Join-Path $tool "config") | Out-Null
    $found = @(Get-ChildItem -Path $Photos -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -in '.mov', '.mp4' -and $_.Length -gt 1MB } |
        Select-Object -First 60)
    $chosenFilms = @($found | Sort-Object Length | Select-Object -First 4)
    foreach ($film in $chosenFilms) { Copy-Item -LiteralPath $film.FullName -Destination $filmDir }
    Get-ChildItem -Path (Join-Path $data "flat") -File | Select-Object -First 4 | Copy-Item -Destination $filmDir
    $hevcPath = Read-Host "31a. Path of ONE HEVC video of your photos (inventory.xlsx, column Codec = hevc), or Enter to skip"
    $hevcCopied = "none"
    if ($hevcPath -ne "" -and (Test-Path -LiteralPath $hevcPath)) {
        Copy-Item -LiteralPath $hevcPath -Destination (Join-Path $filmDir ("hevc-" + (Split-Path $hevcPath -Leaf)))
        $hevcCopied = "yes"
    }
    $sizes = ($chosenFilms | ForEach-Object { '{0} {1:N0} MB' -f $_.Extension, ($_.Length / 1MB) }) -join ', '
    Log ("   31a. videos copied: {0} ({1}); HEVC copied: {2}" -f $chosenFilms.Count, $sizes, $hevcCopied)
    $filmFile = Join-Path $filmTool "mh.ps1"
    $filmMounts = @(
        "-v", "${volume}:/cache",
        "-v", "$(Join-Path $tool 'config'):/config",
        "-v", "$(Join-Path $tool 'journal'):/journal",
        "-v", "$(Join-Path $tool 'quarantine'):/quarantine",
        "-v", "$(Join-Path $tool 'reports'):/reports"
    )
    & docker run --rm -e "MEDIA_HYGIENE_IMAGE=$Image" @filmMounts $Image launcher --photos $data > $filmFile
    . $filmFile
    $watch = [Diagnostics.Stopwatch]::StartNew()
    mh audit | Out-Null
    $watch.Stop()
    Log ("   31a. mh audit of the test folder: exit code {0}, {1:N1} s" -f $LASTEXITCODE, $watch.Elapsed.TotalSeconds)
    $address = _mh_lan_address
    if ($address) {
        Write-Host "31: open a NEW Windows PowerShell window and type these two lines:"
        Write-Host "        . '$filmFile'"
        Write-Host "        mh slideshow --folder '$filmDir' --lan"
        $filmPort = Read-Host "31b. The port in the TV's address on the PC's page (Enter: 8088)"
        if ($filmPort -eq "") { $filmPort = "8088" }
        $hevcUrl = ""
        try {
            $slides = (Invoke-WebRequest -Uri "http://127.0.0.1:$filmPort/api/slides" -UseBasicParsing -TimeoutSec 30).Content | ConvertFrom-Json
            $kinds = @($slides.slides | ForEach-Object { if ($_.film) { 'video ' + $_.format } elseif ($_.format) { 'not on the TV ' + $_.format } else { 'photo' } })
            Log ("   31b. the show as the server lists it: " + ($kinds -join ', '))
            $hevc = @($slides.slides | Where-Object { $_.format -eq 'hevc' } | Select-Object -First 1)
            if ($hevc.Count -eq 1) { $hevcUrl = "http://${address}:$filmPort/film/$($hevc[0].key)" }
        } catch {
            Log ("   31b. GET /api/slides failed: " + $_.Exception.Message)
        }
        Write-Host "    Pair the Chromecast's browser and the phone as in step 30 (the TV's code, the QR code)."
        $marked = Read-Host "31c. On the phone: the videos' thumbnails show a frame and a play mark, the HEVC one says 'Not on the TV: its format (hevc) ...'? (y / n: what)"
        Write-Host "    On the phone: Pause if playing, then tap a video's thumbnail; press Enter at the tap."
        $null = Read-Host "    Enter as you tap"
        $watch = [Diagnostics.Stopwatch]::StartNew()
        $null = Read-Host "    ... Enter when its first frame is on the TV"
        $watch.Stop()
        Log ("   31d. tap -> the video's first frame on the TV: {0:N1} s" -f $watch.Elapsed.TotalSeconds)
        $plays = Read-Host "31d. On the phone: Play. The video plays on the TV? (s: with sound / m: muted / d: offered a download / n: black or frozen)"
        $smooth = Read-Host "31e. Smooth, no stutter, the whole picture (not cropped, not stretched)? (y / n: what)"
        $paused = Read-Host "31f. On the phone: Pause, wait 5 s, Play. The video paused, then went on where it was? (y / r: restarted / n)"
        $endNext = Read-Host "31g. At the video's end, the TV moved on alone to the next photo or video? (y / n: it stayed)"
        $afterFilm = Read-Host "31g. The photo after the video came at once (loaded during the video)? (y / n: seconds)"
        Log "   31: marked $marked, plays $plays, smooth $smooth, pause/play $paused, moved on at the end $endNext, next photo at once $afterFilm"
        if ($hevcUrl -ne "") {
            $hevcExt = [IO.Path]::GetExtension($hevcPath).ToLower()
            Write-Host "    In the Chromecast's browser, open a NEW tab and type: $hevcUrl$hevcExt"
            $hevcPlays = Read-Host "31h. Does the HEVC video play there? (y / d: offered a download / n: black or error)"
            Log "   31h. HEVC on the Chromecast's browser, opened by its address: $hevcPlays"
        } else {
            Log "   31h. HEVC: no HEVC video in the show, not tried"
        }
        $ownFilms = Read-Host "31i. Now the TV's own browser (Samsung Internet app), paired as in 30k: try it? (y/n)"
        if ($ownFilms -eq 'y') {
            $ownSkip = Read-Host "31i. Play on the phone: the TV shows the photos only, never a video, and the phone's line says the videos are skipped? (y / n: what)"
            Log "   31i. TV's own browser: $ownSkip"
        }
        Write-Host "    In the slideshow's window: Ctrl+C, then close it."
    } else {
        Log "   31: skipped the TV part: no private address found (mh --lan says the same)"
    }
    $ErrorActionPreference = $saved
}

# --- 32: mh share, an album made ready to send (0296) ----------------------------------------
# A test mh audits the test folder; an album of its first photos is written into the test
# reports (albums.json, SHA-256 by Get-FileHash); mh share makes the copies in YOUR
# $HOME\media-hygiene\Shares (the fixed folder of mh share): the album's folder and zip there are
# removed at the end. The photos of the test folder are only read: compared before and after.
if (Wanted 32) {
    $saved = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    Log ""
    Log "== 32. mh share, an album made ready to send (0296)"
    $shareTool = Join-Path $tool "share"
    New-Item -ItemType Directory -Force -Path $shareTool, (Join-Path $tool "config") | Out-Null
    $shareFile = Join-Path $shareTool "mh.ps1"
    $shareMounts = @(
        "-v", "${volume}:/cache",
        "-v", "$(Join-Path $tool 'config'):/config",
        "-v", "$(Join-Path $tool 'journal'):/journal",
        "-v", "$(Join-Path $tool 'quarantine'):/quarantine",
        "-v", "$(Join-Path $tool 'reports'):/reports"
    )
    & docker run --rm -e "MEDIA_HYGIENE_IMAGE=$Image" @shareMounts $Image launcher --photos $data > $shareFile
    . $shareFile
    $watch = [Diagnostics.Stopwatch]::StartNew()
    mh audit | Out-Null
    $watch.Stop()
    Log ("   32a. mh audit of the test folder: exit code {0}, {1:N1} s" -f $LASTEXITCODE, $watch.Elapsed.TotalSeconds)
    $albumPhotos = @(Get-ChildItem -Path (Join-Path $data "flat") -File | Sort-Object Name | Select-Object -First 60)
    $entries = @(foreach ($photo in $albumPhotos) {
        [ordered]@{
            path = $photo.FullName
            sha256 = (Get-FileHash -LiteralPath $photo.FullName -Algorithm SHA256).Hash.ToLower()
            size = $photo.Length
            added = "2026-10-22T00:00:00Z"
        }
    })
    $albumName = "mh-measure share"
    $albums = [ordered]@{ version = 1; albums = @([ordered]@{ name = $albumName; entries = $entries }) }
    $albumsFile = Join-Path $tool "reports\albums.json"
    [IO.File]::WriteAllText($albumsFile, ($albums | ConvertTo-Json -Depth 6), [Text.UTF8Encoding]::new($false))
    $originalMb = ($albumPhotos | Measure-Object -Property Length -Sum).Sum / 1MB
    Log ("   32a. album of {0} photos ({1:N1} MB) written to {2}" -f $albumPhotos.Count, $originalMb, $albumsFile)
    $before = @($albumPhotos | ForEach-Object { "$($_.Name) $($_.Length) $($_.LastWriteTimeUtc.Ticks)" }) -join '|'
    $shares = Join-Path $mhHome "Shares"
    $watch = [Diagnostics.Stopwatch]::StartNew()
    $said = @(mh share --album $albumName 2>&1)
    $status = $LASTEXITCODE
    $watch.Stop()
    Log ("   32b. mh share: exit code {0}, {1:N1} s" -f $status, $watch.Elapsed.TotalSeconds)
    foreach ($line in $said) {
        $text = "$line".Trim()
        if ($text -match 'ready to send|read back|GPS|not included|25 MB|replaced|missing|could not') { Log "   32b. $text" }
    }
    $after = @(Get-ChildItem -LiteralPath $albumPhotos.FullName | ForEach-Object { "$($_.Name) $($_.Length) $($_.LastWriteTimeUtc.Ticks)" }) -join '|'
    Log ("   32c. the album's originals unchanged (size and date): {0}" -f ($before -eq $after))
    $shareFolder = Join-Path $shares $albumName
    $shareZip = Join-Path $shares "$albumName.zip"
    $copies = @(Get-ChildItem -LiteralPath $shareFolder -File -ErrorAction SilentlyContinue)
    if ($copies.Count -gt 0) {
        $copiedMb = ($copies | Measure-Object -Property Length -Sum).Sum / 1MB
        $zipMb = (Get-Item -LiteralPath $shareZip).Length / 1MB
        Log ("   32c. copies: {0}, {1:N1} MB, {2:N2} MB per photo (originals {3:N2} MB each); zip {4:N1} MB" -f $copies.Count, $copiedMb, ($copiedMb / $copies.Count), ($originalMb / $albumPhotos.Count), $zipMb)
        # GPSLatitude (0x0002) through System.Drawing: an assembly of Windows, nothing compiled.
        Add-Type -AssemblyName System.Drawing
        $gpsIn = 0
        foreach ($photo in $albumPhotos) {
            $picture = [Drawing.Image]::FromFile($photo.FullName)
            if ($picture.PropertyIdList -contains 2) { $gpsIn++ }
            $picture.Dispose()
        }
        $gpsOut = 0
        foreach ($copy in $copies) {
            $picture = [Drawing.Image]::FromFile($copy.FullName)
            if ($picture.PropertyIdList -contains 2) { $gpsOut++ }
            $picture.Dispose()
        }
        Log "   32c. photos with a GPS position: $gpsIn of the originals, $gpsOut of the copies (expected 0)"
    } else {
        Log "   32c. no copy found in $shareFolder"
    }
    $explorer = Read-Host "32d. Did the Explorer open on $shares, the folder '$albumName' and its zip side by side? (y / n: what)"
    $look = Read-Host "32e. Open two copies: upright, sharp enough on screen, colours as the originals? (y / n: what)"
    Log "   32d. Explorer opened on Shares: $explorer; copies look right: $look"
    Remove-Item -Recurse -Force -LiteralPath $shareFolder -ErrorAction SilentlyContinue
    Remove-Item -Force -LiteralPath $shareZip -ErrorAction SilentlyContinue
    Log "   32: the test album's folder and zip removed from $shares"
    $ErrorActionPreference = $saved
}

# --- 33: an album on the phone at home (0297) -----------------------------------------------
# A test mh audits the test folder (and 2 small videos of your photos copied into it); an album
# of its photos is written into the test reports (albums.json, as in step 32). You open
# mh --lan in a NEW window with this test mh: the album list, an album and a phone-sized picture
# are timed from the PC (127.0.0.1), then the phone is asked. Your photos are only read.
if (Wanted 33) {
    $saved = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    Log ""
    Log "== 33. an album on the phone at home (0297)"
    $phoneTool = Join-Path $tool "album-phone"
    New-Item -ItemType Directory -Force -Path $phoneTool, (Join-Path $tool "config") | Out-Null
    $phoneFilms = Join-Path $data "album-videos"
    New-Item -ItemType Directory -Force -Path $phoneFilms | Out-Null
    $smallFilms = @(Get-ChildItem -Path $Photos -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -in '.mov', '.mp4' -and $_.Length -gt 1MB } |
        Select-Object -First 40 | Sort-Object Length | Select-Object -First 2)
    foreach ($film in $smallFilms) { Copy-Item -LiteralPath $film.FullName -Destination $phoneFilms }
    $phoneFile = Join-Path $phoneTool "mh.ps1"
    $phoneMounts = @(
        "-v", "${volume}:/cache",
        "-v", "$(Join-Path $tool 'config'):/config",
        "-v", "$(Join-Path $tool 'journal'):/journal",
        "-v", "$(Join-Path $tool 'quarantine'):/quarantine",
        "-v", "$(Join-Path $tool 'reports'):/reports"
    )
    & docker run --rm -e "MEDIA_HYGIENE_IMAGE=$Image" @phoneMounts $Image launcher --photos $data > $phoneFile
    . $phoneFile
    $watch = [Diagnostics.Stopwatch]::StartNew()
    mh audit | Out-Null
    $watch.Stop()
    Log ("   33a. mh audit of the test folder: exit code {0}, {1:N1} s" -f $LASTEXITCODE, $watch.Elapsed.TotalSeconds)
    $albumFiles = @(Get-ChildItem -Path (Join-Path $data "flat") -File | Sort-Object Name | Select-Object -First $Count) + @(Get-ChildItem -Path $phoneFilms -File)
    $entries = @(foreach ($file in $albumFiles) {
        [ordered]@{
            path = $file.FullName
            sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLower()
            size = $file.Length
            added = "2026-10-22T00:00:00Z"
        }
    })
    $phoneAlbum = "mh-measure phone"
    $albums = [ordered]@{ version = 1; albums = @([ordered]@{ name = $phoneAlbum; entries = $entries }) }
    $phoneAlbums = Join-Path $tool "reports\albums.json"
    [IO.File]::WriteAllText($phoneAlbums, ($albums | ConvertTo-Json -Depth 6), [Text.UTF8Encoding]::new($false))
    Log ("   33a. album of {0} files ({1} videos) written to {2}" -f $albumFiles.Count, $smallFilms.Count, $phoneAlbums)
    $address = _mh_lan_address
    if ($address) {
        Write-Host "33: open a NEW Windows PowerShell window and type these two lines:"
        Write-Host "        . '$phoneFile'"
        Write-Host "        mh --lan"
        $phonePort = Read-Host "33b. The port in the address on the PC's page, in 'On your phone' (Enter: 8088)"
        if ($phonePort -eq "") { $phonePort = "8088" }
        $base = "http://127.0.0.1:$phonePort"
        $named = [Uri]::EscapeDataString($phoneAlbum)
        try {
            foreach ($round in 'cold', 'warm') {
                $watch = [Diagnostics.Stopwatch]::StartNew()
                $null = Invoke-WebRequest -Uri "$base/api/album-list" -UseBasicParsing -TimeoutSec 120
                $listMs = $watch.Elapsed.TotalMilliseconds
                $watch = [Diagnostics.Stopwatch]::StartNew()
                $view = (Invoke-WebRequest -Uri "$base/api/album/$named" -UseBasicParsing -TimeoutSec 120).Content | ConvertFrom-Json
                $albumMs = $watch.Elapsed.TotalMilliseconds
                Log ("   33b. {0}: the album list {1:N0} ms, the album {2:N0} ms ({3} files, {4} days, place '{5}')" -f $round, $listMs, $albumMs, $view.count, @($view.days).Count, $view.place)
            }
            $firstPhoto = @($view.days | ForEach-Object { $_.items } | Where-Object { $_.photo } | Select-Object -First 1)
            if ($firstPhoto.Count -eq 1) {
                foreach ($round in 'cold', 'warm') {
                    $watch = [Diagnostics.Stopwatch]::StartNew()
                    $picture = Invoke-WebRequest -Uri "$base$($firstPhoto[0].photo)" -UseBasicParsing -TimeoutSec 120
                    Log ("   33c. {0}: one phone-sized picture {1:N0} ms, {2:N0} KB" -f $round, $watch.Elapsed.TotalMilliseconds, ($picture.RawContentLength / 1KB))
                }
            }
            $films = @($view.days | ForEach-Object { $_.items } | Where-Object { -not $_.photo } | ForEach-Object { if ($_.film) { 'plays ' + $_.film } else { 'labelled ' + $_.format } })
            Log ("   33c. the videos as the page lists them: " + ($films -join ', '))
        } catch {
            Log ("   33b. the albums' routes failed: " + $_.Exception.Message)
        }
        Write-Host "    On the phone (same Wi-Fi): pair it with the QR code, then 'Open the albums' on its home page."
        $listed = Read-Host "33d. The list shows the album, its cover, its dates and its count? (y / n: what)"
        $scroll = Read-Host "33e. Open the album and scroll the mosaic quickly to the end: smooth? (y / j: jerky / b: blank tiles for long)"
        # Asked, not timed: two Enter presses around a tap were misread (2026-10-22, 23.9 s logged
        # for a photo shown at once); 33c times a phone-sized picture from the PC.
        $tapped = Read-Host "33f. Tap a photo far down the mosaic: full screen at once, sharp and whole? (y / n: about how many seconds)"
        Log "   33f. tap -> photo full screen at once: $tapped"
        $swipe = Read-Host "33g. Swipe left 5 times: each next photo at once (loaded in advance)? (y / n: seconds) ; a tap closes it? (y/n)"
        $video = Read-Host "33h. Open a video of the album: it plays in place, with sound? (y / m: muted / n: what)"
        $back = Read-Host "33i. Full screen, the phone's Back button closes the photo and stays in the album? (y / n: what)"
        $before = (Get-Content -LiteralPath $phoneAlbums -Raw | ConvertFrom-Json).albums
        $moved = Read-Host "33j. Full screen: Take out of the album (OK), then on another photo Add to an album, name 'Kids'. Said and saved? (y / n: what)"
        $after = (Get-Content -LiteralPath $phoneAlbums -Raw | ConvertFrom-Json).albums
        $counts = ($after | ForEach-Object { "$($_.name): $(@($_.entries).Count)" }) -join ', '
        Log ("   33j. albums.json before: {0} files in 1 album; after: {1}" -f @($before[0].entries).Count, $counts)
        $other = Read-Host "33k. In the phone's address bar, type http://${address}:$phonePort/original/1.jpg then /preview/1.jpg: refused both? (y / n: what shows)"
        $mobile = Read-Host "33l. Wi-Fi off (mobile data), reload the album: the page cannot be reached? (y / n)"
        Log "   33: list $listed, scroll $scroll, swipe $swipe, video $video, Back $back, changed $moved, another file refused $other, mobile data cut off $mobile"
        Write-Host "    In the window of mh --lan: Quit on the PC's page (or Ctrl+C), then close it."
    } else {
        Log "   33: skipped the phone part: no private address found (mh --lan says the same)"
    }
    $ErrorActionPreference = $saved
}

# --- 34: shrink, heavy videos re-encoded in H.264 (0303) -----------------------------------
# Two of your videos are copied into the test folder (yours are only read): the first MJPEG clip
# `shrink` lists on C:\Photos (with your usual cache, read-only) and a phone's video. Each is
# encoded by the image's ffmpeg at both levels, with the arguments of shrink/encode.py (keep them
# in sync): time, size, seconds per minute of film. Then the real `shrink --apply` on a copy of
# the MJPEG clip: the lighter video in place, the original in the test quarantine. You play the
# results in Windows (Photos, Media Player) and on your phone.
if (Wanted 34) {
    $saved = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    Log ""
    Log "== 34. shrink, heavy videos re-encoded in H.264 (0303)"
    $shrinkData = Join-Path $Work "shrink"
    $clips = Join-Path $shrinkData "clips"
    $encoded = Join-Path $shrinkData "out"
    $lighten = Join-Path $shrinkData "real"
    New-Item -ItemType Directory -Force -Path $clips, $encoded, $lighten | Out-Null
    $dash = [string][char]0x2014
    $listed = @(& docker run --rm --env COLUMNS=400 @real $Image --locale en shrink 2>&1)
    $summary = @($listed | Where-Object { "$_" -match 'worth lightening' } | Select-Object -First 1)
    Log "   34a. shrink on $Photos (list only): $summary"
    $mjpeg = $null
    foreach ($line in $listed) {
        $text = "$line".Trim()
        if ($text -notmatch [regex]::Escape(" $dash mjpeg")) { continue }
        $path = $text.Substring(0, $text.IndexOf(" $dash "))
        if ((Test-Path -LiteralPath $path) -and (Get-Item -LiteralPath $path).Length -lt 600MB) { $mjpeg = Get-Item -LiteralPath $path; break }
    }
    $phone = @(Get-ChildItem -Path $Photos -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -in '.mp4', '.mov' -and $_.Length -gt 20MB -and $_.Length -lt 600MB } |
        Select-Object -First 1)
    $films = @()
    if ($mjpeg) { $films += $mjpeg } else { Log "   34a. no MJPEG clip under 600 MB in the list of shrink" }
    if ($phone.Count -eq 1) { $films += $phone[0] } else { Log "   34a. no phone video (.mp4/.mov, 20 to 600 MB) found" }
    foreach ($film in $films) { Copy-Item -LiteralPath $film.FullName -Destination $clips }
    $threads = [Math]::Max(1, [int]([Environment]::ProcessorCount / 2))
    $fit = "scale='if(gt(iw,ih),-2,min(iw,720))':'if(gt(iw,ih),min(ih,720),-2)'"
    foreach ($film in $films) {
        $name = $film.Name
        $probe = @(& docker run --rm --entrypoint ffprobe -v "${shrinkData}:/w:ro" $Image -v error -show_entries "format=duration:stream=codec_name,width,height" -of csv=p=0 "/w/clips/$name" 2>&1)
        $seconds = 0.0
        foreach ($line in $probe) { $number = 0.0; if ([double]::TryParse("$line".Trim(), [Globalization.NumberStyles]::Float, [Globalization.CultureInfo]::InvariantCulture, [ref]$number)) { $seconds = $number } }
        Log ("   34b. {0}: {1:N1} MB, {2:N0} s, {3}" -f $name, ($film.Length / 1MB), $seconds, (($probe | Select-Object -First 2) -join ' / '))
        foreach ($level in 'same', 'lighter') {
            $quality = if ($level -eq 'same') { @("-crf", "23") } else { @("-crf", "23", "-vf", $fit) }
            $target = "/w/out/$($film.BaseName)-$level.mp4"
            $watch = [Diagnostics.Stopwatch]::StartNew()
            $said = @(& docker run --rm --entrypoint ffmpeg -v "${shrinkData}:/w" $Image -nostdin -v error -y -i "/w/clips/$name" -map "0:v:0" -map "0:a?" -map_metadata 0 -c:v libx264 -pix_fmt yuv420p -preset medium @quality -c:a aac -b:a 160000 -threads $threads -movflags "+faststart+use_metadata_tags" -f mp4 $target 2>&1)
            $watch.Stop()
            $result = Join-Path $encoded "$($film.BaseName)-$level.mp4"
            if (Test-Path -LiteralPath $result) {
                $after = (Get-Item -LiteralPath $result).Length
                $perMinute = if ($seconds -gt 0) { $watch.Elapsed.TotalSeconds / ($seconds / 60) } else { 0 }
                Log ("   34b. {0} {1}: {2:N1} s, {3:N1} MB -> {4:N1} MB ({5:N0} % of the original), {6:N1} s per minute of film, {7} threads" -f $name, $level, $watch.Elapsed.TotalSeconds, ($film.Length / 1MB), ($after / 1MB), (100 * $after / $film.Length), $perMinute, $threads)
            } else {
                Log ("   34b. {0} {1}: no result after {2:N1} s: {3}" -f $name, $level, $watch.Elapsed.TotalSeconds, (($said | Select-Object -Last 2) -join ' '))
            }
        }
    }
    if ($mjpeg) {
        Copy-Item -LiteralPath $mjpeg.FullName -Destination $lighten
        $shrinkMounts = @(
            "-v", "${lighten}:/data/c/shrink",
            "-v", "${volume}:/cache",
            "-v", "$(Join-Path $tool 'journal'):/journal",
            "-v", "$(Join-Path $tool 'quarantine'):/quarantine",
            "-v", "$(Join-Path $tool 'reports'):/reports"
        )
        & docker run --rm @shrinkMounts $Image --locale en audit | Out-Null
        $watch = [Diagnostics.Stopwatch]::StartNew()
        $said = @(& docker run --rm --env COLUMNS=200 @shrinkMounts $Image --locale en shrink --apply --yes 2>&1)
        $watch.Stop()
        Log ("   34c. shrink --apply on a copy of {0}: exit code {1}, {2:N1} s" -f $mjpeg.Name, $LASTEXITCODE, $watch.Elapsed.TotalSeconds)
        foreach ($line in $said) {
            $text = "$line".Trim()
            if ($text -match 'lightened|not worth|left where|Stopped|cannot') { Log "   34c. $text" }
        }
        $now = @(Get-ChildItem -LiteralPath $lighten -File | ForEach-Object { "$($_.Name) $([Math]::Round($_.Length / 1MB, 1)) MB $($_.LastWriteTime)" }) -join '; '
        Log "   34c. the folder now holds: $now (the original: $($mjpeg.Name), $($mjpeg.LastWriteTime))"
    }
    Write-Host "34: the encoded videos are in $encoded, the real shrink's result in $lighten."
    $windows = Read-Host "34d. Play each one in Windows (Photos, Media Player): picture, sound, upright, smooth? (y / n: which, what)"
    $look = Read-Host "34e. Next to its original: any visible difference at the same level 'same'? and 'lighter'? (say which)"
    $phoneSays = Read-Host "34f. Copy one 'same' and one 'lighter' to your phone: do they play, with the right date in its gallery? (y / n: what)"
    Log "   34d. plays in Windows: $windows"
    Log "   34e. visible difference: $look"
    Log "   34f. on the phone: $phoneSays"
    $ErrorActionPreference = $saved
}

# --- 35: the pages opened from the home page, each phase timed (0354) -----------------------
# Your own mh and your usual cache, read-only: nothing is written. 35a-35c run alone. The
# clicks on the home page are timed by Chromium in the CI since 0366
# (tests/e2e/test_pages_browser.py): no step asks to time a page by hand.
if (Wanted 35) {
    $saved = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    Log ""
    Log "== 35. pages opened from the home page, each phase timed (0354)"
    foreach ($try in 1, 2, 3) {
        $watch = [Diagnostics.Stopwatch]::StartNew()
        & docker run --rm --entrypoint python $Image -c "pass" 2>&1 | Out-Null
        $watch.Stop()
        $bare = $watch.Elapsed.TotalSeconds
        $watch = [Diagnostics.Stopwatch]::StartNew()
        & docker run --rm $Image --version 2>&1 | Out-Null
        $watch.Stop()
        Log ("   35a. try {0}: a container running python -c pass {1:N2} s, media-hygiene --version {2:N2} s" -f $try, $bare, $watch.Elapsed.TotalSeconds)
    }
    # Your own mh: the one of your profile, else the file mh writes in your home.
    MhRestore
    $own = Join-Path $mhHome "mh.ps1"
    if (-not (Get-Command mh -ErrorAction SilentlyContinue) -and (Test-Path -LiteralPath $own)) { . $own }
    if (Get-Command mh -ErrorAction SilentlyContinue) {
        foreach ($try in 1, 2, 3) {
            $watch = [Diagnostics.Stopwatch]::StartNew()
            $listed = @(mh --color never menu 2>$null)
            $watch.Stop()
            Log ("   35b. mh menu (run after each click, to read the step chosen), try {0}: {1:N2} s, {2} lines" -f $try, $watch.Elapsed.TotalSeconds, $listed.Count)
        }
    } else {
        Log "   35b. no mh in this console nor in ${own}: skipped"
    }
    # Inside a container: what mh search does before its page answers, phase by phase.
    $code = @'
import time
start = time.perf_counter()
last = start
def mark(name, said=''):
    global last
    now = time.perf_counter()
    print(f'35c. {name}: {(now - last) * 1000:.0f} ms{said}')
    last = now
from media_hygiene.i18n import install
from media_hygiene.i18n.bootstrap import resolve_locale
install(resolve_locale([]))
mark('locale')
from media_hygiene.cli.app import build_app
build_app()
mark('the CLI built (every command, as mh search starts)')
import media_hygiene.services.search_pages
import media_hygiene.services.search
mark('the code of search and its pages loaded')
from media_hygiene.cli.context import build_runtime
runtime = build_runtime({})
mark('settings and mounts read')
from media_hygiene.search.meaning_index import MeaningIndex
from media_hygiene.search.people_words import people_words
from media_hygiene.search.query import SearchQuery, parse_terms
from media_hygiene.services.search_meaning import with_meaning
index = MeaningIndex.open(runtime.index_file)
mark('index opened', f' ({runtime.index_file.stat().st_size / 1e6:.0f} MB)')
names = people_words(index.connection, runtime.settings.people)
index.name_people(names)
mark('names of the people read', f' ({len(names)} photos named)')
with_meaning(runtime, index)
mark('search by meaning prepared')
for text in ('plage', 'plage', 'neige 2008'):
    found = index.find(SearchQuery(parse_terms(text)), 60)
    mark(f'search "{text}"', f' ({found.total} found)')
print(f'35c. total inside the container: {(time.perf_counter() - start) * 1000:.0f} ms')
'@
    $encoded = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($code))
    $phaseMounts = @("-v", "${Cache}:/cache:ro")
    $config = Join-Path $mhHome "config"
    if (Test-Path -LiteralPath $config) { $phaseMounts += "-v", "${config}:/config:ro" }
    foreach ($try in 1, 2) {
        Log "   35c. try $try (the second one with the index in Docker's memory)"
        $watch = [Diagnostics.Stopwatch]::StartNew()
        $lines = & docker run --rm @phaseMounts --entrypoint python $Image -c "import base64; exec(base64.b64decode('$encoded'))" 2>&1
        $watch.Stop()
        foreach ($line in $lines) { Log ("   " + "$line".Trim()) }
        Log ("   35c. the whole docker run: {0:N2} s" -f $watch.Elapsed.TotalSeconds)
    }
    $felt = Read-Host "35f. Quelle attente vous gene le plus (une page qui s'ouvre, le retour a l'accueil, une etape en console, autre) ?"
    Log "   35f. what bothers you most: $felt"
    $ErrorActionPreference = $saved
}

# --- 36: the home page by hand, three yes/no questions (0355, 0366) ----------------------------
# What the browser test of the CI cannot prove: mh.ps1, Windows and Docker Desktop. The image of
# the branch built first, and mh written again (mh update). Nothing written but what the step
# does: choose a step that only reads (history).
if (Wanted 36) {
    $saved = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    Log ""
    Log "== 36. the home page by hand on Windows (0355, 0366)"
    Write-Host "36 : dans votre fenetre Windows PowerShell habituelle, tapez mh update, puis mh."
    $opens = Read-Host "36a. La page d'accueil s'ouvre-t-elle dans le navigateur, avec ses etapes ? (o/n)"
    $kept = Read-Host "36b. Cliquez 'history' sur la page : l'etape tourne-t-elle dans la fenetre de mh pendant que la page reste ouverte, puis la page dit-elle 'termine' ? (o/n)"
    $again = Read-Host "36c. Cliquez Quitter sur la page, puis tapez mh a nouveau : la page d'accueil revient-elle ? (o/n)"
    Log "   36a. the home page opens: $opens"
    Log "   36b. a console step runs in the window of mh, the page staying open: $kept"
    Log "   36c. Quit, then mh again, the home page back: $again"
    $ErrorActionPreference = $saved
}

# --- clean up -------------------------------------------------------------------------------
if (-not $Keep) {
    if ($otherRoot -ne "") { Remove-Item -Recurse -Force $otherRoot }
    if ($driveRoot -ne "") { Remove-Item -Recurse -Force $driveRoot }
    MhLeftovers "clean-up"
    try {
        Remove-Item -Recurse -Force $Work -ErrorAction Stop
    } catch {
        if (Test-Path -LiteralPath $Work) { Set-Content -Path (Join-Path $Work ".mh-measure") -Value "made by mh-measure.ps1" }
        Log "   clean-up: $Work is still in use (an Explorer or mh window open in it?): close it, the next run removes it. $($_.Exception.Message)"
    }
    docker volume rm -f $volume | Out-Null
}
MhRestore
Log ""
Log "   the test mh of this run removed from this console; the mh loaded before it (from your profile) put back"
Log "Done. Results: $out"
Log "Tell Claude: the measurements are in $out"
