param(
    [string]$BlenderPath = 'C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe'
)

$sourceDirectory = Join-Path $PSScriptRoot 'vroid_blender_tools'

if (-not (Test-Path -LiteralPath $BlenderPath -PathType Leaf)) {
    throw "Blender executable not found: $BlenderPath"
}

& $BlenderPath --command extension build `
    --source-dir $sourceDirectory `
    --output-dir $PSScriptRoot

exit $LASTEXITCODE
