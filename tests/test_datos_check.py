import json

from agpctl.datos import check

ESQUEMA = "app_finance_demo"
TABLA = "App_Finance_Demo_Alarma"


def _manifiesto(tipo="datetime2", defecto="SYSUTCDATETIME()"):
    columna_fecha = {"name": "Fecha", "sensible": False, "tipo": tipo, "nulable": False}
    if defecto is not None:
        columna_fecha["valor_por_defecto"] = defecto
    return {
        "version": "1",
        "desarrollo": "demo",
        "fuentes_datos": [
            {
                "database_id": "colsap", "server": "agpcolsap.database.windows.net", "database": "DB_COL_SAP",
                "esquemas": [
                    {"schema": ESQUEMA, "tablas": [{
                        "table": TABLA, "origen": "propia_del_desarrollo", "crear_en_despliegue": True, "sensibilidad": "ninguna",
                        "descripcion": "Alarma", "operaciones_permitidas": ["SELECT", "INSERT"],
                        "columnas": [{"name": "Id", "sensible": False, "tipo": "int", "clave_primaria": True, "autoincremental": True}, columna_fecha],
                    }]},
                    {"schema": "dbo", "tablas": [{
                        "table": "ODATA_MB52", "origen": "preexistente", "sensibilidad": "baja", "descripcion": "Inventario",
                        "operaciones_permitidas": ["SELECT"], "columnas": [{"name": "Material", "sensible": False}],
                    }]},
                ],
            }
        ],
    }


RUNTIME = """apiVersion: agp.runtime/v1
env:
  - name: COLSAP_DB_NAME
    value: "DB_COL_SAP"
secrets:
  - name: COLSAP_DB_USER
    secret: demo-db-user
  - name: COLSAP_DB_PASSWORD
    secret: demo-db-pwd
  - name: COLSAP_DB_SERVER
    secret: demo-db-server
"""


def _repo(tmp_path, manifiesto, runtime=RUNTIME):
    (tmp_path / "ai" / "outputs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "ai" / "outputs" / "data-access-manifest.json").write_text(json.dumps(manifiesto), encoding="utf-8")
    if runtime is not None:
        (tmp_path / ".agp").mkdir(exist_ok=True)
        (tmp_path / ".agp" / "runtime.yaml").write_text(runtime, encoding="utf-8")
    return tmp_path


def test_sin_manifiesto_no_hay_nada_que_revisar(tmp_path):
    assert check(tmp_path)["valid"] is True


def test_manifiesto_y_conexion_correctos_pasan(tmp_path):
    resultado = check(_repo(tmp_path, _manifiesto()))
    assert resultado["issues"] == []


def test_tipo_con_precision_fuera_de_la_lista_cerrada(tmp_path):
    resultado = check(_repo(tmp_path, _manifiesto(tipo="datetime2(0)")))
    assert resultado["valid"] is False
    assert any("fuera de la lista cerrada" in i for i in resultado["issues"])


def test_valor_por_defecto_incompatible_con_el_tipo(tmp_path):
    resultado = check(_repo(tmp_path, _manifiesto(tipo="int", defecto="SYSUTCDATETIME()")))
    assert any("valor_por_defecto no es válido" in i for i in resultado["issues"])


def test_base_con_tablas_preexistentes_sin_conexion_declarada(tmp_path):
    resultado = check(_repo(tmp_path, _manifiesto(), runtime="apiVersion: agp.runtime/v1\nenv: []\nsecrets: []\n"))
    assert any("DB_COL_SAP" in i and "runtime.yaml debe declarar la base" in i for i in resultado["issues"])


def test_secretos_de_conexion_de_las_tablas_propias_sin_declarar(tmp_path):
    runtime = RUNTIME.replace("demo-db-pwd", "otro-nombre")
    resultado = check(_repo(tmp_path, _manifiesto(), runtime=runtime))
    assert any("secretos de conexión de las tablas propias" in i and "demo-db-pwd" in i for i in resultado["issues"])


def _con_sqlite(manifiesto):
    manifiesto["fuentes_datos"].append({
        "database_id": "local", "server": "archivo-local", "database": "app.db", "motor": "SQLite local",
        "esquemas": [{"schema": "main", "tablas": [{"table": "config_local", "origen": "preexistente", "sensibilidad": "baja", "descripcion": "Parámetros",
                                                    "operaciones_permitidas": ["SELECT", "INSERT"], "columnas": [{"name": "Id", "sensible": False}]}]}]})
    return manifiesto


def test_sqlite_como_origen_de_despliegue_se_rechaza(tmp_path):
    resultado = check(_repo(tmp_path, _con_sqlite(_manifiesto())))
    assert resultado["valid"] is False
    assert any("SQLite" in i or "sqlite" in i for i in resultado["issues"])


def test_la_tabla_propia_que_viene_de_sqlite_con_migracion_desde_pasa(tmp_path):
    manifiesto = _manifiesto()
    manifiesto["fuentes_datos"][0]["esquemas"][0]["tablas"][0]["migracion_desde"] = {"motor": "sqlite", "tabla": "alarma_local"}
    assert check(_repo(tmp_path, manifiesto))["issues"] == []


def test_migracion_desde_mal_formada_se_rechaza(tmp_path):
    manifiesto = _manifiesto()
    manifiesto["fuentes_datos"][0]["esquemas"][0]["tablas"][0]["migracion_desde"] = {"motor": "oracle", "tabla": "x"}
    assert check(_repo(tmp_path, manifiesto))["valid"] is False


def test_la_sensibilidad_media_o_alta_no_bloquea_y_las_columnas_sensibles_tampoco(tmp_path):
    manifiesto = _manifiesto()
    tabla = manifiesto["fuentes_datos"][0]["esquemas"][1]["tablas"][0]   # dbo.ODATA_MB52, preexistente
    for nivel in ("media", "alta"):
        tabla["sensibilidad"] = nivel
        tabla["columnas"] = [{"name": "Material", "sensible": False}, {"name": "Correo", "sensible": True}]
        resultado = check(_repo(tmp_path / nivel, manifiesto))
        assert not any("dueño del dato" in i or "sensibilidad" in i for i in resultado["issues"]), resultado
