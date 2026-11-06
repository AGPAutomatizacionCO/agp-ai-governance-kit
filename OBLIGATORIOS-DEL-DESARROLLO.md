# Obligatorios de un desarrollo AGP: la norma, cómo se ve bien y cómo se comprueba

Un solo lugar para saber **qué exige la norma a todo desarrollo que se despliega con la Mesa de Requerimientos**, con la regla, el documento donde vive, un ejemplo correcto, uno incorrecto y **quién lo comprueba**.
Sirve a tres lectores: la persona o el agente que **construye** (para llegar con el desarrollo maduro y no con preguntas), el **Agente de Despliegue** (cada fila es un requisito de su informe
`PreparacionDespliegue`, ver `agent-despliegue.md` §7 y `prompt-agente-despliegue-evaluacion.md` PASO 2B) y quien **revisa** (IT).

Este documento no reemplaza a las normas: las **enlaza**. Si algo aquí contradice a la norma enlazada, manda la norma y se corrige este documento. Sobre la Mesa: si el código de la Mesa y la norma
difieren, manda el código de la Mesa y se corrige la norma.

## Quién comprueba qué

| Quién | Qué hace | Cuándo |
|---|---|---|
| **El desarrollador / su agente** | Construye siguiendo la norma y ejecuta `python -m agpctl …` | Antes de pedir el despliegue |
| **Agente de Despliegue** | Lee el repositorio y reporta cada requisito como `ok`, `falta`, `no_aplica` o `no_verificable` (informativo: no califica ni bloquea) | Cuando se le pide, en cualquier estado del desarrollo |
| **`agpctl`** | Comprobaciones locales, de solo lectura, con las mismas reglas de la Mesa (`agpctl/README.md`) | Antes de pedir el despliegue |
| **La Mesa** | Preflight al aprobar el plan: **bloquea** (no hay despliegue) o **avisa** (se ve en el plan que aprueba IT) | Al generar y aprobar el plan |
| **El responsable** | Confirma lo declarado y firma el contrato del desarrollador (ver 20) | Después del ensayo, antes de IT |
| **IT** | Aprueba el plan completo una vez y fija la política de CD | Al final |

Lo que la Mesa **bloquea** no se negocia en la aprobación; lo que **avisa** se explica en el expediente.

## Resumen

| # | Obligatorio | Norma | Id en `PreparacionDespliegue` | `agpctl` | Mesa |
|---|---|---|---|---|---|
| 1 | Monolito desplegable y perfil | `ARQUITECTURA-DESPLIEGUE.md` | `perfil` | `validate` | Bloquea |
| 2 | Pin del kit | `schemas/governance-manifest.schema.json` | `governance` | `validate` | Bloquea |
| 3 | Contrato `agp-deploy.json` | `schemas/agp-deploy-v2.schema.json` | `agp_deploy` | `validate` | Bloquea |
| 4 | CI y publicación | `DESPLIEGUE-A-MAIN.md` §5 | `ci`, `publicacion` | — | Bloquea |
| 5 | Dockerfile | `ARQUITECTURA-DESPLIEGUE.md`, `templates/Dockerfile-odbc-sqlserver.snippet` | `dockerfile`, `contexto_docker` | `validate` | Bloquea |
| 6 | Login Microsoft (MSAL) y `.agp/entra.yaml` | `templates/auth-estandar/README.md` | `entra`, `auth_estandar` | — | Bloquea |
| 7 | Acceso: organización o asignado | `ACCESO-Y-ROLES-DEL-DESARROLLO.md` §1 | `acceso_usuarios` | — | Aviso y se muestra a IT |
| 8 | `ROLES.md` (v2) | `ACCESO-Y-ROLES-DEL-DESARROLLO.md` §2 | `roles` | — | Bloquea si falta o es inválido (obligatorio con `gestionRoles: true`) |
| 9 | Menú de usuario estándar | `ACCESO-Y-ROLES-DEL-DESARROLLO.md` §4 | `menu_usuario` | — | Bloquea |
| 10 | Pantalla «Configuración de roles y secretos» | `ACCESO-Y-ROLES-DEL-DESARROLLO.md` §6, `CONTRATO-TUNEL-ROLES.md` | `configuracion_roles` | — | Aviso |
| 11 | Pantalla estándar «sin acceso» | `ACCESO-Y-ROLES-DEL-DESARROLLO.md` §2 | `pantalla_sin_acceso` | — | Aviso |
| 12 | Sin login ni gestor de roles propios | `ACCESO-Y-ROLES-DEL-DESARROLLO.md` §7 | `mecanismo_propio_acceso` | — | Aviso |
| 13 | Manifiesto de datos | `PERMISOS-Y-SECRETOS-DEL-WORKER.md`, `schemas/data-access-manifest.schema.json` | `manifiesto_datos` | `datos check` | Bloquea |
| 14 | Datos propios: nombres, SQLite → tabla propia | `NOMENCLATURA-DATOS.md` | `datos_locales` | `datos check` | Bloquea |
| 15 | Permisos de datos mínimos | `PERMISOS-Y-SECRETOS-DEL-WORKER.md` §3 | `manifiesto_datos` | `datos check` | Bloquea |
| 16 | `runtime.yaml`: variables y secretos por nombre | `PERMISOS-Y-SECRETOS-DEL-WORKER.md` §4 | `runtime` | `runtime check` | Bloquea |
| 17 | Nombre de los secretos `<desarrollo>-<dato>` | `ACCESO-Y-ROLES-DEL-DESARROLLO.md` §6 | `secretos_norma` | `runtime check` | Bloquea |
| 18 | Recursos externos (`recursos_externos`) | este documento (§18) | `recursos_externos` | `runtime check` | Bloquea la forma; IT los revisa |
| 19 | Expediente y notas de despliegue | `agent-documental.md` | `project_card`, `specs`, `deployment_notes` | — | Bloquea |
| 20 | Preparación a IT y contrato del desarrollador | este documento (§20) | — (lo hace el responsable) | — | Sin contrato no hay CD |
| 21 | Despliegue continuo (CD) | `DESPLIEGUE-A-MAIN.md` | — | — | Lo decide IT |

---

## 1. Monolito desplegable y perfil

**Regla.** Un repositorio, una imagen, un recurso de Azure. Si hay pantalla y API, la imagen lleva las dos y la API sirve el frontend. Un solo `.agp/profile.yaml` (`kind: container`) y un solo `.agp/runtime.yaml`.

```yaml
# .agp/profile.yaml — correcto (examples/profile-container-monolito.valid.yaml)
apiVersion: profile.agp/v1
id: python-api
kind: container
build: { context: ., dockerfile: Dockerfile, dependencyManifest: backend/requirements.txt }
runtime: { port: 5000, healthPath: /api/health }
deploy: { target: app-service }
```

**Incorrecto.** API en una Web App y la pantalla en una Static Web App (`react-static`), o nginx + backend + frontend como contenedores separados: solo con excepción escrita de IT.
**Se comprueba:** `python -m agpctl validate --repo <ruta> --environment dev`; el agente reporta `perfil`.

## 2. Pin del kit (`.agp/governance.yaml`)

**Regla.** `kit.ref` es el SHA de 40 caracteres de un commit del kit (nunca `main` ni un SHA abreviado) y `profile` es el mismo `id` del perfil.

```yaml
apiVersion: governance.agp/v1
kit: { source: AGPAutomatizacionCO/agp-ai-governance-kit, version: v4.0.0-rc.1, ref: <sha de 40 caracteres> }
profile: python-api
```

**Incorrecto.** `ref: main`, `ref: 268ef85` o un `profile` distinto al de `profile.yaml`. **Se comprueba:** `agpctl validate`; agente `governance`. Si el pin es anterior a una norma nueva, el desarrollo se evalúa con el kit de **ese** SHA: subirlo es una decisión del desarrollo.

## 3. Contrato `.github/agp-deploy.json`

**Regla.** Formato v2: `Puerto` (1–65535) y `RutaHealthCheck` (empieza por `/`) que **coinciden** con `runtime.port` y `runtime.healthPath` del perfil. Las claves planas `port` / `health` son el formato viejo.
**Se comprueba:** `agpctl validate`; agente `agp_deploy`.

## 4. CI y publicación

**Regla.** `.github/workflows/ci.yml` con trigger en `main` (verde sobre el commit que se despliega) y `.github/workflows/dev-publish.yml` solo con `workflow_dispatch` (entradas `run_id` y `expected_sha`), que repite las
pruebas antes de construir y usa acciones de terceros fijadas por SHA. El `--file` del `az acr build` es exactamente `build.dockerfile` y el último argumento exactamente `build.context`.
**Incorrecto.** Un `dev-publish.yml` con `push:`; un publicador propio que despliega por su cuenta (el único camino de publicación es el que dispara la Mesa). **Se comprueba:** agente `ci` (el estado verde solo lo ve la Mesa: `no_verificable` sin evidencia) y `publicacion`.

## 5. Dockerfile

**Regla.** Usuario sin privilegios (`USER`), imagen base por digest (`@sha256`), `EXPOSE` igual al puerto del perfil, `HEALTHCHECK`; el `.dockerignore` no excluye lo que el Dockerfile copia. Con `pyodbc`/SQL Server: `msodbcsql18`, `unixodbc` y
**`libgssapi-krb5-2`** instalados en la misma instrucción (`templates/Dockerfile-odbc-sqlserver.snippet`); sin esa librería el contenedor arranca y `/api/health` responde 200, pero toda ruta con SQL devuelve 503.
**Incorrecto.** `FROM python:3.12` (sin digest), correr como root, `*.json` en `.dockerignore` con un `COPY package.json`. **Se comprueba:** `agpctl validate`; agente `dockerfile` y `contexto_docker`.

## 6. Login Microsoft (MSAL) y `.agp/entra.yaml`

**Regla.** MSAL con Entra ID es obligatorio para todo desarrollo, tenga o no bases de datos. Se copia el paquete `templates/auth-estandar/` **sin cambios** (`LoginScreen.jsx`, `login-estandar.css`, `agp-tema.css`,
encabezado y menú); la API expone `GET /api/config` y valida el token con `require_auth`. `.agp/entra.yaml` declara al menos un administrador (el desarrollador funcional) con su correo @agpglass.com; **no hay secreto de cliente** (`secrets: []`).

```yaml
apiVersion: entra.agp/v1
login: required
redirectUriPath: /
signInAudience: AzureADMyOrg
graphPermissions: [User.Read, offline_access]
acceso: organizacion
administradores:
  - { nombre: Nombre Apellido, correo: usuario@agpglass.com }
secrets: []
env: [MSAL_CLIENT_ID, MSAL_TENANT_ID]
```

**Incorrecto.** Un login propio; un secreto de cliente en `secrets`; `administradores` vacío o con un correo que no es @agpglass.com. **Se comprueba:** agente `entra` y `auth_estandar`; la Mesa compara los archivos del paquete byte a byte con el kit fijado en `governance.yaml`.

## 7. Acceso: organización o asignado

**Regla.** Por defecto, **todo desarrollo está abierto a la organización** (como la Mesa de Ayuda): `acceso: organizacion`; quien entra sin rol ve la vista general y los roles los da el administrador en «Configuración».
Restringir es la excepción: `acceso: asignado` con `justificacion` (≥ 40 caracteres) y `publico` (≤ 300). Ver `ACCESO-Y-ROLES-DEL-DESARROLLO.md` §1.

```yaml
# Excepción justificada
acceso: asignado
justificacion: "Nómina individual: solo Compensaciones puede ver los salarios; ni la vista general puede mostrarse a otros departamentos."
publico: "Personal de Compensaciones"
```

**Incorrecto.** `assignmentRequired: true` a secas (ya no cierra la app: se quita); `organizacion` junto a `assignmentRequired: true`; `asignado` sin `justificacion`; una vista general con funciones administrativas; un módulo administrativo que no exige `Admin`.
**Se comprueba:** agente `acceso_usuarios`; la Mesa lo muestra en el plan («Acceso de usuarios») y lo ata a la aprobación.

## 8. `ROLES.md` (v2)

**Regla.** El archivo `ROLES.md` (contrato `roles.agp/v2`) es la vista para personas de los roles, áreas y permisos y es lo que valida la Mesa. Sus `areas` son dominios de datos del desarrollo, **no** departamentos de Microsoft (`CONTRATO-TUNEL-ROLES.md` §3.1). Declara el catálogo de `permisos` (módulos y funciones que el código sabe ocultar y bloquear) y los `perfilesIniciales`.
Quien entra sin rol ve la vista general (la marca el administrador en «Configuración»). **No** lleva `sinAcceso.mensaje` (obsoleto: lo reemplaza la pantalla estándar).

```markdown
---
apiVersion: roles.agp/v2
gestionRoles: true
adminsGlobales:
  - correo: responsable@agpglass.com
permisos:
  - modulo: estado-pedidos
    nombre: Estado de pedidos
    funciones:
      - { id: exportar, nombre: Exportar a Excel }
perfilesIniciales:
  - { id: solo-consulta, nombre: Solo consulta, permisos: [estado-pedidos] }
---

# Roles de Portal de pedidos
| Rol | Qué puede |
|---|---|
| Admin | Todo |
| Solo consulta | Ver el estado de los pedidos |
```

**Incorrecto.** `apiVersion: roles.agp/v1` en un desarrollo nuevo; texto que contradice a `entra.yaml` (por ejemplo «lo usa toda la organización» con `acceso: asignado`).
**Se comprueba:** agente `roles` (existe y cumple la forma `roles.agp/v1` o `v2`; con `gestionRoles: true` en `.agp/entra.yaml` es obligatorio) y `acceso_usuarios` (coherencia con el código y con `entra.yaml`).

## 9. Menú de usuario estándar

**Regla.** El encabezado monta el mismo menú de todos (`UserMenu`): el botón con nombre y rol visibles y, al abrirlo, «Configuración» (enlace **directo** a `/configuracion`, solo para quien administra) y «Cerrar sesión». Se cumple con el componente del paquete o con uno propio que respete las marcas.

| Marca | Qué es |
|---|---|
| `data-agp-menu="usuario"` y `aria-label="Menú de usuario"` | El botón con el nombre y el rol |
| `data-agp-menu="configuracion"` | «Configuración» (solo con varios enlaces administrativos propios despliega «Administración») |
| `data-agp-menu="cerrar-sesion"` | «Cerrar sesión» |

**Incorrecto.** Un menú sin «Configuración» para el administrador; «Configuración» → «Administración» → «Configuración del desarrollo» (el doble clic que se eliminó); un submenú con un solo enlace. **Se comprueba:** agente `menu_usuario`; la Mesa lo bloquea como el login.

## 10. Pantalla «Configuración de roles y secretos»

**Regla.** `/configuracion` monta `ConfiguracionDesarrollo` (pestañas Roles, Usuarios, Secretos y Actividad), conectada a la Mesa por el túnel de roles; **no se arma otra**. Qué ve cada persona está en `ACCESO-Y-ROLES-DEL-DESARROLLO.md` §6 y la API en `CONTRATO-TUNEL-ROLES.md`.

| Marca | Qué es |
|---|---|
| `data-agp-configuracion="estandar"` | La raíz de la pantalla |
| `data-agp-pestana="roles\|usuarios\|secretos\|actividad"` | Cada pestaña |
| `role="dialog"` y `aria-modal="true"` | El modal de asignar usuario (tres pasos) |

La Mesa guarda los roles de un desarrollo nuevo en tres tablas de su propio esquema, que crea y valida el worker en cada despliegue (SAC y los que ya tenían roles siguen en las tablas centrales hasta migrar). La app solo usa el túnel (`/mios`…): no las crea, no las escribe, no las lee directamente y **no las declara en el manifiesto de datos** (nombre reservado, `ACCESO-Y-ROLES-DEL-DESARROLLO.md` §6). Son de gestión continua: **sin vigencia ni cláusula de tiempo**.
Conexión: `ROLES_DESDE_MESA`, `MESA_API_URL` y `MESA_ID_PROYECTO` en `env` de `runtime.yaml`, `roles` en `GET /api/config` y `ROLES.md` v2. El backend lee el rol por el túnel con el helper `templates/auth-estandar/backend/src/helpers/roles_mesa.py` (`GET /api/roles-app/<id>/mios`, falla cerrada).
**Incorrecto.** Una pantalla de «Administración de usuarios» con tabla propia de usuarios y rutas de roles propias; escribir las llamadas a `/api/roles-app` a mano en vez del cliente `rolesMesa.js`. **Se comprueba:** agente `configuracion_roles`.

## 11. Pantalla estándar «sin acceso»

**Regla.** Quien inicia sesión y no tiene acceso ve `SinAcceso` (raíz con `data-agp-sin-acceso="estandar"`), **sin texto libre**: el nombre de la app, el contacto del desarrollador funcional (`administradores[0]` de `.agp/entra.yaml`, correo @agpglass.com, entregado por
`GET /api/config` como `contactoNombre` y `contactoCorreo`) y la persona con sesión; ES / PT; botones Copiar correo, Reintentar y Cerrar sesión.
**Incorrecto.** Un mensaje propio (`sinAcceso.mensaje` de `ROLES.md`) o un «contacta a TI» genérico; un contacto que no es @agpglass.com. **Se comprueba:** agente `pantalla_sin_acceso`.

## 12. Sin login ni gestor de roles propios

**Regla.** La fuente de verdad de los roles es la Mesa. No quedan una tabla de usuarios del desarrollo, rutas de administración de usuarios o roles ni una pantalla de administración de usuarios: se migran (`ACCESO-Y-ROLES-DEL-DESARROLLO.md` §7). El agente **detecta y reporta**; no corrige ni elige.
**Se comprueba:** agente `mecanismo_propio_acceso` (`ok` = no hay ninguno).

## 13. Manifiesto de datos

**Regla.** Si el código toca una base de datos (`RequiereAccesoBD: true`), existe `ai/outputs/data-access-manifest.json` (ruta fija, se sobreescribe) que cumple el esquema y lista **todas** las tablas que el código usa: las propias y las
**preexistentes** (con su base, servidor `*.database.windows.net`, esquema **real**, columnas usadas y operaciones observadas). Usar bases reales no es un hallazgo; no declararlas, sí.
**Incorrecto.** Un mapa solo con las tablas propias; `server: null`; un esquema inventado. **Se comprueba:** `python -m agpctl datos check --repo <ruta>` (copiar la salida literal en el informe; con `valid: false` el requisito va `falta`, nunca `ok`); agente `manifiesto_datos`.

## 14. Datos propios: nomenclatura y SQLite

**Regla.** Lo que el desarrollo **crea** vive en su esquema `app_<área>_<desarrollo>` y con el nombre `App_<Área>_<Desarrollo>_<tabla>` (`NOMENCLATURA-DATOS.md`), con `origen: propia_del_desarrollo` y `crear_en_despliegue: true`, tipos de
columna de la lista cerrada del esquema y una clave primaria por tabla. **SQLite (o cualquier archivo local) no es un origen de despliegue**: lo que hoy vive ahí se declara como **tabla propia nueva**, con `migracion_desde` solo como referencia. **Las tablas nacen vacías**; el desarrollador migra
sus datos después, por su cuenta. No hay aprobación del dueño del dato y la sensibilidad es informativa.

```json
{ "table": "App_Manufacturing_GestorSolicitudes_solicitudes", "origen": "propia_del_desarrollo", "crear_en_despliegue": true,
  "migracion_desde": { "motor": "sqlite", "tabla": "solicitudes" }, "operaciones_permitidas": ["SELECT", "INSERT", "UPDATE"] }
```

```json
{ "database_id": "local", "motor": "sqlite:///./app.db" }
```

El segundo bloque es **incorrecto**: una fuente con `motor` que empieza por `sqlite` bloquea el plan. Ejemplo completo: `templates/data-access-manifest.crear-tablas.example.json`.
**Se comprueba:** `agpctl datos check`; agente `datos_locales` (reporta también si el código de producción sigue conectándose a SQLite: el archivo se pierde al reiniciar). El código puede seguir usando SQLite en local con otra cadena de conexión.

## 15. Permisos de datos mínimos

**Regla.** Por tabla solo `SELECT`, `INSERT` y `UPDATE`; **nunca `DELETE`** ni permisos de esquema. `INSERT`/`UPDATE` sobre tablas preexistentes son una excepción que IT ve resaltada y que se explica en la `descripcion` de la tabla. Las columnas sensibles no bloquean:
IT las ve resaltadas. Lo que no está declarado no se concede.
**Incorrecto.** `DELETE` en `operaciones_permitidas`; una tabla preexistente con `crear_en_despliegue: true`. **Se comprueba:** `agpctl datos check`; agente `manifiesto_datos`.

## 16. `runtime.yaml`: variables y secretos por nombre

**Regla.** `.agp/runtime.yaml` (`runtime.agp/v1`) declara por **nombre** las variables (`env`, con valores no secretos) y los secretos (`secrets`: variable ← secreto del vault de desarrollos). Nunca valores. Para cada base: `<PREFIJO>DB_NAME` y los tres secretos
de conexión (`PERMISOS-Y-SECRETOS-DEL-WORKER.md` §4). Claves permitidas: `apiVersion`, `desarrollo`, `env`, `secrets`, `fuentes`, `recursos_externos` (`vault` no se puede elegir). Las variables reservadas (`MSAL_*`, `AZURE_*`, `WEBSITES_*`…) las pone la plataforma.
**Incorrecto.** Un valor secreto escrito en `env`; una variable que el código lee y no está declarada (o al revés); `vault: …`. **Se comprueba:** `python -m agpctl runtime check --repo <ruta>`; agente `runtime`.

## 17. Nombre de los secretos `<desarrollo>-<dato>`

**Regla.** `runtime.yaml` declara `desarrollo: <nombre>` (minúsculas, dígitos y guiones, 2 a 63 caracteres) y **todos** sus secretos se llaman `<desarrollo>-<dato>` (dato en minúsculas, dígitos y guiones; hasta 127 caracteres). Los de conexión a bases los crea la Mesa
(`<desarrollo>-db-server|user|pwd` con una base; `<desarrollo>-<base>-db-server|username|password` con varias; la Mesa reconoce ambas formas). La carga del valor está en `ACCESO-Y-ROLES-DEL-DESARROLLO.md` §6 («Secretos del desarrollo») y en 20.

```yaml
desarrollo: portal-pedidos
secrets:
  - { name: API_REPORTES, secret: portal-pedidos-api-reportes }     # correcto
  - { name: FIRMA_SESION, secret: sesion-firma }                    # incorrecto: no empieza con «portal-pedidos-»
```

**Se comprueba:** `agpctl runtime check` (error si no empieza con el desarrollo; **aviso** si falta `desarrollo` con secretos declarados, porque la preparación a IT lo exige); agente `secretos_norma`. Sin `desarrollo`, la Mesa no exige el prefijo en el preflight pero el paso «Secretos» de la preparación sí.

## 18. Recursos externos

**Regla.** Todo lo que el desarrollo usa **fuera de su Web App** y que IT debe conocer (un worker, una máquina virtual, un job programado, un script externo, un servicio de otro equipo) se declara en `recursos_externos` de `.agp/runtime.yaml`. **Declararlo no lo crea ni lo concede**:
IT lo revisa junto con el contrato. Cada recurso lleva:

| Campo | Regla |
|---|---|
| `tipo` | `worker`, `vm`, `job`, `script_externo`, `servicio_externo` u `otro` |
| `nombre` | minúsculas, dígitos y guiones (2 a 63), sin repetir |
| `descripcion` | qué hace y por qué existe (mínimo 20 caracteres) |
| `ubicacion` | dónde vive o corre (host, recurso de Azure, ruta, programador de tareas), hasta 300 caracteres, **nunca** con usuario, clave o token |
| `acceso` | `ninguno` o el **nombre** de un secreto ya declarado en `secrets` |
| `escribe_datos` | `true` o `false`: si modifica datos de alguna base |
| `responsable` | correo @agpglass.com de quien lo opera |

```yaml
recursos_externos:
  - tipo: worker
    nombre: cola-reportes
    descripcion: "Genera reportes nocturnos de pedidos y los deja en la tabla propia"
    ubicacion: "Container App agp-reportes"
    acceso: portal-pedidos-api-reportes
    escribe_datos: true
    responsable: persona@agpglass.com
```

**Incorrecto.** Un script que corre en el equipo de una persona y no se declara; una `ubicacion: "https://usuario:clave@host"`; `acceso` con la clave escrita en vez del nombre del secreto. **Se comprueba:** `agpctl runtime check`; agente `recursos_externos` (`no_aplica` si el desarrollo no usa nada fuera de su Web App).

## 19. Expediente y notas de despliegue

**Regla.** `project-card.md`, `specs/001` a `010` y `specs/007-deployment-notes.md` (cómo ejecutar, rollback y secretos **por nombre**, nunca valores). **Se comprueba:** agente `project_card`, `specs` y `deployment_notes`; lo documenta el Agente Documental.

## 20. Preparación a IT y contrato del desarrollador

**Regla.** Después de que el Agente de Despliegue y el worker tester aprueban, y **antes** de que IT apruebe, el responsable confirma en la Mesa lo que el agente **declaró** en el repositorio y firma el contrato del desarrollador. Es solo para desarrollos con repositorio que aún no están
desplegados. Está en el paso «Despliegue» de su ruta, bloque «Prepara tu solicitud a IT» (`specs/024-preparacion-solicitud-a-it.md` y `docs/despliegue/RUTA-READY-TO-DEPLOY.md` de la Mesa), con siete pasos:

1. **Ensayo aprobado** (automático). 2. **Origen de los datos** (tablas con la norma, permisos CRUD, «hoy en SQLite → tabla propia, nace vacía»). 3. **Acceso y privacidad** (pública dentro de la empresa o privada con justificación ≥ 40 caracteres). 4. **Secretos** (los nombres salen del
manifiesto; aquí solo se registra el valor). 5. **Recursos externos**. 6. **Contrato** (seis cláusulas, confirmación final y firma). 7. **Revisar y enviar a IT**.

- **Todo sale del repositorio:** lo que el desarrollador no declaró no aparece. Por eso 7, 13–18 deben estar bien **antes**: la pantalla confirma, no inventa. Un nombre de secreto nuevo es un commit nuevo.
- **La firma es la persona de la sesión** (no se escribe un nombre) y queda atada a la **huella** del plan: si cambia el commit, un archivo de contrato (`.agp/*`, el manifiesto de datos, `ROLES.md`) o el plan, todo queda obsoleto y se repite. GitHub es la auditoría.
- **El agente no confirma ni firma**: prepara el repositorio para que la confirmación sea completa (`agent-despliegue.md` §7).

## 21. Despliegue continuo (CD)

**Regla.** Lo decide IT por desarrollo (`DESPLIEGUE-A-MAIN.md`): apagado (por defecto), automático o limitado a N por día. **Sin contrato firmado y vigente no hay CD:** en el primer despliegue oficial exitoso la Mesa deja **limitado, 3 publicaciones automáticas por día** solo si hay un contrato del
desarrollador firmado de la versión actual y para el plan que se despliega; sin él, no escribe ninguna política y el CD queda apagado. Nunca pisa una decisión de IT. El CD solo publica la imagen y **no publica nada** si el commit toca `.agp/entra.yaml`, `.agp/runtime.yaml`,
`.agp/profile.yaml` o `ai/outputs/data-access-manifest.json`: eso va por la aprobación completa de IT.
**Para el equipo de desarrollo:** no configuras ni despliegas el CD; asume que un merge a `main` puede publicarse solo; avisa en el PR si tocas el contrato (`DESPLIEGUE-A-MAIN.md` §6).

---

## Antes de pedir el despliegue: la lista de comprobación

La versión con los pasos para dejarlo funcional está en `COMO-DEJARLO-FUNCIONAL.md`. Antes de pedir el despliegue, verifica que **todo esto quedó en el repositorio**:

1. `python -m agpctl validate --repo <ruta> --environment dev` → `valid: true` (1–5).
2. `python -m agpctl datos check --repo <ruta>` → `valid: true` si hay manifiesto de datos (13–15).
3. `python -m agpctl runtime check --repo <ruta>` → `valid: true` y sin `avisos` (16–18).
4. **Identidad y roles:** `.agp/entra.yaml` con `acceso`, `administradores[0]` @agpglass.com y `secrets: []` (6–7); `ROLES.md` v2 con `permisos` y `perfilesIniciales`, sin `sinAcceso.mensaje` (8).
5. **Conexión con la Mesa:** `ROLES_DESDE_MESA`, `MESA_API_URL` (https) y `MESA_ID_PROYECTO` en `env` de `.agp/runtime.yaml` (10).
6. **Secretos por nombre:** `desarrollo:` y todo secreto como `<desarrollo>-<dato>`, sin valores en el repositorio ni en `env` (16–17).
7. **El backend lee el rol por el túnel:** consulta `GET /api/roles-app/<id>/mios` con el `id_token` (helper `roles_mesa.py` del paquete o equivalente), falla cerrada y no llama a Graph para roles (10).
8. **Frontend estándar:** `UserMenu` con las marcas `data-agp-menu` y «Configuración» directo a `/configuracion`; `ConfiguracionDesarrollo` (`data-agp-configuracion="estandar"`); cliente `rolesMesa.js`; `SinAcceso` sin texto libre y `GET /api/config` con `contactoNombre` y `contactoCorreo` (9–11).
9. **La app solo usa el túnel:** ninguna tabla de usuarios o de roles propia, ningún `CREATE TABLE`, `INSERT` o `UPDATE` sobre tablas de roles, ninguna ruta propia de administración de usuarios o roles, y el manifiesto de datos no declara tablas de roles: hoy los roles viven en tablas centrales de la Mesa y las tres tablas por desarrollo son un modelo objetivo pendiente (12).
10. Sin `.env` real en el repositorio; `DISABLE_AUTH` solo en local.
11. Expediente y notas de despliegue al día (19).
12. Pedir el informe al Agente de Despliegue: cada requisito `ok` o con su motivo en `falta`.
