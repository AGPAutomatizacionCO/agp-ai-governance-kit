import os

from flask import Blueprint
from flask_jsonpify import jsonify

bp_base = Blueprint("base", __name__, url_prefix="/api")


@bp_base.get("/config")
def config_publica():
    """Configuración PÚBLICA del login para el frontend (tenant y aplicación de Entra). Sin secretos: son los mismos identificadores que
    valida la API en los tokens. Así una instancia de desarrollo usa el registro de login que le creó la Mesa y no uno escrito en el frontend."""
    from src.helpers.auth import _client_id, _tenant_id

    cliente, tenant = _client_id(), _tenant_id()
    nombre = (os.environ.get("APP_NAME") or "").strip()[:80] or None   # lo fija la Mesa al desplegar; la pantalla de login lo muestra
    return jsonify({"msal": {"clientId": cliente, "tenantId": tenant} if cliente and tenant else None, "appName": nombre}), 200


@bp_base.get("/health")
def health_check():
    return jsonify({"msg": "API de Gobernanza AI funcionando correctamente"}), 200
