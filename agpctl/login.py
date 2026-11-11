"""`agpctl login check`: el retorno del login con MSAL 5 (página puente), comprobado por texto y solo lectura.

Con `@azure/msal-browser` 5.x el popup de login vuelve a `redirectUri`, y esa ruta debe ser una página puente que llame a
`broadcastResponseToMainFrame()`. Con `redirectUri` en la raíz el popup recarga la pantalla de login y la persona ve «Error al iniciar sesión.
Intenta de nuevo.» sin error en la consola. Este chequeo comprueba, sin ejecutar nada ni leer secretos:

  1. la versión de `@azure/msal-browser` del `package.json` del frontend (con 5.x o superior aplican las reglas siguientes);
  2. que exista el script puente (importa `broadcastResponseToMainFrame` de `@azure/msal-browser/redirect-bridge`) y la página `auth/redirect.html`
     (sin `id="root"`: nunca monta la aplicación);
  3. que `redirectUri` y `postLogoutRedirectUri` de la configuración de MSAL apunten a la ruta puente y no a la raíz;
  4. que esa ruta sea EXACTAMENTE `redirectUriPath` de `.agp/entra.yaml` (lo que la Mesa registra en Entra ID);
  5. que la compilación incluya la página (entrada de Vite) y que algún servidor/configuración exponga la ruta;
  6. que la instancia de MSAL se inicialice (`initialize()` o `MsalProvider`) antes de llamar a loginPopup/acquireToken*/getAllAccounts (cualquier flujo, MSAL >= 3).

Regla y guía: OBLIGATORIOS-DEL-DESARROLLO.md §6 e INTEGRAR-MSAL.md.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

RUTA_PUENTE = "/auth/redirect"
GUIA = "INTEGRAR-MSAL.md"
_OMITIR = {"node_modules", ".git", "dist", "build", ".venv", "venv", "__pycache__", ".next"}
_EXTENSIONES_SERVIDOR = {".js", ".mjs", ".cjs", ".py", ".ts", ".json", ".conf", ".yaml", ".yml"}
_CODIGO_FRONTEND = {".js", ".jsx", ".ts", ".tsx", ".mjs"}
_VERSION = re.compile(r"(\d+)")
_REDIRECT_URI = re.compile(r"\bredirectUri\s*:\s*([^\n]+)")
_POST_LOGOUT = re.compile(r"\bpostLogoutRedirectUri\s*:\s*([^\n]+)")
_RAIZ = re.compile(r"^[`'\"]?\$?\{?\s*window\.location\.origin\s*\}?[`'\"]?\s*[,}]?\s*$")
_CONSTANTE_RUTA = re.compile(r"""RUTA_RETORNO_MSAL\s*=\s*['"`]([^'"`]+)['"`]""")
_ID_RAIZ = re.compile(r"""id\s*=\s*["']root["']""")
_POPUP = re.compile(r"\b(?:loginPopup|acquireTokenPopup|logoutPopup)\b")
_REDIRECT = re.compile(r"\b(?:loginRedirect|acquireTokenRedirect|logoutRedirect|handleRedirectPromise)\b")
_NUEVA_INSTANCIA = re.compile(r"\bnew\s+PublicClientApplication\s*\(")
_OPERACION_MSAL = re.compile(r"\.(?:loginPopup|loginRedirect|acquireToken\w*|getAllAccounts|getActiveAccount|logoutPopup|logoutRedirect|handleRedirectPromise|ssoSilent)\s*\(")
_INICIALIZA = re.compile(r"\.initialize\s*\(|\bMsalProvider\b|\bcreateStandardPublicClientApplication\b|\bcreatePublicClientApplication\b")
_ES_PRUEBA = re.compile(r"(?:\.test\.|\.spec\.|[\/](?:tests?|__tests__)[\/])")


def _archivos(raiz: Path):
    for ruta in sorted(raiz.rglob("*")):
        if ruta.is_file() and not (set(ruta.relative_to(raiz).parts) & _OMITIR):
            yield ruta


def _leer(ruta: Path) -> str:
    try:
        return ruta.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _frontends(repo: Path) -> list[tuple[Path, str]]:
    """[(carpeta, versión declarada de @azure/msal-browser)] de cada package.json (raíz y un nivel) que la declara."""
    encontrados = []
    for paquete in sorted(repo.glob("package.json")) + sorted(repo.glob("*/package.json")):
        if set(paquete.relative_to(repo).parts) & _OMITIR:
            continue
        try:
            datos = json.loads(_leer(paquete))
        except ValueError:
            continue
        version = {**(datos.get("devDependencies") or {}), **(datos.get("dependencies") or {})}.get("@azure/msal-browser")
        if version:
            encontrados.append((paquete.parent, str(version)))
    return encontrados


def _flujo(carpeta: Path) -> str:
    """«popup» si el código de la app abre la ventana emergente de Microsoft (loginPopup/acquireTokenPopup/logoutPopup), «redirect» si SOLO usa
    el flujo por redirección (loginRedirect/acquireTokenRedirect/logoutRedirect) y «desconocido» si no hay ninguna llamada (se trata como popup,
    que es lo que trae la plantilla). Los archivos de prueba no cuentan."""
    popup = redirect = False
    for f in _archivos(carpeta):
        if f.suffix not in _CODIGO_FRONTEND or _ES_PRUEBA.search("/" + f.relative_to(carpeta).as_posix()):
            continue
        texto = _leer(f)
        popup = popup or bool(_POPUP.search(texto))
        redirect = redirect or bool(_REDIRECT.search(texto))
    if popup:
        return "popup"
    return "redirect" if redirect else "desconocido"


def _mayor(version: str) -> int | None:
    coincidencia = _VERSION.search(version)
    return int(coincidencia.group(1)) if coincidencia else None


def _ruta_de(expresion: str) -> str | None:
    """La ruta de una expresión de redirectUri (`${origin}/auth/redirect`, `origin + "/auth/redirect"`)."""
    limpia = re.sub(r"\$\{[^}]*\}", "", expresion)
    coincidencia = re.search(r"(/[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*)", limpia)
    return coincidencia.group(1) if coincidencia else None


def _revisar_frontend(repo: Path, carpeta: Path, version: str, issues: list[str], avisos: list[str]) -> str | None:
    etiqueta = carpeta.relative_to(repo).as_posix() or "."
    todos = list(_archivos(carpeta))
    codigo = [f for f in todos if f.suffix in _CODIGO_FRONTEND]
    html = [f for f in todos if f.suffix == ".html"]

    # 2. script y página puente
    puente_js = [f for f in codigo if "broadcastResponseToMainFrame" in _leer(f) and "@azure/msal-browser/redirect-bridge" in _leer(f)]
    if not puente_js:
        issues.append(
            f"{etiqueta}: MSAL {version} exige una página puente para el retorno del login y no hay ningún script que llame a "
            "broadcastResponseToMainFrame() (import desde '@azure/msal-browser/redirect-bridge'). Cómo corregirlo: copia src/auth/redirect.js "
            f"de templates/auth-estandar/ del kit (ver {GUIA})."
        )
    paginas = [f for f in html if f.as_posix().endswith("auth/redirect.html")]
    if not paginas:
        issues.append(
            f"{etiqueta}: falta la página auth/redirect.html (la ruta {RUTA_PUENTE} no tiene a dónde volver). Cómo corregirlo: copia "
            f"templates/auth-estandar/auth/redirect.html del kit (ver {GUIA})."
        )
    for pagina in paginas:
        if _ID_RAIZ.search(_leer(pagina)):
            issues.append(
                f"{pagina.relative_to(repo).as_posix()}: la página puente no debe montar la aplicación (tiene id=\"root\"): con eso el popup recarga el "
                "login. Debe contener solo el aviso de estado y el script del puente."
            )

    # 3. redirectUri y postLogoutRedirectUri
    ruta = None
    configuraciones = [f for f in codigo if re.search(r"redirectUri\s*:", _leer(f)) and re.search(r"PublicClientApplication|msalConfig|authority", _leer(f))]
    if not configuraciones:
        avisos.append(f"{etiqueta}: no encontré la configuración de MSAL (redirectUri) para comprobarla; revisa a mano que apunte a {RUTA_PUENTE}.")
    for configuracion in configuraciones:
        texto = _leer(configuracion)
        nombre = configuracion.relative_to(repo).as_posix()
        constante = _CONSTANTE_RUTA.search(texto)
        for clave, patron in (("redirectUri", _REDIRECT_URI), ("postLogoutRedirectUri", _POST_LOGOUT)):
            lineas = [m.group(1).strip() for m in patron.finditer(texto) if not m.group(1).strip().startswith("//")]
            if not lineas:
                if clave == "postLogoutRedirectUri":
                    issues.append(
                        f"{nombre}: falta postLogoutRedirectUri: el cierre de sesión con popup también vuelve a la página puente. "
                        "Cómo corregirlo: agrega `postLogoutRedirectUri: <igual que redirectUri>` a la configuración de MSAL."
                    )
                continue
            expresion = lineas[0]
            usa_constante = bool(constante) and "RUTA_RETORNO_MSAL" in expresion
            if _RAIZ.match(expresion) or not (_ruta_de(expresion) or usa_constante):
                issues.append(
                    f"{nombre}: {clave} apunta a la raíz del sitio ({expresion.rstrip(',')}). Con MSAL {version} el popup recarga la pantalla de login y la persona ve "
                    f"«Error al iniciar sesión. Intenta de nuevo.» sin error en la consola. Cómo corregirlo: {clave}: `${{window.location.origin}}{RUTA_PUENTE}` "
                    f"(y `redirectUriPath: {RUTA_PUENTE}` en .agp/entra.yaml)."
                )
            elif clave == "redirectUri":
                ruta = (constante.group(1) if usa_constante else _ruta_de(expresion)) or ruta

    # 5. compilación: entrada de Vite
    vite = [f for f in todos if re.fullmatch(r"vite\.config\.[cm]?[jt]s", f.name)]
    if vite and not any("auth/redirect.html" in _leer(f) for f in vite):
        issues.append(
            f"{vite[0].relative_to(repo).as_posix()}: la compilación no incluye la página puente: Vite solo genera index.html y {RUTA_PUENTE} devolvería la SPA. "
            "Cómo corregirlo: agrega `build.rollupOptions.input: { main: 'index.html', redirect: 'auth/redirect.html' }` (ver vite.config.example.js del kit)."
        )
    elif not vite:
        avisos.append(f"{etiqueta}: no hay vite.config.*; comprueba a mano que tu compilación genere auth/redirect.html.")
    return ruta


def _sin_comentarios(texto: str) -> str:
    """El código sin comentarios `//` ni `/* */`: una frase como «sin MsalProvider» en un comentario no inicializa nada."""
    texto = re.sub(r"/\*.*?\*/", "", texto, flags=re.DOTALL)
    return re.sub(r"(?m)^\s*//.*$|(?<=[\s;,)])//[^\n]*$", "", texto)


def _revisar_inicializacion(repo: Path, carpeta: Path, version: str, issues: list[str]) -> None:
    """MSAL (>= 3) exige `await instance.initialize()` antes de cualquier operación. Si el código crea `new PublicClientApplication(...)` a mano, llama a
    loginPopup/acquireToken*/getAllAccounts... y en ningún sitio inicializa (ni `MsalProvider` ni `createStandardPublicClientApplication`), MSAL lanza
    `uninitialized_public_client_application` ANTES de abrir el popup: la persona ve «Error al iniciar sesión» al instante y no hay ninguna petición en Network."""
    crea = opera = inicializa = False
    for f in _archivos(carpeta):
        if f.suffix not in _CODIGO_FRONTEND or _ES_PRUEBA.search("/" + f.relative_to(carpeta).as_posix()):
            continue
        texto = _sin_comentarios(_leer(f))
        crea = crea or bool(_NUEVA_INSTANCIA.search(texto))
        opera = opera or bool(_OPERACION_MSAL.search(texto))
        inicializa = inicializa or bool(_INICIALIZA.search(texto))
    if crea and opera and not inicializa:
        etiqueta = carpeta.relative_to(repo).as_posix() or "."
        issues.append(
            f"{etiqueta}: el código crea `new PublicClientApplication` y llama a loginPopup/acquireToken*/getAllAccounts sin `initialize()` ni MsalProvider. "
            f"MSAL {version} lanza `uninitialized_public_client_application` ANTES de abrir el popup: la persona ve «Error al iniciar sesión. Intenta de nuevo.» al instante y "
            "no hay ninguna petición en Network. Cómo corregirlo: copia `msalListo()` y `usarMsalInicializado()` de templates/auth-estandar/src/config/msal.js y usa "
            f"`await usarMsalInicializado((msal) => msal.loginPopup(...))` en cada operación (ver {GUIA}, «MSAL exige initialize()»)."
        )


def _servidor_expone(repo: Path, ruta: str) -> bool:
    """¿Algún servidor o configuración de hosting (rutas Flask/Node, serve.json, staticwebapp.config.json, nginx) menciona la ruta?"""
    clave = ruta.lstrip("/")
    for archivo in _archivos(repo):
        relativa = archivo.relative_to(repo).parts
        nombre = archivo.name
        if archivo.suffix not in _EXTENSIONES_SERVIDOR or nombre.startswith(("test_", "vite.config")) or ".test." in nombre or relativa[0] in {"tests", "test"}:
            continue
        # el propio código del frontend (src/, auth/) no cuenta: se busca quién SIRVE la ruta
        if relativa[0] in {"src", "auth"} or (len(relativa) > 1 and relativa[1] in {"src", "auth"} and archivo.suffix in _CODIGO_FRONTEND):
            continue
        if clave in _leer(archivo):
            return True
    return False


def _patron_dockerignore(patron: str) -> re.Pattern:
    """Un patrón de .dockerignore como expresión regular (`**` cruza carpetas, `*` y `?` no)."""
    salida, i = [], 0
    while i < len(patron):
        c = patron[i]
        if c == "*":
            if patron[i : i + 2] == "**":
                salida.append(".*")
                i += 2
                if patron[i : i + 1] == "/":
                    i += 1
                    salida[-1] = "(?:.*/)?"
                continue
            salida.append("[^/]*")
        elif c == "?":
            salida.append("[^/]")
        else:
            salida.append(re.escape(c))
        i += 1
    return re.compile("".join(salida))


def excluido_por_dockerignore(texto: str, ruta: str) -> bool:
    """¿Deja fuera de la imagen `ruta` (relativa al contexto) este .dockerignore? Gana la última regla que coincide; una regla coincide con la ruta o con una carpeta padre."""
    excluido = False
    partes = ruta.strip("/").split("/")
    padres = ["/".join(partes[: n + 1]) for n in range(len(partes))]
    for linea in texto.splitlines():
        regla = linea.strip()
        if not regla or regla.startswith("#"):
            continue
        negada = regla.startswith("!")
        regla = regla.lstrip("!").strip().lstrip("/").rstrip("/")
        if not regla:
            continue
        patron = _patron_dockerignore(regla)
        if any(patron.fullmatch(p) for p in padres):
            excluido = not negada
    return excluido


def _revisar_dockerignore(repo: Path, carpeta: Path, issues: list[str]) -> None:
    """El .dockerignore (lista blanca en AGPTS) debe dejar pasar la página puente y su script: si no, la imagen se construye sin ellas y el build o el login fallan."""
    paginas = [f for f in _archivos(carpeta) if f.as_posix().endswith("auth/redirect.html")]
    scripts = [f for f in _archivos(carpeta) if f.suffix in _CODIGO_FRONTEND and re.fullmatch(r"redirect\.[cm]?[jt]sx?", f.name) and f.parent.name == "auth"]
    for contexto in dict.fromkeys([repo, carpeta]):
        ignorado = contexto / ".dockerignore"
        if not ignorado.is_file():
            continue
        texto = _leer(ignorado)
        for archivo in paginas + scripts:
            try:
                relativa = archivo.relative_to(contexto).as_posix()
            except ValueError:
                continue
            if excluido_por_dockerignore(texto, relativa):
                carpeta_puente = relativa.rsplit("/", 1)[0]
                issues.append(
                    f"{ignorado.relative_to(repo).as_posix()}: deja fuera de la imagen {relativa} (la página puente del login). La imagen se construye sin ella: el build falla o "
                    f"{RUTA_PUENTE} devuelve 404 y el login muestra «Error al iniciar sesión. Intenta de nuevo.». Cómo corregirlo: agrega `!{carpeta_puente}` "
                    f"(y, si usas lista blanca con `{carpeta.name}/*`, ponlo DESPUÉS de esa línea). Referencia: .dockerignore de AGP_CO_PEOPLE_AGPTS (ver {GUIA})."
                )


def check(repo: Path) -> dict:
    repo = Path(repo)
    issues: list[str] = []
    avisos: list[str] = []
    frontends = _frontends(repo)
    if not frontends:
        return {"valid": True, "issues": [], "avisos": [], "note": "no hay @azure/msal-browser en ningún package.json: nada que revisar del retorno del login"}
    ruta_codigo = None
    revisados = []
    aplica_msal5 = False
    for carpeta, version in frontends:
        mayor = _mayor(version)
        etiqueta = carpeta.relative_to(repo).as_posix() or "."
        flujo = _flujo(carpeta)
        revisados.append({"carpeta": etiqueta, "msalBrowser": version, "mayor": mayor, "flujo": flujo})
        if mayor is None or mayor >= 3:
            _revisar_inicializacion(repo, carpeta, version, issues)
        if mayor is not None and mayor >= 5 and flujo == "redirect":
            avisos.append(
                f"{etiqueta}: usa MSAL {version} con el flujo por REDIRECCIÓN (loginRedirect/logoutRedirect): la página puente no es necesaria y `redirectUri` en la raíz "
                f"funciona. Si algún día cambias a loginPopup, la página puente pasa a ser obligatoria (ver {GUIA}); `redirectUriPath` de .agp/entra.yaml debe seguir siendo "
                "el `redirectUri` que usa el código."
            )
            continue
        if mayor is not None and mayor < 5:
            avisos.append(f"{etiqueta}: @azure/msal-browser {version} (< 5): la página puente no es obligatoria; la plantilla del kit se prueba con 5.x.")
            continue
        if mayor is None:
            avisos.append(f"{etiqueta}: no pude leer la versión de @azure/msal-browser («{version}»); se aplican las reglas de MSAL 5. Fija una versión exacta (p. ej. 5.29.0).")
        aplica_msal5 = True
        ruta_codigo = _revisar_frontend(repo, carpeta, version, issues, avisos) or ruta_codigo
        _revisar_dockerignore(repo, carpeta, issues)
    if not aplica_msal5:
        return {"valid": not issues, "issues": issues, "avisos": avisos, "frontends": revisados}
    ruta = ruta_codigo or RUTA_PUENTE

    # 4. coincidencia con entra.yaml
    entra = repo / ".agp" / "entra.yaml"
    if entra.is_file():
        try:
            declarado = (yaml.safe_load(_leer(entra)) or {}).get("redirectUriPath")
        except yaml.YAMLError as exc:
            issues.append(f".agp/entra.yaml no es YAML válido: {exc}")
        else:
            if declarado != ruta:
                issues.append(
                    f".agp/entra.yaml: redirectUriPath es «{declarado}» y el código vuelve a «{ruta}». La Mesa registra en Entra ID lo que dice entra.yaml: si no coinciden, "
                    f"Entra rechaza el retorno. Cómo corregirlo: redirectUriPath: {ruta} (y vuelve a ejecutar la fase «entra» de la Mesa si el desarrollo ya estaba desplegado)."
                )
    else:
        avisos.append(".agp/entra.yaml no existe: no pude comprobar que redirectUriPath coincida con el retorno del código.")

    # 5. servidor
    if not _servidor_expone(repo, ruta):
        issues.append(
            f"ningún servidor ni configuración de hosting expone {ruta}: sin eso la ruta devuelve index.html (o 404) y el popup no vuelve. Cómo corregirlo: con Flask, registra bp_retorno_msal.py del kit; "
            f"con Node, una ruta que sirva dist/auth/redirect.html; con serve, public/serve.json con un rewrite; con Static Web Apps, una ruta en staticwebapp.config.json (ver {GUIA})."
        )
    return {"valid": not issues, "issues": issues, "avisos": avisos, "ruta": ruta, "frontends": revisados}
