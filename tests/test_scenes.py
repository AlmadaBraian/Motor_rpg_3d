from __future__ import annotations

import json

import pytest

from motor_rpg.domain.scenes import SceneDocument, SceneValidationError


def test_scene_round_trip_preserves_script_and_start_alias(tmp_path):
    scene_path = tmp_path / "intro.json"
    scene_path.write_text(
        json.dumps(
            {
                "scene": "Intro",
                "map_id": "Map001",
                "player_start": {"gx": 2, "gy": 3, "facing": "south"},
                "script": [{"action": "dialog", "text": "Hola"}],
            }
        ),
        encoding="utf-8",
    )

    document = SceneDocument.load(scene_path)

    assert document.scene == "Intro"
    assert document.start_map == "Map001"
    assert document.script == [{"action": "dialog", "text": "Hola"}]
    assert SceneDocument.from_dict(json.loads(document.dumps())).to_dict() == document.to_dict()


def test_scene_rejects_non_object_script_entries():
    with pytest.raises(SceneValidationError):
        SceneDocument.from_dict({"scene": "Broken", "script": ["wait"]})
