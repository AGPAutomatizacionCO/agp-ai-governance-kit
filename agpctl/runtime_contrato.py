"""Reglas de `.agp/runtime.yaml` que la Mesa aplica además de «el código usa lo que el contrato declara».

Mismas reglas que `backend/src/helpers/runtime_config.py` de la Mesa de Requerimientos (`revisar`, `_prefijo_de_secretos`,
`revisar_recursos_externos`): el desarrollador y su agente las comprueban con `python -m agpctl runtime check` ANTES de pedir el
despliegue, y lo que aquí pasa no aparece luego como bloqueo en la Mesa. La Mesa manda: si cambia una regla, se actualiza este archivo.

Solo lectura y sin red: no consulta ningún vault ni lee valores de secretos.
"""
import re

CLAVES_CONOCIDAS = {"apiVersion", "desarrollo", "env", "secrets", "vault", "fuentes", "recursos_externos"}
TIPOS_RECURSO_EXTERNO = ("worker", "vm", "job", "script_externo", "servicio_externo", "otro")

_NOMBRE_DESARROLLO = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")
_NOMBRE_RECURSO = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")
_CORREO_AGP = re.compile(r"^[A-Za-z0-9._%+-]+@agpglass\.com$")
_URL_CON_CREDENCIALES = re.compile(r"://[^/\s:@]+:[^/\s@]+@")
_PARECE_SECRETO = re.compile(
    r"-----BEGIN|AccountKey=|Password=|SharedAccessSignature|[?&]sig=|eyJ[A-Za-z0-9_-]{20,}|^[A-Za-z0-9+/_-]{40,}={0,2}$",
    re.IGNORECASE,
)
_CAMPOS_RECURSO = {"tipo", "nombre", "descripcion", "ubicacion", "acceso", "escribe_datos", "responsable"}


def claves_no_reconocidas(contrato: dict) -> list[str]:
    """Problemas por claves de primer nivel que la Mesa no reconoce o que no se permiten (`vault`)."""
    problemas = []
    if "vault" in contrato:
        problemas.append("no se permite elegir el vault: solo se usa el de desarrollos")
    desconocidas = sorted(str(c) for c in set(contrato) - CLAVES_CONOCIDAS)
    if desconocidas:
        problemas.append("claves no reconocidas: " + ", ".join(desconocidas))
    return problemas


def prefijo_de_secretos(desarrollo, secretos: list[dict]) -> list[str]:
    """Norma `<desarrollo>-<dato>`: si el contrato declara `desarrollo`, todos sus secretos empiezan con ese nombre y un guion.
    `secretos` = [{name, secret}]. Sin `desarrollo` no hay nada que comprobar aquí (el aviso lo da `avisos_de_contrato`)."""
    if desarrollo is None:
        return []
    if not isinstance(desarrollo, str) or not _NOMBRE_DESARROLLO.fullmatch(desarrollo):
        return ["desarrollo: use minúsculas, dígitos y guiones (2 a 63 caracteres), el mismo nombre que prefija sus secretos"]
    prefijo = desarrollo + "-"
    fuera = [str(s.get("secret")) for s in secretos if not str(s.get("secret")).startswith(prefijo) or len(str(s.get("secret"))) == len(prefijo)]
    if not fuera:
        return []
    return [f"secrets: los secretos deben llamarse <desarrollo>-<dato> y empezar con «{prefijo}»; no cumplen: " + ", ".join(fuera)]


def avisos_de_contrato(contrato: dict) -> list[str]:
    """Avisos que no bloquean `check` pero la ruta de preparación a IT sí exige (specs/024 de la Mesa)."""
    if contrato.get("desarrollo") is None and contrato.get("secrets"):
        return ["falta `desarrollo`: declare el nombre que prefija sus secretos (<desarrollo>-<dato>); la preparación a IT lo exige"]
    return []


def revisar_recursos_externos(lista, secretos: list[dict] | None = None) -> list[str]:
    """Problemas de `recursos_externos` (workers, VM, jobs, scripts externos…): todo lo que corre FUERA de la Web App y que IT debe conocer.
    Declararlo no lo crea ni lo concede."""
    if lista in (None, []):
        return []
    if not isinstance(lista, list):
        return ["recursos_externos debe ser una lista"]
    problemas, nombres = [], set()
    declarados = {str(s.get("name")) for s in secretos or []} | {str(s.get("secret")) for s in secretos or []}
    for i, r in enumerate(lista, 1):
        donde = f"recursos_externos[{i}]"
        if not isinstance(r, dict):
            problemas.append(f"{donde}: debe ser un objeto")
            continue
        extra = sorted(set(r) - _CAMPOS_RECURSO)
        if extra:
            problemas.append(f"{donde}: claves no reconocidas: " + ", ".join(map(str, extra)))
        nombre = r.get("nombre")
        if not isinstance(nombre, str) or not _NOMBRE_RECURSO.fullmatch(nombre):
            problemas.append(f"{donde}: nombre inválido (minúsculas, dígitos y guiones, 2 a 63)")
        elif nombre in nombres:
            problemas.append(f"{donde}: nombre repetido ({nombre})")
        else:
            nombres.add(nombre)
        etiqueta = f"recursos_externos «{nombre}»" if isinstance(nombre, str) and nombre else donde
        if r.get("tipo") not in TIPOS_RECURSO_EXTERNO:
            problemas.append(f"{etiqueta}: tipo debe ser uno de {', '.join(TIPOS_RECURSO_EXTERNO)}")
        if len(str(r.get("descripcion") or "").strip()) < 20:
            problemas.append(f"{etiqueta}: la descripción debe decir qué hace y por qué existe (mínimo 20 caracteres)")
        ubicacion = str(r.get("ubicacion") or "").strip()
        if not ubicacion or len(ubicacion) > 300:
            problemas.append(f"{etiqueta}: declare dónde vive o corre (ubicacion, hasta 300 caracteres)")
        elif _PARECE_SECRETO.search(ubicacion) or _URL_CON_CREDENCIALES.search(ubicacion):
            problemas.append(f"{etiqueta}: la ubicación no puede llevar usuario, clave ni tokens")
        acceso = r.get("acceso")
        if acceso != "ninguno" and acceso not in declarados:
            problemas.append(f"{etiqueta}: acceso debe ser «ninguno» o el nombre de un secreto declarado en secrets")
        if not isinstance(r.get("escribe_datos"), bool):
            problemas.append(f"{etiqueta}: escribe_datos debe ser true o false")
        if not _CORREO_AGP.fullmatch(str(r.get("responsable") or "")):
            problemas.append(f"{etiqueta}: responsable debe ser un correo @agpglass.com")
    return problemas
