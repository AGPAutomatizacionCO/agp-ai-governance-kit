"""Deterministic checks for a governance-kit release candidate."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_compatibility import build as build_compatibility

RAW_PREFIX = "https://raw.githubusercontent.com/AGPAutomatizacionCO/agp-ai-governance-kit/"
REQUIRED = (
    "AGENTS.md",
    "PROMPT_ANALISIS_REPOSITORIO_AGENTES.md",
    "constitution.md",
    "harness-policy.md",
    "agent-specification.md",
    "agent-development.md",
    "agent-technical-review.md",
    "agent-testing.md",
    "agent-documental.md",
    "agent-despliegue.md",
    "prompt-agente-despliegue-evaluacion.md",
)
NORMATIVE = re.compile(
    r"^(AGENTS\.md|START-HERE\.md|constitution\.md|harness-policy\.md|"
    r"agent-[^/]+\.md|prompt-agente-[^/]+\.md|schemas/.*)$"
)


def report(errors: list[str], message: str) -> None:
    errors.append(message)
    print(f"ERROR: {message}", file=sys.stderr)


def validate_paths(errors: list[str]) -> None:
    for name in REQUIRED:
        if not (ROOT / name).is_file():
            report(errors, f"Falta archivo obligatorio: {name}")

    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    if RAW_PREFIX + "main/" in agents or RAW_PREFIX + "refs/heads/main/" in agents:
        report(errors, "AGENTS.md contiene referencias normativas mutables a main")

    urls = re.findall(re.escape(RAW_PREFIX) + r"<GOVERNANCE_KIT_REF>/([^\s`]+)", agents)
    if not urls:
        report(errors, "AGENTS.md no declara archivos bajo GOVERNANCE_KIT_REF")
    for name in sorted(set(urls)):
        if not (ROOT / name).is_file():
            report(errors, f"Referencia inexistente en AGENTS.md: {name}")

    # Sólo se comprueban vínculos relativos de Markdown: los enlaces externos
    # dependen de red y no son una prueba determinística del release.
    for markdown in ROOT.rglob("*.md"):
        if any(part in {".git", ".claude"} for part in markdown.relative_to(ROOT).parts):
            continue
        text = markdown.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            target = target.strip().strip("<>").split("#", 1)[0]
            if not target or "://" in target or target.startswith(("mailto:", "#")):
                continue
            path = markdown.parent / unquote(target)
            if not path.exists():
                report(errors, f"Enlace relativo roto en {markdown.relative_to(ROOT)}: {target}")


def validate_json(errors: list[str]) -> None:
    schemas: dict[str, dict] = {}
    for path in (ROOT / "schemas").glob("*.schema.json"):
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
            schemas[path.name] = schema
        except (OSError, json.JSONDecodeError, SchemaError) as exc:
            report(errors, f"Esquema inválido {path.relative_to(ROOT)}: {exc}")

    example = ROOT / "templates" / "data-access-manifest.example.json"
    schema = schemas.get("data-access-manifest.schema.json")
    if schema and example.is_file():
        try:
            data = json.loads(example.read_text(encoding="utf-8"))
            for error in Draft202012Validator(schema).iter_errors(data):
                location = "/".join(str(part) for part in error.absolute_path)
                report(errors, f"Ejemplo de acceso a datos inválido en {location}: {error.message}")
        except json.JSONDecodeError as exc:
            report(errors, f"Ejemplo JSON inválido: {exc}")
    else:
        report(errors, "Falta esquema o ejemplo de acceso a datos")

    examples = (
        ("governance-manifest.schema.json", "governance.valid.yaml", True),
        ("governance-manifest.schema.json", "governance.invalid.yaml", False),
        ("agp-deploy-v2.schema.json", "agp-deploy-v2.valid.json", True),
        ("agp-deploy-v2.schema.json", "agp-deploy-v2.invalid.json", False),
        ("profile-v1.schema.json", "profile-container.valid.yaml", True),
        ("profile-v1.schema.json", "profile-static.valid.yaml", True),
        ("profile-v1.schema.json", "profile-container.invalid.yaml", False),
    )
    for schema_name, example_name, should_pass in examples:
        if schema_name not in schemas:
            report(errors, f"Falta esquema para ejemplo {example_name}: {schema_name}")
            continue
        path = ROOT / "examples" / example_name
        try:
            content = path.read_text(encoding="utf-8")
            data = json.loads(content) if path.suffix == ".json" else yaml.safe_load(content)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            report(errors, f"Ejemplo ilegible {example_name}: {exc}")
            continue
        violations = list(Draft202012Validator(schemas[schema_name]).iter_errors(data))
        if should_pass and violations:
            report(errors, f"Ejemplo válido rechazado {example_name}: {violations[0].message}")
        if not should_pass and not violations:
            report(errors, f"Ejemplo inválido aceptado {example_name}")

    manifest = ROOT / "release" / "compatibility.template.json"
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        for key in ("kitVersion", "kitCommit", "status", "schemaVersions", "agpctl", "profiles"):
            if key not in data:
                report(errors, f"Plantilla de compatibilidad sin {key}")
        try:
            build_compatibility("a" * 40, template=manifest)
        except (ValueError, KeyError) as exc:
            report(errors, f"Compatibilidad del RC inválida: {exc}")
    except (OSError, json.JSONDecodeError) as exc:
        report(errors, f"Plantilla de compatibilidad inválida: {exc}")


def validate_normative_change(errors: list[str], base: str | None) -> None:
    if not base:
        return
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{base}...HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        report(errors, f"No se pudo comparar con la base del PR: {exc.stderr.strip()}")
        return
    changed = set(result.stdout.splitlines())
    if any(NORMATIVE.match(name) for name in changed) and "CHANGELOG.md" not in changed:
        report(errors, "El PR cambia reglas normativas sin actualizar CHANGELOG.md")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", help="SHA de la rama base del pull request")
    args = parser.parse_args()
    errors: list[str] = []
    validate_paths(errors)
    validate_json(errors)
    validate_normative_change(errors, args.base)
    if errors:
        print(f"Validación fallida: {len(errors)} problema(s).", file=sys.stderr)
        return 1
    print("Validación del candidato de release correcta.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
