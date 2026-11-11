// vite.config.js del desarrollo (ejemplo): el login con MSAL 5 necesita DOS páginas HTML en la compilación, la aplicación y la página puente.
import { resolve } from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// En desarrollo y en `vite preview`, /auth/redirect (sin extensión) se reescribe a la página puente; si no, Vite devuelve index.html y el popup no vuelve.
const rutaPuente = () => (req, _res, next) => {
  if (req.url && req.url.split("?")[0] === "/auth/redirect") req.url = req.url.replace("/auth/redirect", "/auth/redirect.html");
  next();
};

export default defineConfig({
  plugins: [
    react(),
    {
      name: "agp-ruta-puente-msal",
      // con llaves: `use()` devuelve la app de connect y Vite trataría ese retorno como un hook posterior (el servidor no arranca)
      configureServer(servidor) { servidor.middlewares.use(rutaPuente()) },
      configurePreviewServer(servidor) { servidor.middlewares.use(rutaPuente()) },
    },
  ],
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, "index.html"),
        redirect: resolve(__dirname, "auth/redirect.html"),   // → dist/auth/redirect.html
      },
    },
  },
});
