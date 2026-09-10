"""Blender operators for VRoid Blender Tools."""

from typing import ClassVar

from bpy.props import BoolProperty
from bpy.types import Context, Event, Operator

from .adapters import (
    RenameApplicationError,
    apply_armature_bone_names,
    apply_material_names,
    apply_selected_mesh_names,
    convert_mtoon_materials,
    mesh_names_require_confirmation,
    plan_active_armature_bone_names,
    plan_active_armature_materials,
    plan_selected_mesh_names,
    selected_editable_meshes,
    separate_selected_meshes_by_material,
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


class VROIDBLENDERTOOLS_OT_separate_by_material(Operator):
    """Separate all selected editable meshes by material."""

    bl_idname = "vroid_blender_tools.separate_by_material"
    bl_label = "Separate by Material"
    bl_description = "Separate all selected mesh geometry by assigned material"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        try:
            meshes = selected_editable_meshes(context)
        except RenameApplicationError as error:
            cls.poll_message_set(str(error))
            return False
        if not meshes:
            cls.poll_message_set("Select at least one editable mesh")
            return False
        return True

    def execute(self, context: Context) -> set[str]:
        try:
            meshes = selected_editable_meshes(context)
            if not meshes:
                raise RenameApplicationError("Select at least one editable mesh")
        except RenameApplicationError as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}

        try:
            parts = separate_selected_meshes_by_material(context, meshes)
        except (RenameApplicationError, RuntimeError) as error:
            self.report({"ERROR"}, f"Separation stopped: {error}. Use Undo to revert")
            return {"FINISHED"}

        self.report(
            {"INFO"},
            f"Separated {len(meshes)} meshes into {len(parts)} selected parts",
        )
        return {"FINISHED"}


class VROIDBLENDERTOOLS_OT_rename_object_and_mesh_from_material(Operator):
    """Rename selected objects and mesh data from their first material."""

    bl_idname = "vroid_blender_tools.rename_object_and_mesh_from_material"
    bl_label = "Rename Object and Mesh"
    bl_description = "Use the first assigned material to name each selected object and mesh"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    confirmed_multiple_materials: BoolProperty(
        name="Confirm Multiple Materials",
        default=False,
        options={"HIDDEN", "SKIP_SAVE"},
    )

    @classmethod
    def poll(cls, context: Context) -> bool:
        try:
            renames, _ = plan_selected_mesh_names(context)
        except RenameApplicationError as error:
            cls.poll_message_set(str(error))
            return False
        if not renames:
            cls.poll_message_set("No selected object or mesh names need changes")
            return False
        return True

    def invoke(self, context: Context, event: Event) -> set[str]:
        try:
            renames, _ = plan_selected_mesh_names(context)
        except RenameApplicationError as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}
        if mesh_names_require_confirmation(renames) and not (
            self.confirmed_multiple_materials
        ):
            self.confirmed_multiple_materials = True
            return context.window_manager.invoke_confirm(
                self,
                event,
                title="Use First Material Name?",
                message="Some selected meshes have multiple assigned materials.",
                confirm_text="Rename",
                icon="QUESTION",
            )
        return self.execute(context)

    def execute(self, context: Context) -> set[str]:
        try:
            renames, materialless_objects = plan_selected_mesh_names(context)
            if mesh_names_require_confirmation(renames) and not (
                self.confirmed_multiple_materials
            ):
                self.report(
                    {"ERROR"},
                    "Multiple assigned materials require confirmation",
                )
                return {"CANCELLED"}
            rename_count = apply_selected_mesh_names(context, renames)
        except RenameApplicationError as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}

        message = f"Renamed {rename_count} objects and meshes"
        if materialless_objects:
            message += f"; skipped {len(materialless_objects)} without materials"
        self.report({"INFO"}, message)
        return {"FINISHED"}
