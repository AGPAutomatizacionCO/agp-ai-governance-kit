"""El helper de backend de la plantilla que lee el rol por el túnel de la Mesa (`GET /api/roles-app/<id>/mios`)."""
import importlib.util
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
_ruta = ROOT / "templates" / "auth-estandar" / "backend" / "src" / "helpers" / "roles_mesa.py"
_spec = importlib.util.spec_from_file_location("roles_mesa_plantilla", _ruta)
rm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rm)

ENTORNO = {"ROLES_DESDE_MESA": "true", "MESA_API_URL": "https://mesa.ejemplo.agpglass.com/", "MESA_ID_PROYECTO": "id-ejemplo"}


class Respuesta:
    def __init__(self, codigo=200, cuerpo=None, json_invalido=False):
        self.status_code, self._cuerpo, self._invalido = codigo, cuerpo, json_invalido

    def json(self):
        if self._invalido:
            raise ValueError("no es JSON")
        return self._cuerpo


def mios(nivel="usuario", perfil=None, modulos=(), funciones=()):
    datos = {"correo": "persona@agpglass.com", "nivel": nivel, "adminGlobal": nivel == "global", "permisos": {"modulos": list(modulos), "funciones": list(funciones)}}
    datos["perfil"] = perfil
    return {"data": datos}


class RolesMesaTests(unittest.TestCase):
    def setUp(self):
        rm.olvidar()
        parche = mock.patch.dict("os.environ", ENTORNO, clear=True)
        parche.start()
        self.addCleanup(parche.stop)
        self.addCleanup(rm.olvidar)

    # ── activo ──
    def test_activo_exige_las_tres_variables_y_https(self):
        self.assertTrue(rm.activo())
        for quitar in ("ROLES_DESDE_MESA", "MESA_API_URL", "MESA_ID_PROYECTO"):
            entorno = {k: v for k, v in ENTORNO.items() if k != quitar}
            with mock.patch.dict("os.environ", entorno, clear=True):
                self.assertFalse(rm.activo(), quitar)
        with mock.patch.dict("os.environ", {**ENTORNO, "MESA_API_URL": "http://127.0.0.1:5000"}, clear=True):
            self.assertFalse(rm.activo())
        with mock.patch.dict("os.environ", {**ENTORNO, "ROLES_DESDE_MESA": "false"}, clear=True):
            self.assertFalse(rm.activo())

    # ── traducción de lo que responde la Mesa ──
    def test_administrador_principal_y_secundario(self):
        self.assertEqual("global", rm.alcance_desde_respuesta(mios("global")["data"]).nivel)
        self.assertEqual("admin", rm.alcance_desde_respuesta(mios("admin")["data"]).nivel)
        self.assertTrue(rm.alcance_desde_respuesta(mios("admin")["data"]).administra)

    def test_usuario_con_rol_trae_sus_vistas_y_acciones(self):
        datos = mios("usuario", {"id": "logistica", "nombre": "Logística", "general": False}, ["estado-pedidos"], ["estado-pedidos.exportar"])["data"]
        a = rm.alcance_desde_respuesta(datos)
        self.assertEqual("usuario", a.nivel)
        self.assertEqual("logistica", a.perfil)
        self.assertIn("estado-pedidos", a.modulos)
        self.assertIn("estado-pedidos.exportar", a.funciones)
        self.assertFalse(a.administra)

    def test_sin_rol_o_con_vista_general_es_general(self):
        self.assertEqual("general", rm.alcance_desde_respuesta(mios("usuario", None)["data"]).nivel)
        self.assertEqual("general", rm.alcance_desde_respuesta(mios("usuario", {"id": "general", "general": True})["data"]).nivel)

    def test_respuesta_con_formas_raras_no_revienta(self):
        a = rm.alcance_desde_respuesta({"perfil": "texto", "permisos": [1, 2]})
        self.assertEqual("general", a.nivel)
        self.assertEqual(frozenset(), a.modulos)

    # ── resolver: Mesa, caché y falla cerrada ──
    def test_pregunta_a_la_mesa_con_el_id_token_y_reutiliza_la_cache(self):
        llamadas = []

        def http(url, cabeceras, timeout):
            llamadas.append((url, cabeceras, timeout))
            return Respuesta(200, mios("global"))

        self.assertEqual("global", rm.resolver("Persona@AGPGlass.com", "TOKEN", http_get=http).nivel)
        self.assertEqual("global", rm.resolver("persona@agpglass.com", "TOKEN", http_get=http).nivel)
        self.assertEqual(1, len(llamadas))
        url, cabeceras, timeout = llamadas[0]
        self.assertEqual("https://mesa.ejemplo.agpglass.com/api/roles-app/id-ejemplo/mios", url)
        self.assertEqual({"Authorization": "Bearer TOKEN"}, cabeceras)
        self.assertEqual(rm.TIMEOUT_S, timeout)

    def test_vuelve_a_preguntar_pasado_el_ttl(self):
        llamadas = []

        def http(*_):
            llamadas.append(1)
            return Respuesta(200, mios("usuario", {"id": "x"}))

        rm.resolver("p@agpglass.com", "T", ahora=lambda: 1000, http_get=http)
        rm.resolver("p@agpglass.com", "T", ahora=lambda: 1000 + rm.TTL_S + 1, http_get=http)
        self.assertEqual(2, len(llamadas))

    def test_la_mesa_caida_sin_nada_guardado_da_la_vista_general(self):
        for http in (lambda *_: Respuesta(500, {"message": "error"}), lambda *_: Respuesta(200, json_invalido=True),
                     lambda *_: Respuesta(200, {"data": None}), mock.Mock(side_effect=OSError("sin red"))):
            rm.olvidar()
            a = rm.resolver("p@agpglass.com", "T", http_get=http)
            self.assertEqual("general", a.nivel)
            self.assertFalse(a.de_la_mesa)

    def test_la_mesa_caida_respeta_el_admin_del_token_de_microsoft(self):
        a = rm.resolver("p@agpglass.com", "T", roles_entra=["Admin"], http_get=lambda *_: Respuesta(503, {}))
        self.assertEqual("global", a.nivel)
        self.assertFalse(a.de_la_mesa)
        self.assertEqual("general", rm.resolver("q@agpglass.com", "T", roles_entra=["Usuario"], http_get=lambda *_: Respuesta(503, {})).nivel)

    def test_la_mesa_caida_reutiliza_lo_ultimo_que_dijo_pero_no_mas_que_una_sesion(self):
        rm.resolver("p@agpglass.com", "T", ahora=lambda: 1000, http_get=lambda *_: Respuesta(200, mios("global")))
        caida = lambda *_: Respuesta(502, {})
        self.assertEqual("global", rm.resolver("p@agpglass.com", "T", ahora=lambda: 1000 + rm.TTL_S + 5, http_get=caida).nivel)
        self.assertEqual("general", rm.resolver("p@agpglass.com", "T", ahora=lambda: 1000 + rm.MAX_VIGENCIA_S + 5, http_get=caida).nivel)

    def test_sin_token_usa_lo_guardado_o_el_respaldo(self):
        self.assertEqual("general", rm.resolver("p@agpglass.com", None).nivel)
        rm.resolver("p@agpglass.com", "T", ahora=lambda: 1000, http_get=lambda *_: Respuesta(200, mios("admin")))
        self.assertEqual("admin", rm.resolver("p@agpglass.com", None, ahora=lambda: 1000 + 3600).nivel)

    def test_olvidar_una_persona_o_todas(self):
        http = lambda *_: Respuesta(200, mios("global"))
        rm.resolver("a@agpglass.com", "T", http_get=http)
        rm.resolver("b@agpglass.com", "T", http_get=http)
        rm.olvidar("a@agpglass.com")
        self.assertEqual("general", rm.resolver("a@agpglass.com", None).nivel)
        self.assertEqual("global", rm.resolver("b@agpglass.com", None).nivel)
        rm.olvidar()
        self.assertEqual("general", rm.resolver("b@agpglass.com", None).nivel)

    # ── local ──
    def test_sin_la_mesa_activa_en_local_manda_roles_local_nivel(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            self.assertEqual("general", rm.resolver("p@agpglass.com", "T").nivel)
        for pedido, esperado in (("admin", "global"), ("usuario", "usuario"), ("general", "general"), ("raro", "general")):
            with mock.patch.dict("os.environ", {"ROLES_LOCAL_NIVEL": pedido}, clear=True):
                a = rm.resolver("p@agpglass.com", "T")
                self.assertEqual(esperado, a.nivel, pedido)
                self.assertFalse(a.de_la_mesa)

    def test_en_azure_roles_local_nivel_se_ignora(self):
        with mock.patch.dict("os.environ", {"ROLES_LOCAL_NIVEL": "admin", "WEBSITE_SITE_NAME": "mi-app"}, clear=True):
            self.assertEqual("general", rm.resolver("p@agpglass.com", "T").nivel)


if __name__ == "__main__":
    unittest.main()
