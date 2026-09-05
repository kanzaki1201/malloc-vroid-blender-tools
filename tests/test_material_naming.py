"""Behavior tests for VRoid material-name planning."""

import unittest

from vroid_blender_tools.material_naming import plan_vroid_material_renames
from vroid_blender_tools.rename_planning import PlannedRename, RenamePlan


class PlanVroidMaterialRenamesTests(unittest.TestCase):
    def test_vroid_codes_are_removed_without_changing_semantic_case(self) -> None:
        names = (
            "N00_000_00_FaceMouth_00_FACE (Instance)",
            "N00_005_01_Shoes_01_CLOTH (Instance)",
        )

        plan = plan_vroid_material_renames(names, names)

        self.assertEqual(
            plan,
            RenamePlan(
                renames=(
                    PlannedRename(names[0], "FaceMouth"),
                    PlannedRename(names[1], "Shoes"),
                ),
                conflicts=(),
            ),
        )

    def test_duplicate_labels_receive_blender_numbering(self) -> None:
        names = (
            "N00_000_Hair_00_HAIR_01 (Instance)",
            "N00_001_Hair_00_HAIR_02 (Instance)",
        )

        plan = plan_vroid_material_renames(names, names)

        self.assertEqual(
            tuple(rename.target for rename in plan.renames),
            ("Hair", "Hair.001"),
        )

    def test_existing_scene_material_reserves_its_name(self) -> None:
        source = "N00_000_Hair_00_HAIR_01 (Instance)"

        plan = plan_vroid_material_renames((source, "Hair"), (source,))

        self.assertEqual(plan.renames, (PlannedRename(source, "Hair.001"),))

    def test_clean_and_unknown_names_remain_unchanged(self) -> None:
        names = ("FaceMouth", "Custom_Material")

        self.assertEqual(
            plan_vroid_material_renames(names, names),
            RenamePlan(renames=(), conflicts=()),
        )


if __name__ == "__main__":
    unittest.main()
