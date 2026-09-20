# Updated by: Codex (case-bible/mp-handoff-protocol) | Date: 2026-09-12 | Rev: 2 | Platform: Codex / win32 | Changes: Qualify the built-in archive cmdlet | Context: PSCX shadows Expand-Archive with an incompatible parameter set on this host
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$release = '26.07.0-0'
$archiveSha256 = 'A711B0563B06EDC488583D28198B6734C5A494AFBBD1B9D87D3D2866062FB7E2'
$downloadUri = 'https://github.com/oschwartz10612/poppler-windows/releases/download/v26.07.0-0/Release-26.07.0-0.zip'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$runtimeRoot = [IO.Path]::GetFullPath((Join-Path $projectRoot 'runtime-codex'))
$downloadRoot = Join-Path $runtimeRoot 'downloads\poppler-windows'
$engineParent = Join-Path $runtimeRoot 'engines\poppler-windows-amd64'
$engineRoot = Join-Path $engineParent 'poppler-26.07.0'
$executable = Join-Path $engineRoot 'Library\bin\pdftotext.exe'
$archive = Join-Path $downloadRoot "Release-$release.zip"
$receiptRoot = Join-Path $runtimeRoot 'receipts'
$receiptPath = Join-Path $receiptRoot 'poppler-windows-amd64.json'
$quarantineRoot = Join-Path $projectRoot 'to_be_deleted\poppler-install'

foreach ($path in @($runtimeRoot, $downloadRoot, $engineParent, $receiptRoot, $quarantineRoot)) {
    $full = [IO.Path]::GetFullPath($path)
    if (-not $full.StartsWith($projectRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing path outside project: $full"
    }
}

function Move-ToQuarantine {
    param([Parameter(Mandatory)][string]$LiteralPath, [Parameter(Mandatory)][string]$Label)
    if (-not (Test-Path -LiteralPath $LiteralPath)) { return }
    New-Item -ItemType Directory -Force -Path $quarantineRoot | Out-Null
    $destination = Join-Path $quarantineRoot ("{0}-{1}-{2}" -f (Get-Date -Format 'yyyyMMdd-HHmmss-fff'), $Label, [guid]::NewGuid().ToString('N'))
    Move-Item -LiteralPath $LiteralPath -Destination $destination
    Write-Warning "Moved superseded material to $destination; only the owner deletes quarantine contents."
}

New-Item -ItemType Directory -Force -Path $downloadRoot, $engineParent, $receiptRoot | Out-Null

if (Test-Path -LiteralPath $archive) {
    $observedArchiveHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $archive).Hash
    if ($observedArchiveHash -ne $archiveSha256) {
        Move-ToQuarantine -LiteralPath $archive -Label 'archive-hash-mismatch'
    }
}

if (-not (Test-Path -LiteralPath $archive)) {
    $partial = "$archive.partial-$([guid]::NewGuid().ToString('N'))"
    try {
        Invoke-WebRequest -Uri $downloadUri -OutFile $partial -UseBasicParsing
        $observedArchiveHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $partial).Hash
        if ($observedArchiveHash -ne $archiveSha256) {
            Move-ToQuarantine -LiteralPath $partial -Label 'download-hash-mismatch'
            throw "Poppler archive SHA-256 mismatch: expected $archiveSha256, observed $observedArchiveHash"
        }
        Move-Item -LiteralPath $partial -Destination $archive
    }
    catch {
        if (Test-Path -LiteralPath $partial) {
            Move-ToQuarantine -LiteralPath $partial -Label 'failed-download'
        }
        throw
    }
}

$observedArchiveHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $archive).Hash
if ($observedArchiveHash -ne $archiveSha256) {
    throw "Verified archive changed unexpectedly: expected $archiveSha256, observed $observedArchiveHash"
}

if (-not (Test-Path -LiteralPath $executable -PathType Leaf)) {
    if (Test-Path -LiteralPath $engineRoot) {
        Move-ToQuarantine -LiteralPath $engineRoot -Label 'incomplete-engine'
    }
    $stagingRoot = Join-Path $runtimeRoot ("install-staging\poppler-{0}" -f [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Force -Path $stagingRoot | Out-Null
    try {
        Microsoft.PowerShell.Archive\Expand-Archive -LiteralPath $archive -DestinationPath $stagingRoot
        $expanded = Join-Path $stagingRoot 'poppler-26.07.0'
        $expandedExecutable = Join-Path $expanded 'Library\bin\pdftotext.exe'
        if (-not (Test-Path -LiteralPath $expandedExecutable -PathType Leaf)) {
            throw "Archive did not contain expected executable: $expandedExecutable"
        }
        Move-Item -LiteralPath $expanded -Destination $engineRoot
        Move-ToQuarantine -LiteralPath $stagingRoot -Label 'empty-staging'
    }
    catch {
        if (Test-Path -LiteralPath $stagingRoot) {
            Move-ToQuarantine -LiteralPath $stagingRoot -Label 'failed-staging'
        }
        throw
    }
}

$versionText = (& $executable -v 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($versionText)) {
    throw "pdftotext version probe failed with exit $LASTEXITCODE"
}
$executableHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $executable).Hash
$receipt = [ordered]@{
    schema_version = 1
    engine_profile_id = 'poppler-windows-amd64'
    source = [ordered]@{
        release = $release
        uri = $downloadUri
        archive_path = [IO.Path]::GetFullPath($archive)
        archive_bytes = (Get-Item -LiteralPath $archive).Length
        archive_sha256 = $observedArchiveHash.ToLowerInvariant()
    }
    executable = [ordered]@{
        resolved_path = [IO.Path]::GetFullPath($executable)
        sha256 = $executableHash.ToLowerInvariant()
        version_output = $versionText
    }
    installed_at = (Get-Date).ToUniversalTime().ToString('o')
    scope = 'project-contained development/test engine; no PATH or system package changes'
}
$receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $receiptPath -Encoding utf8

$receipt | ConvertTo-Json -Depth 6
