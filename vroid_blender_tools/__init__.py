"""VRoid Blender Tools extension entry point."""


def register() -> None:
    from .registration import register as register_extension

    register_extension()


def unregister() -> None:
    from .registration import unregister as unregister_extension

    unregister_extension()
