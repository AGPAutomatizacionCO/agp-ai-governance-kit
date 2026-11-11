"""Servidor de un desarrollo con la plantilla vieja: sirve la SPA para cualquier ruta, sin página puente."""
from flask import Flask, send_from_directory

app = Flask(__name__, static_folder=None)


@app.get("/", defaults={"ruta": ""})
@app.get("/<path:ruta>")
def spa(ruta):
    return send_from_directory("frontend_dist", "index.html")
