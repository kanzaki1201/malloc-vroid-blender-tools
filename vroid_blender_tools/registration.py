"""Blender registration boundary."""

import bpy

from .operators import (
    VROIDBLENDERTOOLS_OT_apply_bone_names,
    VROIDBLENDERTOOLS_OT_apply_material_names,
    VROIDBLENDERTOOLS_OT_convert_mtoon_materials,
    VROIDBLENDERTOOLS_OT_rename_object_and_mesh_from_material,
    VROIDBLENDERTOOLS_OT_separate_by_material,
)
from .panel import (
    VROIDBLENDERTOOLS_PT_tools,
    register_ui_properties,
    unregister_ui_properties,
)

_CLASSES = (
    VROIDBLENDERTOOLS_OT_apply_bone_names,
    VROIDBLENDERTOOLS_OT_convert_mtoon_materials,
    VROIDBLENDERTOOLS_OT_apply_material_names,
    VROIDBLENDERTOOLS_OT_separate_by_material,
    VROIDBLENDERTOOLS_OT_rename_object_and_mesh_from_material,
    VROIDBLENDERTOOLS_PT_tools,
)


def register() -> None:
    """Register extension classes."""
    register_ui_properties()
    for cls in _CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    """Unregister extension classes."""
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
    unregister_ui_properties()
