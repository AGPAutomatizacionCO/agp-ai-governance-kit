"""Sirve la página puente del login con MSAL 5: GET /auth/redirect (OBLIGATORIOS-DEL-DESARROLLO.md §6).

El popup de Microsoft vuelve a esta ruta y la página solo entrega la respuesta a la ventana principal. Debe ser el HTML real de la compilación
(`auth/redirect.html`), NUNCA el `index.html` de la aplicación: con el fallback de la SPA el popup recarga la pantalla de login y el acceso no se completa.
Regístralo ANTES del fallback que sirve la SPA: `app.register_blueprint(bp_retorno_msal)`.

Carpeta de la compilación: `FRONTEND_DIST` o, por defecto, `backend/frontend_dist` (donde el Dockerfile copia `dist/`).
"""
import os
from pathlib import Path

from flask import Blueprint, abort, send_file

bp_retorno_msal = Blueprint("retorno_msal", __name__)


def _carpeta_compilada():
    return Path(os.environ.get("FRONTEND_DIST") or Path(__file__).resolve().parents[2] / "frontend_dist")


@bp_retorno_msal.get("/auth/redirect")
def pagina_puente():
    pagina = _carpeta_compilada() / "auth" / "redirect.html"
    if not pagina.is_file():
        abort(404, description="Falta la página de retorno de Microsoft (auth/redirect.html): revisa la compilación del frontend.")
    respuesta = send_file(pagina, mimetype="text/html")
    respuesta.headers["Cache-Control"] = "no-store"     # sin Cross-Origin-Opener-Policy: con ese encabezado el popup pierde la ventana que lo abrió
    return respuesta
