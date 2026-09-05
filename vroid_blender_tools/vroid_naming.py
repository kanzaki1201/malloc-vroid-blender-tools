"""Pure-Python VRoid bone-name proposals."""

from collections.abc import Sequence

from .rename_planning import RenamePlan, plan_renames

_VROID_BONE_KINDS = frozenset({"Adj", "Bip", "Opt", "Sec"})


def _propose_vroid_bone_name(name: str) -> str | None:
    prefix, separator, remainder = name.partition("_")
    if prefix != "J" or not separator:
        return None

    kind, separator, basename = remainder.partition("_")
    if kind not in _VROID_BONE_KINDS or not separator or not basename:
        return None

    side, separator, side_basename = basename.partition("_")
    if separator and side_basename:
        if side in {"L", "R"}:
            return f"{side_basename}.{side}"
        if side == "C":
            return side_basename

    return basename



def plan_vroid_bone_renames(existing_names: Sequence[str]) -> RenamePlan:
    """Plan Blender-friendly names for recognizable VRoid bones."""
    proposed_names: dict[str, str] = {}
    for name in existing_names:
        target = _propose_vroid_bone_name(name)
        if target is not None:
            proposed_names[name] = target

    return plan_renames(existing_names, proposed_names)
