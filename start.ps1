[CmdletBinding()]
param(
    [switch] $SkipInstall,

    [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
    [string[]] $ZenCadArguments
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([System.Environment]::OSVersion.Platform -ne [System.PlatformID]::Win32NT) {
    throw "start.ps1 is intended for Windows."
}

$projectRoot = $PSScriptRoot
$venvDirectory = Join-Path $projectRoot "venv"
$venvPython = Join-Path $venvDirectory "Scripts\python.exe"
$probeCode = @'
import json, platform, struct, sys
print(json.dumps({
    "architecture": struct.calcsize("P") * 8,
    "implementation": platform.python_implementation(),
    "version": platform.python_version(),
    "version_info": list(sys.version_info[:3]),
}))
'@

function Find-SupportedPython {
    $candidates = [System.Collections.Generic.List[object]]::new()

    if ($env:ZENCAD_PYTHON) {
        $candidates.Add([pscustomobject]@{
            File = $env:ZENCAD_PYTHON
            Arguments = @()
            Label = "ZENCAD_PYTHON"
        })
    }

    $python = Get-Command "python.exe" -ErrorAction SilentlyContinue
    if ($python) {
        $candidates.Add([pscustomobject]@{
            File = $python.Source
            Arguments = @()
            Label = "python.exe"
        })
    }

    $launcher = Get-Command "py.exe" -ErrorAction SilentlyContinue
    if ($launcher) {
        $candidates.Add([pscustomobject]@{
            File = $launcher.Source
            Arguments = @("-3")
            Label = "py.exe -3"
        })
    }

    foreach ($candidate in $candidates) {
        try {
            $prefixArguments = $candidate.Arguments
            $probeOutput = & $candidate.File @prefixArguments -c $probeCode 2>$null
            if ($LASTEXITCODE -ne 0) {
                continue
            }
            $probe = $probeOutput | ConvertFrom-Json
            $versionInfo = $probe.version_info
            $supportedVersion = (
                $versionInfo[0] -eq 3 -and
                $versionInfo[1] -ge 10 -and
                $versionInfo[1] -lt 15
            )
            if (
                $probe.implementation -eq "CPython" -and
                $probe.architecture -eq 64 -and
                $supportedVersion
            ) {
                return [pscustomobject]@{
                    File = $candidate.File
                    Arguments = $candidate.Arguments
                    Label = $candidate.Label
                    Version = $probe.version
                }
            }
        }
        catch {
            continue
        }
    }

    throw @"
64-bit CPython 3.10-3.14 was not found.
Install it from https://www.python.org/downloads/windows/ and enable
'Add python.exe to PATH', or set ZENCAD_PYTHON to the full python.exe path.
"@
}

$basePython = Find-SupportedPython
Write-Host "Using $($basePython.Label): Python $($basePython.Version)"

if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
    if (Test-Path -LiteralPath $venvDirectory) {
        throw "The existing '$venvDirectory' is not a valid Windows virtual environment."
    }

    Write-Host "Creating virtual environment in '$venvDirectory'..."
    $baseArguments = $basePython.Arguments
    & $basePython.File @baseArguments -m venv $venvDirectory
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create the virtual environment (exit code $LASTEXITCODE)."
    }
}

if (-not $SkipInstall) {
    Write-Host "Installing ZenCad and its GUI dependencies..."
    & $venvPython -m pip install --editable "${projectRoot}[gui]"
    if ($LASTEXITCODE -ne 0) {
        throw "Dependency installation failed (exit code $LASTEXITCODE)."
    }
}

Write-Host "Starting ZenCad..."
& $venvPython -m zencad @ZenCadArguments
if ($LASTEXITCODE -ne 0) {
    throw "ZenCad exited with code $LASTEXITCODE."
}
