# D:\Backup Case Bible copies — IN-PLACE sort scan (DRY-RUN ONLY, moves nothing)
# _Byline: Claude Code · Fable 5 · 2026-07-12_
# Emits D:\casebible\backup-sort-plan.csv: one row per TOP-LEVEL item in both copies,
# proposed destination = D:\Backup\CaseBible-sorted\<Domain>\_intake\<name> (v2 domains,
# internals never touched — dir-level rough sort only). Judgment calls => action REVIEW.

$ErrorActionPreference = 'Stop'
$Out = 'D:\casebible\backup-sort-plan.csv'
$Dest = 'D:\Backup\CaseBible-sorted'

# dir-name -> domain routing (v2). Anything unlisted => REVIEW.
$Map = @{
  # KnowledgeBase
  'AI_Chats'='KnowledgeBase'; 'Raw AI Chats'='KnowledgeBase'; 'ChatGPT_ChatGPT_Custody_Case_O'='KnowledgeBase';
  'Clippings'='KnowledgeBase'; 'AI_Resources'='KnowledgeBase'; 'Legal_Knowledge_Base_Obsidian'='KnowledgeBase';
  'Legal_Reference_DUPLICATE'='KnowledgeBase'; 'Legal_Research'='KnowledgeBase'; 'mi-legal-resources'='KnowledgeBase';
  'Reference'='KnowledgeBase'; 'System_Guides'='KnowledgeBase'; 'Context_Files'='KnowledgeBase'; 'Global_Transcripts'='KnowledgeBase';
  # EvidenceVault
  'Evidence'='EvidenceVault'; 'Google Takeout'='EvidenceVault'; 'Snap Export'='EvidenceVault';
  'Snap_Export_2024-11-24'='EvidenceVault'; 'Snap_Export_2025-04-11'='EvidenceVault'; 'Snap_Export_2025-04-25'='EvidenceVault';
  'Snap_Export-0425'='EvidenceVault'; 'Snap_Export-1124'='EvidenceVault'; 'snap data'='EvidenceVault';
  'SMS_KK_Phone'='EvidenceVault'; 'SMS-KK-3592'='EvidenceVault'; 'Attachments(1)'='EvidenceVault';
  # CaseManagement
  'Court'='CaseManagement'; 'Motions_Filings'='CaseManagement'; 'Case_Files'='CaseManagement';
  'Case_Dashboard'='CaseManagement'; 'plans'='CaseManagement'; 'Narrative'='CaseManagement'; 'plannotator'='CaseManagement';
  # Entities
  'people'='Entities'; 'Person Info'='Entities'; 'Person_Info_Backup_2026-03-12'='Entities';
  # Code
  'coercive_control_pipeline'='Code'; 'AI_Evidence_Engine'='Code'; 'STACK_Deployment'='Code';
  'Deployment_Artifacts'='Code'; 'AI_Firm_Strategy'='Code';
  # Triage / Recovered
  'INBOX'='Triage'; 'INBOX_partial_downloads_Empty_2026-03-12'='Triage';
  'Archives'='Recovered'; 'Obsidian Vault'='Recovered'
}
# never move (state/system) — stay with their copy
$Keep = @('.obsidian','.smart-env','.claude','.infio_json_db','_system','_TO_BE_DELETED')
# sensitive — always REVIEW, never auto-route
$Sensitive = @('Secrets_Work_Area')

$rows = [System.Collections.Generic.List[object]]::new()
foreach ($copy in 'D:\Backup\Case Bible','D:\Backup\Case Bible BACKUP 2026-03-12') {
  $tag = Split-Path $copy -Leaf
  foreach ($it in (Get-ChildItem -LiteralPath $copy -Force)) {
    $isDir = $it.PSIsContainer
    if ($isDir) { $m = Get-ChildItem -LiteralPath $it.FullName -Recurse -File -Force -ErrorAction SilentlyContinue | Measure-Object -Sum Length; $files=$m.Count; $mb=[math]::Round(($m.Sum ?? 0)/1MB,1) }
    else { $files=1; $mb=[math]::Round($it.Length/1MB,2) }
    if ($Keep -contains $it.Name) { $action='KEEP-IN-PLACE'; $domain=''; $dst='' }
    elseif ($Sensitive -contains $it.Name) { $action='REVIEW-SENSITIVE'; $domain='?'; $dst='' }
    elseif ($isDir -and $Map.ContainsKey($it.Name)) {
      $action='auto'; $domain=$Map[$it.Name]
      $dst = Join-Path $Dest "$domain\_intake\$($it.Name)"
      if ($rows | Where-Object { $_.new_path -eq $dst }) { $dst = Join-Path $Dest "$domain\_intake\$($it.Name) (from $tag)" }
    }
    elseif (-not $isDir) {
      $domain = switch -Regex ($it.Extension) {
        '^\.(ps1|py|js|json|ini|code-workspace)$' { 'Code' }
        '^\.(md|txt|csv)$'                        { 'KnowledgeBase' }
        '^\.(zip|7z|rar|gz)$'                     { 'Triage' }
        default                                    { '' } }
      if ($domain) { $action='auto'; $sub = if ($domain -eq 'Triage') {'exports-bundles'} else {'_intake\_root-loose'}
        $dst = Join-Path $Dest "$domain\$sub\$($it.Name)" }
      else { $action='REVIEW'; $dst='' }
    }
    else { $action='REVIEW'; $domain='?'; $dst='' }
    $rows.Add([pscustomobject]@{ source_copy=$tag; item=$it.Name; kind=($isDir ? 'dir':'file'); files=$files; size_mb=$mb; domain=$domain; action=$action; new_path=$dst })
  }
}
$rows | Export-Csv -LiteralPath $Out -NoTypeInformation -Encoding utf8
"rows: $($rows.Count) -> $Out  (DRY-RUN, nothing moved)"
"`n=== per-domain/action summary ==="
$rows | Group-Object action, domain | Sort-Object Count -Descending | ForEach-Object { "{0,-38} {1,4} items  {2,10:N1} MB" -f $_.Name, $_.Count, (($_.Group | Measure-Object size_mb -Sum).Sum) }
"`n=== REVIEW rows ==="
$rows | Where-Object action -like 'REVIEW*' | Format-Table source_copy, item, kind, files, size_mb -AutoSize
