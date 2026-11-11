import { describe, expect, it } from "vitest";
import { aadstsDeErrorMsal, causaProbable, extraerErrorEntra, textoDelPuente } from "./erroresEntra";

describe("extraerErrorEntra", () => {
  it("toma solo el error y el código AADSTS del hash", () => {
    const r = extraerErrorEntra("#error=access_denied&error_description=AADSTS65001%3A+The+user+or+administrator+has+not+consented&state=XYZ&code=ABC", "");
    expect(r).toEqual({ error: "access_denied", aadsts: "AADSTS65001" });
    expect(JSON.stringify(r)).not.toMatch(/XYZ|ABC|consented/);
  });
  it("también lee la query y descripciones con +", () => {
    expect(extraerErrorEntra("", "?error=server_error&error_description=AADSTS700016%3A+Application+not+found")).toEqual({ error: "server_error", aadsts: "AADSTS700016" });
  });
  it("sin error en la respuesta devuelve null (un retorno correcto no se toca)", () => {
    expect(extraerErrorEntra("#code=ABC&state=XYZ", "")).toBeNull();
    expect(extraerErrorEntra("", "")).toBeNull();
    expect(extraerErrorEntra(undefined, undefined)).toBeNull();
  });
  it("ignora un error con caracteres raros en el nombre", () => {
    expect(extraerErrorEntra("#error=<script>alert(1)</script>", "")).toBeNull();
  });
  it("una descripción mal codificada no rompe", () => {
    expect(extraerErrorEntra("#error=server_error&error_description=%E0%A4%A", "")).toEqual({ error: "server_error", aadsts: "" });
  });
});

describe("causas probables", () => {
  it.each(["AADSTS50105", "AADSTS65001", "AADSTS50011", "AADSTS700016", "AADSTS9002326"])("%s tiene instrucción", (codigo) => {
    expect(causaProbable({ aadsts: codigo })).not.toBe("");
  });
  it("access_denied, consent_required, interaction_required y server_error tienen instrucción", () => {
    for (const error of ["access_denied", "consent_required", "interaction_required", "server_error"]) expect(causaProbable({ error })).not.toBe("");
  });
  it("un código desconocido no inventa una causa", () => {
    expect(causaProbable({ error: "otra_cosa", aadsts: "AADSTS99999" })).toBe("");
  });
  it("el texto del puente sin error es la instrucción de siempre y con error añade el código", () => {
    expect(textoDelPuente(null, "AGPTS")).toBe("No se pudo completar el acceso. Cierra esta ventana y vuelve a intentarlo desde AGPTS.");
    expect(textoDelPuente({ error: "", aadsts: "AADSTS99999" }, "AGPTS")).toContain("Informa a TI con este código");
  });
});

describe("aadstsDeErrorMsal", () => {
  it("busca el código en subError, errorMessage y message", () => {
    expect(aadstsDeErrorMsal({ subError: "AADSTS50105" })).toBe("AADSTS50105");
    expect(aadstsDeErrorMsal({ errorMessage: "server_error: AADSTS65001: texto" })).toBe("AADSTS65001");
    expect(aadstsDeErrorMsal(new Error("x AADSTS700016 y"))).toBe("AADSTS700016");
    expect(aadstsDeErrorMsal({})).toBe("");
  });
});
