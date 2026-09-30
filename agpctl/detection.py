"""Detección explicable de perfiles; nunca modifica el repositorio analizado."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

SEARCH_DIRS = (".", "backend", "api", "frontend", "web")


def _within(repo: Path, relative: str) -> Path | None:
    candidate = (repo / relative).resolve()
    return candidate if candidate.is_relative_to(repo) else None


def _is_file(repo: Path, relative: str) -> bool:
    candidate = _within(repo, relative)
    return candidate is not None and candidate.is_file()


def _is_dir(repo: Path, relative: str) -> bool:
    candidate = _within(repo, relative)
    return candidate is not None and candidate.is_dir()


def _path(folder: str, name: str) -> str:
    return name if folder == "." else f"{folder}/{name}"


def _candidate(profile: str, folder: str, signals: list[str]) -> dict:
    return {"profile": profile, "location": folder, "signals": signals}


def detect_project(repo: Path) -> dict:
    repo = repo.resolve()
    if not repo.is_dir():
        raise ValueError(f"Repositorio inexistente: {repo}")

    candidates: list[dict] = []
    warnings: list[str] = []
    for folder in SEARCH_DIRS:
        python_manifest = next(
            (name for name in ("pyproject.toml", "requirements.txt") if _is_file(repo, _path(folder, name))),
            None,
        )
        python_entry = next(
            (name for name in ("app.py", "main.py", "wsgi.py", "asgi.py") if _is_file(repo, _path(folder, name))),
            None,
        )
        if python_manifest and python_entry:
            candidates.append(
                _candidate("python-api", folder, [_path(folder, python_manifest), _path(folder, python_entry)])
            )

        package_path = _path(folder, "package.json")
        if not _is_file(repo, package_path):
            continue
        try:
            package = json.loads((repo / package_path).read_text(encoding="utf-8"))
            if not isinstance(package, dict):
                raise TypeError("la raíz debe ser un objeto JSON")
        except (OSError, ValueError, TypeError) as exc:
            warnings.append(f"{package_path}: no se puede analizar: {exc}")
            continue

        scripts = package.get("scripts", {})
        dependencies = package.get("dependencies", {})
        dev_dependencies = package.get("devDependencies", {})
        if not isinstance(scripts, dict) or not isinstance(dependencies, dict) or not isinstance(dev_dependencies, dict):
            warnings.append(f"{package_path}: scripts/dependencies deben ser objetos")
            continue
        node_entry = next(
            (name for name in ("server.mjs", "server.js", "app.mjs", "app.js", "index.mjs", "index.js")
             if _is_file(repo, _path(folder, name))),
            None,
        )
        framework = next(
            (name for name in ("express", "fastify", "@nestjs/core") if name in dependencies),
            None,
        )
        if scripts.get("start") and (node_entry or framework):
            signals = [package_path, "scripts.start"]
            signals.append(_path(folder, node_entry) if node_entry else f"dependencies.{framework}")
            candidates.append(_candidate("node-api", folder, signals))

        has_react = "react" in dependencies or "react" in dev_dependencies
        if has_react and scripts.get("build") and _is_dir(repo, _path(folder, "src")):
            if not _is_file(repo, _path(folder, "index.html")):
                warnings.append(f"{folder}: frontend React sin index.html; revisar entrada de build")
            candidates.append(
                _candidate("react-static", folder, [package_path, "dependencies.react", "scripts.build", _path(folder, "src")])
            )

    manifest = repo / ".agp" / "profile.yaml"
    declared = None
    if manifest.is_file():
        try:
            profile_data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
            declared = profile_data.get("id") if isinstance(profile_data, dict) else None
        except (OSError, yaml.YAMLError) as exc:
            warnings.append(f".agp/profile.yaml: no se puede analizar: {exc}")

    candidates.sort(key=lambda item: (item["profile"], item["location"]))
    unique_profiles = {item["profile"] for item in candidates}
    unambiguous = len(candidates) == 1
    if len(candidates) > 1:
        warnings.append("Hay varios componentes o perfiles posibles; se requiere selección humana")
    if not candidates:
        warnings.append("No hay señales suficientes para seleccionar un perfil soportado")
    if declared and declared not in unique_profiles:
        warnings.append("El perfil declarado no coincide con las señales detectadas; revisar manualmente")

    return {
        "repo": str(repo),
        "readOnly": True,
        "declaredProfile": declared,
        "recommendedProfile": candidates[0]["profile"] if unambiguous else None,
        "requiresConfirmation": not unambiguous,
        "candidates": candidates,
        "warnings": warnings,
    }
