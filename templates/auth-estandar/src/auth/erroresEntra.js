// Ayudas puras para mostrar el error REAL que devuelve Microsoft Entra ID al volver del login (sin MSAL ni DOM, para poder probarlas).
// Regla de seguridad: del retorno solo se leen DOS datos, el `error` (letras y guion bajo) y el código `AADSTS#####` de `error_description`.
// Nunca se muestra ni se guarda el resto (code, state, tokens, texto libre de Microsoft).

const ERROR = /(?:^|[?&#])error=([a-z_]{1,60})(?=&|$)/i;
const DESCRIPCION = /(?:^|[?&#])error_description=([^&]*)/i;
export const AADSTS = /AADSTS\d{4,7}/;

/** {error, aadsts} del hash y la query del retorno, o null si Microsoft no devolvió un error. Cualquiera de los dos puede venir vacío. */
export function extraerErrorEntra(hash, search) {
  const texto = `${hash || ""}&${search || ""}`;
  const error = ERROR.exec(texto)?.[1] || "";
  let descripcion = "";
  const bruta = DESCRIPCION.exec(texto)?.[1] || "";
  try {
    descripcion = decodeURIComponent(bruta.replace(/\+/g, " "));
  } catch {
    descripcion = bruta;
  }
  const aadsts = AADSTS.exec(descripcion)?.[0] || "";
  return error || aadsts ? { error, aadsts } : null;
}

/** Código AADSTS dentro de un error de MSAL (`subError`, `errorMessage` o `message`), mirando solo sus primeros 300 caracteres. */
export function aadstsDeErrorMsal(e) {
  for (const campo of [e?.subError, e?.errorMessage, e?.message]) {
    const hallado = AADSTS.exec(String(campo || "").slice(0, 300))?.[0];
    if (hallado) return hallado;
  }
  return "";
}

const CAUSAS = {
  AADSTS50105: "Tu usuario no está asignado a esta aplicación en Entra. Pide a TI que te asigne o que quite «asignación requerida».",
  AADSTS65001: "Falta el consentimiento de la aplicación. TI debe conceder el consentimiento del administrador (User.Read).",
  AADSTS50011: "El URI de retorno no coincide con el registrado en Entra. TI debe registrar <sitio>/auth/redirect como «Aplicación de una sola página».",
  AADSTS700016: "Microsoft no encuentra la aplicación (clientId) en este directorio. Avisa a TI.",
  AADSTS9002326: "El URI de retorno debe registrarse como «Aplicación de una sola página» (SPA), no como Web. Avisa a TI.",
  AADSTS50020: "Tu cuenta no pertenece al directorio de AGP. Entra con tu correo corporativo.",
};

const CAUSAS_POR_ERROR = {
  access_denied: "Se canceló o se negó el acceso. Vuelve a intentarlo y acepta los permisos.",
  consent_required: "Falta el consentimiento de la aplicación. TI debe concederlo.",
  interaction_required: "Microsoft pide completar un paso adicional. Cierra la ventana y vuelve a entrar.",
  server_error: "Microsoft tuvo un error al iniciar sesión. Espera un minuto e intenta de nuevo; si persiste, informa a TI con el código.",
};

/** Qué hacer ante un error de Entra (texto corto), según el código AADSTS o, si no hay, el `error`. Cadena vacía si no se conoce la causa. */
export function causaProbable({ error = "", aadsts = "" } = {}) {
  return CAUSAS[aadsts] || CAUSAS_POR_ERROR[error] || "";
}

/** Texto del puente cuando la respuesta no se pudo entregar. Con error de Entra muestra solo `error` y AADSTS; sin él, la instrucción de siempre. */
export function textoDelPuente(errorEntra, aplicacion) {
  const base = `No se pudo completar el acceso. Cierra esta ventana y vuelve a intentarlo desde ${aplicacion}.`;
  if (!errorEntra) return base;
  const codigo = [errorEntra.error, errorEntra.aadsts && `(${errorEntra.aadsts})`].filter(Boolean).join(" ");
  const causa = causaProbable(errorEntra);
  return `Microsoft respondió: ${codigo}. ${causa || "Informa a TI con este código."} ${base}`;
}
