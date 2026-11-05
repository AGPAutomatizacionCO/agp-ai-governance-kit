// Pantalla estándar de AGP para quien inicia sesión pero no tiene acceso al desarrollo. Aprobada por IT; NO admite texto libre: solo cambian el nombre de la
// aplicación, el contacto (el desarrollador funcional) y la persona con sesión. Reemplaza a `sinAcceso.mensaje` de ROLES.md (obsoleto).
// Contrato que exigen la Mesa y los agentes: la raíz lleva `data-agp-sin-acceso="estandar"`. Textos ES / PT con el idioma estándar (useIdiomaAgp).
// El contacto es administradores[0] de .agp/entra.yaml, que la API entrega en GET /api/config (contactoNombre, contactoCorreo) y cargarConfigMsal guarda en appInfo.
import { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import AgpLogo from "../components/AgpLogo";
import { appInfo } from "../config/msal";
import useIdiomaAgp from "../hooks/useIdiomaAgp";
import "../styles/sin-acceso-estandar.css";

export const TEXTOS = {
  es: {
    titulo: "No tienes acceso a esta aplicación",
    cuerpo: (app) => `Tu cuenta de AGP inició sesión correctamente, pero todavía no tienes permiso para usar ${app}. Comunícate con quien la administra para que te asigne un rol.`,
    contacto: "Comunícate con (desarrollador funcional)",
    copiar: "Copiar correo", copiado: "Correo copiado", reintentar: "Reintentar", salir: "Cerrar sesión",
    sesion: (u) => `Sesión iniciada como ${u}`,
  },
  pt: {
    titulo: "Você não tem acesso a esta aplicação",
    cuerpo: (app) => `Sua conta da AGP entrou com sucesso, mas você ainda não tem permissão para usar ${app}. Fale com quem a administra para que lhe atribuam um papel.`,
    contacto: "Fale com (desenvolvedor funcional)",
    copiar: "Copiar e-mail", copiado: "E-mail copiado", reintentar: "Tentar de novo", salir: "Sair",
    sesion: (u) => `Sessão iniciada como ${u}`,
  },
};

/** Props opcionales: appName, contactoNombre, contactoCorreo, usuario (por omisión, appInfo y la sesión); onReintentar y onSalir (por omisión, recargar y logout). */
export default function SinAcceso({ appName, contactoNombre, contactoCorreo, usuario, onReintentar, onSalir }) {
  const { currentUser, logout } = useAuth();
  const { idioma } = useIdiomaAgp();
  const [copiado, setCopiado] = useState(false);
  const t = TEXTOS[idioma] || TEXTOS.es;
  const app = appName || appInfo.nombre || "esta aplicación";
  const nombre = contactoNombre ?? appInfo.contactoNombre;
  const correo = contactoCorreo ?? appInfo.contactoCorreo;
  const quien = usuario || currentUser?.email || "";

  const copiar = async () => {
    try { await navigator.clipboard.writeText(correo); setCopiado(true); setTimeout(() => setCopiado(false), 1800); }
    catch { /* sin portapapeles: el correo queda visible para seleccionarlo */ }
  };

  return (
    <main className="agp-sin-acceso" data-agp-sin-acceso="estandar" aria-labelledby="agp-sin-acceso-titulo">
      <section className="agp-sin-acceso__tarjeta">
        <AgpLogo />
        <h1 id="agp-sin-acceso-titulo">{t.titulo}</h1>
        <p>{t.cuerpo(app)}</p>
        {correo && (
          <div className="agp-sin-acceso__contacto">
            <small>{t.contacto}</small>
            {nombre && <b>{nombre}</b>}
            <span>{correo}</span>
          </div>
        )}
        <div className="agp-sin-acceso__acciones">
          {correo && <button type="button" className="agp-sin-acceso__principal" onClick={copiar}>{copiado ? t.copiado : t.copiar}</button>}
          <button type="button" onClick={onReintentar || (() => window.location.reload())}>{t.reintentar}</button>
          <button type="button" onClick={onSalir || logout}>{t.salir}</button>
        </div>
        {quien && <p className="agp-sin-acceso__sesion">{t.sesion(quien)}</p>}
      </section>
    </main>
  );
}
