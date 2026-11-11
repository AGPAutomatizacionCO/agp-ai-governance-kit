import { broadcastResponseToMainFrame } from "@azure/msal-browser/redirect-bridge";
import { extraerErrorEntra, textoDelPuente } from "./erroresEntra";

// Página puente del login y del logout con MSAL 5 (ruta /auth/redirect; ver config/msal.js). Solo entrega la respuesta de Microsoft a la ventana
// principal: nunca monta la aplicación, la pantalla de login ni el encabezado. No agregues nada más aquí.
//
// MSAL limpia el hash antes de relanzar un error de Entra: se lee ANTES y solo se conservan el `error` y el código AADSTS (nunca code, state ni tokens).
const errorEntra = extraerErrorEntra(globalThis.location?.hash ?? "", globalThis.location?.search ?? "");

void broadcastResponseToMainFrame().catch(() => {
  const estado = document.getElementById("auth-status");
  if (estado) estado.textContent = textoDelPuente(errorEntra, "la aplicación");
});
