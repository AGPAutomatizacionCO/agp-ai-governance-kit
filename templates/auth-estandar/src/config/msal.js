import { PublicClientApplication } from "@azure/msal-browser";

// Login estándar de AGP (MSAL en el navegador, PKCE, SIN secreto de cliente).
// El tenant y la aplicación de Entra ID NO se escriben aquí: los entrega la API en GET /api/config y se cargan con cargarConfigMsal() ANTES
// de crear la instancia de MSAL (ver main.jsx.example). La Mesa registra la aplicación de login del desarrollo al desplegarlo.
// MSAL 5 (@azure/msal-browser 5.x) exige una PÁGINA PUENTE dedicada para el retorno del login y del logout: el popup vuelve a esta ruta, la página
// solo entrega la respuesta a la ventana principal (src/auth/redirect.js) y no monta la aplicación. Si el retorno cae en la raíz, el popup recarga
// la pantalla de login y el acceso nunca se completa («Error al iniciar sesión. Intenta de nuevo.»). Esta ruta debe ser EXACTAMENTE `redirectUriPath`
// de .agp/entra.yaml: es la que la Mesa registra en Entra ID (OBLIGATORIOS-DEL-DESARROLLO.md §6).
export const RUTA_RETORNO_MSAL = "/auth/redirect";

export const msalConfig = {
  auth: {
    clientId: "",
    authority: "https://login.microsoftonline.com/organizations",
    redirectUri: `${window.location.origin}${RUTA_RETORNO_MSAL}`,
    postLogoutRedirectUri: `${window.location.origin}${RUTA_RETORNO_MSAL}`,
  },
  // localStorage (no sessionStorage): la sesión se comparte entre pestañas y sobrevive a cerrar el navegador, como se espera de un login único.
  cache: { cacheLocation: "localStorage" },
};

export const loginRequest = { scopes: ["User.Read"], prompt: "select_account" };

// Nombre propio del desarrollo: lo entrega la API (appName de /api/config, que la Mesa fija al desplegar). null = sin nombre.
// El contacto de la pantalla sin acceso (administradores[0] de .agp/entra.yaml) llega igual: contactoNombre y contactoCorreo.
// `roles`: { mesaUrl, idProyecto } cuando la gestión de roles desde la Mesa está activa (ROLES_DESDE_MESA); null si no.
export const appInfo = { nombre: null, contactoNombre: null, contactoCorreo: null, roles: null };

// Carga la configuración del login que entrega la API. Devuelve true si quedó configurado. Si la API no responde o no la trae, la pantalla de
// login lo informa (no hay valores de respaldo: un desarrollo sin registro de login no debe iniciar sesión contra otra aplicación).
export async function cargarConfigMsal(apiUrl, enviar = (typeof fetch === "function" ? fetch : null)) {
  if (!enviar) return false;
  try {
    const respuesta = await enviar(`${apiUrl}/api/config`, { headers: { Accept: "application/json" } });
    if (!respuesta.ok) return false;
    const cuerpo = await respuesta.json();
    const nombre = typeof cuerpo?.appName === "string" ? cuerpo.appName.trim() : "";
    if (nombre) appInfo.nombre = nombre.slice(0, 80);
    if (typeof cuerpo?.contactoNombre === "string" && cuerpo.contactoNombre.trim()) appInfo.contactoNombre = cuerpo.contactoNombre.trim().slice(0, 80);
    if (typeof cuerpo?.contactoCorreo === "string" && cuerpo.contactoCorreo.trim()) appInfo.contactoCorreo = cuerpo.contactoCorreo.trim().slice(0, 120);
    const roles = cuerpo?.roles;
    if (typeof roles?.mesaUrl === "string" && typeof roles?.idProyecto === "string" && roles.mesaUrl && roles.idProyecto) appInfo.roles = { mesaUrl: roles.mesaUrl, idProyecto: roles.idProyecto };
    const msal = cuerpo?.msal;
    if (!msal?.clientId || !msal?.tenantId) return false;
    msalConfig.auth.clientId = msal.clientId;
    msalConfig.auth.authority = `https://login.microsoftonline.com/${msal.tenantId}`;
    return true;
  } catch (_) {
    return false;
  }
}

let _instance = null;
export function getMsalInstance() {
  if (!_instance) _instance = new PublicClientApplication(msalConfig);
  return _instance;
}
