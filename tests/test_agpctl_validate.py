import json
import tempfile
import unittest
from pathlib import Path

from agpctl.__main__ import KIT_ROOT, validate_project


class ValidateProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        (self.repo / ".agp").mkdir()
        (self.repo / ".github").mkdir()
        (self.repo / "backend").mkdir()
        (self.repo / "infra").mkdir()
        (self.repo / ".agp" / "governance.yaml").write_text(
            (KIT_ROOT / "examples" / "governance.valid.yaml").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        (self.repo / ".agp" / "profile.yaml").write_text(
            (KIT_ROOT / "examples" / "profile-container.valid.yaml").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        self.deploy_path = self.repo / ".github" / "agp-deploy.json"
        self.deploy_path.write_text(
            (KIT_ROOT / "examples" / "agp-deploy-v2.valid.json").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        (self.repo / "backend" / "Dockerfile").write_text(
            "FROM python:3.13-slim@sha256:" + "a" * 64 + "\nUSER 10001\n",
            encoding="utf-8",
        )
        (self.repo / "backend" / "requirements.txt").write_text("Flask==3.1.2\n", encoding="utf-8")
        (self.repo / "infra" / "sitecontainers.bicep").write_text("// fixture\n", encoding="utf-8")

    def test_valid_contracts_pass_without_network_lookup(self):
        self.assertEqual([], validate_project(self.repo, verify_tag=False))

    def test_mutable_image_root_user_and_unpinned_dependency_fail(self):
        (self.repo / "backend" / "Dockerfile").write_text("FROM python:latest\nUSER root\n", encoding="utf-8")
        (self.repo / "backend" / "requirements.txt").write_text("Flask>=3\n", encoding="utf-8")
        issues = validate_project(self.repo, verify_tag=False)
        self.assertTrue(any("sin digest" in issue for issue in issues))
        self.assertTrue(any("no-root" in issue for issue in issues))
        self.assertTrue(any("versión exacta" in issue for issue in issues))

    def test_unapproved_observed_data_access_fails(self):
        deployment = json.loads(self.deploy_path.read_text(encoding="utf-8"))
        deployment["campos"]["MapeoAccesoBD"]["valor"] = json.loads(
            (KIT_ROOT / "templates" / "data-access-manifest.example.json").read_text(encoding="utf-8")
        )
        self.deploy_path.write_text(json.dumps(deployment), encoding="utf-8")
        issues = validate_project(self.repo, verify_tag=False)
        self.assertTrue(any("faltan aprobaciones confiables" in issue for issue in issues))

    def test_mismatched_runtime_fails(self):
        deployment = json.loads(self.deploy_path.read_text(encoding="utf-8"))
        deployment["azure"]["recursos"][0]["Puerto"] = 5000
        self.deploy_path.write_text(json.dumps(deployment), encoding="utf-8")
        issues = validate_project(self.repo, verify_tag=False)
        self.assertTrue(any("Puerto y health check" in issue for issue in issues))

    def test_multistage_alias_is_not_an_external_image(self):
        (self.repo / "backend" / "Dockerfile").write_text(
            "FROM python:3.13-slim@sha256:"
            + "a" * 64
            + " AS build\nFROM build AS runtime\nUSER 10001\n",
            encoding="utf-8",
        )
        self.assertEqual([], validate_project(self.repo, verify_tag=False))

    def test_multistage_external_image_still_needs_digest(self):
        (self.repo / "backend" / "Dockerfile").write_text(
            "FROM python:3.13-slim@sha256:"
            + "a" * 64
            + " AS build\nFROM alpine:latest AS runtime\nUSER 10001\n",
            encoding="utf-8",
        )
        issues = validate_project(self.repo, verify_tag=False)
        self.assertTrue(any("alpine:latest" in issue and "sin digest" in issue for issue in issues))

    def test_local_preview_no_afirma_release_pero_mantiene_gates(self):
        (self.repo / ".agp" / "governance.yaml").unlink()
        self.assertEqual([], validate_project(self.repo, local_preview=True))
        self.assertTrue(any("governance.yaml" in issue for issue in validate_project(self.repo, verify_tag=False)))
        (self.repo / "backend" / "Dockerfile").write_text("FROM python:latest\nUSER root\n", encoding="utf-8")
        issues = validate_project(self.repo, local_preview=True)
        self.assertTrue(any("sin digest" in issue for issue in issues))
        self.assertTrue(any("no-root" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
