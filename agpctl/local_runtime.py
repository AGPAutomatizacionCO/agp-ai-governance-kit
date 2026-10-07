"""Ejecución Docker local. Nunca autentica en Azure ni publica imágenes."""

from __future__ import annotations

import datetime as dt
import hashlib
import http.client
import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path

import yaml


class LocalRunError(RuntimeError):
    pass


def _names(repo: Path) -> tuple[str, str]:
    slug = re.sub(r"[^a-z0-9-]", "-", repo.name.lower()).strip("-")[:30] or "project"
    suffix = hashlib.sha256(str(repo.resolve()).encode("utf-8")).hexdigest()[:10]
    return f"agp-local/{slug}:{suffix}", f"agp-local-{slug}-{suffix}"


def local_plan(repo: Path, host_port: int | None = None) -> dict:
    repo = repo.resolve()
    profile = yaml.safe_load((repo / ".agp" / "profile.yaml").read_text(encoding="utf-8"))
    if profile["kind"] != "container":
        raise LocalRunError("local up soporta por ahora sólo perfiles de contenedor")
    runtime = profile["runtime"]
    port = runtime["port"] if host_port is None else host_port
    if not 1 <= port <= 65535:
        raise LocalRunError("El puerto local debe estar entre 1 y 65535")
    image, container = _names(repo)
    build = profile["build"]
    return {
        "localOnly": True,
        "governanceVerified": False,
        "repo": str(repo),
        "profile": profile["id"],
        "image": image,
        "containerName": container,
        "hostPort": port,
        "containerPort": runtime["port"],
        "healthPath": runtime["healthPath"],
        "buildCommand": [
            "docker", "build", "--pull", "--tag", image,
            "--file", str(repo / build["dockerfile"]), str(repo / build["context"]),
        ],
        "runCommand": [
            "docker", "run", "--detach", "--rm", "--name", container,
            "--publish", f"127.0.0.1:{port}:{runtime['port']}",
            "--security-opt", "no-new-privileges", "--cap-drop", "ALL", image,
        ],
    }


def _docker(args: list[str], *, docker_sudo: bool = False) -> str:
    command = ["sudo", "-n", *args] if docker_sudo else args
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        executable = "sudo" if docker_sudo else "Docker CLI"
        raise LocalRunError(f"{executable} no está instalado o no está en PATH") from exc
    if result.returncode:
        hint = "; ejecuta sudo -v y comprueba el daemon" if docker_sudo else ""
        raise LocalRunError(f"Docker devolvió código {result.returncode} en {args[1]}{hint}")
    return result.stdout.strip()


def _healthy(port: int, path: str) -> bool:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        response.read()
        return 200 <= response.status < 300
    except (OSError, http.client.HTTPException):
        return False
    finally:
        connection.close()


def _atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(temporary, path)


def local_up(plan: dict, timeout_seconds: int = 60, *, docker_sudo: bool = False) -> dict:
    repo = Path(plan["repo"])
    state = repo / ".agp" / "local-runs"
    active = state / "active.json"
    if active.exists():
        raise LocalRunError("Ya existe una ejecución local activa; usa local down primero")
    if not 1 <= timeout_seconds <= 600:
        raise LocalRunError("El timeout debe estar entre 1 y 600 segundos")

    _docker(["docker", "version", "--format", "{{.Server.Version}}"], docker_sudo=docker_sudo)
    _docker(plan["buildCommand"], docker_sudo=docker_sudo)
    image_id = _docker(["docker", "image", "inspect", "--format", "{{.Id}}", plan["image"]], docker_sudo=docker_sudo)
    started = False
    try:
        _docker(plan["runCommand"], docker_sudo=docker_sudo)
        started = True
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if _healthy(plan["hostPort"], plan["healthPath"]):
                break
            time.sleep(1)
        else:
            raise LocalRunError("El contenedor no respondió con HTTP 2xx en el health check")

        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        record_name = f"{stamp}.json"
        evidence = {
            "status": "running",
            "localOnly": True,
            "governanceVerified": False,
            "startedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
            "projectPath": str(repo),
            "profile": plan["profile"],
            "imageId": image_id,
            "containerName": plan["containerName"],
            "dockerViaSudo": docker_sudo,
            "healthUrl": f"http://127.0.0.1:{plan['hostPort']}{plan['healthPath']}",
        }
        _atomic_json(state / record_name, evidence)
        _atomic_json(active, {"record": record_name, "containerName": plan["containerName"]})
        return evidence
    except Exception:
        if started:
            try:
                _docker(["docker", "stop", plan["containerName"]], docker_sudo=docker_sudo)
            except LocalRunError:
                pass
        raise


def local_down(repo: Path, *, docker_sudo: bool = False) -> dict:
    repo = repo.resolve()
    state = repo / ".agp" / "local-runs"
    active = state / "active.json"
    if not active.is_file():
        raise LocalRunError("No hay una ejecución local activa")
    entry = json.loads(active.read_text(encoding="utf-8"))
    expected = _names(repo)[1]
    if entry.get("containerName") != expected or not re.fullmatch(r"\d{8}T\d{12}Z\.json", entry.get("record", "")):
        raise LocalRunError("El registro de ejecución local no corresponde a este proyecto")
    record = state / entry["record"]
    evidence = json.loads(record.read_text(encoding="utf-8"))
    _docker(["docker", "stop", expected], docker_sudo=docker_sudo)
    evidence["status"] = "stopped"
    evidence["stoppedAt"] = dt.datetime.now(dt.timezone.utc).isoformat()
    _atomic_json(record, evidence)
    active.unlink()
    return evidence
