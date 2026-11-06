"""Rol y permisos de quien inicia sesión, leídos de la Mesa por el túnel de roles (`GET /api/roles-app/<id>/mios`).

La Mesa es la fuente de verdad de los roles: quien administra los asigna en «Configuración de roles y secretos» (pantalla estándar) y la Mesa los valida, aplica y audita.
**Este módulo solo LEE**: pregunta por la persona con el MISMO `id_token` de Microsoft del login. La app no crea ni escribe tablas de roles, no llama a Graph para roles y no
depende de tablas propias de roles: solo usa el túnel (contrato en `CONTRATO-TUNEL-ROLES.md`). Hoy los roles viven en tablas centrales de la Mesa; el modelo de tres tablas por
desarrollo es el destino de la spec 018 y está pendiente: no hay que leerlas directamente.

Se activa con tres variables (no son secretos; se declaran en `env` de `.agp/runtime.yaml`):
    ROLES_DESDE_MESA=true   MESA_API_URL=https://…   MESA_ID_PROYECTO=<id del desarrollo en la Mesa>

Reglas (las del piloto de SAC):
  · Falla cerrada: si la Mesa no responde y no hay nada guardado, la persona entra con la vista general (solo lectura), salvo el rol `Admin` del token de Microsoft. Nunca más de lo que dijo la Mesa.
  · Caché corta (TTL_S) para no preguntar en cada llamada; con la Mesa caída se reutiliza lo último que dijo mientras dure una sesión (MAX_VIGENCIA_S).
  · Timeout de 15 s: con reglas por departamento de Microsoft la Mesa también consulta a Graph y la primera llamada tras un rato sin uso puede tardar.
  · Local (fuera de Azure) y sin la Mesa activa: `ROLES_LOCAL_NIVEL=admin|usuario|general` (por defecto `general`). Dentro de Azure esa variable se ignora.

Uso:
    from src.helpers import roles_mesa
    alcance = roles_mesa.resolver(g.user_email, id_token, roles_entra=claims.get("roles"))
    if alcance.nivel in ("global", "admin"): ...                      # administra
    if "estado-pedidos" in alcance.modulos: ...                       # puede abrir esa vista
    if "estado-pedidos.exportar" in alcance.funciones: ...            # puede hacer esa acción
"""
import logging
import os
import threading
import time
from dataclasses import dataclass

log = logging.getLogger(__name__)

TTL_S = 60                  # cuánto se reutiliza lo que respondió la Mesa antes de volver a preguntarle (con token)
MAX_VIGENCIA_S = 8 * 3600   # sin token (cookie de sesión) se usa lo último que dijo la Mesa, hasta la duración de la sesión
TIMEOUT_S = 15
ROL_ADMIN_ENTRA = "Admin"
NIVELES = ("global", "admin", "usuario", "general")


@dataclass(frozen=True)
class Alcance:
    """Qué es la persona en la app. `nivel`: global (administrador principal), admin (secundario), usuario (tiene rol) o general (sin rol: vista general)."""
    nivel: str
    perfil: str = ""
    modulos: frozenset = frozenset()     # vistas que puede abrir (ids de `permisos` de ROLES.md)
    funciones: frozenset = frozenset()   # acciones dentro de ellas (`<modulo>.<accion>`)
    de_la_mesa: bool = True              # False: se usó el respaldo (la Mesa no respondió o no está activa)

    @property
    def administra(self) -> bool:
        return self.nivel in ("global", "admin")


_cache: dict = {}
_cerrojo = threading.Lock()


def activo() -> bool:
    """La gestión de roles desde la Mesa está encendida y bien configurada (la URL debe ser https)."""
    return (os.getenv("ROLES_DESDE_MESA", "false").strip().lower() == "true"
            and (os.getenv("MESA_API_URL") or "").strip().lower().startswith("https://")
            and bool((os.getenv("MESA_ID_PROYECTO") or "").strip()))


class MesaNoDisponible(Exception):
    pass


def _http_get(url: str, headers: dict, timeout: int):
    import requests   # la plantilla de auth ya lo trae (backend/src/helpers/auth.py)

    return requests.get(url, headers=headers, timeout=timeout)


def consultar(id_token: str, http_get=_http_get) -> dict:
    """`data` de `GET /api/roles-app/<id>/mios`. Lanza MesaNoDisponible si la Mesa no responde 200 con datos."""
    url = f"{os.environ['MESA_API_URL'].strip().rstrip('/')}/api/roles-app/{os.environ['MESA_ID_PROYECTO'].strip()}/mios"
    try:
        r = http_get(url, {"Authorization": f"Bearer {id_token}"}, TIMEOUT_S)
    except Exception as exc:   # red, DNS, timeout: no se muestra el detalle
        raise MesaNoDisponible(f"sin conexión con la Mesa ({type(exc).__name__})") from exc
    if r.status_code != 200:
        try:
            motivo = str((r.json() or {}).get("message") or "")[:200]
        except Exception:   # cuerpo vacío o que no es JSON: basta el código
            motivo = ""
        raise MesaNoDisponible(f"la Mesa respondió {r.status_code}" + (f": {motivo}" if motivo else ""))
    try:
        datos = (r.json() or {}).get("data")
    except Exception as exc:   # 200 con un cuerpo que no es JSON (un proxy, una página de error)
        raise MesaNoDisponible("respuesta de la Mesa que no es JSON") from exc
    if not isinstance(datos, dict):
        raise MesaNoDisponible("respuesta de la Mesa sin datos")
    return datos


def alcance_desde_respuesta(datos: dict) -> Alcance:
    """Traduce lo que respondió la Mesa. Pura. Un administrador recibe todo el catálogo de permisos (la Mesa ya lo suma en `permisos`)."""
    nivel = str(datos.get("nivel") or "")
    if datos.get("adminGlobal"):
        nivel = "global"
    perfil = datos.get("perfil") if isinstance(datos.get("perfil"), dict) else {}
    permisos = datos.get("permisos") if isinstance(datos.get("permisos"), dict) else {}
    modulos = frozenset(str(m) for m in permisos.get("modulos") or [])
    funciones = frozenset(str(f) for f in permisos.get("funciones") or [])
    if nivel in ("global", "admin"):
        return Alcance(nivel, str(perfil.get("id") or ""), modulos, funciones)
    if perfil.get("general") or not perfil:
        return Alcance("general", str(perfil.get("id") or ""), modulos, funciones)
    return Alcance("usuario", str(perfil.get("id") or ""), modulos, funciones)


def respaldo(roles_entra=None) -> Alcance:
    """La Mesa no responde y no hay nada guardado: el rol `Admin` del token de Microsoft sigue mandando; todos los demás, vista general (solo lectura)."""
    es_admin = isinstance(roles_entra, list) and ROL_ADMIN_ENTRA in roles_entra
    return Alcance("global" if es_admin else "general", de_la_mesa=False)


def alcance_local() -> Alcance:
    """Sin la Mesa activa. En Azure: el respaldo. En el equipo local: `ROLES_LOCAL_NIVEL` (admin, usuario o general; por defecto general)."""
    if os.getenv("WEBSITE_SITE_NAME"):
        return respaldo()
    pedido = (os.getenv("ROLES_LOCAL_NIVEL") or "general").strip().lower()
    return Alcance({"admin": "global", "usuario": "usuario"}.get(pedido, "general"), de_la_mesa=False)


def resolver(correo: str, id_token=None, roles_entra=None, ahora=time.time, http_get=_http_get) -> Alcance:
    """Alcance de la persona. Con `id_token`: pregunta a la Mesa si lo guardado tiene más de TTL_S; si la Mesa falla, usa lo último que dijo (si hay) o el respaldo.
    Sin `id_token` (cookie de sesión del servidor): lo último que dijo la Mesa mientras dure la sesión, o el respaldo."""
    if not activo():
        return alcance_local()
    clave = (correo or "").strip().lower()
    with _cerrojo:
        guardado = _cache.get(clave)
    ahora_s = ahora()
    if guardado and (ahora_s - guardado[0] < TTL_S or (not id_token and ahora_s - guardado[0] < MAX_VIGENCIA_S)):
        return guardado[1]
    if id_token:
        try:
            alcance = alcance_desde_respuesta(consultar(id_token, http_get))
            with _cerrojo:
                _cache[clave] = (ahora_s, alcance)
            return alcance
        except MesaNoDisponible as exc:
            log.warning("roles_mesa: %s; se usa %s", exc, "lo último que dijo la Mesa" if guardado else "el respaldo (vista general)")
    if guardado and ahora_s - guardado[0] < MAX_VIGENCIA_S:
        return guardado[1]
    return respaldo(roles_entra)


def olvidar(correo=None) -> None:
    """Borra lo guardado (de una persona o de todas): al cerrar sesión y en las pruebas."""
    with _cerrojo:
        if correo is None:
            _cache.clear()
        else:
            _cache.pop((correo or "").strip().lower(), None)
