$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Bin = Get-Command blender -ErrorAction SilentlyContinue
if ($Bin) {
    $BlenderExe = $Bin.Source
} else {
    $InstallRoot = Join-Path $env:ProgramFiles "Blender Foundation"
    if (Test-Path $InstallRoot) {
        $Candidate = Get-ChildItem $InstallRoot -Filter "blender.exe" -Recurse -File -ErrorAction SilentlyContinue |
            Sort-Object FullName -Descending |
            Select-Object -First 1
        if ($Candidate) { $BlenderExe = $Candidate.FullName }
    }
}
if (-not $BlenderExe) {
    throw "Blender executable not found. Add blender.exe to PATH or install under Program Files\Blender Foundation."
}
Write-Host "Using Blender: $BlenderExe"
& $BlenderExe --background --python "blender/scripts/build_smoke_test.py"
if ($LASTEXITCODE -ne 0) { throw "Blender exited with code $LASTEXITCODE" }

$Blend = "blender/generated/smoke_test.blend"
$Glb = "godot/assets/generated/smoke_test.glb"
if (-not (Test-Path $Blend) -or -not (Test-Path $Glb)) {
    throw "Missing smoke-test outputs."
}
Write-Host "SUCCESS: generated $Blend and $Glb" -ForegroundColor Green
Write-Host "Next: open Blender source and godot/project.godot."
