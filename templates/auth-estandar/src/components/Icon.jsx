// Iconos SVG inline que heredan color (currentColor por defecto) en vez de traer
// el color fijo de la fuente-emoji del sistema operativo. Ver auditoría de
// colorimetría — reemplaza los emojis genéricos del header, sidebar, tarjetas
// de servicio y mensajes de estado por glifos que respetan la paleta de AGP.
const PATHS = {
  check:     <path d="M20 6 9 17l-5-5" />,
  close:     <path d="M18 6 6 18M6 6l12 12" />,
  warning:   <><path d="M10.29 3.86 1.82 18a1.5 1.5 0 0 0 1.28 2.25h17.8a1.5 1.5 0 0 0 1.28-2.25L13.71 3.86a1.5 1.5 0 0 0-2.42 0Z" /><path d="M12 9v4" /><path d="M12 17h.01" /></>,
  undo:      <path d="M9 14 4 9l5-5M4 9h10.5a5.5 5.5 0 0 1 0 11H11" />,
  settings:  <><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.6 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1Z" /></>,
  laptop:    <><rect x="3" y="4" width="18" height="12" rx="2" /><path d="M2 20h20" /></>,
  monitor:   <><rect x="2" y="3" width="20" height="14" rx="2" /><path d="M8 21h8M12 17v4" /></>,
  server:    <><rect x="2" y="3" width="20" height="7" rx="1.5" /><rect x="2" y="14" width="20" height="7" rx="1.5" /><path d="M6 6.5h.01M6 17.5h.01" /></>,
  database:  <><ellipse cx="12" cy="5" rx="9" ry="3" /><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" /><path d="M3 12c0 1.66 4 3 9 3s9-1.34 9-3" /></>,
  book:      <><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" /><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z" /></>,
  folder:    <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z" />,
  file:      <><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" /><path d="M14 2v6h6" /></>,
  trash:     <><path d="M3 6h18" /><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0-.87 13.14A2 2 0 0 1 16.14 21H7.86a2 2 0 0 1-2-1.86L5 6" /></>,
  save:      <><path d="M5 3h11l4 4v13a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" /><path d="M9 3v5h7V3M8 13h8v7H8Z" /></>,
  search:    <><circle cx="11" cy="11" r="7" /><path d="m21 21-4.3-4.3" /></>,
  upload:    <><path d="M12 16V4M6 10l6-6 6 6" /><path d="M4 20h16" /></>,
  download:  <><path d="M12 4v12M6 12l6 6 6-6" /><path d="M4 20h16" /></>,
  trophy:    <><path d="M8 21h8M12 17v4" /><path d="M7 4h10v5a5 5 0 0 1-10 0Z" /><path d="M7 5H4a1 1 0 0 0-1 1 5 5 0 0 0 4 4.9M17 5h3a1 1 0 0 1 1 1 5 5 0 0 1-4 4.9" /></>,
  rocket:    <><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z" /><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0" /><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5" /><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z" /></>,
  lock:      <><rect x="4" y="10" width="16" height="10" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></>,
  bot:       <><rect x="4" y="8" width="16" height="11" rx="2" /><path d="M12 8V4M9 4h6" /><circle cx="9" cy="13.5" r="1.2" /><circle cx="15" cy="13.5" r="1.2" /><path d="M2 12v3M22 12v3" /></>,
  user:      <><circle cx="12" cy="8" r="4" /><path d="M4 21c1.4-4 4.6-6 8-6s6.6 2 8 6" /></>,
  link:      <><path d="M9 15 15 9" /><path d="M10 6.5 12 4.4a4 4 0 0 1 5.6 5.6L15.5 12" /><path d="m14 17.5-2 2a4 4 0 0 1-5.6-5.6L8.5 12" /></>,
  star:      <path d="m12 2.5 2.9 6.1 6.6.7-4.9 4.6 1.3 6.6L12 17.4l-5.9 3.1 1.3-6.6-4.9-4.6 6.6-.7Z" />,
  plus:      <path d="M12 5v14M5 12h14" />,
  moon:      <path d="M20.5 14.5A8.5 8.5 0 1 1 9.5 3.5a7 7 0 0 0 11 11Z" />,
  sun:       <><circle cx="12" cy="12" r="4.2" /><path d="M12 2.5v2.3M12 19.2v2.3M4.9 4.9l1.6 1.6M17.5 17.5l1.6 1.6M2.5 12h2.3M19.2 12h2.3M4.9 19.1l1.6-1.6M17.5 6.5l1.6-1.6" /></>,
  chart:     <><path d="M4 20V10M12 20V4M20 20v-7" /><path d="M2 20h20" /></>,
  flask:     <><path d="M9 2h6M10 2v6.2L4.7 18a2 2 0 0 0 1.8 3h11a2 2 0 0 0 1.8-3L14 8.2V2" /><path d="M7.5 14h9" /></>,
  inbox:     <><path d="M3 12h4.5l1.5 3h6l1.5-3H21" /><path d="M5.4 5h13.2a1 1 0 0 1 .96.73L21 12v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-6l1.44-6.27A1 1 0 0 1 5.4 5Z" /></>,
  wrench:    <path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.6 2.6-2-2Z" />,
  pencil:    <><path d="m18 2 4 4-13 13-5 1 1-5Z" /><path d="m15 5 4 4" /></>,
  image:     <><rect x="3" y="4" width="18" height="16" rx="2" /><circle cx="8.5" cy="9.5" r="1.5" /><path d="m21 15-5-5-9 9" /></>,
  message:   <path d="M4 4h16v12H8l-4 4Z" />,
  clipboard: <><rect x="6" y="4" width="12" height="17" rx="2" /><rect x="9" y="2" width="6" height="4" rx="1" /></>,
  clock:     <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3.5 2" /></>,
  bell:      <><path d="M18 8a6 6 0 1 0-12 0c0 5-2.5 6-2.5 6h17S18 13 18 8Z" /><path d="M13.7 20a2 2 0 0 1-3.4 0" /></>,
  play:      <path d="M7 4v16l13-8Z" />,
  pause:     <><rect x="6.5" y="4" width="3.5" height="16" rx="1" /><rect x="14" y="4" width="3.5" height="16" rx="1" /></>,
  chevrons:  <><path d="M6 17 11 12 6 7" /><path d="M13 17 18 12 13 7" /></>,
  filter:    <path d="M4 4h16l-6.5 8v6l-3 2v-8Z" />,
  "more-vertical": <><circle cx="12" cy="5" r="1.5" /><circle cx="12" cy="12" r="1.5" /><circle cx="12" cy="19" r="1.5" /></>,
  "chevron-up":   <path d="m6 15 6-6 6 6" />,
  "chevron-down": <path d="m6 9 6 6 6-6" />,
  refresh:   <><path d="M21 12a9 9 0 0 1-15.3 6.4L3 16" /><path d="M3 12a9 9 0 0 1 15.3-6.4L21 8" /><path d="M3 16v-4h4" /><path d="M21 8v4h-4" /></>,
  send:      <><path d="M22 2 11 13" /><path d="M22 2 15 22l-4-9-9-4Z" /></>,
  logout:    <><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><path d="M16 17l5-5-5-5" /><path d="M21 12H9" /></>,
  users:     <><circle cx="18" cy="5" r="3" /><circle cx="6" cy="12" r="3" /><circle cx="18" cy="19" r="3" /><path d="M8.6 10.5 15.4 6.9M8.6 13.5 15.4 17.1" /></>,
};

export default function Icon({ name, size = 15, color = "currentColor", strokeWidth = 2, style, ...rest }) {
  const content = PATHS[name];
  if (!content) return null;
  return (
    <svg
      width={size} height={size} viewBox="0 0 24 24"
      fill="none" stroke={color} strokeWidth={strokeWidth}
      strokeLinecap="round" strokeLinejoin="round"
      style={{ display: "inline-block", verticalAlign: "-3px", flexShrink: 0, ...style }}
      aria-hidden="true"
      {...rest}
    >
      {content}
    </svg>
  );
}

// Insignia circular numerada — reemplaza los emojis de teclado (1️⃣ 2️⃣ 3️⃣…)
// usados como marcadores de paso en PipelineConfigEditor.
export function StepBadge({ n }) {
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", justifyContent: "center",
      width: "18px", height: "18px", borderRadius: "50%", flexShrink: 0,
      background: "var(--brand)", color: "#fff", fontSize: "11px", fontWeight: 700,
      verticalAlign: "-4px",
    }}>{n}</span>
  );
}

// Versión en string de un subconjunto mínimo de iconos, para los pocos casos
// donde el texto viaja como HTML plano (dangerouslySetInnerHTML) y no puede
// contener un componente React: banners de chat y burbujas de mensaje.
const RAW_PATHS = {
  check:     '<path d="M20 6 9 17l-5-5"/>',
  close:     '<path d="M18 6 6 18M6 6l12 12"/>',
  clipboard: '<rect x="6" y="4" width="12" height="17" rx="2"/><rect x="9" y="2" width="6" height="4" rx="1"/>',
};

export function iconMarkup(name, { size = 14, color = "currentColor" } = {}) {
  const inner = RAW_PATHS[name];
  if (!inner) return "";
  return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:-2px;flex-shrink:0" aria-hidden="true">${inner}</svg>`;
}
