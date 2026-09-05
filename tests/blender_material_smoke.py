"""Blender-hosted smoke test for independent VRoid material tools."""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bpy

import vroid_blender_tools
from tests.blender_apply_smoke import create_vrm_armature, enable_official_vrm_addon
from vroid_blender_tools.adapters import plan_active_armature_materials
from vroid_blender_tools.operators import (
    VROIDBLENDERTOOLS_OT_apply_material_names,
    VROIDBLENDERTOOLS_OT_convert_mtoon_materials,
)


def create_mesh(
    name: str,
    materials: tuple[bpy.types.Material, ...],
    armature: bpy.types.Object | None = None,
) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(((0, 0, 0), (1, 0, 0), (0, 1, 0)), (), ((0, 1, 2),))
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for material in materials:
        mesh.materials.append(material)
    if armature is not None:
        modifier = obj.modifiers.new("Armature", "ARMATURE")
        modifier.object = armature
    return obj


def create_mtoon_material(
    name: str,
    alpha_mode: str,
    base_image: bpy.types.Image | None = None,
    normal_image: bpy.types.Image | None = None,
    emission_image: bpy.types.Image | None = None,
) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    mtoon = material.vrm_addon_extension.mtoon1
    mtoon.enabled = True
    mtoon.pbr_metallic_roughness.base_color_factor = (0.2, 0.3, 0.4, 0.5)
    mtoon.alpha_mode = alpha_mode
    mtoon.alpha_cutoff = 0.4
    mtoon.double_sided = True
    mtoon.normal_texture.scale = 0.35
    mtoon.emissive_factor = (0.6, 0.7, 0.8)
    mtoon.extensions.khr_materials_emissive_strength.emissive_strength = 2.5
    if base_image is not None:
        mtoon.pbr_metallic_roughness.base_color_texture.index.source = base_image
    if normal_image is not None:
        mtoon.normal_texture.index.source = normal_image
    if emission_image is not None:
        mtoon.emissive_texture.index.source = emission_image
    return material


def find_principled(material: bpy.types.Material):
    assert material.node_tree
    return next(
        node
        for node in material.node_tree.nodes
        if node.bl_idname == "ShaderNodeBsdfPrincipled"
    )


def node_signature(material: bpy.types.Material) -> tuple[tuple[str, str], ...]:
    assert material.node_tree
    return tuple(sorted((node.bl_idname, node.label) for node in material.node_tree.nodes))


def assert_close(actual: float, expected: float) -> None:
    assert math.isclose(actual, expected, rel_tol=1e-6, abs_tol=1e-6)


def assert_direct_image(socket, image: bpy.types.Image) -> None:
    assert len(socket.links) == 1
    node = socket.links[0].from_node
    assert node.bl_idname == "ShaderNodeTexImage"
    assert node.image is image


def main() -> None:
    enable_official_vrm_addon()
    armature = create_vrm_armature()

    base_image = bpy.data.images.new("MaterialSmokeBase", 1, 1, alpha=True)
    normal_image = bpy.data.images.new("MaterialSmokeNormal", 1, 1)
    normal_image.colorspace_settings.is_data = True
    emission_image = bpy.data.images.new("MaterialSmokeEmission", 1, 1)

    face_source = "N00_000_00_FaceMouth_00_FACE (Instance)"
    mask_source = "N00_001_00_EyeWhite_00_FACE (Instance)"
    opaque_source = "N00_002_00_Body_00_SKIN (Instance)"
    hair_one_source = "N00_000_Hair_00_HAIR_01 (Instance)"
    hair_two_source = "N00_001_Hair_00_HAIR_02 (Instance)"
    transformed_source = "N00_777_00_Transformed_00_FACE (Instance)"
    shared_source = "N00_888_00_Shared_00_FACE (Instance)"
    unrelated_source = "N00_999_00_Unrelated_00_FACE (Instance)"

    face = create_mtoon_material(
        face_source,
        "BLEND",
        base_image,
        normal_image,
        emission_image,
    )
    mask = create_mtoon_material(mask_source, "MASK", base_image)
    opaque = create_mtoon_material(opaque_source, "OPAQUE")
    transformed = create_mtoon_material(transformed_source, "BLEND", base_image)
    transformed_texture = (
        transformed.vrm_addon_extension.mtoon1.pbr_metallic_roughness.base_color_texture
    )
    transformed_texture.extensions.khr_texture_transform.offset = (0.25, 0.0)
    shared = create_mtoon_material(shared_source, "BLEND", base_image)
    unrelated = create_mtoon_material(unrelated_source, "BLEND", base_image)
    hair_one = bpy.data.materials.new(hair_one_source)
    hair_two = bpy.data.materials.new(hair_two_source)
    bpy.data.materials.new("Hair")

    create_mesh(
        "BoundMaterialMesh",
        (face, mask, opaque, hair_one, hair_two, transformed, shared),
        armature,
    )
    create_mesh("UnrelatedMaterialMesh", (unrelated,))
    curve = bpy.data.curves.new("UnrelatedMaterialCurve", "CURVE")
    curve.materials.append(shared)
    curve_object = bpy.data.objects.new("UnrelatedMaterialCurve", curve)
    bpy.context.collection.objects.link(curve_object)

    vroid_blender_tools.register()
    try:
        assert "UNDO" in VROIDBLENDERTOOLS_OT_convert_mtoon_materials.bl_options
        assert "UNDO" in VROIDBLENDERTOOLS_OT_apply_material_names.bl_options

        _, plan = plan_active_armature_materials(bpy.context)
        assert {material.name for material in plan.mtoon_materials} == {
            face_source,
            mask_source,
            opaque_source,
        }
        assert {skip.material_name for skip in plan.conversion_skips} == {
            shared_source,
            transformed_source,
        }
        assert {skip.material_name for skip in plan.rename_skips} == {shared_source}
        assert bpy.ops.vroid_blender_tools.convert_mtoon_materials() == {"FINISHED"}
        assert not face.vrm_addon_extension.mtoon1.enabled
        assert not mask.vrm_addon_extension.mtoon1.enabled
        assert not opaque.vrm_addon_extension.mtoon1.enabled
        assert transformed.vrm_addon_extension.mtoon1.enabled
        assert shared.vrm_addon_extension.mtoon1.enabled
        assert unrelated.vrm_addon_extension.mtoon1.enabled
        assert not bpy.ops.vroid_blender_tools.convert_mtoon_materials.poll()

        face_principled = find_principled(face)
        assert_direct_image(face_principled.inputs["Base Color"], base_image)
        assert_direct_image(face_principled.inputs["Alpha"], base_image)
        normal_link = face_principled.inputs["Normal"].links[0]
        normal_map = normal_link.from_node
        assert normal_link.from_socket.name == "Normal"
        assert normal_map.bl_idname == "ShaderNodeNormalMap"
        assert normal_map.space == "TANGENT"
        assert_direct_image(normal_map.inputs["Color"], normal_image)
        assert_close(normal_map.inputs["Strength"].default_value, 0.35)
        assert_direct_image(face_principled.inputs["Emission Color"], emission_image)
        assert_close(face_principled.inputs["Emission Strength"].default_value, 2.5)
        assert face.surface_render_method == "BLENDED"
        assert not face.use_backface_culling

        assert face.node_tree
        assert {
            node.bl_idname for node in face.node_tree.nodes
        } <= {
            "ShaderNodeOutputMaterial",
            "ShaderNodeBsdfPrincipled",
            "ShaderNodeTexImage",
            "ShaderNodeNormalMap",
        }
        for actual, expected in zip(
            face_principled.inputs["Base Color"].default_value[:3],
            (0.2, 0.3, 0.4),
            strict=True,
        ):
            assert_close(actual, expected)
        assert_close(face_principled.inputs["Alpha"].default_value, 0.5)
        for actual, expected in zip(
            face_principled.inputs["Emission Color"].default_value[:3],
            (0.6, 0.7, 0.8),
            strict=True,
        ):
            assert_close(actual, expected)

        mask_principled = find_principled(mask)
        assert_direct_image(mask_principled.inputs["Alpha"], base_image)
        assert mask.surface_render_method == "DITHERED"

        opaque_principled = find_principled(opaque)
        assert not opaque_principled.inputs["Alpha"].is_linked
        assert_close(opaque_principled.inputs["Alpha"].default_value, 1.0)

        face_graph = node_signature(face)
        assert bpy.ops.vroid_blender_tools.apply_material_names() == {"FINISHED"}
        assert face.name == "FaceMouth"
        assert mask.name == "EyeWhite"
        assert opaque.name == "Body"
        assert hair_one.name == "Hair.001"
        assert hair_two.name == "Hair.002"
        assert transformed.name == "Transformed"
        assert shared.name == shared_source
        assert unrelated.name == unrelated_source
        assert node_signature(face) == face_graph
        assert not bpy.ops.vroid_blender_tools.apply_material_names.poll()
    finally:
        vroid_blender_tools.unregister()

    print("VRoid Blender Tools material smoke test passed")


if __name__ == "__main__":
    main()
