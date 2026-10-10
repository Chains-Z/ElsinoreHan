"""用真实门对象验证提示字段与内部场景、音效的分类边界。"""
import hashlib
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("audit_door_tooltip", ROOT / "analysis/ui-audit/audit-door-tooltip.py")
door_audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(door_audit)


class DoorTooltipAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.file_count, cls.doors = door_audit.read_doors()
        cls.audit = door_audit.audit

    def test_actual_source_is_player_facing_override(self):
        door = next(d for d in self.doors if d["file"] == "level1" and d["path_id"] == 15212)
        fields = self.audit.door_marker_string_fields(door["raw"], door["pos"])
        source, _ = self.audit.read_string(door["raw"], 80)
        self.assertEqual(source, "Out to Sea")
        self.assertEqual(hashlib.sha256(source.encode()).hexdigest(), "fa1153552ae56de681289f76fdf597f2ea95925218f6b45c4d11f86412296d05")
        self.assertEqual(fields[80]["field"], "OverrideTooltip")
        self.assertEqual(fields[80]["decision"], "player_facing")

    def test_same_object_locked_scene_stays_internal(self):
        door = next(d for d in self.doors if d["file"] == "level1" and d["path_id"] == 15212)
        fields = self.audit.door_marker_string_fields(door["raw"], door["pos"])
        source, _ = self.audit.read_string(door["raw"], 96)
        self.assertEqual(source, "Enviro_ShipNotPresent")
        self.assertEqual(fields[96]["field"], "LockedDoorScene")
        self.assertEqual(fields[96]["decision"], "excluded")

    def test_all_actual_door_objects_reject_internal_fields(self):
        self.assertEqual(self.file_count, 12)
        self.assertEqual(len(self.doors), 74)
        visible = []
        for door in self.doors:
            fields = self.audit.door_marker_string_fields(door["raw"], door["pos"])
            self.assertEqual(len(fields), 4)
            for offset, descriptor in fields.items():
                with self.subTest(file=door["file"], path_id=door["path_id"], field=descriptor["field"]):
                    source, _ = self.audit.read_string(door["raw"], offset)
                    if descriptor["field"] == "OverrideTooltip":
                        self.assertEqual(descriptor["decision"], "player_facing")
                        if source:
                            visible.append(source)
                    else:
                        self.assertEqual(descriptor["decision"], "excluded")
        self.assertEqual(visible, ["Out to Sea"])


if __name__ == "__main__":
    unittest.main()
