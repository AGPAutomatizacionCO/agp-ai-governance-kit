"""Regression tests for immutable governance references in project manifests."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import validate_governance_ref as governance_ref

VERSION = "v4.0.0-rc.1"
COMMIT = "a" * 40
OTHER_COMMIT = "b" * 40


class GovernanceRefTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.manifest = Path(self.temp.name) / "governance.yaml"

    def write_manifest(self, commit: str = COMMIT) -> None:
        self.manifest.write_text(
            "apiVersion: governance.agp/v1\n"
            "kit:\n"
            "  source: AGPAutomatizacionCO/agp-ai-governance-kit\n"
            f"  version: {VERSION}\n"
            f"  ref: {commit}\n"
            "profile: python-api\n",
            encoding="utf-8",
        )

    def test_exact_tag_commit_is_accepted(self) -> None:
        self.write_manifest()
        with patch.object(governance_ref, "resolve_tag", return_value=COMMIT) as lookup:
            self.assertEqual(governance_ref.validate(self.manifest), [])
        lookup.assert_called_once_with(VERSION)

    def test_annotated_tag_resolves_to_peeled_commit(self) -> None:
        result = subprocess.CompletedProcess(
            args=["git", "ls-remote"],
            returncode=0,
            stdout=(
                f"{OTHER_COMMIT}\trefs/tags/{VERSION}\n"
                f"{COMMIT}\trefs/tags/{VERSION}^{{}}\n"
            ),
        )
        with patch.object(governance_ref.subprocess, "run", return_value=result):
            self.assertEqual(governance_ref.resolve_tag(VERSION), COMMIT)

    def test_lightweight_tag_resolves_to_commit(self) -> None:
        result = subprocess.CompletedProcess(
            args=["git", "ls-remote"],
            returncode=0,
            stdout=f"{COMMIT}\trefs/tags/{VERSION}\n",
        )
        with patch.object(governance_ref.subprocess, "run", return_value=result):
            self.assertEqual(governance_ref.resolve_tag(VERSION), COMMIT)

    def test_mismatched_tag_commit_is_rejected(self) -> None:
        self.write_manifest()
        with patch.object(governance_ref, "resolve_tag", return_value=OTHER_COMMIT):
            errors = governance_ref.validate(self.manifest)
        self.assertTrue(any("apunta a" in error for error in errors))

    def test_missing_tag_is_rejected(self) -> None:
        self.write_manifest()
        with patch.object(governance_ref, "resolve_tag", return_value=""):
            errors = governance_ref.validate(self.manifest)
        self.assertTrue(any("no existe" in error for error in errors))

    def test_network_failure_fails_closed(self) -> None:
        self.write_manifest()
        with patch.object(
            governance_ref,
            "resolve_tag",
            side_effect=subprocess.TimeoutExpired("git", 20),
        ):
            errors = governance_ref.validate(self.manifest)
        self.assertTrue(any("No se pudo comprobar" in error for error in errors))

    def test_duplicate_yaml_key_is_rejected_before_lookup(self) -> None:
        self.write_manifest()
        with self.manifest.open("a", encoding="utf-8") as stream:
            stream.write("profile: node-api\n")
        with patch.object(governance_ref, "resolve_tag") as lookup:
            errors = governance_ref.validate(self.manifest)
        self.assertTrue(any("duplicada" in error for error in errors))
        lookup.assert_not_called()

    def test_non_sha_reference_is_rejected_before_lookup(self) -> None:
        self.write_manifest("main")
        with patch.object(governance_ref, "resolve_tag") as lookup:
            errors = governance_ref.validate(self.manifest)
        self.assertTrue(any("ref" in error for error in errors))
        lookup.assert_not_called()


if __name__ == "__main__":
    unittest.main()
