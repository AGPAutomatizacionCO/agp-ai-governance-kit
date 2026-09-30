"""Validate a project's pinned governance release against its immutable tag target."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "governance-manifest.schema.json"
REPOSITORY = "https://github.com/AGPAutomatizacionCO/agp-ai-governance-kit.git"


class UniqueKeyLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader: UniqueKeyLoader, node: yaml.MappingNode) -> dict:
    mapping: dict = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if key in mapping:
            raise ValueError(f"Clave YAML duplicada: {key}")
        mapping[key] = loader.construct_object(value_node)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping
)


def resolve_tag(version: str) -> str:
    refs = [f"refs/tags/{version}", f"refs/tags/{version}^{{}}"]
    result = subprocess.run(
        ["git", "ls-remote", "--tags", REPOSITORY, *refs],
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    )
    found = {}
    for line in result.stdout.splitlines():
        sha, ref = line.split("\t", 1)
        found[ref] = sha
    return found.get(refs[1]) or found.get(refs[0]) or ""


def validate(manifest: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = yaml.load(manifest.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        for error in Draft202012Validator(schema).iter_errors(data):
            path = "/".join(str(part) for part in error.absolute_path)
            errors.append(f"{path or 'raíz'}: {error.message}")
    except (OSError, yaml.YAMLError, ValueError, json.JSONDecodeError) as exc:
        return [f"No se pudo leer el manifiesto o esquema: {exc}"]
    if errors:
        return errors

    version = data["kit"]["version"]
    expected = data["kit"]["ref"]
    try:
        actual = resolve_tag(version)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
        return [f"No se pudo comprobar el tag {version}: {exc}"]
    if not actual:
        errors.append(f"El tag {version} no existe en el kit")
    elif not re.fullmatch(r"[0-9a-f]{40}", actual) or actual != expected:
        errors.append(f"El tag {version} apunta a {actual}; el proyecto fijó {expected}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    errors = validate(args.manifest)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Versión y SHA de gobernanza comprobados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
