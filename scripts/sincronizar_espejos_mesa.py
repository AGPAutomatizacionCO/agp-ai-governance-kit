"""Regenera (o comprueba) los espejos `agpctl/mesa_datos_*.py` a partir del código de la Mesa de Requerimientos.

La Mesa manda: son las reglas con las que valida el plan que aprueba IT. El kit las copia para que el desarrollador y su agente las apliquen ANTES de pedir el
despliegue (`python -m agpctl datos check`). Un espejo es el archivo de la Mesa **sin cambios de lógica**: solo se adaptan los imports.

    python scripts/sincronizar_espejos_mesa.py --mesa <ruta al repo de la Mesa> [--ref origin/main]            # regenera
    python scripts/sincronizar_espejos_mesa.py --mesa <ruta al repo de la Mesa> [--ref origin/main] --check    # no escribe; falla si hay deriva

Cada espejo empieza con un encabezado de comentarios (commit de la Mesa del que sale y huella de su cuerpo). `tests/test_espejos_mesa.py` comprueba que nadie lo
editó a mano y, con `AGP_MESA_PATH` apuntando a un repo de la Mesa, que no hay deriva frente a su `main`.
"""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGEN = "backend/src/helpers/{}.py"
ESPEJOS = {
    "datos_ddl": "mesa_datos_ddl",
    "datos_permisos": "mesa_datos_permisos",
    "datos_plan": "mesa_datos_plan",
}
# Los únicos cambios permitidos respecto de la Mesa: cómo se importan entre sí.
IMPORTS = {
    "from src.helpers import datos_ddl\n": "from agpctl import mesa_datos_ddl as datos_ddl\n",
    "from src.helpers.datos_permisos import ": "from agpctl.mesa_datos_permisos import ",
}
MARCA_INICIO = "# ===== ESPEJO DE LA MESA: inicio del código (no editar a mano; regenerar con scripts/sincronizar_espejos_mesa.py) =====\n"
ENCABEZADO = (
    "# ESPEJO de la Mesa de Requerimientos ({origen}), copiado sin cambios de lógica: solo se adaptan los imports.\n"
    "# La Mesa es la fuente de verdad: son las mismas reglas con las que valida el plan antes de que IT apruebe.\n"
    "# Si la Mesa cambia una regla, se regenera con `python scripts/sincronizar_espejos_mesa.py --mesa <repo de la Mesa>`; no se edita a mano.\n"
    "# ESPEJO-COMMIT: {commit}\n"
    "# ESPEJO-SHA256: {huella}\n"
)


def adaptar(texto: str) -> str:
    """El código de la Mesa con los imports del kit."""
    for original, adaptado in IMPORTS.items():
        texto = texto.replace(original, adaptado)
    return texto


def huella(cuerpo: str) -> str:
    return hashlib.sha256(cuerpo.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def construir(origen: str, commit: str, codigo_mesa: str) -> str:
    cuerpo = adaptar(codigo_mesa.replace("\r\n", "\n"))
    return ENCABEZADO.format(origen=origen, commit=commit, huella=huella(cuerpo)) + MARCA_INICIO + cuerpo


def partir(espejo: str) -> tuple[str, str]:
    """(encabezado, cuerpo) de un espejo ya generado. Lanza ValueError si no trae la marca."""
    espejo = espejo.replace("\r\n", "\n")
    if MARCA_INICIO not in espejo:
        raise ValueError("el espejo no trae la marca de inicio del código")
    encabezado, cuerpo = espejo.split(MARCA_INICIO, 1)
    return encabezado, cuerpo


def _git(mesa: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(mesa), *args], check=True, capture_output=True, text=True, encoding="utf-8").stdout


def leer_de_la_mesa(mesa: Path, ref: str) -> tuple[str, dict[str, str]]:
    """(commit, {nombre_de_origen: código}) tal como estaba en `ref` de la Mesa."""
    commit = _git(mesa, "rev-parse", ref).strip()
    return commit, {nombre: _git(mesa, "show", f"{commit}:{ORIGEN.format(nombre)}") for nombre in ESPEJOS}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--mesa", required=True, help="ruta a un clon del repositorio de la Mesa")
    parser.add_argument("--ref", default="origin/main", help="rama o commit de la Mesa (por defecto origin/main)")
    parser.add_argument("--check", action="store_true", help="no escribe: falla si algún espejo difiere de la Mesa")
    args = parser.parse_args()
    mesa = Path(args.mesa)
    try:
        commit, codigos = leer_de_la_mesa(mesa, args.ref)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"No se pudo leer la Mesa ({args.ref}): {exc}", file=sys.stderr)
        return 2
    deriva = []
    for origen, destino in ESPEJOS.items():
        ruta = ROOT / "agpctl" / f"{destino}.py"
        nuevo = construir(ORIGEN.format(origen), commit, codigos[origen])
        actual = ruta.read_text(encoding="utf-8").replace("\r\n", "\n") if ruta.exists() else ""
        if actual != nuevo:
            deriva.append(destino)
            if not args.check:
                ruta.write_text(nuevo, encoding="utf-8", newline="\n")
    if args.check:
        if deriva:
            print("Deriva frente a la Mesa en: " + ", ".join(deriva), file=sys.stderr)
            return 1
        print(f"Los espejos coinciden con la Mesa ({commit[:7]}).")
        return 0
    print(("Regenerados: " + ", ".join(deriva)) if deriva else "Sin cambios: los espejos ya coinciden.", f"(Mesa {commit[:7]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
