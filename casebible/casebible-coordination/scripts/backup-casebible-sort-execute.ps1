# D:\Backup Case Bible copies — sort EXECUTOR (Phase A of full-backup cleanup)
# _Byline: Claude Code · Fable 5 · 2026-07-12_
# Executes backup-sort-plan.csv with REVIEW rows resolved per the v2 spec:
#   wiki->Code/wiki (governance: wiki = coding/app docs), Takeout Data->EvidenceVault (export pkg),
#   timeline_analyzer/TECH_ASSETS_SW->Code, Software Research & Reference->KnowledgeBase,
#   untitled folder/Timeline/Secrets_Work_Area->Triage/_triage (unclassifiable per mapping;
#   Secrets flagged), .obsidianignore->KEEP. Dir-level moves only, internals untouched,
#   everything stays inside D:\Backup. No deletes. Ledgered.

$ErrorActionPreference = 'Stop'
$Plan = Import-Csv 'D:\casebible\backup-sort-plan.csv'
$Dest = 'D:\Backup\CaseBible-sorted'
$L    = 'D:\casebible\casebible-coordination\specs\local-consolidation-ledger.csv'

$Resolve = @{
  'wiki'                          = 'Code\wiki'
  'Takeout Data'                  = 'EvidenceVault\_intake\Takeout Data'
  'timeline_analyzer'             = 'Code\_intake\timeline_analyzer'
  'TECH_ASSETS_SW'                = 'Code\_intake\TECH_ASSETS_SW'
  'Software Research & Reference' = 'KnowledgeBase\_intake\Software Research & Reference'
  'untitled folder'               = 'Triage\_triage\untitled folder'
  'Timeline'                      = 'Triage\_triage\Timeline'
  'Secrets_Work_Area'             = 'Triage\_triage\Secrets_Work_Area'
}

$moved = 0; $skipped = 0; $fail = 0
foreach ($r in $Plan) {
  $src = Join-Path "D:\Backup\$($r.source_copy)" $r.item
  $dst = $r.new_path
  if ($r.action -like 'REVIEW*') {
    if ($Resolve.ContainsKey($r.item)) { $dst = Join-Path $Dest $Resolve[$r.item] }
    elseif ($r.item -eq '.obsidianignore') { $skipped++; continue }
    else { $dst = Join-Path $Dest "Triage\_triage\$($r.item)" }
    if (Test-Path -LiteralPath $dst) { $dst = "$dst (from $($r.source_copy))" }
  }
  elseif ($r.action -ne 'auto') { $skipped++; continue }   # KEEP-IN-PLACE
  if (-not (Test-Path -LiteralPath $src)) { $fail++; Write-Warning "missing: $src"; continue }
  try {
    New-Item -ItemType Directory -Force (Split-Path $dst) | Out-Null
    Move-Item -LiteralPath $src -Destination $dst
    $note = if ($r.item -eq 'Secrets_Work_Area') { 'sort-backup-copy FLAG-SENSITIVE' } else { 'sort-backup-copy' }
    "$($src -replace ',','_'),$($dst -replace ',','_'),$note,$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Add-Content $L
    $moved++
  } catch { $fail++; Write-Warning "FAILED $src -> $dst : $($_.Exception.Message)" }
}
"moved=$moved skipped(keep)=$skipped failed=$fail"
"--- CaseBible-sorted top level ---"
(Get-ChildItem $Dest -Directory).Name
"--- leftovers in source copies (should be keep-list only) ---"
foreach ($c in 'D:\Backup\Case Bible','D:\Backup\Case Bible BACKUP 2026-03-12') { "$c :: $((Get-ChildItem -LiteralPath $c -Force).Name -join ', ')" }
