"""对来源关联错误做最低层回归，不调用模型或读凭证。"""
import copy
import json
import unittest
from pathlib import Path

import verify_inputs

OUT = Path(__file__).resolve().parent


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
        cls.inputs = {batch["file"]: json.loads((OUT / "inputs" / batch["file"]).read_text(encoding="utf-8")) for batch in cls.manifest["batches"]}
        old = json.loads((OUT.parent / "trial-2026-10-09/manifest.json").read_text(encoding="utf-8"))
        cls.old = [row["message"] for row in old["entries"]]

    def test_real_contract(self):
        verify_inputs.verify_contract(self.manifest, self.inputs, self.old)

    def test_source_hash_mismatch(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["entries"][0]["message"] += " altered"
        with self.assertRaisesRegex(ValueError, "哈希"):
            verify_inputs.verify_contract(manifest, self.inputs, self.old)

    def test_vntext_order_mismatch(self):
        inputs = copy.deepcopy(self.inputs)
        first = next(iter(inputs.values()))
        first[0], first[1] = first[1], first[0]
        with self.assertRaisesRegex(ValueError, "输入"):
            verify_inputs.verify_contract(self.manifest, inputs, self.old)

    def test_old_sample_overlap(self):
        with self.assertRaisesRegex(ValueError, "重复"):
            verify_inputs.verify_contract(self.manifest, self.inputs, self.old + [self.manifest["entries"][0]["message"]])

    def test_explicit_nested_json_path(self):
        value = {"list": [{"id": "actor", "lines": [{"id": "initial", "text": "source"}]}]}
        self.assertEqual(verify_inputs.resolve_path(value, "list[id=actor].lines[id=initial].text"), "source")


if __name__ == "__main__":
    unittest.main()
