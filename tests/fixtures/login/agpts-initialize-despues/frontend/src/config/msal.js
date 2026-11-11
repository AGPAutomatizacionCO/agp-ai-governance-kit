import { PublicClientApplication } from "@azure/msal-browser";

// Login estándar de AGP (MSAL en el navegador, PKCE, SIN secreto de cliente).
// El tenant y la aplicación de Entra ID NO se escriben aquí: los entrega la API en GET /api/config y se cargan con cargarConfigMsal() ANTES
// de crear la instancia de MSAL (ver main.jsx.example). La Mesa registra la aplicación de login del desarrollo al desplegarlo.
export const msalConfig = {
  auth: {
    clientId: "",
    authority: "https://login.microsoftonline.com/organizations",
    redirectUri: window.location.origin,
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
function getMsalInstance() {
  if (!_instance) _instance = new PublicClientApplication(msalConfig);
  return _instance;
}

// MSAL v3+ requiere initialize() antes de cualquier operación de la instancia.
// Compartir la promesa evita inicializaciones duplicadas en StrictMode y entre llamadas concurrentes.
let _inicializacion = null;
export function msalListo() {
  if (!_inicializacion) {
    _inicializacion = getMsalInstance().initialize().catch((error) => {
      // Permite reintentar si falló la inicialización (por ejemplo, una interrupción transitoria).
      _inicializacion = null;
      throw error;
    });
  }
  return _inicializacion;
}

// Toda operación pasa por aquí para que no se use PublicClientApplication antes de inicializarla.
export async function usarMsalInicializado(operacion) {
  await msalListo();
  return operacion(getMsalInstance());
}

export function esErrorMsalSinInicializar(error) {
  return error?.errorCode === "uninitialized_public_client_application"
    || String(error?.message || "").includes("uninitialized_public_client_application");
}
