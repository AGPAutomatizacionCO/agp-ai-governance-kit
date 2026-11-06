# ESPEJO de la Mesa de Requerimientos (backend/src/helpers/datos_plan.py), copiado sin cambios de lógica: solo se adaptan los imports.
# La Mesa es la fuente de verdad: son las mismas reglas con las que valida el plan antes de que IT apruebe.
# Si la Mesa cambia una regla, se regenera con `python scripts/sincronizar_espejos_mesa.py --mesa <repo de la Mesa>`; no se edita a mano.
# ESPEJO-COMMIT: 3b311cdd4851b068973ea7bfb4ec04398075e16c
# ESPEJO-SHA256: bb7db4e7c5f142c3eda15fdb0fca9869c1d1df50befffce753edd23d8bb91259
# ===== ESPEJO DE LA MESA: inicio del código (no editar a mano; regenerar con scripts/sincronizar_espejos_mesa.py) =====
"""Parte de DATOS del plan de despliegue: qué esquema y tablas propias se crean, dónde, y con qué script (por hash).

Es lógica pura (sin red ni base): la usan el preflight de la Mesa, que mete estos campos en el plan que aprueba IT, y el worker, que
vuelve a calcularlos del commit aprobado y se niega a ejecutar si el hash no coincide. Norma de nombres: NOMENCLATURA-DATOS.md del kit.

Campos del plan (todos entran al hash que aprueba IT, así que IT ve dónde se van a crear las tablas):
  datosServidor, datosBase, datosEsquema, datosTablas (nombres), datosLecturas (tablas preexistentes que se comparten, solo SELECT), datosRol, datosUsuario,
  datosScriptSha256
"""
import re

from agpctl import mesa_datos_ddl as datos_ddl
from agpctl.mesa_datos_permisos import OPERACIONES, _texto_corto

RUTA_MANIFIESTO = "ai/outputs/data-access-manifest.json"
_SERVIDOR = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}\.database\.windows\.net$")
_BASE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
CAMPOS_DEL_PLAN = ("datosServidor", "datosBase", "datosEsquema", "datosTablas", "datosLecturas", "datosRol", "datosUsuario", "datosScriptSha256")


def nombres(esquema):
    """Usuario, rol y secretos que corresponden a un esquema `app_<area>_<desarrollo>` (NOMENCLATURA-DATOS.md)."""
    partes = str(esquema or "").split("_", 2)
    if len(partes) != 3 or partes[0] != "app" or not all(partes[1:]):
        raise ValueError("Esquema fuera de la norma app_<area>_<desarrollo>")
    desarrollo = partes[2]
    return {"esquema": esquema, "usuario": f"{esquema}_app", "rol": f"{esquema}_crud",
            "secretos": {"user": f"{desarrollo}-db-user", "pwd": f"{desarrollo}-db-pwd", "server": f"{desarrollo}-db-server"}}


def _fila_de_tabla(esquema, tabla, origen):
    """Una fila del documento que ve IT (mismo formato que las tablas de bases existentes): objeto, permisos, sensibilidad, motivo y columnas sensibles."""
    operaciones = set(tabla.get("operaciones_permitidas") or [])
    fila = {"objeto": f"{esquema}.{tabla.get('table')}", "origen": origen, "permisos": [o for o in OPERACIONES if o in operaciones],
            "sensibilidad": str(tabla.get("sensibilidad") or ""), "motivo": _texto_corto(tabla.get("descripcion")),
            "columnasSensibles": sorted(str(c.get("name")) for c in tabla.get("columnas") or [] if c.get("sensible") is True)}
    desde = tabla.get("migracion_desde")
    if isinstance(desde, dict) and desde.get("tabla"):
        fila["desde"] = f"SQLite · {desde['tabla']}"   # informativo: de dónde venía; la tabla nace vacía
    return fila


def detalle_de_tablas(mapeo, servidor, base):
    """Tablas propias que se crean (permisos de su manifiesto) y tablas existentes que solo se leen, para MOSTRARLAS. No entra a CAMPOS_DEL_PLAN: lo que se
    aprueba y se compara sigue siendo el script por hash; esto es la misma información legible."""
    return ([_fila_de_tabla(e, t, "propia") for e, t in datos_ddl.tablas_a_crear(mapeo)]
            + [_fila_de_tabla(e, t, "existente") for e, t in datos_ddl.tablas_a_leer(mapeo, servidor, base)])


def plan_de_datos(mapeo, servidor, base, habilitado):
    """(info, bloqueos). `info` es None si el manifiesto no crea tablas; si las crea, trae los campos del plan.

    `servidor` y `base` salen de la configuración de la Mesa (AGP_DATOS_SQL_SERVER / AGP_DATOS_SQL_DATABASE)."""
    locales = datos_ddl.revisar_datos_locales(mapeo)
    if locales:
        return None, [f"Datos: {p}" for p in locales]   # SQLite como origen de despliegue: se declara su tabla propia (bloquea con o sin AGP_DATOS_ENABLED)
    if not datos_ddl.tablas_a_crear(mapeo):
        return None, []
    if not habilitado:
        return None, ["Datos: el manifiesto pide crear tablas en el despliegue (crear_en_despliegue) pero la creación automática de tablas "
                      "no está habilitada (AGP_DATOS_ENABLED=true): la variable debe estar en la Mesa (App Service) Y en el Job del worker, que repite esta "
                      "validación con su propio entorno"]
    bloqueos = []
    if not _SERVIDOR.fullmatch(str(servidor or "")) or not _BASE.fullmatch(str(base or "")):
        bloqueos.append("Datos: falta o es inválida la configuración del destino de las tablas (AGP_DATOS_SQL_SERVER / AGP_DATOS_SQL_DATABASE)")
    bloqueos += [f"Datos: {p}" for p in datos_ddl.revisar_tablas_a_crear(mapeo) + datos_ddl.revisar_lecturas(mapeo, servidor, base)]
    if bloqueos:
        return None, bloqueos
    esquema = datos_ddl.tablas_a_crear(mapeo)[0][0]
    n = nombres(esquema)
    resultado = datos_ddl.generar_script(mapeo, n["rol"], servidor, base)
    return ({"datosServidor": servidor, "datosBase": base, "datosEsquema": esquema, "datosTablas": resultado["tablas"], "datosLecturas": resultado["lecturas"],
             "datosRol": n["rol"], "datosUsuario": n["usuario"], "datosScriptSha256": resultado["sha256"],
             "datosSecretos": sorted(n["secretos"].values()), "datosTablasDetalle": detalle_de_tablas(mapeo, servidor, base)}, [])


def documento_de_datos_propios(info):
    """Markdown de lo que el worker crea en la base propia (mismo formato que el documento de permisos de bases existentes), para el documento que IT aprueba."""
    lineas = [f"## Base «{info['datosBase']}» · {info['datosServidor']} (esquema propio, lo crea el worker)", "",
              f"- Esquema: `{info['datosEsquema']}` · cuenta del desarrollo: `{info['datosUsuario']}` (rol `{info['datosRol']}`)",
              "- Nombres según la norma del kit: esquema `app_<área>_<desarrollo>` y tabla `App_<Área>_<Desarrollo>_<tabla>`", "",
              "| Tabla | Permisos | Sensibilidad | Motivo |", "|---|---|---|---|"]
    for t in info.get("datosTablasDetalle") or []:
        marca = "" if t["origen"] == "propia" else " (tabla existente, solo lectura)"
        origen = f" ← {t['desde']} (nace vacía)" if t.get("desde") else ""
        lineas.append(f"| {t['objeto']}{origen} | {', '.join(t['permisos'])}{marca} | {t['sensibilidad']} | {t['motivo'] or '—'} |")
    return "\n".join(lineas + ["", f"Hash del script: `{info['datosScriptSha256']}`", ""]) + "\n"


def secretos_sin_declarar(secretos_declarados, esquema):
    """Secretos de conexión que `.agp/runtime.yaml` debe declarar (usuario, contraseña y servidor) y no declara."""
    return [s for s in nombres(esquema)["secretos"].values() if s not in set(secretos_declarados or [])]
