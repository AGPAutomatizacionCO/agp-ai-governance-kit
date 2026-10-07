"""Build the immutable release attachment from the checked-out kit commit."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

from agpctl import __version__

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "release" / "compatibility.template.json"
SHA = re.compile(r"[0-9a-f]{40}\Z")


def build(commit: str, *, template: Path = TEMPLATE) -> dict:
    if not SHA.fullmatch(commit):
        raise ValueError("kitCommit debe ser un SHA completo de 40 caracteres")
    data = json.loads(template.read_text(encoding="utf-8"))
    if data.get("status") != "candidate":
        raise ValueError("El manifiesto del RC debe tener status=candidate")
    if data.get("kitVersion") != "v4.0.0-rc.1":
        raise ValueError("Versión del kit inesperada")
    if data.get("agpctl") != {"minInclusive": __version__, "maxExclusive": "0.1.1"}:
        raise ValueError("Intervalo de agpctl incompatible con el CLI probado")
    if data.get("profiles") != {"python-api": "1"}:
        raise ValueError("Sólo el contrato python-api v1 está declarado para este piloto")
    if "pending" in json.dumps(data).lower():
        raise ValueError("El manifiesto contiene valores pendientes")
    data["kitCommit"] = commit
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-sha", help="SHA aprobado por la persona responsable")
    args = parser.parse_args()
    dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
    if dirty:
        parser.error("El checkout contiene cambios sin confirmar; no se puede generar el adjunto")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if args.expected_sha and args.expected_sha != commit:
        parser.error("El checkout no coincide con el SHA aprobado")
    data = build(commit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{data['kitVersion']} @ {commit}: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
