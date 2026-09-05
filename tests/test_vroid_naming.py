"""Behavior tests for VRoid bone-name planning."""

import unittest

from vroid_blender_tools.rename_planning import (
    ConflictReason,
    PlannedRename,
    RenameConflict,
    RenamePlan,
)
from vroid_blender_tools.vroid_naming import plan_vroid_bone_renames


class PlanVroidBoneRenamesTests(unittest.TestCase):
    def test_left_vroid_bone_gets_terminal_blender_side(self) -> None:
        plan = plan_vroid_bone_renames(("J_Bip_L_UpperArm",))

        self.assertEqual(
            plan,
            RenamePlan(
                renames=(PlannedRename("J_Bip_L_UpperArm", "UpperArm.L"),),
                conflicts=(),
            ),
        )

    def test_official_vroid_prefixes_preserve_basenames(self) -> None:
        plan = plan_vroid_bone_renames(
            (
                "J_Adj_L_FaceEye",
                "J_Bip_C_Hips",
                "J_Opt_R_FaceEye",
                "J_Sec_Hair1",
                "custom_bone.L",
            )
        )

        self.assertEqual(
            plan,
            RenamePlan(
                renames=(
                    PlannedRename("J_Adj_L_FaceEye", "FaceEye.L"),
                    PlannedRename("J_Bip_C_Hips", "Hips"),
                    PlannedRename("J_Opt_R_FaceEye", "FaceEye.R"),
                    PlannedRename("J_Sec_Hair1", "Hair1"),
                ),
                conflicts=(),
            ),
        )

    def test_existing_blender_name_withholds_vroid_rename(self) -> None:
        plan = plan_vroid_bone_renames(("J_Bip_L_UpperArm", "UpperArm.L"))

        self.assertEqual(
            plan,
            RenamePlan(
                renames=(),
                conflicts=(
                    RenameConflict(
                        source="J_Bip_L_UpperArm",
                        target="UpperArm.L",
                        reason=ConflictReason.TARGET_EXISTS,
                    ),
                ),
            ),
        )


if __name__ == "__main__":
    unittest.main()
