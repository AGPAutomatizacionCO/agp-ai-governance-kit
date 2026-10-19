import time
from functools import wraps
from os import getenv

import jwt
import requests
from flask import g, jsonify, request

_JWKS_TTL_SECONDS = 3600
_jwks_cache = {"keys": None, "fetched_at": 0}


def _tenant_id():
    # No usar AZURE_TENANT_ID: azure-identity (DefaultAzureCredential, usado en
    # azure_secrets.py para Key Vault) también lee esa variable, y en App Service
    # pisa la resolución de la Managed Identity.
    return getenv("MSAL_TENANT_ID") or getenv("JWT_TENANT_ID")


def _client_id():
    # Mismo motivo que _tenant_id(): evitar AZURE_CLIENT_ID. En una instancia de desarrollo, la Mesa registra una aplicación de login propia y
    # la entrega en MSAL_CLIENT_ID (referencia a Key Vault): es la que firma los tokens de esa instancia. Sin ella, rige JWT_CLIENT_ID.
    return getenv("MSAL_CLIENT_ID") or getenv("JWT_CLIENT_ID")


def _fetch_jwks():
    url = f"https://login.microsoftonline.com/{_tenant_id()}/discovery/v2.0/keys"
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    _jwks_cache["keys"] = response.json()["keys"]
    _jwks_cache["fetched_at"] = time.time()


def _find_key(kid):
    for key in _jwks_cache["keys"] or []:
        if key["kid"] == kid:
            return key
    return None


def _get_signing_key(kid):
    now = time.time()
    if not _jwks_cache["keys"] or now - _jwks_cache["fetched_at"] > _JWKS_TTL_SECONDS:
        _fetch_jwks()

    key = _find_key(kid)
    if key is None:
        # Azure AD puede rotar las llaves dentro de la ventana de caché de 1h: si el kid no
        # aparece, se refresca una vez antes de rendirse en vez de esperar al vencimiento del
        # TTL (si no, un token perfectamente válido se rechaza como "expirado" hasta la
        # siguiente hora).
        _fetch_jwks()
        key = _find_key(kid)

    if key is None:
        raise ValueError("No se encontró la llave de firma indicada en el token")

    return jwt.algorithms.RSAAlgorithm.from_jwk(key)


def _decode_token(token):
    header = jwt.get_unverified_header(token)
    signing_key = _get_signing_key(header["kid"])

    claims = jwt.decode(token, key=signing_key, algorithms=["RS256"], audience=_client_id())

    expected_issuer = f"https://login.microsoftonline.com/{_tenant_id()}/v2.0"
    if claims.get("iss") != expected_issuer:
        raise ValueError(f"Emisor del token no reconocido: {claims.get('iss')}")

    return claims


def _auth_desactivada_para_desarrollo():
    """DISABLE_AUTH=true solo vale en el equipo local. Dentro de Azure App Service (WEBSITE_SITE_NAME) se ignora: una variable mal puesta no
    puede dejar la API sin autenticación."""
    return getenv("DISABLE_AUTH", "false").lower() == "true" and not getenv("WEBSITE_SITE_NAME")


def require_auth(view_func):
    """Exige un id_token de MSAL válido en Authorization: Bearer <token> y expone
    el correo del usuario en g.user_email para el resto de la vista.

    Con DISABLE_AUTH=true se salta la validación y usa DEV_USER_EMAIL — solo para
    correr en local sin pasar por el login real de MSAL (se ignora dentro de Azure)."""

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if _auth_desactivada_para_desarrollo():
            g.user_email = getenv("DEV_USER_EMAIL", "dev@local")
            g.user_name = getenv("DEV_USER_NAME", "dev")
            return view_func(*args, **kwargs)

        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return jsonify({"message": "Falta el token de autenticación"}), 401

        token = header.split(" ", 1)[1]
        try:
            claims = _decode_token(token)
        except Exception as e:
            return jsonify({"message": "Token inválido o expirado", "data": str(e)}), 401

        user_email = claims.get("preferred_username") or claims.get("email") or claims.get("upn")
        if not user_email:
            return jsonify({"message": "El token no contiene un correo identificable"}), 401

        g.user_email = user_email
        g.user_name = claims.get("name")

        return view_func(*args, **kwargs)

    return wrapper
