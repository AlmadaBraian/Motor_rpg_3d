from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from motor_rpg.domain.config import AssetPolicy  # noqa: E402


def main() -> int:
    root = ROOT
    policy = AssetPolicy()
    errors: list[str] = []
    for folder in policy.asset_roots:
        asset_root = root / folder
        if not asset_root.exists():
            continue
        for path in asset_root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in policy.allowed_extensions:
                errors.append(f"Unsupported extension: {path.relative_to(root)}")
            if path.stat().st_size > policy.max_bytes:
                errors.append(f"File too large: {path.relative_to(root)}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("Asset policy OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
