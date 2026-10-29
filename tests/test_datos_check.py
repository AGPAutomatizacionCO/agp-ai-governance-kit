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
    (tmp_path / "ai" / "outputs").mkdir(parents=True)
    (tmp_path / "ai" / "outputs" / "data-access-manifest.json").write_text(json.dumps(manifiesto), encoding="utf-8")
    if runtime is not None:
        (tmp_path / ".agp").mkdir()
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
