# OneDrive Case Bible root corral — plan/execute (Phase 1 of the root cleanup)
# _Byline: Claude Code · Fable 5 · 2026-07-11_
# Plan mode (default): writes the move ledger (status=PLANNED), touches NOTHING.
# -Execute: performs the moves from the freshly built plan, rewrites ledger with status=MOVED/FAILED.
# Rules: same-volume Move-Item only (server-side rename, no hydration), no deletes, LiteralPath everywhere.

param(
    [switch]$Execute
)

$ErrorActionPreference = 'Stop'
$Root   = 'C:\Users\matts\OneDrive\Case Bible'
$Ledger = 'D:\casebible\casebible-coordination\specs\onedrive-root-cleanup-ledger.csv'

# --- keep-lists (never moved) ---
$KeepDirs = @(
    'INBOX', '_TO_BE_DELETED', '_system', '_SWEPT',
    '.claude', '.infio_json_db', '.memsearch', '.obsidian', '.remember', '.smart-env',
    '.tmp.drivedownload', '.tmp.driveupload'
)
$KeepFiles = @('.agentignore', '.obsidianignore', '.directory')

# --- sync-conflict / duplicate dirs -> _SWEPT\_sync-conflicts\ ---
$ConflictDirs = @(
    'AI_Chats1', 'Clippings1', 'wiki1', 'plans1', 'transcript1',
    'General_Code_&_Repos1', 'Legal_Knowledge_Base_Obsidian1', 'People Enrichment Files1',
    'Takeout Data1', '_REVIEW_HOLD1',
    'Legal_Reference_DUPLICATE', 'case-bible-reorg-kit (2)', '6EEY0I.plannotator',
    'Unsorted_Empty_2026-03-12', 'INBOX_partial_downloads_Empty_2026-03-12'
)

$Swept     = Join-Path $Root '_SWEPT'
$Conflicts = Join-Path $Swept '_sync-conflicts'
$RootLoose = Join-Path $Swept '_root-loose'
$Recycle   = Join-Path $RootLoose '_recycle-artifacts'

# --- build the move plan ---
$moves = [System.Collections.Generic.List[object]]::new()

foreach ($d in (Get-ChildItem -LiteralPath $Root -Directory -Force)) {
    if ($KeepDirs -contains $d.Name) { continue }
    $kind = if ($ConflictDirs -contains $d.Name) { 'dir-sync-conflict' } else { 'dir-content' }
    $dstParent = if ($kind -eq 'dir-sync-conflict') { $Conflicts } else { $Swept }
    $moves.Add([pscustomobject]@{
        old_path = $d.FullName
        new_path = Join-Path $dstParent $d.Name
        kind     = $kind
        status   = 'PLANNED'
        timestamp = ''
    })
}

foreach ($f in (Get-ChildItem -LiteralPath $Root -File -Force)) {
    if ($KeepFiles -contains $f.Name) { continue }
    $isRecycle = $f.Name -match '^\$(I|R)[A-Z0-9]{6}(\.|$)'
    $kind = if ($isRecycle) { 'file-recycle-artifact' } else { 'file-root-loose' }
    $dstParent = if ($isRecycle) { $Recycle } else { $RootLoose }
    $moves.Add([pscustomobject]@{
        old_path = $f.FullName
        new_path = Join-Path $dstParent $f.Name
        kind     = $kind
        status   = 'PLANNED'
        timestamp = ''
    })
}

# --- plan summary ---
$moves | Group-Object kind | ForEach-Object { "{0,-24} {1,5}" -f $_.Name, $_.Count } | Write-Host
Write-Host ("TOTAL moves planned: {0}" -f $moves.Count)

if (-not $Execute) {
    $moves | Export-Csv -LiteralPath $Ledger -NoTypeInformation -Encoding utf8
    Write-Host "PLAN ONLY — ledger written to $Ledger. Nothing moved."
    exit 0
}

# --- execute ---
$onedrive = Get-Process -Name OneDrive -ErrorAction SilentlyContinue
if (-not $onedrive) { Write-Warning 'OneDrive.exe is NOT running — moves will sync when it next starts.' }

foreach ($p in @($Swept, $Conflicts, $RootLoose, $Recycle)) {
    if (-not (Test-Path -LiteralPath $p)) { New-Item -ItemType Directory -Path $p | Out-Null }
}

$fail = 0
foreach ($m in $moves) {
    try {
        Move-Item -LiteralPath $m.old_path -Destination $m.new_path
        $m.status = 'MOVED'
    } catch {
        $m.status = "FAILED: $($_.Exception.Message)"
        $fail++
    }
    $m.timestamp = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
}

$moves | Export-Csv -LiteralPath $Ledger -NoTypeInformation -Encoding utf8
$moved = ($moves | Where-Object status -eq 'MOVED').Count
Write-Host ("EXECUTED: {0} moved, {1} failed. Ledger: {2}" -f $moved, $fail, $Ledger)
if ($fail -gt 0) { $moves | Where-Object { $_.status -ne 'MOVED' } | Format-Table -AutoSize; exit 1 }
