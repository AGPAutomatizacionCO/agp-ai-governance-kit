"""`agpctl runtime`: de las variables de entorno que usa un desarrollo a `.agp/runtime.yaml` (runtime.agp/v1).

Solo LEE el repositorio y nunca modifica nada. Nunca lee un `.env` real (no se versiona y puede tener secretos): usa los
NOMBRES de `.env.example`, del código (`os.getenv`, `os.environ`, `process.env`, `import.meta.env`) y de los `docker-compose*.yml`.
Jamás copia ni escribe un valor secreto, y no crea nada en ningún vault: solo declara nombres. Revisa IT.

  plan  propone el contrato y un informe de lo que hay que decidir
  check compara el contrato que ya existe con lo que lee el código
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

API_VERSION = "runtime.agp/v1"
_NOMBRE_ENV = re.compile(r"^[A-Z][A-Z0-9_]{1,63}$")
_NOMBRE_SECRETO = re.compile(r"^[A-Za-z0-9-]{1,127}$")
_RESERVADAS = ("WEBSITES_", "DOCKER_", "AZURE_", "AGP_DEV_", "AGP_ENSAYO", "MSAL_", "GITHUB_APP_")
_DEL_SISTEMA = {"PATH", "HOME", "PWD", "USER", "HOSTNAME", "LANG", "LC_ALL", "TZ", "PYTHONPATH", "PYTHONUNBUFFERED", "PORT",
                "NODE_ENV", "CI", "TERM", "SHELL", "TMPDIR", "TEMP", "TMP", "DEBUG"}
# Catálogo IED de solo lectura (Mesa: fuentes_solo_lectura.py). Prefijo de variable -> id de fuente.
_FUENTES = {"CALENDARIO": "calendar", "PRODUCTIVITY": "productivity", "AGPCOL": "agpcol", "SAGA": "saga", "COMERCIAL": "comercial"}
_SECRETO = re.compile(r"(PASSWORD|PASSWD|PWD|SECRET|TOKEN|API_?KEY|PRIVATE|CREDENTIAL|CONNECTION|DATABASE_URL|(^|_)KEY$|(^|_)USER$|(^|_)SERVER$)")
_CANTIDAD = re.compile(r"(EXPIRE|EXPIRES|TTL|(^|_)MAX(_|$)|MINUTES|SECONDS|TIMEOUT|TOKENS$|(^|_)LIMIT)")
_PARECE_SECRETO = re.compile(r"-----BEGIN|AccountKey=|Password=|SharedAccessSignature|[?&]sig=|eyJ[A-Za-z0-9_-]{20,}|^[A-Za-z0-9+/_-]{40,}={0,2}$", re.I)
_IP_PRIVADA = re.compile(r"(https?://|@|//)(localhost|127\.|10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)", re.I)
_CODIGO = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
_OMITIR = {"node_modules", ".git", ".venv", "venv", "__pycache__", "dist", "build", ".next", "tests", "test", "__tests__"}
_PATRONES = (
    re.compile(r"""os\.getenv\(\s*['"]([A-Z][A-Z0-9_]+)['"](?:\s*,\s*(['"][^'"\n]*['"]))?"""),
    re.compile(r"""os\.environ\.get\(\s*['"]([A-Z][A-Z0-9_]+)['"](?:\s*,\s*(['"][^'"\n]*['"]))?"""),
    re.compile(r"""os\.environ\[\s*['"]([A-Z][A-Z0-9_]+)['"]\s*\]"""),
    re.compile(r"""process\.env\.([A-Z][A-Z0-9_]+)"""),
    re.compile(r"""process\.env\[\s*['"]([A-Z][A-Z0-9_]+)['"]\s*\]"""),
    re.compile(r"""import\.meta\.env\.([A-Z][A-Z0-9_]+)"""),
)


def _omitido(ruta: Path, repo: Path) -> bool:
    return any(parte in _OMITIR for parte in ruta.relative_to(repo).parts[:-1])


def _anotar(encontradas: dict, nombre: str, fuente: str, defecto: str | None = None) -> None:
    dato = encontradas.setdefault(nombre, {"fuentes": set(), "defecto": None})
    dato["fuentes"].add(fuente)
    if defecto is not None and dato["defecto"] is None:
        dato["defecto"] = defecto


def leer_variables(repo: Path) -> dict:
    """{nombre: {"fuentes": {...}, "defecto": valor literal o None}}. Nunca lee archivos .env reales."""
    repo = Path(repo)
    encontradas: dict = {}
    for ejemplo in list(repo.rglob(".env.example")) + list(repo.rglob(".env.sample")):
        if _omitido(ejemplo, repo):
            continue
        for linea in ejemplo.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"\s*(?:export\s+)?([A-Z][A-Z0-9_]+)\s*=\s*(.*)$", linea)
            if m:
                valor = m.group(2).strip().strip("'\"")
                _anotar(encontradas, m.group(1), ".env.example", None if _PARECE_SECRETO.search(valor) else (valor or None))
    for archivo in repo.rglob("*"):
        if not archivo.is_file() or _omitido(archivo, repo):
            continue
        rel = str(archivo.relative_to(repo)).replace("\\", "/")
        if archivo.suffix in _CODIGO:
            texto = archivo.read_text(encoding="utf-8", errors="replace")
            for patron in _PATRONES:
                for m in patron.finditer(texto):
                    defecto = m.group(2)[1:-1] if m.lastindex and m.lastindex >= 2 and m.group(2) else None
                    _anotar(encontradas, m.group(1), rel, defecto)
        elif re.fullmatch(r"docker-compose.*\.ya?ml", archivo.name):
            try:
                datos = yaml.safe_load(archivo.read_text(encoding="utf-8", errors="replace")) or {}
            except yaml.YAMLError:
                continue
            for servicio in (datos.get("services") or {}).values():
                entorno = (servicio or {}).get("environment") or []
                nombres = entorno.keys() if isinstance(entorno, dict) else [str(e).split("=", 1)[0] for e in entorno]
                for nombre in nombres:
                    if _NOMBRE_ENV.fullmatch(str(nombre)):
                        _anotar(encontradas, str(nombre), rel)
    return encontradas


def clasificar(nombre: str, defecto: str | None) -> tuple[str, str]:
    """(tipo, motivo). tipo: omitir | build | fuente | secreto | env | decidir."""
    if nombre in _DEL_SISTEMA:
        return "omitir", "variable del sistema"
    if any(nombre.startswith(p) for p in _RESERVADAS):
        return "omitir", "la fija la plataforma o la Mesa; un desarrollo no la redefine"
    if nombre.startswith("VITE_") or nombre.startswith("NEXT_PUBLIC_"):
        return "build", "se fija al COMPILAR el frontend, no al ejecutar: la Mesa no la entrega en runtime"
    prefijo = nombre.split("_", 1)[0]
    if prefijo in _FUENTES and (_SECRETO.search(nombre) or nombre.endswith("_DB")):
        return "fuente", f"fuente de solo lectura del catálogo IED: {_FUENTES[prefijo]}"
    # «TOKEN» o «KEY» en un nombre de duración, límite o cantidad (ACCESS_TOKEN_EXPIRE_MINUTES, GROQ_MAX_TOKENS) no es un secreto.
    es_numerica = _CANTIDAD.search(nombre) and not re.search(r"(PASSWORD|PASSWD|PWD|SECRET)", nombre)
    if _SECRETO.search(nombre) and not es_numerica:
        return "secreto", "nombre sensible: el valor vive en Key Vault"
    if defecto is not None and not _PARECE_SECRETO.search(defecto):
        return "env", "valor no secreto con valor por defecto en el repositorio"
    return "decidir", "sin valor por defecto ni señal clara: lo decide una persona"


def _avisos(nombre: str, defecto: str | None) -> list[str]:
    avisos = []
    if defecto and _IP_PRIVADA.search(defecto):
        avisos.append(f"{nombre}: el valor por defecto apunta a una dirección privada o local; no se alcanza desde Azure")
    if nombre == "DATABASE_URL" and defecto and defecto.startswith("sqlite"):
        avisos.append("DATABASE_URL: SQLite local; dentro del contenedor se pierde en cada reinicio y no es una base de producción")
    return avisos


def _slug(texto: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")[:40] or "desarrollo"


def plan(repo: Path, prefijo: str | None = None) -> dict:
    repo = Path(repo)
    prefijo = _slug(prefijo or repo.resolve().name)
    variables, avisos = [], []
    for clave, dato in sorted(leer_variables(repo).items()):
        tipo, motivo = clasificar(clave, dato["defecto"])
        entrada = {"name": clave, "tipo": tipo, "motivo": motivo, "fuentes": sorted(dato["fuentes"])}
        if tipo == "secreto":
            entrada["secret"] = f"{prefijo}-{_slug(clave)}"
        if tipo == "env":
            entrada["value"] = dato["defecto"]
        if tipo not in ("omitir", "build"):
            avisos += _avisos(clave, dato["defecto"])
        variables.append(entrada)
    return {"readOnly": True, "apiVersion": API_VERSION, "prefijo": prefijo, "variables": variables, "avisos": avisos,
            "yaml": _yaml(variables), "porDecidir": [v["name"] for v in variables if v["tipo"] == "decidir"]}


def _yaml(variables: list[dict]) -> str:
    env = [v for v in variables if v["tipo"] == "env"]
    secretos = [v for v in variables if v["tipo"] == "secreto"]
    fuentes = sorted({v["motivo"].rsplit(": ", 1)[-1] for v in variables if v["tipo"] == "fuente"})
    lineas = ["# Propuesto por `agpctl runtime plan`: solo NOMBRES, nunca valores secretos. Revisar antes de fusionar.",
              f"apiVersion: {API_VERSION}", ""]
    if env:
        lineas.append("env:")
        for v in env:
            valor = '"' + str(v["value"]).replace("\\", "\\\\").replace('"', '\\"') + '"'
            lineas += [f"  - name: {v['name']}", f"    value: {valor}"]
    if secretos:
        lineas.append("secrets:")
        for v in secretos:
            lineas += [f"  - name: {v['name']}", f"    secret: {v['secret']}"]
    if fuentes:
        lineas.append("fuentes: [" + ", ".join(fuentes) + "]")
    for v in variables:
        if v["tipo"] == "decidir":
            lineas.append(f"# DECIDIR: {v['name']} ({v['motivo']})")
    return "\n".join(lineas) + "\n"


def check(repo: Path) -> dict:
    repo = Path(repo)
    ruta = repo / ".agp" / "runtime.yaml"
    usadas = {n: d for n, d in leer_variables(repo).items() if clasificar(n, d["defecto"])[0] not in ("omitir", "build")}
    if not ruta.exists():
        faltan = sorted(usadas)
        return {"valid": not faltan, "issues": [f"falta .agp/runtime.yaml y el código usa: {', '.join(faltan)}"] if faltan else []}
    try:
        contrato = yaml.safe_load(ruta.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        return {"valid": False, "issues": [f".agp/runtime.yaml no es YAML válido: {exc}"]}
    issues, declaradas = [], set()
    if contrato.get("apiVersion") != API_VERSION:
        issues.append(f"apiVersion debe ser {API_VERSION}")
    for item in contrato.get("env") or []:
        declaradas.add(item.get("name"))
        if not _NOMBRE_ENV.fullmatch(str(item.get("name"))):
            issues.append(f"env: nombre inválido {item.get('name')!r}")
        if _PARECE_SECRETO.search(str(item.get("value", ""))):
            issues.append(f"env: el valor de {item.get('name')} parece un secreto; va en secrets")
    for item in contrato.get("secrets") or []:
        declaradas.add(item.get("name"))
        if not _NOMBRE_SECRETO.fullmatch(str(item.get("secret"))):
            issues.append(f"secrets: nombre de secreto inválido para {item.get('name')}")
    de_fuentes = {n for n in usadas if clasificar(n, usadas[n]["defecto"])[0] == "fuente"} if contrato.get("fuentes") else set()
    for nombre in sorted(set(usadas) - declaradas - de_fuentes):
        issues.append(f"el código usa {nombre} ({', '.join(sorted(usadas[nombre]['fuentes']))}) y no está en runtime.yaml")
    for nombre in sorted(d for d in declaradas - set(usadas) if d):
        issues.append(f"runtime.yaml declara {nombre} pero el código no lo lee")
    return {"valid": not issues, "issues": issues}
