import { existsSync, readFileSync, readdirSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

// Prueba de humo del login con MSAL 5 (INTEGRAR-MSAL.md). Falla si vuelve la raíz del sitio como `redirectUri`, si falta la página puente o si la
// compilación/servidor no la exponen: el síntoma sería «Error al iniciar sesión. Intenta de nuevo.» sin ningún error en la consola.
// Raíz del frontend = dos carpetas arriba de este archivo (src/auth/). En la plantilla del kit no hay package.json: se asume MSAL 5.
const raiz = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const leer = (ruta) => readFileSync(join(raiz, ruta), "utf8");

function archivos(carpeta, salida = []) {
  if (!existsSync(carpeta)) return salida;
  for (const nombre of readdirSync(carpeta, { withFileTypes: true })) {
    const ruta = join(carpeta, nombre.name);
    if (nombre.isDirectory()) {
      if (nombre.name !== "node_modules") archivos(ruta, salida);
    } else salida.push(ruta);
  }
  return salida;
}

function mayorDeMsal() {
  if (!existsSync(join(raiz, "package.json"))) return 5;
  const paquete = JSON.parse(leer("package.json"));
  const version = { ...paquete.devDependencies, ...paquete.dependencies }["@azure/msal-browser"];
  if (!version) return null;
  const coincidencia = /(\d+)/.exec(version);
  return coincidencia ? Number(coincidencia[1]) : 5;
}

const mayor = mayorDeMsal();
const conMsal5 = mayor !== null && mayor >= 5;

describe.skipIf(!conMsal5)("login con MSAL 5: la raíz no puede ser el retorno", () => {
  it("ningún archivo de src/ usa window.location.origin (sin ruta) como redirectUri o postLogoutRedirectUri", () => {
    const codigo = archivos(join(raiz, "src")).filter((f) => /\.(jsx?|tsx?|mjs)$/.test(f) && !/\.test\./.test(f));
    const malos = [];
    for (const archivo of codigo) {
      const texto = readFileSync(archivo, "utf8");
      if (/\b(?:redirectUri|postLogoutRedirectUri)\s*:\s*window\.location\.origin\s*[,}\n]/.test(texto)) malos.push(relative(raiz, archivo));
    }
    expect(malos, `redirectUri en la raíz con MSAL 5 (usa \`\${window.location.origin}/auth/redirect\`; INTEGRAR-MSAL.md): ${malos.join(", ")}`).toEqual([]);
  });

  it("existe la página puente y no monta la aplicación", () => {
    expect(existsSync(join(raiz, "auth/redirect.html")), "falta auth/redirect.html").toBe(true);
    const html = leer("auth/redirect.html");
    expect(html).not.toMatch(/id\s*=\s*["']root["']/);
    expect(html).toContain("/src/auth/redirect.");
    const script = ["src/auth/redirect.js", "src/auth/redirect.ts"].find((f) => existsSync(join(raiz, f)));
    expect(script, "falta src/auth/redirect.js").toBeTruthy();
    expect(leer(script)).toContain("@azure/msal-browser/redirect-bridge");
    expect(leer(script)).toContain("broadcastResponseToMainFrame");
  });

  it("la configuración de MSAL (si existe) vuelve a la página puente", async () => {
    if (!existsSync(join(raiz, "src/config/msal.js"))) return;
    const modulo = "../config/msal.js";   // especificador calculado: en un repositorio sin este archivo, Vite no intenta resolverlo
    const { msalConfig } = await import(/* @vite-ignore */ modulo);
    expect(msalConfig.auth.redirectUri).toBe(`${window.location.origin}/auth/redirect`);
    expect(msalConfig.auth.postLogoutRedirectUri).toBe(msalConfig.auth.redirectUri);
  });

  it("la compilación incluye la página puente (Vite)", () => {
    const vite = ["vite.config.js", "vite.config.ts", "vite.config.mjs", "vite.config.example.js"].find((f) => existsSync(join(raiz, f)));
    if (!vite) return;
    expect(leer(vite), `${vite} no compila auth/redirect.html`).toContain("auth/redirect.html");
  });
});
