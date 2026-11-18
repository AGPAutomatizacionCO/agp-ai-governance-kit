// Cliente de la API PROPIA del desarrollo para la pantalla «Configuración» (backend/src/flask_config/bp_configuracion.py). No habla con la Mesa: usa el id_token de
// Microsoft de quien administra y el backend del desarrollo decide, vuelve a leer sus tablas y audita. El valor de un secreto viaja una vez y nunca se devuelve.
export class ErrorConfiguracion extends Error {
  constructor(mensaje, estado = 0) { super(mensaje); this.estado = estado; }
}

/** `base`: "" con la imagen de un solo contenedor (mismo origen). `getAuthToken`: el de AuthContext. */
export function crearClienteLocal({ getAuthToken, base = "", enviar = (typeof fetch === "function" ? fetch : null) }) {
  const raiz = `${String(base).replace(/\/$/, "")}/api/configuracion`;

  async function llamar(ruta, { method = "GET", body } = {}) {
    if (!enviar) throw new ErrorConfiguracion("Este navegador no puede conectarse con el servidor.");
    const token = await getAuthToken();
    if (!token) throw new ErrorConfiguracion("Tu sesión venció. Cierra sesión y vuelve a entrar.", 401);
    let respuesta;
    try {
      respuesta = await enviar(`${raiz}${ruta}`, {
        method,
        headers: { Authorization: `Bearer ${token}`, Accept: "application/json", ...(body ? { "Content-Type": "application/json" } : {}) },
        body: body ? JSON.stringify(body) : undefined,
      });
    } catch {
      throw new ErrorConfiguracion("No hay conexión con el servidor. Intenta de nuevo en unos minutos.");
    }
    const cuerpo = await respuesta.json().catch(() => ({}));
    if (!respuesta.ok) throw new ErrorConfiguracion(cuerpo?.message || `El servidor respondió ${respuesta.status}.`, respuesta.status);
    return cuerpo;
  }

  return {
    estado: async () => (await llamar("/estado")).data,
    /** `perfil` null quita el acceso. El actor lo decide el servidor con el token: no se envía. */
    asignar: async (correo, perfil) => (await llamar("/personas", { method: "PUT", body: { correo, perfil } })).data,
    directorio: async (q) => {
      const r = await llamar(`/directorio?q=${encodeURIComponent(String(q).trim())}`);
      return Array.isArray(r.data) ? r.data : [];
    },
    secretos: async () => (await llamar("/secretos")).data,
    /** El valor viaja una sola vez; la respuesta trae el nombre y si quedó registrado en la auditoría, nunca el valor. */
    cargarSecreto: async (nombre, valor) => { const r = await llamar(`/secretos/${encodeURIComponent(nombre)}`, { method: "PUT", body: { valor } }); return { ...r.data, aviso: r.message || null }; },
    actividad: async () => { const r = await llamar("/actividad"); return Array.isArray(r.data) ? r.data : []; },
  };
}

/** El cliente de este desarrollo (misma API, mismo origen salvo que `base` diga otra cosa). */
export function clienteDeEsteDesarrollo(getAuthToken, base = "") {
  return crearClienteLocal({ getAuthToken, base });
}
