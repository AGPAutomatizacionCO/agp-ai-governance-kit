"""API PROPIA de la pantalla «Configuración de roles y secretos» (CONFIGURACION-LOCAL-ROLES-Y-SECRETOS.md). No llama a la Mesa.

    GET  /api/configuracion/estado             quién eres, perfiles, personas con acceso y qué puedes hacer
    PUT  /api/configuracion/personas           asigna o quita el perfil de una persona   {correo, perfil | null}
    GET  /api/configuracion/directorio?q=      busca personas en la vista corporativa de IT
    GET  /api/configuracion/secretos           NOMBRES de los secretos manuales permitidos (nunca valores)
    PUT  /api/configuracion/secretos/<nombre>  carga o actualiza un secreto manual propio   {valor}
    GET  /api/configuracion/actividad          últimos cambios de la auditoría

Reglas que cumple cada endpoint (no son opcionales):
  · `@require_auth` valida el token; el ACTOR es `g.user_email` (nunca un campo del cuerpo). Sin sesión: 401.
  · El permiso se VUELVE A LEER de la tabla en cada llamada administrativa (no se confía en la caché ni en el claim del token): sin permiso, 403; si no se puede confirmar, 403.
  · Los secretos: solo los nombres de `CONFIG_SECRETOS_PERMITIDOS` (lista del servidor), en el vault fijado por `CONFIG_KEY_VAULT_URL`, con `ManagedIdentityCredential`.
    Nada de SQL aprovisionado, secretos de otros desarrollos ni vault elegido por el cliente. Nunca se lee un valor (`get_secret`) ni se enumera el vault. Ni los valores ni los
    errores crudos del SDK llegan a las respuestas, los logs o la auditoría.
  · Los errores devuelven un mensaje corto y estable; el detalle técnico no sale.
Registro: `app.register_blueprint(bp_configuracion)` (junto a `bp_base`).
"""
import logging
import os
import re

from flask import Blueprint, g, jsonify, request

from src.helpers import roles_propios
from src.helpers.auth import require_auth

log = logging.getLogger(__name__)
bp_configuracion = Blueprint("configuracion", __name__, url_prefix="/api/configuracion")

_NOMBRE_SECRETO = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{0,126}$")   # nombres de Key Vault: letras, números y guiones
MAX_VALOR = 4096


def _repo():
    return roles_propios.RepoSql()


def _kv():
    """Cliente del vault FIJADO por configuración confiable. En las pruebas se reemplaza."""
    from azure.identity import ManagedIdentityCredential
    from azure.keyvault.secrets import SecretClient

    return SecretClient(vault_url=os.environ["CONFIG_KEY_VAULT_URL"], credential=ManagedIdentityCredential())


def secretos_permitidos(entorno=None):
    texto = (entorno if entorno is not None else os.environ).get("CONFIG_SECRETOS_PERMITIDOS", "")
    return [n for n in re.split(r"[,\s;]+", texto) if _NOMBRE_SECRETO.fullmatch(n)]


def _error(mensaje, codigo):
    return jsonify({"message": mensaje}), codigo


def _administra():
    """(alcance, repo) o lanza ErrorRoles 403: relee la tabla en cada llamada."""
    repo = _repo()
    alcance = roles_propios.resolver_sin_cache(roles_propios.normalizar_correo(g.user_email), repo, roles_propios.administradores_iniciales())
    if not alcance.administra:
        raise roles_propios.ErrorRoles("No tienes permiso para administrar el acceso", 403)
    return alcance, repo


def _con_permiso(vista):
    from functools import wraps

    @wraps(vista)
    def envoltura(*args, **kwargs):
        try:
            alcance, repo = _administra()
            return vista(alcance, repo, *args, **kwargs)
        except roles_propios.ErrorRoles as exc:
            return _error(str(exc), exc.codigo)
        except Exception as exc:   # SQL, vault u otro fallo: sin detalle crudo
            log.warning("configuracion: %s falló (%s)", vista.__name__, type(exc).__name__)
            return _error("No se pudo completar la operación. Intenta de nuevo.", 503)
    return envoltura


@bp_configuracion.get("/estado")
@require_auth
def estado():
    """Cualquier persona con sesión ve quién es; solo quien administra recibe las personas."""
    correo = roles_propios.normalizar_correo(g.user_email)
    alcance = roles_propios.resolver(correo, repo=_repo())
    datos = {"yo": {"correo": correo, "nivel": alcance.nivel, "perfil": alcance.perfil}, "puedeConfigurar": alcance.administra,
             "perfiles": [{"id": i, "nombre": p.nombre, "administra": p.administra} for i, p in roles_propios.PERFILES.items()]}
    if alcance.administra:
        try:
            datos["personas"] = [{"correo": c, "perfil": p} for c, p in _repo().personas()]
        except Exception as exc:
            log.warning("configuracion: no se pudo listar personas (%s)", type(exc).__name__)
            return _error("No se pudo leer la lista de personas. Intenta de nuevo.", 503)
        datos["administradoresIniciales"] = sorted(roles_propios.administradores_iniciales())
    return jsonify({"data": datos})


@bp_configuracion.put("/personas")
@require_auth
@_con_permiso
def asignar(alcance, repo):
    cuerpo = request.get_json(silent=True) or {}
    perfil = cuerpo.get("perfil")
    if perfil is not None and not isinstance(perfil, str):
        return _error("Perfil inválido", 400)
    # El actor es SIEMPRE el del token: lo que venga en el cuerpo (`actor`, `rol`…) se ignora.
    anterior = roles_propios.asignar(g.user_email, cuerpo.get("correo"), perfil, repo=repo)
    return jsonify({"data": {"correo": roles_propios.normalizar_correo(cuerpo.get("correo")), "perfilAnterior": anterior, "perfilNuevo": perfil}})


@bp_configuracion.get("/directorio")
@require_auth
@_con_permiso
def directorio(alcance, repo):
    q = (request.args.get("q") or "").strip()
    if len(q) < 2:
        return jsonify({"data": []})
    return jsonify({"data": repo.buscar_usuarios(q)})


@bp_configuracion.get("/actividad")
@require_auth
@_con_permiso
def actividad(alcance, repo):
    return jsonify({"data": repo.auditoria()})


@bp_configuracion.get("/secretos")
@require_auth
@_con_permiso
def secretos(alcance, repo):
    """Solo NOMBRES permitidos. Un nombre declarado no prueba que el secreto exista: no se consulta el vault para decirlo."""
    return jsonify({"data": {"nombres": secretos_permitidos(), "puedeCargar": True}})


@bp_configuracion.put("/secretos/<nombre>")
@require_auth
@_con_permiso
def cargar_secreto(alcance, repo, nombre):
    if nombre not in secretos_permitidos():
        return _error("Ese secreto no se gestiona desde esta pantalla", 403)
    valor = (request.get_json(silent=True) or {}).get("valor")
    if not isinstance(valor, str) or not valor or len(valor) > MAX_VALOR:
        return _error("Valor inválido", 400)
    actor = roles_propios.normalizar_correo(g.user_email)
    try:
        _kv().set_secret(nombre, valor)
    except Exception as exc:   # el SDK puede traer el cuerpo de la petición en el mensaje: solo el tipo
        log.warning("configuracion: no se pudo cargar el secreto %s (%s)", nombre, type(exc).__name__)
        _registrar(repo, actor, f"secreto:{nombre}", "fallido")
        return _error("No se pudo guardar el secreto. Intenta de nuevo.", 503)
    parcial = not _registrar(repo, actor, f"secreto:{nombre}", "aplicado")
    cuerpo = {"data": {"nombre": nombre, "guardado": True}}
    if parcial:   # SQL y Key Vault no comparten transacción: se dice el estado parcial, no se repite a ciegas
        cuerpo["data"]["auditoria"] = "pendiente"
        cuerpo["message"] = "El secreto se guardó, pero no se pudo registrar en la auditoría. Revisa el registro del vault antes de repetir."
    return jsonify(cuerpo)


def _registrar(repo, actor, destinatario, resultado):
    try:
        repo.registrar(actor, destinatario, resultado)
        return True
    except Exception as exc:
        log.warning("configuracion: no se pudo auditar (%s)", type(exc).__name__)
        return False
