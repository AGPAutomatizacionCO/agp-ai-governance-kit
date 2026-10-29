"""ESPEJO de la Mesa de Requerimientos (backend/src/helpers/datos_permisos.py), copiado sin cambios de lógica.

La Mesa es la fuente de verdad: son las mismas reglas con las que valida el plan antes de que IT apruebe. Copiado aquí para que el
desarrollador y su agente las apliquen ANTES de pedir el despliegue (python -m agpctl datos check). Si la Mesa cambia una regla, se
vuelve a copiar el archivo; no se edita a mano.
"""
"""Permisos de un desarrollo sobre bases de datos que YA existen: qué pide, el documento que IT aprueba y el script cerrado que lo aplica.

Lógica pura (sin red ni base). La usan el preflight de la Mesa, que mete estos campos en el plan que aprueba IT (entran al hash del plan), la Mesa al aprobar
(crea la cuenta acotada y sus secretos) y el worker (vuelve a calcularlo del commit aprobado y aplica los GRANT solo si todo coincide).

Una sola declaración: `ai/outputs/data-access-manifest.json` (fuentes, servidor, base, esquema, tabla, operaciones, sensibilidad, columnas). Los nombres de los
secretos de conexión salen de `.agp/runtime.yaml` (variables `<PREFIJO>DB_DATABASE` y secretos `<PREFIJO>DB_SERVER|USERNAME|PASSWORD`). Nada se infiere del código:
lo que no está declarado no se concede.

Qué se concede y qué no:
  - SELECT, INSERT y UPDATE por tabla. INSERT/UPDATE son una excepción (se marca como escritura y exige explicar el motivo en la descripción de la tabla).
  - Nunca DELETE ni permisos de esquema. Sensibilidad media o alta: no se concede por esta vía (la aprueba el dueño del dato).
  - Las columnas marcadas como sensibles (p. ej. correos) no bloquean pero IT las ve resaltadas en el documento: aprobarlo es aprobar esa excepción.
  - Las tablas propias a crear (`crear_en_despliegue`) las cubre `datos_plan`; aquí solo las tablas `preexistente`.

Cuentas de plataforma (una vez por base, las crea IT): `datos-<slug>-prov-{user,pwd}` (la Mesa: crea el rol y la cuenta del desarrollo) y
`datos-<slug>-worker-{user,pwd}` (el worker: otorga los permisos; el dueño del dato le delegó cada tabla con WITH GRANT OPTION).
Slug de la base: minúsculas, `_` → `-` y sin el prefijo `agpc-` o `agp-` (agpc-productivity → productivity, AGP_Ingenieria → ingenieria).
"""
import hashlib
import re

from agpctl import mesa_datos_ddl as datos_ddl

VARIABLE_DESTINOS = "AGP_DATOS_DESTINOS"
CAMPOS_DEL_PLAN = ("datosPermisos", "datosPermisosSha256")
OPERACIONES = ("SELECT", "INSERT", "UPDATE")
_SERVIDOR = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}\.database\.windows\.net$")
_BASE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,40}$")
_IDENT = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,127}$")
_PERMISO = re.compile(r"^[A-Z][A-Z ]{2,40}$")
_PREFIJOS_DE_BASE = ("agpc-", "agp-")
_PARTE_DE_NOMBRE_DE_BASE = re.compile(r"^((?:[A-Z0-9]+_)*?)DB_(?:DATABASE|NAME)$")


def slug_de_base(base):
    slug = str(base or "").lower().replace("_", "-")
    for prefijo in _PREFIJOS_DE_BASE:
        if slug.startswith(prefijo) and len(slug) > len(prefijo):
            return slug[len(prefijo):]
    return slug


def secretos_de_plataforma(slug, quien):
    """(secreto del usuario, secreto de la contraseña) de la cuenta de plataforma `prov` (la Mesa) o `worker` (el worker) de esa base."""
    return f"datos-{slug}-{quien}-user", f"datos-{slug}-{quien}-pwd"


def secretos_de_cuentas_de_plataforma(slug):
    """Los cuatro secretos de las cuentas de plataforma de una base: usuario y contraseña de la Mesa (`prov`) y del worker."""
    return [n for quien in ("prov", "worker") for n in secretos_de_plataforma(slug, quien)]


def destinos_permitidos(texto):
    """Conjunto de `servidor/base` (minúsculas) de AGP_DATOS_DESTINOS (separados por coma o espacio). Es una lista RESTRICTIVA opcional: vacía = sin restricción
    adicional (un destino se habilita porque existen en el vault las cuentas de plataforma de su base, ver `motivo_de_destino_no_habilitado`)."""
    return {p.strip().lower() for p in re.split(r"[,\s]+", str(texto or "")) if p.strip()}


def motivo_de_destino_no_habilitado(d, restrictivos=(), faltan_secretos=None):
    """None si el destino `d` está habilitado; si no, el motivo, que dice qué debe crear IT (no una variable).

    Un destino queda habilitado cuando IT creó en esa base las cuentas de plataforma y guardó sus credenciales en el vault de desarrollos
    (`datos-<slug>-prov-*` y `datos-<slug>-worker-*`): crearlas ES la habilitación. Si AGP_DATOS_DESTINOS trae algo, además restringe: solo esos destinos.
    `faltan_secretos(nombres)` devuelve los nombres que no existen y lanza si no puede comprobarlo: ante un fallo se bloquea (nunca se da por habilitado).
    Sin `faltan_secretos` solo vale la lista restrictiva (compatibilidad con quien no puede consultar el vault)."""
    restrictivos = set(restrictivos or ())
    clave = f"{d['servidor']}/{d['base']}".lower()
    if restrictivos and clave not in restrictivos:
        return f"el destino {d['servidor']}/{d['base']} no está entre los destinos que IT permitió (AGP_DATOS_DESTINOS restringe los destinos de datos)"
    nombres = secretos_de_cuentas_de_plataforma(d["slug"])
    if faltan_secretos is None:
        return None if restrictivos else _mensaje_de_cuentas(d, nombres)
    try:
        faltan = list(faltan_secretos(nombres))
    except Exception:
        return (f"no se pudo comprobar en el vault de desarrollos si existen las cuentas de plataforma de {d['base']}: por seguridad el destino "
                f"{d['servidor']}/{d['base']} no se da por habilitado")
    return _mensaje_de_cuentas(d, faltan) if faltan else None


def _mensaje_de_cuentas(d, faltan):
    return (f"el destino {d['servidor']}/{d['base']} no está habilitado: IT debe crear en esa base las cuentas de plataforma (la de la Mesa y la del worker, "
            f"ver docs/despliegue/DATOS-DEL-DESARROLLO.md) y guardar sus credenciales en el vault de desarrollos; faltan los secretos {', '.join(faltan)}")


def _conexion_declarada(base, variables, secretos):
    """{server, user, pwd} con los nombres de secreto que `.agp/runtime.yaml` declara para esa base, o None si no declara los tres."""
    prefijo = None
    for variable in variables or []:
        m = _PARTE_DE_NOMBRE_DE_BASE.fullmatch(str(variable.get("name")))
        if m and str(variable.get("value")).lower() == str(base).lower():
            prefijo = m.group(1)
            break
    if prefijo is None:
        return None
    por_nombre = {s["name"]: s["secret"] for s in secretos or []}

    def elegir(*sufijos):
        return next((por_nombre[prefijo + s] for s in sufijos if prefijo + s in por_nombre), None)

    conexion = {"server": elegir("DB_SERVER", "DB_HOST"), "user": elegir("DB_USERNAME", "DB_USER"), "pwd": elegir("DB_PASSWORD", "DB_PWD")}
    return conexion if all(conexion.values()) else None


def _nombres_de_cuenta(secreto_de_usuario):
    """(cuenta, rol) derivados del secreto de usuario declarado (…-db-username → …_app y …_crud). Si el secreto ya existe en el vault, la Mesa reutiliza esa cuenta."""
    raiz = re.sub(r"-db-(username|user)$", "", secreto_de_usuario)
    ident = re.sub(r"[^a-z0-9]+", "_", raiz.lower()).strip("_")[:100]
    if not ident or not ident[0].isalpha():
        ident = "app_" + ident
    return f"{ident}_app", f"{ident}_crud"


def _texto_corto(valor, largo=160):
    return " ".join(str(valor or "").split())[:largo]


def leer_destinos(mapeo, excluir=None):
    """(destinos, problemas): las tablas `preexistente` del manifiesto agrupadas por servidor y base.

    `excluir` = (servidor, base) de las tablas propias del desarrollo: esa base la cubre `datos_plan` (que ya otorga su SELECT)."""
    problemas, grupos = [], {}
    for fuente in (mapeo or {}).get("fuentes_datos") or []:
        servidor, base = str(fuente.get("server") or "").lower(), str(fuente.get("database") or "")
        tablas = [(str(e.get("schema") or ""), t) for e in fuente.get("esquemas") or [] for t in e.get("tablas") or [] if t.get("origen") == "preexistente"]
        if not tablas:
            continue
        if excluir and base.lower() == str(excluir[1] or "").lower() and (not servidor or servidor == str(excluir[0] or "").lower()):
            continue
        etiqueta_base = base or str(fuente.get("database_id") or "?")
        if not servidor or not _SERVIDOR.fullmatch(servidor):
            problemas.append(f"{etiqueta_base}: la fuente debe declarar `server` con el nombre del servidor Azure SQL (*.database.windows.net)")
            continue
        if not _BASE.fullmatch(base):
            problemas.append(f"{etiqueta_base}: nombre de base inválido")
            continue
        destino = grupos.setdefault((servidor, base.lower()), {"servidor": servidor, "base": base, "tablas": {}})
        for esquema, tabla in tablas:
            nombre = str(tabla.get("table") or "")
            etiqueta = f"{base}: {esquema}.{nombre}"
            operaciones = tabla.get("operaciones_permitidas") or []
            if esquema == datos_ddl._ESQUEMA_SIN_CALIFICAR:
                problemas.append(f"{etiqueta}: declara el esquema real de la tabla (hoy dice «{esquema}»)")
            elif not _IDENT.fullmatch(esquema) or esquema.lower() in datos_ddl._ESQUEMAS_NO_COMPARTIBLES or esquema.lower().startswith("app_"):
                problemas.append(f"{etiqueta}: el esquema «{esquema}» no se puede compartir por esta vía (sistema o esquema propio de otro desarrollo)")
            if not _IDENT.fullmatch(nombre):
                problemas.append(f"{etiqueta}: nombre de tabla inválido")
            fuera = sorted({str(o) for o in operaciones} - set(OPERACIONES))
            if not operaciones or fuera:
                problemas.append(f"{etiqueta}: " + (f"{', '.join(fuera)} no se otorga por esta vía (solo {', '.join(OPERACIONES)})" if fuera
                                                     else "no declara operaciones_permitidas"))
            if str(tabla.get("sensibilidad") or "") not in datos_ddl._SENSIBILIDAD_AUTOMATICA:
                problemas.append(f"{etiqueta}: sensibilidad «{tabla.get('sensibilidad')}»: no se otorga por esta vía; lo aprueba el dueño del dato")
            permisos = [o for o in OPERACIONES if o in operaciones]
            escritura = any(o in permisos for o in ("INSERT", "UPDATE"))
            if escritura and not _texto_corto(tabla.get("descripcion")):
                problemas.append(f"{etiqueta}: escribe (INSERT/UPDATE) pero su descripción no dice para qué; es una excepción y IT necesita el motivo")
            clave = (esquema.lower(), nombre.lower())
            if clave in destino["tablas"]:
                problemas.append(f"{etiqueta}: tabla repetida en el manifiesto")
            destino["tablas"][clave] = {
                "objeto": f"{esquema}.{nombre}", "esquema": esquema, "tabla": nombre, "permisos": permisos, "escritura": escritura,
                "sensibilidad": str(tabla.get("sensibilidad") or ""), "motivo": _texto_corto(tabla.get("descripcion")),
                "columnasSensibles": sorted(str(c.get("name")) for c in tabla.get("columnas") or [] if c.get("sensible") is True)}
    destinos = []
    for clave in sorted(grupos):
        d = grupos[clave]
        d["tablas"] = [d["tablas"][k] for k in sorted(d["tablas"])]
        d["slug"] = slug_de_base(d["base"])
        if not _SLUG.fullmatch(d["slug"]):
            problemas.append(f"{d['base']}: no se puede derivar un nombre de cuenta de plataforma de esa base")
        destinos.append(d)
    visto = {}
    for d in destinos:
        if visto.setdefault(d["slug"], d["base"]) != d["base"]:
            problemas.append(f"Las bases {visto[d['slug']]} y {d['base']} dan el mismo nombre de cuenta de plataforma ({d['slug']})")
    return destinos, problemas


def _q(identificador):
    return datos_ddl._q(identificador)


def script_de_destino(destino):
    """T-SQL cerrado que otorga exactamente lo declarado al rol del desarrollo. Cada tabla: comprueba que exista, retira SOLO lo que el rol tiene y el manifiesto ya no declara
    (un REVOKE de un permiso que la cuenta del worker no tiene delegado falla aunque el rol no lo tenga) y otorga lo declarado. Sin DELETE ni permisos de esquema. Los identificadores ya pasaron la validación estricta."""
    validar_destino(destino)
    rol = destino["rol"]
    lineas = ["-- Generado por la Mesa a partir del manifiesto aprobado. No editar a mano: el hash entra en el plan de IT.",
              "SET XACT_ABORT ON;", "BEGIN TRANSACTION;",
              f"IF DATABASE_PRINCIPAL_ID(N'{rol}') IS NULL THROW 50003, N'El rol {rol} no existe: lo crea la Mesa al aprobar.', 1;"]
    for t in destino["tablas"]:
        lineas += [f"IF OBJECT_ID(N'{t['esquema']}.{t['tabla']}') IS NULL THROW 50002, N'La tabla {t['esquema']}.{t['tabla']} no existe en esta base.', 1;",
                   *[(f"IF EXISTS (SELECT 1 FROM sys.database_permissions WHERE class = 1 AND major_id = OBJECT_ID(N'{t['esquema']}.{t['tabla']}') "
                      f"AND grantee_principal_id = DATABASE_PRINCIPAL_ID(N'{rol}') AND permission_name = N'{o}' AND state IN ('G', 'W')) "
                      f"REVOKE {o} ON OBJECT::{_q(t['esquema'])}.{_q(t['tabla'])} FROM {_q(rol)};") for o in OPERACIONES if o not in t["permisos"]],
                   f"GRANT {', '.join(t['permisos'])} ON OBJECT::{_q(t['esquema'])}.{_q(t['tabla'])} TO {_q(rol)};"]
    lineas += ["COMMIT TRANSACTION;", ""]
    return "\n".join(lineas)


def validar_destino(destino):
    """Lanza ValueError si un destino (p. ej. leído de un plan guardado) trae algo fuera de la norma: nada que no cumpla llega a una sentencia."""
    if not _SERVIDOR.fullmatch(str(destino.get("servidor"))) or not _BASE.fullmatch(str(destino.get("base"))) or not _SLUG.fullmatch(str(destino.get("slug"))):
        raise ValueError("Destino de datos fuera de la norma")
    if not _IDENT.fullmatch(str(destino.get("rol"))) or not _IDENT.fullmatch(str(destino.get("cuenta"))):
        raise ValueError("Cuenta o rol fuera de la norma")
    for t in destino.get("tablas") or []:
        if (not _IDENT.fullmatch(str(t.get("esquema"))) or not _IDENT.fullmatch(str(t.get("tabla")))
                or not t.get("permisos") or not set(t["permisos"]) <= set(OPERACIONES)):
            raise ValueError("Tabla o permiso fuera de la norma")


def sentencias_de_reconciliacion(destino, existentes):
    """REVOKE de lo que el rol tiene en la base y el manifiesto ya no declara. `existentes` = [(esquema, objeto, permiso)]. Solo quita permisos: nunca otorga."""
    declarado = {(t["esquema"].lower(), t["tabla"].lower()): set(t["permisos"]) for t in destino["tablas"]}
    sentencias = []
    for esquema, objeto, permiso in sorted(existentes):
        if permiso in declarado.get((str(esquema).lower(), str(objeto).lower()), set()):
            continue
        if not (_IDENT.fullmatch(str(esquema)) and _IDENT.fullmatch(str(objeto)) and _PERMISO.fullmatch(str(permiso))):
            raise ValueError("Permiso existente fuera de la norma")
        sentencias.append(f"REVOKE {permiso} ON OBJECT::{_q(esquema)}.{_q(objeto)} FROM {_q(destino['rol'])};")
    return sentencias


def faltan_o_sobran(destino, existentes):
    """(faltan, sobran) respecto de lo declarado, como textos `esquema.tabla permiso`."""
    esperado = {(t["esquema"].lower(), t["tabla"].lower(), p): f"{t['objeto']} {p}" for t in destino["tablas"] for p in t["permisos"]}
    actual = {(str(e).lower(), str(o).lower(), str(p)): f"{e}.{o} {p}" for e, o, p in existentes}
    return sorted(esperado[k] for k in esperado.keys() - actual.keys()), sorted(actual[k] for k in actual.keys() - esperado.keys())


def _hash(destinos):
    return hashlib.sha256("\n".join(f"{d['servidor']}/{d['base']}:{d['scriptSha256']}" for d in destinos).encode("utf-8")).hexdigest()


def plan_de_permisos(mapeo, variables, secretos, *, destinos_configurados=(), habilitado=False, excluir=None, faltan_secretos=None, comprobar_habilitacion=True):
    """(info, bloqueos). `info` es None si el manifiesto no pide permisos sobre bases existentes.

    Con `habilitado` (AGP_DATOS_ENABLED) los problemas bloquean el plan y cada destino debe estar habilitado (existen sus cuentas de plataforma en el vault:
    `faltan_secretos`; AGP_DATOS_DESTINOS, si trae algo, restringe). `comprobar_habilitacion=False` (el worker, que no puede listar el vault y lo comprueba al leer
    su propia cuenta) omite esa comprobación pero no el resto. Sin habilitar, la ejecución automática está apagada:
    el documento se genera igual para que IT lo vea y lo configure a mano, y los problemas quedan como observaciones (no bloquean, para no romper despliegues vigentes)."""
    destinos, problemas = leer_destinos(mapeo, excluir)
    if not destinos and not problemas:
        return None, []
    secretos_de_la_mesa = []
    for d in destinos:
        conexion = _conexion_declarada(d["base"], variables, secretos)
        if conexion is None:
            problemas.append(f"{d['base']}: .agp/runtime.yaml debe declarar la base (variable <PREFIJO>DB_DATABASE) y sus tres secretos de conexión "
                             "(<PREFIJO>DB_SERVER, <PREFIJO>DB_USERNAME y <PREFIJO>DB_PASSWORD)")
            continue
        d["secretos"] = conexion
        d["cuenta"], d["rol"] = _nombres_de_cuenta(conexion["user"])
        secretos_de_la_mesa += list(conexion.values())
        if habilitado and comprobar_habilitacion:
            motivo = motivo_de_destino_no_habilitado(d, destinos_configurados, faltan_secretos)
            if motivo:
                problemas.append(f"{d['base']}: {motivo}")
    if problemas and habilitado:
        return None, [f"Datos: {p}" for p in problemas]
    completos = [d for d in destinos if "rol" in d]
    for d in completos:
        d["scriptSha256"] = hashlib.sha256(script_de_destino(d).encode("utf-8")).hexdigest()
    info = {"datosPermisos": completos, "datosPermisosSha256": _hash(completos), "datosPermisosActivo": bool(habilitado),
            "datosPermisosSecretos": sorted(set(secretos_de_la_mesa)) if habilitado else []}
    if problemas:
        info["datosPermisosObservaciones"] = problemas
    info["datosPermisosDocumento"] = documento(info, str((mapeo or {}).get("desarrollo") or "el desarrollo"))
    return info, []


def documento(info, desarrollo):
    """El documento que IT aprueba (Markdown): por base y servidor, la cuenta, los secretos y por tabla el permiso, la sensibilidad y el motivo."""
    activo = info.get("datosPermisosActivo") is True
    lineas = [f"# Permisos de datos de {desarrollo}", "",
              "Al aprobar el despliegue, IT aprueba estos permisos completos. " + (
                  "La ejecución automática está ACTIVA: la Mesa crea la cuenta y sus secretos y el worker otorga los permisos."
                  if activo else "La ejecución automática está APAGADA: IT configura estas cuentas y permisos a mano (los secretos deben existir en el vault)."), ""]
    for d in info.get("datosPermisos") or []:
        lineas += [f"## Base «{d['base']}» · {d['servidor']}", "",
                   f"- Cuenta del desarrollo: `{d['cuenta']}` (rol `{d['rol']}`). Si el secreto de usuario ya existe en el vault se reutiliza esa cuenta.",
                   f"- Secretos de conexión (vault de desarrollos): `{d['secretos']['server']}`, `{d['secretos']['user']}`, `{d['secretos']['pwd']}`",
                   f"- Cuentas de plataforma de esta base: `datos-{d['slug']}-prov-*` (la Mesa) y `datos-{d['slug']}-worker-*` (el worker)", "",
                   "| Tabla | Permisos | Sensibilidad | Motivo |", "|---|---|---|---|"]
        for t in d["tablas"]:
            marca = " (ESCRITURA: excepción)" if t["escritura"] else ""
            lineas.append(f"| {t['objeto']} | {', '.join(t['permisos'])}{marca} | {t['sensibilidad']} | {t['motivo'] or '—'} |")
        sensibles = [f"{t['objeto']}: {', '.join(t['columnasSensibles'])}" for t in d["tablas"] if t["columnasSensibles"]]
        if sensibles:
            lineas += ["", "Columnas sensibles que la cuenta podrá leer (IT las aprueba al aprobar): " + "; ".join(sensibles)]
        lineas += ["", f"Hash del script: `{d['scriptSha256']}`", ""]
    lineas += ["Nunca se otorga DELETE ni permisos de esquema. Retirar una tabla o un permiso del manifiesto exige aprobar un plan nuevo y revoca lo ya otorgado."]
    if info.get("datosPermisosObservaciones"):
        lineas += ["", "Observaciones (no bloquean mientras la ejecución automática esté apagada):"] + [f"- {o}" for o in info["datosPermisosObservaciones"]]
    return "\n".join(lineas) + "\n"
