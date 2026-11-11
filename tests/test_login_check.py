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


FIXTURES = ROOT / "tests" / "fixtures" / "login"


class InicializacionMsalTests(unittest.TestCase):
    """MSAL >= 3 exige initialize() antes de cualquier operación: sin eso «Error al iniciar sesión» al instante y sin peticiones en Network (AGPTS, 2026-11-11)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def _frontend(self, archivos: dict, version="5.29.0"):
        carpeta = self.dir / "frontend"
        for nombre, contenido in archivos.items():
            ruta = carpeta / nombre
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_text(contenido, encoding="utf-8")
        (carpeta / "package.json").write_text(json.dumps({"name": "x", "dependencies": {"@azure/msal-browser": version}}), encoding="utf-8")
        return self.dir

    @staticmethod
    def _inicializacion(resultado):
        return [i for i in resultado["issues"] if "uninitialized_public_client_application" in i]

    def test_antes_agpts_sin_initialize_se_detecta_con_guia(self):
        r = check(FIXTURES / "agpts-initialize-antes")
        hallazgos = self._inicializacion(r)
        self.assertEqual(len(hallazgos), 1, r["issues"])
        self.assertIn("Cómo corregirlo", hallazgos[0])
        self.assertIn("ninguna petición en Network", hallazgos[0])
        self.assertIn("usarMsalInicializado", hallazgos[0])

    def test_despues_agpts_con_initialize_no_se_marca(self):
        self.assertEqual(self._inicializacion(check(FIXTURES / "agpts-initialize-despues")), [])

    def test_la_plantilla_actual_del_kit_inicializa(self):
        carpeta = self.dir / "frontend"
        for origen in ("src/config/msal.js", "src/contexts/AuthContext.jsx"):
            (carpeta / origen).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(PLANTILLA / origen, carpeta / origen)
        (carpeta / "package.json").write_text(json.dumps(PAQUETE_MSAL5), encoding="utf-8")
        self.assertEqual(self._inicializacion(check(self.dir)), [])

    def test_con_msal_provider_no_se_marca(self):
        raiz = self._frontend({
            "src/config/msal.js": "export const i = new PublicClientApplication(c);",
            "src/main.jsx": "import { MsalProvider } from '@azure/msal-react'; render(<MsalProvider instance={i} />);",
            "src/Auth.jsx": "await i.loginPopup(req);",
        })
        self.assertEqual(self._inicializacion(check(raiz)), [])

    def test_un_comentario_que_menciona_msal_provider_no_inicializa(self):
        raiz = self._frontend({
            "src/config/msal.js": "// sin MsalProvider ni initialize() " + chr(10) + "export const i = new PublicClientApplication(c);",
            "src/Auth.jsx": "await i.loginPopup(req);",
        })
        self.assertEqual(len(self._inicializacion(check(raiz))), 1)

    def test_tambien_aplica_al_flujo_por_redireccion(self):
        raiz = self._frontend({
            "src/config/msal.js": "export const i = new PublicClientApplication(c);",
            "src/Auth.jsx": "await i.loginRedirect(req);",
        })
        r = check(raiz)
        self.assertEqual(len(self._inicializacion(r)), 1, r["issues"])
        self.assertFalse(r["valid"])

    def test_sin_operaciones_o_con_msal_2_no_se_marca(self):
        solo_config = self._frontend({"src/config/msal.js": "export const i = new PublicClientApplication(c);"})
        self.assertEqual(self._inicializacion(check(solo_config)), [])
        otro = tempfile.TemporaryDirectory()
        self.addCleanup(otro.cleanup)
        carpeta = Path(otro.name) / "frontend"
        (carpeta / "src").mkdir(parents=True)
        (carpeta / "src" / "a.js").write_text("const i = new PublicClientApplication(c); i.loginPopup(r);", encoding="utf-8")
        (carpeta / "package.json").write_text(json.dumps({"dependencies": {"@azure/msal-browser": "2.39.0"}}), encoding="utf-8")
        self.assertEqual(self._inicializacion(check(Path(otro.name))), [])


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

    # ── popup o redirección: la página puente solo es obligatoria con loginPopup ──
    def _app_sin_puente(self, codigo_login: str, nombre: str = "src/auth/AuthGate.jsx") -> Path:
        """Un desarrollo con MSAL 5 y `redirectUri` en la raíz, SIN página puente (como Portal SAC), cuyo login usa `codigo_login`."""
        (self.dir / "src" / "auth").mkdir(parents=True)
        (self.dir / "package.json").write_text(json.dumps(PAQUETE_MSAL5), encoding="utf-8")
        (self.dir / "src" / "config").mkdir(parents=True)
        (self.dir / "src" / "config" / "msal.js").write_text(
            'import { PublicClientApplication } from "@azure/msal-browser";\nexport const msalConfig = { auth: { clientId: "x", authority: "a", redirectUri: window.location.origin } };\n',
            encoding="utf-8")
        (self.dir / nombre).write_text(codigo_login, encoding="utf-8")
        (self.dir / ".agp").mkdir()
        (self.dir / ".agp" / "entra.yaml").write_text("redirectUriPath: /\n", encoding="utf-8")
        return self.dir

    def test_flujo_por_redireccion_no_exige_la_pagina_puente(self):
        self._app_sin_puente("await msalInstance.handleRedirectPromise();\nmsalInstance.loginRedirect({ scopes });\nmsalInstance.logoutRedirect();\n")
        r = check(self.dir)
        self.assertTrue(r["valid"], r["issues"])
        self.assertEqual(r["frontends"][0]["flujo"], "redirect")
        self.assertTrue(any("flujo por REDIRECCIÓN" in a and "loginPopup" in a for a in r["avisos"]), r["avisos"])

    def test_flujo_por_popup_exige_la_pagina_puente(self):
        self._app_sin_puente("const r = await msal.loginPopup(loginRequest);\n")
        r = check(self.dir)
        self.assertFalse(r["valid"])
        self.assertEqual(r["frontends"][0]["flujo"], "popup")
        self.assertTrue(any("redirectUri apunta a la raíz" in i for i in r["issues"]))

    def test_popup_y_redireccion_a_la_vez_se_trata_como_popup(self):
        self._app_sin_puente("msal.loginRedirect({ scopes });\nconst r = await msal.acquireTokenPopup(req);\n")
        self.assertFalse(check(self.dir)["valid"])

    def test_sin_ninguna_llamada_de_login_se_trata_como_popup(self):
        self._app_sin_puente("export const nada = 1;\n")
        r = check(self.dir)
        self.assertFalse(r["valid"])
        self.assertEqual(r["frontends"][0]["flujo"], "desconocido")

    def test_las_pruebas_no_cuentan_para_detectar_el_flujo(self):
        self._app_sin_puente("msal.loginRedirect({ scopes });\n")
        (self.dir / "src" / "auth" / "AuthGate.test.jsx").write_text("expect(msal.loginPopup).toHaveBeenCalled();\n", encoding="utf-8")
        self.assertEqual(check(self.dir)["frontends"][0]["flujo"], "redirect")

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
