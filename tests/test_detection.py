import json
import tempfile
import unittest
from pathlib import Path

from agpctl.detection import detect_project


class DetectionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.repo = Path(temp.name) / "repo"
        self.repo.mkdir()

    def _write(self, relative: str, content: str = "") -> None:
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_python_api_unico(self):
        self._write("backend/requirements.txt", "Flask==3.1.3\n")
        self._write("backend/app.py", "")
        result = detect_project(self.repo)
        self.assertEqual("python-api", result["recommendedProfile"])
        self.assertFalse(result["requiresConfirmation"])
        self.assertTrue(result["readOnly"])

    def test_node_api_unico(self):
        self._write("backend/package.json", json.dumps({"scripts": {"start": "node index.mjs"}}))
        self._write("backend/server.mjs", "")
        result = detect_project(self.repo)
        self.assertEqual("node-api", result["recommendedProfile"])

    def test_react_static_unico(self):
        self._write("frontend/package.json", json.dumps({
            "scripts": {"build": "vite build"}, "dependencies": {"react": "19.0.0"},
        }))
        self._write("frontend/index.html", "")
        self._write("frontend/src/main.jsx", "")
        result = detect_project(self.repo)
        self.assertEqual("react-static", result["recommendedProfile"])

    def test_fullstack_es_ambiguo_no_se_elige_silenciosamente(self):
        self._write("backend/requirements.txt", "Flask==3.1.3\n")
        self._write("backend/app.py", "")
        self._write("frontend/package.json", json.dumps({
            "scripts": {"build": "vite build"}, "dependencies": {"react": "19.0.0"},
        }))
        self._write("frontend/index.html", "")
        self._write("frontend/src/main.jsx", "")
        result = detect_project(self.repo)
        self.assertTrue(result["requiresConfirmation"])
        self.assertIsNone(result["recommendedProfile"])
        self.assertEqual(2, len(result["candidates"]))

    def test_paquete_invalido_no_se_interpreta_como_perfil(self):
        self._write("package.json", "{invalid")
        result = detect_project(self.repo)
        self.assertIsNone(result["recommendedProfile"])
        self.assertTrue(any("no se puede analizar" in warning for warning in result["warnings"]))

    def test_frontend_incompleto_sigue_contando_como_componente(self):
        self._write("backend/requirements.txt", "Flask==3.1.3\n")
        self._write("backend/app.py", "")
        self._write("frontend/package.json", json.dumps({
            "scripts": {"build": "vite build"}, "dependencies": {"react": "19.0.0"},
        }))
        self._write("frontend/src/main.jsx", "")
        result = detect_project(self.repo)
        self.assertTrue(result["requiresConfirmation"])
        self.assertIsNone(result["recommendedProfile"])
        self.assertTrue(any("sin index.html" in warning for warning in result["warnings"]))

    def test_perfil_declarado_divergente_se_advierte(self):
        self._write("backend/requirements.txt", "Flask==3.1.3\n")
        self._write("backend/app.py", "")
        self._write(".agp/profile.yaml", "id: node-api\n")
        result = detect_project(self.repo)
        self.assertEqual("node-api", result["declaredProfile"])
        self.assertTrue(any("no coincide" in warning for warning in result["warnings"]))
