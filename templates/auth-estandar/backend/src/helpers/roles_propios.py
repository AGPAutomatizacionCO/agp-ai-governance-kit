"""Roles PROPIOS del desarrollo: quién entra y con qué perfil, guardado en DOS tablas del esquema del propio desarrollo (personas y auditoría).

Guía: CONFIGURACION-LOCAL-ROLES-Y-SECRETOS.md. Reemplaza al túnel heredado (`templates/auth-estandar-tunel-heredado/`): la autorización se decide aquí, con las tablas del
desarrollo, sin llamar a la Mesa en cada login ni en cada cambio.

Qué decide y qué NO decide
  · La identidad la prueba el token de Microsoft que valida `auth.py` (`g.user_email`). El navegador nunca dice quién es administrador ni quién hace el cambio:
    el ACTOR siempre sale del token, nunca del cuerpo de la petición.
  · La autorización sale de la tabla de personas y de los administradores iniciales (`CONFIG_ADMINISTRADORES_INICIALES`, correos separados por coma, cargados por
    configuración confiable). El claim `roles` de un token viejo NO autoriza: se lee la tabla cada vez, así que revocar a alguien surte efecto en la siguiente llamada.
  · Falla cerrada: si la base no responde, la persona queda en «general» (vista general, sin permisos de administración), nunca con más de lo que dice la tabla.

Tablas (se declaran en `ai/outputs/data-access-manifest.json`, ver `examples/data-access-manifest.roles-propios.valid.json`; la plantilla de nombres está en NOMENCLATURA-DATOS.md):
    <esquema>.<tabla de personas>    Id (int, identidad) · Correo (único, minúsculas) · Perfil
    <esquema>.<tabla de auditoría>   Id (int, identidad) · Fecha · Actor · Destinatario · PerfilAnterior · PerfilNuevo · Resultado
  Permisos mínimos: personas SELECT/INSERT/UPDATE/DELETE y auditoría SELECT/INSERT (la auditoría nunca se edita ni se borra). Los nombres vienen de variables de entorno
  (no son secretos; se declaran en `env` de `.agp/runtime.yaml`):
    ROLES_PROPIOS_ESQUEMA   ROLES_PROPIOS_TABLA_PERSONAS   ROLES_PROPIOS_TABLA_AUDITORIA   CONFIG_ADMINISTRADORES_INICIALES
  No se usan los nombres `_Roles`, `_RolesDatos` y `_RolesPersonas`: están reservados para el modo heredado de la Mesa.

Perfiles: el catálogo `PERFILES` es el del desarrollo (la matriz REAL de vistas y acciones). La pantalla solo asigna esos perfiles; no inventa permisos que la API ignore.

Uso:
    from src.helpers import roles_propios
    alcance = roles_propios.resolver(g.user_email)
    if alcance.administra: ...                              # puede abrir Configuración y asignar
    if "estado-pedidos" in alcance.modulos: ...             # puede abrir esa vista
    if "estado-pedidos.exportar" in alcance.funciones: ...  # puede hacer esa acción
"""
import logging
import os
import re
import threading
import time
from dataclasses import dataclass

log = logging.getLogger(__name__)

NIVELES = ("global", "admin", "usuario", "general")
_CORREO = re.compile(r"^[a-z0-9._%+-]+@agpglass\.com$")
_IDENT = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,127}$")
TTL_S = 30   # caché corta por persona; `olvidar` la vacía al cambiar un perfil. Con varias instancias cada una vuelve a leer la tabla en TTL_S como máximo.


@dataclass(frozen=True)
class Perfil:
    """Un perfil del desarrollo: si administra la configuración y qué vistas (módulos) y acciones (funciones `<módulo>.<acción>`) abre."""
    nombre: str
    administra: bool = False
    modulos: frozenset = frozenset()
    funciones: frozenset = frozenset()


# EDITAR: la matriz real del desarrollo. Los ids son los que guarda la tabla de personas. El perfil que administra es el único que abre «Configuración».
PERFILES = {
    "administrador": Perfil("Administrador", administra=True),
    "consulta": Perfil("Consulta"),
}


@dataclass(frozen=True)
class Alcance:
    """Qué es la persona en la app. `nivel`: global (administrador inicial, de configuración), admin (perfil que administra), usuario (tiene perfil) o general (sin perfil)."""
    nivel: str
    perfil: str = ""
    modulos: frozenset = frozenset()
    funciones: frozenset = frozenset()
    de_la_tabla: bool = True   # False: no se pudo leer la tabla y se aplicó la falla cerrada

    @property
    def administra(self) -> bool:
        return self.nivel in ("global", "admin")


class ErrorRoles(Exception):
    """Cambio rechazado. `codigo`: 400 petición inválida, 403 sin permiso o regla de protección, 409 conflicto, 503 la base no responde."""

    def __init__(self, mensaje, codigo=400):
        super().__init__(mensaje)
        self.codigo = codigo


def normalizar_correo(correo) -> str:
    return str(correo or "").strip().lower()


def administradores_iniciales(entorno=None) -> frozenset:
    texto = (entorno if entorno is not None else os.environ).get("CONFIG_ADMINISTRADORES_INICIALES", "")
    return frozenset(c for c in (normalizar_correo(p) for p in re.split(r"[,\s;]+", texto)) if _CORREO.fullmatch(c))


def _ident(valor, nombre):
    if not _IDENT.fullmatch(str(valor or "")):
        raise ErrorRoles(f"Falta o es inválida la configuración {nombre}", 503)
    return str(valor)


class RepoSql:
    """Acceso SQL a las dos tablas. `abrir()` devuelve una conexión DB-API con autocommit APAGADO (pyodbc por defecto, ver `abrir_conexion`). Todo valor viaja como
    parámetro (`?`); solo los nombres de esquema y tablas, validados como identificadores, se escriben en el SQL."""

    def __init__(self, abrir=None, entorno=None, abrir_directorio=None):
        self._abrir_directorio = abrir_directorio
        env = entorno if entorno is not None else os.environ
        self._abrir = abrir or abrir_conexion
        esquema = _ident(env.get("ROLES_PROPIOS_ESQUEMA"), "ROLES_PROPIOS_ESQUEMA")
        self._personas = f"[{esquema}].[{_ident(env.get('ROLES_PROPIOS_TABLA_PERSONAS'), 'ROLES_PROPIOS_TABLA_PERSONAS')}]"
        self._auditoria = f"[{esquema}].[{_ident(env.get('ROLES_PROPIOS_TABLA_AUDITORIA'), 'ROLES_PROPIOS_TABLA_AUDITORIA')}]"

    def perfil_de(self, correo):
        con = self._abrir()
        try:
            fila = con.cursor().execute(f"SELECT Perfil FROM {self._personas} WHERE Correo = ?", correo).fetchone()
            return fila[0] if fila else None
        finally:
            con.close()

    def personas(self):
        con = self._abrir()
        try:
            return [(f[0], f[1]) for f in con.cursor().execute(f"SELECT Correo, Perfil FROM {self._personas} ORDER BY Correo").fetchall()]
        finally:
            con.close()

    def auditoria(self, limite=100):
        con = self._abrir()
        try:
            filas = con.cursor().execute(
                f"SELECT TOP (?) Fecha, Actor, Destinatario, PerfilAnterior, PerfilNuevo, Resultado FROM {self._auditoria} ORDER BY Id DESC", int(limite)).fetchall()
            return [{"fecha": str(f[0]), "actor": f[1], "destinatario": f[2], "perfilAnterior": f[3], "perfilNuevo": f[4], "resultado": f[5]} for f in filas]
        finally:
            con.close()

    def registrar(self, actor, destinatario, resultado):
        """Una línea de auditoría que no cambia perfiles (cargar un secreto, un intento rechazado). Nunca lleva valores."""
        con = self._abrir()
        try:
            con.cursor().execute(f"INSERT INTO {self._auditoria} (Fecha, Actor, Destinatario, PerfilAnterior, PerfilNuevo, Resultado) VALUES (SYSUTCDATETIME(), ?, ?, NULL, NULL, ?)",
                                 actor, destinatario, resultado)
            con.commit()
        except Exception:
            try:
                con.rollback()
            except Exception:
                pass
            raise
        finally:
            con.close()

    def buscar_usuarios(self, texto, limite=20):
        """Personas de la vista corporativa de IT (`corporacion.vw_UsuariosCorporacion`: IDUsuario, Correo, Nombre, Area, Cargo), declarada `preexistente` y solo SELECT en el
        manifiesto. Si la vista está en otra base, el repositorio recibe `abrir_directorio` con la conexión de esa base."""
        patron = "%" + re.sub(r"([%_\\[])", lambda m: "\\" + m.group(1), str(texto or "").strip()[:60]) + "%"
        con = (self._abrir_directorio or self._abrir)()
        try:
            filas = con.cursor().execute(
                "SELECT TOP (?) Correo, Nombre, Area, Cargo FROM [corporacion].[vw_UsuariosCorporacion] WHERE Correo LIKE ? ESCAPE '\\' OR Nombre LIKE ? ESCAPE '\\' ORDER BY Nombre",
                int(limite), patron, patron).fetchall()
            return [{"correo": normalizar_correo(f[0]), "nombre": f[1], "area": f[2], "cargo": f[3]} for f in filas]
        finally:
            con.close()

    def aplicar(self, actor, destinatario, perfil_nuevo, validar):
        """Cambia el perfil y deja la auditoría en UNA transacción. `validar(perfil_anterior, personas)` corre dentro de la transacción, con lo que hay en la tabla
        AHORA, y lanza ErrorRoles si no se debe aplicar. Si cualquier paso falla se hace rollback: no queda un cambio sin su auditoría ni al revés."""
        con = self._abrir()
        try:
            cur = con.cursor()
            anterior = cur.execute(f"SELECT Perfil FROM {self._personas} WHERE Correo = ?", destinatario).fetchone()
            anterior = anterior[0] if anterior else None
            personas = [(f[0], f[1]) for f in cur.execute(f"SELECT Correo, Perfil FROM {self._personas}").fetchall()]
            validar(anterior, personas)
            if perfil_nuevo is None:
                cur.execute(f"DELETE FROM {self._personas} WHERE Correo = ?", destinatario)
            elif anterior is None:
                cur.execute(f"INSERT INTO {self._personas} (Correo, Perfil) VALUES (?, ?)", destinatario, perfil_nuevo)
            else:
                cur.execute(f"UPDATE {self._personas} SET Perfil = ? WHERE Correo = ?", perfil_nuevo, destinatario)
            cur.execute(f"INSERT INTO {self._auditoria} (Fecha, Actor, Destinatario, PerfilAnterior, PerfilNuevo, Resultado) VALUES (SYSUTCDATETIME(), ?, ?, ?, ?, ?)",
                        actor, destinatario, anterior, perfil_nuevo, "aplicado")
            con.commit()
            return anterior
        except Exception:
            try:
                con.rollback()
            except Exception:   # la conexión ya cayó: el servidor revierte lo no confirmado
                pass
            raise
        finally:
            con.close()


def abrir_conexion():
    """Conexión por defecto (pyodbc, Azure SQL). Usa las variables de conexión que declara el `runtime.yaml` del desarrollo (SQL_SERVER, SQL_DATABASE, SQL_USER y el
    secreto SQL_PASSWORD, con los nombres que deje el aprovisionamiento). Sin autocommit. En las pruebas se pasa `abrir` y esto no corre."""
    import pyodbc   # solo con la base real

    cadena = (f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={os.environ['SQL_SERVER']};DATABASE={os.environ['SQL_DATABASE']};"
              f"UID={os.environ['SQL_USER']};PWD={os.environ['SQL_PASSWORD']};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=15")
    return pyodbc.connect(cadena, autocommit=False)


_cache: dict = {}
_cerrojo = threading.Lock()


def olvidar(correo=None) -> None:
    """Vacía la caché (de una persona o de todas): al cambiar un perfil y en las pruebas."""
    with _cerrojo:
        if correo is None:
            _cache.clear()
        else:
            _cache.pop(normalizar_correo(correo), None)


def _alcance_de(perfil_id, correo, iniciales):
    if correo in iniciales:
        return Alcance("global", perfil_id or "")
    perfil = PERFILES.get(perfil_id or "")
    if perfil is None:   # sin fila o con un perfil que ya no existe: vista general, nunca permisos implícitos
        return Alcance("general")
    return Alcance("admin" if perfil.administra else "usuario", perfil_id, perfil.modulos, perfil.funciones)


def resolver(correo, repo=None, entorno=None, ahora=time.time) -> Alcance:
    """Alcance de la persona que prueba el token. Lee la tabla (con caché corta). Si no puede leerla: falla cerrada (general, `de_la_tabla=False`); los administradores
    iniciales conservan su acceso para poder corregir la configuración."""
    correo = normalizar_correo(correo)
    iniciales = administradores_iniciales(entorno)
    with _cerrojo:
        guardado = _cache.get(correo)
    if guardado and ahora() - guardado[0] < TTL_S:
        return guardado[1]
    try:
        alcance = _alcance_de((repo or RepoSql(entorno=entorno)).perfil_de(correo), correo, iniciales)
    except Exception as exc:   # base caída o mal configurada: no se muestra el detalle
        log.warning("roles_propios: no se pudo leer la tabla de personas (%s); falla cerrada", type(exc).__name__)
        return Alcance("global" if correo in iniciales else "general", de_la_tabla=False)
    with _cerrojo:
        _cache[correo] = (ahora(), alcance)
    return alcance


def asignar(actor, destinatario, perfil, repo=None, entorno=None):
    """El `actor` (correo del TOKEN, nunca del cuerpo) asigna `perfil` a `destinatario` (None = quitarle el acceso). Devuelve el perfil anterior.

    Reglas: el actor debe administrar AHORA (se vuelve a leer la tabla); correo corporativo; perfil conocido; nadie cambia su propio perfil; no se toca a un administrador
    inicial; no se deja el desarrollo sin administradores. Un perfil desconocido o una persona inexistente a quitar se rechaza sin tocar nada."""
    actor, destinatario = normalizar_correo(actor), normalizar_correo(destinatario)
    iniciales = administradores_iniciales(entorno)
    repo = repo or RepoSql(entorno=entorno)
    if not resolver_sin_cache(actor, repo, iniciales).administra:
        raise ErrorRoles("No tienes permiso para administrar el acceso", 403)
    if not _CORREO.fullmatch(destinatario):
        raise ErrorRoles("El correo debe ser corporativo (@agpglass.com)")
    if perfil is not None and perfil not in PERFILES:
        raise ErrorRoles("Perfil desconocido")
    if actor == destinatario:
        raise ErrorRoles("No puedes cambiar tu propio perfil: pídeselo a otra persona administradora", 403)
    if destinatario in iniciales:
        raise ErrorRoles("Esa persona es administradora inicial del desarrollo y no se cambia desde la pantalla", 403)

    def validar(anterior, personas):
        if perfil is None and anterior is None:
            raise ErrorRoles("Esa persona no tiene acceso asignado", 409)
        if anterior == perfil:
            raise ErrorRoles("Esa persona ya tiene ese perfil", 409)
        era_admin = anterior in PERFILES and PERFILES[anterior].administra
        sigue_admin = perfil in PERFILES and PERFILES[perfil].administra
        if era_admin and not sigue_admin:
            restantes = {c for c, p in personas if c != destinatario and p in PERFILES and PERFILES[p].administra} | set(iniciales)
            if not restantes:
                raise ErrorRoles("Debe quedar al menos una persona administradora", 403)

    anterior = repo.aplicar(actor, destinatario, perfil, validar)
    olvidar(destinatario)
    olvidar(actor)
    return anterior


def resolver_sin_cache(correo, repo, iniciales) -> Alcance:
    """Como `resolver` pero siempre lee la tabla: lo usan los endpoints administrativos (un administrador revocado no debe poder seguir actuando por una caché)."""
    try:
        return _alcance_de(repo.perfil_de(correo), correo, iniciales)
    except Exception as exc:
        log.warning("roles_propios: no se pudo confirmar el permiso (%s); falla cerrada", type(exc).__name__)
        return Alcance("global" if correo in iniciales else "general", de_la_tabla=False)
