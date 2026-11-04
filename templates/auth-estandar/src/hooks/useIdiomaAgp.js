// Idioma estándar de AGP (ES / PT), el mismo selector de la Mesa: español por omisión y sin detectar el idioma del navegador (decisión de
// producto de la Mesa). Guarda 'es' | 'pt' en localStorage y ajusta <html lang>. La aplicación traduce SUS textos leyendo useIdiomaAgp();
// todos los componentes que lo usan ven el mismo valor.
import { useEffect, useSyncExternalStore } from "react";

export const CLAVE_IDIOMA = "agp_lang";   // la misma clave que usa la Mesa

const oyentes = new Set();
let actual = null;

function guardado() {
  try { return localStorage.getItem(CLAVE_IDIOMA) === "pt" ? "pt" : "es"; }
  catch { return "es"; }
}

const leer = () => actual ?? (actual = guardado());
const suscribir = (oyente) => { oyentes.add(oyente); return () => oyentes.delete(oyente); };

export function fijarIdioma(idioma) {
  actual = idioma === "pt" ? "pt" : "es";
  try { localStorage.setItem(CLAVE_IDIOMA, actual); } catch { /* almacenamiento bloqueado */ }
  oyentes.forEach((oyente) => oyente());
}

/** Devuelve { idioma: 'es' | 'pt', fijarIdioma }. */
export default function useIdiomaAgp() {
  const idioma = useSyncExternalStore(suscribir, leer, leer);
  useEffect(() => {
    if (typeof document !== "undefined") document.documentElement.lang = idioma === "pt" ? "pt-BR" : "es";
  }, [idioma]);
  return { idioma, fijarIdioma };
}
