"""Pure-Python planning for safe object renames."""

from collections import Counter
from collections.abc import Collection, Mapping
from dataclasses import dataclass
from enum import Enum


class ConflictReason(str, Enum):
    """Why a proposed rename was withheld."""

    TARGET_EXISTS = "target_exists"
    TARGET_DUPLICATED = "target_duplicated"


@dataclass(frozen=True, slots=True)
class PlannedRename:
    """One rename that can be applied safely."""

    source: str
    target: str


@dataclass(frozen=True, slots=True)
class RenameConflict:
    """One proposal that cannot be applied safely."""

    source: str
    target: str
    reason: ConflictReason


@dataclass(frozen=True, slots=True)
class RenamePlan:
    """Safe renames and proposals withheld from application."""

    renames: tuple[PlannedRename, ...]
    conflicts: tuple[RenameConflict, ...]


def plan_renames(
    existing_names: Collection[str],
    proposed_names: Mapping[str, str],
) -> RenamePlan:
    """Return the unambiguous proposed renames for an existing name collection."""
    renames: list[PlannedRename] = []
    conflicts: list[RenameConflict] = []
    target_counts = Counter(
        target
        for source, target in proposed_names.items()
        if source in existing_names and source != target
    )

    for source, target in proposed_names.items():
        if source not in existing_names or source == target:
            continue
        if target in existing_names:
            conflicts.append(RenameConflict(source, target, ConflictReason.TARGET_EXISTS))
            continue
        if target_counts[target] > 1:
            conflicts.append(RenameConflict(source, target, ConflictReason.TARGET_DUPLICATED))
            continue
        renames.append(PlannedRename(source, target))

    return RenamePlan(renames=tuple(renames), conflicts=tuple(conflicts))
