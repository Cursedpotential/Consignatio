# OneDrive Case Bible — Phase 2 clone-pair merge EXECUTOR
# _Byline: Claude Code · Fable 5 · 2026-07-11_
# Executes exactly the rows in D:\casebible\merge-plan.csv (owner-approved 2026-07-11;
# Takeout Data merges at top level only — relative paths preserved, no deeper reorganization).
# No deletes ever: "losing" identical copies land in _SWEPT\_merge-quarantine\<pair>\<relpath>.
# Appends every completed move to the Phase 1 ledger.

$ErrorActionPreference = 'Stop'
$PlanCsv = 'D:\casebible\merge-plan.csv'
$Ledger  = 'D:\casebible\casebible-coordination\specs\onedrive-root-cleanup-ledger.csv'

$rows = Import-Csv -LiteralPath $PlanCsv
Write-Host "plan rows: $($rows.Count)"

# pre-create every destination parent dir (batched, much faster than per-file checks)
$parents = $rows | ForEach-Object { Split-Path $_.dst } | Sort-Object -Unique
foreach ($p in $parents) {
    if (-not (Test-Path -LiteralPath $p)) { New-Item -ItemType Directory -Path $p -Force | Out-Null }
}
Write-Host "destination dirs ensured: $($parents.Count)"

$done = [System.Collections.Generic.List[object]]::new()
$fail = 0
foreach ($r in $rows) {
    $status = 'MOVED'
    try {
        switch -Wildcard ($r.action) {
            'move-unique'            { Move-Item -LiteralPath $r.src -Destination $r.dst }
            'keep-both'              { Move-Item -LiteralPath $r.src -Destination $r.dst }
            'identical-keep-primary' { Move-Item -LiteralPath $r.src -Destination $r.dst }  # clone copy -> quarantine
            'identical-keep-clone'   {
                # primary copy -> quarantine, clone takes its place
                $primaryPath = Join-Path (Split-Path $r.dst -Parent) ''  # not used; explicit below
                throw 'identical-keep-clone rows require manual handling (none expected in this plan)'
            }
            default { throw "unknown action '$($r.action)'" }
        }
    } catch {
        $status = "FAILED: $($_.Exception.Message)"
        $fail++
    }
    $done.Add([pscustomobject]@{
        old_path = $r.src; new_path = $r.dst
        kind = "merge:$($r.action)"; status = $status
        timestamp = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
    })
}

$done | Export-Csv -LiteralPath $Ledger -NoTypeInformation -Encoding utf8 -Append
$moved = ($done | Where-Object status -eq 'MOVED').Count
Write-Host ("EXECUTED: {0} moved, {1} failed (ledger appended)" -f $moved, $fail)
if ($fail -gt 0) { $done | Where-Object { $_.status -ne 'MOVED' } | Select-Object -First 20 | Format-Table -Wrap }
