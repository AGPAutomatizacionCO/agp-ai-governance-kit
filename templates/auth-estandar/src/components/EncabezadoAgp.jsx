// Encabezado estándar de AGP: la barra superior de la Mesa de Ayuda IT en cualquier desarrollo. A la izquierda, el nombre del desarrollo y,
// si el desarrollo las pasa como children, sus propias acciones; a la derecha, ES / PT, modo claro / oscuro y el menú de usuario estándar.
// Se copia sin cambios. Lo que la Mesa verifica es el CONTRATO: la raíz con `data-agp-encabezado="estandar"`, el grupo ES / PT con
// `data-agp-idioma` (botones con aria-pressed) y el botón de tema con `data-agp-tema` (aria-label «Modo claro» / «Modo oscuro»).
import AgpLogo from "./AgpLogo";
import Icon from "./Icon";
import UserMenu from "./UserMenu";
import { appInfo } from "../config/msal";
import useIdiomaAgp from "../hooks/useIdiomaAgp";
import useTemaAgp from "../hooks/useTemaAgp";
import "../styles/encabezado-estandar.css";

// El botón dice a qué modo cambia: en oscuro, «Modo claro»; en claro, «Modo oscuro». Mismas traducciones que la Mesa.
const ETIQUETA_TEMA = {
  es: { light: "Modo oscuro", dark: "Modo claro" },
  pt: { light: "Modo escuro", dark: "Modo claro" },
};

/** `nombre`: el del desarrollo (por omisión, el que entrega la API: appInfo.nombre). `children`: acciones propias del desarrollo, junto al
 *  nombre. `menuProps`: se pasan tal cual a UserMenu (`enlaces`, `onNavegar`, `rolEtiqueta`). */
export default function EncabezadoAgp({ nombre, children, menuProps }) {
  const { idioma, fijarIdioma } = useIdiomaAgp();
  const { tema, alternarTema } = useTemaAgp();
  const titulo = nombre || appInfo.nombre || "Nombre del desarrollo";
  const etiquetaTema = ETIQUETA_TEMA[idioma][tema];

  return (
    <header className="agp-encabezado" data-agp-encabezado="estandar">
      <div className="agp-encabezado__info">
        <AgpLogo width={64} height={26} className="agp-encabezado__logo" />
        <p className="agp-encabezado__titulo" title={titulo}>{titulo}</p>
        {children && <div className="agp-encabezado__acciones">{children}</div>}
      </div>

      <div className="agp-encabezado__idioma" data-agp-idioma={idioma} role="group" aria-label="Español / Português" title="Español / Português">
        <button type="button" aria-pressed={idioma === "es"} onClick={() => fijarIdioma("es")}>ES</button>
        <button type="button" aria-pressed={idioma === "pt"} onClick={() => fijarIdioma("pt")}>PT</button>
      </div>

      <button type="button" className="agp-encabezado__tema" data-agp-tema={tema} aria-label={etiquetaTema} title={etiquetaTema} onClick={alternarTema}>
        <Icon name={tema === "light" ? "moon" : "sun"} size={14} />
      </button>

      <UserMenu {...menuProps} />
    </header>
  );
}
