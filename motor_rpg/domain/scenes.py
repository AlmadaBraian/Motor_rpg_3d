from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]


class SceneValidationError(ValueError):
    """Raised when a scene file does not match the expected schema subset."""


@dataclass(frozen=True, slots=True)
class SceneDocument:
    scene: str
    start_map: str = ""
    script: list[JsonDict] = field(default_factory=list)
    player_start: JsonDict | None = None
    visual_novel: JsonDict | None = None
    raw: JsonDict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: JsonDict, *, fallback_name: str = "") -> SceneDocument:
        if not isinstance(data, dict):
            raise SceneValidationError("Scene data must be a JSON object")

        scene = data.get("scene") or fallback_name
        if not isinstance(scene, str) or not scene:
            raise SceneValidationError("Scene requires a non-empty 'scene' name")

        script = data.get("script", [])
        if script is None:
            script = []
        if not isinstance(script, list):
            raise SceneValidationError("Scene 'script' must be a list when present")
        for index, command in enumerate(script):
            if not isinstance(command, dict):
                raise SceneValidationError(f"Scene script command #{index} must be an object")

        player_start = data.get("player_start")
        if player_start is not None and not isinstance(player_start, dict):
            raise SceneValidationError("Scene 'player_start' must be an object when present")

        visual_novel = data.get("visual_novel")
        if visual_novel is not None and not isinstance(visual_novel, dict):
            raise SceneValidationError("Scene 'visual_novel' must be an object when present")

        start_map = (
            data.get("start_map")
            or data.get("map")
            or data.get("map_id")
            or data.get("map_name")
            or ""
        )
        if start_map is not None and not isinstance(start_map, str):
            raise SceneValidationError("Scene map identifier must be a string")

        return cls(
            scene=scene,
            start_map=start_map or "",
            script=copy.deepcopy(script),
            player_start=copy.deepcopy(player_start),
            visual_novel=copy.deepcopy(visual_novel),
            raw=copy.deepcopy(data),
        )

    @classmethod
    def load(cls, path: Path | str) -> SceneDocument:
        scene_path = Path(path)
        with scene_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return cls.from_dict(data, fallback_name=scene_path.stem)

    def to_dict(self) -> JsonDict:
        data = copy.deepcopy(self.raw)
        data["scene"] = self.scene
        if self.start_map:
            data["start_map"] = self.start_map
        data["script"] = copy.deepcopy(self.script)
        if self.player_start is not None:
            data["player_start"] = copy.deepcopy(self.player_start)
        if self.visual_novel is not None:
            data["visual_novel"] = copy.deepcopy(self.visual_novel)
        return data

    def dumps(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)
