"""Blender-hosted smoke test for extension registration."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bpy

import vroid_blender_tools
from vroid_blender_tools.operators import (
    VROIDBLENDERTOOLS_OT_apply_bone_names,
    VROIDBLENDERTOOLS_OT_apply_material_names,
    VROIDBLENDERTOOLS_OT_convert_mtoon_materials,
)
from vroid_blender_tools.panel import VROIDBLENDERTOOLS_PT_tools

CLASSES = (
    VROIDBLENDERTOOLS_OT_apply_bone_names,
    VROIDBLENDERTOOLS_OT_convert_mtoon_materials,
    VROIDBLENDERTOOLS_OT_apply_material_names,
    VROIDBLENDERTOOLS_PT_tools,
)


def main() -> None:
    vroid_blender_tools.register()
    try:
        assert all(cls.is_registered for cls in CLASSES)
        assert VROIDBLENDERTOOLS_PT_tools.bl_label == "Malloc's Vroid Blender Tools"
        assert bpy.context.window_manager.vroid_blender_tools_tab == "BONES"
        bpy.context.window_manager.vroid_blender_tools_tab = "RENAME"
        assert bpy.context.window_manager.vroid_blender_tools_tab == "RENAME"
    finally:
        vroid_blender_tools.unregister()

    assert all(not cls.is_registered for cls in CLASSES)
    assert not hasattr(bpy.types.WindowManager, "vroid_blender_tools_tab")
    print("VRoid Blender Tools registration smoke test passed")


if __name__ == "__main__":
    main()
