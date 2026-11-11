import { broadcastResponseToMainFrame } from "@azure/msal-browser/redirect-bridge";

// Página puente del login y del logout con MSAL 5 (ruta /auth/redirect; ver config/msal.js). Solo entrega la respuesta de Microsoft a la ventana
// principal: nunca monta la aplicación, la pantalla de login ni el encabezado. No agregues nada más aquí.
void broadcastResponseToMainFrame().catch(() => {
  const estado = document.getElementById("auth-status");
  if (estado) estado.textContent = "No se pudo completar el acceso. Cierra esta ventana y vuelve a intentarlo desde la aplicación.";
});
