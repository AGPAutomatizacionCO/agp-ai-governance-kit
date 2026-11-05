import os
import re

from flask import Blueprint
from flask_jsonpify import jsonify

bp_base = Blueprint("base", __name__, url_prefix="/api")

_CORREO = re.compile(r"^[A-Za-z0-9._%+-]+@agpglass\.com$")


def _contacto():
    """(nombre, correo) del desarrollador funcional para la pantalla estándar sin acceso: administradores[0] de .agp/entra.yaml. Sin archivo o sin
    administrador, CONTACTO_NOMBRE / CONTACTO_CORREO del entorno (la Mesa los puede fijar al desplegar). Solo se acepta un correo @agpglass.com."""
    nombre, correo = "", ""
    try:
        import yaml

        ruta = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".agp", "entra.yaml")
        with open(ruta, encoding="utf-8") as f:
            admin = ((yaml.safe_load(f) or {}).get("administradores") or [{}])[0]
        nombre, correo = str(admin.get("nombre") or ""), str(admin.get("correo") or "")
    except Exception:
        pass
    nombre = (nombre or os.environ.get("CONTACTO_NOMBRE") or "").strip()[:80]
    correo = (correo or os.environ.get("CONTACTO_CORREO") or "").strip()
    return nombre or None, correo if _CORREO.fullmatch(correo) else None


def _roles_de_la_mesa():
    """A qué Mesa y a qué desarrollo habla la pantalla de «Configuración» (no son secretos). Solo con ROLES_DESDE_MESA=true, MESA_API_URL y MESA_ID_PROYECTO."""
    url, id_proyecto = (os.environ.get("MESA_API_URL") or "").strip().rstrip("/"), (os.environ.get("MESA_ID_PROYECTO") or "").strip()
    if os.environ.get("ROLES_DESDE_MESA", "false").lower() == "true" and url.startswith("https://") and id_proyecto:
        return {"mesaUrl": url, "idProyecto": id_proyecto}
    return None


@bp_base.get("/config")
def config_publica():
    """Configuración PÚBLICA del login para el frontend (tenant y aplicación de Entra). Sin secretos: son los mismos identificadores que
    valida la API en los tokens. Así una instancia de desarrollo usa el registro de login que le creó la Mesa y no uno escrito en el frontend."""
    from src.helpers.auth import _client_id, _tenant_id

    cliente, tenant = _client_id(), _tenant_id()
    nombre = (os.environ.get("APP_NAME") or "").strip()[:80] or None   # lo fija la Mesa al desplegar; la pantalla de login lo muestra
    contacto_nombre, contacto_correo = _contacto()
    return jsonify({"msal": {"clientId": cliente, "tenantId": tenant} if cliente and tenant else None, "appName": nombre,
                    "contactoNombre": contacto_nombre, "contactoCorreo": contacto_correo,
                    "roles": _roles_de_la_mesa()}), 200


@bp_base.get("/health")
def health_check():
    return jsonify({"msg": "API de Gobernanza AI funcionando correctamente"}), 200
