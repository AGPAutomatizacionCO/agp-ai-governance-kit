"""El retorno del login con MSAL 5: la plantilla `templates/auth-estandar` trae la página puente y todo lo que debe coincidir con ella.

Con @azure/msal-browser 5.x el popup vuelve a `redirectUri`; si es la raíz de la aplicación, el popup recarga la pantalla de login y el acceso nunca se completa
(«Error al iniciar sesión. Intenta de nuevo.»). Estas pruebas no necesitan red ni Node: comprueban los archivos de la plantilla y la ruta del servidor.
"""
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parents[1]
PAQUETE = ROOT / "templates" / "auth-estandar"
RUTA = "/auth/redirect"


def _leer(ruta):
    return (PAQUETE / ruta).read_text(encoding="utf-8")


class PaginaPuenteTests(unittest.TestCase):
    def test_msal_js_vuelve_a_la_pagina_puente_en_login_y_logout(self):
        texto = _leer("src/config/msal.js")
        self.assertIn(f'RUTA_RETORNO_MSAL = "{RUTA}"', texto)
        self.assertIn("redirectUri: `${window.location.origin}${RUTA_RETORNO_MSAL}`", texto)
        self.assertIn("postLogoutRedirectUri: `${window.location.origin}${RUTA_RETORNO_MSAL}`", texto)
        self.assertNotIn("redirectUri: window.location.origin", texto)

    def test_entra_yaml_registra_la_misma_ruta_que_usa_el_codigo(self):
        entra = yaml.safe_load(_leer(".agp/entra.yaml"))
        self.assertEqual(entra["redirectUriPath"], RUTA)

    def test_la_pagina_puente_no_monta_la_aplicacion(self):
        html = _leer("auth/redirect.html")
        self.assertIn('id="auth-status"', html)
        self.assertNotIn('id="root"', html)
        self.assertIn('src="/src/auth/redirect.js"', html)

    def test_el_script_puente_llama_a_la_entrega_de_msal_5(self):
        js = _leer("src/auth/redirect.js")
        self.assertIn('from "@azure/msal-browser/redirect-bridge"', js)
        self.assertIn("broadcastResponseToMainFrame()", js)
        self.assertNotIn("react", js.lower())

    def test_el_ejemplo_de_vite_compila_las_dos_paginas(self):
        vite = _leer("vite.config.example.js")
        self.assertIn('resolve(__dirname, "auth/redirect.html")', vite)
        self.assertIn("/auth/redirect.html", vite)     # reescritura en desarrollo y en preview
        # con llaves: si `use()` se devuelve, Vite lo toma por un hook posterior y el servidor de desarrollo no arranca
        self.assertIn("configureServer(servidor) { servidor.middlewares.use(", vite)
        self.assertIn("configurePreviewServer(servidor) { servidor.middlewares.use(", vite)

    def test_los_mensajes_de_login_cubren_los_errores_del_popup(self):
        texto = _leer("src/contexts/AuthContext.jsx")
        for codigo in ("interaction_in_progress", "monitor_popup_timeout", "hash_empty_error", "popup_window_error", "user_cancelled"):
            self.assertIn(codigo, texto)
        self.assertIn("loginEnCurso", texto)    # un solo popup por clic


@unittest.skipUnless(importlib.util.find_spec("flask"), "Flask no está instalado en este entorno")
class RutaDelServidorTests(unittest.TestCase):
    def setUp(self):
        from flask import Flask

        spec = importlib.util.spec_from_file_location("bp_retorno_msal_plantilla", PAQUETE / "backend" / "src" / "flask_config" / "bp_retorno_msal.py")
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dist = Path(self.tmp.name)
        (self.dist / "index.html").write_text('<div id="root"></div>', encoding="utf-8")
        parche = mock.patch.dict(os.environ, {"FRONTEND_DIST": str(self.dist)})
        parche.start()
        self.addCleanup(parche.stop)
        app = Flask(__name__)
        app.register_blueprint(modulo.bp_retorno_msal)
        self.cliente = app.test_client()

    def test_sirve_la_pagina_puente_real_sin_cache_ni_coop(self):
        (self.dist / "auth").mkdir()
        (self.dist / "auth" / "redirect.html").write_text(_leer("auth/redirect.html"), encoding="utf-8")
        r = self.cliente.get(RUTA)
        self.assertEqual(r.status_code, 200)
        self.assertIn("text/html", r.headers["Content-Type"])
        self.assertIn(b'id="auth-status"', r.data)
        self.assertNotIn(b'id="root"', r.data)
        self.assertEqual(r.headers["Cache-Control"], "no-store")
        self.assertIsNone(r.headers.get("Cross-Origin-Opener-Policy"))

    def test_si_falta_la_pagina_responde_404_y_nunca_index_html(self):
        r = self.cliente.get(RUTA)
        self.assertEqual(r.status_code, 404)
        self.assertNotIn(b'id="root"', r.data)


class NormaDocumentadaTests(unittest.TestCase):
    def test_la_regla_esta_en_la_norma_y_en_las_guias(self):
        for archivo in ("OBLIGATORIOS-DEL-DESARROLLO.md", "COMO-DEJARLO-FUNCIONAL.md", "agent-despliegue.md",
                        "prompt-agente-despliegue-evaluacion.md", "templates/auth-estandar/README.md"):
            texto = (ROOT / archivo).read_text(encoding="utf-8")
            self.assertIn(RUTA, texto, archivo)
        obligatorios = (ROOT / "OBLIGATORIOS-DEL-DESARROLLO.md").read_text(encoding="utf-8")
        self.assertIn("Error al iniciar sesión. Intenta de nuevo.", obligatorios)   # el error que produce y cómo se ve
        self.assertIn("redirectUriPath: /auth/redirect", obligatorios)
        self.assertIn("broadcastResponseToMainFrame", obligatorios)


if __name__ == "__main__":
    unittest.main()
