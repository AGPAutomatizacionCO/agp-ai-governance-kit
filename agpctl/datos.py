"""`agpctl datos check`: las reglas de datos que la Mesa aplica al plan, ejecutadas ANTES de pedir el despliegue.

Solo LEE el repositorio. Revisa `ai/outputs/data-access-manifest.json` (esquema del kit + tablas a crear + lecturas de tablas
preexistentes + permisos) y que `.agp/runtime.yaml` declare la conexión de cada base que el manifiesto toca. Las reglas son las de la
Mesa (agpctl/mesa_datos_*.py, espejo de su backend): lo que aquí pasa no aparece después como «Revisar pendientes» al aprobar.

Una diferencia a propósito: la Mesa no exige la conexión declarada de la base donde ella crea las tablas propias (AGP_DATOS_SQL_DATABASE,
configuración suya que el repositorio no conoce). Aquí se exige para toda base con tablas preexistentes: declararla de más no estorba y
declararla de menos es justo lo que la Mesa rechazaba al aprobar.
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from agpctl import mesa_datos_ddl as ddl
from agpctl import mesa_datos_permisos as permisos
from agpctl import mesa_datos_plan as plan

MANIFIESTO = Path("ai") / "outputs" / "data-access-manifest.json"
RUNTIME = Path(".agp") / "runtime.yaml"
ESQUEMA = Path(__file__).resolve().parents[1] / "schemas" / "data-access-manifest.schema.json"


def _base_propia(mapeo):
    """(servidor, base) de la fuente donde el desarrollo crea sus tablas, o (None, None) si no crea ninguna."""
    for fuente in mapeo.get("fuentes_datos") or []:
        for esquema in fuente.get("esquemas") or []:
            if any(t.get("crear_en_despliegue") is True for t in esquema.get("tablas") or []):
                return str(fuente.get("server") or ""), str(fuente.get("database") or "")
    return None, None


def check(repo: Path) -> dict:
    repo = Path(repo)
    ruta = repo / MANIFIESTO
    if not ruta.exists():
        return {"valid": True, "issues": [], "note": f"no hay {MANIFIESTO.as_posix()}: nada que revisar"}
    try:
        mapeo = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"valid": False, "issues": [f"{MANIFIESTO.as_posix()} no es JSON válido: {exc}"]}
    esquema = json.loads(ESQUEMA.read_text(encoding="utf-8"))
    issues = [
        f"manifiesto {'/'.join(str(p) for p in e.absolute_path) or '(raíz)'}: {e.message[:200]}"
        for e in sorted(Draft202012Validator(esquema).iter_errors(mapeo), key=lambda e: [str(p) for p in e.absolute_path])
    ]
    servidor, base = _base_propia(mapeo)
    issues += ddl.revisar_tablas_a_crear(mapeo)
    if base:
        issues += ddl.revisar_lecturas(mapeo, servidor, base)

    variables, secretos = [], []
    ruta_runtime = repo / RUNTIME
    if ruta_runtime.exists():
        try:
            contrato = yaml.safe_load(ruta_runtime.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            issues.append(f"{RUNTIME.as_posix()} no es YAML válido: {exc}")
            contrato = {}
        variables, secretos = contrato.get("env") or [], contrato.get("secrets") or []
    propias = ddl.tablas_a_crear(mapeo)
    if propias and not ddl.revisar_tablas_a_crear(mapeo):
        declarados = [str(x.get("secret")) for x in secretos]
        faltan = plan.secretos_sin_declarar(declarados, propias[0][0])
        if faltan:
            issues.append(".agp/runtime.yaml debe declarar los secretos de conexión de las tablas propias: " + ", ".join(faltan))
    _, bloqueos = permisos.plan_de_permisos(
        mapeo, variables, secretos, habilitado=True, comprobar_habilitacion=False)
    issues += bloqueos
    unicos = list(dict.fromkeys(issues))
    return {"valid": not unicos, "issues": unicos}
