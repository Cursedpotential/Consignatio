# OneDrive Case Bible — Phase 2 clone-pair merge scan (DRY-RUN ONLY, metadata-only, no hydration)
# _Byline: Claude Code · Fable 5 · 2026-07-11_
# Emits D:\casebible\merge-plan.csv — one row per clone file with the action the locked rules dictate.
# Rules (owner, 2026-07-11):
#   clone-only file                  -> move-unique            (fills gap in primary)
#   same relpath, different size     -> keep-both              (clone lands beside primary as name~dup.ext)
#   same relpath+size, primary older -> identical-keep-primary (clone copy -> _merge-quarantine)
#   same relpath+size, clone older   -> identical-keep-clone   (primary copy -> _merge-quarantine, clone takes its place)
# Anything odd -> REVIEW. This script MOVES NOTHING.

$ErrorActionPreference = 'Stop'
$Swept = 'C:\Users\matts\OneDrive\Case Bible\_SWEPT'
$Conf  = Join-Path $Swept '_sync-conflicts'
$OutCsv = 'D:\casebible\merge-plan.csv'

$Pairs = @('AI_Chats','Clippings','wiki','plans','transcript','General_Code_&_Repos',
           'Legal_Knowledge_Base_Obsidian','People Enrichment Files','Takeout Data','_REVIEW_HOLD')

function Get-FileMap([string]$base) {
    $map = @{}
    if (-not (Test-Path -LiteralPath $base)) { return $map }
    foreach ($f in (Get-ChildItem -LiteralPath $base -Recurse -File -Force)) {
        $rel = $f.FullName.Substring($base.Length).TrimStart('\')
        $map[$rel] = $f
    }
    return $map
}

$rows = [System.Collections.Generic.List[object]]::new()
foreach ($p in $Pairs) {
    $priBase = Join-Path $Swept $p
    $cloBase = Join-Path $Conf ($p + '1')
    $pri = Get-FileMap $priBase
    $clo = Get-FileMap $cloBase

    foreach ($rel in $clo.Keys) {
        $cf = $clo[$rel]
        if (-not $pri.ContainsKey($rel)) {
            $action = 'move-unique'; $dst = Join-Path $priBase $rel; $note = ''
            $pf = $null
        } else {
            $pf = $pri[$rel]
            if ($pf.Length -ne $cf.Length) {
                $action = 'keep-both'
                $dir = Split-Path (Join-Path $priBase $rel)
                $bn  = [IO.Path]::GetFileNameWithoutExtension($cf.Name); $ext = $cf.Extension
                $dst = Join-Path $dir ($bn + '~dup' + $ext)
                $note = 'same name, different size'
            } elseif ($pf.LastWriteTimeUtc -le $cf.LastWriteTimeUtc) {
                $action = 'identical-keep-primary'
                $dst = Join-Path (Join-Path $Swept "_merge-quarantine\$p") $rel
                $note = 'same size; primary is older/equal -> clone copy quarantined'
            } else {
                $action = 'identical-keep-clone'
                $dst = Join-Path (Join-Path $Swept "_merge-quarantine\$p") $rel
                $note = 'same size; CLONE is older -> primary copy quarantined, clone takes its place'
            }
        }
        $rows.Add([pscustomobject]@{
            pair = $p; relative_path = $rel; action = $action
            src = $cf.FullName; dst = $dst
            size_src = $cf.Length; size_dst = if ($pf) { $pf.Length } else { '' }
            mtime_src = $cf.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss')
            mtime_dst = if ($pf) { $pf.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss') } else { '' }
            note = $note
        })
    }
    "{0,-32} primary={1,6}  clone={2,6}" -f $p, $pri.Count, $clo.Count | Write-Host
}

$rows | Export-Csv -LiteralPath $OutCsv -NoTypeInformation -Encoding utf8
Write-Host "`n=== per-action totals ==="
$rows | Group-Object action | Sort-Object Count -Descending | ForEach-Object { "{0,-24} {1,6}" -f $_.Name, $_.Count } | Write-Host
Write-Host "rows: $($rows.Count) -> $OutCsv  (DRY-RUN: nothing moved)"
