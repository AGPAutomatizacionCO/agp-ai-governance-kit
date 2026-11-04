import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";

const sesion = { currentUser: { email: "ana@agpglass.com", name: "Ana Pérez" }, isAdmin: false, logout: vi.fn() };
vi.mock("../contexts/AuthContext", () => ({ useAuth: () => sesion }));
vi.mock("../config/msal", () => ({ appInfo: { nombre: "Portal de Calidad" } }));
vi.mock("../styles/menu-usuario-estandar.css", () => ({}));
vi.mock("../styles/encabezado-estandar.css", () => ({}));

import EncabezadoAgp from "./EncabezadoAgp";
import { fijarIdioma } from "../hooks/useIdiomaAgp";
import { fijarTema } from "../hooks/useTemaAgp";

const pintar = (props) => renderToStaticMarkup(<EncabezadoAgp {...props} />);

describe("encabezado estándar de AGP", () => {
    afterEach(() => { fijarTema("dark"); fijarIdioma("es"); });

    it("cumple el contrato que verifica la Mesa: encabezado, selector ES / PT y botón de tema", () => {
        const html = pintar({ nombre: "Gestor de Turnos" });
        expect(html).toContain('data-agp-encabezado="estandar"');
        expect(html).toContain("data-agp-idioma");
        expect(html).toMatch(/<button[^>]*aria-pressed="true"[^>]*>ES<\/button>/);
        expect(html).toMatch(/<button[^>]*aria-pressed="false"[^>]*>PT<\/button>/);
        expect(html).toContain("data-agp-tema");
        expect(html).toContain('aria-label="Modo claro"');
    });

    it("muestra el nombre del desarrollo; sin la prop, el que entrega la API", () => {
        expect(pintar({ nombre: "Gestor de Turnos" })).toContain("Gestor de Turnos");
        expect(pintar()).toContain("Portal de Calidad");
    });

    it("monta el menú de usuario estándar con el nombre de quien entró", () => {
        const html = pintar();
        expect(html).toContain('data-agp-menu="usuario"');
        expect(html).toContain("Ana Pérez");
        expect(html).toContain('data-agp-menu="cerrar-sesion"');
    });

    it("deja espacio para las acciones propias del desarrollo", () => {
        expect(pintar({ children: <button type="button">Exportar</button> })).toContain("Exportar");
    });

    it("en modo claro el botón ofrece «Modo oscuro» y el selector marca el idioma elegido", () => {
        fijarTema("light");
        fijarIdioma("pt");
        const html = pintar();
        expect(html).toContain('aria-label="Modo escuro"');
        expect(html).toMatch(/<button[^>]*aria-pressed="true"[^>]*>PT<\/button>/);
        fijarIdioma("es");
        expect(pintar()).toContain('aria-label="Modo oscuro"');
    });
});
