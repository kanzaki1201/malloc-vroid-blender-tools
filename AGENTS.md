# malloc-vroid-blender-tools

- Target Blender 5.0+ Extensions packaging.
- Integrate only with official VRM Add-on for Blender.
- Keep naming and planning logic pure Python; isolate `bpy` in adapters/UI.
- Never commit VRM samples or other avatar assets; tests use synthetic fixtures.
- Preserve VRM re-export metadata, hierarchy, rest pose, transforms, and materials.
- Commit after each completed action before starting the next action.
