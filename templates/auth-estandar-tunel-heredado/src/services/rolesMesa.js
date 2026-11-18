// Cliente de la API de roles y secretos de la Mesa (túnel de la spec 018 de la Mesa): la pantalla estándar de «Configuración» habla directo con la Mesa con el
// id_token de Microsoft de quien administra; la Mesa verifica que el token sea de ESTA app y que el desarrollo sea este, valida cada cambio y lo aplica.
// El desarrollo no escribe roles ni toca el vault: PIDE, y la Mesa decide. Los valores de los secretos viajan una vez y nunca se devuelven.
import { appInfo } from "../config/msal";

export class ErrorMesa extends Error {}

/** `mesaUrl` e `idProyecto` los entrega la API del desarrollo en `GET /api/config` → `roles` (appInfo.roles). `getAuthToken`: el de AuthContext. */
export function crearClienteMesa({ mesaUrl, idProyecto, getAuthToken, enviar = (typeof fetch === "function" ? fetch : null) }) {
  const base = `${String(mesaUrl).replace(/\/$/, "")}/api/roles-app/${encodeURIComponent(idProyecto)}`;

  async function llamar(ruta, { method = "GET", body } = {}) {
    if (!enviar) throw new ErrorMesa("Este navegador no puede conectarse con la Mesa de Ayuda.");
    const token = await getAuthToken();
    if (!token) throw new ErrorMesa("Tu sesión venció. Cierra sesión y vuelve a entrar.");
    let respuesta;
    try {
      respuesta = await enviar(`${base}${ruta}`, {
        method,
        headers: { Authorization: `Bearer ${token}`, Accept: "application/json", ...(body ? { "Content-Type": "application/json" } : {}) },
        body: body ? JSON.stringify(body) : undefined,
      });
    } catch {
      throw new ErrorMesa("No hay conexión con la Mesa de Ayuda. Intenta de nuevo en unos minutos.");
    }
    const cuerpo = await respuesta.json().catch(() => ({}));
    if (!respuesta.ok) throw new ErrorMesa(cuerpo?.message || `La Mesa de Ayuda respondió ${respuesta.status}.`);
    return cuerpo.data;
  }

  return {
    estado: () => llamar("/estado"),
    peticiones: () => llamar("/peticiones"),
    /** `cambio`: { accion, ... } de la spec 013 (asignar_rol_acceso, quitar_rol, guardar_perfil, borrar_perfil, marcar_vista_general...) más
     *  `justificacion` y `criterio` si la persona es de otra área. La Mesa autoriza al instante o rechaza con el motivo. */
    solicitar: (cambio) => llamar("/solicitudes", { method: "POST", body: cambio }),
    cancelar: (idSolicitud) => llamar(`/peticiones/${encodeURIComponent(idSolicitud)}`, { method: "DELETE" }),
    directorio: async (q) => {
      const lista = await llamar(`/directorio?q=${encodeURIComponent(String(q).trim())}`);
      return Array.isArray(lista) ? lista : [];
    },
    secretos: () => llamar("/secretos"),
    cargarSecreto: (nombre, valor) => llamar(`/secretos/${encodeURIComponent(nombre)}`, { method: "PUT", body: { valor } }),
    reiniciar: () => llamar("/secretos/reiniciar", { method: "POST" }),
  };
}

/** El cliente de este desarrollo, o null si la Mesa no está configurada (ROLES_DESDE_MESA apagado): entonces la pantalla lo dice y no hace nada. */
export function clienteDeEsteDesarrollo(getAuthToken) {
  const roles = appInfo.roles;
  return roles?.mesaUrl && roles?.idProyecto ? crearClienteMesa({ mesaUrl: roles.mesaUrl, idProyecto: roles.idProyecto, getAuthToken }) : null;
}
