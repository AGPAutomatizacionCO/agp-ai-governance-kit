"""Nomenclatura de datos (NOMENCLATURA-DATOS.md): el esquema solo exige nombres y tipos cuando la tabla se crea en el despliegue."""
import copy
import json
import unittest
from pathlib import Path

import jsonschema

KIT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((KIT / "schemas" / "data-access-manifest.schema.json").read_text(encoding="utf-8"))
EXISTENTE = json.loads((KIT / "templates" / "data-access-manifest.example.json").read_text(encoding="utf-8"))
CREAR = json.loads((KIT / "templates" / "data-access-manifest.crear-tablas.example.json").read_text(encoding="utf-8"))


def _errores(manifiesto):
    return list(jsonschema.Draft202012Validator(SCHEMA).iter_errors(manifiesto))


def _tabla(manifiesto, indice=0):
    return manifiesto["fuentes_datos"][0]["esquemas"][0]["tablas"][indice]


class NomenclaturaDatosTests(unittest.TestCase):
    def test_el_meta_esquema_es_valido(self):
        jsonschema.Draft202012Validator.check_schema(SCHEMA)

    def test_los_manifiestos_existentes_siguen_siendo_validos(self):
        # Retrocompatibilidad: la Mesa descarga este esquema de main; un manifiesto sin crear_en_despliegue no se exige nombrado ni tipos.
        self.assertEqual([], _errores(EXISTENTE))
        sin_tipos = copy.deepcopy(EXISTENTE)
        _tabla(sin_tipos)["table"] = "users"
        self.assertEqual([], _errores(sin_tipos))

    def test_el_ejemplo_de_tablas_a_crear_es_valido(self):
        self.assertEqual([], _errores(CREAR))

    def test_una_tabla_a_crear_exige_el_prefijo_del_desarrollo(self):
        for nombre in ("users", "app_Manufacturing_RPC_users", "App_Manufacturing_users", "App_Manufacturing_RPC_", "App_Manufacturing-RPC_users", "App_Manufacturing_RPC_1x"):
            malo = copy.deepcopy(CREAR)
            _tabla(malo)["table"] = nombre
            self.assertNotEqual([], _errores(malo), nombre)

    def test_el_esquema_debe_ser_propio_del_desarrollo(self):
        for nombre in ("dbo", "App_Manufacturing_RPC", "app_manufacturing", "app_manufacturing_rpc_x", "sys"):
            malo = copy.deepcopy(CREAR)
            malo["fuentes_datos"][0]["esquemas"][0]["schema"] = nombre
            self.assertNotEqual([], _errores(malo), nombre)

    def test_cada_columna_de_una_tabla_a_crear_lleva_tipo(self):
        malo = copy.deepcopy(CREAR)
        del _tabla(malo)["columnas"][1]["tipo"]
        self.assertNotEqual([], _errores(malo))

    def test_solo_tipos_de_la_lista_cerrada(self):
        for tipo in ("text", "nvarchar(5000)", "money", "int identity", "nvarchar", "xml", "decimal(40,2)"):
            malo = copy.deepcopy(CREAR)
            _tabla(malo)["columnas"][1]["tipo"] = tipo
            self.assertNotEqual([], _errores(malo), tipo)
        for tipo in ("int", "bigint", "bit", "datetime2", "uniqueidentifier", "nvarchar(max)", "nvarchar(4000)", "varchar(8000)",
                     "decimal(18,2)", "varbinary(max)"):
            bueno = copy.deepcopy(CREAR)
            _tabla(bueno)["columnas"][1]["tipo"] = tipo
            self.assertEqual([], _errores(bueno), tipo)

    def test_una_tabla_a_crear_no_puede_ser_preexistente(self):
        malo = copy.deepcopy(CREAR)
        _tabla(malo)["origen"] = "preexistente"
        self.assertNotEqual([], _errores(malo))

    def test_la_referencia_apunta_a_una_tabla_propia_con_formato_tabla_columna(self):
        for ref in ("solicitudes.id", "dbo.clientes.id", "App_Manufacturing_GestorSolicitudes_solicitudes"):
            malo = copy.deepcopy(CREAR)
            _tabla(malo, 1)["columnas"][1]["referencia"] = ref
            self.assertNotEqual([], _errores(malo), ref)

    def test_crear_en_despliegue_false_equivale_a_solo_describir(self):
        descrito = copy.deepcopy(CREAR)
        for tabla in descrito["fuentes_datos"][0]["esquemas"][0]["tablas"]:
            tabla["crear_en_despliegue"] = False
            tabla["table"] = tabla["table"].replace("App_Manufacturing_GestorSolicitudes_", "")
        descrito["fuentes_datos"][0]["esquemas"][0]["schema"] = "dbo"
        for tabla in descrito["fuentes_datos"][0]["esquemas"][0]["tablas"]:
            for columna in tabla["columnas"]:
                columna.pop("tipo", None)
                columna.pop("referencia", None)
        self.assertEqual([], _errores(descrito))


if __name__ == "__main__":
    unittest.main()


class AutoincrementalTests(unittest.TestCase):
    def test_el_ejemplo_declara_identidad_y_sigue_siendo_valido(self):
        self.assertTrue(_tabla(CREAR)["columnas"][0]["autoincremental"])
        self.assertEqual([], _errores(CREAR))

    def test_autoincremental_debe_ser_booleano(self):
        malo = copy.deepcopy(CREAR)
        _tabla(malo)["columnas"][0]["autoincremental"] = "si"
        self.assertNotEqual([], _errores(malo))
