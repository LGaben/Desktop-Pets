param(
    [string]$Python = 'python',
    [switch]$InstallLockedDependencies,
    [string]$SignThumbprint,
    [string]$SignTool,
    [string]$TimestampUrl
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$buildArguments = @((Join-Path $repoRoot 'scripts\build_release.py'))
if ($InstallLockedDependencies) { $buildArguments += '--install' }
if ($SignThumbprint) {
    $buildArguments += @('--sign-thumbprint', $SignThumbprint, '--signtool', $SignTool, '--timestamp-url', $TimestampUrl)
}
& $Python @buildArguments
exit $LASTEXITCODE
