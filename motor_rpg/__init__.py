"""Motor RPG 3D package namespace.

The package separates pure domain rules, runtime orchestration, rendering helpers and
editor-facing services. Existing top-level modules remain as compatibility entry
points while new code should import from this package.
"""

__all__ = ["domain", "runtime", "rendering", "editor"]
