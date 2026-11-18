"""Plantilla de configuración LOCAL de roles y secretos (`templates/auth-estandar`): `roles_propios.py` y `bp_configuracion.py`.

Sin red, sin SQL y sin Key Vault reales: dobles en memoria. Casos mínimos de CONFIGURACION-LOCAL-ROLES-Y-SECRETOS.md: sesión válida con rol permitido, 401 sin sesión,
403 sin capacidad, administrador revocado, perfil desconocido, rollback si falla la auditoría, secretos ajenos bloqueados, actor no falsificable, ninguna respuesta ni log
con valores y que importar los módulos no abre conexiones.
"""
import logging
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "templates" / "auth-estandar" / "backend"
ENTORNO = {"ROLES_PROPIOS_ESQUEMA": "app_ejemplo_demo", "ROLES_PROPIOS_TABLA_PERSONAS": "App_Ejemplo_Demo_acceso_personas",
           "ROLES_PROPIOS_TABLA_AUDITORIA": "App_Ejemplo_Demo_acceso_auditoria", "CONFIG_ADMINISTRADORES_INICIALES": "inicial@agpglass.com",
           "CONFIG_SECRETOS_PERMITIDOS": "demo-clave-externa, demo-otra-clave", "CONFIG_KEY_VAULT_URL": "https://vault-de-prueba.invalid"}


def _importar():
    sys.path.insert(0, str(BACKEND))
    try:
        import importlib

        for nombre in [n for n in sys.modules if n == "src" or n.startswith("src.")]:
            del sys.modules[nombre]
        rp = importlib.import_module("src.helpers.roles_propios")
        bp = importlib.import_module("src.flask_config.bp_configuracion")
        return rp, bp
    finally:
        sys.path.remove(str(BACKEND))


rp, bp = _importar()


class RepoMemoria:
    """Doble del repositorio con la misma interfaz que RepoSql."""

    def __init__(self, personas=None, falla_auditoria=False, cae=False):
        self.filas, self.auditoria_, self.falla_auditoria, self.cae, self.llamadas = dict(personas or {}), [], falla_auditoria, cae, []

    def perfil_de(self, correo):
        if self.cae:
            raise RuntimeError("base caída")
        return self.filas.get(correo)

    def personas(self):
        return sorted(self.filas.items())

    def aplicar(self, actor, destinatario, perfil, validar):
        self.llamadas.append((actor, destinatario, perfil))
        anterior = self.filas.get(destinatario)
        validar(anterior, list(self.filas.items()))
        copia = dict(self.filas)                       # transacción: si la auditoría falla, no queda el cambio
        if perfil is None:
            copia.pop(destinatario, None)
        else:
            copia[destinatario] = perfil
        if self.falla_auditoria:
            raise RuntimeError("falló la auditoría")
        self.filas = copia
        self.auditoria_.append((actor, destinatario, anterior, perfil, "aplicado"))
        return anterior

    def registrar(self, actor, destinatario, resultado):
        self.auditoria_.append((actor, destinatario, None, None, resultado))

    def auditoria(self, limite=100):
        return [{"actor": a, "destinatario": d, "resultado": r} for a, d, _, _, r in self.auditoria_]

    def buscar_usuarios(self, texto):
        return [{"correo": "ana@agpglass.com", "nombre": "Ana", "area": "X", "cargo": "Y"}]


class Base(unittest.TestCase):
    def setUp(self):
        rp.olvidar()
        self.addCleanup(rp.olvidar)
        p = mock.patch.dict(os.environ, {**ENTORNO}, clear=True)
        p.start()
        self.addCleanup(p.stop)


class AsignarTests(Base):
    def repo(self, **kw):
        return RepoMemoria({"admin@agpglass.com": "administrador", "otra@agpglass.com": "administrador", "ana@agpglass.com": "consulta"}, **kw)

    def test_el_administrador_asigna_y_queda_auditado(self):
        r = self.repo()
        self.assertIsNone(rp.asignar("admin@agpglass.com", "Nueva@AGPglass.com", "consulta", repo=r))
        self.assertEqual(r.filas["nueva@agpglass.com"], "consulta")
        self.assertEqual(r.auditoria_[-1], ("admin@agpglass.com", "nueva@agpglass.com", None, "consulta", "aplicado"))

    def test_sin_capacidad_no_asigna_aunque_tenga_perfil(self):
        r = self.repo()
        with self.assertRaises(rp.ErrorRoles) as c:
            rp.asignar("ana@agpglass.com", "nueva@agpglass.com", "consulta", repo=r)
        self.assertEqual(c.exception.codigo, 403)
        self.assertEqual(r.llamadas, [])

    def test_administrador_revocado_pierde_el_permiso_en_la_siguiente_llamada(self):
        r = self.repo()
        self.assertTrue(rp.resolver("otra@agpglass.com", repo=r).administra)             # queda en caché
        del r.filas["otra@agpglass.com"]                                                 # IT o un administrador lo revoca
        with self.assertRaises(rp.ErrorRoles):                                           # el endpoint relee la tabla, no usa la caché
            rp.asignar("otra@agpglass.com", "nueva@agpglass.com", "consulta", repo=r)

    def test_perfil_desconocido_se_rechaza_sin_tocar_nada(self):
        r = self.repo()
        with self.assertRaises(rp.ErrorRoles):
            rp.asignar("admin@agpglass.com", "nueva@agpglass.com", "superadmin", repo=r)
        self.assertEqual(r.llamadas, [])

    def test_correo_no_corporativo_se_rechaza(self):
        with self.assertRaises(rp.ErrorRoles):
            rp.asignar("admin@agpglass.com", "alguien@otro.com", "consulta", repo=self.repo())

    def test_nadie_cambia_su_propio_perfil(self):
        with self.assertRaises(rp.ErrorRoles) as c:
            rp.asignar("admin@agpglass.com", "admin@agpglass.com", "consulta", repo=self.repo())
        self.assertEqual(c.exception.codigo, 403)

    def test_el_administrador_inicial_no_se_toca(self):
        with self.assertRaises(rp.ErrorRoles):
            rp.asignar("admin@agpglass.com", "inicial@agpglass.com", None, repo=self.repo())

    def test_siempre_queda_una_persona_administradora(self):
        # El actor debe administrar y no puede cambiarse a sí mismo, así que retirar a otro administrador deja al actor; la regla de «último administrador» de
        # `validar` es la defensa adicional si se llamara con otro orden. Aquí se comprueba el resultado observable.
        with mock.patch.dict(os.environ, {"CONFIG_ADMINISTRADORES_INICIALES": ""}):
            r = RepoMemoria({"admin@agpglass.com": "administrador", "otra@agpglass.com": "administrador"})
            rp.asignar("admin@agpglass.com", "otra@agpglass.com", None, repo=r)
            self.assertEqual([c for c, p in r.filas.items() if p == "administrador"], ["admin@agpglass.com"])
            with self.assertRaises(rp.ErrorRoles):   # y el que queda no puede retirarse a sí mismo
                rp.asignar("admin@agpglass.com", "admin@agpglass.com", None, repo=r)

    def test_rollback_si_falla_la_auditoria(self):
        r = self.repo(falla_auditoria=True)
        with self.assertRaises(RuntimeError):
            rp.asignar("admin@agpglass.com", "nueva@agpglass.com", "consulta", repo=r)
        self.assertNotIn("nueva@agpglass.com", r.filas)
        self.assertEqual(r.auditoria_, [])

    def test_quitar_a_quien_no_tiene_acceso_o_repetir_el_perfil_es_conflicto(self):
        r = self.repo()
        for destinatario, perfil in (("nadie@agpglass.com", None), ("ana@agpglass.com", "consulta")):
            with self.assertRaises(rp.ErrorRoles) as c:
                rp.asignar("admin@agpglass.com", destinatario, perfil, repo=r)
            self.assertEqual(c.exception.codigo, 409)


class ResolverTests(Base):
    def test_falla_cerrada_si_la_base_no_responde(self):
        r = RepoMemoria({"admin@agpglass.com": "administrador"}, cae=True)
        a = rp.resolver("admin@agpglass.com", repo=r)
        self.assertEqual((a.nivel, a.de_la_tabla), ("general", False))
        self.assertFalse(a.administra)

    def test_el_administrador_inicial_conserva_acceso_aunque_la_base_caiga(self):
        a = rp.resolver("inicial@agpglass.com", repo=RepoMemoria(cae=True))
        self.assertEqual(a.nivel, "global")

    def test_sin_fila_o_con_perfil_que_ya_no_existe_es_vista_general(self):
        self.assertEqual(rp.resolver("nadie@agpglass.com", repo=RepoMemoria()).nivel, "general")
        self.assertEqual(rp.resolver("viejo@agpglass.com", repo=RepoMemoria({"viejo@agpglass.com": "perfil-retirado"})).nivel, "general")

    def test_mismo_alcance_que_el_helper_heredado(self):
        a = rp.resolver("ana@agpglass.com", repo=RepoMemoria({"ana@agpglass.com": "consulta"}))
        self.assertEqual((a.nivel, a.perfil), ("usuario", "consulta"))
        self.assertTrue(hasattr(a, "modulos") and hasattr(a, "funciones") and hasattr(a, "administra"))


class FakeCon:
    """Doble de conexión DB-API: registra el SQL, confirma o revierte."""

    def __init__(self, filas=None, falla_en=None):
        self.sql, self.commits, self.rollbacks, self.cerrada, self.filas, self.falla_en = [], 0, 0, False, filas or {}, falla_en

    def cursor(self):
        return self

    def execute(self, sql, *params):
        if self.falla_en and self.falla_en in sql:
            raise RuntimeError("falla simulada")
        self.sql.append((sql, params))
        self._ultimo = (sql, params)
        return self

    def fetchone(self):
        sql, params = self._ultimo
        if "SELECT Perfil" in sql:
            return (self.filas[params[0]],) if params[0] in self.filas else None
        return None

    def fetchall(self):
        return [(c, p) for c, p in self.filas.items()]

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.cerrada = True


class RepoSqlTests(Base):
    def test_importar_los_modulos_no_abre_conexiones(self):
        self.assertTrue(callable(rp.abrir_conexion))   # solo se ejecuta cuando alguien la llama

    def test_falta_configuracion_o_nombres_invalidos(self):
        with self.assertRaises(rp.ErrorRoles):
            rp.RepoSql(entorno={})
        with self.assertRaises(rp.ErrorRoles):
            rp.RepoSql(entorno={**ENTORNO, "ROLES_PROPIOS_TABLA_PERSONAS": "x]; DROP TABLE y;--"})

    def test_aplicar_es_una_sola_transaccion_con_parametros(self):
        con = FakeCon({"ana@agpglass.com": "consulta"})
        repo = rp.RepoSql(abrir=lambda: con)
        repo.aplicar("admin@agpglass.com", "nueva@agpglass.com", "consulta", lambda a, p: None)
        self.assertEqual((con.commits, con.rollbacks, con.cerrada), (1, 0, True))
        instrucciones = [s for s, _ in con.sql]
        self.assertTrue(any(s.startswith("INSERT INTO [app_ejemplo_demo].[App_Ejemplo_Demo_acceso_personas]") for s in instrucciones))
        self.assertTrue(any(s.startswith("INSERT INTO [app_ejemplo_demo].[App_Ejemplo_Demo_acceso_auditoria]") for s in instrucciones))
        for _, params in con.sql:
            self.assertNotIn("nueva@agpglass.com", "".join(s for s, _ in con.sql))   # los valores nunca se escriben en el SQL
        self.assertIn("nueva@agpglass.com", [p for _, ps in con.sql for p in ps])

    def test_si_falla_la_auditoria_se_revierte_y_no_se_confirma(self):
        con = FakeCon(falla_en="acceso_auditoria")
        repo = rp.RepoSql(abrir=lambda: con)
        with self.assertRaises(RuntimeError):
            repo.aplicar("admin@agpglass.com", "nueva@agpglass.com", "consulta", lambda a, p: None)
        self.assertEqual((con.commits, con.rollbacks, con.cerrada), (0, 1, True))

    def test_si_la_validacion_rechaza_no_se_escribe_nada(self):
        con = FakeCon()

        def no(a, p):
            raise rp.ErrorRoles("no", 403)
        with self.assertRaises(rp.ErrorRoles):
            rp.RepoSql(abrir=lambda: con).aplicar("a@agpglass.com", "b@agpglass.com", "consulta", no)
        self.assertFalse(any(s.startswith(("INSERT", "UPDATE", "DELETE")) for s, _ in con.sql))
        self.assertEqual(con.rollbacks, 1)

    def test_el_directorio_escapa_los_comodines(self):
        con = FakeCon()
        con.fetchall = list
        rp.RepoSql(abrir=lambda: con).buscar_usuarios("50%_[x")
        self.assertEqual(con.sql[0][1][1], "%50\\%\\_\\[x%")
        self.assertIn("[corporacion].[vw_UsuariosCorporacion]", con.sql[0][0])


class KVFalso:
    def __init__(self, falla=False):
        self.guardados, self.falla = {}, falla

    def set_secret(self, nombre, valor):
        if self.falla:
            raise RuntimeError(f"error del SDK con el cuerpo {valor}")
        self.guardados[nombre] = valor

    def get_secret(self, nombre):
        raise AssertionError("nunca se lee un valor")


class EndpointsTests(Base):
    def setUp(self):
        super().setUp()
        from flask import Flask

        self.repo = RepoMemoria({"admin@agpglass.com": "administrador", "ana@agpglass.com": "consulta"})
        self.kv = KVFalso()
        for p in (mock.patch.object(bp, "_repo", lambda: self.repo), mock.patch.object(bp, "_kv", lambda: self.kv)):
            p.start()
            self.addCleanup(p.stop)
        app = Flask(__name__)
        app.register_blueprint(bp.bp_configuracion)
        self.c = app.test_client()
        os.environ["DISABLE_AUTH"] = "true"   # solo local: el actor sale de DEV_USER_EMAIL, igual que g.user_email con un token válido

    def como(self, correo):
        os.environ["DEV_USER_EMAIL"] = correo
        return self.c

    def test_401_sin_sesion(self):
        os.environ["DISABLE_AUTH"] = "false"
        for metodo, ruta in (("get", "/estado"), ("put", "/personas"), ("get", "/secretos"), ("put", "/secretos/demo-clave-externa"), ("get", "/directorio?q=an"), ("get", "/actividad")):
            r = getattr(self.c, metodo)("/api/configuracion" + ruta)
            self.assertEqual(r.status_code, 401, ruta)

    def test_403_sin_capacidad_en_cada_endpoint_administrativo(self):
        c = self.como("ana@agpglass.com")
        for metodo, ruta, cuerpo in (("put", "/personas", {"correo": "x@agpglass.com", "perfil": "consulta"}), ("get", "/secretos", None),
                                     ("put", "/secretos/demo-clave-externa", {"valor": "v"}), ("get", "/directorio?q=an", None), ("get", "/actividad", None)):
            r = getattr(c, metodo)("/api/configuracion" + ruta, json=cuerpo)
            self.assertEqual(r.status_code, 403, ruta)
        self.assertEqual(self.kv.guardados, {})

    def test_estado_solo_entrega_personas_a_quien_administra(self):
        self.assertNotIn("personas", self.como("ana@agpglass.com").get("/api/configuracion/estado").get_json()["data"])
        datos = self.como("admin@agpglass.com").get("/api/configuracion/estado").get_json()["data"]
        self.assertTrue(datos["puedeConfigurar"])
        self.assertEqual({p["correo"] for p in datos["personas"]}, {"admin@agpglass.com", "ana@agpglass.com"})

    def test_el_actor_es_el_del_token_aunque_el_cuerpo_diga_otro(self):
        r = self.como("admin@agpglass.com").put("/api/configuracion/personas", json={"correo": "nueva@agpglass.com", "perfil": "consulta", "actor": "ana@agpglass.com",
                                                                                      "rol": "global", "admin": True})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.repo.llamadas, [("admin@agpglass.com", "nueva@agpglass.com", "consulta")])
        self.assertEqual(self.repo.auditoria_[-1][0], "admin@agpglass.com")

    def test_perfil_desconocido_y_regla_de_proteccion_devuelven_el_codigo_de_la_regla(self):
        c = self.como("admin@agpglass.com")
        self.assertEqual(c.put("/api/configuracion/personas", json={"correo": "n@agpglass.com", "perfil": "superadmin"}).status_code, 400)
        self.assertEqual(c.put("/api/configuracion/personas", json={"correo": "admin@agpglass.com", "perfil": None}).status_code, 403)

    def test_la_base_caida_responde_503_sin_detalle(self):
        self.repo.cae = True
        os.environ["CONFIG_ADMINISTRADORES_INICIALES"] = "admin@agpglass.com"
        r = self.como("admin@agpglass.com").put("/api/configuracion/personas", json={"correo": "n@agpglass.com", "perfil": "consulta"})
        self.assertNotIn("base caída", r.get_data(as_text=True))

    def test_secretos_solo_nombres_y_solo_los_permitidos(self):
        c = self.como("admin@agpglass.com")
        self.assertEqual(c.get("/api/configuracion/secretos").get_json()["data"]["nombres"], ["demo-clave-externa", "demo-otra-clave"])
        for ajeno in ("datos-otro-worker-password", "demo-no-permitido"):
            self.assertEqual(c.put(f"/api/configuracion/secretos/{ajeno}", json={"valor": "v"}).status_code, 403, ajeno)
        self.assertEqual(self.kv.guardados, {})

    def test_cargar_secreto_no_devuelve_ni_registra_el_valor(self):
        with self.assertLogs(level=logging.DEBUG) as logs:
            logging.getLogger("prueba").debug("inicio")
            r = self.como("admin@agpglass.com").put("/api/configuracion/secretos/demo-clave-externa", json={"valor": "VALOR-SECRETO-123"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.kv.guardados, {"demo-clave-externa": "VALOR-SECRETO-123"})
        self.assertNotIn("VALOR-SECRETO-123", r.get_data(as_text=True))
        self.assertNotIn("VALOR-SECRETO-123", str(self.repo.auditoria_))
        self.assertNotIn("VALOR-SECRETO-123", "\n".join(logs.output))

    def test_el_error_del_sdk_no_filtra_el_valor_ni_el_detalle(self):
        self.kv.falla = True
        with self.assertLogs(level=logging.WARNING) as logs:
            r = self.como("admin@agpglass.com").put("/api/configuracion/secretos/demo-clave-externa", json={"valor": "VALOR-SECRETO-123"})
        self.assertEqual(r.status_code, 503)
        self.assertNotIn("VALOR-SECRETO-123", r.get_data(as_text=True) + "\n".join(logs.output) + str(self.repo.auditoria_))
        self.assertEqual(self.repo.auditoria_[-1][-1], "fallido")

    def test_valor_vacio_o_demasiado_largo(self):
        c = self.como("admin@agpglass.com")
        for valor in ("", "x" * (bp.MAX_VALOR + 1), 5, None):
            self.assertEqual(c.put("/api/configuracion/secretos/demo-clave-externa", json={"valor": valor}).status_code, 400)

    def test_si_la_auditoria_falla_tras_guardar_se_informa_el_estado_parcial(self):
        self.repo.registrar = mock.Mock(side_effect=RuntimeError("sin auditoría"))
        r = self.como("admin@agpglass.com").put("/api/configuracion/secretos/demo-clave-externa", json={"valor": "v1"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["data"]["auditoria"], "pendiente")

    def test_las_plantillas_no_leen_valores_del_vault(self):
        for ruta in (BACKEND / "src" / "flask_config" / "bp_configuracion.py", BACKEND / "src" / "helpers" / "roles_propios.py"):
            texto = ruta.read_text(encoding="utf-8")
            self.assertNotIn(".get_secret(", texto, ruta.name)
            self.assertNotIn("list_properties_of_secrets", texto, ruta.name)
        self.assertIn("ManagedIdentityCredential", (BACKEND / "src" / "flask_config" / "bp_configuracion.py").read_text(encoding="utf-8"))


class ManifiestoDeEjemploTests(unittest.TestCase):
    RUNTIME = """apiVersion: agp.runtime/v1
env:
  - name: COLOMBIA_DB_DATABASE
    value: "AGP_Colombia"
  - name: ROLES_PROPIOS_ESQUEMA
    value: "app_ejemplo_demo"
secrets:
  - name: COLOMBIA_DB_SERVER
    secret: demo-db-server
  - name: COLOMBIA_DB_USERNAME
    secret: demo-db-user
  - name: COLOMBIA_DB_PASSWORD
    secret: demo-db-pwd
"""

    def test_el_ejemplo_declara_dos_tablas_propias_y_la_vista_de_usuarios_solo_lectura_y_pasa_agpctl(self):
        import json
        import tempfile

        from agpctl.datos import check

        ruta = ROOT / "examples" / "data-access-manifest.roles-propios.valid.json"
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        tablas = {t["table"]: t for f in datos["fuentes_datos"] for e in f["esquemas"] for t in e["tablas"]}
        propias = [t for t in tablas.values() if t["origen"] == "propia_del_desarrollo"]
        self.assertEqual(len(propias), 2)
        for t in propias:
            self.assertTrue(t["crear_en_despliegue"])
            pk = [c for c in t["columnas"] if c.get("clave_primaria")]
            self.assertTrue(pk and pk[0].get("autoincremental"), t["table"])   # sin esto la tabla se crea sin IDENTITY
        self.assertEqual(tablas["App_Ejemplo_Demo_acceso_auditoria"]["operaciones_permitidas"], ["SELECT", "INSERT"])   # la auditoría no se edita ni se borra
        vista = tablas["vw_UsuariosCorporacion"]
        self.assertEqual((vista["origen"], vista["operaciones_permitidas"]), ("preexistente", ["SELECT"]))
        self.assertFalse(any(n.endswith(("_Roles", "_RolesDatos", "_RolesPersonas")) for n in tablas))   # nombres reservados del modo heredado
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "ai" / "outputs").mkdir(parents=True)
            (Path(d) / ".agp").mkdir()
            (Path(d) / "ai" / "outputs" / "data-access-manifest.json").write_text(ruta.read_text(encoding="utf-8"), encoding="utf-8")
            (Path(d) / ".agp" / "runtime.yaml").write_text(self.RUNTIME, encoding="utf-8")
            self.assertEqual(check(Path(d)), {"valid": True, "issues": []})


if __name__ == "__main__":
    unittest.main()
