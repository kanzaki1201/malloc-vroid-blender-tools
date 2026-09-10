"""3D View sidebar UI for VRoid Blender Tools."""

from bpy.props import EnumProperty
from bpy.types import Context, Panel, UILayout, WindowManager

from .adapters import (
    ArmatureMaterialPlan,
    RenameApplicationError,
    official_vrm_addon_available,
    plan_active_armature_bone_names,
    plan_active_armature_materials,
    plan_selected_mesh_names,
    selected_editable_meshes,
)
from .operators import (
    VROIDBLENDERTOOLS_OT_apply_bone_names,
    VROIDBLENDERTOOLS_OT_apply_material_names,
    VROIDBLENDERTOOLS_OT_convert_mtoon_materials,
    VROIDBLENDERTOOLS_OT_rename_object_and_mesh_from_material,
    VROIDBLENDERTOOLS_OT_separate_by_material,
)
from .rename_planning import ConflictReason

_TAB_PROPERTY = "vroid_blender_tools_tab"


def register_ui_properties() -> None:
    """Register transient UI state."""
    setattr(
        WindowManager,
        _TAB_PROPERTY,
        EnumProperty(
            name="Tool",
            items=(
                ("BONES", "Bones", "Rename VRoid bones"),
                ("MESH", "Mesh", "Edit selected meshes"),
                ("CONVERT", "Convert", "Convert MToon materials"),
                ("RENAME", "Rename", "Rename materials, objects, and mesh data"),
            ),
            default="BONES",
        ),
    )


def unregister_ui_properties() -> None:
    """Unregister transient UI state."""
    delattr(WindowManager, _TAB_PROPERTY)


def _conflict_message(reason: ConflictReason) -> str:
    if reason == ConflictReason.TARGET_EXISTS:
        return "Target already exists"
    if reason == ConflictReason.TARGET_DUPLICATED:
        return "Multiple bones want this target"
    return "Rename is not safe"


def _draw_bone_names(layout: UILayout, context: Context) -> None:
    try:
        _, plan = plan_active_armature_bone_names(context)
    except RenameApplicationError as error:
        layout.label(text=str(error), icon="INFO")
        return

    if plan.renames:
        header, preview = layout.panel("vroid_bone_names_preview", default_closed=True)
        header.label(text=f"Preview: {len(plan.renames)} safe changes")
        if preview is not None:
            for rename in plan.renames:
                preview.label(text=f"{rename.source} → {rename.target}", icon="BONE_DATA")
    else:
        layout.label(text="No VRoid-prefixed bone names need changes", icon="CHECKMARK")

    if plan.conflicts:
        conflicts = layout.box()
        conflicts.alert = True
        conflicts.label(text=f"Skipped: {len(plan.conflicts)} conflicts", icon="ERROR")
        for conflict in plan.conflicts:
            conflicts.label(text=f"{conflict.source} → {conflict.target}")
            conflicts.label(text=_conflict_message(conflict.reason), icon="INFO")

    apply_row = layout.row()
    apply_row.enabled = bool(plan.renames)
    apply_row.operator(
        VROIDBLENDERTOOLS_OT_apply_bone_names.bl_idname,
        text=f"Apply {len(plan.renames)} Bone Name Changes",
        icon="CHECKMARK",
    )


def _draw_conversion(layout: UILayout, plan: ArmatureMaterialPlan) -> None:
    preview = layout.box()
    preview.label(
        text=f"MToon → Principled: {len(plan.mtoon_materials)}",
        icon="MATERIAL",
    )
    for material in plan.mtoon_materials:
        preview.label(text=material.name)
    for skip in plan.conversion_skips:
        preview.label(
            text=f"Skipped {skip.material_name}: {skip.reason}",
            icon="ERROR",
        )

    apply_row = layout.row()
    apply_row.enabled = bool(plan.mtoon_materials)
    apply_row.operator(
        VROIDBLENDERTOOLS_OT_convert_mtoon_materials.bl_idname,
        text=f"Convert {len(plan.mtoon_materials)} MToon Materials",
        icon="NODE_MATERIAL",
    )


def _draw_material_names(layout: UILayout, plan: ArmatureMaterialPlan) -> None:
    preview = layout.box()
    preview.label(
        text=f"Material names: {len(plan.rename_plan.renames)}",
        icon="SORTALPHA",
    )
    for item in plan.rename_plan.renames:
        preview.label(text=f"{item.source} → {item.target}")
    for skip in plan.rename_skips:
        preview.label(
            text=f"Skipped {skip.material_name}: {skip.reason}",
            icon="ERROR",
        )

    apply_row = layout.row()
    apply_row.enabled = bool(plan.rename_plan.renames)
    apply_row.operator(
        VROIDBLENDERTOOLS_OT_apply_material_names.bl_idname,
        text=f"Apply {len(plan.rename_plan.renames)} Material Name Changes",
        icon="CHECKMARK",
    )


def _draw_mesh_tools(layout: UILayout, context: Context) -> None:
    try:
        mesh_count = len(selected_editable_meshes(context))
    except RenameApplicationError as error:
        layout.label(text=str(error), icon="INFO")
        mesh_count = 0
    layout.label(text=f"Selected editable meshes: {mesh_count}", icon="MESH_DATA")
    row = layout.row()
    row.enabled = bool(mesh_count)
    row.operator(
        VROIDBLENDERTOOLS_OT_separate_by_material.bl_idname,
        text="Separate by Material",
        icon="MESH_DATA",
    )


def _draw_object_and_mesh_names(layout: UILayout, context: Context) -> None:
    try:
        renames, materialless_objects = plan_selected_mesh_names(context)
    except RenameApplicationError as error:
        layout.label(text=str(error), icon="INFO")
        return

    preview = layout.box()
    preview.label(text=f"Object and mesh names: {len(renames)}", icon="OBJECT_DATA")
    for obj, target_name, material_count in renames:
        preview.label(text=f"{obj.name} / {obj.data.name} → {target_name}")
        if material_count > 1:
            preview.label(text="Uses first of multiple materials", icon="ERROR")
    for object_name in materialless_objects:
        preview.label(text=f"Skipped {object_name}: No assigned material", icon="ERROR")

    row = layout.row()
    row.enabled = bool(renames)
    row.operator(
        VROIDBLENDERTOOLS_OT_rename_object_and_mesh_from_material.bl_idname,
        text="Rename Object and Mesh",
        icon="CHECKMARK",
    )


class VROIDBLENDERTOOLS_PT_tools(Panel):
    """Show the independent VRoid tools in one tabbed panel."""

    bl_idname = "VROIDBLENDERTOOLS_PT_tools"
    bl_label = "Malloc's Vroid Blender Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRoid"

    def draw(self, context: Context) -> None:
        layout = self.layout
        tabs = layout.row(align=True)
        tabs.prop(context.window_manager, _TAB_PROPERTY, expand=True)

        tab = getattr(context.window_manager, _TAB_PROPERTY)
        if tab == "MESH":
            _draw_mesh_tools(layout, context)
            return

        if tab == "RENAME":
            if official_vrm_addon_available():
                try:
                    _, plan = plan_active_armature_materials(context)
                except RenameApplicationError as error:
                    layout.label(text=str(error), icon="INFO")
                else:
                    _draw_material_names(layout, plan)
            else:
                layout.label(text="Material names require the official VRM Add-on")
            _draw_object_and_mesh_names(layout, context)
            return

        if not official_vrm_addon_available():
            layout.label(text="Official VRM Add-on is not enabled", icon="ERROR")
            layout.label(text="Enable it in Preferences → Add-ons")
            return

        if tab == "BONES":
            _draw_bone_names(layout, context)
            return

        try:
            _, plan = plan_active_armature_materials(context)
        except RenameApplicationError as error:
            layout.label(text=str(error), icon="INFO")
            return

        _draw_conversion(layout, plan)
