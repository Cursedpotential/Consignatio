[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$BuildDirectory,
    [string]$ExpectedVersion = '0.0.0-phase0'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$projectRoot = Split-Path $PSScriptRoot -Parent
$BuildDirectory = [IO.Path]::GetFullPath($BuildDirectory)
if (-not $BuildDirectory.StartsWith($projectRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Smoke-test artifacts must remain inside this project.'
}
$ancestor = $BuildDirectory
while ($ancestor.Length -ge $projectRoot.Length) {
    if ((Get-Item -LiteralPath $ancestor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
        throw "Smoke-test path traverses a reparse point: $ancestor"
    }
    $ancestor = [IO.Path]::GetDirectoryName($ancestor)
}
function Get-PESubsystem([string]$Path) {
    $stream = [IO.File]::OpenRead($Path)
    $reader = [IO.BinaryReader]::new($stream)
    try {
        if ($reader.ReadUInt16() -ne 0x5a4d) { throw "Not a PE executable: $Path" }
        $stream.Position = 0x3c
        $peOffset = $reader.ReadUInt32()
        $stream.Position = $peOffset
        if ($reader.ReadUInt32() -ne 0x4550) { throw "Invalid PE signature: $Path" }
        $stream.Position = $peOffset + 24 + 68
        return $reader.ReadUInt16()
    } finally { $reader.Dispose() }
}
foreach ($binary in @('casekit.exe','casekitw.exe')) {
    $path = Join-Path $BuildDirectory $binary
    $expectedSubsystem = if ($binary -eq 'casekit.exe') { 3 } else { 2 }
    if ((Get-PESubsystem $path) -ne $expectedSubsystem) { throw "Wrong subsystem: $binary" }
    $start = [Diagnostics.ProcessStartInfo]::new($path)
    $start.ArgumentList.Add('--version')
    $start.UseShellExecute = $false
    $start.CreateNoWindow = $true
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    $process = [Diagnostics.Process]::Start($start)
    try {
        if (-not $process.WaitForExit(10000)) { throw "Version check timed out: $binary (PID $($process.Id))" }
        $stdout = $process.StandardOutput.ReadToEnd()
        $stderr = $process.StandardError.ReadToEnd()
        if ($process.ExitCode -ne 0 -or $stderr.Length -ne 0 -or $stdout.TrimEnd("`r","`n") -ne $ExpectedVersion) {
            throw "Version check failed: $binary exit=$($process.ExitCode) stdout=$stdout stderr=$stderr"
        }
        Write-Output "PASS $binary subsystem=$expectedSubsystem version=$ExpectedVersion"
    } finally { $process.Dispose() }
}
$linuxPath = Join-Path $BuildDirectory 'casekit-linux-amd64'
if (Test-Path -LiteralPath $linuxPath) {
    $stream = [IO.File]::OpenRead($linuxPath)
    try {
        $header = [byte[]]::new(20)
        if ($stream.Read($header, 0, 20) -ne 20 -or $header[0] -ne 127 -or [Text.Encoding]::ASCII.GetString($header,1,3) -ne 'ELF' -or $header[4] -ne 2 -or $header[18] -ne 62) {
            throw 'Linux artifact is not an ELF64 x86-64 executable'
        }
    } finally { $stream.Dispose() }
    Write-Output 'PASS Linux ELF64 x86-64 header (not executed on Linux)'
}
$shortcutPath = Join-Path $BuildDirectory ('casekitw-smoke-' + [Guid]::NewGuid().ToString('N') + '.lnk')
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = Join-Path $BuildDirectory 'casekitw.exe'
$shortcut.Arguments = '--version'
$shortcut.WorkingDirectory = $BuildDirectory
$shortcut.WindowStyle = 1
$shortcut.Save()
# Normal shell launch: no hidden-window setting masks an incorrect subsystem.
$exitCode = $shell.Run(('"' + $shortcutPath + '"'), 1, $true)
if ($exitCode -ne 0) { throw "Shortcut returned $exitCode" }
Write-Output "PASS normal shortcut launch exited 0: $shortcutPath"
Write-Output 'GUI subsystem verified; physical no-flash observation requires the user.'
