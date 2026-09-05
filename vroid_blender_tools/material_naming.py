"""Pure-Python VRoid material-name proposals."""

import re
from collections.abc import Collection, Sequence

from .rename_planning import RenamePlan, plan_renames

_VROID_MATERIAL_NAME = re.compile(
    r"^N\d+(?:_\d+)+_(?P<label>[A-Za-z][A-Za-z0-9]*)(?:_\d+)+_[A-Z]+(?:_\d+)*$"
)


def propose_vroid_material_name(name: str) -> str | None:
    """Return the semantic label in a recognizable VRoid material name."""
    match = _VROID_MATERIAL_NAME.fullmatch(name.removesuffix(" (Instance)"))
    return match.group("label") if match else None


def plan_vroid_material_renames(
    existing_names: Collection[str],
    scoped_names: Sequence[str],
) -> RenamePlan:
    """Plan unique names for recognizable VRoid materials in one avatar."""
    reserved_names = set(existing_names)
    proposed_names: dict[str, str] = {}

    for source in dict.fromkeys(scoped_names):
        base = propose_vroid_material_name(source)
        if base is None:
            continue

        target = base
        suffix = 1
        while target in reserved_names:
            target = f"{base}.{suffix:03d}"
            suffix += 1

        reserved_names.add(target)
        proposed_names[source] = target

    return plan_renames(existing_names, proposed_names)
