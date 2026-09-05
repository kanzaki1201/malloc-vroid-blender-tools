"""Blender-hosted smoke test for applying and undoing bone-name changes."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import addon_utils
import bpy

import vroid_blender_tools
from vroid_blender_tools.adapters import is_vrm_armature
from vroid_blender_tools.operators import VROIDBLENDERTOOLS_OT_apply_bone_names


def enable_official_vrm_addon() -> None:
    if hasattr(bpy.types.Armature, "vrm_addon_extension"):
        return

    addon_utils.enable("bl_ext.blender_org.vrm", default_set=False, persistent=False)
    assert hasattr(bpy.types.Armature, "vrm_addon_extension")


def create_vrm_armature() -> bpy.types.Object:
    armature_data = bpy.data.armatures.new("VRoidSmokeArmature")
    armature_object = bpy.data.objects.new("VRoidSmokeAvatar", armature_data)
    bpy.context.collection.objects.link(armature_object)
    bpy.context.view_layer.objects.active = armature_object
    armature_object.select_set(True)

    bpy.ops.object.mode_set(mode="EDIT")
    armature_data.edit_bones.new("J_Bip_C_Hips")
    armature_data.edit_bones.new("J_Bip_L_UpperArm")
    bpy.ops.object.mode_set(mode="OBJECT")

    assert not is_vrm_armature(armature_object)
    extension = armature_data.vrm_addon_extension
    extension.addon_version = (999, 0, 0)
    extension.spec_version = "1.0"
    extension.vrm1.humanoid.human_bones.hips.node.bone_name = "J_Bip_C_Hips"
    return armature_object


def main() -> None:
    enable_official_vrm_addon()
    armature_object = create_vrm_armature()
    hips_node = (
        armature_object.data.vrm_addon_extension.vrm1.humanoid.human_bones.hips.node
    )

    vroid_blender_tools.register()
    try:
        assert "UNDO" in VROIDBLENDERTOOLS_OT_apply_bone_names.bl_options
        assert bpy.ops.vroid_blender_tools.apply_bone_names.poll()
        assert bpy.ops.vroid_blender_tools.apply_bone_names() == {"FINISHED"}
        assert set(armature_object.data.bones.keys()) == {"Hips", "UpperArm.L"}
        assert hips_node.bone_name == "Hips"
    finally:
        vroid_blender_tools.unregister()

    print("VRoid Blender Tools apply smoke test passed")


if __name__ == "__main__":
    main()
