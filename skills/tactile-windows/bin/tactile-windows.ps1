$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$skillDir = Resolve-Path (Join-Path $scriptDir "..")
$python = $env:TACTILE_WINDOWS_PYTHON
if (-not $python) {
  $python = "python"
}

& $python (Join-Path $skillDir "scripts\windows_interface.py") @args
exit $LASTEXITCODE
