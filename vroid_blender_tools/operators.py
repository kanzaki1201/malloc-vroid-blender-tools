"""Blender operators for VRoid Blender Tools."""

from typing import ClassVar

from bpy.types import Context, Operator

from .adapters import (
    RenameApplicationError,
    apply_armature_bone_names,
    apply_material_names,
    convert_mtoon_materials,
    plan_active_armature_bone_names,
    plan_active_armature_materials,
)


class VROIDBLENDERTOOLS_OT_apply_bone_names(Operator):
    """Apply the safe VRoid bone-name plan."""

    bl_idname = "vroid_blender_tools.apply_bone_names"
    bl_label = "Apply Bone Names"
    bl_description = "Apply the previewed safe VRoid bone-name changes"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        try:
            _, plan = plan_active_armature_bone_names(context)
        except RenameApplicationError as error:
            cls.poll_message_set(str(error))
            return False

        if not plan.renames:
            cls.poll_message_set("No safe VRoid bone-name changes are available")
            return False
        return True

    def execute(self, context: Context) -> set[str]:
        try:
            armature_object, plan = plan_active_armature_bone_names(context)
            rename_count = apply_armature_bone_names(armature_object, plan)
        except RenameApplicationError as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}

        if not rename_count:
            self.report({"INFO"}, "No safe VRoid bone-name changes were available")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Renamed {rename_count} bones")
        return {"FINISHED"}


class VROIDBLENDERTOOLS_OT_convert_mtoon_materials(Operator):
    """Convert scoped MToon materials to Principled BSDF."""

    bl_idname = "vroid_blender_tools.convert_mtoon_materials"
    bl_label = "Convert MToon Materials"
    bl_description = "Convert the previewed MToon materials to Principled BSDF"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        try:
            _, plan = plan_active_armature_materials(context)
        except RenameApplicationError as error:
            cls.poll_message_set(str(error))
            return False

        if not plan.mtoon_materials:
            cls.poll_message_set("No safe MToon materials are available")
            return False
        return True

    def execute(self, context: Context) -> set[str]:
        try:
            _, plan = plan_active_armature_materials(context)
            conversion_count = convert_mtoon_materials(plan.mtoon_materials)
        except RenameApplicationError as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}

        self.report({"INFO"}, f"Converted {conversion_count} MToon materials")
        return {"FINISHED"}


class VROIDBLENDERTOOLS_OT_apply_material_names(Operator):
    """Apply the safe VRoid material-name plan."""

    bl_idname = "vroid_blender_tools.apply_material_names"
    bl_label = "Apply Material Names"
    bl_description = "Apply the previewed safe VRoid material-name changes"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        try:
            _, plan = plan_active_armature_materials(context)
        except RenameApplicationError as error:
            cls.poll_message_set(str(error))
            return False

        if not plan.rename_plan.renames:
            cls.poll_message_set("No safe VRoid material-name changes are available")
            return False
        return True

    def execute(self, context: Context) -> set[str]:
        try:
            _, plan = plan_active_armature_materials(context)
            rename_count = apply_material_names(plan.rename_plan)
        except RenameApplicationError as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}

        self.report({"INFO"}, f"Renamed {rename_count} materials")
        return {"FINISHED"}
