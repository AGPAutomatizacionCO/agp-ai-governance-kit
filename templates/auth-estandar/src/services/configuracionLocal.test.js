import { describe, expect, it, vi } from "vitest";
import { crearClienteLocal, ErrorConfiguracion } from "./configuracionLocal";

function cliente(respuestas, token = "tok") {
  const enviar = vi.fn(async () => respuestas.shift());
  return { api: crearClienteLocal({ getAuthToken: async () => token, enviar }), enviar };
}
const ok = (cuerpo) => ({ ok: true, status: 200, json: async () => cuerpo });
const mal = (status, message) => ({ ok: false, status, json: async () => ({ message }) });

describe("cliente de la API propia de configuración", () => {
  it("llama a /api/configuracion del propio desarrollo con el id_token, sin hablar con la Mesa", async () => {
    const { api, enviar } = cliente([ok({ data: { yo: { correo: "a@agpglass.com" } } })]);
    expect((await api.estado()).yo.correo).toBe("a@agpglass.com");
    const [url, opciones] = enviar.mock.calls[0];
    expect(url).toBe("/api/configuracion/estado");
    expect(url).not.toContain("roles-app");
    expect(opciones.headers.Authorization).toBe("Bearer tok");
  });

  it("asignar envía solo correo y perfil: el actor lo decide el servidor", async () => {
    const { api, enviar } = cliente([ok({ data: {} }), ok({ data: {} })]);
    await api.asignar("ana@agpglass.com", "consulta");
    await api.asignar("ana@agpglass.com", null);
    expect(JSON.parse(enviar.mock.calls[0][1].body)).toEqual({ correo: "ana@agpglass.com", perfil: "consulta" });
    expect(JSON.parse(enviar.mock.calls[1][1].body)).toEqual({ correo: "ana@agpglass.com", perfil: null });
    expect(enviar.mock.calls[0][1].method).toBe("PUT");
  });

  it("el directorio codifica la búsqueda y devuelve una lista aunque la respuesta venga rara", async () => {
    const { api, enviar } = cliente([ok({ data: [{ correo: "a@agpglass.com" }] }), ok({ data: null })]);
    expect(await api.directorio(" ana pérez ")).toHaveLength(1);
    expect(enviar.mock.calls[0][0]).toBe("/api/configuracion/directorio?q=ana%20p%C3%A9rez");
    expect(await api.directorio("x")).toEqual([]);
  });

  it("el valor del secreto viaja una vez y la respuesta no lo trae; el aviso parcial se conserva", async () => {
    const { api, enviar } = cliente([ok({ data: { nombre: "demo-clave", guardado: true, auditoria: "pendiente" }, message: "Se guardó pero no se auditó" })]);
    const r = await api.cargarSecreto("demo-clave", "valor-de-prueba");
    expect(enviar.mock.calls[0][0]).toBe("/api/configuracion/secretos/demo-clave");
    expect(JSON.parse(enviar.mock.calls[0][1].body)).toEqual({ valor: "valor-de-prueba" });
    expect(JSON.stringify(r)).not.toContain("valor-de-prueba");
    expect(r.aviso).toContain("auditó");
  });

  it("errores: sin sesión, sin conexión y respuesta del servidor con su mensaje", async () => {
    await expect(cliente([], null).api.estado()).rejects.toMatchObject({ estado: 401 });
    const roto = crearClienteLocal({ getAuthToken: async () => "t", enviar: async () => { throw new Error("red"); } });
    await expect(roto.estado()).rejects.toBeInstanceOf(ErrorConfiguracion);
    await expect(cliente([mal(403, "No tienes permiso")]).api.actividad()).rejects.toMatchObject({ message: "No tienes permiso", estado: 403 });
    await expect(cliente([{ ok: false, status: 502, json: async () => { throw new Error("html"); } }]).api.estado()).rejects.toThrow("502");
  });
});
