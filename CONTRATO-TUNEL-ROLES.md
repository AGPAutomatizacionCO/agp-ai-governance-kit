# Contrato del túnel de roles y secretos (`/api/roles-app`)

Referencia técnica para quien construye o revisa la pantalla estándar «Configuración de roles y secretos» o el backend de un desarrollo. Responde una pregunta que no debe volver a hacerse:
**¿con qué API habla la pantalla de configuración, cómo se autentica y qué devuelve cada ruta?** Complementa `ACCESO-Y-ROLES-DEL-DESARROLLO.md` (la norma: qué es obligatorio y quién puede qué) y
`templates/auth-estandar/README.md` (qué archivos se copian).

> **Fuente de verdad: la Mesa de Requerimientos.** Este contrato se verificó contra `backend/src/flask_config/bp_roles.py` y los módulos que llama (`gestion_roles.py`, `roles_cola.py`,
> `roles_por_area.py`, `secretos_tunel.py`, `auth.py`) en el commit `e27b3ca` de la Mesa (2026-11-05). Si la Mesa y este documento difieren, **manda la Mesa** y se corrige el documento.
> El desarrollo no escribe roles ni toca el Key Vault: **pide**, y la Mesa valida, aplica y audita.
>
> **Dónde quedan los roles y cuánto duran.** Los roles personalizados viven en tres tablas del propio desarrollo (`App_<Área>_<Desarrollo>_Roles`, `…_RolesDatos` y `…_RolesPersonas`) que solo escribe la Mesa; mientras no existan, en las tablas centrales de la Mesa, y el túnel funciona igual. **Los roles son de gestión continua: no tienen vigencia ni fecha de vencimiento.** Una asignación dura hasta que quien administra la cambia o la quita; ni la pantalla, ni el túnel ni las tablas llevan una cláusula de tiempo. Ninguna ruta de este contrato recibe ni devuelve una fecha de vigencia.

## 1. Qué es y quién lo llama

El túnel son las rutas `/api/roles-app/<idProyecto>/…` de la Mesa. Las usan dos clientes, siempre con el `id_token` de Microsoft de la **persona** que tiene la sesión abierta en **esa** app:

| Cliente | Para qué | Rutas que usa |
|---|---|---|
| **El navegador** (la pantalla estándar `ConfiguracionDesarrollo`, con `src/services/rolesMesa.js`) | Gestionar roles, personas y secretos | `estado`, `peticiones`, `solicitudes`, `directorio`, `secretos`, `secretos/<nombre>`, `secretos/reiniciar` |
| **El backend del desarrollo** (con `ROLES_DESDE_MESA=true`) | Saber qué rol y qué permisos tiene quien inicia sesión y autorizar con eso | `mios` |

No confundir con `/api/proyectos/<id>/roles…`: esas son las rutas de la pestaña Roles de la **propia Mesa** (token de la Mesa). Un desarrollo **nunca** las llama.

### De dónde salen la dirección y el identificador

La API del desarrollo los entrega a la pantalla en `GET /api/config` → `roles: { mesaUrl, idProyecto }` (plantilla `templates/auth-estandar/backend/src/flask_config/bp_base.py`), a partir de tres variables
que **no son secretos** y que se declaran en `env` de `.agp/runtime.yaml`:

| Variable | Valor |
|---|---|
| `ROLES_DESDE_MESA` | `"true"` para activar la gestión desde la Mesa (con `"false"` la pantalla dice que la conexión no está activa) |
| `MESA_API_URL` | `https://…` de la Mesa (sin barra final). En producción: `https://agp-co-registro-desarrollos.azurewebsites.net` |
| `MESA_ID_PROYECTO` | El identificador del desarrollo en la Mesa (un GUID que se ve en la página del desarrollo) |

La base de todas las rutas es `{MESA_API_URL}/api/roles-app/{MESA_ID_PROYECTO}`. La Mesa responde con CORS abierto (`*`), por eso el navegador puede llamarla directo.

## 2. Autenticación

```text
Authorization: Bearer <id_token de Microsoft de la persona, emitido para ESTA app>
```

- Es el **`id_token`** de MSAL (el que ya trae `getAuthToken()` de `AuthContext.jsx`), **no** un `access_token` de Graph y **no** un token de la Mesa.
- La Mesa verifica la firma (JWKS del tenant de AGP) y el emisor. La audiencia (`aud`) es el registro de login del desarrollo: la Mesa la traduce a la Web App del desarrollo y exige que coincida con
  `<idProyecto>` de la ruta. Un token de otra app responde `403`.
- La persona se identifica por `preferred_username`, `email` o `upn` (en ese orden). Si el token no trae un correo, `401`.
- Solo local (`DISABLE_AUTH=true` en la Mesa, nunca en Azure) la Mesa no pide token.

## 3. Forma de las respuestas

```json
{ "message": "Listo", "data": <lo que devuelve cada ruta> }
```

Un error trae `{ "message": "<motivo legible>" }` con su código HTTP (a veces `"data"` con el detalle técnico del token). El cliente estándar lanza `ErrorMesa(message)`.

| Código | Cuándo |
|---|---|
| `400` | Cuerpo o parámetro inválido (acción desconocida, `areas` que no es lista, `PUT` de secreto con claves distintas de `valor`…) |
| `401` | Sin `Authorization`, token inválido o vencido, token sin correo |
| `403` | La app que llama no es un desarrollo registrado; el token es de otro desarrollo; la persona no administra o no tiene la autoridad para esa acción |
| `404` | El desarrollo, el rol (perfil), el permiso, el área o el secreto no existen |
| `409` | Conflicto de estado: el desarrollo no tiene Web App todavía, secreto que crea la Mesa, ya hay `n` admins globales, último admin global, perfil en uso, petición que ya no está pendiente |
| `502` | Error del sistema (Entra, Graph, vault, base de datos). El mensaje es genérico: nunca lleva valores de secretos ni detalles internos |
| `503` | La Mesa no pudo verificar la app que llama; reintentar |

## 4. Quién puede llamar qué

«Administra» = la persona tiene el rol `Admin` (administrador principal, «Admin global»), el rol `AdminApp` (administrador secundario, «Admin») o es de IT. «Principal» = `Admin` o IT.
La jerarquía fina de cada cambio la aplica la Mesa al procesarlo, no la pantalla: **lo que la pantalla deshabilita, la Mesa igual lo rechaza.**

| Ruta | Método | Quién |
|---|---|---|
| `/mios` | GET | Cualquier persona con sesión en la app |
| `/directorio` | GET | Cualquier persona con sesión en la app |
| `/estado` | GET | Quien administra |
| `/personas` | GET | Quien administra |
| `/peticiones` | GET | Quien administra |
| `/solicitudes` | POST | Quien administra (la jerarquía fina decide qué puede dar cada uno) |
| `/peticiones` | POST | Quien administra |
| `/peticiones/<idSolicitud>` | DELETE | Quien la envió, o IT |
| `/personas-por-area` | GET | Quien asigna personas (principal; con `ROLES.md` v2, `AdminApp` solo si `adminAppAsignaRoles: true`; con v1, también quien administra un dominio) |
| `/asignacion-por-area` | POST | Ídem |
| `/auditoria` | GET | Quien administra (con `ROLES.md` v2, solo quien asigna personas) |
| `/secretos` | GET | Quien administra (solo lectura para el secundario) |
| `/secretos/historial` | GET | Quien administra |
| `/secretos/<nombre>` | PUT | **Solo el principal** |
| `/secretos/reiniciar` | POST | **Solo el principal** |

## 5. Rutas de lectura

### `GET /mios` — quién soy y qué puedo abrir

Lo pide **el backend de la app** al iniciar y renovar la sesión. Devuelve lo que la persona ve en la app:

```json
{
  "correo": "persona@agpglass.com",
  "rol": "Usuario",
  "adminGlobal": false,
  "dominiosAdmin": [],
  "areas": ["pedidos"],
  "areasEfectivas": ["pedidos"],
  "detalleAreas": [],
  "version": "v2",
  "nivel": "usuario",
  "perfil": { "id": "logistica", "nombre": "Logística", "general": false },
  "permisos": { "modulos": ["estado-pedidos"], "funciones": ["estado-pedidos.exportar"] }
}
```

- `nivel`: `global` (administrador principal), `admin` (secundario) o `usuario`. Con `ROLES.md` v2 también vienen `version`, `perfil` y `permisos`; `perfil` es `null` si la persona no tiene rol ni vista general.
- `perfil.general: true` = la persona **no tiene rol asignado** y ve la vista general. `perfil.porArea` aparece cuando el rol le llegó por la regla de su área de Microsoft.
- `permisos.modulos` son las **vistas** que puede abrir y `permisos.funciones` las **acciones** dentro de ellas (`<modulo>.<accion>`). Un administrador recibe todo el catálogo.
- `sinAcceso` (texto) viene por compatibilidad y está **obsoleto**: la pantalla sin acceso es la estándar y no usa texto libre.

### `GET /estado` — todo lo que muestra la pantalla

Devuelve el catálogo, las personas con rol y qué puede hacer quien mira. Campos principales:

```json
{
  "desarrollo": { "id": "…", "nombre": "…", "web": "…", "area": "…" },
  "version": "v2",
  "catalogo": [], "catalogoPermisos": [], "maxAdminsGlobales": 2,
  "personas": [{ "correo": "…", "nombre": "…", "rol": "…", "etiqueta": "…", "nivel": "…", "areas": [], "editable": true, "vistaGeneral": false, "porArea": null, "perfil": null }],
  "yo": { "correo": "…", "etiqueta": "Admin global", "nivel": "global", "adminGlobal": true, "esAdmin": true, "asignarAdmins": true, "asignarPersonas": true, "editarPerfiles": true, "dominiosAdministrables": [] },
  "rolesApp": [],
  "perfiles": [{ "id": "logistica", "nombre": "Logística", "permisos": [], "obsoletos": [], "personas": 3, "areas": null, "general": false }],
  "vistaGeneral": "general", "accesoPorArea": [], "cupos": {},
  "asignarAcceso": true, "adminAppAsignaRoles": false, "rolesDeAcceso": false
}
```

- `yo` es lo que decide qué botones se habilitan: `adminGlobal` = principal (carga secretos y pide cambios de personas); `asignarPersonas`, `editarPerfiles` y `esAdmin` los demás permisos.
- `personas` solo llega completa a quien puede asignar personas; `rolesApp` (los roles propios del desarrollo) solo al principal. Los campos de `ROLES.md` v2 (`perfiles`, `catalogoPermisos`, `vistaGeneral`,
  `accesoPorArea`, `cupos`) solo existen con `version: "v2"`.
- En la API, lo que la pantalla llama **«rol»** se llama **`perfil`** (nombre histórico). `rol` es el rol de Entra ID (`Admin`, `AdminApp`, `Usuario` o uno propio del desarrollo).

### `GET /personas?q=texto` y `GET /directorio?q=texto` — buscar en el directorio de AGP

Devuelven `[{ "nombre": "…", "correo": "…@agpglass.com", "detalle": "…" }]`. `personas` es para quien administra; `directorio` sirve **a cualquier pantalla** de la app (un buscador de
entrevistados, responsables…) y solo pide sesión en esa app. La Mesa usa su propia identidad de Graph: el token del usuario nunca se usa contra Graph. Las búsquedas se reutilizan 5 minutos.

### `GET /personas-por-area?area=Texto del área`

Personas de un área de Microsoft (el `department` de Entra ID, el mismo texto que muestra Teams): `{ "area", "personas": [...], "truncado", "requiereJustificacion" }`. Cada persona trae `asignable` (falso para
administradores y para quien pide) y el `motivo`. `requiereJustificacion` es `true` cuando el área no es la del desarrollo. Máximo 500 personas (`truncado`). El `area` va de 2 a 100 caracteres.

### `GET /peticiones?estado=a,b&limite=n`, `GET /auditoria?limite=n`, `GET /secretos/historial?limite=n`

- `peticiones`: la cola y el historial, la más nueva primero. Estados: `pendiente → validada → aplicada | rechazada | fallida`, y `cancelada`. `estado` filtra por una lista separada por comas.
- `auditoria`: los eventos de roles (`Fecha`, `Actor`, `RolActor`, `Accion`, `Persona`, `Rol`, `Resultado`, `Motivo`, `Origen`, `Mensaje`).
- `secretos/historial`: `[{ "fecha", "actor", "secreto", "resultado" }]`; nunca valores.
- `limite` por defecto 200 (máximo 1000 en peticiones y 500 en el historial de secretos).

## 6. Rutas de escritura: roles y personas

### `POST /solicitudes` — pedir un cambio y aplicarlo ya

Cuerpo: `{ "accion": "…", …campos de la acción…, "justificacion"?, "criterio"?, "clave"? }`. La petición se encola (queda en el historial con su correlación) y se aplica en el momento.
`clave` es una **clave de idempotencia** (hasta 80 caracteres): repetir la misma clave devuelve la petición ya atendida en vez de duplicarla.

| `accion` | Campos | Qué hace |
|---|---|---|
| `asignar_perfil` | `correo`, `perfil` (clave, o `null` para quitar) | Da a la persona un rol (perfil) de `ROLES.md` v2 |
| `asignar_rol_acceso` | `correo`, `perfil` | Igual, con `rolesDeAcceso: true`: el rol trae sus áreas |
| `asignar_acceso` | `correo`, `perfil`, `areas[]` | Rol y áreas juntos (v2) |
| `asignar_areas` | `correo`, `areas[]` | Da áreas de `ROLES.md` (v1 y v2) |
| `asignar_rol` | `correo`, `rol` | Cambia el rol de Entra: `Admin`, `AdminApp`, `Usuario`, el rol de administrador de un dominio (`ROLES.md` v1) o uno propio del desarrollo |
| `quitar_rol` | `correo` | Quita el rol de Entra |
| `guardar_perfil` | `perfil: { id?, nombre, permisos[], general?, areas? }` | Crea (sin `id`) o edita un rol: nombre de 2 a 60 caracteres y permisos del catálogo |
| `borrar_perfil` | `perfil` (clave) | Elimina un rol sin personas, que no sea la vista general ni el rol por defecto de un área |
| `marcar_vista_general` | `perfil` (clave, o `null` para quitarla) | Marca el rol que ven todos los que no tienen uno asignado |

Respuesta (`data`): `{ "resultado": "autorizado", "mensaje": "…", "detalle": …, "peticion": { "IDSolicitud", "Estado", "Correlacion" } }`. Un rechazo de reglas es un error HTTP con el motivo; un error del
sistema deja la petición pendiente y la Mesa la reintenta sola (la respuesta lo dice).

Reglas que la Mesa impone siempre:

- Solo cuentas `@agpglass.com`. **Nadie cambia sus propios permisos** (salvo IT).
- Si la persona **no es del área del desarrollo** (por su `department` de Entra), las acciones que dan acceso exigen `justificacion` y `criterio` de **al menos 20 caracteres cada uno**. Si el área o el
  departamento no se conocen, se trata como otra área (falla del lado de pedir justificación).
- Máximo 2 administradores globales; no se puede quitar ni cambiar al último; un admin delegado no puede cambiar a un administrador ni a IT.
- Máximo 30 roles (perfiles) por desarrollo. Un rol con personas asignadas no se borra.
- Cambios de `ROLES.md` v2 (`guardar_perfil`, `borrar_perfil`, `asignar_perfil`, `asignar_acceso`, `asignar_rol_acceso`) con un `ROLES.md` v1 responden `409`.

### `POST /peticiones` y `DELETE /peticiones/<idSolicitud>`

- `POST`: mismo cuerpo que `solicitudes`, pero **solo encola**: devuelve la fila de la petición (`pendiente`) y la atiende el proceso de la Mesa. Para quien espera la respuesta, usar `solicitudes`.
- `DELETE`: cancela una petición **pendiente** (`{ "cancelada": true }`). Solo quien la envió o IT; si ya no está pendiente, `409`.

### `POST /asignacion-por-area` — el mismo rol a todo un área

Cuerpo: `{ "area": "…", "correos": ["…"], "perfil": "clave" | null, "justificacion"?, "criterio"?, "clave"? }` (con `ROLES.md` v1, `areas: [...]` en lugar de `perfil`). Hasta **200** correos por lote.
La Mesa **vuelve a leer el área** y solo acepta correos que de verdad son de ella. Cada persona pasa por las mismas reglas que una petición individual; un rechazo no corta el lote. Si el área no es la
del desarrollo, el lote exige **una** `justificacion` y **un** `criterio` (20 caracteres cada uno). Respuesta:

```json
{ "area": "…", "aplicados": 12, "rechazados": 1, "enCola": 0,
  "resultados": [{ "correo": "…", "nombre": "…", "estado": "aplicado | rechazado | en cola", "motivo": null }] }
```

## 7. Rutas de escritura: secretos

Solo existen los secretos que el desarrollo **declara** en `.agp/runtime.yaml` (se leen de `main`) y que **no** crea la Mesa. La norma de nombres (`<desarrollo>-<dato>`) está en
`ACCESO-Y-ROLES-DEL-DESARROLLO.md` §6 y `NOMENCLATURA-DATOS.md`.

### `GET /secretos`

```json
{ "puedeCargar": true, "reinicio": true, "problema": null,
  "secretos": [{ "nombre": "mi-desarrollo-api-reportes", "variable": "API_REPORTES", "estado": "cargado | falta", "actualizado": "2026-11-05T14:02:11+00:00", "administrable": true }] }
```

- `administrable: false` = lo crea la Mesa al aprobar el plan (cuentas de conexión a bases: `…-db-server|user|username|pwd|password`); se lista como «creado por la Mesa» y no se edita.
- `puedeCargar` es `true` solo para el principal. `problema` trae el motivo si no se pudo leer el contrato o el vault (por ejemplo, el repositorio no declara secretos).
- Nunca trae valores: solo nombre, variable, estado y fecha de la última versión.

### `PUT /secretos/<nombre>`

Cuerpo: **exactamente** `{ "valor": "…" }`. Cualquier otra clave (o ninguna) responde `400`. Respuesta: `{ "actualizado": "<fecha ISO>", "avisos": [] }`.

- El valor viaja una vez, se guarda como una versión nueva en el vault de desarrollos y **nunca** se devuelve, registra ni audita. La auditoría guarda quién, qué secreto, cuándo y el resultado.
- El valor se recorta de espacios, debe ser texto, no vacío, de hasta 8192 caracteres y sin caracteres de control (un salto de línea al pegar es el error más común).
- `404` si el secreto no está declarado en `runtime.yaml` de `main` (un secreto **nuevo** declarado en una rama no se puede cargar hasta fusionarlo); `409` si lo crea la Mesa; `403` si no es el principal.
- La app toma el valor nuevo al **reiniciarse**.

### `POST /secretos/reiniciar`

Reinicia la Web App del desarrollo para que tome los secretos nuevos. Solo el principal. Respuesta: `{ "reiniciada": true }`; `409` si el desarrollo aún no tiene Web App; `502` si Azure no pudo reiniciarla.

## 8. Ejemplos

### La pantalla (frontend): usar el cliente de la plantilla, no escribir llamadas a mano

```js
import { clienteDeEsteDesarrollo } from "../services/rolesMesa";

const mesa = clienteDeEsteDesarrollo(getAuthToken);   // null si ROLES_DESDE_MESA está apagado
if (!mesa) return <p>La conexión con la Mesa no está activa.</p>;

const estado = await mesa.estado();                    // GET  /estado
await mesa.solicitar({ accion: "asignar_perfil", correo: "persona@agpglass.com", perfil: "logistica" });   // POST /solicitudes
await mesa.cargarSecreto("mi-desarrollo-api-reportes", valorPegado);                                          // PUT  /secretos/<nombre>
```

`crearClienteMesa({ mesaUrl, idProyecto, getAuthToken })` arma `{mesaUrl}/api/roles-app/{idProyecto}` y añade el `Authorization: Bearer`. Un error de la Mesa llega como `ErrorMesa` con su `message`.

### El backend: preguntar por la persona con su mismo token (`mios`)

```python
import os
import requests

def alcance_de(id_token: str) -> dict:
    url = f"{os.environ['MESA_API_URL'].rstrip('/')}/api/roles-app/{os.environ['MESA_ID_PROYECTO']}/mios"
    r = requests.get(url, headers={"Authorization": f"Bearer {id_token}"}, timeout=15)
    r.raise_for_status()
    return r.json()["data"]        # nivel, perfil, permisos.modulos, permisos.funciones, areas…
```

Reglas de un backend bien hecho (las que sigue el piloto de SAC, `backend/app/roles_mesa.py`):

- **Falla cerrada:** si la Mesa no responde y no hay nada guardado, la persona entra con la **vista general (solo lectura)**; nunca con más de lo que dijo la Mesa.
- **Caché corta** (≈60 s con token) para no preguntar en cada llamada; con la Mesa caída se puede reutilizar lo último que dijo mientras dure la sesión.
- **Timeout de 15 s:** con reglas por área de Microsoft la Mesa también consulta a Graph y la primera llamada tras un rato sin uso puede tardar (arranque en frío).
- La API del desarrollo sigue validando el token y exige `Admin` en lo administrativo (`ACCESO-Y-ROLES-DEL-DESARROLLO.md` §1): el túnel decide **qué ve** la persona, no reemplaza la autorización.

### Comprobar a mano (sin pegar tokens en ningún archivo)

```bash
curl -s -H "Authorization: Bearer $ID_TOKEN" "$MESA_API_URL/api/roles-app/$MESA_ID_PROYECTO/mios"
```

`$ID_TOKEN` sale de la sesión del navegador de la app (nunca se guarda en el repositorio ni se pega en un chat).

## 9. Errores frecuentes

| Síntoma | Causa | Qué hacer |
|---|---|---|
| `401 Token inválido o expirado` | Se envió un `access_token`, un token de la Mesa o uno vencido | Usar el `id_token` de `getAuthToken()` de ESA app; si venció, cerrar sesión y entrar |
| `403 La aplicación que llama no es un desarrollo registrado` | La app no se desplegó con la Mesa o `MSAL_CLIENT_ID` no es el de su registro | Desplegar con la Mesa; no cambiar `MSAL_CLIENT_ID` |
| `403 Esta aplicación no puede operar los roles de otro desarrollo` | `MESA_ID_PROYECTO` es de otro desarrollo | Corregir la variable en `runtime.yaml` |
| `409 … todavía no tiene nombre de aplicación en Azure` | El desarrollo aún no tiene Web App asignada | Primero el despliegue aprobado por IT |
| `403 Solo el administrador principal carga secretos` | Lo intentó el administrador secundario | Lo carga el principal (`Admin`) o IT |
| `404 Ese secreto no está declarado en el .agp/runtime.yaml` | El nombre no está en `main` o está mal escrito | Declararlo en `runtime.yaml`, fusionar a `main` y volver a cargar |
| `409 Ese secreto lo crea la Mesa` | Es una cuenta de conexión a base de datos | No se carga a mano: lo crea la Mesa al aprobar el plan |
| `400 Se requiere únicamente el valor del secreto` | El cuerpo trae algo más que `valor` | Enviar solo `{ "valor": "…" }` |
| Todos entran con la vista general | La Mesa no responde o aún no hay asignaciones cargadas | Revisar `MESA_API_URL`, y cargar las asignaciones actuales antes de apagar el sistema anterior |
| `La conexión con la Mesa no está activa` | Falta `ROLES_DESDE_MESA`, `MESA_API_URL` (https) o `MESA_ID_PROYECTO` | Declararlas en `env` de `.agp/runtime.yaml` |
