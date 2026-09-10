# Malloc's Vroid Blender Tools

Simple VRoid cleanup tools for Blender 5.0+.

Use this extension with **`.vrm` files exported from VRoid Studio**.
It does **not** open or edit VRoid Studio's `.vroid` project files.

- **Bones:** clean VRoid bone names with Blender-style `.L` / `.R` suffixes.
- **Mesh:** separate selected meshes by material.
- **Convert:** transfer basic MToon inputs to Principled BSDF.
- **Rename:** clean material names, such as
  `N00_000_00_FaceMouth_00_FACE (Instance)` → `FaceMouth`.
  Or rename selected objects and their mesh data from their material names.

Each operation has its own action.
Material conversion, material renaming, and object naming are independent.

## Requirements

- Blender 5.0 or newer.
- The official [VRM Add-on for Blender](https://vrm-addon-for-blender.info/en-us/),
  installed and enabled in a version that supports your Blender version.
- A VRoid model imported through that add-on as VRM 0.x or VRM 1.0.

Mesh separation and object/mesh naming also work on ordinary Blender meshes.
These two operations do not require VRM metadata or the VRM Add-on.

## Install

1. Download `vroid_blender_tools-0.3.0.zip` from the
   [GitHub release assets](https://github.com/kanzaki1201/malloc-vroid-blender-tools/releases/latest).
2. In Blender, open **Edit → Preferences → Get Extensions**.
3. Open the menu at the top right and select **Install from Disk**.
4. Select the downloaded ZIP and enable **Malloc's Vroid Blender Tools**.

Use the built extension ZIP, not the GitHub source ZIP or `__init__.py`.

## Quick use

Save a copy of your model before making changes.

1. Export a `.vrm` from VRoid Studio, then import it with the official VRM Add-on.
   Select its armature for bone and material tools, or select meshes for mesh tools.
2. In the 3D View, press `N` and open the **VRoid** sidebar tab.
3. Choose **Bones**, **Mesh**, **Convert**, or **Rename** in the **Malloc's Vroid Blender Tools** panel.
4. Review the preview and any skipped items.
   The bone preview starts collapsed; click its header to expand it.
5. Click the action button for that tab.

The tools use Blender's Undo system (`Ctrl+Z`).
Bone renaming leaves the hierarchy, rest pose, and transforms unchanged.
Unknown or conflicting bone names stay unchanged.
Material names keep their semantic casing; duplicates receive suffixes such as `.001`.

### Selected mesh tools

In Object Mode, select one or more mesh objects.

- **Mesh → Separate by Material:** split each selected mesh with Blender's native separation tool.
  It processes the whole mesh and leaves the resulting parts selected.
  It does not rename objects or materials.
- **Rename → Rename Object and Mesh:** name each selected object and its mesh data
  after its first non-empty material slot.
  Confirm the warning if a mesh has multiple materials.
  Meshes without materials stay unchanged.

Separate first, then rename the selected parts in one click.
Blender adds numeric suffixes when names conflict.
Shared mesh data becomes single-user when needed to protect other objects.

### Basic material conversion

Conversion creates Principled BSDF, Material Output, Image Texture nodes,
and a standard Normal Map node when a normal texture exists.

| MToon input | Principled result |
| --- | --- |
| Main texture | Base Color |
| Texture alpha | Alpha for transparent materials; opaque materials stay opaque |
| Normal texture | Normal Map node, with the source strength |
| Emission texture | Emission Color, with strength in the Principled socket |
| Double-sided setting | Backface culling setting |

Without a texture, the source color and alpha values become socket defaults.
Connected textures do not use the source color tint or alpha multiplier.
This is a basic transfer, not an exact reproduction of MToon shading.
Alpha cutoff, toon shading, rim lighting, matcap, outlines, and UV animation are not transferred.

Material tools affect only materials used exclusively by meshes bound to the selected armature.
Materials shared with unrelated objects are skipped.
Conversion also skips non-default UV transforms, filtering, and wrapping.
The preview shows the reason for each skip.
Conversion skips already-converted materials.

## Build from source

Clone this repository, or download it with **Code → Download ZIP** and extract it.
From the repository folder, run this in PowerShell:

```powershell
.\build.ps1
```

The script defaults to the Steam Blender installation.
For another installation, specify the executable:

```powershell
.\build.ps1 -BlenderPath 'C:\path\to\blender.exe'
```

On any platform with Blender on `PATH`, use:

```sh
blender --command extension build --source-dir vroid_blender_tools --output-dir .
```

This creates `vroid_blender_tools-0.3.0.zip` in the repository folder.
Install it with the [installation steps](#install) above.

## Source development

For live source development, close Blender and link the `vroid_blender_tools` package folder
into your local Blender extension repository.
On Windows, run this from the source repository:

```powershell
$source = (Resolve-Path .\vroid_blender_tools).Path
$repository = Join-Path $env:APPDATA 'Blender Foundation\Blender\5.0\extensions\user_default'
New-Item -ItemType Directory -Path $repository -Force | Out-Null
New-Item -ItemType Junction -Path (Join-Path $repository 'vroid_blender_tools') -Target $source
```

Use your Blender version's folder and uninstall any existing copy before creating the junction.
Refresh local extensions in Preferences, enable the extension, and restart Blender after source changes.

Run the pure Python tests from the repository folder:

```sh
python -m unittest discover -s tests
```

## License and dependencies

[MIT](LICENSE), copyright 2026 malloc.
The extension ZIP includes a copy of the license.

This project uses Blender's Python API and the separately installed
[VRM Add-on for Blender](https://github.com/saturday06/VRM-Addon-for-Blender),
originally by iCyP and maintained by saturday06.
Neither dependency is bundled or relicensed by this project.
Tests use synthetic data; no avatars or textures are included.
