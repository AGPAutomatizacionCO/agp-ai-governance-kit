import { existsSync, readFileSync, readdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { beforeEach, describe, expect, it, vi } from "vitest";

// MSAL (>= 3) exige initialize() antes de cualquier operación de la instancia. Sin eso `loginPopup` lanza `uninitialized_public_client_application`
// ANTES de abrir el popup: «Error al iniciar sesión» al instante y ninguna petición en Network (caso AGPTS, 2026-11-11).
const iniciar = vi.hoisted(() => vi.fn());
vi.mock("@azure/msal-browser", () => ({ PublicClientApplication: vi.fn(() => ({ initialize: iniciar, loginPopup: vi.fn(async () => "popup") })) }));

beforeEach(() => {
  vi.resetModules();
  iniciar.mockReset();
});

describe("msalListo / usarMsalInicializado", () => {
  it("la operación no corre hasta que initialize() termina", async () => {
    const orden = [];
    iniciar.mockImplementation(async () => { orden.push("initialize"); });
    const { usarMsalInicializado } = await import("../config/msal");
    await usarMsalInicializado(async (msal) => { orden.push("operacion"); return msal.loginPopup({}); });
    expect(orden).toEqual(["initialize", "operacion"]);
  });
  it("es idempotente: dos llamadas concurrentes inicializan una sola vez", async () => {
    iniciar.mockResolvedValue(undefined);
    const { msalListo } = await import("../config/msal");
    await Promise.all([msalListo(), msalListo(), msalListo()]);
    expect(iniciar).toHaveBeenCalledTimes(1);
  });
  it("si initialize() falla, la siguiente llamada vuelve a intentarlo", async () => {
    iniciar.mockRejectedValueOnce(new Error("transitorio")).mockResolvedValueOnce(undefined);
    const { msalListo } = await import("../config/msal");
    await expect(msalListo()).rejects.toThrow("transitorio");
    await expect(msalListo()).resolves.toBeUndefined();
    expect(iniciar).toHaveBeenCalledTimes(2);
  });
  it("reconoce el error de MSAL sin inicializar", async () => {
    const { esErrorMsalSinInicializar } = await import("../config/msal");
    expect(esErrorMsalSinInicializar({ errorCode: "uninitialized_public_client_application" })).toBe(true);
    expect(esErrorMsalSinInicializar(new Error("x uninitialized_public_client_application"))).toBe(true);
    expect(esErrorMsalSinInicializar(new Error("otro"))).toBe(false);
  });
});

describe("ningún archivo usa la instancia de MSAL sin inicializarla", () => {
  const raiz = resolve(dirname(fileURLToPath(import.meta.url)), "..");
  function archivos(carpeta, salida = []) {
    if (!existsSync(carpeta)) return salida;
    for (const e of readdirSync(carpeta, { withFileTypes: true })) {
      const ruta = join(carpeta, e.name);
      if (e.isDirectory()) { if (e.name !== "node_modules") archivos(ruta, salida); } else salida.push(ruta);
    }
    return salida;
  }
  it("quien llama a loginPopup/acquireToken*/getAllAccounts/logoutPopup pasa por usarMsalInicializado, msalListo o initialize()", () => {
    const malos = archivos(raiz)
      .filter((f) => /\.(jsx?|tsx?|mjs)$/.test(f) && !/\.test\./.test(f) && !/config[\/]msal\.js$/.test(f))
      .filter((f) => {
        const texto = readFileSync(f, "utf8");
        return /\.(loginPopup|acquireToken\w*|getAllAccounts|getActiveAccount|logoutPopup)\(/.test(texto) && !/usarMsalInicializado|msalListo|\.initialize\(/.test(texto);
      });
    expect(malos, "Estos archivos usan MSAL sin initialize() (ver INTEGRAR-MSAL.md): " + malos.join(", ")).toEqual([]);
  });
});
