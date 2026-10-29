"""ESPEJO de la Mesa de Requerimientos (backend/src/helpers/datos_ddl.py), copiado sin cambios de lógica.

La Mesa es la fuente de verdad: son las mismas reglas con las que valida el plan antes de que IT apruebe. Copiado aquí para que el
desarrollador y su agente las apliquen ANTES de pedir el despliegue (python -m agpctl datos check). Si la Mesa cambia una regla, se
vuelve a copiar el archivo; no se edita a mano.
"""
"""Tablas propias de un desarrollo: validar la norma de nombres y generar el T-SQL que las crea (sin ejecutar nada).

Fuente de la norma: NOMENCLATURA-DATOS.md del kit de gobernanza. Entrada: `ai/outputs/data-access-manifest.json` ya validado contra el
esquema del kit. Solo se consideran las tablas con `crear_en_despliegue: true`.

Por qué se genera desde el JSON y no se ejecuta SQL del repositorio: el worker corre con permisos de creación sobre el esquema del
desarrollo, así que lo que ejecuta tiene que salir de una lista cerrada (nombres, tipos y operaciones ya aprobados), nunca de texto
libre del desarrollador. El hash del script entra en el plan que aprueba IT: si el script cambia, hay que aprobar de nuevo.

Seguridad de los identificadores: los `GRANT`/`CREATE` son DDL y no admiten parámetros. Todo identificador se valida con una expresión
estricta ANTES de usarse y además se escapa entre corchetes; nada que no cumpla llega al script.
"""
import hashlib
import re

_ESQUEMA = re.compile(r"^app_[a-z0-9]+_[a-z0-9]+$")
_TABLA = re.compile(r"^App_([A-Za-z0-9]+)_([A-Za-z0-9]+)_([A-Za-z][A-Za-z0-9_]{0,100})$")
_COLUMNA = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,127}$")
_ROL = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_REFERENCIA = re.compile(r"^(App_[A-Za-z0-9]+_[A-Za-z0-9]+_[A-Za-z][A-Za-z0-9_]*)\.([A-Za-z][A-Za-z0-9_]*)$")
_TIPO = re.compile(
    r"^(int|bigint|smallint|tinyint|bit|date|datetime2|uniqueidentifier|float|real"
    r"|nvarchar\((max|4000|[1-3][0-9]{3}|[1-9][0-9]{0,2})\)|varchar\((max|8000|[1-7][0-9]{3}|[1-9][0-9]{0,2})\)"
    r"|decimal\(([1-9]|[12][0-9]|3[0-8]),([0-9]|[12][0-9]|3[0-8])\)|varbinary\((max|[1-9][0-9]{0,3})\))$")
_ENTEROS = {"int", "bigint", "smallint", "tinyint"}
_OPERACIONES = ("SELECT", "INSERT", "UPDATE", "DELETE")
_TEXTO_SIMPLE = re.compile(r"^[A-Za-z0-9 _.:-]{0,100}$")
_FUNCION_PERMITIDA = "SYSUTCDATETIME()"
_MAX_CLAVE_BYTES = 1700  # límite de una clave de índice no agrupado en SQL Server / Azure SQL
_BYTES_FIJOS = {"bit": 1, "tinyint": 1, "smallint": 2, "int": 4, "bigint": 8, "real": 4, "float": 8, "date": 3, "datetime2": 8,
                "uniqueidentifier": 16}


def _bytes_de_clave(tipo):
    """Bytes que ocupa un tipo en una clave de índice, o None si no puede ser clave (los tipos max)."""
    if tipo in _BYTES_FIJOS:
        return _BYTES_FIJOS[tipo]
    m = re.fullmatch(r"(nvarchar|varchar|varbinary)\((max|\d+)\)", tipo)
    if m:
        if m.group(2) == "max":
            return None
        return int(m.group(2)) * (2 if m.group(1) == "nvarchar" else 1)
    if tipo.startswith("decimal("):
        return 17
    return None


def _nombre_objeto(prefijo, tabla, columnas=()):
    """Nombre de restricción/índice (máx. 128): si no cabe se recorta y se agrega un sufijo estable."""
    nombre = "_".join([prefijo, tabla, *columnas])
    if len(nombre) <= 128:
        return nombre
    return nombre[:119] + "_" + hashlib.sha1(nombre.encode("utf-8")).hexdigest()[:8]


def _literal(valor, tipo):
    """Literal T-SQL del valor por defecto, o None si no es compatible con el tipo."""
    if valor == _FUNCION_PERMITIDA:
        return _FUNCION_PERMITIDA if tipo in ("datetime2", "date") else None
    if isinstance(valor, bool):
        return "1" if valor and tipo == "bit" else ("0" if tipo == "bit" else None)
    if isinstance(valor, (int, float)):
        if tipo == "bit":
            return str(int(valor)) if valor in (0, 1) else None
        numerico = tipo in _ENTEROS or tipo in ("float", "real") or tipo.startswith("decimal(")
        entero_ok = isinstance(valor, int) or tipo not in _ENTEROS
        return repr(valor) if numerico and entero_ok and valor == valor and abs(valor) < 1e15 else None
    if isinstance(valor, str) and _TEXTO_SIMPLE.fullmatch(valor) and re.match(r"^(nvarchar|varchar)\(", tipo):
        return "N'" + valor.replace("'", "''") + "'"
    return None


def _q(identificador):
    """Escapa un identificador ya validado para T-SQL."""
    return "[" + identificador.replace("]", "]]") + "]"


def tablas_a_crear(mapeo):
    """[(esquema, tabla_dict)] de las tablas con crear_en_despliegue=true, en el orden del manifiesto."""
    resultado = []
    for fuente in (mapeo or {}).get("fuentes_datos") or []:
        for esquema in fuente.get("esquemas") or []:
            for tabla in esquema.get("tablas") or []:
                if tabla.get("crear_en_despliegue") is True:
                    resultado.append((str(esquema.get("schema") or ""), tabla))
    return resultado


# ---- Lectura de tablas PREEXISTENTES (mismo script, misma aprobación de IT) ------------------------------------------------------------
# Un desarrollo con esquema propio también lee tablas que ya existen en esa misma base (p. ej. dbo.ODATA_MB52_IM03). Las declara en el manifiesto con
# origen «preexistente» y operaciones_permitidas = [SELECT]; el script suma un GRANT SELECT por tabla al rol del desarrollo y IT lo ve en el plan
# (datosLecturas) antes de aprobar. Solo SELECT, solo en la base donde se crean las tablas propias y solo de sensibilidad baja: lo demás lo decide el dueño del dato.
# El LÍMITE REAL lo pone la base: el GRANT solo prospera si el DBA delegó SELECT ... WITH GRANT OPTION sobre esa tabla a la cuenta del worker.
_ESQUEMAS_NO_COMPARTIBLES = {"sys", "information_schema", "guest"}
_SENSIBILIDAD_AUTOMATICA = ("ninguna", "baja")
_ESQUEMA_SIN_CALIFICAR = "sin_calificar_en_el_codigo"   # marcador de los manifiestos cuando el código no califica el esquema: no es un esquema real
_IDENTIFICADOR = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,127}$")


def tablas_a_leer(mapeo, servidor, base):
    """[(esquema, tabla_dict)] de las tablas preexistentes del manifiesto que viven en la MISMA base (y servidor, si lo declara) donde se crean las propias."""
    resultado = []
    for fuente in (mapeo or {}).get("fuentes_datos") or []:
        if str(fuente.get("database") or "").lower() != str(base or "").lower():
            continue
        declarado = str(fuente.get("server") or "").lower()
        if declarado and declarado != str(servidor or "").lower():
            continue
        for esquema in fuente.get("esquemas") or []:
            for tabla in esquema.get("tablas") or []:
                if tabla.get("origen") == "preexistente":
                    resultado.append((str(esquema.get("schema") or ""), tabla))
    return resultado


def revisar_lecturas(mapeo, servidor, base):
    """Problemas de las lecturas de tablas preexistentes frente a la regla; vacía si no hay o si cumplen."""
    problemas, vistas = [], set()
    for esquema, tabla in tablas_a_leer(mapeo, servidor, base):
        nombre = str(tabla.get("table") or "")
        etiqueta = f"{esquema}.{nombre}"
        if (esquema.lower(), nombre.lower()) in vistas:
            problemas.append(f"{etiqueta}: tabla preexistente repetida")
        vistas.add((esquema.lower(), nombre.lower()))
        if esquema == _ESQUEMA_SIN_CALIFICAR:
            problemas.append(f"{etiqueta}: declara el esquema real de la tabla preexistente (hoy dice «{_ESQUEMA_SIN_CALIFICAR}»)")
        elif not _IDENTIFICADOR.fullmatch(esquema) or esquema.lower() in _ESQUEMAS_NO_COMPARTIBLES or esquema.lower().startswith("app_"):
            problemas.append(f"{etiqueta}: el esquema «{esquema}» no se puede compartir por esta vía (sistema o esquema propio de otro desarrollo)")
        if not _IDENTIFICADOR.fullmatch(nombre):
            problemas.append(f"{etiqueta}: nombre de tabla inválido")
        operaciones = set(tabla.get("operaciones_permitidas") or [])
        if operaciones != {"SELECT"}:
            problemas.append(f"{etiqueta}: sobre tablas preexistentes solo se otorga SELECT; {', '.join(sorted(operaciones - {'SELECT'})) or 'sin operaciones'} "
                             "requiere una excepción aprobada por IT")
        sensibles = [c.get("name") for c in tabla.get("columnas") or [] if c.get("sensible") is True]
        if str(tabla.get("sensibilidad") or "") not in _SENSIBILIDAD_AUTOMATICA or sensibles:
            problemas.append(f"{etiqueta}: sensibilidad «{tabla.get('sensibilidad')}»" + (f" o columnas sensibles ({', '.join(sensibles[:3])})" if sensibles else "")
                             + ": no se otorga por la ruta automática; lo aprueba el dueño del dato")
    return problemas


def lecturas_del_plan(mapeo, servidor, base):
    """['esquema.tabla', ...] ordenadas: lo que IT ve y aprueba en el plan (datosLecturas)."""
    return sorted({f"{e}.{t['table']}" for e, t in tablas_a_leer(mapeo, servidor, base)})


def revisar_tablas_a_crear(mapeo):
    """Lista de problemas de las tablas propias a crear frente a la norma; vacía si cumplen (o si no hay ninguna)."""
    tablas = tablas_a_crear(mapeo)
    if not tablas:
        return []
    problemas = []
    esquemas = sorted({e for e, _ in tablas})
    if len(esquemas) > 1:
        problemas.append("Las tablas a crear deben ir todas en el esquema propio del desarrollo; hay varios: " + ", ".join(esquemas))
    nombres = {}
    for esquema, tabla in tablas:
        nombre = str(tabla.get("table") or "")
        etiqueta = f"{esquema}.{nombre}"
        if not _ESQUEMA.fullmatch(esquema) or len(esquema) > 128:
            problemas.append(f"{etiqueta}: el esquema debe ser app_<area>_<desarrollo> en minúsculas (NOMENCLATURA-DATOS.md)")
        coincidencia = _TABLA.fullmatch(nombre)
        if not coincidencia or len(nombre) > 128:
            problemas.append(f"{etiqueta}: la tabla debe llamarse App_<Área>_<Desarrollo>_<tabla> (letras y dígitos; guion bajo solo en <tabla>)")
        elif _ESQUEMA.fullmatch(esquema) and f"app_{coincidencia.group(1).lower()}_{coincidencia.group(2).lower()}" != esquema:
            problemas.append(f"{etiqueta}: el prefijo de la tabla (App_{coincidencia.group(1)}_{coincidencia.group(2)}_) no corresponde al esquema")
        if nombre.lower() in nombres:
            problemas.append(f"{etiqueta}: nombre repetido (SQL Server no distingue mayúsculas)")
        nombres[nombre.lower()] = tabla
        if tabla.get("origen") != "propia_del_desarrollo":
            problemas.append(f"{etiqueta}: solo se crean tablas con origen propia_del_desarrollo")
    for esquema, tabla in tablas:
        nombre = str(tabla.get("table") or "")
        etiqueta = f"{esquema}.{nombre}"
        columnas = tabla.get("columnas") or []
        vistas, claves = set(), 0
        if not columnas:
            problemas.append(f"{etiqueta}: no declara columnas")
        for columna in columnas:
            cn = str(columna.get("name") or "")
            if not _COLUMNA.fullmatch(cn):
                problemas.append(f"{etiqueta}: nombre de columna inválido «{cn}»")
            if cn.lower() in vistas:
                problemas.append(f"{etiqueta}: columna repetida «{cn}»")
            vistas.add(cn.lower())
            tipo = str(columna.get("tipo") or "")
            if not _TIPO.fullmatch(tipo):
                problemas.append(f"{etiqueta}.{cn}: tipo «{tipo or 'sin tipo'}» fuera de la lista cerrada")
            if columna.get("clave_primaria") is True:
                claves += 1
            if columna.get("autoincremental") is True and not (tipo in _ENTEROS and columna.get("clave_primaria") is True):
                problemas.append(f"{etiqueta}.{cn}: autoincremental solo aplica a una clave primaria entera")
            for campo in ("unico", "indice"):
                if columna.get(campo) is not None and not isinstance(columna.get(campo), bool):
                    problemas.append(f"{etiqueta}.{cn}: {campo} debe ser verdadero o falso")
                elif columna.get(campo) is True and _TIPO.fullmatch(tipo):
                    clave = _bytes_de_clave(tipo)
                    if clave is None:
                        problemas.append(f"{etiqueta}.{cn}: una columna {campo} no puede ser {tipo}; declara un largo (p. ej. nvarchar(320))")
                    elif clave > _MAX_CLAVE_BYTES:
                        problemas.append(f"{etiqueta}.{cn}: la clave de {campo} ocupa {clave} bytes y el máximo es {_MAX_CLAVE_BYTES}")
            if "valor_por_defecto" in columna:
                if _literal(columna["valor_por_defecto"], tipo) is None:
                    problemas.append(f"{etiqueta}.{cn}: valor_por_defecto no es válido para el tipo {tipo or 'sin tipo'}")
                elif columna.get("autoincremental") is True:
                    problemas.append(f"{etiqueta}.{cn}: una columna de identidad no lleva valor_por_defecto")
            referencia = columna.get("referencia")
            if referencia is not None:
                m = _REFERENCIA.fullmatch(str(referencia))
                destino = nombres.get(m.group(1).lower()) if m else None
                if not m:
                    problemas.append(f"{etiqueta}.{cn}: referencia inválida «{referencia}» (formato tabla.columna)")
                elif destino is None:
                    problemas.append(f"{etiqueta}.{cn}: la referencia apunta a «{m.group(1)}», que no es una tabla propia a crear en este manifiesto")
                elif m.group(2).lower() not in {str(c.get("name") or "").lower() for c in destino.get("columnas") or []}:
                    problemas.append(f"{etiqueta}.{cn}: la tabla «{m.group(1)}» no tiene la columna «{m.group(2)}»")
        if claves == 0:
            problemas.append(f"{etiqueta}: falta una columna con clave_primaria")
        tipos = {str(c.get("name") or "").lower(): str(c.get("tipo") or "") for c in columnas}
        for campo in ("restricciones_unicas", "indices"):
            for grupo in tabla.get(campo) or []:
                cols = [str(x) for x in (grupo.get("columnas") if isinstance(grupo, dict) else None) or []]
                if len(cols) < 2 or len({x.lower() for x in cols}) != len(cols):
                    problemas.append(f"{etiqueta}: cada elemento de {campo} lleva dos o más columnas distintas")
                    continue
                faltan = [x for x in cols if x.lower() not in tipos]
                if faltan:
                    problemas.append(f"{etiqueta}: {campo} usa columnas que la tabla no tiene: {', '.join(faltan)}")
                    continue
                pesos = [_bytes_de_clave(tipos[x.lower()]) for x in cols]
                if any(p is None for p in pesos):
                    problemas.append(f"{etiqueta}: {campo} ({', '.join(cols)}) incluye una columna max o sin tipo válido; declara un largo")
                elif sum(pesos) > _MAX_CLAVE_BYTES:
                    problemas.append(f"{etiqueta}: la clave de {campo} ({', '.join(cols)}) ocupa {sum(pesos)} bytes y el máximo es {_MAX_CLAVE_BYTES}")
        if not tabla.get("operaciones_permitidas"):
            problemas.append(f"{etiqueta}: no declara operaciones_permitidas (la cuenta de la aplicación no tendría ningún permiso)")
    return problemas


def generar_script(mapeo, rol, servidor=None, base=None):
    """{"esquema", "tablas", "lecturas", "script", "sha256"}: T-SQL idempotente que crea las tablas y otorga permisos por tabla y operación.
    Con `servidor` y `base` (el destino de las tablas) suma el GRANT SELECT sobre las tablas preexistentes de esa base que el manifiesto declara.

    Supone que el esquema ya existe (lo crea el aprovisionamiento de la Mesa) y no altera tablas que ya existen. Lanza ValueError si el
    manifiesto no cumple la norma: nunca genera un script a medias."""
    problemas = revisar_tablas_a_crear(mapeo) + (revisar_lecturas(mapeo, servidor, base) if base else [])
    if problemas:
        raise ValueError("El manifiesto no cumple la norma de datos: " + "; ".join(problemas[:5]))
    if not _ROL.fullmatch(str(rol or "")):
        raise ValueError("Nombre de rol inválido")
    tablas = tablas_a_crear(mapeo)
    if not tablas:
        raise ValueError("El manifiesto no declara tablas para crear en el despliegue")
    esquema = tablas[0][0]
    lineas = [
        "-- Generado por la Mesa de Requerimientos a partir del manifiesto aprobado. No editar a mano: el hash entra en el plan de IT.",
        "SET XACT_ABORT ON;",
        "BEGIN TRANSACTION;",
        f"IF SCHEMA_ID(N'{esquema}') IS NULL THROW 50001, N'El esquema {esquema} no existe: lo crea el aprovisionamiento de la Mesa.', 1;",
        "",
    ]
    for _, tabla in tablas:
        nombre = tabla["table"]
        definiciones, indices = [], []
        claves = [c["name"] for c in tabla["columnas"] if c.get("clave_primaria") is True]
        admite_nulo = {c["name"]: not (c.get("clave_primaria") is True or c.get("nulable") is False) for c in tabla["columnas"]}
        for c in tabla["columnas"]:
            partes = [_q(c["name"]), c["tipo"]]
            if c.get("autoincremental") is True:
                partes.append("IDENTITY(1,1)")
            partes.append("NULL" if admite_nulo[c["name"]] else "NOT NULL")
            if "valor_por_defecto" in c:
                partes.append(f"CONSTRAINT {_q(_nombre_objeto('DF', nombre, [c['name']]))} DEFAULT {_literal(c['valor_por_defecto'], c['tipo'])}")
            definiciones.append("    " + " ".join(partes))
        definiciones.append(f"    CONSTRAINT {_q(_nombre_objeto('PK', nombre))} PRIMARY KEY ({', '.join(_q(k) for k in claves)})")
        # Únicos e índices. Una unicidad con columnas que admiten NULL se crea como índice único filtrado (WHERE ... IS NOT NULL): así
        # varias filas con NULL siguen siendo válidas, igual que en SQLite/ORM; una restricción UNIQUE de SQL Server solo admite un NULL.
        grupos = ([([c["name"]], True) for c in tabla["columnas"] if c.get("unico") is True]
                  + [(g["columnas"], True) for g in tabla.get("restricciones_unicas") or []]
                  + [([c["name"]], False) for c in tabla["columnas"] if c.get("indice") is True]
                  + [(g["columnas"], False) for g in tabla.get("indices") or []])
        for columnas, unico in grupos:
            llaves = ", ".join(_q(x) for x in columnas)
            if unico and not any(admite_nulo[x] for x in columnas):
                definiciones.append(f"    CONSTRAINT {_q(_nombre_objeto('UQ', nombre, columnas))} UNIQUE ({llaves})")
            else:
                filtro = (" WHERE " + " AND ".join(f"{_q(x)} IS NOT NULL" for x in columnas if admite_nulo[x])) if unico else ""
                indices.append(f"    CREATE {'UNIQUE ' if unico else ''}INDEX {_q(_nombre_objeto('UX' if unico else 'IX', nombre, columnas))} "
                               f"ON {_q(esquema)}.{_q(nombre)} ({llaves}){filtro};")
        lineas += [f"IF OBJECT_ID(N'{esquema}.{nombre}', N'U') IS NULL", "BEGIN",
                   f"    CREATE TABLE {_q(esquema)}.{_q(nombre)} (", ",\n".join(definiciones), "    );", *indices, "END;", ""]
    for _, tabla in tablas:
        for c in tabla["columnas"]:
            referencia = c.get("referencia")
            if not referencia:
                continue
            destino, columna_destino = referencia.split(".", 1)
            destino = next(t["table"] for _, t in tablas if t["table"].lower() == destino.lower())
            fk = _nombre_objeto("FK", tabla["table"], [c["name"]])
            lineas += [f"IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = N'{fk}' AND parent_object_id = OBJECT_ID(N'{esquema}.{tabla['table']}'))",
                       f"    ALTER TABLE {_q(esquema)}.{_q(tabla['table'])} ADD CONSTRAINT {_q(fk)} FOREIGN KEY ({_q(c['name'])}) "
                       f"REFERENCES {_q(esquema)}.{_q(destino)} ({_q(columna_destino)});", ""]
    for _, tabla in tablas:
        operaciones = [o for o in _OPERACIONES if o in tabla["operaciones_permitidas"]]
        if operaciones:
            lineas.append(f"GRANT {', '.join(operaciones)} ON OBJECT::{_q(esquema)}.{_q(tabla['table'])} TO {_q(rol)};")
    lecturas = sorted({(e, t["table"]) for e, t in tablas_a_leer(mapeo, servidor, base)}) if base else []
    if lecturas:
        lineas += ["", "-- Lectura (solo SELECT) de tablas que ya existen. Prospera solo si el DBA delegó el permiso sobre cada tabla a la cuenta del worker."]
        for e, t in lecturas:
            lineas += [f"IF OBJECT_ID(N'{e}.{t}') IS NULL THROW 50002, N'La tabla preexistente {e}.{t} no existe en esta base.', 1;",
                       f"GRANT SELECT ON OBJECT::{_q(e)}.{_q(t)} TO {_q(rol)};"]
    lineas += ["", "COMMIT TRANSACTION;", ""]
    script = "\n".join(lineas)
    return {"esquema": esquema, "tablas": [t["table"] for _, t in tablas], "lecturas": [f"{e}.{t}" for e, t in lecturas], "script": script,
            "sha256": hashlib.sha256(script.encode("utf-8")).hexdigest()}
