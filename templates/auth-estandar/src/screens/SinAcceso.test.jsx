import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

vi.mock("../contexts/AuthContext", () => ({ useAuth: () => ({ currentUser: { email: "ana@agpglass.com" }, logout: vi.fn() }) }));
vi.mock("../styles/sin-acceso-estandar.css", () => ({}));
vi.mock("../components/AgpLogo", () => ({ default: () => <svg aria-label="AGP" /> }));
vi.mock("../config/msal", () => ({ appInfo: { nombre: null, contactoNombre: null, contactoCorreo: null } }));   // el real necesita window

import { appInfo } from "../config/msal";
import SinAcceso from "./SinAcceso";

describe("pantalla estándar sin acceso de AGP", () => {
    it("cumple el contrato: marca, contacto del desarrollador funcional, copiar, reintentar y cerrar sesión", () => {
        appInfo.nombre = "Web SmartBending"; appInfo.contactoNombre = "Ana Pérez"; appInfo.contactoCorreo = "ana@agpglass.com";
        const html = renderToStaticMarkup(<SinAcceso />);
        expect(html).toContain('data-agp-sin-acceso="estandar"');
        expect(html).toContain("No tienes acceso a esta aplicación");
        expect(html).toContain("Web SmartBending");
        expect(html).toContain("Ana Pérez");
        expect(html).toContain("Copiar correo");
        expect(html).toContain("Reintentar");
        expect(html).toContain("Cerrar sesión");
        expect(html).toContain("Sesión iniciada como ana@agpglass.com");
    });
    it("no tiene texto libre: sin contacto no inventa uno y no muestra «Copiar correo»", () => {
        appInfo.contactoNombre = null; appInfo.contactoCorreo = null;
        const html = renderToStaticMarkup(<SinAcceso />);
        expect(html).not.toContain("Copiar correo");
        expect(html).toContain('data-agp-sin-acceso="estandar"');
    });
});
