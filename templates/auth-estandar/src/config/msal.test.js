import { describe, expect, it } from "vitest";
import { RUTA_RETORNO_MSAL, msalConfig } from "./msal";

describe("retorno del login con MSAL 5", () => {
  it("el retorno de login y de logout usa la página puente, nunca la raíz de la aplicación", () => {
    expect(RUTA_RETORNO_MSAL).toBe("/auth/redirect");
    expect(msalConfig.auth.redirectUri).toBe(`${window.location.origin}/auth/redirect`);
    expect(msalConfig.auth.postLogoutRedirectUri).toBe(msalConfig.auth.redirectUri);
  });
});
