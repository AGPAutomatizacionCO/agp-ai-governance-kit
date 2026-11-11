import { beforeEach, describe, expect, it, vi } from "vitest";

const broadcast = vi.hoisted(() => vi.fn());
vi.mock("@azure/msal-browser/redirect-bridge", () => ({ broadcastResponseToMainFrame: broadcast }));

beforeEach(() => {
  vi.resetModules();
  broadcast.mockReset();
  document.body.innerHTML = '<p id="auth-status">Completando acceso</p>';
});

describe("página puente de MSAL 5 (/auth/redirect)", () => {
  it("entrega una sola respuesta y no monta otra pantalla de login", async () => {
    broadcast.mockResolvedValue(undefined);
    await import("./redirect");
    expect(broadcast).toHaveBeenCalledTimes(1);
    expect(document.querySelector("#root")).toBeNull();
    expect(document.querySelector('[data-agp-login="estandar"]')).toBeNull();
  });
  it("un fallo muestra una instrucción segura sin copiar datos del proveedor", async () => {
    broadcast.mockRejectedValue(new Error("NO-MOSTRAR-RESPUESTA-OAUTH"));
    await import("./redirect");
    await Promise.resolve();
    expect(document.body.textContent).toContain("No se pudo completar el acceso");
    expect(document.body.textContent).not.toContain("NO-MOSTRAR");
  });
  it("si Microsoft devolvió un error, muestra solo el error y el código AADSTS con su causa, nunca el resto de la respuesta", async () => {
    window.history.replaceState(null, "", "/auth/redirect#error=access_denied&error_description=AADSTS50105%3A+not+assigned+SECRETO-LIBRE&state=ESTADO-OCULTO&code=CODIGO-OCULTO");
    broadcast.mockRejectedValue(new Error("fallo del puente"));
    await import("./redirect");
    await Promise.resolve();
    expect(document.body.textContent).toContain("Microsoft respondió: access_denied (AADSTS50105)");
    for (const oculto of ["SECRETO-LIBRE", "ESTADO-OCULTO", "CODIGO-OCULTO"]) expect(document.body.textContent).not.toContain(oculto);
    window.history.replaceState(null, "", "/");
  });
});
