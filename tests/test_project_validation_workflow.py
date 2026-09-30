from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "project-validation.yml"


class ProjectValidationWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = WORKFLOW.read_text(encoding="utf-8")
        cls.workflow = yaml.load(cls.source, Loader=yaml.BaseLoader)

    def test_reusable_check_has_no_write_permissions_or_secrets(self) -> None:
        self.assertIn("workflow_call", self.workflow["on"])
        self.assertEqual(self.workflow["permissions"], {"contents": "read"})
        self.assertNotIn("secrets:", self.source)
        self.assertNotIn("continue-on-error:", self.source)

    def test_kit_and_actions_are_pinned(self) -> None:
        steps = self.workflow["jobs"]["validate"]["steps"]
        actions = [step["uses"] for step in steps if "uses" in step]
        self.assertTrue(actions)
        self.assertTrue(all(re.fullmatch(r"[^@]+@[0-9a-f]{40}", action) for action in actions))
        self.assertIn("^[0-9a-f]{40}$", self.source)
        self.assertIn("ref: ${{ inputs.kit_sha }}", self.source)
        self.assertIn('git -C kit rev-parse HEAD', self.source)

    def test_project_validation_and_secret_scan_are_mandatory(self) -> None:
        self.assertIn("python -m agpctl validate --repo", self.source)
        self.assertIn("gitleaks\" git --redact", self.source)
        self.assertIn("gitleaks\" dir --redact", self.source)


if __name__ == "__main__":
    unittest.main()
