# Malloc's Vroid Blender Tools

Simple VRoid cleanup tools for Blender 5.0+, by malloc.

- **Bones:** clean VRoid bone names with Blender-style `.L` / `.R` suffixes.
- **Convert:** transfer basic MToon inputs to Principled BSDF.
- **Rename:** clean material names, such as
  `N00_000_00_FaceMouth_00_FACE (Instance)` → `FaceMouth`.

Each tool has its own preview and action.
Material conversion and material renaming are independent.

## Requirements

- Blender 5.0 or newer.
- The official [VRM Add-on for Blender](https://vrm-addon-for-blender.info/en-us/),
  installed and enabled in a version that supports your Blender version.
- A VRoid model imported through that add-on as VRM 0.x or VRM 1.0.

## Install

1. Download this repository with **Code → Download ZIP** and extract it, or clone it.
2. Build the extension ZIP from the repository folder.
   On Windows, run this in PowerShell:

   ```powershell
   .\build.ps1
   ```

   The script defaults to the Steam Blender installation.
   For another installation, specify the executable:

   ```powershell
   .\build.ps1 -BlenderPath 'C:\path\to\blender.exe'
   ```

   On any platform with Blender on `PATH`, you can use its build command:

   ```sh
   blender --command extension build --source-dir vroid_blender_tools --output-dir .
   ```

3. In Blender, open **Edit → Preferences → Get Extensions**.
4. Open the menu at the top right and select **Install from Disk**.
5. Select the generated `vroid_blender_tools-0.2.1.zip` and enable **Malloc's Vroid Blender Tools**.

Use the built extension ZIP, not the GitHub source ZIP or `__init__.py`.

## Quick use

Save a copy of your model before making changes.

1. Import your VRM and select its armature.
2. In the 3D View, press `N` and open the **VRoid** sidebar tab.
3. Choose **Bones**, **Convert**, or **Rename** in the **Malloc's Vroid Blender Tools** panel.
4. Review the preview and any skipped items.
   The bone preview starts collapsed; click its header to expand it.
5. Click the action button for that tab.

The tools use Blender's Undo system (`Ctrl+Z`).
Bone renaming leaves the hierarchy, rest pose, and transforms unchanged.
Unknown or conflicting bone names stay unchanged.
Material names keep their semantic casing; duplicates receive suffixes such as `.001`.

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
