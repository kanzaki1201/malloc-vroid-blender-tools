"""Blender-hosted smoke test for selected mesh tools."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bpy

import vroid_blender_tools
from vroid_blender_tools.adapters import official_vrm_addon_available
from vroid_blender_tools.operators import (
    VROIDBLENDERTOOLS_OT_rename_object_and_mesh_from_material,
    VROIDBLENDERTOOLS_OT_separate_by_material,
)
from vroid_blender_tools.panel import VROIDBLENDERTOOLS_PT_tools


class LayoutRecorder:
    """Record panel operator buttons without requiring a visible viewport."""

    def __init__(self) -> None:
        self.operators: list[str] = []
        self.enabled = True
        self.alert = False

    def row(self, **_kwargs):
        return self

    def column(self, **_kwargs):
        return self

    def box(self):
        return self

    def panel(self, *_args, **_kwargs):
        return self, self

    def prop(self, *_args, **_kwargs) -> None:
        pass

    def label(self, *_args, **_kwargs) -> None:
        pass

    def separator(self, *_args, **_kwargs) -> None:
        pass

    def operator(self, operator_id: str, **_kwargs):
        self.operators.append(operator_id)
        return SimpleNamespace()


def reset_scene() -> None:
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for material in list(bpy.data.materials):
        bpy.data.materials.remove(material)


def create_material(name: str) -> bpy.types.Material:
    return bpy.data.materials.new(name)


def create_mesh(
    name: str,
    materials: tuple[bpy.types.Material | None, ...] = (),
    material_indices: tuple[int, ...] = (0,),
) -> bpy.types.Object:
    vertices = []
    faces = []
    for index in range(len(material_indices)):
        start = len(vertices)
        x = float(index * 2)
        vertices.extend(((x, 0, 0), (x + 1, 0, 0), (x, 1, 0)))
        faces.append((start, start + 1, start + 2))

    mesh = bpy.data.meshes.new(f"{name}Mesh")
    mesh.from_pydata(vertices, (), faces)
    for material in materials:
        mesh.materials.append(material)
    for polygon, material_index in zip(mesh.polygons, material_indices, strict=True):
        polygon.material_index = material_index

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def select_only(*objects: bpy.types.Object) -> None:
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]


def draw_tab(tab: str) -> tuple[str, ...]:
    bpy.context.window_manager.vroid_blender_tools_tab = tab
    layout = LayoutRecorder()
    VROIDBLENDERTOOLS_PT_tools.draw(SimpleNamespace(layout=layout), bpy.context)
    return tuple(layout.operators)


def first_material_name(obj: bpy.types.Object) -> str | None:
    material = obj.material_slots[0].material
    return material.name if material else None


def test_separate_all_selected_meshes() -> None:
    reset_scene()
    red = create_material("SeparateRed")
    blue = create_material("SeparateBlue")
    green = create_material("SeparateGreen")
    yellow = create_material("SeparateYellow")
    solo_material = create_material("SeparateSolo")

    shaped = create_mesh("Shaped", (red, blue), (0, 1))
    shaped.location = (1, 2, 3)
    shaped.rotation_euler = (0.1, 0.2, 0.3)
    shaped.scale = (2, 3, 4)
    shaped.modifiers.new("Weighted", "WEIGHTED_NORMAL")
    shaped.shape_key_add(name="Basis")
    shaped.shape_key_add(name="Smile").data[0].co.z = 0.5

    other = create_mesh("Other", (green, yellow), (0, 1))
    other.location = (10, 0, 0)
    solo = create_mesh("Solo", (solo_material,))
    curve = bpy.data.curves.new("SelectedCurve", "CURVE")
    curve_object = bpy.data.objects.new("SelectedCurve", curve)
    bpy.context.collection.objects.link(curve_object)

    select_only(shaped, other, solo, curve_object)
    bpy.context.view_layer.objects.active = curve_object
    assert VROIDBLENDERTOOLS_OT_separate_by_material.poll(bpy.context)
    assert bpy.ops.vroid_blender_tools.separate_by_material() == {"FINISHED"}

    selected = tuple(bpy.context.selected_objects)
    selected_meshes = tuple(obj for obj in selected if obj.type == "MESH")
    assert curve_object in selected
    assert len(selected_meshes) == 5
    assert sum(len(obj.data.polygons) for obj in selected_meshes) == 5
    assert {
        obj.data.materials[0].name for obj in selected_meshes
    } == {
        "SeparateRed",
        "SeparateBlue",
        "SeparateGreen",
        "SeparateYellow",
        "SeparateSolo",
    }

    shaped_parts = tuple(obj for obj in selected_meshes if tuple(obj.location) == (1, 2, 3))
    assert len(shaped_parts) == 2
    for part in shaped_parts:
        assert tuple(round(value, 3) for value in part.rotation_euler) == (0.1, 0.2, 0.3)
        assert tuple(part.scale) == (2, 3, 4)
        assert [modifier.type for modifier in part.modifiers] == ["WEIGHTED_NORMAL"]
        assert part.data.shape_keys
        assert tuple(part.data.shape_keys.key_blocks.keys()) == ("Basis", "Smile")


def test_rename_selected_meshes() -> None:
    reset_scene()
    exact_material = create_material("ExactTarget")
    collision_material = create_material("CollisionTarget")

    exact = create_mesh("ExactSource", (None, exact_material), (1,))
    collision = create_mesh("CollisionSource", (collision_material,))
    materialless = create_mesh("Materialless")
    original_materialless_mesh_name = materialless.data.name
    collision_holder = create_mesh("CollisionTarget")
    collision_holder.data.name = "CollisionTarget"

    select_only(exact, collision, materialless)
    assert VROIDBLENDERTOOLS_OT_rename_object_and_mesh_from_material.poll(bpy.context)
    assert bpy.ops.vroid_blender_tools.rename_object_and_mesh_from_material() == {
        "FINISHED"
    }

    assert exact.name == "ExactTarget"
    assert exact.data.name == "ExactTarget"
    assert collision.name == "CollisionTarget.001"
    assert collision.data.name == "CollisionTarget.001"
    assert materialless.name == "Materialless"
    assert materialless.data.name == original_materialless_mesh_name


def test_separate_shared_mesh_data() -> None:
    reset_scene()
    base_a = create_material("SharedBaseA")
    base_b = create_material("SharedBaseB")
    one_a = create_material("SelectedOneA")
    one_b = create_material("SelectedOneB")
    two_b = create_material("SelectedTwoB")
    unselected_a = create_material("UnselectedA")
    unselected_b = create_material("UnselectedB")

    selected_one = create_mesh("SelectedOne", (base_a, base_b), (0, 1))
    original_mesh = selected_one.data
    selected_two = bpy.data.objects.new("SelectedTwo", original_mesh)
    unselected = bpy.data.objects.new("Unselected", original_mesh)
    bpy.context.collection.objects.link(selected_two)
    bpy.context.collection.objects.link(unselected)
    selected_one.location.x = 20
    selected_two.location.x = 30
    unselected.location.x = 40

    selected_one.material_slots[0].link = "OBJECT"
    selected_one.material_slots[0].material = one_a
    selected_one.material_slots[1].link = "OBJECT"
    selected_one.material_slots[1].material = one_b
    selected_two.material_slots[0].link = "OBJECT"
    selected_two.material_slots[0].material = None
    selected_two.material_slots[1].link = "OBJECT"
    selected_two.material_slots[1].material = two_b
    unselected.material_slots[0].link = "OBJECT"
    unselected.material_slots[0].material = unselected_a
    unselected.material_slots[1].link = "OBJECT"
    unselected.material_slots[1].material = unselected_b

    select_only(selected_one, selected_two)
    assert bpy.ops.vroid_blender_tools.separate_by_material() == {"FINISHED"}

    selected_parts = tuple(obj for obj in bpy.context.selected_objects if obj.type == "MESH")
    one_parts = tuple(obj for obj in selected_parts if obj.location.x == 20)
    two_parts = tuple(obj for obj in selected_parts if obj.location.x == 30)
    assert len(selected_parts) == 4
    assert all(len(obj.data.polygons) == 1 for obj in selected_parts)
    assert {first_material_name(obj) for obj in one_parts} == {
        "SelectedOneA",
        "SelectedOneB",
    }
    assert {first_material_name(obj) for obj in two_parts} == {
        None,
        "SelectedTwoB",
    }

    assert not unselected.select_get()
    assert unselected.data is original_mesh
    assert len(original_mesh.polygons) == 2
    assert tuple(material.name for material in original_mesh.materials) == (
        "SharedBaseA",
        "SharedBaseB",
    )
    assert tuple(slot.link for slot in unselected.material_slots) == ("OBJECT", "OBJECT")
    assert tuple(slot.material for slot in unselected.material_slots) == (
        unselected_a,
        unselected_b,
    )


def test_multi_material_confirmation() -> None:
    reset_scene()
    first = create_material("FirstMaterial")
    second = create_material("SecondMaterial")
    obj = create_mesh("NeedsConfirmation", (first, second), (0, 1))
    original_mesh_name = obj.data.name
    select_only(obj)

    try:
        bpy.ops.vroid_blender_tools.rename_object_and_mesh_from_material()
    except RuntimeError as error:
        assert str(error).strip() == "Error: Multiple assigned materials require confirmation"
    else:
        raise AssertionError("Multi-material naming did not require confirmation")
    assert obj.name == "NeedsConfirmation"
    assert obj.data.name == original_mesh_name

    assert bpy.ops.vroid_blender_tools.rename_object_and_mesh_from_material(
        confirmed_multiple_materials=True
    ) == {"FINISHED"}
    assert obj.name == "FirstMaterial"
    assert obj.data.name == "FirstMaterial"


def test_shared_mesh_with_object_linked_materials() -> None:
    reset_scene()
    selected_material = create_material("SelectedObjectMaterial")
    unselected_material = create_material("UnselectedObjectMaterial")
    data_material = create_material("SharedDataMaterial")
    selected = create_mesh("SelectedShared", (data_material,))
    original_mesh = selected.data
    unselected = bpy.data.objects.new("UnselectedShared", original_mesh)
    bpy.context.collection.objects.link(unselected)

    selected.material_slots[0].link = "OBJECT"
    selected.material_slots[0].material = selected_material
    unselected.material_slots[0].link = "OBJECT"
    unselected.material_slots[0].material = unselected_material
    original_mesh_name = original_mesh.name

    select_only(selected)
    assert bpy.ops.vroid_blender_tools.rename_object_and_mesh_from_material() == {
        "FINISHED"
    }

    assert selected.name == "SelectedObjectMaterial"
    assert selected.data.name == "SelectedObjectMaterial"
    assert selected.data is not original_mesh
    assert selected.material_slots[0].link == "OBJECT"
    assert selected.material_slots[0].material is selected_material
    assert unselected.name == "UnselectedShared"
    assert unselected.data is original_mesh
    assert original_mesh.name == original_mesh_name
    assert unselected.material_slots[0].material is unselected_material


def test_no_vrm_ui_and_operator_availability() -> None:
    reset_scene()
    material = create_material("NoVrmMaterial")
    mesh = create_mesh("NoVrmMesh", (material,))
    curve = bpy.data.curves.new("NoVrmCurve", "CURVE")
    curve_object = bpy.data.objects.new("NoVrmCurve", curve)
    bpy.context.collection.objects.link(curve_object)
    select_only(mesh, curve_object)
    bpy.context.view_layer.objects.active = curve_object

    assert not official_vrm_addon_available()
    assert VROIDBLENDERTOOLS_OT_separate_by_material.poll(bpy.context)
    assert VROIDBLENDERTOOLS_OT_rename_object_and_mesh_from_material.poll(bpy.context)
    assert VROIDBLENDERTOOLS_OT_separate_by_material.bl_idname in draw_tab("MESH")
    assert VROIDBLENDERTOOLS_OT_rename_object_and_mesh_from_material.bl_idname in draw_tab(
        "RENAME"
    )


def main() -> None:
    vroid_blender_tools.register()
    try:
        assert "UNDO" in VROIDBLENDERTOOLS_OT_separate_by_material.bl_options
        assert "UNDO" in VROIDBLENDERTOOLS_OT_rename_object_and_mesh_from_material.bl_options
        test_separate_all_selected_meshes()
        test_rename_selected_meshes()
        test_separate_shared_mesh_data()
        test_multi_material_confirmation()
        test_shared_mesh_with_object_linked_materials()
        test_no_vrm_ui_and_operator_availability()
    finally:
        vroid_blender_tools.unregister()

    print("VRoid Blender Tools mesh smoke test passed")


if __name__ == "__main__":
    main()
