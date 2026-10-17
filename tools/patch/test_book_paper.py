"""用标准DXT5解码与真实书页检测旧遮盖偏位、纸块边界和原图改写风险。"""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
STREAM = Path("D:/SteamLibrary/steamapps/common/Elsinore/Elsinore_Data/sharedassets1.assets.resS")
SOURCE_SHA256 = "7bd5234ad6cf2d6b3dfaa78b8a140c506f1ad4f9e435f6c75810188fafdc35fb"


@unittest.skipUnless(os.name == "nt" and STREAM.exists(), "需要本机真实游戏资源与.NET编译器")
class BookPaperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.directory = Path(cls.temporary.name)
        cls.executable = cls.directory / "paper.exe"
        subprocess.run([str(Path(os.environ["WINDIR"]) / "Microsoft.NET/Framework/v4.0.30319/csc.exe"),
                        "/nologo", "/out:" + str(cls.executable), str(ROOT / "tools/patch/BookPaperReconstruction.cs"),
                        str(ROOT / "tools/patch/BookPaperReconstructionTests.cs")], check=True, capture_output=True)
        with STREAM.open("rb") as stream:
            stream.seek(371948484)
            cls.blocks = stream.read(2048 * 1400)
        assert hashlib.sha256(cls.blocks).hexdigest() == SOURCE_SHA256
        (cls.directory / "source.dxt5").write_bytes(cls.blocks)
        result = subprocess.run([str(cls.executable), str(cls.directory / "source.dxt5"), str(cls.directory / "paper")],
                                check=True, capture_output=True, text=True)
        cls.report = json.loads(result.stdout)
        cls.original = np.frombuffer((cls.directory / "paper-source.rgba").read_bytes(), np.uint8).reshape(1400, 2048, 4)
        cls.clean = np.frombuffer((cls.directory / "paper-clean.rgba").read_bytes(), np.uint8).reshape(1400, 2048, 4)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_codec_and_rejection_boundaries(self):
        result = subprocess.run([str(self.executable)], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), {"pure_cases": 7, "passed": True})

    def test_decoder_matches_standard_consumer_exactly(self):
        reference = np.array(Image.frombytes("RGBA", (2048, 1400), self.blocks, "bcn", 3))
        np.testing.assert_array_equal(self.original, reference)

    def test_repair_changes_only_ink_mask_and_keeps_alpha(self):
        mask = np.zeros(1400 * 2048, dtype=bool)
        indices = [int(v) for v in (self.directory / "paper-mask.txt").read_text().splitlines()]
        mask[indices] = True
        changed = np.any(self.original != self.clean, axis=2).reshape(-1)
        self.assertFalse(np.any(changed & ~mask))
        self.assertLess(np.sum(changed), 10000)
        self.assertGreater(np.sum(changed), 5000)
        np.testing.assert_array_equal(self.original[:, :, 3], self.clean[:, :, 3])
        self.assertLess(self.report["residual"], 0.0021)
        top = self.clean[::-1]
        for box in ((1350, 240, 1650, 334), (1425, 458, 1555, 548)):
            roi = top[box[1]:box[3], box[0]:box[2], :3]
            self.assertFalse(np.any(np.max(roi, axis=2) < 150), "仍有英文深色笔画")

    def test_legacy_cropped_coordinates_reproduce_uncovered_english(self):
        top = self.original[::-1]
        ink = np.zeros((1400, 2048), dtype=bool)
        for box in ((1350, 240, 1650, 334), (1425, 458, 1555, 548)):
            ink[box[1]:box[3], box[0]:box[2]] = np.max(top[box[1]:box[3], box[0]:box[2], :3], axis=2) < 150
        legacy = np.zeros_like(ink)
        for x, y, w, h in ((0.64, 0.13, 0.19, 0.075), (0.69, 0.30, 0.10, 0.075)):
            legacy[int(y * 1400):int((y + h) * 1400), int(x * 2048):int((x + w) * 2048)] = True
        self.assertGreater(np.sum(ink & ~legacy), 500, "旧坐标应复现用户截图中的英文残留")


if __name__ == "__main__":
    unittest.main()
