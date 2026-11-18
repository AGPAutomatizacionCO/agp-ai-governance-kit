import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

vi.mock("../contexts/AuthContext", () => ({ useAuth: () => ({ getAuthToken: async () => "token" }) }));
vi.mock("../config/msal", () => ({ appInfo: { roles: null } }));
vi.mock("../styles/configuracion-estandar.css", () => ({}));

import ConfiguracionDesarrollo, { capacidades, filtrarPersonas, ordenarPermisos, origenDe, perfilParaGuardar, resumenDeRol } from "./ConfiguracionDesarrollo";

const CATALOGO = [
    { modulo: "pedidos", nombre: "Pedidos", funciones: [{ id: "crear", nombre: "Crear" }, { id: "exportar", nombre: "Exportar" }] },
    { modulo: "alarmas", nombre: "Alarmas", funciones: [{ id: "editar", nombre: "Editar" }] },
];

describe("pantalla estándar de configuración de roles y secretos", () => {
    it("cumple el contrato que verifica la Mesa: raíz con data-agp-configuracion y título", () => {
        const html = renderToStaticMarkup(<ConfiguracionDesarrollo />);
        expect(html).toContain('data-agp-configuracion="estandar"');
        expect(html).toContain("Configuración de roles y secretos");
    });

    it("sin conexión con la Mesa lo dice y no inventa datos", () => {
        const html = renderToStaticMarkup(<ConfiguracionDesarrollo />);
        expect(html).toContain("ROLES_DESDE_MESA");
        expect(html).not.toContain('role="tablist"');
    });

    it("quien mira solo puede lo que la Mesa le responde (el servidor igual lo rechaza)", () => {
        expect(capacidades({ yo: { esAdmin: true, adminGlobal: true, asignarPersonas: true, editarPerfiles: true } }, { puedeCargar: true }))
            .toEqual({ esAdmin: true, asignar: true, editarRoles: true, principal: true, cargarSecretos: true });
        // administrador secundario: ve todo y edita roles, pero no asigna ni carga secretos
        expect(capacidades({ yo: { esAdmin: true, adminGlobal: false, asignarPersonas: false, editarPerfiles: true } }, { puedeCargar: false }))
            .toEqual({ esAdmin: true, asignar: false, editarRoles: true, principal: false, cargarSecretos: false });
        expect(capacidades(null, null).esAdmin).toBe(false);
    });

    it("los permisos se guardan en el orden del catálogo: módulo y luego sus funciones", () => {
        expect(ordenarPermisos(CATALOGO, new Set(["alarmas.editar", "pedidos.exportar", "pedidos", "alarmas"]))).toEqual(["pedidos", "pedidos.exportar", "alarmas", "alarmas.editar"]);
        expect(ordenarPermisos(CATALOGO, ["pedidos.crear"])).toEqual(["pedidos.crear"]);
        expect(ordenarPermisos(null, null)).toEqual([]);
    });

    it("el resumen de un rol cuenta vistas, acciones y datos", () => {
        expect(resumenDeRol({ permisos: ["pedidos", "pedidos.crear", "alarmas"], areas: ["a", "b"] })).toEqual({ vistas: 2, acciones: 1, datos: 2 });
        expect(resumenDeRol(undefined)).toEqual({ vistas: 0, acciones: 0, datos: 0 });
    });

    it("el rol que se pide guardar lleva el nombre limpio, permisos ordenados y su id solo si ya existe", () => {
        const nuevo = perfilParaGuardar({ id: null, nombre: "  Consulta   de pedidos ", permisos: new Set(["pedidos.exportar", "pedidos"]), areas: new Set(["x"]) }, CATALOGO);
        expect(nuevo).toEqual({ nombre: "Consulta de pedidos", permisos: ["pedidos", "pedidos.exportar"], areas: ["x"] });
        expect(perfilParaGuardar({ id: "p1", nombre: "A b", permisos: [], areas: [] }, CATALOGO).id).toBe("p1");
    });

    const PERSONAS = [
        { correo: "ana@agpglass.com", nombre: "Ana Pérez", perfil: "alarmas", nivel: "usuario" },
        { correo: "luis@agpglass.com", nombre: "Luis Gómez", nivel: "admin" },
        { correo: "marta@agpglass.com", nombre: "Marta Rojas", perfil: "consulta", porArea: "Finance" },
        { correo: "paola@agpglass.com", nombre: "Paola Ruiz", vistaGeneral: true },
    ];

    it("cada usuario tiene un origen: asignado, regla de área o vista general", () => {
        expect(PERSONAS.map(origenDe)).toEqual(["asignado", "asignado", "regla", "general"]);
    });

    it("los filtros combinan texto, rol y origen", () => {
        expect(filtrarPersonas(PERSONAS, {})).toHaveLength(4);
        expect(filtrarPersonas(PERSONAS, { texto: "MARTA" }).map((p) => p.correo)).toEqual(["marta@agpglass.com"]);
        expect(filtrarPersonas(PERSONAS, { texto: "agpglass.com", rol: "alarmas" }).map((p) => p.nombre)).toEqual(["Ana Pérez"]);
        expect(filtrarPersonas(PERSONAS, { rol: "@admin" }).map((p) => p.nombre)).toEqual(["Luis Gómez"]);
        expect(filtrarPersonas(PERSONAS, { origen: "regla" }).map((p) => p.nombre)).toEqual(["Marta Rojas"]);
        expect(filtrarPersonas(PERSONAS, { origen: "general" }).map((p) => p.nombre)).toEqual(["Paola Ruiz"]);
        expect(filtrarPersonas(PERSONAS, { texto: "zzz" })).toEqual([]);
        expect(filtrarPersonas(null, {})).toEqual([]);
    });
});
