import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const msal = vi.hoisted(() => ({
  getActiveAccount: vi.fn(() => null),
  getAllAccounts: vi.fn(() => []),
  setActiveAccount: vi.fn(),
  loginPopup: vi.fn(),
  acquireTokenSilent: vi.fn(),
  logoutPopup: vi.fn(),
}));
vi.mock("../config/msal", () => ({ getMsalInstance: () => msal, loginRequest: { scopes: ["User.Read"] } }));

import { AuthProvider, mensajeDeErrorLogin, useAuth } from "./AuthContext";

const cuenta = { username: "Ana@agpglass.com", name: "Ana", idTokenClaims: { roles: ["Usuario"] } };

function Sonda() {
  const { login, loginError, currentUser, authChecking } = useAuth();
  return (
    <div>
      <button onClick={login}>entrar</button>
      <span data-testid="estado">{authChecking ? "cargando" : currentUser ? `dentro:${currentUser.email}` : "fuera"}</span>
      <span data-testid="error">{loginError}</span>
    </div>
  );
}
const montar = () => render(<AuthProvider><Sonda /></AuthProvider>);

afterEach(cleanup);

beforeEach(() => {
  Object.values(msal).forEach((f) => f.mockReset());
  msal.getActiveAccount.mockReturnValue(null);
  msal.getAllAccounts.mockReturnValue([]);
});

describe("mensajeDeErrorLogin", () => {
  it.each([
    ["interaction_in_progress", "Ya hay una ventana de Microsoft abierta"],
    ["monitor_popup_timeout", "Microsoft no pudo devolver el acceso"],
    ["hash_empty_error", "Microsoft no pudo devolver el acceso"],
    ["popup_window_error", "bloqueó la ventana de Microsoft"],
  ])("%s tiene un mensaje que dice qué hacer", (errorCode, texto) => {
    expect(mensajeDeErrorLogin({ errorCode })).toContain(texto);
  });
  it("un error desconocido conserva el mensaje genérico y no copia el texto del proveedor", () => {
    const m = mensajeDeErrorLogin({ message: "NO-MOSTRAR-RESPUESTA-OAUTH" });
    expect(m).toBe("Error al iniciar sesión. Intenta de nuevo.");
    expect(m).not.toContain("NO-MOSTRAR");
  });
});

describe("AuthProvider con MSAL 5", () => {
  it("dos clics seguidos abren una sola ventana y emiten una sola sesión", async () => {
    let terminar;
    msal.loginPopup.mockImplementation(() => new Promise((resolve) => { terminar = resolve; }));
    montar();
    await waitFor(() => expect(screen.getByTestId("estado").textContent).toBe("fuera"));
    await act(async () => {
      screen.getByText("entrar").click();
      screen.getByText("entrar").click();
    });
    expect(msal.loginPopup).toHaveBeenCalledTimes(1);
    await act(async () => { terminar({ account: cuenta }); });
    await waitFor(() => expect(screen.getByTestId("estado").textContent).toBe("dentro:ana@agpglass.com"));
  });
  it("si MSAL falla con un código conocido se muestra el mensaje claro", async () => {
    msal.loginPopup.mockRejectedValue({ errorCode: "monitor_popup_timeout" });
    montar();
    await waitFor(() => expect(screen.getByTestId("estado").textContent).toBe("fuera"));
    await act(async () => { screen.getByText("entrar").click(); });
    await waitFor(() => expect(screen.getByTestId("error").textContent).toContain("Microsoft no pudo devolver el acceso"));
  });
  it("cancelar el popup no muestra error", async () => {
    msal.loginPopup.mockRejectedValue({ errorCode: "user_cancelled" });
    montar();
    await waitFor(() => expect(screen.getByTestId("estado").textContent).toBe("fuera"));
    await act(async () => { screen.getByText("entrar").click(); });
    expect(screen.getByTestId("error").textContent).toBe("");
  });
});
