"""Blender data adapters for VRoid bone and material tools."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass

import bpy
from bpy.types import Armature, Context, Image, Material, Object

from .material_naming import plan_vroid_material_renames, propose_vroid_material_name
from .rename_planning import PlannedRename, RenamePlan
from .vroid_naming import plan_vroid_bone_renames


class RenameApplicationError(RuntimeError):
    """The Blender data no longer matches a rename plan."""


@dataclass(frozen=True, slots=True)
class MaterialSkip:
    """One scoped material withheld from an operation."""

    material_name: str
    reason: str


@dataclass(frozen=True, slots=True)
class ArmatureMaterialPlan:
    """Independent conversion and rename plans for one VRM armature."""

    mtoon_materials: tuple[Material, ...]
    conversion_skips: tuple[MaterialSkip, ...]
    rename_plan: RenamePlan
    rename_skips: tuple[MaterialSkip, ...]


@dataclass(frozen=True, slots=True)
class _MtoonTransfer:
    """MToon inputs that have direct Principled BSDF equivalents."""

    base_color: tuple[float, float, float, float]
    base_image: Image | None
    normal_image: Image | None
    normal_strength: float
    emission_color: tuple[float, float, float]
    emission_image: Image | None
    emission_strength: float
    alpha_mode: str
    double_sided: bool


def official_vrm_addon_available() -> bool:
    """Return whether the official VRM add-on registered its armature data."""
    return hasattr(bpy.types.Armature, "vrm_addon_extension")


def is_vrm_armature(obj: Object | None) -> bool:
    """Return whether an object contains official VRM model metadata."""
    if obj is None or obj.type != "ARMATURE":
        return False

    armature = obj.data
    if not isinstance(armature, Armature):
        return False

    extension = getattr(armature, "vrm_addon_extension", None)
    if extension is None or str(getattr(extension, "spec_version", "")) not in {
        "0.0",
        "1.0",
    }:
        return False

    detector = getattr(type(extension), "has_vrm_model_metadata", None)
    if callable(detector):
        typed_detector: Callable[[Object], bool] = detector
        return bool(typed_detector(obj))

    addon_version = tuple(int(part) for part in getattr(extension, "addon_version", ()))
    if addon_version > (2, 0, 1):
        return True

    return isinstance(obj.get("humanoid_params"), str) and "hips" in armature.bones


def active_vrm_armature(context: Context) -> Object | None:
    """Return the active official VRM armature, if any."""
    obj = context.active_object
    return obj if is_vrm_armature(obj) else None


def _bound_meshes(context: Context, armature_object: Object) -> tuple[Object, ...]:
    return tuple(
        obj
        for obj in context.scene.objects
        if obj.type == "MESH"
        and any(
            modifier.type == "ARMATURE" and modifier.object is armature_object
            for modifier in obj.modifiers
        )
    )


def _material_is_mtoon(material: Material) -> bool:
    extension = getattr(material, "vrm_addon_extension", None)
    mtoon = getattr(extension, "mtoon1", None)
    return bool(mtoon and mtoon.enabled)


def _unsupported_texture_reason(material: Material) -> str | None:
    mtoon = material.vrm_addon_extension.mtoon1
    textures = (
        mtoon.pbr_metallic_roughness.base_color_texture,
        mtoon.normal_texture,
        mtoon.emissive_texture,
    )
    for texture in textures:
        if texture.index.source is None:
            continue
        transform = texture.extensions.khr_texture_transform
        if tuple(transform.offset) != (0.0, 0.0):
            return "Uses a non-default UV transform"
        if tuple(transform.scale) != (1.0, 1.0):
            return "Uses a non-default UV transform"
        sampler = texture.index.sampler
        if sampler.mag_filter != "LINEAR" or sampler.min_filter != "LINEAR":
            return "Uses non-default texture filtering"
        if sampler.wrap_s != "REPEAT" or sampler.wrap_t != "REPEAT":
            return "Uses non-default texture wrapping"
    return None


def _collect_scoped_materials(
    context: Context,
    armature_object: Object,
) -> tuple[tuple[Material, ...], set[int]]:
    bound_meshes = _bound_meshes(context, armature_object)
    bound_mesh_pointers = {obj.as_pointer() for obj in bound_meshes}
    materials: dict[int, Material] = {}
    for obj in bound_meshes:
        for slot in obj.material_slots:
            material = slot.material
            if material is not None:
                materials[material.as_pointer()] = material

    shared_materials: set[int] = set()
    for obj in context.blend_data.objects:
        if obj.as_pointer() in bound_mesh_pointers:
            continue
        for slot in obj.material_slots:
            material = slot.material
            if material is not None and material.as_pointer() in materials:
                shared_materials.add(material.as_pointer())

    return (
        tuple(sorted(materials.values(), key=lambda material: material.name)),
        shared_materials,
    )


def _plan_mtoon_conversion(
    materials: Sequence[Material],
    shared_materials: set[int],
) -> tuple[tuple[Material, ...], tuple[MaterialSkip, ...]]:
    mtoon_materials: list[Material] = []
    skips: list[MaterialSkip] = []
    for material in materials:
        if not _material_is_mtoon(material):
            continue
        if material.as_pointer() in shared_materials:
            skips.append(
                MaterialSkip(material.name, "Also used by an unrelated object")
            )
            continue
        unsupported_reason = _unsupported_texture_reason(material)
        if unsupported_reason is None:
            mtoon_materials.append(material)
        else:
            skips.append(MaterialSkip(material.name, unsupported_reason))
    return tuple(mtoon_materials), tuple(skips)


def _plan_material_names(
    context: Context,
    materials: Sequence[Material],
    shared_materials: set[int],
) -> tuple[RenamePlan, tuple[MaterialSkip, ...]]:
    all_names = tuple(context.blend_data.materials.keys())
    exclusive_materials = tuple(
        material
        for material in materials
        if material.as_pointer() not in shared_materials
    )
    rename_plan = plan_vroid_material_renames(
        all_names,
        tuple(material.name for material in exclusive_materials),
    )
    rename_skips = tuple(
        MaterialSkip(material.name, "Also used by an unrelated object")
        for material in materials
        if material.as_pointer() in shared_materials
        and propose_vroid_material_name(material.name) is not None
    )
    return rename_plan, rename_skips


def plan_active_armature_materials(
    context: Context,
) -> tuple[Object, ArmatureMaterialPlan]:
    """Plan independent material operations for the active VRM armature."""
    armature_object = active_vrm_armature(context)
    if armature_object is None:
        raise RenameApplicationError(
            "Select an armature imported by the official VRM add-on"
        )

    materials, shared_materials = _collect_scoped_materials(context, armature_object)
    mtoon_materials, conversion_skips = _plan_mtoon_conversion(
        materials,
        shared_materials,
    )
    rename_plan, rename_skips = _plan_material_names(
        context,
        materials,
        shared_materials,
    )

    return armature_object, ArmatureMaterialPlan(
        mtoon_materials=mtoon_materials,
        conversion_skips=conversion_skips,
        rename_plan=rename_plan,
        rename_skips=rename_skips,
    )


def plan_armature_bone_names(armature_object: Object) -> RenamePlan:
    """Build a safe name plan from a Blender armature's current bones."""
    if not is_vrm_armature(armature_object):
        raise RenameApplicationError("The active object is not an official VRM armature")

    armature = armature_object.data
    if not isinstance(armature, Armature):
        raise RenameApplicationError("The active object has no armature data")

    return plan_vroid_bone_renames(tuple(armature.bones.keys()))


def plan_active_armature_bone_names(context: Context) -> tuple[Object, RenamePlan]:
    """Return the active official VRM armature and its current name plan."""
    armature_object = active_vrm_armature(context)
    if armature_object is None:
        raise RenameApplicationError(
            "Select an armature imported by the official VRM add-on"
        )
    return armature_object, plan_armature_bone_names(armature_object)


def _validate_renames(
    existing_names: set[str],
    renames: Sequence[PlannedRename],
) -> None:
    sources = tuple(rename.source for rename in renames)
    targets = tuple(rename.target for rename in renames)

    if len(set(sources)) != len(sources):
        raise RenameApplicationError("The rename plan contains a source more than once")
    if len(set(targets)) != len(targets):
        raise RenameApplicationError("The rename plan contains a target more than once")
    if not set(sources).issubset(existing_names):
        raise RenameApplicationError("The armature changed after the preview was built")
    if set(targets) & existing_names:
        raise RenameApplicationError("A previewed target name is no longer available")


def apply_armature_bone_names(
    armature_object: Object,
    plan: RenamePlan,
) -> int:
    """Apply a prevalidated plan through Blender's bone rename API."""
    if not is_vrm_armature(armature_object):
        raise RenameApplicationError("The active object is not an official VRM armature")

    armature = armature_object.data
    if not isinstance(armature, Armature):
        raise RenameApplicationError("The active object has no armature data")

    _validate_renames(set(armature.bones.keys()), plan.renames)
    for rename in plan.renames:
        bone = armature.bones.get(rename.source)
        if bone is None:
            raise RenameApplicationError("The armature changed while names were applied")
        bone.name = rename.target

    return len(plan.renames)


def _snapshot_mtoon(material: Material) -> _MtoonTransfer:
    mtoon = material.vrm_addon_extension.mtoon1
    return _MtoonTransfer(
        base_color=tuple(mtoon.pbr_metallic_roughness.base_color_factor),
        base_image=mtoon.pbr_metallic_roughness.base_color_texture.index.source,
        normal_image=mtoon.normal_texture.index.source,
        normal_strength=mtoon.normal_texture.scale,
        emission_color=tuple(mtoon.emissive_factor),
        emission_image=mtoon.emissive_texture.index.source,
        emission_strength=(
            mtoon.extensions.khr_materials_emissive_strength.emissive_strength
        ),
        alpha_mode=mtoon.alpha_mode,
        double_sided=mtoon.double_sided,
    )


def _restore_principled(material: Material, transfer: _MtoonTransfer) -> None:
    node_tree = material.node_tree
    if node_tree is None:
        raise RenameApplicationError(
            f"Could not create a Principled BSDF for {material.name}"
        )

    nodes = node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (300.0, 0.0)
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.location = (0.0, 0.0)
    node_tree.links.new(principled.outputs["BSDF"], output.inputs["Surface"])

    principled.inputs["Base Color"].default_value = transfer.base_color
    principled.inputs["Alpha"].default_value = (
        1.0 if transfer.alpha_mode == "OPAQUE" else transfer.base_color[3]
    )
    principled.inputs["Emission Color"].default_value = (
        *transfer.emission_color,
        1.0,
    )
    principled.inputs["Emission Strength"].default_value = transfer.emission_strength

    if transfer.base_image is not None:
        base_image = nodes.new("ShaderNodeTexImage")
        base_image.image = transfer.base_image
        base_image.location = (-300.0, 100.0)
        node_tree.links.new(
            base_image.outputs["Color"],
            principled.inputs["Base Color"],
        )
        if transfer.alpha_mode != "OPAQUE":
            node_tree.links.new(
                base_image.outputs["Alpha"],
                principled.inputs["Alpha"],
            )

    if transfer.normal_image is not None:
        normal_image = nodes.new("ShaderNodeTexImage")
        normal_image.image = transfer.normal_image
        normal_image.location = (-600.0, -200.0)
        normal_map = nodes.new("ShaderNodeNormalMap")
        normal_map.location = (-300.0, -200.0)
        normal_map.space = "TANGENT"
        normal_map.inputs["Strength"].default_value = transfer.normal_strength
        node_tree.links.new(
            normal_image.outputs["Color"],
            normal_map.inputs["Color"],
        )
        node_tree.links.new(
            normal_map.outputs["Normal"],
            principled.inputs["Normal"],
        )

    if transfer.emission_image is not None:
        emission_image = nodes.new("ShaderNodeTexImage")
        emission_image.image = transfer.emission_image
        emission_image.location = (-300.0, -500.0)
        node_tree.links.new(
            emission_image.outputs["Color"],
            principled.inputs["Emission Color"],
        )

    material.use_backface_culling = not transfer.double_sided
    material.surface_render_method = (
        "BLENDED" if transfer.alpha_mode == "BLEND" else "DITHERED"
    )


def convert_mtoon_materials(materials: Sequence[Material]) -> int:
    """Convert prevalidated MToon materials through the official VRM operator."""
    transfers: list[tuple[Material, _MtoonTransfer]] = []
    for material in materials:
        if bpy.data.materials.get(material.name) is not material:
            raise RenameApplicationError("A material changed after the preview was built")
        if not _material_is_mtoon(material):
            raise RenameApplicationError(f"{material.name} is no longer an MToon material")
        transfers.append((material, _snapshot_mtoon(material)))

    for material, transfer in transfers:
        result = bpy.ops.vrm.convert_mtoon1_to_bsdf_principled(
            "EXEC_DEFAULT",
            False,
            material_name=material.name,
        )
        if result != {"FINISHED"}:
            raise RenameApplicationError(f"Could not convert {material.name}")
        _restore_principled(material, transfer)

    return len(transfers)


def apply_material_names(plan: RenamePlan) -> int:
    """Apply a prevalidated material-name plan."""
    _validate_renames(set(bpy.data.materials.keys()), plan.renames)
    for rename in plan.renames:
        material = bpy.data.materials.get(rename.source)
        if material is None:
            raise RenameApplicationError("A material changed while names were applied")
        material.name = rename.target

    return len(plan.renames)
