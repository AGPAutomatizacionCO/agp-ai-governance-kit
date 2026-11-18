import { describe, expect, it, vi } from "vitest";

vi.mock("../config/msal", () => ({ appInfo: { roles: null } }));

import { crearClienteMesa, ErrorMesa } from "./rolesMesa";

const respuesta = (cuerpo, ok = true, status = 200) => ({ ok, status, json: async () => cuerpo });
const cliente = (enviar, token = "tok") => crearClienteMesa({ mesaUrl: "https://mesa.example/", idProyecto: "ID 1", getAuthToken: async () => token, enviar });

describe("cliente de la API de roles y secretos de la Mesa", () => {
    it("llama a la ruta del desarrollo con el id_token y devuelve data", async () => {
        const enviar = vi.fn(async () => respuesta({ data: { ok: 1 } }));
        expect(await cliente(enviar).estado()).toEqual({ ok: 1 });
        const [url, opciones] = enviar.mock.calls[0];
        expect(url).toBe("https://mesa.example/api/roles-app/ID%201/estado");
        expect(opciones.headers.Authorization).toBe("Bearer tok");
    });

    it("pide cambios con POST, cancela con DELETE y carga secretos con PUT solo con el valor", async () => {
        const enviar = vi.fn(async () => respuesta({ data: {} }));
        const c = cliente(enviar);
        await c.solicitar({ accion: "quitar_rol", correo: "a@agpglass.com" });
        await c.cancelar("S 1");
        await c.cargarSecreto("portalsac-session-secret", "valor-largo");
        await c.reiniciar();
        const [[u1, o1], [u2, o2], [u3, o3], [u4, o4]] = enviar.mock.calls;
        expect([o1.method, u1.endsWith("/solicitudes")]).toEqual(["POST", true]);
        expect(JSON.parse(o1.body)).toEqual({ accion: "quitar_rol", correo: "a@agpglass.com" });
        expect([o2.method, u2.endsWith("/peticiones/S%201")]).toEqual(["DELETE", true]);
        expect([o3.method, u3.endsWith("/secretos/portalsac-session-secret")]).toEqual(["PUT", true]);
        expect(JSON.parse(o3.body)).toEqual({ valor: "valor-largo" });
        expect([o4.method, u4.endsWith("/secretos/reiniciar")]).toEqual(["POST", true]);
    });

    it("el directorio siempre devuelve una lista", async () => {
        const c = cliente(vi.fn(async () => respuesta({ data: null })));
        expect(await c.directorio("ana")).toEqual([]);
    });

    it("sin token, sin conexión o con error de la Mesa lanza ErrorMesa con un mensaje claro", async () => {
        await expect(cliente(vi.fn(), "").estado()).rejects.toThrow(/sesión venció/);
        await expect(cliente(vi.fn(async () => { throw new Error("red"); })).estado()).rejects.toThrow(ErrorMesa);
        await expect(cliente(vi.fn(async () => respuesta({ message: "Solo el administrador principal carga secretos." }, false, 403))).cargarSecreto("x", "y")).rejects.toThrow("Solo el administrador principal carga secretos.");
        await expect(cliente(vi.fn(async () => respuesta({}, false, 500))).estado()).rejects.toThrow("500");
    });
});
