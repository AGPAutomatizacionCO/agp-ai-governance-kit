import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Como lo dejaba la plantilla vieja: una sola página (index.html), sin entrada para la página puente.
export default defineConfig({ plugins: [react()] });
