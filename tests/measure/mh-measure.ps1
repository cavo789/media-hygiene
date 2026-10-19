# mh-measure.ps1 - the measurements only the maintainer's Windows + Docker Desktop can give.
#
# Runs, one after the other, the measurements the PARTIAL TODOs wait for, and writes the lines
# that matter to one text file Claude reads afterwards (from the devcontainer, through a
# read-only mount of C:\). Windows PowerShell 5.1, ASCII only (an accented byte breaks the
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
#      another program listening on 8088: mh review names it, the probe timed     (0253)
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
#      mount -t drvfs in the distribution (what mh.sh does)                     (0254)
#  12. clean of photos on another drive (-OtherDrive, else the first drive but C: with 2 GB
#      free), quarantine on C:: the line before the question names both drives, the size and
#      C:'s free space (checked against Windows'); quarantine on that drive: no line   (0182)
#  13. 1 GB set aside from another drive (-OtherDrive, else the first drive but C: with 3 GB
#      free): to the quarantine on C: (copy E: -> C:), then to that drive's own quarantine
#      /quarantine/x (copy E: -> E:): wall time of each clean and undo; then undo without
#      the drive's quarantine mounted must refuse, naming the drive                  (0183)
#  14. mh menu by hand, old console then your usual one: colours, columns, a number +
#      Enter, Ctrl+C; then mh alone: the home page, a step run from it, the page back,
#      Home from a review page, Quit; asks what you saw                        (0172, 0210)
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
#   .\mh-measure.ps1 -Only 20 -Count 1 -Sample 1000 -Cpus 4 -Branch iterate/2026-10-17   (image embeddings)
#   .\mh-measure.ps1 -Only 21 -Count 1 -Nas 192.168.1.2 -NasShare photo -NasUser me   (the NAS, read-only)
#   .\mh-measure.ps1 -Only 22 -Count 3   (a pair keeping both names: hard links, 0213)

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
    [string]$NasUser = ""
)

$ErrorActionPreference = "Stop"
# The tool writes UTF-8 (emoji, table borders): read docker's output as such, not as the
# console code page, which garbles them.
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$stamp = Get-Date -Format "yyyyMMdd-HHmm"
$outDir = Join-Path $HOME "media-hygiene"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$out = Join-Path $outDir "measures-$stamp.txt"
$wanted = 'Time per step|Duration|Report written|moved or renamed|unchanged folder|Reading 128 KB|copies|Error|first time|Next audit|No new or changed|per photo|A full run|faces in|Left out|Source folders removed|will be copied|Not enough room|not mounted'

function Log([string]$text) {
    Add-Content -Path $out -Value $text -Encoding UTF8
    Write-Host $text
}

function MhLeftovers([string]$part) {
    foreach ($id in @(& docker ps --quiet)) {
        $binds = "$(& docker inspect $id --format '{{json .HostConfig.Binds}}' 2>$null)"
        if (-not $binds.Contains($Work.Replace('\', '\\'))) { continue }
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
$menu = @(mh menu 2>&1 | ForEach-Object { "$_" })
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
if (Wanted 10) {
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
    $popup = Read-Host "10c. Click Run on the line mh audit. Does the page say 'mh audit runs in the PowerShell window of mh (in the taskbar)'? Wait 30 s: does it add 'Nothing moves? Look at ...'? (y/y, y/n, n/n...)"
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

    # 10f (0253): which program Windows names for a port a container publishes (Docker
    # Desktop's own listener, never "another program"), then another program on 8088: mh
    # review must name it in one line, never Docker's raw error; the probe timed.
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
    $picked = Join-Path $Work "Picked photos"
    New-Item -ItemType Directory -Force -Path $picked | Out-Null
    Get-ChildItem -Path (Join-Path $data "flat") -File | Select-Object -First 2 | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $picked ("picked-" + $_.Name)) }
    Write-Host "11f. A folder window opens: choose $picked (This PC, then the folders), then OK."
    $said = @(mh folders add 6>&1 | ForEach-Object { "$_" })
    foreach ($line in $said) { Log ("   11f. " + $line) }
    Log ("   11f. the file names the folder chosen: " + [bool](Select-String -LiteralPath $mhFile -SimpleMatch -Pattern $picked -Quiet))
    $front = Read-Host "11f. Did the window open in front of this console, without Alt+Tab? (y/n)"
    Log "   11f. window in front of the console: $front"
    $before = (Get-FileHash -LiteralPath $mhFile).Hash
    Write-Host "11g. The folder window opens again: click Cancel."
    $said = @(mh folders add 6>&1 | ForEach-Object { "$_" })
    foreach ($line in $said) { Log ("   11g. cancelled: " + $line) }
    Log ("   11g. mh.ps1 unchanged after cancel: " + ($before -eq (Get-FileHash -LiteralPath $mhFile).Hash))
    $avast = Read-Host "11g. Did your antivirus say anything during 11f or 11g? (n, or what it said)"
    Log "   11g. antivirus: $avast"
    $null = @(mh folders remove $picked 6>&1)

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
    $null = @(mh undo --yes 2>&1)
    Log "   11i. mh undo of that clean: exit code $LASTEXITCODE"
    if ("$kind" -eq 'Removable') {
        # 11k (0254): from your WSL distribution (Docker Desktop's integration on): is the
        # interop on, is the stick in /mnt, and which mount does a container started from
        # WSL see: the distribution's /mnt/x once mounted there (as mh.sh does), or not.
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
        Log ("   11k. mount -t drvfs ${letter}: /mnt/$low in $distro (as mh.sh does with sudo): exit code $LASTEXITCODE " + ($said -join ' / '))
        $seen = @(& wsl.exe -e docker run --rm -v "${wslPath}:/x:ro" --entrypoint ls $Image /x 2>&1)
        Log ("   11k. files a container from WSL sees, mounted in $distro (planted: $planted expected): exit code $LASTEXITCODE, " + @($seen).Count + " lines")
        $vm = @(& wsl.exe -d docker-desktop sh -c "grep ' /mnt/host/$low ' /proc/mounts || echo none" 2>&1 | ForEach-Object { "$_" })
        Log ("   11k. drive ${letter}: in Docker Desktop's VM meanwhile (none: the distribution's mount is what counts): " + ($vm -join ' / '))
        $said = @(& wsl.exe -u root -e umount "/mnt/$low" 2>&1 | ForEach-Object { "$_" })
        Log ("   11k. umount /mnt/$low in ${distro}: exit code $LASTEXITCODE " + ($said -join ' / '))
        # 0252: after each command mh unshares the stick, so Windows can eject it.
        $ejected = Read-Host "11j. Safely remove ${letter}: now (taskbar, Safely Remove Hardware, Eject). Did Windows let you, without 'This device is currently in use'? (y/n, or what it said)"
        Log "   11j. ${letter}: ejected safely after the mh commands: $ejected"
        $null = Read-Host "11j. Plug ${letter}: back in (same letter), then press Enter"
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
    } else {
        $driveRoot = Join-Path ($drive13.TrimEnd('\') + "\") "mh-measure-13"
        $driveData = Join-Path $driveRoot "data"
        $driveQuarantine = Join-Path $driveRoot "quarantine"
        foreach ($folder in "data\a", "data\b", "quarantine") {
            New-Item -ItemType Directory -Force -Path (Join-Path $driveRoot $folder) | Out-Null
        }
        $bytes = 0
        $files = 0
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
    Write-Host "    Then click Run on a 'review' step; on that page, click the Home link at the bottom right."
    Write-Host "    Finally click Quit on the home page."
    $opened = Read-Host "14h. mh alone opened the home page in the browser? (y/n)"
    $asked = Read-Host "14h. Run on 'clean' ran it in the PowerShell window, with its question? (y/n)"
    $back = Read-Host "14h. After it, the home page came back by itself (reloaded)? (y/n)"
    $homeLink = Read-Host "14h. Home from the review page brought the home page back? (y/n)"
    $quit = Read-Host "14h. Quit gave the PowerShell prompt back, no red error? (y/n)"
    Log "   14h (home page): opened $opened, clean in the console $asked, page back $back, Home from review $homeLink, Quit clean $quit"
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
            $said = @(mh phone 6>&1 | ForEach-Object { "$_" })
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
}

# --- 20: image embeddings, a bench on photos of C:\Photos (0220, for 0221) ------------------
# Downloads the bench (tests/measure/embeddings of the -Branch) under -Work; the models once
# into $HOME\media-hygiene\embeddings-models (2.5 GB, kept for the next runs: delete that
# folder to get the room back); the pages into $HOME\media-hygiene\embeddings-<stamp>. The
# searches come from $HOME\media-hygiene\embeddings-queries.txt: the first time, the step
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
        Log "   20d. open $(Join-Path $pages 'index.html'), tick the searches and the pairs, download both JSON files, then tell Claude where they are"
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
    names = sorted(name for name in names if not name.startswith(('@', '#')))
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
        ftp.cwd('/' + share)
    say('the share as FTP shows it: ' + ftp.pwd())
    mlsd = offered['MLSD'] or offered['MLST']
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
    start = time.monotonic()
    parts = 0
    for path in photos[:10]:
        size = ftp.size(path) or 0
        partial(ftp, path, None)
        partial(ftp, path, max(size - CHUNK, 0))
        parts += 1
    say('first and last 64 KiB: %d photos, %.2f s per photo' % (parts, (time.monotonic() - start) / max(parts, 1)))
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
            if ($NasUser -eq "") { $NasUser = Read-Host "21c. User name on the NAS" }
            $secure = Read-Host "21c. Password of $NasUser on the NAS (never logged)" -AsSecureString
            $credential = New-Object System.Management.Automation.PSCredential($NasUser, $secure)
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
                    $yearName = @($tops | Where-Object { $_ -match '^(19|20)\d\d$' })[0]
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
                    # 20 photos read whole into memory: nothing copied to disk.
                    $photos = @($files | Where-Object { $_.Extension -match '^\.(jpe?g|heic)$' } | Select-Object -First 20)
                    $buffer = New-Object byte[] 1048576
                    $read = 0
                    $watch = [Diagnostics.Stopwatch]::StartNew()
                    foreach ($photo in $photos) {
                        $stream = [IO.File]::OpenRead($photo.FullName)
                        try { while (($count = $stream.Read($buffer, 0, $buffer.Length)) -gt 0) { $read += $count } } finally { $stream.Close() }
                    }
                    $seconds = [Math]::Max($watch.Elapsed.TotalSeconds, 0.001)
                    $speed = "{0} photos, {1:N1} MB in {2:N1} s = {3:N2} MB/s" -f $photos.Count, ($read / 1MB), $seconds, ($read / 1MB / $seconds)
                    Log "   21d. read whole: $speed"
                    # The same photos for the container (21e, 21f), relative to the share.
                    $relative = @($photos | ForEach-Object { $_.FullName.Substring($root.Length).Replace('\', '/') })
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
                # 21f: a Docker CIFS volume, read-only; SMB 3.0, else 2.1. The volume keeps the
                # password in its options: removed right after, and in the finally.
                if ($script:nasSecret -match '[,"]') {
                    Log "   21f. skipped: the password holds a comma or a double quote, which the CIFS options cannot carry"
                } else {
                    foreach ($version in '3.0', '2.1') {
                        & docker volume rm -f $nasVolume 2>&1 | Out-Null
                        $made = @(& docker volume create --driver local --opt type=cifs --opt "device=//$ip/$NasShare" --opt "o=addr=$ip,username=$NasUser,password=$($script:nasSecret),ro,vers=$version" $nasVolume 2>&1 | ForEach-Object { "$_" })
                        if ($LASTEXITCODE -ne 0) { NasLog ("   21f. vers=${version}: volume refused: " + ($made -join ' / ')); continue }
                        $run = NasDocker "21f vers=$version" @("-v", "${nasVolume}:/nas:ro", "-v", "${nasProbe}:/probe:ro", "--entrypoint", "python", $Image, "/probe/nas_probe.py", "smb", $yearName)
                        & docker volume rm -f $nasVolume 2>&1 | Out-Null
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
Log ""
Log "Done. Results: $out"
Log "Tell Claude: the measurements are in $out"
