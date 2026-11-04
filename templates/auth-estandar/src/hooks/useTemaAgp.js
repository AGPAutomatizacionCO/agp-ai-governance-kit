// Modo claro / oscuro estándar de AGP, el mismo de la Mesa: oscuro por omisión y, en claro, la clase `theme-light` en <body> (los colores
// viven en styles/agp-tema.css). Lo usa el encabezado estándar; la aplicación puede leerlo con useTemaAgp() y todos ven el mismo valor.
// Sin elección guardada se sigue la preferencia del sistema; al cambiarlo se guarda 'light' | 'dark' en localStorage.
import { useCallback, useEffect, useSyncExternalStore } from "react";

export const CLAVE_TEMA = "agp_theme";   // la misma clave que usa la Mesa

const oyentes = new Set();
let actual = null;

function guardado() {
  try {
    const valor = localStorage.getItem(CLAVE_TEMA);
    return valor === "light" || valor === "dark" ? valor : null;
  } catch { return null; }
}

function delSistema() {
  try { return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark"; }
  catch { return "dark"; }
}

const leer = () => actual ?? (actual = guardado() || delSistema());
const suscribir = (oyente) => { oyentes.add(oyente); return () => oyentes.delete(oyente); };

// Pone o quita las clases en la página: `theme-light` en <body> (la que leen los estilos) y `dark` en <html>, como la Mesa (para
// bibliotecas que miran esa clase, p. ej. Tailwind con darkMode: "class").
export function aplicarTema(tema) {
  if (typeof document === "undefined") return;
  document.body.classList.toggle("theme-light", tema === "light");
  document.documentElement.classList.toggle("dark", tema !== "light");
}

export function fijarTema(tema) {
  actual = tema === "light" ? "light" : "dark";
  try { localStorage.setItem(CLAVE_TEMA, actual); } catch { /* almacenamiento bloqueado */ }
  aplicarTema(actual);
  oyentes.forEach((oyente) => oyente());
}

/** Devuelve { tema: 'light' | 'dark', fijarTema, alternarTema }. */
export default function useTemaAgp() {
  const tema = useSyncExternalStore(suscribir, leer, leer);
  useEffect(() => { aplicarTema(tema); }, [tema]);
  const alternarTema = useCallback(() => fijarTema(leer() === "light" ? "dark" : "light"), []);
  return { tema, fijarTema, alternarTema };
}
