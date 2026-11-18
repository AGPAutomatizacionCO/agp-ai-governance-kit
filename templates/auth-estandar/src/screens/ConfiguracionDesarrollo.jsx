// Pantalla estándar «Configuración de roles y secretos» de AGP (CONFIGURACION-LOCAL-ROLES-Y-SECRETOS.md). Se llega a ella desde el menú de usuario («Configuración»,
// directo a /configuracion) y solo la ve quien administra. Habla con la API PROPIA del desarrollo (services/configuracionLocal.js → backend bp_configuracion.py):
// el backend vuelve a comprobar el permiso en cada llamada, guarda las asignaciones en las tablas del esquema del desarrollo y audita. El navegador no decide nada:
// ocultar un botón aquí NO es el control de seguridad. El valor de un secreto viaja una vez y no se vuelve a mostrar.
//
// Contrato que la Mesa y los agentes verifican (se copia sin cambios o se respeta): la raíz con `data-agp-configuracion="estandar"`, las pestañas con
// `data-agp-pestana="usuarios|secretos|actividad"` y el modal de asignar con role="dialog" y aria-modal="true".
// El catálogo de perfiles lo entrega el backend (PERFILES de roles_propios.py): la pantalla asigna esos perfiles y no ofrece un editor de permisos que la API ignore.
import { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import useIdiomaAgp from "../hooks/useIdiomaAgp";
import { clienteDeEsteDesarrollo } from "../services/configuracionLocal";
import "../styles/configuracion-estandar.css";

const TEXTOS = {
  es: {
    titulo: "Configuración de roles y secretos", subtitulo: "Quién entra al desarrollo, con qué perfil, y los secretos manuales que usa. Cada cambio queda auditado.", volver: "Volver",
    cargando: "Cargando…", reintentar: "Reintentar", sinPermiso: "No tienes permiso para configurar este desarrollo.",
    pUsuarios: "Usuarios", pSecretos: "Secretos", pActividad: "Actividad", asignar: "Asignar usuario", quitar: "Quitar acceso", cambiar: "Cambiar perfil",
    correo: "Correo", perfil: "Perfil", inicial: "Administrador inicial", sinUsuarios: "Todavía no hay personas con acceso asignado.",
    buscar: "Buscar por nombre o correo", buscando: "Buscando…", sinResultados: "Sin resultados", elegirPerfil: "Perfil", cancelar: "Cancelar", confirmar: "Confirmar",
    okAsignado: "Cambio aplicado y auditado.", secretosAyuda: "Solo los secretos manuales de este desarrollo. El valor se guarda en el Key Vault y nunca se muestra de nuevo.",
    sinSecretos: "Este desarrollo no declara secretos manuales.", cargar: "Cargar valor", valor: "Valor", guardar: "Guardar", okSecreto: "Secreto guardado. No se muestra el valor.",
    secretosNota: "Un nombre declarado no prueba que el secreto exista. Cambiar un secreto no reinicia la aplicación.",
    fecha: "Fecha", actor: "Quién", destinatario: "A quién", cambio: "Cambio", resultado: "Resultado", sinActividad: "Sin actividad registrada.",
  },
  pt: {
    titulo: "Configuração de papéis e segredos", subtitulo: "Quem entra no desenvolvimento, com qual perfil, e os segredos manuais que ele usa. Cada mudança fica auditada.", volver: "Voltar",
    cargando: "Carregando…", reintentar: "Tentar de novo", sinPermiso: "Você não tem permissão para configurar este desenvolvimento.",
    pUsuarios: "Usuários", pSecretos: "Segredos", pActividad: "Atividade", asignar: "Atribuir usuário", quitar: "Remover acesso", cambiar: "Mudar perfil",
    correo: "E-mail", perfil: "Perfil", inicial: "Administrador inicial", sinUsuarios: "Ainda não há pessoas com acesso atribuído.",
    buscar: "Buscar por nome ou e-mail", buscando: "Buscando…", sinResultados: "Sem resultados", elegirPerfil: "Perfil", cancelar: "Cancelar", confirmar: "Confirmar",
    okAsignado: "Mudança aplicada e auditada.", secretosAyuda: "Somente os segredos manuais deste desenvolvimento. O valor fica no Key Vault e nunca é mostrado de novo.",
    sinSecretos: "Este desenvolvimento não declara segredos manuais.", cargar: "Carregar valor", valor: "Valor", guardar: "Salvar", okSecreto: "Segredo salvo. O valor não é mostrado.",
    secretosNota: "Um nome declarado não prova que o segredo exista. Mudar um segredo não reinicia a aplicação.",
    fecha: "Data", actor: "Quem", destinatario: "Para quem", cambio: "Mudança", resultado: "Resultado", sinActividad: "Sem atividade registrada.",
  },
};

export const PESTANAS = ["usuarios", "secretos", "actividad"];

/** Texto de un error sin detalles técnicos. */
export function mensajeDe(error) {
  return (error && error.message) || "No se pudo completar la operación. Intenta de nuevo.";
}

export function nombreDePerfil(perfiles, id) {
  const p = (perfiles || []).find((x) => x.id === id);
  return p ? p.nombre : id || "—";
}

export function PanelUsuarios({ estado, t, ocupado, onAsignar, onCambiar, onQuitar }) {
  const personas = estado.personas || [];
  const iniciales = estado.administradoresIniciales || [];
  return (
    <section className="agp-config__tarjeta" aria-label={t.pUsuarios}>
      <div className="agp-config__tarjeta agp-config__tarjeta--fila">
        <strong>{t.pUsuarios} <span className="agp-config__tag">{personas.length + iniciales.length}</span></strong>
        <button type="button" className="agp-config__btn agp-config__btn--primario" disabled={ocupado} onClick={onAsignar}>{t.asignar}</button>
      </div>
      {iniciales.map((c) => (
        <p key={`i-${c}`} className="agp-config__suave">{c} <span className="agp-config__tag agp-config__tag--info">{t.inicial}</span></p>
      ))}
      {personas.length === 0 && <p className="agp-config__suave">{t.sinUsuarios}</p>}
      {personas.length > 0 && (
        <div className="agp-config__tabla">
          <table>
            <thead><tr><th>{t.correo}</th><th>{t.perfil}</th><th /></tr></thead>
            <tbody>
              {personas.map((p) => (
                <tr key={p.correo}>
                  <td>{p.correo}</td>
                  <td>{nombreDePerfil(estado.perfiles, p.perfil)}</td>
                  <td>
                    <button type="button" className="agp-config__btn agp-config__btn--chico" disabled={ocupado} onClick={() => onCambiar(p)}>{t.cambiar}</button>{" "}
                    <button type="button" className="agp-config__btn agp-config__btn--chico agp-config__btn--peligro" disabled={ocupado} onClick={() => onQuitar(p)}>{t.quitar}</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

/** Modal de asignar: busca en el directorio corporativo (o recibe la persona a cambiar), elige perfil y confirma. */
export function ModalAsignar({ t, perfiles, api, persona, onCerrar, onConfirmar }) {
  const [texto, setTexto] = useState("");
  const [candidatos, setCandidatos] = useState([]);
  const [buscando, setBuscando] = useState(false);
  const [elegida, setElegida] = useState(persona || null);
  const [perfil, setPerfil] = useState(persona?.perfil || (perfiles[0]?.id ?? ""));

  useEffect(() => {
    if (elegida || String(texto).trim().length < 2 || !api) { setCandidatos([]); return undefined; }
    let vigente = true;
    setBuscando(true);
    const espera = setTimeout(() => {
      api.directorio(texto).then((l) => { if (vigente) setCandidatos(l); }).catch(() => { if (vigente) setCandidatos([]); }).finally(() => { if (vigente) setBuscando(false); });
    }, 250);
    return () => { vigente = false; clearTimeout(espera); };
  }, [texto, elegida, api]);

  return (
    <div className="agp-config__fondo">
      <div className="agp-config__modal" role="dialog" aria-modal="true" aria-label={t.asignar}>
        <h2>{persona ? t.cambiar : t.asignar}</h2>
        {!elegida && (
          <label className="agp-config__campo">{t.buscar}
            <input type="search" value={texto} onChange={(e) => setTexto(e.target.value)} autoFocus />
          </label>
        )}
        {!elegida && buscando && <p className="agp-config__suave">{t.buscando}</p>}
        {!elegida && !buscando && texto.trim().length >= 2 && candidatos.length === 0 && <p className="agp-config__suave">{t.sinResultados}</p>}
        {!elegida && candidatos.map((c) => (
          <button key={c.correo} type="button" className="agp-config__rol" onClick={() => setElegida(c)}>
            <strong>{c.nombre || c.correo}</strong><span className="agp-config__suave">{c.correo}{c.area ? ` · ${c.area}` : ""}</span>
          </button>
        ))}
        {elegida && (
          <>
            <p><strong>{elegida.nombre || elegida.correo}</strong> <span className="agp-config__suave">{elegida.correo}</span></p>
            <label className="agp-config__campo">{t.elegirPerfil}
              <select value={perfil} onChange={(e) => setPerfil(e.target.value)}>
                {perfiles.map((p) => <option key={p.id} value={p.id}>{p.nombre}</option>)}
              </select>
            </label>
          </>
        )}
        <div className="agp-config__botones">
          <button type="button" className="agp-config__btn" onClick={onCerrar}>{t.cancelar}</button>
          <button type="button" className="agp-config__btn agp-config__btn--primario" disabled={!elegida || !perfil} onClick={() => onConfirmar(elegida.correo, perfil)}>{t.confirmar}</button>
        </div>
      </div>
    </div>
  );
}

export function PanelSecretos({ secretos, t, ocupado, onGuardar }) {
  const [editando, setEditando] = useState(null);
  const [valor, setValor] = useState("");
  const nombres = secretos?.nombres || [];
  const guardar = async () => {
    const ok = await onGuardar(editando, valor);
    setValor("");   // el campo se vacía siempre, haya salido bien o mal
    if (ok) setEditando(null);
  };
  return (
    <section className="agp-config__tarjeta" aria-label={t.pSecretos}>
      <p className="agp-config__suave">{t.secretosAyuda}</p>
      {nombres.length === 0 && <p className="agp-config__suave">{t.sinSecretos}</p>}
      {nombres.map((n) => (
        <div key={n} className="agp-config__tarjeta agp-config__tarjeta--fila">
          <code>{n}</code>
          {editando === n ? (
            <span className="agp-config__acciones">
              <input type="password" autoComplete="new-password" aria-label={t.valor} value={valor} onChange={(e) => setValor(e.target.value)} />
              <button type="button" className="agp-config__btn agp-config__btn--primario agp-config__btn--chico" disabled={ocupado || !valor} onClick={guardar}>{t.guardar}</button>
              <button type="button" className="agp-config__btn agp-config__btn--chico" onClick={() => { setEditando(null); setValor(""); }}>{t.cancelar}</button>
            </span>
          ) : (
            <button type="button" className="agp-config__btn agp-config__btn--chico" disabled={ocupado} onClick={() => setEditando(n)}>{t.cargar}</button>
          )}
        </div>
      ))}
      <p className="agp-config__suave">{t.secretosNota}</p>
    </section>
  );
}

export function PanelActividad({ filas, t }) {
  if (!filas || filas.length === 0) return <section className="agp-config__tarjeta"><p className="agp-config__suave">{t.sinActividad}</p></section>;
  return (
    <section className="agp-config__tarjeta agp-config__tabla" aria-label={t.pActividad}>
      <table>
        <thead><tr><th>{t.fecha}</th><th>{t.actor}</th><th>{t.destinatario}</th><th>{t.cambio}</th><th>{t.resultado}</th></tr></thead>
        <tbody>
          {filas.map((f, i) => (
            <tr key={`${f.fecha}-${i}`}>
              <td>{f.fecha}</td><td>{f.actor}</td><td>{f.destinatario}</td>
              <td>{f.perfilAnterior || "—"} → {f.perfilNuevo || "—"}</td><td>{f.resultado}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

export default function ConfiguracionDesarrollo({ onVolver, api: apiInyectada }) {
  const { getAuthToken } = useAuth();
  const { idioma } = useIdiomaAgp();
  const t = TEXTOS[idioma] || TEXTOS.es;
  const api = useMemo(() => apiInyectada || clienteDeEsteDesarrollo(getAuthToken), [apiInyectada, getAuthToken]);
  const [estado, setEstado] = useState(null);
  const [secretos, setSecretos] = useState(null);
  const [actividad, setActividad] = useState(null);
  const [pestana, setPestana] = useState("usuarios");
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");
  const [ocupado, setOcupado] = useState(false);
  const [modal, setModal] = useState(null);   // { persona } | {}

  const cargar = useCallback(async () => {
    setError("");
    try {
      const est = await api.estado();
      setEstado(est);
      if (est.puedeConfigurar) {
        const [sec, act] = await Promise.all([api.secretos().catch(() => null), api.actividad().catch(() => [])]);
        setSecretos(sec);
        setActividad(act);
      }
    } catch (e) { setError(mensajeDe(e)); }
  }, [api]);
  useEffect(() => { cargar(); }, [cargar]);

  const hacer = async (accion, ok) => {
    setOcupado(true); setError(""); setAviso("");
    try { const r = await accion(); setAviso(r?.aviso || ok); await cargar(); return true; }
    catch (e) { setError(mensajeDe(e)); return false; }
    finally { setOcupado(false); }
  };

  return (
    <main className="agp-config" data-agp-configuracion="estandar">
      <header className="agp-config__cabecera">
        <div><h1>{t.titulo}</h1><p className="agp-config__suave">{t.subtitulo}</p></div>
        {onVolver && <button type="button" className="agp-config__btn" onClick={onVolver}>{t.volver}</button>}
      </header>
      {error && <p role="alert" className="agp-config__aviso agp-config__aviso--error">{error} <button type="button" className="agp-config__btn agp-config__btn--chico" onClick={cargar}>{t.reintentar}</button></p>}
      {aviso && <p role="status" className="agp-config__aviso agp-config__aviso--ok">{aviso}</p>}
      {!estado && !error && <p className="agp-config__suave">{t.cargando}</p>}
      {estado && !estado.puedeConfigurar && <p role="alert" className="agp-config__aviso agp-config__aviso--warn">{t.sinPermiso}</p>}
      {estado?.puedeConfigurar && (
        <>
          <div className="agp-config__pestanas" role="tablist">
            {PESTANAS.map((id) => (
              <button key={id} type="button" role="tab" data-agp-pestana={id} aria-selected={pestana === id} className="agp-config__pestana" onClick={() => setPestana(id)}>
                {{ usuarios: t.pUsuarios, secretos: t.pSecretos, actividad: t.pActividad }[id]}
              </button>
            ))}
          </div>
          {pestana === "usuarios" && (
            <PanelUsuarios estado={estado} t={t} ocupado={ocupado} onAsignar={() => setModal({})} onCambiar={(persona) => setModal({ persona })}
              onQuitar={(p) => hacer(() => api.asignar(p.correo, null), t.okAsignado)} />
          )}
          {pestana === "secretos" && <PanelSecretos secretos={secretos} t={t} ocupado={ocupado} onGuardar={(n, v) => hacer(() => api.cargarSecreto(n, v), t.okSecreto)} />}
          {pestana === "actividad" && <PanelActividad filas={actividad} t={t} />}
        </>
      )}
      {modal && (
        <ModalAsignar t={t} perfiles={estado?.perfiles || []} api={api} persona={modal.persona} onCerrar={() => setModal(null)}
          onConfirmar={async (correo, perfil) => { if (await hacer(() => api.asignar(correo, perfil), t.okAsignado)) setModal(null); }} />
      )}
    </main>
  );
}
