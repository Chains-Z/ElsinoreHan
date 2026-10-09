"""地图确认框严格参数与真实XUnity组件消费回归，不启动游戏或确认移动。"""

import hashlib
import json
from pathlib import Path
import re
import subprocess
import struct
import tempfile
import unittest

from export_sol_full import encode, format_rule
from prepare_map_ui import EVIDENCE, FULL, OUT, ROOT, build, read


class MapUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = read(OUT / "map-ui-rules.json")
        cls.tests = read(OUT / "map-ui-tests.json")
        cls.evidence = read(EVIDENCE)

    def test_short_frozen_template_reproduces_export_omission(self):
        template = self.evidence["template"]
        self.assertEqual(template["source"], "Go to {0}?")
        self.assertEqual(template["target"], "前往{0}？")
        self.assertEqual(len(template["source"].replace("{0}", "")), 7)
        self.assertIsNone(format_rule(template["source"], template["target"]))

    def test_complete_reviewed_parameter_sources_are_covered(self):
        rules, tests, records, _, groups = build()
        self.assertEqual(rules, self.rules)
        self.assertEqual(tests, self.tests)
        self.assertEqual(records, self.evidence["destinations"])
        self.assertEqual(len(groups["room"]), 33)
        rooms = {row["source"] for row in groups["room"]}
        self.assertEqual(len(rooms), 31)
        self.assertIn("Upper Hallway", rooms)
        self.assertIn("Gertrude's Chambers", rooms)
        frozen_names = read(FULL / "character-names.json")
        self.assertEqual({row["source"] for row in groups["character"]}, set(frozen_names.values()))
        self.assertEqual(len(groups["character"]), len(frozen_names))
        positives = [row for row in self.tests if row["target"] is not None]
        self.assertEqual({row["parameter_source"] for row in positives},
                         rooms | set(frozen_names.values()))

    def test_whitelist_rejects_unknown_parameters_and_extra_structure(self):
        pattern = self.rules[0]["pattern"].replace("(?<destination>", "(?P<destination>").replace(r"\z", r"\Z")
        compiled = re.compile(pattern)
        self.assertNotIn("[\\s\\S]", pattern)
        for row in self.tests:
            with self.subTest(case=row["id"]):
                self.assertEqual(bool(compiled.match(row["source"])), row["target"] is not None)

    def test_case_hashes_and_frozen_leaf_translations_match(self):
        translations = {row["source"]: row for row in read(FULL / "translations.json")}
        for destination in self.evidence["destinations"]:
            if destination["source"] == "???":
                self.assertIsNone(destination["translation_id"])
                self.assertEqual(destination["target"], "???")
            else:
                original = translations[destination["source"]]
                self.assertEqual(destination["target"], original["target"])
                self.assertEqual(destination["translation_id"], original["id"])
        for row in self.tests:
            self.assertEqual(hashlib.sha256(row["source"].encode("utf-8")).hexdigest(), row["source_sha256"])
            if row["target"] is not None:
                self.assertEqual(hashlib.sha256(row["target"].encode("utf-8")).hexdigest(), row["target_sha256"])

    def test_static_source_evidence_matches_real_assembly_and_room_consumer(self):
        assembly = Path(self.evidence["assembly_path"])
        self.assertEqual(hashlib.sha256(assembly.read_bytes()).hexdigest(), self.evidence["assembly_sha256"])
        methods = {row["owner"]: row["instructions"] for row in self.evidence["methods"]}
        owner = "System.Void Elsinore.Ui.MapUI/<>c__DisplayClass32_0::<Awake>b__2(Elsinore.Game.RoomId)"
        self.assertIn('IL_003e: ldstr "Go to {0}?"', methods[owner])
        self.assertIn("IL_004f: ldfld System.String RoomMarker::playerFacingName", methods[owner])
        self.assertIn("IL_0070: callvirt System.Void TMPro.TMP_Text::SetText(System.Text.StringBuilder)", methods[owner])
        for path, digest in self.evidence["source_artifact_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), digest)

    def test_all_room_sources_match_actual_serialized_field_bytes(self):
        data_directory = Path(self.evidence["assembly_path"]).parents[1]
        checked = 0
        for destination in self.evidence["destinations"]:
            if destination["kind"] != "room":
                continue
            for origin in destination["origins"]:
                with (data_directory / origin["file"]).open("rb") as stream:
                    stream.seek(origin["absolute_offset"])
                    length = struct.unpack("<i", stream.read(4))[0]
                    self.assertGreater(length, 0)
                    self.assertLess(length, 1000)
                    actual = stream.read(length).decode("utf-8")
                self.assertEqual(actual, destination["source"])
                checked += 1
        self.assertEqual(checked, 33)

    def test_actual_recursive_xunity_consumer_accepts_all_real_parameters_and_rejects_negatives(self):
        existing = read(FULL / "dynamic-rules.json")
        identifiers = {row["id"] for row in self.rules}
        base = [row for row in existing if row.get("kind") != "recursive_ui_splitter" and row["id"] not in identifiers]
        ui = [row for row in existing if row.get("kind") == "recursive_ui_splitter" and row["id"] not in identifiers]
        for rule in self.rules:
            ui.append({**rule, "kind": "recursive_ui_splitter",
                       "encoded_line": encode('sr:"' + rule["pattern"] + '"') + "=" + encode('"' + rule["replacement"] + '"')})
        combined = base + sorted(ui, key=lambda row: row.get("priority", 0))
        # 仅写临时组合规则供组件消费者读取；不运行正式导出器、不修改正式生成文件。
        with tempfile.TemporaryDirectory(prefix="elsinorehan-map-ui-") as directory:
            dynamic = Path(directory) / "dynamic-rules.json"
            dynamic.write_text(json.dumps(combined, ensure_ascii=False), encoding="utf-8")
            result = subprocess.run([str(ROOT / "runtime/build/VerifyRecursiveUiRules.exe"),
                                     "D:/SteamLibrary/steamapps/common/Elsinore/BepInEx/plugins/XUnity.AutoTranslator/XUnity.AutoTranslator.Plugin.Core.dll",
                                     str(dynamic), str(FULL / "translations.json"), str(OUT / "map-ui-tests.json")],
                                    cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout), {"actual_recursive_xunity_consumer_passed": True,
                                                    "count": len(self.tests)})


if __name__ == "__main__":
    unittest.main()
