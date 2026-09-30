from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from agpctl.detection import detect_project
from agpctl.local_runtime import LocalRunError, local_down, local_plan, local_up
from scripts.validate_governance_ref import UniqueKeyLoader
from scripts.validate_governance_ref import validate as validate_governance_ref

KIT_ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = {
    "governance": "governance-manifest.schema.json",
    "profile": "profile-v1.schema.json",
    "deployment": "agp-deploy-v2.schema.json",
    "data_access": "data-access-manifest.schema.json",
}
SHA256_IMAGE = re.compile(r"@sha256:[0-9a-f]{64}(?:\s|$)")
MUTABLE_REF = re.compile(
    r"raw\.githubusercontent\.com/AGPAutomatizacionCO/agp-ai-governance-kit/(?:main|refs/heads/main)/"
    r"|\buses:\s*[^\s]+@main\b"
    r"|(?:^|[\s'\"])\S+:latest(?:[\s'\"]|$)",
    re.IGNORECASE | re.MULTILINE,
)


def _load(path: Path):
    content = path.read_text(encoding="utf-8")
    return json.loads(content) if path.suffix == ".json" else yaml.load(content, Loader=UniqueKeyLoader)


def _schema_issues(data, schema_name: str, label: str) -> list[str]:
    schema = json.loads((KIT_ROOT / "schemas" / SCHEMAS[schema_name]).read_text(encoding="utf-8"))
    return [
        f"{label}: {'/'.join(str(p) for p in error.absolute_path) or 'raíz'}: {error.message}"
        for error in Draft202012Validator(schema).iter_errors(data)
    ]


def _project_path(repo: Path, relative: str, label: str, issues: list[str], kind: str = "file") -> Path | None:
    candidate = (repo / relative).resolve()
    if not candidate.is_relative_to(repo):
        issues.append(f"{label}: ruta fuera del repositorio: {relative}")
        return None
    if kind == "file" and not candidate.is_file():
        issues.append(f"{label}: archivo inexistente: {relative}")
        return None
    if kind == "dir" and not candidate.is_dir():
        issues.append(f"{label}: directorio inexistente: {relative}")
        return None
    return candidate


def _validate_requirements(path: Path, issues: list[str]) -> None:
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        item = line.strip()
        if not item or item.startswith("#"):
            continue
        if item.startswith("-") or "==" not in item:
            issues.append(f"{path.name}:{number}: dependencia sin versión exacta o directiva no soportada: {item}")


def _validate_dockerfile(path: Path, issues: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    from_lines = [line.strip() for line in text.splitlines() if line.strip().upper().startswith("FROM ")]
    if not from_lines:
        issues.append(f"{path.name}: falta FROM")
    stages: set[str] = set()
    for line in from_lines:
        parts = line.split()
        image_index = 2 if len(parts) > 2 and parts[1].startswith("--platform=") else 1
        if image_index >= len(parts):
            issues.append(f"{path.name}: FROM incompleto: {line}")
            continue
        image = parts[image_index]
        if image.lower() not in stages and not SHA256_IMAGE.search(image):
            issues.append(f"{path.name}: imagen base sin digest SHA-256: {line}")
        if len(parts) > image_index + 2 and parts[image_index + 1].upper() == "AS":
            stages.add(parts[image_index + 2].lower())
    users = [line.split(None, 1)[1].strip().split()[0] for line in text.splitlines() if line.strip().upper().startswith("USER ")]
    if not users or users[-1].lower() in {"root", "0"}:
        issues.append(f"{path.name}: la etapa final debe declarar USER no-root")


def _observed_access(deployment: dict) -> set[tuple[str, str, str, str]]:
    wrapper = deployment.get("campos", {}).get("MapeoAccesoBD", {})
    mapping = wrapper.get("valor", {}) if isinstance(wrapper, dict) else {}
    observed = set()
    for source in mapping.get("fuentes_datos", []):
        for schema in source.get("esquemas", []):
            for table in schema.get("tablas", []):
                for operation in table.get("operaciones_permitidas", []):
                    observed.add((source["database_id"], schema["schema"], table["table"], operation.upper()))
    return observed


def _validate_approvals(
    observed: set[tuple[str, str, str, str]],
    approvals_path: Path | None,
    environment: str | None,
    issues: list[str],
) -> None:
    if not observed:
        return
    if not approvals_path or not environment:
        issues.append("Hay acceso a datos detectado; faltan aprobaciones confiables y ambiente")
        return
    try:
        approvals = json.loads(approvals_path.read_text(encoding="utf-8"))["approved"]
        approved = set()
        now = dt.datetime.now(dt.timezone.utc)
        for entry in approvals:
            expires = dt.datetime.fromisoformat(entry["expiresAt"].replace("Z", "+00:00"))
            if expires.tzinfo is None:
                raise ValueError("expiresAt debe incluir zona horaria")
            if entry["environment"] != environment or expires <= now:
                continue
            for operation in entry["operations"]:
                approved.add((entry["database_id"], entry["schema"], entry["table"], operation.upper()))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        issues.append(f"Aprobaciones ilegibles o inválidas: {exc}")
        return
    for access in sorted(observed - approved):
        issues.append(f"Acceso a datos sin aprobación vigente en {environment}: {'/'.join(access)}")


def validate_project(
    repo: Path,
    *,
    verify_tag: bool = True,
    approvals_path: Path | None = None,
    environment: str | None = None,
    local_preview: bool = False,
) -> list[str]:
    repo = repo.resolve()
    issues: list[str] = []
    paths = {
        "profile": repo / ".agp" / "profile.yaml",
        "deployment": repo / ".github" / "agp-deploy.json",
    }
    if not local_preview:
        paths["governance"] = repo / ".agp" / "governance.yaml"
    data = {}
    for kind, path in paths.items():
        try:
            data[kind] = _load(path)
            issues.extend(_schema_issues(data[kind], kind, str(path.relative_to(repo))))
        except (OSError, ValueError, yaml.YAMLError) as exc:
            issues.append(f"No se pudo leer {path.relative_to(repo)}: {exc}")
    if issues:
        return issues

    profile, deployment = data["profile"], data["deployment"]
    if verify_tag and not local_preview:
        issues.extend(validate_governance_ref(paths["governance"]))
    if not local_preview and profile["id"] != data["governance"]["profile"]:
        issues.append("El perfil seleccionado no coincide con .agp/profile.yaml")

    build = profile["build"]
    for name in ("context", "dockerfile", "dependencyManifest", "lockfile", "sourceDir", "outputDir"):
        if name not in build:
            continue
        kind = "dir" if name in {"context", "sourceDir"} else "planned" if name == "outputDir" else "file"
        path = _project_path(repo, build[name], f"build.{name}", issues, kind)
        if name == "dependencyManifest" and path and path.name == "requirements.txt":
            _validate_requirements(path, issues)
        if name == "dependencyManifest" and path and path.name == "package.json" and "lockfile" not in build:
            issues.append("package.json requiere un lockfile declarado en el perfil")
        if name == "dockerfile" and path:
            _validate_dockerfile(path, issues)
    if profile["kind"] == "container":
        resources = deployment["azure"]["recursos"]
        runtime = profile["runtime"]
        if not any(
            str(resource.get("Puerto")) == str(runtime["port"])
            and resource.get("RutaHealthCheck") == runtime["healthPath"]
            for resource in resources
        ):
            issues.append("Puerto y health check del perfil no coinciden con un recurso del despliegue")
    elif not any(resource.get("TipoRecurso") == "Static Web App" for resource in deployment["azure"]["recursos"]):
        issues.append("El perfil estático necesita un recurso Static Web App")

    if not local_preview and not list((repo / "infra").rglob("*.bicep")):
        issues.append("Falta IaC Bicep bajo infra/")
    for pattern in (".github/workflows/*.yml", ".github/workflows/*.yaml", ".agp/*.yaml"):
        for path in repo.glob(pattern):
            if MUTABLE_REF.search(path.read_text(encoding="utf-8")):
                issues.append(f"Referencia mutable a main/latest en {path.relative_to(repo)}")
    mapping = deployment.get("campos", {}).get("MapeoAccesoBD", {}).get("valor")
    if mapping is not None:
        map_issues = _schema_issues(mapping, "data_access", "campos/MapeoAccesoBD/valor")
        issues.extend(map_issues)
        if not map_issues:
            _validate_approvals(_observed_access(deployment), approvals_path, environment, issues)
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(prog="agpctl")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate", help="Validar un repositorio AGP")
    validate.add_argument("--repo", type=Path, required=True)
    validate.add_argument("--approvals", type=Path, help="JSON de aprobaciones entregado por la Mesa")
    validate.add_argument("--environment", choices=("dev", "qa", "prod"))
    detect = sub.add_parser("detect", help="Detectar perfiles candidatos sin modificar el repositorio")
    detect.add_argument("--repo", type=Path, required=True)
    local = sub.add_parser("local", help="Planear o ejecutar una prueba Docker sólo local")
    local_sub = local.add_subparsers(dest="local_command", required=True)
    for action in ("plan", "up", "down"):
        command = local_sub.add_parser(action)
        command.add_argument("--repo", type=Path, required=True)
        if action != "down":
            command.add_argument("--host-port", type=int)
        if action != "plan":
            command.add_argument("--docker-sudo", action="store_true", help="Usar sudo -n para Docker en WSL/Linux")
        if action == "up":
            command.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args()
    if args.command == "validate":
        issues = validate_project(args.repo, approvals_path=args.approvals, environment=args.environment)
        print(json.dumps({"valid": not issues, "issues": issues}, ensure_ascii=False, indent=2))
        return 1 if issues else 0
    if args.command == "detect":
        try:
            result = detect_project(args.repo)
        except (OSError, ValueError) as exc:
            print(json.dumps({"valid": False, "issues": [str(exc)]}, ensure_ascii=False, indent=2))
            return 1
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    try:
        if args.local_command == "down":
            result = local_down(args.repo, docker_sudo=args.docker_sudo)
        else:
            issues = validate_project(args.repo, local_preview=True, environment="dev")
            if issues:
                print(json.dumps({"valid": False, "localOnly": True, "issues": issues}, ensure_ascii=False, indent=2))
                return 1
            plan = local_plan(args.repo, args.host_port)
            result = plan if args.local_command == "plan" else local_up(plan, args.timeout, docker_sudo=args.docker_sudo)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (LocalRunError, OSError, ValueError, KeyError) as exc:
        print(json.dumps({"valid": False, "localOnly": True, "issues": [str(exc)]}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
