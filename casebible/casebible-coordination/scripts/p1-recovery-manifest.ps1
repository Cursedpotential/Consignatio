# P1 — Recovery manifest + verification prep (READ-ONLY: hashes and lists, moves nothing)
# _Byline: Claude Code · Fable 5 · 2026-07-12_
# D: is READ-ONLY (owner-locked) — coordination artifacts now live under
# E:\AI_Workspace\Projects\the-platform-workspace\casebible-coordination-e\ until D: is released.
# Manifests the E: recovery set (+ optional extra roots) with size+MD5, ready to bucket against
# the July-1 D:\Backup manifest (md5 list: D:\casebible\backup-manifest-missing.csv — read from D: is fine).
# Output: casebible-coordination-e\manifests\e-recovery-manifest-<stamp>.csv
# MD5 matches the July-1 manifest algorithm. ~106GB ≈ 10-25 min hashing.
# Run AFTER recovery runs finish (a moving target manifests twice).

param(
    [string[]]$Roots = @('E:\Disk Drill', 'E:\$R0FF85V', 'E:\$R9UM6AT', 'E:\$RVCPI6B', 'E:\court'),
    [string]$OutDir = 'E:\AI_Workspace\Projects\the-platform-workspace\casebible-coordination-e\manifests'
)
$ErrorActionPreference = 'Continue'
New-Item -ItemType Directory -Force $OutDir | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmm'
$out = Join-Path $OutDir "e-recovery-manifest-$stamp.csv"
'root,relative_path,size,mtime,md5' | Set-Content $out -Encoding utf8

$total = 0
foreach ($root in $Roots) {
    if (-not (Test-Path -LiteralPath $root)) { Write-Warning "skip missing root: $root"; continue }
    Write-Host "hashing $root ..."
    Get-ChildItem -LiteralPath $root -Recurse -File -Force -ErrorAction SilentlyContinue | ForEach-Object {
        $md5 = try { (Get-FileHash -LiteralPath $_.FullName -Algorithm MD5 -ErrorAction Stop).Hash.ToLower() } catch { 'HASH_ERROR' }
        $rel = $_.FullName.Substring($root.Length).TrimStart('\') -replace ',', '_'
        "$($root -replace ',','_'),$rel,$($_.Length),$($_.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss')),$md5" | Add-Content $out
        $total++
        if ($total % 500 -eq 0) { Write-Host "  $total files hashed..." }
    }
}
Write-Host "DONE: $total files -> $out"
