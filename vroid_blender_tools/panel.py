"""3D View sidebar UI for VRoid Blender Tools."""

from bpy.props import EnumProperty
from bpy.types import Context, Panel, UILayout, WindowManager

from .adapters import (
    ArmatureMaterialPlan,
    RenameApplicationError,
    official_vrm_addon_available,
    plan_active_armature_bone_names,
    plan_active_armature_materials,
)
from .operators import (
    VROIDBLENDERTOOLS_OT_apply_bone_names,
    VROIDBLENDERTOOLS_OT_apply_material_names,
    VROIDBLENDERTOOLS_OT_convert_mtoon_materials,
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
                ("CONVERT", "Convert", "Convert MToon materials"),
                ("RENAME", "Rename", "Rename VRoid materials"),
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

        if not official_vrm_addon_available():
            layout.label(text="Official VRM Add-on is not enabled", icon="ERROR")
            layout.label(text="Enable it in Preferences → Add-ons")
            return

        tab = getattr(context.window_manager, _TAB_PROPERTY)
        if tab == "BONES":
            _draw_bone_names(layout, context)
            return

        try:
            _, plan = plan_active_armature_materials(context)
        except RenameApplicationError as error:
            layout.label(text=str(error), icon="INFO")
            return

        if tab == "CONVERT":
            _draw_conversion(layout, plan)
        else:
            _draw_material_names(layout, plan)
