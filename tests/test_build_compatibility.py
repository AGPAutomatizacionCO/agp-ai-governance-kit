import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_compatibility import build


class BuildCompatibilityTests(unittest.TestCase):
    def test_manifest_has_exact_sha_and_no_pending(self):
        result = build("a" * 40)
        self.assertEqual("a" * 40, result["kitCommit"])
        self.assertEqual("v4.0.0-rc.1", result["kitVersion"])
        self.assertNotIn("pending", json.dumps(result))

    def test_rejects_short_sha(self):
        with self.assertRaisesRegex(ValueError, "SHA completo"):
            build("a" * 7)

    def test_rejects_pending_profile(self):
        with tempfile.TemporaryDirectory() as directory:
            template = Path(directory) / "compatibility.json"
            template.write_text(json.dumps({
                "kitVersion": "v4.0.0-rc.1", "status": "candidate",
                "agpctl": {"minInclusive": "0.1.0", "maxExclusive": "0.1.1"},
                "profiles": {"python-api": "pending"},
            }), encoding="utf-8")
            with self.assertRaises(ValueError):
                build("a" * 40, template=template)


if __name__ == "__main__":
    unittest.main()
