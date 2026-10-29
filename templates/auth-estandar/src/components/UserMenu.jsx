// Menú de usuario estándar de AGP: el botón con el nombre y el rol de quien entró, y al hacer clic el menú con «Configuración» → «Administración»
// (los accesos administrativos del desarrollo) y «Cerrar sesión». Es el que RPC ya usa en producción; norma en ACCESO-Y-ROLES-DEL-DESARROLLO.md §4.
// Lo que la Mesa y los agentes exigen es el CONTRATO, no este archivo: el botón con `data-agp-menu="usuario"` y aria-label «Menú de usuario», el nombre y
// el rol visibles, la entrada «Configuración» con `data-agp-menu="configuracion"` y «Cerrar sesión». Un desarrollo con su propio componente (otro
// framework de UI) lo cumple igual si respeta ese contrato.
import { useEffect, useId, useRef, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import "../styles/menu-usuario-estandar.css";

export const ENLACE_CONFIGURACION = { nombre: "Configuración del desarrollo", href: "/configuracion" };

const iniciales = (nombre) => nombre.split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0].toUpperCase()).join("") || "·";

// Rol que se muestra: el que el desarrollo declare (`rolEtiqueta`, p. ej. un perfil de la Mesa) o, por omisión, el del token (Admin / Usuario).
export function etiquetaDeRol({ isAdmin, rolEtiqueta }) {
  return rolEtiqueta || (isAdmin ? "Administrador" : "Usuario");
}

// Quién ve «Configuración»: quien administra (Admin) o quien tiene enlaces administrativos propios. Sin enlaces no se muestra una opción vacía.
export function enlacesAdministrativos({ isAdmin, enlaces }) {
  if (Array.isArray(enlaces)) return enlaces;
  return isAdmin ? [ENLACE_CONFIGURACION] : [];
}

export function ContenidoDelMenu({ enlaces, idConfiguracion, configuracionAbierta, saliendo, onAlternar, onNavegar, onSalir }) {
  return (
    <>
      {enlaces.length > 0 && (
        <>
          <button type="button" role="menuitem" data-agp-menu="configuracion" aria-expanded={configuracionAbierta} aria-controls={idConfiguracion} onClick={onAlternar}>
            <span>Configuración</span>
            <span aria-hidden="true">{configuracionAbierta ? "▴" : "▾"}</span>
          </button>
          <div id={idConfiguracion} role="group" aria-label="Administración" hidden={!configuracionAbierta} className="agp-menu-usuario__grupo">
            <p role="presentation">Administración</p>
            {enlaces.map(({ nombre, href }) => (
              <a key={href} href={href} role="menuitem" onClick={(e) => onNavegar(e, href)}>{nombre}</a>
            ))}
          </div>
          <div role="separator" />
        </>
      )}
      <button type="button" role="menuitem" data-agp-menu="cerrar-sesion" disabled={saliendo} onClick={onSalir}>
        {saliendo ? "Cerrando sesión…" : "Cerrar sesión"}
      </button>
    </>
  );
}

/** `enlaces`: [{nombre, href}] de administración (opcional; por omisión, «Configuración del desarrollo» para Admin). `onNavegar(href)`: para
 *  enrutar sin recargar (react-router: `navigate`); sin él, el enlace navega normal. `rolEtiqueta`: el rol a mostrar si no es el del token. */
export default function UserMenu({ enlaces, onNavegar, rolEtiqueta }) {
  const { currentUser, isAdmin, logout } = useAuth();
  const [abierto, setAbierto] = useState(false);
  const [configuracionAbierta, setConfiguracionAbierta] = useState(false);
  const [saliendo, setSaliendo] = useState(false);
  const id = useId();
  const raiz = useRef(null);
  const boton = useRef(null);
  const panel = useRef(null);

  const nombre = currentUser?.name || currentUser?.email || "";
  const rol = etiquetaDeRol({ isAdmin, rolEtiqueta });
  const vinculos = enlacesAdministrativos({ isAdmin, enlaces });
  const cerrar = () => { setAbierto(false); setConfiguracionAbierta(false); };

  useEffect(() => {
    if (!abierto) return undefined;
    const fuera = (e) => { if (!raiz.current?.contains(e.target)) cerrar(); };
    const escape = (e) => { if (e.key === "Escape") { e.preventDefault(); cerrar(); boton.current?.focus(); } };
    document.addEventListener("pointerdown", fuera);
    document.addEventListener("keydown", escape);
    return () => { document.removeEventListener("pointerdown", fuera); document.removeEventListener("keydown", escape); };
  }, [abierto]);

  const visibles = () => Array.from(panel.current?.querySelectorAll('[role="menuitem"]:not(:disabled)') || []).filter((el) => el.getClientRects().length > 0);
  const navegarConTeclado = (e) => {
    if (!["ArrowDown", "ArrowUp", "Home", "End"].includes(e.key)) return;
    e.preventDefault();
    const items = visibles();
    if (!items.length) return;
    const actual = items.indexOf(document.activeElement);
    const siguiente = e.key === "Home" ? 0 : e.key === "End" ? items.length - 1 : (actual + (e.key === "ArrowUp" ? -1 : 1) + items.length) % items.length;
    items[siguiente].focus();
  };

  async function salir() {
    if (saliendo) return;
    setSaliendo(true);
    try { await logout(); } finally { setSaliendo(false); cerrar(); }
  }

  function navegar(e, href) {
    cerrar();
    if (onNavegar) { e.preventDefault(); onNavegar(href); }
  }

  return (
    <div ref={raiz} className="agp-menu-usuario" onBlurCapture={(e) => { if (!e.currentTarget.contains(e.relatedTarget)) cerrar(); }}>
      <button ref={boton} type="button" id={`${id}-boton`} data-agp-menu="usuario" aria-haspopup="menu" aria-expanded={abierto} aria-controls={id}
        aria-label="Menú de usuario" title={currentUser?.email || undefined} onClick={() => { setAbierto(!abierto); setConfiguracionAbierta(false); }}
        onKeyDown={(e) => {
          if (e.key === "ArrowDown" || e.key === "ArrowUp") {
            e.preventDefault();
            setAbierto(true);
            requestAnimationFrame(() => { const items = visibles(); (e.key === "ArrowUp" ? items[items.length - 1] : items[0])?.focus(); });
          }
        }}>
        <span aria-hidden="true" className="agp-menu-usuario__iniciales">{iniciales(nombre)}</span>
        <span className="agp-menu-usuario__texto">
          <span className="agp-menu-usuario__nombre">{nombre}</span>
          <span className="agp-menu-usuario__rol">{rol}</span>
        </span>
        <span aria-hidden="true">▾</span>
      </button>
      <div ref={panel} id={id} role="menu" aria-labelledby={`${id}-boton`} hidden={!abierto} onKeyDown={navegarConTeclado}>
        <div role="presentation" className="agp-menu-usuario__cabecera">
          <p>{nombre}</p>
          <p>{currentUser?.email}</p>
          <p>{rol}</p>
        </div>
        <ContenidoDelMenu enlaces={vinculos} idConfiguracion={`${id}-configuracion`} configuracionAbierta={configuracionAbierta} saliendo={saliendo}
          onAlternar={() => setConfiguracionAbierta(!configuracionAbierta)} onNavegar={navegar} onSalir={salir} />
      </div>
    </div>
  );
}
