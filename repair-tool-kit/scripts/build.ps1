[CmdletBinding()]
param(
    [ValidateSet('all','windows','linux','verify')][string]$Target = 'all',
    [ValidatePattern('^[A-Za-z0-9._+-]+$')][string]$Version = 'phase0-dev',
    [string]$StateRoot = ''
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$projectRoot = Split-Path $PSScriptRoot -Parent
if ([string]::IsNullOrWhiteSpace($StateRoot)) { $StateRoot = Join-Path $projectRoot 'runtime-codex' }
if (-not [IO.Path]::IsPathRooted($StateRoot)) { $StateRoot = Join-Path $projectRoot $StateRoot }
$resolvedState = [IO.Path]::GetFullPath($StateRoot)
if (-not $projectRoot.StartsWith('E:\AI_Workspace\', [StringComparison]::OrdinalIgnoreCase) -or
    -not $resolvedState.StartsWith($projectRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Build state must remain inside this project under E:\AI_Workspace.'
}
# Reject junction/symlink ancestors that could redirect writes outside the project.
$ancestor = $resolvedState
while ($ancestor.Length -ge $projectRoot.Length) {
    if (Test-Path -LiteralPath $ancestor) {
        if ((Get-Item -LiteralPath $ancestor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw "Build state traverses a reparse point: $ancestor"
        }
    }
    $ancestor = [IO.Path]::GetDirectoryName($ancestor)
}
$savedEnvironment = @{}
$environmentValues = @{
    GOCACHE = Join-Path $resolvedState 'cache\go-build'
    GOPATH = Join-Path $resolvedState 'cache\go'
    GOMODCACHE = Join-Path $resolvedState 'cache\go-mod'
    GOTMPDIR = Join-Path $resolvedState 'tmp'
    TEMP = Join-Path $resolvedState 'tmp'
    TMP = Join-Path $resolvedState 'tmp'
    GOTOOLCHAIN = 'local'
    GOTELEMETRY = 'off'
    GOENV = 'off'
    GOWORK = 'off'
    GOFLAGS = '-p=2'
    GOMAXPROCS = '2'
    GOMEMLIMIT = '512MiB'
    CGO_ENABLED = '0'
    GOOS = 'windows'
    GOARCH = 'amd64'
}
function Invoke-Go {
    param([string[]]$Arguments)
    & go @Arguments
    if ($LASTEXITCODE -ne 0) { throw "go $($Arguments -join ' ') failed ($LASTEXITCODE)" }
}
Push-Location $projectRoot
try {
    foreach ($name in $environmentValues.Keys) {
        $savedEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
        [Environment]::SetEnvironmentVariable($name, $environmentValues[$name], 'Process')
    }
    foreach ($name in @('GOCACHE','GOPATH','GOMODCACHE','GOTMPDIR')) {
        New-Item -ItemType Directory -Path $environmentValues[$name] -Force | Out-Null
    }
    # Unique output directories preserve every earlier build; no executable replacement.
    $runId = (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '-' + [Guid]::NewGuid().ToString('N').Substring(0,8)
    $output = Join-Path $resolvedState "builds\$runId"
    New-Item -ItemType Directory -Path $output | Out-Null
    Write-Output "Build output: $output"
    Write-Output "State root: $resolvedState"
    Invoke-Go @('mod','download','all')
    if ($Target -in @('all','verify')) {
        Invoke-Go @('vet','./...')
        Invoke-Go @('build','./...')
        Invoke-Go @('test','-count=1','-v','./...')
    }
    if ($Target -in @('all','windows','verify')) {
        Invoke-Go @('build','-trimpath','-ldflags',"-X main.version=$Version -X 'casekit/internal/config.ProjectRoot=$projectRoot'",'-o',"$output\casekit.exe",'./cmd/casekit')
        Invoke-Go @('build','-trimpath','-ldflags',"-H windowsgui -X main.version=$Version -X 'casekit/internal/config.ProjectRoot=$projectRoot'",'-o',"$output\casekitw.exe",'./cmd/casekitw')
        & "$output\casekit.exe" --version
        if ($LASTEXITCODE -ne 0) { throw 'Console version check failed' }
    }
    if ($Target -in @('all','linux')) {
        $env:GOOS = 'linux'
        Invoke-Go @('build','-trimpath','-ldflags',"-X main.version=$Version",'-o',"$output\casekit-linux-amd64",'./cmd/casekit')
    }
    Write-Output "Completed: $output"
} finally {
    foreach ($name in $savedEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($name, $savedEnvironment[$name], 'Process')
    }
    Pop-Location
}
