"""`agpctl login check`: fixtures «antes» (plantilla vieja con MSAL 5 y redirectUri en la raíz) y «después» (la plantilla actual del kit)."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agpctl.login import RUTA_PUENTE, check, excluido_por_dockerignore

ROOT = Path(__file__).resolve().parents[1]
PLANTILLA = ROOT / "templates" / "auth-estandar"
ANTES = ROOT / "tests" / "fixtures" / "login" / "antes"
PAQUETE_MSAL5 = {"name": "demo", "private": True, "dependencies": {"@azure/msal-browser": "5.29.0"}, "devDependencies": {"vite": "7.1.9"}}


def construir_despues(destino: Path, base: str = "", paquete=None) -> Path:
    """Un desarrollo bien integrado: los archivos de la plantilla actual + la compilación y el servidor que la acompañan."""
    frontend = destino / base if base else destino
    for origen, copia in (
        ("auth/redirect.html", "auth/redirect.html"),
        ("src/auth/redirect.js", "src/auth/redirect.js"),
        ("src/config/msal.js", "src/config/msal.js"),
        ("vite.config.example.js", "vite.config.js"),
    ):
        (frontend / copia).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(PLANTILLA / origen, frontend / copia)
    (frontend / "package.json").write_text(json.dumps(paquete or PAQUETE_MSAL5), encoding="utf-8")
    (destino / ".agp").mkdir(exist_ok=True)
    shutil.copy(PLANTILLA / ".agp" / "entra.yaml", destino / ".agp" / "entra.yaml")
    (destino / "backend").mkdir(exist_ok=True)
    shutil.copy(PLANTILLA / "backend" / "src" / "flask_config" / "bp_retorno_msal.py", destino / "backend" / "bp_retorno_msal.py")
    return destino


class LoginCheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    # ── fixtures «antes» y «después» ──
    def test_antes_plantilla_vieja_falla_con_mensajes_accionables(self):
        r = check(ANTES)
        self.assertFalse(r["valid"])
        texto = "\n".join(r["issues"])
        self.assertIn("broadcastResponseToMainFrame", texto)         # sin script puente
        self.assertIn("falta la página auth/redirect.html", texto)    # sin página puente
        self.assertIn("redirectUri apunta a la raíz del sitio", texto)
        self.assertIn("Error al iniciar sesión. Intenta de nuevo.", texto)   # el síntoma que ve la persona
        self.assertIn("falta postLogoutRedirectUri", texto)
        self.assertIn("redirectUriPath es «/»", texto)                # entra.yaml no coincide
        self.assertIn("la compilación no incluye la página puente", texto)
        self.assertIn(f"ningún servidor ni configuración de hosting expone {RUTA_PUENTE}", texto)
        self.assertTrue(all("Cómo corregirlo" in i for i in r["issues"]), r["issues"])

    def test_despues_plantilla_actual_pasa_sin_observaciones(self):
        r = check(construir_despues(self.dir))
        self.assertTrue(r["valid"], r["issues"])
        self.assertEqual(r["ruta"], RUTA_PUENTE)

    def test_despues_con_frontend_en_subcarpeta(self):
        r = check(construir_despues(self.dir, base="frontend"))
        self.assertTrue(r["valid"], r["issues"])

    # ── reglas sueltas ──
    def test_sin_msal_browser_no_hay_nada_que_revisar(self):
        (self.dir / "package.json").write_text(json.dumps({"name": "x", "dependencies": {"react": "19.0.0"}}), encoding="utf-8")
        r = check(self.dir)
        self.assertTrue(r["valid"])
        self.assertIn("nada que revisar", r["note"])

    def test_con_msal_4_la_pagina_puente_no_es_obligatoria(self):
        construir_despues(self.dir, paquete={**PAQUETE_MSAL5, "dependencies": {"@azure/msal-browser": "^4.7.0"}})
        shutil.rmtree(self.dir / "auth")
        r = check(self.dir)
        self.assertTrue(r["valid"], r["issues"])
        self.assertTrue(any("(< 5)" in a for a in r["avisos"]))

    def test_redirect_uri_y_entra_yaml_deben_coincidir(self):
        construir_despues(self.dir)
        entra = self.dir / ".agp" / "entra.yaml"
        entra.write_text(entra.read_text(encoding="utf-8").replace("redirectUriPath: /auth/redirect", "redirectUriPath: /auth/callback"), encoding="utf-8")
        issues = check(self.dir)["issues"]
        self.assertEqual(len(issues), 1)
        self.assertIn("redirectUriPath es «/auth/callback» y el código vuelve a «/auth/redirect»", issues[0])

    def test_la_pagina_puente_no_puede_montar_la_aplicacion(self):
        construir_despues(self.dir)
        pagina = self.dir / "auth" / "redirect.html"
        pagina.write_text(pagina.read_text(encoding="utf-8").replace("<body>", '<body><div id="root"></div>'), encoding="utf-8")
        self.assertTrue(any('id="root"' in i for i in check(self.dir)["issues"]))

    def test_sin_post_logout_redirect_uri_falla(self):
        construir_despues(self.dir)
        msal = self.dir / "src" / "config" / "msal.js"
        msal.write_text("\n".join(linea for linea in msal.read_text(encoding="utf-8").splitlines() if "postLogoutRedirectUri" not in linea), encoding="utf-8")
        self.assertTrue(any("falta postLogoutRedirectUri" in i for i in check(self.dir)["issues"]))

    # ── .dockerignore: la lista blanca debe dejar pasar la página puente ──
    LISTA_BLANCA_SIN_PUENTE = "*\n!backend\n!.agp\n!frontend\nfrontend/*\n!frontend/package.json\n!frontend/index.html\n!frontend/vite.config.js\n!frontend/src\n"

    def test_dockerignore_lista_blanca_que_excluye_la_pagina_puente(self):
        construir_despues(self.dir, base="frontend")
        (self.dir / ".dockerignore").write_text(self.LISTA_BLANCA_SIN_PUENTE, encoding="utf-8")
        issues = check(self.dir)["issues"]
        self.assertTrue(any(".dockerignore" in i and "frontend/auth/redirect.html" in i and "!frontend/auth" in i for i in issues), issues)

    def test_dockerignore_con_la_regla_de_la_pagina_puente_pasa(self):
        construir_despues(self.dir, base="frontend")
        (self.dir / ".dockerignore").write_text(self.LISTA_BLANCA_SIN_PUENTE + "!frontend/auth\n", encoding="utf-8")
        self.assertTrue(check(self.dir)["valid"], check(self.dir)["issues"])

    def test_dockerignore_de_la_carpeta_del_frontend(self):
        construir_despues(self.dir, base="frontend")
        (self.dir / "frontend" / ".dockerignore").write_text("*\n!package.json\n!src\n!index.html\n", encoding="utf-8")
        issues = check(self.dir)["issues"]
        self.assertTrue(any("frontend/.dockerignore" in i and "auth/redirect.html" in i for i in issues), issues)

    def test_excluido_por_dockerignore(self):
        self.assertTrue(excluido_por_dockerignore("*\n!src\n", "auth/redirect.html"))
        self.assertFalse(excluido_por_dockerignore("*\n!src\n!auth\n", "auth/redirect.html"))
        self.assertTrue(excluido_por_dockerignore("node_modules\nauth\n", "auth/redirect.html"))
        self.assertFalse(excluido_por_dockerignore("**/*.pyc\n.env*\n", "auth/redirect.html"))
        self.assertTrue(excluido_por_dockerignore("**/*.html\n", "frontend/auth/redirect.html"))
        self.assertFalse(excluido_por_dockerignore("**/*.html\n!frontend/auth/redirect.html\n", "frontend/auth/redirect.html"))

    # ── línea de comandos ──
    def _agpctl(self, repo: Path):
        proceso = subprocess.run([sys.executable, "-m", "agpctl", "login", "check", "--repo", str(repo)], cwd=ROOT, capture_output=True, text=True, check=False)
        return proceso.returncode, json.loads(proceso.stdout)

    def test_comando_devuelve_1_antes_y_0_despues(self):
        codigo, salida = self._agpctl(ANTES)
        self.assertEqual(codigo, 1)
        self.assertFalse(salida["valid"])
        codigo, salida = self._agpctl(construir_despues(self.dir))
        self.assertEqual(codigo, 0)
        self.assertTrue(salida["valid"])


if __name__ == "__main__":
    unittest.main()
