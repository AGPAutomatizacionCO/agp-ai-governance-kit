import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agpctl.local_runtime import (
    LocalRunError,
    _docker,
    local_down,
    local_plan,
    local_up,
)


class LocalRuntimeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.repo = Path(temp.name) / "pilot"
        (self.repo / ".agp").mkdir(parents=True)
        (self.repo / ".agp" / "profile.yaml").write_text(
            "apiVersion: profile.agp/v1\n"
            "id: python-api\nkind: container\n"
            "build:\n  context: backend\n  dockerfile: backend/Dockerfile\n"
            "  dependencyManifest: backend/requirements.txt\n"
            "runtime:\n  port: 8000\n  healthPath: /health\n"
            "deploy:\n  target: app-service\n",
            encoding="utf-8",
        )

    def test_plan_solo_usa_loopback_y_se_declara_no_formal(self):
        plan = local_plan(self.repo, 18000)
        self.assertTrue(plan["localOnly"])
        self.assertFalse(plan["governanceVerified"])
        self.assertIn("127.0.0.1:18000:8000", plan["runCommand"])
        self.assertNotIn("Azure", " ".join(plan["buildCommand"] + plan["runCommand"]))

    def test_up_down_conserva_evidencia_sin_docker_real(self):
        plan = local_plan(self.repo)
        with patch("agpctl.local_runtime._docker", return_value="sha256:image") as docker:
            with patch("agpctl.local_runtime._healthy", return_value=True):
                result = local_up(plan)
            self.assertEqual("running", result["status"])
            self.assertTrue((self.repo / ".agp" / "local-runs" / "active.json").exists())
            stopped = local_down(self.repo)
        self.assertEqual("stopped", stopped["status"])
        self.assertFalse((self.repo / ".agp" / "local-runs" / "active.json").exists())
        records = list((self.repo / ".agp" / "local-runs").glob("20*.json"))
        self.assertEqual(1, len(records))
        self.assertEqual("stopped", json.loads(records[0].read_text(encoding="utf-8"))["status"])
        self.assertTrue(any(call.args[0][1] == "stop" for call in docker.call_args_list))

    def test_health_fallido_detiene_contenedor_y_no_deja_activo(self):
        plan = local_plan(self.repo)
        with (
            patch("agpctl.local_runtime._docker", return_value="sha256:image") as docker,
            patch("agpctl.local_runtime._healthy", return_value=False),
            patch("agpctl.local_runtime.time.monotonic", side_effect=[0, 2]),
            self.assertRaises(LocalRunError),
        ):
            local_up(plan, timeout_seconds=1)
        self.assertTrue(any(call.args[0][1] == "stop" for call in docker.call_args_list))
        self.assertFalse((self.repo / ".agp" / "local-runs" / "active.json").exists())

    def test_no_acepta_puerto_invalido(self):
        with self.assertRaises(LocalRunError):
            local_plan(self.repo, 70000)
        with self.assertRaises(LocalRunError):
            local_plan(self.repo, 0)

    def test_docker_sudo_no_interactivo_es_explicito(self):
        with patch("agpctl.local_runtime.subprocess.run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = "29.8.1\n"
            self.assertEqual("29.8.1", _docker(["docker", "version"], docker_sudo=True))
        self.assertEqual(["sudo", "-n", "docker", "version"], run.call_args.args[0])

    def test_up_down_transmite_sudo_sin_elevar_python(self):
        plan = local_plan(self.repo)
        with (
            patch("agpctl.local_runtime._docker", return_value="sha256:image") as docker,
            patch("agpctl.local_runtime._healthy", return_value=True),
        ):
            result = local_up(plan, docker_sudo=True)
            stopped = local_down(self.repo, docker_sudo=True)
        self.assertTrue(result["dockerViaSudo"])
        self.assertEqual("stopped", stopped["status"])
        self.assertTrue(all(call.kwargs["docker_sudo"] for call in docker.call_args_list))
