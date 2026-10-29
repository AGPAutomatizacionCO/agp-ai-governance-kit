import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

const sesion = { currentUser: { email: "ana@agpglass.com", name: "Ana Pérez" }, isAdmin: false, logout: vi.fn() };
vi.mock("../contexts/AuthContext", () => ({ useAuth: () => sesion }));
vi.mock("../styles/menu-usuario-estandar.css", () => ({}));

import UserMenu, { ContenidoDelMenu, enlacesAdministrativos, etiquetaDeRol } from "./UserMenu";

const pintar = (props) => renderToStaticMarkup(<UserMenu {...props} />);

describe("menú de usuario estándar de AGP", () => {
    it("cumple el contrato que exigen la Mesa y los agentes: botón «Menú de usuario» con nombre y rol visibles", () => {
        const html = pintar();
        expect(html).toContain('data-agp-menu="usuario"');
        expect(html).toContain('aria-label="Menú de usuario"');
        expect(html).toContain("Ana Pérez");
        expect(html).toContain("Usuario");
        expect(html).toContain('data-agp-menu="cerrar-sesion"');
        expect(html).toContain("Cerrar sesión");
    });

    it("un usuario sin rol de administración no ve «Configuración»", () => {
        expect(pintar()).not.toContain('data-agp-menu="configuracion"');
    });

    it("el administrador ve «Configuración» → «Configuración del desarrollo» y su rol dice Administrador", () => {
        sesion.isAdmin = true;
        const html = pintar();
        sesion.isAdmin = false;
        expect(html).toContain('data-agp-menu="configuracion"');
        expect(html).toContain("Configuración del desarrollo");
        expect(html).toContain('href="/configuracion"');
        expect(html).toContain("Administrador");
    });

    it("el desarrollo puede declarar sus propios enlaces administrativos y su propio rol", () => {
        const html = pintar({ enlaces: [{ nombre: "Usuarios", href: "/usuarios" }], rolEtiqueta: "Líder de mejora" });
        expect(html).toContain('href="/usuarios"');
        expect(html).toContain("Líder de mejora");
        expect(enlacesAdministrativos({ isAdmin: true, enlaces: [] })).toEqual([]);
        expect(etiquetaDeRol({ isAdmin: true })).toBe("Administrador");
    });

    it("con la sesión cerrándose el botón de salir queda deshabilitado", () => {
        const html = renderToStaticMarkup(<ContenidoDelMenu enlaces={[]} idConfiguracion="c" configuracionAbierta={false} saliendo onAlternar={() => {}} onNavegar={() => {}} onSalir={() => {}} />);
        expect(html).toContain("disabled");
        expect(html).toContain("Cerrando sesión…");
    });
});
