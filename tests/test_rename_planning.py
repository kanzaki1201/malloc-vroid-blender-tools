"""Behavior tests for collision-safe rename planning."""

import unittest

from vroid_blender_tools.rename_planning import (
    ConflictReason,
    PlannedRename,
    RenameConflict,
    RenamePlan,
    plan_renames,
)


class PlanRenamesTests(unittest.TestCase):
    def test_unambiguous_proposal_is_planned(self) -> None:
        plan = plan_renames(
            existing_names=("J_Bip_L_UpperArm",),
            proposed_names={"J_Bip_L_UpperArm": "upper_arm.L"},
        )

        self.assertEqual(
            plan,
            RenamePlan(
                renames=(PlannedRename("J_Bip_L_UpperArm", "upper_arm.L"),),
                conflicts=(),
            ),
        )

    def test_proposal_is_withheld_when_target_already_exists(self) -> None:
        plan = plan_renames(
            existing_names=("J_Bip_L_UpperArm", "upper_arm.L"),
            proposed_names={"J_Bip_L_UpperArm": "upper_arm.L"},
        )

        self.assertEqual(
            plan,
            RenamePlan(
                renames=(),
                conflicts=(
                    RenameConflict(
                        source="J_Bip_L_UpperArm",
                        target="upper_arm.L",
                        reason=ConflictReason.TARGET_EXISTS,
                    ),
                ),
            ),
        )

    def test_all_proposals_are_withheld_when_they_share_a_target(self) -> None:
        plan = plan_renames(
            existing_names=("J_Bip_L_UpperArm", "legacy_upper_arm_left"),
            proposed_names={
                "J_Bip_L_UpperArm": "upper_arm.L",
                "legacy_upper_arm_left": "upper_arm.L",
            },
        )

        self.assertEqual(
            plan,
            RenamePlan(
                renames=(),
                conflicts=(
                    RenameConflict(
                        source="J_Bip_L_UpperArm",
                        target="upper_arm.L",
                        reason=ConflictReason.TARGET_DUPLICATED,
                    ),
                    RenameConflict(
                        source="legacy_upper_arm_left",
                        target="upper_arm.L",
                        reason=ConflictReason.TARGET_DUPLICATED,
                    ),
                ),
            ),
        )


if __name__ == "__main__":
    unittest.main()
