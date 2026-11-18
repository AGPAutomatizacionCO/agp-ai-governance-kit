// Pantalla estándar «Configuración de roles y secretos» de AGP (norma ACCESO-Y-ROLES-DEL-DESARROLLO.md §4 y §6; spec 023 de la Mesa). Es la misma en todo
// desarrollo: se llega a ella desde el menú de usuario («Configuración», directo) y ahí quien administra gestiona los roles, los usuarios y los secretos.
// Todo va por el túnel de la Mesa (services/rolesMesa.js): la pantalla PIDE y la Mesa valida, aplica y audita. El valor de un secreto viaja una vez y no se
// vuelve a mostrar.
//
// Rol = nombre + vistas que puede abrir (con sus acciones) + datos que consulta + «vista general» opcional. En ROLES.md v2 las vistas son los módulos, las acciones
// son sus funciones y los datos son las áreas; «perfil» es el nombre histórico del mismo concepto y no se muestra.
// Contrato que la Mesa y los agentes verifican (se copia sin cambios o se respeta): la raíz con `data-agp-configuracion="estandar"`, las pestañas con
// `data-agp-pestana="roles|usuarios|secretos|actividad"` y el modal de asignar con role="dialog" y aria-modal="true".
import { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import useIdiomaAgp from "../hooks/useIdiomaAgp";
import { clienteDeEsteDesarrollo } from "../services/rolesMesa";
import "../styles/configuracion-estandar.css";

const TEXTOS = {
  es: {
    titulo: "Configuración de roles y secretos", subtitulo: "Qué vistas ve cada persona y qué secretos usa el desarrollo. La Mesa valida y aplica los cambios.", volver: "Volver",
    cargando: "Cargando…", reintentar: "Reintentar", sinMesa: "La conexión con la Mesa de Ayuda no está activa en este ambiente (ROLES_DESDE_MESA). Pídele a IT que la active.",
    soloV2: "Este desarrollo todavía usa ROLES.md v1: actualízalo a v2 para gestionar roles desde aquí.",
    soloLectura: "Eres administrador secundario: ves todo y puedes editar la definición de los roles. Asignar usuarios y cargar secretos solo lo hace el administrador principal.",
    pRoles: "Roles", pUsuarios: "Usuarios", pSecretos: "Secretos", pActividad: "Actividad",
    nuevoRol: "Nuevo rol", fijo: "Fijo", personalizado: "Personalizado", vistaGeneral: "Vista general", personas: "usuarios", vistas: "vistas", acciones: "acciones", datos: "datos",
    adminTxt: "Administra el desarrollo, asigna roles y carga secretos.", usuarioTxt: "Rol básico de Entra ID.", fijoNota: "Este rol vive en Entra ID y no se edita aquí.",
    nombreRol: "Nombre del rol", vistasYAcciones: "Vistas y acciones", vistasAyuda: "Solo las vistas activadas se abren para quien tenga este rol.",
    datosQueVe: "Datos que consulta", datosAyuda: "Solo datos del manifiesto aprobado.", marcarGeneral: "Vista general", generalAyuda: "Es lo que ve quien entra sin rol. Nunca incluye funciones administrativas.",
    asiSeVe: "Así lo ve quien tenga este rol", ningunaVista: "No ve ninguna vista todavía.", guardar: "Guardar rol", duplicar: "Duplicar", descartar: "Descartar cambios", eliminar: "Eliminar", noEliminar: "No se puede eliminar mientras tenga usuarios.",
    sinAreasAviso: "Este rol no tiene datos: sin ellos no abre nada. Elige al menos un dato.", copia: "copia", rolNuevo: "Rol nuevo",
    buscar: "Buscar", nombreOCorreo: "Nombre o correo", todosRoles: "Todos los roles", todosOrigenes: "Todos los orígenes", origen: "Origen", limpiar: "Limpiar filtros", mostrando: "{n} de {m} usuarios", ninguno: "Ningún usuario coincide.",
    usuario: "Usuario", rol: "Rol", datosCol: "Datos", fecha: "Fecha", estado: "Estado", quitar: "Quitar",
    oAsignado: "Asignado", oRegla: "Regla de área", oGeneral: "Vista general", sinRol: "Sin rol",
    asignarUsuario: "Asignar usuario", paso1: "Usuario", paso2: "Rol", paso3: "Confirmar", elegirUsuario: "Busca al usuario en el directorio de AGP", escribe: "Escribe al menos 3 letras",
    sinCoincidencias: "Sin coincidencias. Prueba con el nombre o el correo completo.", elegirRol: "Elige el rol de", resumen: "Resumen", tendra: "{p} tendrá el rol «{r}».", sinRolOpcion: "Sin rol propio (queda con la vista general)",
    otraAreaT: "Si el usuario es de otra área, la Mesa exige dos textos", porQue: "Por qué se le autoriza", criterio: "Criterio de negocio de este rol y acceso", minimo: "mínimo 20 letras",
    atras: "Atrás", siguiente: "Siguiente", enviar: "Enviar petición", cancelar: "Cancelar", cerrar: "Cerrar", notaAsignar: "No se escribe nada directamente: la Mesa valida la petición y la aplica; queda en el historial.",
    reglasT: "Reglas por área de Microsoft", reglasD: "Se definen en ROLES.md (accesoPorArea) y la Mesa las aplica: quien pertenece al área recibe el rol solo.", area: "Área de Microsoft",
    reglasPrio: "Prioridad: un rol asignado a mano gana a la regla por área, y esta gana a la vista general.",
    secretosT: "Secretos del desarrollo", secretosD: "Solo los que declara .agp/runtime.yaml. Los valores nunca se muestran.", secreto: "Secreto", variable: "Variable", actualizado: "Actualizado", cargado: "Cargado", falta: "Falta",
    oManual: "Manual", oMesa: "La crea la Mesa", cargarValor: "Cargar valor", cargarDe: "Cargar el valor de", nuevoValor: "Nuevo valor", unaVez: "El valor viaja una sola vez, se guarda y no se puede volver a ver.", guardarValor: "Guardar valor",
    reiniciarNota: "La app lee el secreto con el tiempo; reiníciala para aplicarlo ya.", reiniciar: "Reiniciar app", valorOculto: "valor oculto", sinSecretos: "El desarrollo no declara secretos manuales.",
    actividadT: "Actividad", actividadD: "Peticiones en curso e historial. Las pendientes se pueden cancelar.", todas: "Todas", queCol: "Qué", pedidoPor: "Pedido por", cancelarPet: "Cancelar",
    ePendiente: "Pendiente", eValidada: "Validada", eAplicada: "Aplicada", eRechazada: "Rechazada", eFallida: "Fallida", eCancelada: "Cancelada", sinPeticiones: "Todavía no hay peticiones.",
    okPeticion: "Listo. La Mesa aplicó el cambio.", okSecreto: "Guardado. El valor no se puede volver a ver.", okReinicio: "Reinicio pedido. La app volverá a leer los secretos.",
  },
  pt: {
    titulo: "Configuração de papéis e segredos", subtitulo: "Quais visões cada pessoa vê e quais segredos o desenvolvimento usa. A Mesa valida e aplica as mudanças.", volver: "Voltar",
    cargando: "Carregando…", reintentar: "Tentar de novo", sinMesa: "A conexão com a Mesa de Ayuda não está ativa neste ambiente (ROLES_DESDE_MESA). Peça à TI que a ative.",
    soloV2: "Este desenvolvimento ainda usa ROLES.md v1: atualize para v2 para gerenciar papéis aqui.",
    soloLectura: "Você é administrador secundário: vê tudo e pode editar a definição dos papéis. Atribuir usuários e carregar segredos é feito só pelo administrador principal.",
    pRoles: "Papéis", pUsuarios: "Usuários", pSecretos: "Segredos", pActividad: "Atividade",
    nuevoRol: "Novo papel", fijo: "Fixo", personalizado: "Personalizado", vistaGeneral: "Visão geral", personas: "usuários", vistas: "visões", acciones: "ações", datos: "dados",
    adminTxt: "Administra o desenvolvimento, atribui papéis e carrega segredos.", usuarioTxt: "Papel básico do Entra ID.", fijoNota: "Este papel vive no Entra ID e não se edita aqui.",
    nombreRol: "Nome do papel", vistasYAcciones: "Visões e ações", vistasAyuda: "Só as visões ativadas são abertas para quem tiver este papel.",
    datosQueVe: "Dados que consulta", datosAyuda: "Somente dados do manifesto aprovado.", marcarGeneral: "Visão geral", generalAyuda: "É o que vê quem entra sem papel. Nunca inclui funções administrativas.",
    asiSeVe: "Assim vê quem tiver este papel", ningunaVista: "Ainda não vê nenhuma visão.", guardar: "Salvar papel", duplicar: "Duplicar", descartar: "Descartar alterações", eliminar: "Excluir", noEliminar: "Não pode ser excluído enquanto tiver usuários.",
    sinAreasAviso: "Este papel não tem dados: sem eles não abre nada. Escolha pelo menos um dado.", copia: "cópia", rolNuevo: "Papel novo",
    buscar: "Buscar", nombreOCorreo: "Nome ou e-mail", todosRoles: "Todos os papéis", todosOrigenes: "Todas as origens", origen: "Origem", limpiar: "Limpar filtros", mostrando: "{n} de {m} usuários", ninguno: "Nenhum usuário corresponde.",
    usuario: "Usuário", rol: "Papel", datosCol: "Dados", fecha: "Data", estado: "Estado", quitar: "Remover",
    oAsignado: "Atribuído", oRegla: "Regra de área", oGeneral: "Visão geral", sinRol: "Sem papel",
    asignarUsuario: "Atribuir usuário", paso1: "Usuário", paso2: "Papel", paso3: "Confirmar", elegirUsuario: "Procure o usuário no diretório da AGP", escribe: "Digite pelo menos 3 letras",
    sinCoincidencias: "Sem resultados. Tente o nome ou o e-mail completo.", elegirRol: "Escolha o papel de", resumen: "Resumo", tendra: "{p} terá o papel «{r}».", sinRolOpcion: "Sem papel próprio (fica com a visão geral)",
    otraAreaT: "Se o usuário for de outra área, a Mesa exige dois textos", porQue: "Por que é autorizado", criterio: "Critério de negócio deste papel e acesso", minimo: "mínimo de 20 letras",
    atras: "Voltar", siguiente: "Próximo", enviar: "Enviar solicitação", cancelar: "Cancelar", cerrar: "Fechar", notaAsignar: "Nada é gravado diretamente: a Mesa valida a solicitação e a aplica; fica no histórico.",
    reglasT: "Regras por área da Microsoft", reglasD: "São definidas em ROLES.md (accesoPorArea) e a Mesa as aplica: quem pertence à área recebe o papel sozinho.", area: "Área da Microsoft",
    reglasPrio: "Prioridade: um papel atribuído manualmente vence a regra por área, e esta vence a visão geral.",
    secretosT: "Segredos do desenvolvimento", secretosD: "Somente os que .agp/runtime.yaml declara. Os valores nunca são exibidos.", secreto: "Segredo", variable: "Variável", actualizado: "Atualizado", cargado: "Carregado", falta: "Falta",
    oManual: "Manual", oMesa: "Criado pela Mesa", cargarValor: "Carregar valor", cargarDe: "Carregar o valor de", nuevoValor: "Novo valor", unaVez: "O valor viaja uma única vez, é guardado e não pode ser visto de novo.", guardarValor: "Salvar valor",
    reiniciarNota: "O app lê o segredo com o tempo; reinicie-o para aplicar já.", reiniciar: "Reiniciar app", valorOculto: "valor oculto", sinSecretos: "O desenvolvimento não declara segredos manuais.",
    actividadT: "Atividade", actividadD: "Solicitações em andamento e histórico. As pendentes podem ser canceladas.", todas: "Todas", queCol: "O quê", pedidoPor: "Pedido por", cancelarPet: "Cancelar",
    ePendiente: "Pendente", eValidada: "Validada", eAplicada: "Aplicada", eRechazada: "Rejeitada", eFallida: "Falhou", eCancelada: "Cancelada", sinPeticiones: "Ainda não há solicitações.",
    okPeticion: "Pronto. A Mesa aplicou a mudança.", okSecreto: "Salvo. O valor não pode ser visto de novo.", okReinicio: "Reinício solicitado. O app voltará a ler os segredos.",
  },
};

const fmt = (texto, valores) => Object.keys(valores).reduce((a, k) => a.split(`{${k}}`).join(valores[k]), texto);
const NIVELES_FIJOS = [{ id: "@admin", nombre: "Admin", tipo: "admin" }, { id: "@usuario", nombre: "Usuario", tipo: "usuario" }];

// ── Piezas puras (se prueban sin dibujar) ─────────────────────────────────────────────────────────────────────────────────────────────────────

/** Qué puede hacer quien mira, según lo que responde la Mesa. Lo que la pantalla deshabilita, el servidor igual lo rechaza. */
export function capacidades(estado, secretos) {
  const yo = estado?.yo || {};
  return {
    esAdmin: Boolean(yo.esAdmin),
    asignar: Boolean(yo.asignarPersonas),
    editarRoles: Boolean(yo.editarPerfiles),
    principal: Boolean(yo.adminGlobal),
    cargarSecretos: Boolean(secretos?.puedeCargar),
  };
}

/** Permisos «modulo» y «modulo.funcion» en el orden del catálogo (el que guarda la Mesa). */
export function ordenarPermisos(catalogo, permisos) {
  const lista = permisos instanceof Set ? permisos : new Set(permisos || []);
  return (catalogo || []).flatMap((m) => [m.modulo, ...m.funciones.map((f) => `${m.modulo}.${f.id}`)]).filter((p) => lista.has(p));
}

/** Resumen de un rol: cuántas vistas, acciones y datos abre. */
export function resumenDeRol(perfil) {
  const permisos = perfil?.permisos || [];
  const vistas = permisos.filter((p) => !p.includes(".")).length;
  return { vistas, acciones: permisos.length - vistas, datos: (perfil?.areas || []).length };
}

/** Origen de un usuario: asignado a mano, por la regla de su área de Microsoft o por la vista general. */
export function origenDe(persona) {
  if (persona?.porArea) return "regla";
  if (persona?.vistaGeneral) return "general";
  return "asignado";
}

/** Filtra la lista de usuarios por texto, rol y origen. `rol`: id de perfil, «@admin», «@usuario» o «todos». */
export function filtrarPersonas(personas, { texto = "", rol = "todos", origen = "todos" } = {}) {
  const q = texto.trim().toLowerCase();
  return (personas || []).filter((p) => {
    if (q && !`${p.nombre || ""} ${p.correo || ""}`.toLowerCase().includes(q)) return false;
    if (rol !== "todos") {
      const id = p.perfil || (p.nivel === "usuario" ? "@usuario" : p.nivel ? "@admin" : "");
      if (id !== rol) return false;
    }
    return origen === "todos" || origenDe(p) === origen;
  });
}

/** Qué pestañas ve cada quien: Secretos y Actividad solo con permiso de administración. */
export function pestanasVisibles(cap) {
  return cap.esAdmin ? ["roles", "usuarios", "secretos", "actividad"] : [];
}

/** El rol nuevo o el que se edita, listo para pedirle a la Mesa que lo guarde. */
export function perfilParaGuardar(borrador, catalogo) {
  const perfil = { nombre: borrador.nombre.trim().replace(/\s+/g, " "), permisos: ordenarPermisos(catalogo, borrador.permisos), areas: [...(borrador.areas || [])] };
  return borrador.id ? { ...perfil, id: borrador.id } : perfil;
}

// ── Pantalla ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

export default function ConfiguracionDesarrollo({ api: apiProp, onVolver }) {
  const { getAuthToken } = useAuth();
  const { idioma } = useIdiomaAgp();
  const t = TEXTOS[idioma] || TEXTOS.es;
  const api = useMemo(() => apiProp || clienteDeEsteDesarrollo(getAuthToken), [apiProp, getAuthToken]);

  const [estado, setEstado] = useState(null);
  const [peticiones, setPeticiones] = useState([]);
  const [secretos, setSecretos] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");
  const [ocupado, setOcupado] = useState(false);
  const [pestana, setPestana] = useState("roles");

  const recargar = useCallback(async () => {
    if (!api) { setCargando(false); return; }
    setCargando(true);
    setError("");
    try {
      const est = await api.estado();
      setEstado(est);
      const [pet, sec] = await Promise.all([api.peticiones().catch(() => []), api.secretos().catch(() => null)]);
      setPeticiones(Array.isArray(pet) ? pet : pet?.peticiones || []);
      setSecretos(sec);
    } catch (e) {
      setError(e.message || String(e));
    } finally {
      setCargando(false);
    }
  }, [api]);

  useEffect(() => { recargar(); }, [recargar]);

  // Toda escritura pasa por aquí: se pide, la Mesa responde, se avisa y se vuelve a leer.
  const hacer = useCallback(async (accion, mensajeOk) => {
    setOcupado(true);
    setError("");
    setAviso("");
    try {
      await accion();
      setAviso(mensajeOk);
      await recargar();
      return true;
    } catch (e) {
      setError(e.message || String(e));
      return false;
    } finally {
      setOcupado(false);
    }
  }, [recargar]);

  const cap = capacidades(estado, secretos);
  const ayuda = !api ? t.sinMesa : null;

  return (
    <main className="agp-config" data-agp-configuracion="estandar">
      <div className="agp-config__cabecera">
        <div>
          <h1>{t.titulo}</h1>
          <p className="agp-config__suave">{t.subtitulo}</p>
        </div>
        {onVolver && <button type="button" className="agp-config__btn" onClick={onVolver}>{t.volver}</button>}
      </div>

      {ayuda && <p role="status" className="agp-config__aviso agp-config__aviso--info">{ayuda}</p>}
      {estado && estado.version !== "v2" && <p role="status" className="agp-config__aviso agp-config__aviso--info">{t.soloV2}</p>}
      {estado && cap.esAdmin && !cap.principal && <p role="status" className="agp-config__aviso agp-config__aviso--info">{t.soloLectura}</p>}
      {aviso && <p role="status" className="agp-config__aviso agp-config__aviso--ok">{aviso}</p>}
      {error && (
        <p role="alert" className="agp-config__aviso agp-config__aviso--error">{error} <button type="button" className="agp-config__btn agp-config__btn--chico" onClick={recargar}>{t.reintentar}</button></p>
      )}
      {cargando && !estado && <p role="status">{t.cargando}</p>}

      {estado && estado.version === "v2" && (
        <>
          <div role="tablist" aria-label={t.titulo} className="agp-config__pestanas">
            {[["roles", t.pRoles], ["usuarios", t.pUsuarios], ["secretos", t.pSecretos], ["actividad", `${t.pActividad} (${peticiones.filter((p) => p.Estado === "pendiente").length})`]].map(([id, etiqueta]) => (
              <button key={id} type="button" role="tab" data-agp-pestana={id} aria-selected={pestana === id} className="agp-config__pestana" onClick={() => { setPestana(id); setAviso(""); }}>{etiqueta}</button>
            ))}
          </div>
          {pestana === "roles" && <PestanaRoles t={t} estado={estado} cap={cap} ocupado={ocupado} hacer={hacer} api={api} />}
          {pestana === "usuarios" && <PestanaUsuarios t={t} estado={estado} cap={cap} ocupado={ocupado} hacer={hacer} api={api} idioma={idioma} />}
          {pestana === "secretos" && <PestanaSecretos t={t} secretos={secretos} cap={cap} ocupado={ocupado} hacer={hacer} api={api} />}
          {pestana === "actividad" && <PestanaActividad t={t} peticiones={peticiones} cap={cap} ocupado={ocupado} hacer={hacer} api={api} />}
        </>
      )}
    </main>
  );
}

// ── Roles ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

function PestanaRoles({ t, estado, cap, ocupado, hacer, api }) {
  const perfiles = estado.perfiles || [];
  const catalogo = estado.catalogoPermisos || [];
  const dominios = estado.catalogo || [];
  const [sel, setSel] = useState(perfiles[0]?.id || "@nuevo");
  const [borrador, setBorrador] = useState(null);
  const actual = perfiles.find((p) => p.id === sel);

  useEffect(() => {
    if (sel === "@nuevo") return;
    const p = perfiles.find((x) => x.id === sel);
    setBorrador(p ? { id: p.id, nombre: p.nombre, permisos: new Set(p.permisos), areas: new Set(p.areas || []), general: Boolean(p.general) } : null);
  }, [sel, estado]);

  const nuevo = () => { setSel("@nuevo"); setBorrador({ id: null, nombre: t.rolNuevo, permisos: new Set(), areas: new Set(), general: false }); };
  const duplicar = () => { setSel("@nuevo"); setBorrador({ id: null, nombre: `${borrador.nombre} (${t.copia})`, permisos: new Set(borrador.permisos), areas: new Set(borrador.areas), general: false }); };
  const descartar = () => { if (actual) setBorrador({ id: actual.id, nombre: actual.nombre, permisos: new Set(actual.permisos), areas: new Set(actual.areas || []), general: Boolean(actual.general) }); else nuevo(); };

  const alternar = (conjunto, valor) => { const s = new Set(conjunto); if (s.has(valor)) s.delete(valor); else s.add(valor); return s; };
  const alternarModulo = (m) => {
    setBorrador((b) => {
      const permisos = new Set(b.permisos);
      if (permisos.has(m.modulo)) { permisos.delete(m.modulo); m.funciones.forEach((f) => permisos.delete(`${m.modulo}.${f.id}`)); } else permisos.add(m.modulo);
      return { ...b, permisos };
    });
  };

  const guardado = borrador && actual && borrador.nombre === actual.nombre && ordenarPermisos(catalogo, borrador.permisos).join("|") === actual.permisos.join("|")
    && [...borrador.areas].sort().join("|") === [...(actual.areas || [])].sort().join("|");
  const sucio = borrador && (sel === "@nuevo" || !guardado);
  const nombreOk = borrador && borrador.nombre.trim().length >= 3;
  const personasDelRol = actual?.personas || 0;
  const guardar = () => hacer(async () => {
    await api.solicitar({ accion: "guardar_perfil", perfil: perfilParaGuardar({ ...borrador, areas: [...borrador.areas] }, catalogo) });
  }, t.okPeticion).then((ok) => { if (ok && sel === "@nuevo") setSel(perfiles[0]?.id || "@nuevo"); });
  const eliminar = () => hacer(() => api.solicitar({ accion: "borrar_perfil", perfil: actual.id }), t.okPeticion);
  const marcarGeneral = () => hacer(() => api.solicitar({ accion: "marcar_vista_general", perfil: borrador.general ? null : actual.id }), t.okPeticion);

  const vistasActivas = borrador ? catalogo.filter((m) => borrador.permisos.has(m.modulo)) : [];

  return (
    <div className="agp-config__roles">
      <div className="agp-config__lista">
        <button type="button" className="agp-config__btn agp-config__btn--primario" disabled={!cap.editarRoles || ocupado} onClick={nuevo}>+ {t.nuevoRol}</button>
        {NIVELES_FIJOS.map((n) => (
          <div key={n.id} className="agp-config__rol agp-config__rol--fijo">
            <div className="agp-config__rolcab"><strong>{n.nombre}</strong><span className="agp-config__tag agp-config__tag--info">{t.fijo}</span></div>
            <span className="agp-config__suave">{n.tipo === "admin" ? t.adminTxt : t.usuarioTxt}</span>
          </div>
        ))}
        {perfiles.map((p) => {
          const r = resumenDeRol(p);
          return (
            <button key={p.id} type="button" className="agp-config__rol" aria-pressed={sel === p.id} onClick={() => setSel(p.id)}>
              <span className="agp-config__rolcab"><strong>{p.nombre}</strong><span className={`agp-config__tag ${p.general ? "agp-config__tag--ok" : ""}`}>{p.general ? t.vistaGeneral : t.personalizado}</span></span>
              <span className="agp-config__suave">{r.vistas} {t.vistas} · {r.acciones} {t.acciones} · {r.datos} {t.datos} · {p.personas || 0} {t.personas}</span>
            </button>
          );
        })}
      </div>

      {borrador && (
        <div className="agp-config__tarjeta">
          <label className="agp-config__campo"><strong>{t.nombreRol}</strong>
            <input value={borrador.nombre} disabled={!cap.editarRoles} onChange={(e) => setBorrador({ ...borrador, nombre: e.target.value })} />
          </label>

          <fieldset className="agp-config__grupo">
            <legend>{t.vistasYAcciones}</legend>
            <p className="agp-config__suave">{t.vistasAyuda}</p>
            {catalogo.map((m) => {
              const activa = borrador.permisos.has(m.modulo);
              return (
                <div key={m.modulo} className="agp-config__vista">
                  <label className="agp-config__interruptor">
                    <input type="checkbox" role="switch" checked={activa} disabled={!cap.editarRoles} onChange={() => alternarModulo(m)} />
                    <strong>{m.nombre}</strong>
                  </label>
                  <div className="agp-config__acciones">
                    {m.funciones.map((f) => {
                      const id = `${m.modulo}.${f.id}`;
                      return (
                        <button key={id} type="button" className="agp-config__chip" aria-pressed={borrador.permisos.has(id)} disabled={!cap.editarRoles || !activa}
                          onClick={() => setBorrador({ ...borrador, permisos: alternar(borrador.permisos, id) })}>{f.nombre}</button>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </fieldset>

          <fieldset className="agp-config__grupo">
            <legend>{t.datosQueVe}</legend>
            <p className="agp-config__suave">{t.datosAyuda}</p>
            {dominios.map((d) => (
              <div key={d.id} className="agp-config__acciones">
                <span className="agp-config__suave">{d.nombre}</span>
                {d.areas.map((a) => (
                  <button key={a.id} type="button" className="agp-config__chip" aria-pressed={borrador.areas.has(a.id)} disabled={!cap.editarRoles}
                    onClick={() => setBorrador({ ...borrador, areas: alternar(borrador.areas, a.id) })}>{a.nombre}</button>
                ))}
              </div>
            ))}
            {estado.rolesDeAcceso && borrador.areas.size === 0 && <p role="alert" className="agp-config__aviso agp-config__aviso--error">{t.sinAreasAviso}</p>}
          </fieldset>

          {actual && (
            <label className="agp-config__interruptor">
              <input type="checkbox" role="switch" checked={borrador.general} disabled={!cap.asignar || ocupado || sucio} onChange={marcarGeneral} />
              <span><strong>{t.marcarGeneral}</strong><br /><span className="agp-config__suave">{t.generalAyuda}</span></span>
            </label>
          )}

          <div className="agp-config__vista-previa">
            <strong>{t.asiSeVe}</strong>
            <div className="agp-config__acciones">
              {vistasActivas.map((m) => <span key={m.modulo} className="agp-config__tag agp-config__tag--ok">{m.nombre}</span>)}
              {vistasActivas.length === 0 && <span className="agp-config__suave">{t.ningunaVista}</span>}
            </div>
          </div>

          <div className="agp-config__botones">
            <button type="button" className="agp-config__btn agp-config__btn--primario" disabled={!cap.editarRoles || ocupado || !sucio || !nombreOk} onClick={guardar}>{t.guardar}</button>
            <button type="button" className="agp-config__btn" disabled={!cap.editarRoles || ocupado} onClick={duplicar}>{t.duplicar}</button>
            <button type="button" className="agp-config__btn" disabled={!sucio} onClick={descartar}>{t.descartar}</button>
            <button type="button" className="agp-config__btn agp-config__btn--peligro" disabled={!cap.editarRoles || ocupado || !actual || personasDelRol > 0} onClick={eliminar}>{t.eliminar}</button>
          </div>
          {actual && personasDelRol > 0 && <p className="agp-config__suave">{t.noEliminar}</p>}
        </div>
      )}
    </div>
  );
}

// ── Usuarios ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

function PestanaUsuarios({ t, estado, cap, ocupado, hacer, api }) {
  const perfiles = estado.perfiles || [];
  const [f, setF] = useState({ texto: "", rol: "todos", origen: "todos" });
  const [modal, setModal] = useState(false);
  const nombreDePerfil = (id) => perfiles.find((p) => p.id === id)?.nombre;
  const filtradas = filtrarPersonas(estado.personas, f);
  const sinFiltros = f.texto === "" && f.rol === "todos" && f.origen === "todos";
  const etiquetaOrigen = { asignado: t.oAsignado, regla: t.oRegla, general: t.oGeneral };
  const rolDe = (p) => nombreDePerfil(p.perfil) || p.etiqueta || (p.nivel === "global" || p.nivel === "admin" ? "Admin" : p.nivel === "usuario" ? "Usuario" : t.sinRol);

  return (
    <div className="agp-config__usuarios">
      <div className="agp-config__tarjeta agp-config__tarjeta--fila">
        <div><strong>{t.pUsuarios}</strong> <span className="agp-config__tag">{(estado.personas || []).length}</span></div>
        <button type="button" className="agp-config__btn agp-config__btn--primario" disabled={!cap.asignar || ocupado} onClick={() => setModal(true)}>{t.asignarUsuario}</button>
      </div>

      <div className="agp-config__tarjeta">
        <div className="agp-config__filtros">
          <label className="agp-config__campo">{t.buscar}<input placeholder={t.nombreOCorreo} value={f.texto} onChange={(e) => setF({ ...f, texto: e.target.value })} /></label>
          <label className="agp-config__campo">{t.rol}
            <select value={f.rol} onChange={(e) => setF({ ...f, rol: e.target.value })}>
              <option value="todos">{t.todosRoles}</option><option value="@admin">Admin</option><option value="@usuario">Usuario</option>
              {perfiles.map((p) => <option key={p.id} value={p.id}>{p.nombre}</option>)}
            </select>
          </label>
          <label className="agp-config__campo">{t.origen}
            <select value={f.origen} onChange={(e) => setF({ ...f, origen: e.target.value })}>
              <option value="todos">{t.todosOrigenes}</option><option value="asignado">{t.oAsignado}</option><option value="regla">{t.oRegla}</option><option value="general">{t.oGeneral}</option>
            </select>
          </label>
          <button type="button" className="agp-config__btn" disabled={sinFiltros} onClick={() => setF({ texto: "", rol: "todos", origen: "todos" })}>{t.limpiar}</button>
        </div>
        <p className="agp-config__suave">{fmt(t.mostrando, { n: filtradas.length, m: (estado.personas || []).length })}</p>
        <div className="agp-config__tabla">
          <table>
            <thead><tr><th scope="col">{t.usuario}</th><th scope="col">{t.rol}</th><th scope="col">{t.origen}</th><th scope="col">{t.datosCol}</th><th scope="col" /></tr></thead>
            <tbody>
              {filtradas.length === 0 && <tr><td colSpan={5} className="agp-config__suave">{t.ninguno}</td></tr>}
              {filtradas.map((p) => (
                <tr key={p.correo}>
                  <td><strong>{p.nombre}</strong><br /><span className="agp-config__suave">{p.correo}</span></td>
                  <td>{rolDe(p)}</td>
                  <td><span className="agp-config__tag">{etiquetaOrigen[origenDe(p)]}</span></td>
                  <td>{(p.areas || []).join(", ")}</td>
                  <td>{p.editable && p.perfil && (
                    <button type="button" className="agp-config__btn agp-config__btn--chico" disabled={!cap.asignar || ocupado}
                      onClick={() => hacer(() => api.solicitar({ accion: "asignar_rol_acceso", correo: p.correo, perfil: null }), t.okPeticion)}>{t.quitar}</button>
                  )}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="agp-config__tarjeta">
        <h2>{t.reglasT}</h2>
        <p className="agp-config__suave">{t.reglasD}</p>
        <table>
          <thead><tr><th scope="col">{t.area}</th><th scope="col">{t.rol}</th></tr></thead>
          <tbody>
            {(estado.accesoPorArea || []).map((r) => <tr key={`${r.area}-${r.perfil}`}><td><strong>{r.area}</strong></td><td>{nombreDePerfil(r.perfil) || r.perfil}</td></tr>)}
          </tbody>
        </table>
        <p className="agp-config__suave">{t.reglasPrio}</p>
      </div>

      {modal && <ModalAsignar t={t} perfiles={perfiles} cerrar={() => setModal(false)} api={api} hacer={hacer} />}
    </div>
  );
}

function ModalAsignar({ t, perfiles, cerrar, api, hacer }) {
  const [paso, setPaso] = useState(1);
  const [q, setQ] = useState("");
  const [candidatos, setCandidatos] = useState([]);
  const [buscando, setBuscando] = useState(false);
  const [persona, setPersona] = useState(null);
  const [rol, setRol] = useState("");
  const [porQue, setPorQue] = useState("");
  const [criterio, setCriterio] = useState("");

  useEffect(() => {
    const texto = q.trim();
    if (texto.length < 3) { setCandidatos([]); return undefined; }
    let vigente = true;
    setBuscando(true);
    const espera = setTimeout(() => {
      api.directorio(texto).then((l) => { if (vigente) setCandidatos(l); }).catch(() => { if (vigente) setCandidatos([]); }).finally(() => { if (vigente) setBuscando(false); });
    }, 250);
    return () => { vigente = false; clearTimeout(espera); };
  }, [q, api]);

  const rolElegido = perfiles.find((p) => p.id === rol);
  const siguienteOk = paso === 1 ? Boolean(persona) : paso === 2 ? true : false;
  const enviar = async () => {
    const extra = {};
    if (porQue.trim()) extra.justificacion = porQue.trim();
    if (criterio.trim()) extra.criterio = criterio.trim();
    const ok = await hacer(() => api.solicitar({ accion: "asignar_rol_acceso", correo: persona.correo, perfil: rol || null, ...extra }), t.okPeticion);
    if (ok) cerrar();
  };

  return (
    <div className="agp-config__fondo">
      <div role="dialog" aria-modal="true" aria-label={t.asignarUsuario} className="agp-config__modal">
        <div className="agp-config__cabecera">
          <h2>{t.asignarUsuario}</h2>
          <button type="button" className="agp-config__btn agp-config__btn--icono" aria-label={t.cerrar} onClick={cerrar}>✕</button>
        </div>
        <ol className="agp-config__pasos">
          {[t.paso1, t.paso2, t.paso3].map((nombre, i) => <li key={nombre} aria-current={paso === i + 1 ? "step" : undefined}>{i + 1}. {nombre}</li>)}
        </ol>

        {paso === 1 && (
          <div className="agp-config__paso">
            <label className="agp-config__campo"><strong>{t.elegirUsuario}</strong><input autoFocus value={q} placeholder={t.escribe} onChange={(e) => { setQ(e.target.value); setPersona(null); }} /></label>
            {buscando && <p role="status" className="agp-config__suave">{t.cargando}</p>}
            {!buscando && q.trim().length >= 3 && candidatos.length === 0 && <p className="agp-config__suave">{t.sinCoincidencias}</p>}
            <ul className="agp-config__candidatos">
              {candidatos.map((c) => (
                <li key={c.correo}><button type="button" className="agp-config__rol" aria-pressed={persona?.correo === c.correo} onClick={() => setPersona(c)}>
                  <strong>{c.nombre}</strong> <span className="agp-config__suave">· {c.correo}{c.detalle ? ` · ${c.detalle}` : ""}</span></button></li>
              ))}
            </ul>
          </div>
        )}

        {paso === 2 && (
          <div className="agp-config__paso">
            <strong>{t.elegirRol} {persona?.nombre}</strong>
            <div className="agp-config__rejilla">
              <button type="button" className="agp-config__rol" aria-pressed={rol === ""} onClick={() => setRol("")}><strong>{t.sinRol}</strong><span className="agp-config__suave">{t.sinRolOpcion}</span></button>
              {perfiles.map((p) => {
                const r = resumenDeRol(p);
                return (
                  <button key={p.id} type="button" className="agp-config__rol" aria-pressed={rol === p.id} onClick={() => setRol(p.id)}>
                    <strong>{p.nombre}</strong><span className="agp-config__suave">{r.vistas} {t.vistas} · {r.acciones} {t.acciones} · {r.datos} {t.datos}</span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {paso === 3 && (
          <div className="agp-config__paso">
            <div className="agp-config__tarjeta"><strong>{t.resumen}</strong><p>{fmt(t.tendra, { p: persona?.nombre, r: rolElegido?.nombre || t.sinRol })}</p></div>
            <div className="agp-config__aviso agp-config__aviso--warn">
              <strong>{t.otraAreaT}</strong>
              <label className="agp-config__campo">{t.porQue} <span className="agp-config__suave">({t.minimo})</span><textarea rows={2} value={porQue} onChange={(e) => setPorQue(e.target.value)} /></label>
              <label className="agp-config__campo">{t.criterio} <span className="agp-config__suave">({t.minimo})</span><textarea rows={2} value={criterio} onChange={(e) => setCriterio(e.target.value)} /></label>
            </div>
          </div>
        )}

        <div className="agp-config__botones">
          <button type="button" className="agp-config__btn" disabled={paso === 1} onClick={() => setPaso(paso - 1)}>{t.atras}</button>
          {paso < 3 && <button type="button" className="agp-config__btn agp-config__btn--primario" disabled={!siguienteOk} onClick={() => setPaso(paso + 1)}>{t.siguiente}</button>}
          {paso === 3 && <button type="button" className="agp-config__btn agp-config__btn--primario" onClick={enviar}>{t.enviar}</button>}
          <button type="button" className="agp-config__btn" onClick={cerrar}>{t.cancelar}</button>
        </div>
        <p className="agp-config__suave">{t.notaAsignar}</p>
      </div>
    </div>
  );
}

// ── Secretos ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

function PestanaSecretos({ t, secretos, cap, ocupado, hacer, api }) {
  const [editando, setEditando] = useState(null);
  const [valor, setValor] = useState("");
  const [reiniciar, setReiniciar] = useState(false);
  const lista = secretos?.secretos || [];
  const grupos = [[t.oManual, lista.filter((s) => s.administrable)], [t.oMesa, lista.filter((s) => !s.administrable)]];
  const guardar = async () => {
    const ok = await hacer(() => api.cargarSecreto(editando, valor), t.okSecreto);
    setValor("");
    if (ok) { setEditando(null); setReiniciar(true); }
  };

  return (
    <div className="agp-config__tarjeta">
      <h2>{t.secretosT}</h2>
      <p className="agp-config__suave">{t.secretosD}</p>
      {secretos?.problema && <p role="alert" className="agp-config__aviso agp-config__aviso--error">{secretos.problema}</p>}
      {lista.length === 0 && <p className="agp-config__suave">{t.sinSecretos}</p>}
      {grupos.map(([titulo, items]) => items.length > 0 && (
        <details key={titulo} open={titulo === t.oManual} className="agp-config__plegable">
          <summary><strong>{titulo}</strong> <span className="agp-config__tag">{items.length}</span></summary>
          <table>
            <thead><tr><th scope="col">{t.secreto}</th><th scope="col">{t.variable}</th><th scope="col">{t.estado}</th><th scope="col">{t.actualizado}</th><th scope="col" /></tr></thead>
            <tbody>
              {items.map((s) => (
                <tr key={s.nombre}>
                  <td><code>{s.nombre}</code><br /><span className="agp-config__suave">•••• {t.valorOculto}</span></td>
                  <td><code>{s.variable}</code></td>
                  <td><span className={`agp-config__tag ${s.estado === "cargado" ? "agp-config__tag--ok" : "agp-config__tag--warn"}`}>{s.estado === "cargado" ? t.cargado : t.falta}</span></td>
                  <td>{s.actualizado ? String(s.actualizado).slice(0, 10) : "—"}</td>
                  <td>{s.administrable && <button type="button" className="agp-config__btn agp-config__btn--chico" disabled={!cap.cargarSecretos || ocupado} onClick={() => { setEditando(s.nombre); setValor(""); }}>{t.cargarValor}</button>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </details>
      ))}
      {editando && (
        <div className="agp-config__aviso agp-config__aviso--info">
          <strong>{t.cargarDe} <code>{editando}</code></strong>
          <label className="agp-config__campo">{t.nuevoValor}<input type="password" autoComplete="new-password" value={valor} onChange={(e) => setValor(e.target.value)} /></label>
          <p className="agp-config__suave">{t.unaVez}</p>
          <div className="agp-config__botones">
            <button type="button" className="agp-config__btn agp-config__btn--primario" disabled={ocupado || valor.trim().length < 8} onClick={guardar}>{t.guardarValor}</button>
            <button type="button" className="agp-config__btn" onClick={() => { setEditando(null); setValor(""); }}>{t.cancelar}</button>
          </div>
        </div>
      )}
      {reiniciar && (
        <div className="agp-config__aviso agp-config__aviso--warn">
          <span>{t.reiniciarNota}</span>
          <button type="button" className="agp-config__btn" disabled={!cap.cargarSecretos || ocupado} onClick={async () => { if (await hacer(() => api.reiniciar(), t.okReinicio)) setReiniciar(false); }}>{t.reiniciar}</button>
        </div>
      )}
    </div>
  );
}

// ── Actividad ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

function PestanaActividad({ t, peticiones, cap, ocupado, hacer, api }) {
  const [filtro, setFiltro] = useState("todas");
  const etiqueta = { pendiente: t.ePendiente, validada: t.eValidada, aplicada: t.eAplicada, rechazada: t.eRechazada, fallida: t.eFallida, cancelada: t.eCancelada };
  const filas = peticiones.filter((p) => filtro === "todas" || p.Estado === filtro);
  return (
    <div className="agp-config__tarjeta">
      <h2>{t.actividadT}</h2>
      <p className="agp-config__suave">{t.actividadD}</p>
      <div role="group" className="agp-config__acciones">
        {["todas", "pendiente", "aplicada", "rechazada"].map((id) => (
          <button key={id} type="button" className="agp-config__chip" aria-pressed={filtro === id} onClick={() => setFiltro(id)}>{id === "todas" ? t.todas : etiqueta[id]}</button>
        ))}
      </div>
      <div className="agp-config__tabla">
        <table>
          <thead><tr><th scope="col">#</th><th scope="col">{t.queCol}</th><th scope="col">{t.pedidoPor}</th><th scope="col">{t.fecha}</th><th scope="col">{t.estado}</th><th scope="col" /></tr></thead>
          <tbody>
            {filas.length === 0 && <tr><td colSpan={6} className="agp-config__suave">{t.sinPeticiones}</td></tr>}
            {filas.map((p) => (
              <tr key={p.IDSolicitud}>
                <td><code>{String(p.IDSolicitud).slice(0, 8)}</code></td>
                <td>{[p.Accion, p.Destinatario, p.Rol].filter(Boolean).join(" · ")}{p.Motivo ? <><br /><span className="agp-config__suave">{p.Motivo}</span></> : null}</td>
                <td>{p.Solicitante}</td><td>{String(p.Fecha || "").slice(0, 10)}</td>
                <td><span className="agp-config__tag">{etiqueta[p.Estado] || p.Estado}</span></td>
                <td>{p.Estado === "pendiente" && <button type="button" className="agp-config__btn agp-config__btn--chico" disabled={!cap.principal || ocupado} onClick={() => hacer(() => api.cancelar(p.IDSolicitud), t.okPeticion)}>{t.cancelarPet}</button>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
