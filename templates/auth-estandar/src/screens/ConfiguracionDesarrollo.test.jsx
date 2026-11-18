import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

vi.mock("../contexts/AuthContext", () => ({ useAuth: () => ({ getAuthToken: async () => "tok" }) }));
vi.mock("../hooks/useIdiomaAgp", () => ({ default: () => ({ idioma: "es" }) }));
vi.mock("../styles/configuracion-estandar.css", () => ({}));

import ConfiguracionDesarrollo, { ModalAsignar, PanelActividad, PanelSecretos, PanelUsuarios, mensajeDe, nombreDePerfil, PESTANAS } from "./ConfiguracionDesarrollo";

const T = new Proxy({}, { get: (_, k) => String(k) });   // los textos se comprueban por clave, no por traducción
const PERFILES = [{ id: "administrador", nombre: "Administrador", administra: true }, { id: "consulta", nombre: "Consulta", administra: false }];
const ESTADO = { puedeConfigurar: true, perfiles: PERFILES, personas: [{ correo: "ana@agpglass.com", perfil: "consulta" }], administradoresIniciales: ["ini@agpglass.com"] };

describe("pantalla estándar de configuración (local)", () => {
  it("la raíz lleva la marca que verifica la Mesa y, mientras carga, no muestra pestañas ni datos", () => {
    const html = renderToStaticMarkup(<ConfiguracionDesarrollo api={{ estado: () => new Promise(() => {}) }} />);
    expect(html).toContain('data-agp-configuracion="estandar"');
    expect(html).not.toContain("data-agp-pestana");
  });

  it("las pestañas del contrato son usuarios, secretos y actividad", () => {
    expect(PESTANAS).toEqual(["usuarios", "secretos", "actividad"]);
  });

  it("usuarios: lista personas con su perfil, el administrador inicial y las acciones", () => {
    const html = renderToStaticMarkup(<PanelUsuarios estado={ESTADO} t={T} ocupado={false} onAsignar={() => {}} onCambiar={() => {}} onQuitar={() => {}} />);
    for (const texto of ["ana@agpglass.com", "Consulta", "ini@agpglass.com", "inicial", "asignar", "quitar", "cambiar"]) expect(html).toContain(texto);
  });

  it("el modal de asignar cumple role=dialog y aria-modal y ofrece los perfiles del servidor", () => {
    const html = renderToStaticMarkup(<ModalAsignar t={T} perfiles={PERFILES} api={null} persona={{ correo: "ana@agpglass.com", perfil: "consulta" }} onCerrar={() => {}} onConfirmar={() => {}} />);
    expect(html).toContain('role="dialog"');
    expect(html).toContain('aria-modal="true"');
    expect(html).toContain("Administrador");
    expect(html).toContain("ana@agpglass.com");
  });

  it("secretos: solo nombres, sin valores; el campo de valor es de contraseña y solo existe al editar", () => {
    const html = renderToStaticMarkup(<PanelSecretos secretos={{ nombres: ["demo-clave-externa"] }} t={T} ocupado={false} onGuardar={async () => true} />);
    expect(html).toContain("demo-clave-externa");
    expect(html).not.toContain('type="password"');
    expect(renderToStaticMarkup(<PanelSecretos secretos={{ nombres: [] }} t={T} ocupado={false} onGuardar={async () => true} />)).toContain("sinSecretos");
  });

  it("actividad: tabla de la auditoría o mensaje vacío", () => {
    const filas = [{ fecha: "2026-11-18 10:00", actor: "admin@agpglass.com", destinatario: "ana@agpglass.com", perfilAnterior: null, perfilNuevo: "consulta", resultado: "aplicado" }];
    expect(renderToStaticMarkup(<PanelActividad filas={filas} t={T} />)).toContain("admin@agpglass.com");
    expect(renderToStaticMarkup(<PanelActividad filas={[]} t={T} />)).toContain("sinActividad");
  });

  it("ayudantes: mensaje sin detalle técnico y nombre de perfil con respaldo", () => {
    expect(mensajeDe(new Error("No tienes permiso"))).toBe("No tienes permiso");
    expect(mensajeDe(null)).toContain("No se pudo");
    expect(nombreDePerfil(PERFILES, "consulta")).toBe("Consulta");
    expect(nombreDePerfil(PERFILES, "otro")).toBe("otro");
  });

  it("no depende del túnel de la Mesa", async () => {
    const fuente = (await import("node:fs")).readFileSync(new URL("./ConfiguracionDesarrollo.jsx", import.meta.url), "utf8");
    expect(fuente).not.toContain("rolesMesa");
    expect(fuente).not.toContain("roles-app");
  });
});
